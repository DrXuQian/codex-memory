# Resume brief: Resume on /root/marlin_ppu/quactlize (branch `develop`). `git pull --recurse-submodules`, then read `.coord/INBOX.md` items **025 and 026** — your STATUS says inbox-consumed: 024 and both are newer. Keep STATUS current (`inbox-consumed`, `updated-at`).

**026 UNBLOCKS THE NINE PROMOTIONS.** The user pasted the ppu001 logs verbatim; every one is green:

    pytest_cpu_arm.log        16 passed
    pytest_full.log          210 passed,  22 skipped
    fully_quantized_Q2_K.log   5 passed,  20 skipped     (same for Q3_K, Q4_K, Q5_K, Q6_K)
    dense_python_oracle.log    5 passed
    device_vs_cpu_arm.log      1 passed

Five per format with twenty skipped is five tests × five formats, the format gate letting exactly one format's five through: the dense oracle, the grouped oracle, the merge premise, and both BC GEMV arms, each requiring its planted fault to fail first. That is the evidence you have been holding for.

So promote **fully_quantized/dense Q2..Q6 and fully_quantized/grouped Q2, Q3, Q5, Q6** — nine cells, taking the k-quant matrix to 60/60. Conditions unchanged from 019: say what the NEW evidence is rather than deleting the old PARTIAL reason; GPTQ stays; and state plainly that these cells need PPU_PACKED_SCALE=1 plus a per-format PPU_PACKED_FORMAT and five separate builds, which is a different claim from "ships".

ONE CAVEAT I would rather hand you than have you find: those logs are FIVE tests per format, not six. The BC dequant-all oracle (76d6038) is newer than them. `tools/failures.sh` now marks logs older than HEAD, which it did not when these were read. The nine promotions rest on the dense and grouped oracles and are unaffected, but do not let any note imply the BC inverse is device-verified — it is not yet.

**025 IS THE OPEN QUESTION** and it is the sharp one left on the layout work: does ONE TENSOR's optimal (F, TK) move with seqlen? Your dense and MoE numbers are two different OPERATORS, not one tensor at two token counts — but a dense layer's weight is read at M=1 during decode and at large M during prefill, from the same bytes. The cheap version may end it outright: decode is ALU-bound here (the MoE table has int1/int2/int4 all at ~16.0 µs across a 2.5× byte range), so if M=1 is insensitive to the arrangement the choice is decided entirely by the large-M end. One dense weight, one format, sweep (F, TK) at M = 1, 8, 64, 512, 2048; report whether the winner moves and, if it does, at which M. That crossover is the number `DENSE_CROSSOVER_ROWS` needs anyway — its own comment admits it is one measurement at M=2048 turned into a boundary.

Also since you last looked: `PlacedArrangement` in quactlize/formats.py now records (bits, fold, tile_k, high_fold) PER TENSOR — the user's resolution of dense-vs-MoE is that a dense layer's weight and an expert's weight are different tensors, so each is arranged for the operator that reads it. `tools/pack_gguf.py` exists and produces artifacts from a real GGUF with that record in a manifest.

I am taking the xplane token change (`xp{bits}f1` at F=1 and TK<=256, full form otherwise, constructor rejecting F=1/TK>256) and am NOT touching xplane_hi's delivery fields, per your reading.

Commit and push as you go, no Co-Authored-By trailer.

