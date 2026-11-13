# READ THE CODE. Full filesystem read access; both repos are here. Say "I cannot tell from the tree" rather than
inventing. Two questions, and the second is the one I care more about because nobody has ever looked at it.

REPOS
  /root/marlin_ppu/Kernels                      branch ppu_dev
  /root/marlin_ppu/Kernels/third_party/actlize  branch ppu-w4a16-dev

CONTEXT. Mixed-input W4A16 grouped GEMM (MoE, batch-1 decode) on the PPU (T-Head ZW810, SM80-like, 72 CUs, 256 KB
shared per CU, HBM peak ~2766 GB/s). Weights GGUF Q4_K, gs=32. Two ways to feed the per-group scale/zero:
  BASELINE  an offline step pre-multiplies into two fp16 planes (scale, zero: 4 B per group per column), cp.async'd
            straight into shared memory. 20.11 us.
  PACKED    the gguf's own 16 B unit per (superblock, column) -- fp16 d, fp16 dmin, sixteen 6-bit codes -- is
            cp.async'd in raw (2 B per group per column, half the traffic) and decoded on device into the SAME two
            fp16 shared planes, one thread per column, between cp_async_wait and __syncthreads. 22.70 us.
Both numerically correct now. Same kernel, pinned fingerprint grid (8,16,1) block (256,1,1), TileShape 16x128x256,
warp 16x16, Stages 2. Identical on both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960;
smem.ld 31,744; vmem.acp.commit.grp 19,456. Registers 102 -> 98.

