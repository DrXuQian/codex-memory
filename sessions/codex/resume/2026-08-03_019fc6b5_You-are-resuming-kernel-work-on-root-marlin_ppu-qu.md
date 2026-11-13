# Resume brief: You are resuming kernel work on /root/marlin_ppu/quactlize (branch `develop`, remote `origin`). Your previous session ended after reporting "051 post-commit broad suite: 217 passed, 5 skipped". Four instruction batches have accumulated in the shared log since then and you have not read them.

FIRST: read the accumulated instructions.
    tail -320 /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Everything marked [FROM CLAUDE] after your 051 entry is for you. Keep appending your own numbered heartbeat lines there (`[HH:MM:SS] NNN <one line>`), at least every few minutes, so "working" is distinguishable from "stuck".

DIVISION OF LABOUR, set by the user and now strict:
  YOU write kernels and kernel-adjacent C++/CUDA only.
  CLAUDE owns all scaffolding: tests/, ci/, benchmarks/*.sh, pyproject.toml, docs/, quactlize/*.py.
  If you need a change in a scaffolding file, WRITE THE REQUEST IN THE LOG. Do not edit those files.
  Exception: schemes.py's matrix cells and notes remain yours.

Claude has just landed 70efc02, which fixed the box's 17 pytest failures on the scaffolding side. Pull before starting: `git pull` (your working tree may be behind).

YOUR QUEUE, in order:

(a) PROMOTE scale_first/dense from IMPLEMENTED to VALIDATED for Q2_K..Q6_K in schemes.py. The evidence exists: your dense oracle gate runs before the broad suite and returns 1 on failure, and the user's box run reached the broad suite, so the gate passed on ppu001. CONFIRM THIS FROM $OUT/dense_python_oracle.log ON THE BOX FIRST -- if the log does not show five passing cases and no skip, say so and do not promote. Update the note to state what the new evidence IS rather than silently deleting the old "test_fpA_kquant_dense is a self oracle" sentence. GPTQ_INT4_SYM stays IMPLEMENTED. The broad suite is not green, so do not let the wording imply it is.

(b) A REAL DEVICE DEFECT, newly isolated. gguf_prepass_ops.cpp:186 claims the device and CPU arms of gguf_vecdot are "interchangeable". The box falsifies it: identical bytes, relative error 8.0e-01 to 2.0e+00. The asymmetry is the clue -- through routes.matmul_native_gemv (gguf_vecdot_dense) the same five formats agree with official gguf to 1.5e-03; only gguf_vecdot disagrees, and its device call passes blocks_per_row=1:
        api->vecdot(bp, ts, xp16, op, int(rows), 1, int(qtype))
   while vecdot_rows_per_warp(rows, blocks_per_row) dispatches per format with values 2 (Q2/Q6), 2/4 (Q3), 2/8/4 (Q4), 2/8 (Q5). blocks_per_row == 1 may be a combination nothing has exercised. fp16 accumulation in a different order costs ~1e-2 at worst over 256 terms; order 1 is a wrong answer, not a precision effect. There is now a test for exactly this, tests/test_gguf_golden.py::test_device_vecdot_agrees_with_its_own_cpu_reference_arm, marked device_vs_cpu_arm. It is Claude's file -- if the 5e-2 bound needs changing, ask in the log, do not edit it.

(c) place_hi TILE-INVARIANCE. Read the [FROM CLAUDE - NARROW THE TASK AGAIN] entry in the log for the full statement. Short version: unfused_weight_dequantize.hpp's own comment establishes that the UNFOLDED low-plane placement is tile-invariant, verified byte-identical across 11 configurations in fold_derivation/l61 -- do not redo that. But your own Q6 finding (TK=256 wrong, TK=128 right, with F1=F2=1 in BOTH) is a direct counterexample for place_hi, which l61 never covered. Determine whether place_hi is tile-invariant at fixed (F1,F2), and if not, which quantity it depends on and whether that quantity is derived (like a per-plane delivery count) rather than the raw tile shape. This decides whether the on-disk artifact header records (bits, F1, F2) or a whole tactic. Plant a known difference and confirm the hash moves before reporting any "identical".

(d) fully_quantized/dense, Q4_K ONLY to begin with. It is the only one of the five with no prerequisite (single plane, 16-byte unit, already runs in grouped behind PPU_PACKED_SCALE=1); Q5 needs (c), Q2/Q3/Q6 additionally need the collective's hardcoded 16 B/unit generalised. The entry point is an INSTANTIATION at TileK=256 (gs=32 => Scale_TileK == kGroups == 8, what kPackedScaleOn tests) -- dense and grouped come from the same CollectiveBuilder selected by KernelScheduleType, so packed scale lives in the shared mainloop and is already reachable. Copy from the grouped side; do not write a second implementation. If you find the instantiation is format-independent and all five fall out together, say so rather than following the narrow plan.
   USER REQUIREMENT on this cell: KEEP THE SCALE CUTE-IFIED. quactlize/include/gguf_packed_unit.hpp has 0 cute references and 10 hand-written index/bit expressions, and it is exactly what FULLY_QUANTIZED reads. New addressing goes through a cute layout (pass the layout, as the 2-plane converter was done under task #15), not another set of shifts and masks. Do not let this expand into rewriting the existing ten unless that is genuinely the cheaper route -- and say which you did.
   Point its oracle at matmul_dequant_first through official gguf semantics FROM THE START, and plant a fault before reporting a pass. Also state plainly in the matrix note whether the cell is in the default build or behind a flag.

Commit and push as you go (no Co-Authored-By trailer). Report each step in the log.

- **Thread ID:** `019fc6b5-b373-79d3-8d0a-e3280248f5c3`
- **Started / last event:** 2026-08-03 08:20 UTC → 2026-08-03 10:47 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T16-20-24-019fc6b5-b373-79d3-8d0a-e3280248f5c3.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "70efc02f04300693d8773795e14900eaacf0e448", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-03_019fc6b5_You-are-resuming-kernel-work-on-root-marlin_ppu-qu.md](../transcripts/2026-08/2026-08-03_019fc6b5_You-are-resuming-kernel-work-on-root-marlin_ppu-qu.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

You are resuming kernel work on /root/marlin_ppu/quactlize (branch `develop`, remote `origin`). Your previous session ended after reporting "051 post-commit broad suite: 217 passed, 5 skipped". Four instruction batches have accumulated in the shared log since then and you have not read them.

FIRST: read the accumulated instructions.
    tail -320 /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Everything marked [FROM CLAUDE] after your 051 entry is for you. Keep appending your own numbered heartbeat lines there (`[HH:MM:SS] NNN <one line>`), at least every few minutes, so "working" is distinguishable from "stuck".

DIVISION OF LABOUR, set by the user and now strict:
  YOU write kernels and kernel-adjacent C++/CUDA only.
  CLAUDE owns all scaffolding: tests/, ci/, benchmarks/*.sh, pyproject.toml, docs/, quactlize/*.py.
  If you need a change in a scaffolding file, WRITE THE REQUEST IN THE LOG. Do not edit those files.
  Exception: schemes.py's matrix cells and notes remain yours.

Claude has just landed 70efc02, which fixed the box's 17 pytest failures on the scaffolding side. Pull before starting: `git pull` (your working tree may be behind).

YOUR QUEUE, in order:

(a) PROMOTE scale_first/dense from IMPLEMENTED to VALIDATED for Q2_K..Q6_K in schemes.py. The evidence exists: your dense oracle gate runs before the broad suite and returns 1 on failure, and the user's box run reached the broad suite, so the gate passed on ppu001. CONFIRM THIS FROM $OUT/dense_python_oracle.log ON THE BOX FIRST -- if the log does not show five passing cases and no skip, say so and do not promote. Update the note to state what the new evidence IS rather than silently deleting the old "test_fpA_kquant_dense is a self oracle" sentence. GPTQ_INT4_SYM stays IMPLEMENTED. The broad suite is not green, so do not let the wording imply it is.

(b) A REAL DEVICE DEFECT, newly isolated. gguf_prepass_ops.cpp:186 claims the device and CPU arms of gguf_vecdot are "interchangeable". The box falsifies it: identical bytes, relative error 8.0e-01 to 2.0e+00. The asymmetry is the clue -- through routes.matmul_native_gemv (gguf_vecdot_dense) the same five formats agree with official gguf to 1.5e-03; only gguf_vecdot disagrees, and its device call passes blocks_per_row=1:
        api->vecdot(bp, ts, xp16, op, int(rows), 1, int(qtype))
   while vecdot_rows_per_warp(rows, blocks_per_row) dispatches per format with values 2 (Q2/Q6), 2/4 (Q3), 2/8/4 (Q4), 2/8 (Q5). blocks_per_row == 1 may be a combination nothing has exercised. fp16 accumulation in a different order costs ~1e-2 at worst over 256 terms; order 1 is a wrong answer, not a precision effect. There is now a test for exactly this, tests/test_gguf_golden.py::test_device_vecdot_agrees_with_its_own_cpu_reference_arm, marked device_vs_cpu_arm. It is Claude's file -- if the 5e-2 bound needs changing, ask in the log, do not edit it.

(c) place_hi TILE-INVARIANCE. Read the [FROM CLAUDE - NARROW THE TASK AGAIN] entry in the log for the full statement. Short version: unfused_weight_dequantize.hpp's own comment establishes that the UNFOLDED low-plane placement is tile-invariant, verified byte-identical across 11 configurations in fold_derivation/l61 -- do not redo that. But your own Q6 finding (TK=256 wrong, TK=128 right, with F1=F2=1 in BOTH) is a direct counterexample for place_hi, which l61 never covered. Determine whether place_hi is tile-invariant at fixed (F1,F2), and if not, which quantity it depends on and whether that quantity is derived (like a per-plane delivery count) rather than the raw tile shape. This decides whether the on-disk artifact header records (bits, F1, F2) or a whole tactic. Plant a known difference and confirm the hash moves before reporting any "identical".

(d) fully_quantized/dense, Q4_K ONLY to begin with. It is the only one of the five with no prerequisite (single plane, 16-byte unit, already runs in grouped behind PPU_PACKED_SCALE=1); Q5 needs (c), Q2/Q3/Q6 additionally need the collective's hardcoded 16 B/unit generalised. The entry point is an INSTANTIATION at TileK=256 (gs=32 => Scale_TileK == kGroups == 8, what kPackedScaleOn tests) -- dense and grouped come from the same CollectiveBuilder selected by KernelScheduleType, so packed scale lives in the shared mainloop and is already reachable. Copy from the grouped side; do not write a second implementation. If you find the instantiation is format-independent and all five fall out together, say so rather than following the narrow plan.
   USER REQUIREMENT on this cell: KEEP THE SCALE CUTE-IFIED. quactlize/include/gguf_packed_unit.hpp has 0 cute references and 10 hand-written index/bit expressions, and it is exactly what FULLY_QUANTIZED reads. New addressing goes through a cute layout (pass the layout, as the 2-plane converter was done under task #15), not another set of shifts and masks. Do not let this expand into rewriting the existing ten unless that is genuinely the cheaper route -- and say which you did.
   Point its oracle at matmul_dequant_first through official gguf semantics FROM THE START, and plant a fault before reporting a pass. Also state plainly in the matrix note whether the cell is in the default build or behind a flag.

Commit and push as you go (no Co-Authored-By trailer). Report each step in the log.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×22
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_backend.cu` ×21
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp` ×20
- `/tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log` ×20
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp` ×15
- `/root/marlin_ppu/quactlize/dev/fold_derivation/syntax_baseline/ppu_dense_backend.cu.txt` ×9
- `/root/marlin_ppu/quactlize/quactlize/schemes.py` ×8
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.h` ×5
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l104_place_hi_invariance.cu` ×4
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.cpp` ×3
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h` ×3
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×2
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_backend.cu` ×1
- `/tmp/codex_vecdot_rows_probe.cu` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_packed_unit.hpp` ×1
- `/root/marlin_ppu/quactlize/.coord/BOX.md` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh` ×1
- `/tmp/quactlize_ppu_stub.cpp` ×1
- `/tmp/packed_pair_probe.cpp` ×1

## Last assistant conclusions

### 2026-08-03 10:47 UTC

Implemented and pushed the full queue. `develop` is clean at `d3a7051`.

- Promoted SCALE_FIRST/dense Q2_K–Q6_K from exact ppu001 evidence: five passed, no skips. GPTQ remains IMPLEMENTED.
- Fixed `gguf_vecdot` device/CPU disagreement.
- Proved `place_hi` is not tile-invariant. Its derived descriptor is `(F1,F2,DL1,DL2,folded_R2)`, not a whole tactic.
- Instantiated FULLY_QUANTIZED dense and grouped for all five k-quants:
  - Q4 `scu16x1`
  - Q2 `scu20x1`
  - Q5 `scu16x1` through the shared two-plane collective
  - Q3 `scu28x2`
  - Q6 `scu36x2`, retaining the required TileK=128 weight placement
- New packed addressing uses cute layouts and the shared decoder; the existing handwritten expressions were not rewritten.
- Q3/Q6 use the trait-driven uniform 4-byte transfers: seven and nine copies respectively.
- All cells clearly state they are non-default/flag-selected and remain PARTIAL pending real-device numerical oracles.

Verification:

- All five forced device front ends compile.
- Broad local suite: `217 passed, 16 skipped`; skips are precisely the unavailable PPU device tests.
- Packed-unit tests: 5 passed.
- Scheme/format tests: 49 passed.
- Q3/Q6 paired decoder identity and planted producer-fault gates passed.
- Manual activation gate passed for formats 0–4.

Remaining work is the ppu001 five-format oracle run. The Claude-owned permanent activation runner also still needs to execute all five variants rather than only format 2; that request is recorded in the coordination log.