- **Thread ID:** `019fcad5-c05a-7aa3-ae27-a589d5ce1804`
- **Started / last event:** 2026-08-04 03:33 UTC → 2026-08-04 08:02 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/04/rollout-2026-08-04T11-33-53-019fcad5-c05a-7aa3-ae27-a589d5ce1804.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "e985d020e1ff5ffbe1d4af2f1e626e115c5972b6", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-04_019fcad5_Resume-on-root-marlin_ppu-quactlize-branch-develop.md](../transcripts/2026-08/2026-08-04_019fcad5_Resume-on-root-marlin_ppu-quactlize-branch-develop.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Resume on /root/marlin_ppu/quactlize (branch `develop`). `git pull --recurse-submodules`, then read `.coord/INBOX.md` items **025 and 026** — your STATUS says inbox-consumed: 024 and both are newer. Keep STATUS current (`inbox-consumed`, `updated-at`).

**026 UNBLOCKS THE NINE PROMOTIONS.** The user pasted the ppu001 logs verbatim; every one is green:

    pytest_cpu_arm.log        16 passed
    pytest_full.log          210 passed,  22 skipped
    fully_quantized_Q2_K.log   5 passed,  20 skipped     (same for Q3_K, Q4_K, Q5_K, Q6_K)
    dense_python_oracle.log    5 passed
    device_vs_cpu_arm.log      1 passed

Five per format with twenty skipped is five tests × five formats, the format gate letting exactly one format's five through: the dense oracle, the grouped oracle, the merge premise, and both BC GEMV arms, each requiring its planted fault to fail first. That is the evidence you have been holding for.

So promote **fully_quantized/dense Q2..Q6 and fully_quantized/grouped Q2, Q3, Q5, Q6** — nine cells, taking the k-quant matrix to 60/60. Conditions unchanged from 019: say what the NEW evidence is rather than deleting the old PARTIAL reason; GPTQ stays; and state plainly that these cells need PPU_PACKED_SCALE=1 plus a per-format PPU_PACKED_FORMAT and five separate builds, which is a different claim from "ships".

ONE CAVEAT I would rather hand you than have you find: those logs are FIVE tests per format, not six. The BC dequant-all oracle (76d6038) is newer than them. `tools/failures.sh` now marks logs older than HEAD, which it did not when these were read. The nine promotions rest on the dense and grouped oracles and are unaffected, but do not let any note imply the BC inverse is device-verified — it is not yet.

**025 IS THE OPEN QUESTION** and it is the sharp one left on the layout work: does ONE TENSOR's optimal (F, TK) move with seqlen? Your dense and MoE numbers are two different OPERATORS, not one tensor at two token counts — but a dense layer's weight is read at M=1 during decode and at large M during prefill, from the same bytes. The cheap version may end it outright: decode is ALU-bound here (the MoE table has int1/int2/int4 all at ~16.0 µs across a 2.5× byte range), so if M=1 is insensitive to the arrangement the choice is decided entirely by the large-M end. One dense weight, one format, sweep (F, TK) at M = 1, 8, 64, 512, 2048; report whether the winner moves and, if it does, at which M. That crossover is the number `DENSE_CROSSOVER_ROWS` needs anyway — its own comment admits it is one measurement at M=2048 turned into a boundary.

Also since you last looked: `PlacedArrangement` in quactlize/formats.py now records (bits, fold, tile_k, high_fold) PER TENSOR — the user's resolution of dense-vs-MoE is that a dense layer's weight and an expert's weight are different tensors, so each is arranged for the operator that reads it. `tools/pack_gguf.py` exists and produces artifacts from a real GGUF with that record in a manifest.

I am taking the xplane token change (`xp{bits}f1` at F=1 and TK<=256, full form otherwise, constructor rejecting F=1/TK>256) and am NOT touching xplane_hi's delivery fields, per your reading.

Commit and push as you go, no Co-Authored-By trailer.

## Follow-up requests (chronological)

2. (2026-08-04 03:57 UTC) Continuing the same thread deliberately — I had been starting a fresh session each time, which made you rebuild context from zero four times today. That was my error; from now on I continue threads. Your `blocked-on` line is now half clear: I landed the Claude-owned side in `d191e9d`. `formats.FUSED_NATIVE_SCALE` is all five k-quants, `ci/registry.py` declares `NATIVE_P` against the two new oracles, and the two consistency assertions pass — 49/49 in the schemes+formats files. Filling that set also MOVED THE ROUTING, as this repo had already recorded happening once: two expectations in `test_transient_planes_are_allowed` depended on Q3_K not being supported, so they are re-pinned on a format  …
3. (2026-08-04 05:00 UTC) Read .coord/INBOX.md 029 and 030 (both written after your last turn; STATUS still says inbox-consumed 028), then do the work below. Update STATUS when you reach a checkpoint. FIRST, THE ORDERING THE USER JUST SET. The ppu001 box sweep must NOT be requested until the dense AND MoE sweep options are BOTH ready. A sweep that covers only the options that happen to compile today would report a winner over a truncated space and we would take it as the answer. So 029 comes before asking for any box time, and the box request I write afterwards must enumerate the full option set it covers. 029 is the one I want answered first, and it is a question, not a task. I am carrying a measurement labelled den …
4. (2026-08-04 05:48 UTC) Read .coord/INBOX.md 032 and answer it. Short version: the sweep with stages as a real axis is 4521 kernel instantiations per operator (3759 after the free de-duplication), which nobody will run. The user wants you and me to derive the PRUNING RULES independently and then reconcile, so 032 gives you the sizing evidence and deliberately none of my rules. I am writing mine in parallel and will publish as 033 only after yours lands. What I want back is the RULES, not the surviving list -- each with the argument for why it cannot lose the winner, and marked as measured or believed. "I believe deep stages dominate here but have not measured it" is usable; "deep stages dominate" is not. Please add …
5. (2026-08-04 07:24 UTC) Four INBOX items have landed since your STATUS's inbox-consumed: 034. Please read 035, 036, 037, 038 and work them in this order, updating STATUS as you go. 036 FIRST -- it is what your own blocked-on names. Pin the ragged MoE distribution. The sharp part: compact A's capacity IS per-expert Mmax, so the distribution decides which compact builds are reachable at all. The existing mode-2 generator gives Mmax ~= 3*Rows + 36 (about 420 at Rows=128), which capacities 1/2/4 come nowhere near -- so the 5562 compact builds look like they apply only to the decode column, and the 9163/operator figure may be an overcount. And mode 3 sets every touched expert to exactly ONE row, so the fixture cannot cu …

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×23
- `/root/marlin_ppu/quactlize/dev/fold_derivation/SWEEP_032_PRUNING_CODEX.md` ×18
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp` ×11
- `/root/marlin_ppu/quactlize/benchmarks/size_sweep.cpp` ×9
- `/root/marlin_ppu/quactlize/ci/local_gates.py` ×7
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_layout.cu` ×6
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_tactic_space.hpp` ×6
- `/root/marlin_ppu/quactlize/dev/fold_derivation/SWEEP_025_OPTIONS.md` ×6
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp` ×6
- `/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh` ×5
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×5
- `/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp` ×5
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.h` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.cpp` ×3
- `/root/marlin_ppu/quactlize/benchmarks/workloads.py` ×3
- `/root/marlin_ppu/quactlize/quactlize/include/gemv_lowbit/gemv_rt.hpp` ×3
- `/root/marlin_ppu/quactlize/.coord/BOX.md` ×2
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l107_moe_router_fixture.cu` ×2
- `/root/marlin_ppu/quactlize/benchmarks/moe_router_fixture.hpp` ×2
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_moe_bench.cu` ×2
- `/root/marlin_ppu/quactlize/docs/PACKED_ABI.md` ×2
- `/root/marlin_ppu/quactlize/benchmarks/emit_dense_configs.cpp` ×2
- `/root/marlin_ppu/quactlize/quactlize/schemes.py` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/fold_traits.hpp` ×1
- `/root/marlin_ppu/quactlize/tests/test_fpA_kquant_dense.cu` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/emit_tactic_space.cpp` ×1
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp` ×1
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_fold.hpp` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l106_compact_a_rows.cu` ×1
- `/root/marlin_ppu/quactlize/build.sh` ×1
- `/root/marlin_ppu/quactlize/benchmarks/test_moe_splitk_bench.cu` ×1
- `/root/marlin_ppu/quactlize/benchmarks/fixtures.py` ×1
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_backend.cu` ×1
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_backend.cu` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l108_rt_error_contract.cu` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l109_rt_hggc_parse.cu` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_ppu_packed.h` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_unit_pack.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_unit_pack.cpp` ×1
- `/root/marlin_ppu/quactlize/tests/test_gguf_routes.py` ×1
- `/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l110_unit_pack_abi.cu` ×1

## Last assistant conclusions

### 2026-08-04 05:33 UTC

029 is confirmed as **(a)**: the “dense” figures came from `moe_grouped_ppu` at `L=1`, not fpA dense.

Implemented and pushed:

- Added scheduler-level folding to fpA dense, including single-plane formats.
- Added shared dense/grouped tactic rules and a host emitter.
- Emitted 5,760 cells per operator: 1,286 reachable, 4,474 explicitly excluded.
- CI comparator reports `dense 5760 configs, grouped 5760 -> COINCIDE`.
- Documented the complete inventory in [SWEEP_025_OPTIONS.md](/root/marlin_ppu/quactlize/dev/fold_derivation/SWEEP_025_OPTIONS.md).
- Dense folded instantiations, grouped syntax gates, and the 600-unit MoE generator gate pass.
- STATUS now consumes through 031. Item 030 remains deferred.
- No ppu001 sweep was requested.

Pushed commits `6f79d60` and `ee9b66a` to `develop`.

### 2026-08-04 06:43 UTC

Rules are landed, reconciled with 034, committed, and pushed. No box sweep was requested.

The final pruning policy in [SWEEP_032_PRUNING_CODEX.md](/root/marlin_ppu/quactlize/dev/fold_derivation/SWEEP_032_PRUNING_CODEX.md) is:

- **Exact:** apply legality and resident-byte compatibility; scope 025 to one stored schema; retain every M/token point; fully cross stages `{2,3,4}`.
- **Measured protection:** do not prune TileK, TileM, TileN, or WarpN globally. TileM remains protected because it is the recorded ordinary-path smem lever and has interior winners. Compact A removes that smem dependency at small row counts, but not TileM’s grid/masking effects.
- **Measured + believed:** start with maximum legal WarpM and `TileN/WarpN=2`, with smaller-WarpM and ratio-1/4 guards. If a guard enters the winner’s confidence set, expand that entire stratum before declaring a winner.
- **Measured:** use interleaved repeated timings and confidence-set elimination; the recorded 13% run variation makes single-timing elimination invalid.
- **No deep-only rule:** stages 2, 3, and 4 remain crossed. The FA 25% occupancy result rules out assuming deep stages dominate, while measured s3/s4 GEMM winners rule out shallow-only selection. No shared-memory/blocks-per-CU cutoff is used.

Compact A capacities 1/2/4 were also implemented. The capacity is per-expert Mmax for MoE, not global tokens. Current raw inventory is 3,601 ordinary plus 5,562 compact builds—9,163/operator before guarded pruning.

Verification:

- Six dense/grouped capacity instantiations passed.
- Compact layout gate passed.
- Dense/grouped inventories still coincide: 5,760/5,760.
- Actlize pushed at `f1d7eb84`; superproject through `d506041`.
- [STATUS.md](/root/marlin_ppu/quactlize/.coord/STATUS.md) consumes 034 and records the remaining blockers.

### 2026-08-04 08:02 UTC

Completed all four items in order and pushed to `develop`; worktree is clean.

- 036: pinned `token-topk-hot16x4-wor-sm64-s44-v1`. Mmax is `1/2/3/12/239/447`, selecting compact capacities `1/2/4`, then ordinary. Undersized compact builds refuse execution.
- 038: device failures now return rc 41 without terminating the host; failed D2H leaves output untouched.
- 035: exported dense/grouped raw-GGUF unit producers plus allocation query, using one shared expert-aware loop for all five formats.
- 037: found and fixed the guard transcription. H1 now guards every TileM at its light/heavy N shapes; H2 uses per-stage A-smem extremes. Largest WarpM is derived from legal candidates. The generated i4/TK64 table moves from 93 to 99 configurations. The old s5 row was never a recorded winner—s4 was explicitly marked as the winner.

Relevant commits: `b8c9a0d`, `74de702`, `4b354f9`, `45f6870`.

Focused runtime, unit-packer, syntax, portability, overlay, and packed-unit tests pass. The aggregate runner was stopped only because its existing googletest clone hung. No ppu001 sweep was requested. STATUS now consumes through 038.
