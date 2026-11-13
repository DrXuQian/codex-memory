# Resume brief: Fill the support matrix's fillable cells, in /root/marlin_ppu/quactlize, from HEAD 4628a35 (clean, 199/199, actlize gitlink 0b10f9e5). The user's instruction is "fill in everything that CAN be filled".

*** HEARTBEAT, mandatory, and tail it at start — I write into it ***
    echo "[$(date +%H:%M:%S)] <what you just did>" >> /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Every step, at least every ~5 min, numbers in the lines. Three of your runs have been killed at 1800s of MCP silence with the work already on disk; the heartbeat is what saves it.

WHAT "FILLED" MEANS HERE, and it is stricter than "the code runs". schemes.py's Status ladder is ABSENT / PARTIAL / IMPLEMENTED / VALIDATED, and VALIDATED requires an INDEPENDENT oracle -- "a self-comparison is not one". A cell that runs but is only checked against another configuration of itself is IMPLEMENTED, and saying so is the point of the ladder. Do not promote a cell past what its evidence supports; tests/test_schemes_consistency.py will refuse a VALIDATED claim whose only registry evidence is for a different kernel, and ci/registry.py's check() will refuse a VALIDATED cell with no harness at all.

=== FILLABLE, in the order I would do them. Each is wiring or a modest extension, not a new mechanism ===

(1) FULLY_QUANTIZED x GEMV_MOE, all five k-quants. THE HIGHEST-VALUE EMPTY CELL: it is what an MoE model
    needs at decode, recorded elsewhere as "A3B decode bulk unaccelerated, needs a separate MoE GEMV".
    vecdot_rows_kernel is dense-only -- one weight, no expert gather, no routing, no ragged rows -- and the
    extension is modest: an expert dimension on the grid and a per-expert weight base, with rows gathered.
    gemv_lowbit's grouped arm is the shape to learn from: dim3(grid_m, n/CtaN, num_experts) plus row_offsets.
    Locally verifiable end to end, which is why it is first.

(2) SCALE_FIRST x GEMV and x GEMV_MOE, all five k-quants. Currently PARTIAL, and the note says the blocker is
    that fp16 planes must be resident at decode -- a PRODUCT objection, not a technical one. The offline chain
    is complete and every step is already validated: gguf_unpack -> pack_int4 -> preprocess_weights_to_layout
    -> gemv_lowbit, and the row permutation was measured to stay inside its own 32-block so a plane indexed by
    k//gs is unaffected. What is missing is that gemv_lowbit is not reachable from Python. NOTE WHAT I PROVED
    TODAY: gemv_lowbit builds and runs under plain nvcc locally -- the REAL CMake unit generator works via
    dev/fold_derivation/gen_gemv_units_check.sh's cmake -P slice, 20 int4 units, no PPU SDK. So a binding is
    feasible now in a way it was not before. quactlize/csrc/preprocess/thop/ppu_backend.{h,cpp} is the
    established seam for exactly this shape (dlopen, C entry points, raw pointers, no torch in the .so).

(3) SCALE_FIRST x DENSE, all five k-quants. Same shape as (2) with fpA_intB_ppu.cuh. Lowest priority of the
    three and I want you to READ ITS NOTE FIRST: its GPTQ cell is only IMPLEMENTED because test_fpA_intB_ppu
    compares the launcher against another configuration of ITSELF, which is structurally blind to a wrong
    shared constant. Joining the halves would inherit that oracle, not gain one -- so if you do this, the
    honest result is IMPLEMENTED for the k-quants too, and say so rather than reaching for VALIDATED.

=== NOT FILLABLE. Do not attempt these; what is missing is a mechanism, not a wire ===
  * FULLY_QUANTIZED x GROUPED, Q2_K -- the collective hardcodes 16 bytes per unit, one 128-bit cp.async and
    Scale_TileK==8; Q2_K's unit is 20 bytes. The staging tile and its copy have to come from the trait.
  * FULLY_QUANTIZED x GROUPED, Q3_K/Q5_K/Q6_K -- structural: two-plane formats run through a SEPARATE
    collective with no packed-scale plumbing at all.
  * FULLY_QUANTIZED x DENSE -- the dense launcher has no staging for a native scale unit. Missing mechanism.
  * GPTQ_INT4_ASYM / AWQ_INT4 -- no importer, no fixture, no harness, and the asymmetric forms need a
    per-group zero point rather than a different checkpoint layout.
If while working you conclude one of these IS reachable after all, say so with the reason and stop -- do not
start it. And if one of the "fillable" three turns out to hide a mechanism, the same: say what and stop.

