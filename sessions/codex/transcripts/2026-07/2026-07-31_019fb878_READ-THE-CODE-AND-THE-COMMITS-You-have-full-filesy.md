# READ THE CODE AND THE COMMITS. You have full filesystem read access and both repos are here. A previous session of
yours could not open files and answered from prose; do not repeat that. Where you cannot verify something from the
tree, say so explicitly rather than assuming.

REPOS
  /root/marlin_ppu/Kernels                      branch ppu_dev
  /root/marlin_ppu/Kernels/third_party/actlize  branch ppu-w4a16-dev   (a CUTLASS-3 fork for the PPU)

THE WORK TO REVIEW, oldest first. `git log -p` these in the actlize repo; the Kernels repo has matching commits.
  244367ec  packed scale step 3c: the gmem side, so the channel is end-to-end
  a22c8b76  ZMul cancels the converter's -8, and the zero g2s is gated
  d4c6c154  hoist the unit load to once per k-tile, fold every index, make OFF cost nothing
  93541fb5  decode from registers, not through a byte pointer -- the +70% was local memory
  d4a50569  PPU_PACKED_SCALE_NOP, a timing-only ablation
  2d44310e  the units travel BY VALUE, read once per k-tile -- 8 registers, not 64
  6eaf40d7  rewrite as F: decode into smem, not per lane
  a8098be4  store with SmemLayoutScale's own (n, group, stage)
  3474c4af  scale_load_k is already a TILE index
  2dcc9def  F': cp.async the gguf's bytes into staging, decode at the barrier the pipeline already has
  dfc0b8d3  pack both fields into one f16x2 lane pair, and store two columns per thread
  fce4fa41  revert the paired store: it raced
  b5567944  earlyclobber, and the NOP ablation the docs promised but did not have
  bfee6c87  the hazard is subnormal flushing

THE FULL WRITTEN ARGUMENT, including every number and every refutation:
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md      (last four sections)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md   (sections 3, 4, 9, 10)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/README.md                 (converter amortisation)
  Kernels/general/w4a16_gemm/cutlass_w4a16/CMakeLists.txt                            (_SPLITK_CFGS and its comments)