Q1. WHY IS THE NATIVE FORM SLOWER, mechanically? Not "it costs instructions" -- I have the deltas
    (v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944; v.and.i +64,512; v.fma.f16 +36,864;
    tsm.st +71,680; Shared Load +4,608; cp.async's own smem writes -9,216; scalar ~+150K; ~+699K total on ~4.4M).
    What I want is the STRUCTURAL reason, and specifically whether the placement is the problem rather than the
    volume: the decode sits between a per-thread cp_async_wait and the CTA-wide __syncthreads that publishes the
    stage, so every warp in the CTA waits for the slowest decoding warp, and only 128 of the 256 threads decode
    (one per column of Scale_TileN=128) while the other 128 idle at the barrier. Read packed_decode_stage and its
    two call sites in mma() and say whether that placement, the half-idle CTA, or the raw instruction volume best
    explains 2.59 us -- and what the cheapest experiment is that separates them. Also: is there a placement that
    would work (decode stage s+1 during stage s, warp specialisation, decoding in the epilogue of the previous
    iteration), or is the dependency structure genuinely serial here?

Q2. WHERE DO THE BANK CONFLICTS COME FROM? This is the part nobody has examined. The acu TSM table for the pinned
    pair, Current = packed, Baseline = the fp16-plane build:

      Shared Load                445,952 (+1.04%)   transactions 1,945,600 (+1.93%)   bank conflicts 278,528 (+0.00%)
      Shared Store                84,480 (+560%)    transactions   181,248 (+261%)    bank conflicts  81,920 (+900%)
      Shared Store From Global    14,976 (-38.10%)  transactions   516,096 (-12.50%)  bank conflicts       0 (+0.00%)
      Total                      545,408 (+14.02%)  transactions 2,642,944 (+3.70%)   bank conflicts 360,448 (+25.71%)

    So the BASELINE already has 278,528 shared-LOAD bank conflicts and 8,192 store conflicts, and the packed decode
    adds 73,728 store conflicts on top. THE LOAD CONFLICTS ARE THE BIG ONES AND THEY ARE NOT MINE -- they are in the
    shipped path. 278,528 against 445,952 load instructions is 0.62 conflicts per instruction, and 1,945,600 /
    445,952 = 4.36 transactions per load instruction.

    Find them. Which shared-memory READ in the mainloop produces them, with file:line: the A tile, the B tile, the
    scale tile, the zero tile, or the mma's own operand reads? Derive the bank map from the actual layouts rather
    than guessing -- SmemLayoutScale is tile_to_shape(Layout<Shape<_8,_1>>{}, (Scale_TileN, Scale_TileK, Stages)) and
    the scale is read through SmemCopyAtomScale into a fragment made by make_fragment_like(partition_fragment_B(...)),
    so the access pattern is the mma B operand's, not a linear sweep. Note the tree claims the scale fragment is
    deliberately k-broadcast, i.e. many lanes read the SAME address, and lanes sharing an address BROADCAST rather
    than conflict -- so count DISTINCT addresses per bank, not lanes per bank. There is a prior local analysis in
    fold_derivation/l94_native_scale_path.cu section (2) that claims 4-way conflicts on 4 banks for the fp16 scale
    read; check whether it is right and whether it accounts for 278,528.

    Then: for the PACKED decode specifically, which line produces the +73,728 store conflicts and the 1.83
    transactions per store, and what is the cheapest fix that does not break the invariant that a thread may only
    read shared bytes it copied itself (cp_async_wait is per-thread and the publishing __syncthreads comes after the
    decode)? A previous attempt to widen the store to 4 B by pairing two columns per thread violated exactly that
    invariant and had to be reverted.

    Finally: are the load conflicts worth attacking at all? 278,528 conflicts on a 34,191-cycle kernel across 128
    CTAs -- estimate the cycles they can plausibly cost and say whether this is a first-order term or noise.

FILES
  actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp   (mainloop, packed_decode_stage,
      partition_extra_inputs / partition_extra_mma_info, the four transform arms, SmemLayoutScale, SmemCopyAtomScale)
  actlize/include/cutlass/gguf_packed_scale.h
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/l94_native_scale_path.cu   (the prior bank analysis)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md      (the whole history)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/README.md

- **Thread ID:** `019fb896-c33f-7e20-bc3f-a295b51daf57`
- **Started / last event:** 2026-07-31 14:31 UTC → 2026-07-31 14:54 UTC
- **Working dir:** `/root/marlin_ppu/Kernels`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/07/31/rollout-2026-07-31T22-31-55-019fb896-c33f-7e20-bc3f-a295b51daf57.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "118865063de0f945630429afa171fe644e548a61", "branch": "ppu_dev", "repository_url": "git@github.com:DrXuQian/Kernels.git"}`

---

## User · 2026-07-31 14:32 UTC

READ THE CODE. Full filesystem read access; both repos are here. Say "I cannot tell from the tree" rather than
inventing. Two questions, and the second is the one I care more about because nobody has ever looked at it.

REPOS
  /root/marlin_ppu/Kernels                      branch ppu_dev
  /root/marlin_ppu/Kernels/third_party/actlize  branch ppu-w4a16-dev

CONTEXT. Mixed-input W4A16 grouped GEMM (MoE, batch-1 decode) on the PPU (T-Head ZW810, SM80-like, 72 CUs, 256 KB
shared per CU, HBM peak ~2766 GB/s). Weights GGUF Q4_K, gs=32. Two ways to feed the per-group scale/zero:
  BASELINE  an offline step pre-multiplies into two fp16 planes (scale, zero: 4 B per group per column), cp.async'd
            straight into shared memory. 20.11 us.
  PACKED    the gguf's own 16 B unit per (superblock, column) -- fp16 d, fp16 dmin, sixteen 6-bit codes -- is
            cp.async'd in raw (2 B per group per column, half the traffic) and decoded on device into the SAME two
            fp16 shared planes, one thread per column, between cp_async_wait and __syncthreads. 22.70 us.
Both numerically correct now. Same kernel, pinned fingerprint grid (8,16,1) block (256,1,1), TileShape 16x128x256,
warp 16x16, Stages 2. Identical on both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960;
smem.ld 31,744; vmem.acp.commit.grp 19,456. Registers 102 -> 98.

Q1. WHY IS THE NATIVE FORM SLOWER, mechanically? Not "it costs instructions" -- I have the deltas
    (v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944; v.and.i +64,512; v.fma.f16 +36,864;
    tsm.st +71,680; Shared Load +4,608; cp.async's own smem writes -9,216; scalar ~+150K; ~+699K total on ~4.4M).
    What I want is the STRUCTURAL reason, and specifically whether the placement is the problem rather than the
    volume: the decode sits between a per-thread cp_async_wait and the CTA-wide __syncthreads that publishes the
    stage, so every warp in the CTA waits for the slowest decoding warp, and only 128 of the 256 threads decode
    (one per column of Scale_TileN=128) while the other 128 idle at the barrier. Read packed_decode_stage and its
    two call sites in mma() and say whether that placement, the half-idle CTA, or the raw instruction volume best
    explains 2.59 us -- and what the cheapest experiment is that separates them. Also: is there a placement that
    would work (decode stage s+1 during stage s, warp specialisation, decoding in the epilogue of the previous
    iteration), or is the dependency structure genuinely serial here?

Q2. WHERE DO THE BANK CONFLICTS COME FROM? This is the part nobody has examined. The acu TSM table for the pinned
    pair, Current = packed, Baseline = the fp16-plane build:

      Shared Load                445,952 (+1.04%)   transactions 1,945,600 (+1.93%)   bank conflicts 278,528 (+0.00%)
      Shared Store                84,480 (+560%)    transactions   181,248 (+261%)    bank conflicts  81,920 (+900%)
      Shared Store From Global    14,976 (-38.10%)  transactions   516,096 (-12.50%)  bank conflicts       0 (+0.00%)
      Total                      545,408 (+14.02%)  transactions 2,642,944 (+3.70%)   bank conflicts 360,448 (+25.71%)

    So the BASELINE already has 278,528 shared-LOAD bank conflicts and 8,192 store conflicts, and the packed decode
    adds 73,728 store conflicts on top. THE LOAD CONFLICTS ARE THE BIG ONES AND THEY ARE NOT MINE -- they are in the
    shipped path. 278,528 against 445,952 load instructions is 0.62 conflicts per instruction, and 1,945,600 /
    445,952 = 4.36 transactions per load instruction.

    Find them. Which shared-memory READ in the mainloop produces them, with file:line: the A tile, the B tile, the
    scale tile, the zero tile, or the mma's own operand reads? Derive the bank map from the actual layouts rather
    than guessing -- SmemLayoutScale is tile_to_shape(Layout<Shape<_8,_1>>{}, (Scale_TileN, Scale_TileK, Stages)) and
    the scale is read through SmemCopyAtomScale into a fragment made by make_fragment_like(partition_fragment_B(...)),
    so the access pattern is the mma B operand's, not a linear sweep. Note the tree claims the scale fragment is
    deliberately k-broadcast, i.e. many lanes read the SAME address, and lanes sharing an address BROADCAST rather
    than conflict -- so count DISTINCT addresses per bank, not lanes per bank. There is a prior local analysis in
    fold_derivation/l94_native_scale_path.cu section (2) that claims 4-way conflicts on 4 banks for the fp16 scale
    read; check whether it is right and whether it accounts for 278,528.

    Then: for the PACKED decode specifically, which line produces the +73,728 store conflicts and the 1.83
    transactions per store, and what is the cheapest fix that does not break the invariant that a thread may only
    read shared bytes it copied itself (cp_async_wait is per-thread and the publishing __syncthreads comes after the
    decode)? A previous attempt to widen the store to 4 B by pairing two columns per thread violated exactly that
    invariant and had to be reverted.

    Finally: are the load conflicts worth attacking at all? 278,528 conflicts on a 34,191-cycle kernel across 128
    CTAs -- estimate the cycles they can plausibly cost and say whether this is a first-order term or noise.

FILES
  actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp   (mainloop, packed_decode_stage,
      partition_extra_inputs / partition_extra_mma_info, the four transform arms, SmemLayoutScale, SmemCopyAtomScale)
  actlize/include/cutlass/gguf_packed_scale.h
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/l94_native_scale_path.cu   (the prior bank analysis)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md      (the whole history)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/README.md

## Assistant · 2026-07-31 14:32 UTC

I’ll trace the exact producer/consumer layouts and call order in the mixed-input mainloop, then reconcile the derived bank maps against the profiler counts and the prior `l94` analysis. I’ll keep observed facts separate from estimates; where the tree does not determine a hardware detail, I’ll say so.

<details><summary>4 tool call(s)</summary>

- `exec: const p = await tools.update_plan({plan:[ {step:"Inspect the mixed-input mainloop, packed decoder, layouts, copy atoms, and both decode call sites",status:"in_progress"}, {step:"Reconstruct shared-load and packed-store bank maps from the ac …`
- `exec: const r = await tools.exec_command({ cmd: "pwd && git branch --show-current && git -C third_party/actlize branch --show-current && rg -n \"packed_decode_stage|SmemLayoutScale|SmemCopyAtomScale|partition_extra_inputs|partition_extra_mma_info …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1,540p'; nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistag …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '380,530p'; nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multist …`

</details>

## Assistant · 2026-07-31 14:33 UTC

The code confirms the key synchronization fact: decode is inside the stage-publication critical path at both sites, and the ownership restriction is real because the raw copy is one 16-byte unit per column per copying thread. I’m now deriving which dynamic shared operations can produce the exact conflict totals rather than accepting the older comments’ attribution.

<details><summary>20 tool call(s)</summary>

- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '840,1010p'; nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multis …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1020,1080p'; nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multi …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"SmemLayoutAtomScale|ppu_mma_aiu_multistage_mixed_input|TileShape.*16.*128.*256|16x128|ScaleTileShape|Scale_TileK\" third_party/actlize/include general/w4a16_gemm/cutlass_w4a16 -g '*.{h,hpp, …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/l89_scale_read.cu | sed -n '1,280p'; nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/l90_scale_tv.cu | sed -n '1,320p'; nl -ba genera …`
- `exec: const r = await tools.exec_command({ cmd: "find . -type f \\( -name '*.report' -o -name '*.csv' -o -name '*acu*' -o -name '*.log' \\) | head -n 300; rg -n \"445,952|445952|278,528|278528|1,945,600|1945600|84,480|84480|73,728|73728|34,191|34 …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md | sed -n '1,120p'; nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md | sed -n '190,290p …`
- `exec: const r = await tools.exec_command({ cmd: "command -v nvcc || true; ls -l general/w4a16_gemm/cutlass_w4a16/stub_inc; ls -l /tmp/l94 /tmp/l95 2>/dev/null || true; git status --short; git -C third_party/actlize status --short", workdir: "/roo …`
- `exec: const r = await tools.exec_command({ cmd: "git -C third_party/actlize diff -- include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp; git diff --submodule=short -- third_party/actlize; find general/w4a16_gemm/cutlass_w4a16 - …`
- `exec: const r = await tools.exec_command({ cmd: "nvcc -std=c++17 -x cu -arch=sm_80 -w -I fold_derivation/stub_inc -I ../../../../third_party/actlize/include -I .. -I . -o /tmp/l94 fold_derivation/l94_native_scale_path.cu && /tmp/l94", workdir: "/ …`
- `exec: const r = await tools.exec_command({ cmd: "realpath ../../../third_party/actlize/include; nvcc -std=c++17 -x cu -arch=sm_80 -w -I fold_derivation/stub_inc -I ../../../third_party/actlize/include -I .. -I . -o /tmp/l94 fold_derivation/l94_na …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba fold_derivation/syntax_check.sh | sed -n '1,260p'; nl -ba fold_derivation/stub_inc/hggc_fp16.h | sed -n '1,120p'", workdir: "/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16", yield …`
- `exec: const r = await tools.exec_command({ cmd: "nvcc -std=c++17 -arch=sm_80 --expt-relaxed-constexpr -D__HGGCCC__ -I fold_derivation/stub_inc -I ../../../third_party/actlize/include -I ../../../third_party/actlize/tools/util/include -I . -cuda - …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/HANDOFF_packed_scale.md | sed -n '120,205p'; nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '1320,1355p'; rg -n \"S …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"tsm\\.ld|smem\\.ld|DefaultCopy\" third_party/actlize/include/cute/atom third_party/actlize/include/cutlass/arch third_party/actlize/include/cute/arch -g '*.{h,hpp,cuh}' | head -n 300; rg -n …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/l94_native_scale_path.cu | sed -n '254,420p'; nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.h …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/TODO.md | sed -n '1230,1285p'; rg -n \"26,624|26624|252,|251,|139,264|139264|272,384|272384|168,960|168960|31,744|31744\" general/w4a16_gemm/ …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1528,1750p' | rg -n \"PPU_B_DEQUANT_NOP|Utilities to transform B|copy\\(smem_tiled_copy_S …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/README.md | sed -n '280,350p'; nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md | sed -n '510,575p'; nl -ba gener …`
- `exec: const r = await tools.exec_command({ cmd: "awk 'BEGIN {baseL=441344; packL=445952; baseT=1908736; packT=1945600; conf=278528; cta=128; warp=8; cu=72; cyc=34191; dcyc=38588-34191; addi=699000; scale=baseL-168960; printf(\"scale_loads=%d\\nra …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"cp_async_wait\" third_party/actlize/include/cute third_party/actlize/include/cutlass | head -n 100; rg -n \"PER THREAD|per-thread|thread.*cp_async_wait|wait_group\" third_party/actlize/incl …`

</details>

## Assistant · 2026-07-31 14:48 UTC

The main structural surprise is in the call chain, not the decoder comment: `mma()` passes `thread_idx % 128` into `partition_extra_inputs`, so on this pinned shape all 256 threads issue the 128-thread raw copy map. Each column is copied twice—by threads `n` and `n+128`. That means the second 128 threads are valid owners of the same raw unit, and the ownership rule does not force them to be idle. This gives a very cheap, correctness-preserving half-idle ablation.

<details><summary>12 tool call(s)</summary>

- `exec: const r = await tools.exec_command({ cmd: "nvcc -std=c++17 -x cu -arch=sm_80 -w -D__HGGCCC__ --expt-relaxed-constexpr -I fold_derivation/stub_inc -I ../../../third_party/actlize/include -I ../../../third_party/actlize/tools/util/include -I  …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '150,235p'; nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multist …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1102,1142p'; git -C third_party/actlize diff --stat; git -C third_party/actlize diff -- i …`
- `exec: const r = await tools.exec_command({ cmd: "git status --short; git -C third_party/actlize status --short; git -C third_party/actlize log -1 --oneline --decorate; git log -1 --oneline --decorate", workdir: "/root/marlin_ppu/Kernels", yield_t …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1140,1162p'; rg -n \"clear\\(t.*s|clear\\(.*smem|= .*;.*smem\" third_party/actlize/includ …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/l97_packed_thread_partition.cu | sed -n '1,280p'; rg -n \"l97|redundantly copy|thread 128\" general/w4a16_gemm/cutlass_w4a16/fold_derivation/ …`
- `exec: const r = await tools.exec_command({ cmd: "rg --files general/w4a16_gemm/cutlass_w4a16/fold_derivation | rg 'l97|97'; git show --stat --oneline HEAD; git show --format=fuller --name-status HEAD", workdir: "/root/marlin_ppu/Kernels", yield_t …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba general/w4a16_gemm/cutlass_w4a16/fold_derivation/l97_packed_g2s_threads.cu | sed -n '1,220p'; git -C third_party/actlize show --stat --oneline HEAD; git -C third_party/actlize show --format= …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"static auto make_scale_fragment|make_fragment_like<ElementScale>|partition_fragment_B\\(sS|make_tiled_copy_B\\(SmemCopyAtomScale|copy\\(smem_tiled_copy_S, tCsS|sS\\(n, cute::Int<G>|sZ\\(n,  …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1478,1520p'; nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multi …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"constexpr bool FINE|constexpr bool kPfOk|if constexpr \\(kPfOk\\)|const int sk = read_stage|copy\\(smem_tiled_copy_S, tCsZ\" third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_ …`
- `exec: const p = await tools.update_plan({explanation:"Traced the current call graph and layouts, compiled and ran l94/l95, reconciled the layout maps with the pinned ACU totals, and found that the raw copy map is instantiated twice via the caller …`

</details>

## Assistant · 2026-07-31 14:54 UTC

At the current heads—Kernels `cbc472a`, actlize `67bb52e9`—the dominant load conflicts are the scale and zero reloads, while the packed regression is decode/store work placed directly on the stage-publication critical path. The half-idle CTA is real during decode, but the tree contains a cheap way to test it that has been overlooked.

## Q1 — Why packed is slower

The serialized chain is exactly:

```text
raw cp.async → per-thread wait → decode → fp16 shared stores → CTA sync → scale/zero consumers
```

Both call sites place it literally between wait and publication:

- Prologue: [ppu_mma_aiu_multistage_mixed_input.hpp:892](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:892)
- Steady state: [ppu_mma_aiu_multistage_mixed_input.hpp:924](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:924)

Only threads 0–127 enter the decoder loop at [line 1308](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1308). Thus four warps do the entire decode and four reach `__syncthreads()` almost immediately. The slowest decoding warp determines publication latency.

The best mechanical explanation is therefore not “placement versus volume” as two alternatives:

- The ~699K extra instructions are the payload and are quantitatively large enough to explain the regression: `699K/72 ≈ 9,708` extra dynamic instructions per CU against a 4,397-cycle increase, or about 2.2 added instructions/CU-cycle.
- Placement makes that payload exposed rather than overlappable.
- The half-idle CTA is an amplification of that placement; it does not add instructions. In fact, four full decoder warps are more issue-efficient than spreading the same lane work sparsely over eight warps.

So my ranking is: **decode plus explicit-store volume on a forced critical path**, with the half-idle barrier making its latency visible. The present A/B cannot tell how much belongs to each. The existing NOP decomposition at [lines 1321–1328](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1321) still needs to be run:

- `P − N`: decode arithmetic.
- `N − B`: raw transport, explicit stores, and critical-slot/barrier effects.

### The cheapest half-idle experiment

There are actually **two raw-copy owners per column** in the current tree.

For this shape, `(Scale_TileN/8) * Scale_TileK = 16*8 = 128`, and `mma()` passes `thread_idx % 128` into `partition_extra_inputs` at [line 715](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:715). The raw copy is also modulo its 128-thread layout at [line 1122](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1122).

Therefore threads `n` and `n+128` both cp.async the same column into the same location. Each thread’s wait covers a copy it issued itself. The ownership invariant permits both to read that unit.

The clean experiment is:

- Threads 0–127 decode groups 0–3 for column `thread_idx`.
- Threads 128–255 decode groups 4–7 for column `thread_idx-128`.

This gives all eight warps four groups each instead of four warps eight groups each. It preserves:

- The number of per-group decode operations.
- The total fp16 stores.
- The bank-conflict count.
- Correct ownership and publication ordering.

It adds only a second raw 16-byte shared read and header setup per column pair—small compared with the group arithmetic. If this improves materially, slowest-warp/barrier placement is important. If it does not, aggregate instruction/pipe demand is dominant. This is a cleaner placement test than moving the whole wait.

One related finding: the new inner modulo and `l97` comment describe an out-of-range call, but the actual caller already applied the modulo at line 715. `l97` tested unmodded `get_slice(t)` directly, not the call path in `mma()`. In the current call tree, the inner modulo is redundant; the second 128 threads were already duplicate owners.

### Can decode overlap stage s?

The dependency is serial only from raw arrival through publication:

```text
raw ready → decode → stores complete → CTA barrier → consumers
```

It is not necessary for the whole CTA to do no useful stage-s work during that interval. The next raw stage is issued at `k_block == 0`, while decode waits until the last `k_block`. Because stages are double-buffered, these are structurally possible:

- Decode `s+1` while non-owner warps finish compute on `s`.
- Issue the last stage-s MMA before decode/publication.
- Temporally specialize four warps as producers, then reunite at the existing barrier.

The complications are that raw scale, A, and other cp.async operations share commit/wait groups, and all eight warps own MMA N work—there are no spare dedicated producer warps. A true dedicated-warp design therefore requires a larger CTA or a different MMA partition. The duplicate-owner group split above obtains the useful half-idle test without that redesign.

“Epilogue of the previous iteration” works only if that means after an earlier stage-s MMA issue. The kernel epilogue after the entire K loop is too late.

## Q2 — Where the load conflicts come from

The dominant source is the **FINE scale and zero reload pair**:

- Scale: [line 1732](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1732)
- Zero: [line 1733](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1733)

For this pinned shape `Scale_TileK=8 > K_BLOCK_MAX=4`, so the coarse reads at lines 1512/1516 are not the active path.

The scale fragment is indeed shaped from B’s operand partition at [line 1185](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1185), and copied with `make_tiled_copy_B` at [line 1398](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1398).

The alternatives are:

- A shared read: [line 933](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:933), using `tsm.ld.swzl`.
- B shared read: [line 1493](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1493), also swizzled.
- MMA itself: [line 973](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:973), consuming registers, not shared memory.

The count decomposition is almost exact:

```text
441,344 total baseline Shared Loads
−168,960 A/B tsm.ld.swzl
=272,384 scalar scale/zero loads
```

Then:

```text
278,528 conflicts / 272,384 scale/zero loads = 1.0226
```

So essentially every scalar scale/zero load is reported conflicted. The aggregate table cannot assign the remaining 6,144 events between A and B; **I cannot tell from the tree** without per-PC counters.

### Actual scale bank map

The storage layout is `(128,8,2):(1,128,1024)` from [lines 417–419](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:417).

For the first distinct source value in warp 0, the actual B-copy TV layout gives, in half elements:

```text
h(t) = 256*(t mod 4) + floor(t/4) + C
```

where `C` is the group/stage base. Since a bank word is 4 bytes or two halves:

```text
word(t) = floor(h(t)/2)
bank(t) = word(t) mod 32
```

The 256-half thread stride is 128 bank words, exactly four 128-byte bank periods. Therefore it vanishes modulo 32. For `floor(t/4)=0..7`, the lanes land on banks:

```text
0,0,1,1,2,2,3,3
```

For each bank there are four distinct word addresses, corresponding to the four `t mod 4` values. Thus the result is genuinely **4 distinct bank words on each of 4 banks**. The second distinct column per lane is shifted by eight halves and repeats the same 4-way pattern on the next four banks.

Group and stage strides are multiples of the bank period, so every group, both planes, and every stage repeat it. The zero plane has the same layout and access map.

I compiled and ran `l94`; it reports `4-way on 4 banks (16 addrs)`. I also compiled `l95`; its type-identity assertions pass, confirming that the stub’s scale layout, copy atom, B TV layout, and thread layout match the collective. See [l94:115](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/l94_native_scale_path.cu:115) and [l95:56](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/l95_stub_vs_real.cu:56).

The map also reconciles the transaction total:

```text
272,384 scale/zero loads × 4 transactions = 1,089,536
remaining A/B transactions                =   819,200
819,200 / 168,960 swizzled loads           =      4.85
total                                      = 1,908,736
```

What `l94` does **not** establish is ACU’s precise definition of “bank conflicts.” Four banks with four distinct words would be 12 excess bank services under one common definition, not 1.02 counter increments. The data suggest ACU counts a conflicted instruction/replay event rather than every extra word. **I cannot tell from the tree** exactly how that counter is defined.

The packed raw decoder read at [line 1313](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1313) is not the culprit:

```text
+4,608 loads
+36,864 transactions = exactly 8 transactions/load
+0 bank conflicts
```

Thus `l94` is right that the 16-byte raw arrangement is conflict-free. But current F′ decodes it into the old fp16 planes, so the consumers still incur the old conflicts. The old statement that native packing “removes the conflicts” applied to the read-side register-decode design, not this staged-decode design.

### Packed store conflicts

They come from both assignments:

- Scale store: [line 1354](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1354)
- Zero store: [line 1355](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1355)

At fixed group/stage, `n` is contiguous in fp16. A warp’s 32 lanes store 32 adjacent 2-byte values, occupying only 16 bank words. Each bank receives two different halfword stores, which cannot broadcast.

The count is exact:

```text
4 decoder warps
× 8 groups
× 2 planes
× 9 decode passes
× 128 CTAs
= 73,728 conflicted store instructions
```

That is the observed increment. The pre-existing 8,192 store conflicts are most plausibly the explicit scale/zero clears at lines 1127 and 1152, but the aggregate table does not prove their per-PC attribution.

The cheapest ownership-safe store fix is not adjacent-column pairing. It is to store the already-computed same-column `(scale, zero)` pair as one 32-bit word in an interleaved decoded tile, then expose even/odd halfword views to the existing scale and zero consumers. Every thread derives both halves from its own raw unit, and 32 consecutive 4-byte stores use all 32 banks once.

That changes the physical decoded layout, so the read bank probe must be rerun; it is not a free patch. If the physical two-plane layout must remain exactly unchanged, there is no cheap 4-byte store available: the two owned values are in different arrays, while the adjacent value in either array belongs to another column. Then the choices really are pairing the raw copies too, or adding a pre-decode barrier, neither attractive for a roughly 0.6% ceiling.

## Are the load conflicts worth attacking?

Per warp:

```text
278,528 / (128 CTAs × 8 warps) = 272 conflict events
```

The scale path executes about 266 scalar loads per warp. Depending on whether ACU’s event represents one replay or the full 4-way serialization, removing the conflicts plausibly saves roughly:

```text
272 to 3×266 = 272–798 bank-service cycles per warp path
```

Against 34,191 cycles, that is approximately **0.8–2.3%**, or **0.16–0.47 µs** at the measured ~1.70 GHz, before latency hiding. The absolute aggregate ceiling—`278,528/72 = 3,868` cycles/CU—is 11.3%, but it assumes every event serializes on one CU-wide pipe with no overlap; the reported 28% shared-memory peak makes that an unrealistically loose ceiling.

So they are not pure noise, but they are a **second-order, low-single-digit target**, not the explanation for the packed regression. They are identical in both builds and therefore explain none of the 2.59 µs delta. I would first run the NOP triple and the duplicate-owner group split; only then pursue a read-layout change that removes the conflicts without introducing the non-power-of-two address arithmetic that made `PPU_SCALE_PAD` lose.