=== EVIDENCE REQUIREMENTS, per filled cell ===
  * an oracle that can FAIL. tests/test_gguf_routes.py is the model: official gguf as the reference, an
    asymmetric fixture (n != k, activation varying along k, different bytes per expert), and a planted fault
    that the test catches. A cell whose test has only ever been observed passing is not evidence.
  * a ci/registry.py declaration, with the right oracle kind. Note the registry has ONE path name "gemv" for
    both MoE and dense decode, so schemes._CELL_PATH_IS_COARSE currently refuses a VALIDATED claim on
    fully_quantized/gemv_moe and scale_first/gemv_moe. If you fill those cells with real evidence, SPLIT the
    path vocabulary rather than deleting the coarse entry -- that set exists so a claim cannot be approved by
    a neighbouring kernel's harness.
  * update the cell's note in schemes.py to say what now covers it, and delete the stale blocker text.

CONSTRAINTS: CUDA cores only for the GEMV work, no tensor cores, no MMA, dp4a forbidden. Compiles under nvcc
AND hgcc. Measure at rows=131072 for throughput A/Bs and at rows=2048 for the shipping shape -- the event
timer quantises at 2.048 us and warm batching is what resolves the small shape. Report Gelem/s and % of peak.
actlize edits need their own commit plus a gitlink bump in the parent; the chain must end with submodule
HEAD, gitlink and origin/ppu-w4a16-dev all equal.

Do not ask me questions; make the call and state the assumption in the log.