THIS IS A PERFORMANCE REVIEW. The numeric bug found in the last session (f16x2 flushing Q4_K's subnormal d) is
already understood -- do not spend the session on it. What I want attacked is the PERFORMANCE reasoning and the
sequence of decisions, i.e. whether the conclusions drawn are the ones the data supports, and what should be done
next in the decode band.

THE MEASUREMENTS. Decode band: MoE, L=64 experts, top-k 8 so 8 are active, batch 1 so ONE real row per expert,
N=K=2048, gs=32, int4 weights, W4A16. 64 CUs, 256 KB shared per CU, HBM peak ~2766 GB/s.

  Pinned same-config A/B, kernel #233, grid (8,16,1) block (256,1,1), TileShape 16x128x256, warp 16x16, Stages 2:
      baseline (offline fp16 scale/zero planes)  20.11 us   34,191 cycles   102 registers
      packed   (gguf's native 16 B units)        22.70 us   38,588 cycles    98 registers
  Identical both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960; smem.ld 31,744;
  vmem.acp.commit.grp 19,456.
  Deltas: v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944; v.and.i +64,512;
  v.fma.f16 +36,864; tsm.st +71,680 with +73,728 bank conflicts and 1.83 transactions per store instruction;
  Shared Load +4,608; "shared store from global load" (cp.async's own smem writes) -9,216 (-38%);
  scalar bookkeeping ~+150K. About +699K instructions on a ~4.4M baseline.

  Three occupancy ladders, all measured in ONE run so the rows are comparable:
      TileN  16x32:256 (512 CTAs, 8 blk/CU, 2 warps/blk) | 16x64:256 (256, 4, 4) | 16x128:256 (128, 2, 8)
             -> 16x64:256 s2 S=1 = 20.52 us is the winner; 16x128 tied it at 20.11 in another run;
                same-config run-to-run spread is ~13%
      TileK  16x128:128 s2 S=1 24.16 | s4 S=1 22.06 | 16x64:128 s2 S=1 22.94 | s4 S=1 21.85
             (TK=256 wins; TK=64 lost 19% earlier but sits EXACTLY on the swzl delivery bound WN*TK*bits=4096)
      splitK on 16x64:128 s2: S=1 22.94 | S=2 22.48 | S=4 26.64 | S=8 27.79, warps/CU 14.2/28.4/56.9/113.8
             overall "speedup from split-K: 0.938x"
      HBM utilisation is 31-35% in EVERY row of all three ladders.

QUESTIONS.

P1. The conclusions currently written down are: (a) occupancy is not the lever, refuted three ways; (b) the
    pipeline-fill/prologue hypothesis is refuted, because TK=128 halves the fill share yet loses, and s4 beats s2
    despite more fill; (c) a persistent kernel is therefore not worth building for this band, also because 128
    tiles against 128 CTAs is exactly one wave; (d) the limiter is the int4->fp16 dequant pipeline at 1,898,496
    instructions against 131,072 mma. Which of these does the data actually support, which are over-claimed, and
    which are confounded? Note the ~13% run-to-run spread and say which conclusions survive it.

P2. What is the single most likely thing this kernel is ACTUALLY limited by, and what measurement would settle it?
    Rank candidates and say what each predicts. The counters available are acu (an ncu-like tool): per-opcode
    instruction counts, shared-memory transactions and bank conflicts, an HBM utilisation percent, warps/CU,
    registers, cycles, and a stall-reason mix. Assume anything ncu can do, acu can do.

P3. Is 20 us defensible at all for this shape? Compute the floors: weights are 8 experts x 2048 x 2048 x 0.5 B =
    16.8 MB, scale+zero 4.19 MB, A and D 32 KB each. Against 2766 GB/s that is a traffic floor. The mma floor is
    131,072 warp-mma of m16n16k16. Which floor is closer, how far is 20.11 us from each, and does that ratio point
    at the same limiter as P2? A separate CUDA-core-only GEMV on the same hardware and shape takes 22.27 us, i.e.
    within 11% of this tensor-core GEMM -- what does that say?

P4. The sequence E (decode per lane in registers, 26.89 us) -> F (decode in a synchronous loader, 24.17) ->
    F' (cp.async the raw bytes, decode at the existing barrier, 25.00/24.79) -> pinned A/B (22.70). Read the
    diffs. Was each step's stated reason the real reason? Which of these variants should have been predicted to
    fail before it was built, and from what?

P5. What would you do next, concretely, and what would you STOP doing? The current plan is to abandon in-GEMM
    decoding and convert once in a load-time kernel, paying 11% more weight bytes in device memory (160 vs 144
    bytes per 256 weights) for 0% runtime. Argue for or against, and name the experiment that decides it.

- **Thread ID:** `019fb878-4d08-77c3-b885-e84645ac578b`
- **Started / last event:** 2026-07-31 13:58 UTC → 2026-07-31 14:19 UTC
- **Working dir:** `/root/marlin_ppu/Kernels/third_party/actlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/07/31/rollout-2026-07-31T21-58-39-019fb878-4d08-77c3-b885-e84645ac578b.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "bfee6c87d604d6e8afcce19d3f0329f2f4a77f93", "branch": "ppu-w4a16-dev", "repository_url": "https://github.com/DrXuQian/actlize.git"}`

---

## User · 2026-07-31 13:58 UTC

READ THE CODE AND THE COMMITS. You have full filesystem read access and both repos are here. A previous session of
yours could not open files and answered from prose; do not repeat that. Where you cannot verify something from the
tree, say so explicitly rather than assuming.

REPOS
  /root/marlin_ppu/Kernels                      branch ppu_dev
  /root/marlin_ppu/Kernels/third_party/actlize  branch ppu-w4a16-dev   (a CUTLASS-3 fork for the PPU)

THE WORK TO REVIEW, oldest first. `git log -p` these in the actlize repo; the Kernels repo has matching commits.
  244367ec  packed scale step 3c: the gmem side, so the channel is end-to-end
  a22c8b76  ZMul cancels the converter's -8, and the zero g2s is gated
  d4c6c154  hoist the unit load to once per k-tile, fold every index, make OFF cost nothing
  93541fb5  decode from registers, not through a byte pointer -- the +70% was local memory
  d4a50569  PPU_PACKED_SCALE_NOP, a timing-only ablation
  2d44310e  the units travel BY VALUE, read once per k-tile -- 8 registers, not 64
  6eaf40d7  rewrite as F: decode into smem, not per lane
  a8098be4  store with SmemLayoutScale's own (n, group, stage)
  3474c4af  scale_load_k is already a TILE index
  2dcc9def  F': cp.async the gguf's bytes into staging, decode at the barrier the pipeline already has
  dfc0b8d3  pack both fields into one f16x2 lane pair, and store two columns per thread
  fce4fa41  revert the paired store: it raced
  b5567944  earlyclobber, and the NOP ablation the docs promised but did not have
  bfee6c87  the hazard is subnormal flushing

THE FULL WRITTEN ARGUMENT, including every number and every refutation:
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md      (last four sections)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md   (sections 3, 4, 9, 10)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/README.md                 (converter amortisation)
  Kernels/general/w4a16_gemm/cutlass_w4a16/CMakeLists.txt                            (_SPLITK_CFGS and its comments)

THIS IS A PERFORMANCE REVIEW. The numeric bug found in the last session (f16x2 flushing Q4_K's subnormal d) is
already understood -- do not spend the session on it. What I want attacked is the PERFORMANCE reasoning and the
sequence of decisions, i.e. whether the conclusions drawn are the ones the data supports, and what should be done
next in the decode band.

THE MEASUREMENTS. Decode band: MoE, L=64 experts, top-k 8 so 8 are active, batch 1 so ONE real row per expert,
N=K=2048, gs=32, int4 weights, W4A16. 64 CUs, 256 KB shared per CU, HBM peak ~2766 GB/s.

  Pinned same-config A/B, kernel #233, grid (8,16,1) block (256,1,1), TileShape 16x128x256, warp 16x16, Stages 2:
      baseline (offline fp16 scale/zero planes)  20.11 us   34,191 cycles   102 registers
      packed   (gguf's native 16 B units)        22.70 us   38,588 cycles    98 registers
  Identical both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960; smem.ld 31,744;
  vmem.acp.commit.grp 19,456.
  Deltas: v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944; v.and.i +64,512;
  v.fma.f16 +36,864; tsm.st +71,680 with +73,728 bank conflicts and 1.83 transactions per store instruction;
  Shared Load +4,608; "shared store from global load" (cp.async's own smem writes) -9,216 (-38%);
  scalar bookkeeping ~+150K. About +699K instructions on a ~4.4M baseline.

  Three occupancy ladders, all measured in ONE run so the rows are comparable:
      TileN  16x32:256 (512 CTAs, 8 blk/CU, 2 warps/blk) | 16x64:256 (256, 4, 4) | 16x128:256 (128, 2, 8)
             -> 16x64:256 s2 S=1 = 20.52 us is the winner; 16x128 tied it at 20.11 in another run;
                same-config run-to-run spread is ~13%
      TileK  16x128:128 s2 S=1 24.16 | s4 S=1 22.06 | 16x64:128 s2 S=1 22.94 | s4 S=1 21.85
             (TK=256 wins; TK=64 lost 19% earlier but sits EXACTLY on the swzl delivery bound WN*TK*bits=4096)
      splitK on 16x64:128 s2: S=1 22.94 | S=2 22.48 | S=4 26.64 | S=8 27.79, warps/CU 14.2/28.4/56.9/113.8
             overall "speedup from split-K: 0.938x"
      HBM utilisation is 31-35% in EVERY row of all three ladders.

QUESTIONS.

P1. The conclusions currently written down are: (a) occupancy is not the lever, refuted three ways; (b) the
    pipeline-fill/prologue hypothesis is refuted, because TK=128 halves the fill share yet loses, and s4 beats s2
    despite more fill; (c) a persistent kernel is therefore not worth building for this band, also because 128
    tiles against 128 CTAs is exactly one wave; (d) the limiter is the int4->fp16 dequant pipeline at 1,898,496
    instructions against 131,072 mma. Which of these does the data actually support, which are over-claimed, and
    which are confounded? Note the ~13% run-to-run spread and say which conclusions survive it.

P2. What is the single most likely thing this kernel is ACTUALLY limited by, and what measurement would settle it?
    Rank candidates and say what each predicts. The counters available are acu (an ncu-like tool): per-opcode
    instruction counts, shared-memory transactions and bank conflicts, an HBM utilisation percent, warps/CU,
    registers, cycles, and a stall-reason mix. Assume anything ncu can do, acu can do.

P3. Is 20 us defensible at all for this shape? Compute the floors: weights are 8 experts x 2048 x 2048 x 0.5 B =
    16.8 MB, scale+zero 4.19 MB, A and D 32 KB each. Against 2766 GB/s that is a traffic floor. The mma floor is
    131,072 warp-mma of m16n16k16. Which floor is closer, how far is 20.11 us from each, and does that ratio point
    at the same limiter as P2? A separate CUDA-core-only GEMV on the same hardware and shape takes 22.27 us, i.e.
    within 11% of this tensor-core GEMM -- what does that say?

P4. The sequence E (decode per lane in registers, 26.89 us) -> F (decode in a synchronous loader, 24.17) ->
    F' (cp.async the raw bytes, decode at the existing barrier, 25.00/24.79) -> pinned A/B (22.70). Read the
    diffs. Was each step's stated reason the real reason? Which of these variants should have been predicted to
    fail before it was built, and from what?

P5. What would you do next, concretely, and what would you STOP doing? The current plan is to abandon in-GEMM
    decoding and convert once in a load-time kernel, paying 11% more weight bytes in device memory (160 vs 144
    bytes per 256 weights) for 0% runtime. Argue for or against, and name the experiment that decides it.

## Assistant · 2026-07-31 13:59 UTC

I’ll audit the exact patches and the cited documents in both trees, then separate what the measurements establish from what they merely suggest. I’ll keep the numerical-bug thread out of scope except where the final hazard commit changes the performance interpretation.

<details><summary>1 tool call(s)</summary>

- `exec: const p = await tools.update_plan({plan:[ {step:"Inspect repository instructions, branches, matching commit topology, and cited documents",status:"in_progress"}, {step:"Read every listed actlize patch and trace the affected kernel/dataflow  …`

</details>

## Assistant · 2026-07-31 13:59 UTC

Both worktrees are clean and on the requested branches. I found no repository-level `AGENTS.md`, so there are no additional local review instructions to apply. I’m mapping the commit sequence and document sections now before judging the claims.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"git show --no-renames --format='COMMIT %H%nPARENTS %P%nDATE %aI%nSUBJECT %s' --stat 244367ec a22c8b76 d4c6c154 93541fb5 d4a50569 2d44310e 6eaf40d7 a8098be4 3474c4af 2dcc9def dfc0b8d3 fce4fa41 b556794 …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md | sed -n '757,906p'\n\nnl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_deri …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md | sed -n '28,132p'\n\nnl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_de …`

</details>

## Assistant · 2026-07-31 13:59 UTC

The written argument makes two strong inferential jumps I’ll test against the patches: it treats flat HBM percentage as proof against memory latency, and it treats opcode share as a throughput bottleneck. Neither follows from counts alone; the stall and issue/pipe-utilization evidence will be decisive. I’m now tracing whether the variants isolate the terms the prose says they isolate.

<details><summary>5 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"git show --no-ext-diff --no-renames --format='===== %H %s =====' --find-renames=0 244367ec a22c8b76 d4c6c154","workdir":"/root/marlin_ppu/Kernels/third_party/actlize","yield_time_ms":10000,"max_outpu …`
- `exec: const r = await tools.exec_command({cmd:"git show --no-ext-diff --no-renames --format='===== %H %s =====' 93541fb5 d4a50569 2d44310e","workdir":"/root/marlin_ppu/Kernels/third_party/actlize","yield_time_ms":10000,"max_output_tokens":60000}) …`
- `exec: const r = await tools.exec_command({cmd:"git show --no-ext-diff --no-renames --format='===== %H %s =====' 6eaf40d7","workdir":"/root/marlin_ppu/Kernels/third_party/actlize","yield_time_ms":10000,"max_output_tokens":60000}); text(r.output);`
- `exec: const r = await tools.exec_command({cmd:"git show --no-ext-diff --no-renames --format='===== %H %s =====' a8098be4 3474c4af 2dcc9def","workdir":"/root/marlin_ppu/Kernels/third_party/actlize","yield_time_ms":10000,"max_output_tokens":60000}) …`
- `exec: const r = await tools.exec_command({cmd:"git show --no-ext-diff --no-renames --format='===== %H %s =====' dfc0b8d3 fce4fa41 f4453bec adb960b0 b5567944 bfee6c87","workdir":"/root/marlin_ppu/Kernels/third_party/actlize","yield_time_ms":10000, …`

</details>

## Assistant · 2026-07-31 14:00 UTC

The diffs confirm that E and F are structurally different experiments, not incremental cleanups: E removes scale/zero shared reads but multiplies decode work across consuming lanes; F restores the original read side and decodes once per CTA into shared memory. F′ changes only the global-to-staging leg plus 4 KiB/CTA, so it is a good test of the exposed-load story—but only if occupancy and stall deltas are controlled.

<details><summary>4 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"git -C /root/marlin_ppu/Kernels log --format='KCOMMIT %H %s' -p -- third_party/actlize | rg -B3 -A4 'Subproject commit (244367ec|a22c8b76|d4c6c154|93541fb5|d4a50569|2d44310e|6eaf40d7|a8098be4|3474c4a …`
- `exec: const r = await tools.exec_command({cmd:"git -C /root/marlin_ppu/Kernels show --no-ext-diff --format='===== %H %s =====' 32752be 0009f64 051edcf d45427d -- general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md general/w4a16_ …`
- `exec: const r = await tools.exec_command({cmd:"git -C /root/marlin_ppu/Kernels show --no-ext-diff --format='===== %H %s =====' 406392f dbbea87 0f3d623 c7a9a4e -- general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md general/w4a …`
- `exec: const r = await tools.exec_command({cmd:"git -C /root/marlin_ppu/Kernels show --no-ext-diff --format='===== %H %s =====' 6c81c6a 23aa698 c100afc 1ad7630 -- general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md general/w4a16_ …`

</details>

## Assistant · 2026-07-31 14:01 UTC

The commit history exposes an important provenance issue: the 24.17/25.00 comparison was later admitted to have mixed shapes; only the 20.11/22.70 profiler pair is genuinely pinned. Also, the “43% dequant pipeline” is an opcode-count attribution, not yet a demonstrated critical-path attribution. I’m checking the scheduler, split-K accounting, and generated instruction path before ranking the limiter.

<details><summary>9 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"rg -n 'total_ctas|gridDim|split.?k|slices|warps/CU|HBM|speedup from split-K|SPLITK_ACU|SPLITK_ONLY|SPLITK_CFG|SharedStorageSize|moe_ok|WM <= TM|TileShape|WarpShape|K_BLOCK_MAX|transform_B_kblock|MixG …`
- `exec: const r = await tools.exec_command({cmd:"rg -l 'total_ctas' /root/marlin_ppu/Kernels/third_party/actlize/include /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16\n\nrg -n 'moe_ok|WM <= TM|SPLITK_ONLY|SPLITK_CFG|speedup from split-K …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/moe_splitk_bench_common.hpp | sed -n '1,260p'\n\nnl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/test_moe_splitk_benc …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba include/cutlass/gemm/kernel/tile_scheduler_params.h | sed -n '1540,1775p'\n\nnl -ba include/cutlass/gemm/kernel/ppu_aiu_gemm_mixed_input.hpp | sed -n '45,380p'\n\nrg -n 'cu_count|device_multip …`
- `exec: const r = await tools.exec_command({cmd:"rg -n 'isGroupProblemShape|GroupProblem' include/cutlass/gemm/kernel/ppu_aiu_gemm_mixed_input.hpp include/cutlass/gemm/kernel/*.hpp | rg 'mixed_input|group|Group'\n\nrg -n 'hw_info|cu_count|blocks_pe …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba include/cutlass/kernel_hardware_info.h | sed -n '1,220p'\n\nrg -n 'query_device_multiprocessor_count|hggcDeviceProp|multiProcessorCount|cu_count' include/cutlass/kernel_hardware_info.h tools e …`
- `exec: const r = await tools.exec_command({cmd:"rg -n --hidden --glob '!**/.git/**' '34,191|34191|38,588|38588|20\\.11 us|22\\.70 us|13\\.65|MultiProcessor|72-CU|64-CU|64 CUs|CU Count|cu_count' /root/marlin_ppu/Kernels /root/marlin_ppu/Kernels/thi …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/lowbit_moe_bench.hpp | sed -n '45,180p'\n\nnl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/test_moe_splitk_bench.cu | …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '450,545p;700,760p;835,915p'\n\nrg -n -C 10 'stall|Stall|IALU|FALU|LSU|issue|pipe|busy|eligible|warp  …`

</details>

## Assistant · 2026-07-31 14:03 UTC

A concrete inconsistency is now verified in the tree: the split-K harness divides working warps by 72, and its comments call the part 72-CU; the question states 64 CUs. Thus 14.2/28.4/56.9/113.8 are launch-warps ÷ 72, not measured resident warps/CU. On 64 CUs they are 16/32/64/128, and “128 CTAs is exactly one wave” only follows under the 64-CU premise. This has to be resolved from the device attribute or profiler topology before using wave/tail arguments.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"rg -n 'struct MixGemm|class MixGemm|MixGemmEmit|MixGemmChunkEmit|Cvt2Plane|convert\\(|apply_scale_atom|transform_B_kblock|fast_numeric_conversion' include/cutlass/gemm/collective/ppu_mma_aiu_multista …`
- `exec: const r = await tools.exec_command({cmd:"rg -n 'PPU_SCALE_PREFETCH' /root/marlin_ppu/Kernels /root/marlin_ppu/Kernels/third_party/actlize --glob '!**/.git/**'\n\nnl -ba include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '1,420p …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '440,625p'\n\nnl -ba include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '780,970p'","workdir":"/roo …`

</details>

## Assistant · 2026-07-31 14:06 UTC

I’ve found one material provenance issue in the written argument: the reported split-K “warps/CU” values are launch work divided by a hard-coded 72, not an achieved-occupancy counter. That also conflicts with the 64-CU premise behind “128 CTAs = exactly one wave.” I’m resolving the remaining timing provenance and roofline arithmetic before giving the verdict.

<details><summary>27 tool call(s)</summary>

- `exec: const r = await tools.exec_command({ cmd: "awk 'BEGIN { bytes=8*2048*2048*.5 + 8*2048*(2048/32)*4 + 2*8*2048*2; hbm=bytes/2766e9*1e6; mma=131072*2*16*16*16; mmat=mma/500e12*1e6; t=20.11; printf(\"bytes=%.0f\\nHBM_floor_us=%.9f\\n20.11/HBM=% …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n -i \"stall|eligible|memory dep|issue|pipe busy|24\\.17|25\\.00|24\\.79|mixed shapes|warps/CU|/ 72|multiprocessor\" general/w4a16_gemm/cutlass_w4a16/fold_derivation general/w4a16_gemm/cutlass_ …`
- `exec: const r = await tools.exec_command({ cmd: "sed -n '1215,1330p' general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md && sed -n '835,910p' general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md && git log --oneline --decorate --all -- g …`
- `exec: const r = await tools.exec_command({ cmd: "git show --stat --oneline 05a5309 && git show --format=fuller --no-ext-diff 05a5309 -- general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md general/w4a16_gemm/cutlass_w4a16/moe_splitk_bench_com …`
- `exec: const r = await tools.exec_command({ cmd: "for a in 0f3d623 c100afc 1ad7630 05a5309 aa82a75 HEAD; do printf '%s ' \"$a\"; git rev-list --count \"$a\"; done; git merge-base --is-ancestor 1ad7630 05a5309; echo ancestor_1ad_to_05=$?; git merge …`
- `exec: const r = await tools.exec_command({ cmd: "sed -n '1,235p' general/w4a16_gemm/cutlass_w4a16/moe_splitk_bench_common.hpp && sed -n '1,190p' general/w4a16_gemm/cutlass_w4a16/test_moe_splitk_bench.cu && git show 05a5309^:general/w4a16_gemm/cut …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/ppu_aiu_gemm_mixed_input_group.hpp | sed -n '70,215p'; nl -ba general/w4a16_gemm/cutlass_w4a16/moe_splitk_bench_common.hpp | sed -n '1,26p;196,216p'; nl -ba  …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/CMakeLists.txt | sed -n '220,330p'; nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md | sed -n '750,915p'; nl -ba general/w4a16_ge …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n '^## (9|10)\\.' general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md; nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md | sed -n '250,410p';  …`
- `exec: const r = await tools.exec_command({ cmd: "git show --format=fuller --stat b5567944 && git show --format= --no-ext-diff b5567944 -- include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp include/cutlass/gguf_packed_scale.h | …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"SmemLayoutScaleRawStaged|packed_decode_stage|cp_async_wait|transform_B_kblock|MixGemmNumericArrayConverter|kPackedScaleOn|GmemTiledCopyScalePacked\" include/cutlass/gemm/collective/ppu_mma_ …`
- `exec: const r = await tools.exec_command({ cmd: "rg --files | rg 'fast_numeric_conversion_for_mix_gemm\\.h$|numeric_conversion.*mix' && rg -n \"struct MixGemmNumericArrayConverter|uint4b|int4b\" include/cutlass | rg 'MixGemm|fast_numeric' | head  …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '440,530p'; nl -ba include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1580,1765p'", workdir: "/r …`
- `exec: const r = await tools.exec_command({ cmd: "git show --format=fuller --stat d1884b2 && git show --format= --no-ext-diff d1884b2 -- general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '1,260p'; git show --format=fuller --stat ba …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '130,205p;220,290p'; git blame -L 145,190 -- general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md", workdir: "/root/marl …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"16x32:256|16x64:256|16x128:256\" general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md general/w4a16 …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '500,580p'; git blame -L 540,575 -- general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md", workdir: "/root/marlin_ppu/Ke …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '735,1015p'", workdir: "/root/marlin_ppu/Kernels/third_party/actlize", yield_time_ms: 10000, max_output_tokens …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"double time_it|time_it\\(\" general/w4a16_gemm/cutlass_w4a16/lowbit_moe_bench.hpp | head -n 30; nl -ba general/w4a16_gemm/cutlass_w4a16/lowbit_moe_bench.hpp | sed -n '105,190p'", workdir: " …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"PPU_PACKED_SCALE_NOP|baseline B|nop.*full|transport\\+stores|full minus nop|arithmetic =|NOP\" /root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation /root/marlin_ppu/Ker …`
- `exec: const r = await tools.exec_command({ cmd: "awk 'BEGIN {printf(\"pointer_recovery_us=%.2f pointer_share_of_excess=%.1f%% remaining=%.1f%%\\n\",57.83-48.40,100*(57.83-48.40)/(57.83-33.88),100*(48.40/33.88-1)); printf(\"E_to_F=%.1f%% F_vs_base …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"22\\.27|Finegrained|ScaleZero|scale|zero|int4|Q4|mode\" general/w4a16_gemm/cutlass_w4a16/test_gemv_perf.cu general/w4a16_gemm/cutlass_w4a16/*gemv* | head -n 240; nl -ba general/w4a16_gemm/c …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '395,435p'; rg -n \"22\\.27\" general/w4a16_gemm/cutlass_w4a16 -S", workdir: "/root/marlin_ppu/Kernels", yield_time_ms: 1000 …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/gemv_lowbit/gemv_kernel.hpp | sed -n '118,215p'; nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '425,475p'", workdir: "/root/marlin …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"Option E|option E|OPTION E|Option F|decode per lane|same.*column|4 lanes|llama\" general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md | head -n 100; nl -ba general/w4a16_ge …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md | sed -n '495,575p'", workdir: "/root/marlin_ppu/Kernels", yield_time_ms: 10000, max_output_tokens: 12000 }); text(r.out …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"(^| )CU( |)=|#define CU|constexpr int CU|GEMV_CU\" general/w4a16_gemm/cutlass_w4a16/gemv_perf_common.hpp general/w4a16_gemm/cutlass_w4a16/gemv_lowbit general/w4a16_gemm/cutlass_w4a16/CMakeL …`

</details>

## Assistant · 2026-07-31 14:17 UTC

The central result is now clear: the three claimed “occupancy ladders” are not three occupancy experiments. TileN keeps total launch warps exactly constant, TileK does not enter the grid at all, and only split-K raises concurrency—while also changing K slicing, partial traffic, and reduction work. I’m folding that, the actual mainloop prologue code, and the existing (prose-only) stall capture into the final review.

<details><summary>1 tool call(s)</summary>

- `exec: const r = await tools.update_plan({ explanation: "Completed the source/commit audit, provenance checks, floor calculations, and hypothesis review. No files were modified.", plan: [ { step: "Inspect both repositories, branches, relevant file …`

</details>

## Assistant · 2026-07-31 14:19 UTC

I read both trees, all listed actlize patches in order, the matching Kernels commits, and the current implementations. I found no raw `.report`/`.ncu-rep` artifacts, so profiler values preserved only in Markdown cannot be independently rechecked.

Bottom line: the data supports “the tested tuning knobs found no large concurrency win” and “native in-GEMM decoding adds substantial work.” It does not support “occupancy was refuted three ways,” “prologue latency was refuted,” or “the 1.898M dequant instructions are proved to be the limiter.” The most likely limiter is a memory-dependency/request-latency path in the mainloop—not peak HBM bandwidth—with dequant/issue work a close second.

There is also a topology inconsistency that must be fixed before using any wave argument: the prompt says 64 CUs, but the harness divides launch warps by 72 and repeatedly calls the device a 72-CU part ([moe_splitk_bench_common.hpp](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/moe_splitk_bench_common.hpp:200)). The reported 14.02/14.2 achieved values also fit 1024/72, not 1024/64. The kernel itself queries the device CU count ([ppu_aiu_gemm_mixed_input_group.hpp](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/ppu_aiu_gemm_mixed_input_group.hpp:141)). I cannot verify which topology the reported runs actually used without the raw report.

## P1. What the conclusions really support

| Written conclusion | Verdict |
|---|---|
| Occupancy is not the lever, refuted three ways | Too broad. Only split-K actually raises total launch concurrency. |
| Pipeline fill/prologue is refuted | Not supported; the test and fill model are confounded. |
| Therefore persistence is not worth building | Reasonable prioritization, but not a demonstrated performance result. |
| Dequant pipeline is the limiter | It is a large work term, but instruction counts alone do not identify the limiter. |

### (a) Occupancy

TileN is not an occupancy ladder in the sense claimed:

- `512 CTAs × 2 warps`
- `256 × 4`
- `128 × 8`

All equal 1,024 launch warps: 16 warps/CU on 64 CUs or 14.22 on 72. TileN redistributes the same work into fewer, wider CTAs. The tree itself had already derived that TileN cancels from total grid warps ([TODO.md](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md:545)).

TileK also does not enter the grid. It changes K-loop count, shared footprint, delivery granularity and pipeline depth, but not launch warps; the CMake comment explicitly says this ([CMakeLists.txt](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/CMakeLists.txt:273)).

Only split-K raises launch warps, and its printed `warps/CU` is not an occupancy measurement—it is launch work divided by 72. Values such as 56.9 and 113.8 cannot be resident occupancy. Split-K also changes slice length, partial writes, merge work and scheduling.

The narrow conclusion that survives is:

> Raising concurrency through this split-K implementation produced no material gain at S=2 and clear regressions at S=4/8.

The current tree also records an older acu pair where achieved warps really rose 14.02→26.84 while time went 20.18→20.96 µs and Memory Dependency rose 0.98→1.772 ([TODO.md](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md:1256)). That is materially better evidence that simple occupancy is not useful here, although there is no raw report and it is not the exact pinned `16x128:256` fingerprint.

It still does not prove “occupancy is monotonically harmful.” It says additional warps supplied by K-slicing do not help this memory/request path.

### (b) Pipeline fill/prologue

The stated model is not the code’s pipeline. The implementation initially issues `Stages - 1` stages, not `Stages`, and also has a drain loop ([mainloop](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:743)). Therefore

```text
Stages / (K/TK + Stages)
```

is neither the exact number of fill iterations nor a measured fraction of cycles.

TK=128 versus TK=256 changes all of these simultaneously:

- outer-loop iterations: 16 versus 8;
- copy size and delivery granularity;
- shared-memory footprint;
- number of waits/barriers/control iterations;
- legal stage depth;
- compiler-generated unrolled code.

Similarly, s4 versus s2 changes steady-state overlap and resource residency at the same time as prologue work. An s4 win means deeper overlap outweighed its extra fill; it does not mean fill costs zero.

There is also an arithmetic overstatement: `24.16→22.06` is 8.7%, but `22.94→21.85` is only 4.75%, not “8–9%” for both rows.

The data disfavors a very large, fill-only bottleneck. It does not resolve a predicted 9% term, particularly when the relevant differences are 4.8–8.7% and same-config run spread is about 13%.

### (c) Persistence

“Do not build it next” is defensible. “It cannot help” is not.

Even if the hardware really has 64 CUs, `128 CTAs = 2/CU` only removes a grid-wave tail. It does not remove per-CTA pipeline fill. Persistence would need a deliberately smaller grid whose CTAs chain tiles, which trades away resident warps while trying to amortize tile setup.

If the measured machine was actually the 72-CU part described by the tree, the exact-one-wave statement is false: 128 CTAs do not distribute uniformly over 72 CUs.

The current kernel is explicitly non-persistent, one CTA per tile ([ppu_aiu_gemm_mixed_input_group.hpp](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/ppu_aiu_gemm_mixed_input_group.hpp:186)). A persistent variant is also not a drop-in schedule change because the mainloop binds tile coordinates during initialization. Given that engineering cost and the stronger load-time-conversion option, parking persistence is sensible—but it is an opportunity-cost decision, not a proven zero.

### (d) The 1,898,496-instruction dequant pipeline

The arithmetic is correct:

```text
1,898,496 / 131,072 = 14.48 instructions per mma
```

But the attribution is incomplete:

- `lop3`/`bfi` belong to int4 extraction.
- `fma`/`add` include scale/zero application as well as conversion.
- shifts, ORs, addressing, scalar control, waits and other unpack instructions are omitted.
- an instruction share is not a cycle share; these instructions can execute while memory operations are outstanding.

The converter itself contains a shift, four `lop3`s and four f16 conversion operations per eight codes ([fast_numeric_conversion_for_mix_gemm.h](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:452)). The subsequent scale/zero work is a separate dependent chain ([mainloop transform](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1552)).

What survives noise is that dequant is a first-order body of work and an important optimization target. What does not survive is the inference that it is the established bottleneck.

On the 13% spread: it is not necessarily a 13% within-run standard deviation—some drift is common-mode—but there are no repeated interleaved rows or confidence intervals. Cross-run differences below 13% are unusable. Within-run 4–9% differences are directional, not dispositive. The S=4/8 regressions of 16–21% likely survive, but they are split-K regressions, not clean occupancy results. The pinned +12.9% packed result sits exactly at the noise boundary and should be replicated before treating 2.59 µs as precise.

## P2. Most likely actual limiter

The best diagnosis is:

> A memory-dependency/request-latency-limited mainloop—covering global weight delivery, scale/shared-memory transactions and waits—not saturation of the HBM bus.

My ranking:

1. **Memory dependency / request and transaction latency.**  
   Predicts Memory Dependency or long-scoreboard stalls at the load/wait/scale-load PCs, few eligible warps, low individual ALU/tensor pipe utilization, and only modest bandwidth growth when more warps are supplied. That matches the in-tree stall transcription: Memory Dependency was reported above Instruction Fetch, and doubled when split-K doubled achieved warps.

2. **Vector instruction issue or dependency through unpack + affine + addressing.**  
   Predicts stalls and PC samples concentrated on `lop3`, shifts, f16 FMA/add and address/control instructions; core issue utilization should be high, and a B-dequant NOP should remove a large fraction of cycles without changing DRAM bytes. The +699K packed instructions and +12.9% pinned cycle delta make this plausible, but not proven as the baseline limiter.

3. **Pipeline wait/barrier serialization.**  
   Predicts sampling at `cp_async_wait`/`__syncthreads`, with deeper stages reducing those stalls. The s4 direction is suggestive, but too small and confounded to settle it.

4. **Shared-memory transaction inefficiency.**  
   Baseline Q4_K scale reads have a separately recorded conflict/transaction problem; packed F′ additionally introduces store conflicts. This predicts high shared transaction counts and bank-conflict stalls, but not necessarily a saturated shared-memory pipe. The packed store conflicts explain part of the packed delta, not the whole 20 µs baseline.

5. **MMA throughput.**  
   Very unlikely. It predicts high AIU/tensor-pipe busy and time proportional to MMA count, neither of which fits the floor or GEMV comparison.

The settling measurement is one raw full acu capture of the exact pinned fingerprint, with:

- achieved and eligible warps per scheduler;
- issued instructions/cycle and issue-slot utilization;
- per-pipe integer, f16, LSU, shared and MMA utilization;
- complete stall-reason mix with PC/source sampling;
- DRAM and L2 bytes, requests, hit rate, outstanding requests and latency;
- shared transactions per instruction and conflicts;
- cycles at `cp_async_wait`, barriers, converter and scale-load PCs.

Then make it causal with a timing-only `PPU_B_DEQUANT_NOP` that preserves B loads, scale loads and the MMA count but removes the int4 conversion/affine chain. The existing `PPU_PACKED_SCALE_NOP` only decomposes the added packed decoder; it does not remove the baseline weight dequant. The packed NOP now exists at [ppu_mma_aiu_multistage_mixed_input.hpp](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1305).

## P3. The floors

Using the repo’s hard-coded 500 TF/s tensor peak ([lowbit_moe_bench.hpp](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/lowbit_moe_bench.hpp:49)):

| Floor | Work | Floor | 20.11 µs / floor |
|---|---:|---:|---:|
| HBM traffic | 21,037,056 B | **7.606 µs** | **2.64×** |
| MMA | 131,072 × 2 × 16³ = 1.074 GFLOP | **2.147 µs** | **9.36×** |

At 20.11 µs:

- effective compulsory-traffic rate is **1.046 TB/s**, 37.8% of 2.766 TB/s;
- delivered padded-MMA rate is **53.4 TF/s**, 10.7% of 500 TF/s.

The traffic floor is much closer. That points in the same direction as the memory-dependency diagnosis, although roofline distance alone cannot distinguish memory latency from instruction overhead.

Two caveats:

- The tree does not derive the 500 TF/s value from the stated 64-CU configuration. If the real peak differs, the MMA floor scales inversely.
- The timed harness repeats the same resident buffers after a warmup ([lowbit_moe_bench.hpp](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/lowbit_moe_bench.hpp:136)). Actual DRAM traffic may be below logical traffic because of cache reuse. Only the raw DRAM-byte counter establishes whether 21.04 MB really crossed HBM per timed launch.

So 20 µs is defensible as a real implementation result, but not as a fundamental floor. It remains 2.64× from the optimistic traffic roof.

The 22.27 µs CUDA-core GEMV being only 10.7% slower says tensor throughput is not end-to-end decisive. Both implementations share the important things: int4 weight access, scale/zero access, dequantization and per-element/request latency. It does not, by itself, prove both are ALU-bound. The GEMV needs the same stall/pipe capture. The GEMV source does use the same gs=32 ScaleZero mode ([test_gemv_perf.cu](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/test_gemv_perf.cu:31)).

## P4. E → F → F′

### E

E should have been rejected before implementation. The very l94 result used to select it already said a warp touches eight columns and each column is broadcast to four lanes ([PLAN](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md:555)). Decoding “once per owning lane” therefore duplicated each `(column, group)` four times before accounting for multiple warps.

The byte-pointer/local-memory bug was real, but the commit title overstates it. On the quoted row:

- byte pointer: 57.83 µs;
- register extraction: 48.40 µs;
- baseline: 33.88 µs.

The fix recovered 9.43 µs—39% of the 23.95 µs excess—but left the kernel 42.9% slower. Thus “the +70% was local memory” is false; local memory was one large subproblem.

I found no preserved A/B or raw local-load counters for the subsequent by-value change, so its claimed register effect cannot be independently verified.

### F

F was the structurally correct design: decode once per CTA/column and publish fp16 planes to all consumers. Its reason for recovering performance is the fourfold removal of decode multiplicity and deletion of read-side state, not proof that “only an exposed LDG remains.”

The jump 26.89→24.17 is directionally consistent with that. It is not quantitatively attributable because the later handoff admits the 24.17 comparison mixed shapes ([HANDOFF](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md:49)).

F should have been the first implementation. The earlier argument rejected the llama.cpp loader shape solely because synchronous arithmetic would forfeit cp.async, without first pricing the 4× amortization advantage.

### F′

F′ is a good, cheap falsifier for one narrow question: was F’s raw global load latency dominant? It restores asynchronous transport, but:

- keeps every decode operation;
- keeps all explicit fp16 shared stores;
- adds a raw staging tile;
- performs decode after `cp_async_wait` and before the publishing barrier, so decode remains on the critical path.

Given the small scale channel and reported 6% LSU utilization, “probably little or no gain” was predictable. Definite failure was not: the exposed synchronous load could still have dominated.

The measured 24.17 versus 25.00/24.79 difference is only 2–3%, within noise, and later admitted to be mixed-shape. It therefore does not by itself refute the exposed-LDG hypothesis.

### Pinned A/B

The 22.70 result is not a performance-improving step after 25.00. It is the same F′ architecture measured with the correct identical fingerprint. The apparent improvement is measurement/configuration provenance.

The pinned counters establish that the added work exists and there is no spill. They do not prove how many of the 4,397 extra cycles belong to decode arithmetic versus stores/conflicts versus scalar/control work.

That causal decomposition was claimed before it existed: the E-era `PPU_PACKED_SCALE_NOP` was deleted by the F/F′ rewrites. Commit `b5567944` explicitly reintroduced “the NOP ablation the docs promised but did not have.” I found no subsequent baseline/NOP/full timing result. Thus “fully accounted” is too strong.

The paired adjacent-column store in `dfc0b8d3` should definitely have been predicted to race. `cp_async_wait` is per thread, and the code decodes before the block barrier; a thread cannot read the neighbor column copied by another thread. The current source documents exactly that failure ([packed decoder](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1274)).

## P5. What to do next

For this exact decode band, I favor the load-time conversion plan—conditionally on memory capacity and after repeating the pinned timing.

The steady-state numbers already favor it:

- native packed: 22.70 µs;
- preconverted fp16 planes: 20.11 µs;
- recurring saving: 2.59 µs;
- recurring storage/traffic penalty: 160/144 = 1.111×.

For the active eight experts, widening adds 2,097,152 logical bytes per GEMM, whose ideal HBM cost is only 0.758 µs. The measured 2.59 µs execution saving is larger, so the 160-byte form currently wins even after charging its extra recurring traffic.

But “0% runtime” is not literally correct:

- the conversion kernel has a one-time execution cost;
- every GEMM thereafter reads the widened metadata;
- the extra model memory can affect deployment, cache residency and which models fit.

The decisive experiment is:

```text
native:          R × Tpacked
convert-on-load: Tconvert + R × Tbaseline
```

Implement the standalone native→fp16-plane converter, then measure both complete paths in one process for `R = 1, 2, 4, 8, ...`, using repeated ABBA ordering and reporting confidence intervals, actual DRAM/L2 bytes and peak resident memory. The break-even reuse count is:

```text
Rbreak-even = Tconvert / (Tpacked − Tbaseline)
            = Tconvert / 2.59 µs
```

That directly answers the deployment question instead of calling load-time work free.

If the extra roughly 11% capacity is unacceptable, test the existing 148-byte middle form next. It is only +2.8% over native, saves 7.5% versus the fp16-plane baseline, and removes the 6-bit extraction/word-straddle work ([HANDOFF section 10](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md:268)).

I would stop:

- calling TileN and TileK occupancy experiments;
- using launch-warps/CU as achieved occupancy;
- inferring “not latency-bound” from low HBM utilization;
- inferring a bottleneck from opcode share without stall/pipe evidence;
- comparing sub-13% timings across runs or mixed shapes;
- spending rounds on 0.6–4% packed micro-optimizations before the NOP decomposition;
- building persistence for this band before the load-time conversion/reuse experiment.

No files were modified.