- **Thread ID:** `019fc603-0bd2-7510-a8cd-c2acc9a5d2b6`
- **Started / last event:** 2026-08-03 05:05 UTC → 2026-08-03 07:32 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T13-05-16-019fc603-0bd2-7510-a8cd-c2acc9a5d2b6.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "4628a352c4ab18bc6a31279a6cfa06155cdc7655", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-03_019fc603_Fill-the-support-matrix-s-fillable-cells-in-root-m.md](../transcripts/2026-08/2026-08-03_019fc603_Fill-the-support-matrix-s-fillable-cells-in-root-m.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Fill the support matrix's fillable cells, in /root/marlin_ppu/quactlize, from HEAD 4628a35 (clean, 199/199, actlize gitlink 0b10f9e5). The user's instruction is "fill in everything that CAN be filled".

*** HEARTBEAT, mandatory, and tail it at start — I write into it ***
    echo "[$(date +%H:%M:%S)] <what you just did>" >> /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Every step, at least every ~5 min, numbers in the lines. Three of your runs have been killed at 1800s of MCP silence with the work already on disk; the heartbeat is what saves it.

WHAT "FILLED" MEANS HERE, and it is stricter than "the code runs". schemes.py's Status ladder is ABSENT / PARTIAL / IMPLEMENTED / VALIDATED, and VALIDATED requires an INDEPENDENT oracle -- "a self-comparison is not one". A cell that runs but is only checked against another configuration of itself is IMPLEMENTED, and saying so is the point of the ladder. Do not promote a cell past what its evidence supports; tests/test_schemes_consistency.py will refuse a VALIDATED claim whose only registry evidence is for a different kernel, and ci/registry.py's check() will refuse a VALIDATED cell with no harness at all.

=== FILLABLE, in the order I would do them. Each is wiring or a modest extension, not a new mechanism ===

(1) FULLY_QUANTIZED x GEMV_MOE, all five k-quants. THE HIGHEST-VALUE EMPTY CELL: it is what an MoE model
    needs at decode, recorded elsewhere as "A3B decode bulk unaccelerated, needs a separate MoE GEMV".
    vecdot_rows_kernel is dense-only -- one weight, no expert gather, no routing, no ragged rows -- and the
    extension is modest: an expert dimension on the grid and a per-expert weight base, with rows gathered.
    gemv_lowbit's grouped arm is the shape to learn from: dim3(grid_m, n/CtaN, num_experts) plus row_offsets.
    Locally verifiable end to end, which is why it is first.

(2) SCALE_FIRST x GEMV and x GEMV_MOE, all five k-quants. Currently PARTIAL, and the note says the blocker is
    that fp16 planes must be resident at decode -- a PRODUCT objection, not a technical one. The offline chain
    is complete and every step is already validated: gguf_unpack -> pack_int4 -> preprocess_weights_to_layout
    -> gemv_lowbit, and the row permutation was measured to stay inside its own 32-block so a plane indexed by
    k//gs is unaffected. What is missing is that gemv_lowbit is not reachable from Python. NOTE WHAT I PROVED
    TODAY: gemv_lowbit builds and runs under plain nvcc locally -- the REAL CMake unit generator works via
    dev/fold_derivation/gen_gemv_units_check.sh's cmake -P slice, 20 int4 units, no PPU SDK. So a binding is
    feasible now in a way it was not before. quactlize/csrc/preprocess/thop/ppu_backend.{h,cpp} is the
    established seam for exactly this shape (dlopen, C entry points, raw pointers, no torch in the .so).

(3) SCALE_FIRST x DENSE, all five k-quants. Same shape as (2) with fpA_intB_ppu.cuh. Lowest priority of the
    three and I want you to READ ITS NOTE FIRST: its GPTQ cell is only IMPLEMENTED because test_fpA_intB_ppu
    compares the launcher against another configuration of ITSELF, which is structurally blind to a wrong
    shared constant. Joining the halves would inherit that oracle, not gain one -- so if you do this, the
    honest result is IMPLEMENTED for the k-quants too, and say so rather than reaching for VALIDATED.

=== NOT FILLABLE. Do not attempt these; what is missing is a mechanism, not a wire ===
  * FULLY_QUANTIZED x GROUPED, Q2_K -- the collective hardcodes 16 bytes per unit, one 128-bit cp.async and
    Scale_TileK==8; Q2_K's unit is 20 bytes. The staging tile and its copy have to come from the trait.
  * FULLY_QUANTIZED x GROUPED, Q3_K/Q5_K/Q6_K -- structural: two-plane formats run through a SEPARATE
    collective with no packed-scale plumbing at all.
  * FULLY_QUANTIZED x DENSE -- the dense launcher has no staging for a native scale unit. Missing mechanism.
  * GPTQ_INT4_ASYM / AWQ_INT4 -- no importer, no fixture, no harness, and the asymmetric forms need a
    per-group zero point rather than a different checkpoint layout.
If while working you conclude one of these IS reachable after all, say so with the reason and stop -- do not
start it. And if one of the "fillable" three turns out to hide a mechanism, the same: say what and stop.

=== EVIDENCE REQUIREMENTS, per filled cell ===
  * an oracle that can FAIL. tests/test_gguf_routes.py is the model: official gguf as the reference, an
    asymmetric fixture (n != k, activation varying along k, different bytes per expert), and a planted fault
    that the test catches. A cell whose test has only ever been observed passing is not evidence.
  * a ci/registry.py declaration, with the right oracle kind. Note the registry has ONE path name "gemv" for
    both MoE and dense decode, so schemes._CELL_PATH_IS_COARSE currently refuses a VALIDATED claim on
    fully_quantized/gemv_moe and scale_first/gemv_moe. If you fill those cells with real evidence, SPLIT the
    path vocabulary rather than deleting the coarse entry -- that set exists so a claim cannot be approved by
    a neighbouring kernel's harness.
  * update the cell's note in schemes.py to say what now covers it, and delete the stale blocker text.

CONSTRAINTS: CUDA cores only for the GEMV work, no tensor cores, no MMA, dp4a forbidden. Compiles under nvcc
AND hgcc. Measure at rows=131072 for throughput A/Bs and at rows=2048 for the shipping shape -- the event
timer quantises at 2.048 us and warm batching is what resolves the small shape. Report Gelem/s and % of peak.
actlize edits need their own commit plus a gitlink bump in the parent; the chain must end with submodule
HEAD, gitlink and origin/ppu-w4a16-dev all equal.

Do not ask me questions; make the call and state the assumption in the log.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp` ×12
- `/root/marlin_ppu/quactlize/tests/test_gguf_routes.py` ×12
- `/root/marlin_ppu/quactlize/quactlize/__init__.py` ×9
- `/root/marlin_ppu/quactlize/quactlize/routes.py` ×7
- `/root/marlin_ppu/quactlize/quactlize/schemes.py` ×6
- `/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in` ×5
- `/root/marlin_ppu/quactlize/docs/DECODE_GEMV_RESULTS.md` ×5
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_backend.cu` ×5
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_layout.cu` ×5
- `/root/marlin_ppu/quactlize/tests/test_fpA_kquant_dense.cu` ×5
- `/root/marlin_ppu/quactlize/tests/test_gguf_golden.py` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.cpp` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.h` ×3
- `/root/marlin_ppu/quactlize/ci/registry.py` ×3
- `/root/marlin_ppu/quactlize/docs/HANDOFF_gguf_pipeline.md` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_backend.cu` ×2
- `/root/marlin_ppu/quactlize/benchmarks/decode_routes_bench.cu` ×2
- `/root/marlin_ppu/quactlize/benchmarks/decode_routes_bench.py` ×2
- `/root/marlin_ppu/quactlize/tests/test_schemes_consistency.py` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp` ×1
- `/root/marlin_ppu/quactlize/tests/gguf_cuda_probe.cu` ×1
- `/root/marlin_ppu/quactlize/build.sh` ×1
- `/root/marlin_ppu/quactlize/quactlize/formats.py` ×1
- `/root/marlin_ppu/quactlize/tests/test_formats.py` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py` ×1
- `/root/marlin_ppu/quactlize/README.md` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp` ×1
- `/root/marlin_ppu/quactlize/benchmarks/run_batch.sh` ×1

## Last assistant conclusions

### 2026-08-03 07:32 UTC

Implemented and committed the fillable matrix work.

Matrix result:

- `FULLY_QUANTIZED × GEMV_MOE`: all five k-quants VALIDATED.
- `SCALE_FIRST × GEMV/GEMV_MOE`: all five VALIDATED.
- `SCALE_FIRST × DENSE`: all five IMPLEMENTED, not overclaimed.
- Both scale-first artifact families now have Python-reachable dequant-all and lossless dequant-scale inverses.
- Dense Q6 uses TK=128 after the inverse exposed incomplete TK=256 high-plane coverage.

Dense remains IMPLEMENTED because the independent PPU GEMM oracle cannot run here. The new test covers all formats at M=7/65, compares against an official-GGUF weight through the dequant-first GEMM, and plants a code-plane fault first. The device runner rejects skips. Locally: 217 passed, 5 expected PPU-only skips.

Performance values are `Gelem/s / % peak`.

| Format | FQ GEMV_MOE, 131072 | SF GEMV, 131072 | SF GEMV_MOE, 131072 |
|---|---:|---:|---:|
| Q2_K | 3603.4 / 66.4% | 3196.9 / 89.4% | 3328.8 / 93.1% |
| Q3_K | 2140.0 / 51.5% | 2570.0 / 89.8% | 2654.6 / 92.7% |
| Q4_K | 2279.5 / 71.8% | 2621.4 / 91.6% | 2702.5 / 94.4% |
| Q5_K | 1945.4 / 74.8% | 2184.5 / 91.5% | 2255.0 / 94.5% |
| Q6_K | 1820.4 / 83.5% | 1638.4 / 91.5% | 1691.3 / 94.5% |

Shipping-shape warm-batched results:

| Format | FQ GEMV_MOE, 2048 | SF GEMV, 2048 | SF GEMV_MOE, 2048 |
|---|---:|---:|---:|
| Q2_K | 3225.0 / 59.6% | 1491.8 / 41.8% | 4035.7 / 113.0% |
| Q3_K | 1945.0 / 47.0% | 1160.7 / 40.6% | 2913.7 / 101.9% |
| Q4_K | 1148.1 / 36.2% | 1544.0 / 54.0% | 4270.4 / 149.4% |
| Q5_K | 1005.7 / 38.7% | 1305.6 / 54.8% | 3252.5 / 136.5% |
| Q6_K | 1950.2 / 89.6% | 1225.9 / 68.5% | 2786.8 / 155.8% |

Values over 100% are warm L2/HBM-equivalent rates, not DRAM efficiency claims. Full measurements are in [DECODE_GEMV_RESULTS.md](/root/marlin_ppu/quactlize/docs/DECODE_GEMV_RESULTS.md).

Verification included:

- 20 production CUDA-core launch/oracle cases.
- 10/10 dense backend and harness format instantiations clean through the PPU-aware nvcc front end.
- Registry: zero problems.
- Stub-hgcc build graph reached the new harness.
- Actual hgcc/PPU execution remains unavailable locally.

Commits:

- `9b45627` — native and scale-first k-quant GEMV.
- `9ec32f9` — scale-first dense and artifact inverses.
- `95d25a0` — required independent PPU dense oracle.

No actlize edits were needed. Submodule HEAD, parent gitlink, and `origin/ppu-w4a16-dev` all equal `0b10f9e543433e12903c3717dc487962e77f9530`. Worktree is clean.

I also corrected the stale `FULLY_QUANTIZED × DENSE` blocker: dense and grouped share the same builder/mainloop, so the dense-specific gap is a TK=256 instantiation, not a new staging mechanism. I stopped before implementing it because the required dense PPU oracle has not yet run; Q2 and the two-plane formats also retain their format-level packed-scale blockers.
