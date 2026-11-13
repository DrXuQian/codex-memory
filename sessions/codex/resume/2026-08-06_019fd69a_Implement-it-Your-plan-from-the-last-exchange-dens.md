# Resume brief: Implement it. Your plan from the last exchange, dense only.

Scope, as you scoped it yourself:

  * A table parser/batcher in CMake, reusable by both operators, used for dense NOW. Consume
    benchmarks/lowbit_dense_configs.inc; do not restate its axes. Fail closed as you listed: register the .inc as
    a configure dependency, accept only the exact seven-integer row form X(TM,TN,TK,WM,WN,ST,ACR,B), validate the
    parsed count against LOWBIT_DENSE_CFG_ROWS, reject duplicates and malformed rows, put every field including
    ACR into the generated symbol identity even though runtime names omit it today, and generate through
    copy_if_different like the existing unit generators.
  * Many TUs, ONE executable, one process per shape. Compile unit != dispatch unit: one exported wrapper per
    config, several wrappers per generated .cu, the runtime registry holding the wrapper pointer alongside
    TileCfg. LOWBIT_DENSE_DISPATCH's BODY-carrying expansion goes; it names every Cfg<>::Gemm in the main TU,
    which is the serialisation itself. --config calls one wrapper; --search_configs keeps looping the same
    registry in the same process.
  * Batch size selectable. Default to your k=4 (158 TUs, one wave at ~192 slots), but make it a cache variable so
    k=1/2/4/8 can be timed without editing CMake.

DO NOT migrate MoE in this change. You were right that it is not only a build mechanism: the emitter prunes
primary/guard and the MoE Cartesian product deliberately reaches outside that policy, so repointing it at
--space=grouped would silently narrow the sweep. That decision -- pruned grouped table versus full legal grouped
sweep, and whether the emitter needs an unpruned mode -- is its own task and I am recording it as one.

What I can and cannot check here: this machine has no PPU SDK, so I can compile with nvcc through
dev/fold_derivation/syntax_check.sh but I cannot time a real hgcc build. The k=1/2/4/8 timing with JOBS fixed and
peak memory recorded has to happen on the box; leave the knob and say in the commit what still needs measuring
rather than asserting a default is best.

Two things to preserve that the tooling will not tell you about:

  * ci/check_dense_tactic_table.py regenerates the table from the arguments the table's own header declares. If
    the .inc's shape changes at all, that gate and the header must move together.
  * ci/check_generated_include_edges.py (new today) extracts `#include "x.inc"` from file(WRITE) literals and
    requires each to resolve. A new generated unit body -- lowbit_dense_unit.inc or whatever you call it -- is
    covered by it automatically, which is the point; just make sure the include is a literal and not built by
    interpolation, because the checker errors out on interpolation rather than guessing.

Commit and push to origin/develop when the local tier is green, no Co-Authored-By trailer. If a gate fails for a
reason you did not cause, say so rather than working around it.

- **Thread ID:** `019fd69a-65a9-72b0-91dc-b9728b532124`
- **Started / last event:** 2026-08-06 10:24 UTC → 2026-08-06 11:01 UTC
- **Working dir:** `/root`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/06/rollout-2026-08-06T18-24-30-019fd69a-65a9-72b0-91dc-b9728b532124.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-08-06_019fd69a_Implement-it-Your-plan-from-the-last-exchange-dens.md](../transcripts/2026-08/2026-08-06_019fd69a_Implement-it-Your-plan-from-the-last-exchange-dens.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Implement it. Your plan from the last exchange, dense only.

Scope, as you scoped it yourself:

  * A table parser/batcher in CMake, reusable by both operators, used for dense NOW. Consume
    benchmarks/lowbit_dense_configs.inc; do not restate its axes. Fail closed as you listed: register the .inc as
    a configure dependency, accept only the exact seven-integer row form X(TM,TN,TK,WM,WN,ST,ACR,B), validate the
    parsed count against LOWBIT_DENSE_CFG_ROWS, reject duplicates and malformed rows, put every field including
    ACR into the generated symbol identity even though runtime names omit it today, and generate through
    copy_if_different like the existing unit generators.
  * Many TUs, ONE executable, one process per shape. Compile unit != dispatch unit: one exported wrapper per
    config, several wrappers per generated .cu, the runtime registry holding the wrapper pointer alongside
    TileCfg. LOWBIT_DENSE_DISPATCH's BODY-carrying expansion goes; it names every Cfg<>::Gemm in the main TU,
    which is the serialisation itself. --config calls one wrapper; --search_configs keeps looping the same
    registry in the same process.
  * Batch size selectable. Default to your k=4 (158 TUs, one wave at ~192 slots), but make it a cache variable so
    k=1/2/4/8 can be timed without editing CMake.

DO NOT migrate MoE in this change. You were right that it is not only a build mechanism: the emitter prunes
primary/guard and the MoE Cartesian product deliberately reaches outside that policy, so repointing it at
--space=grouped would silently narrow the sweep. That decision -- pruned grouped table versus full legal grouped
sweep, and whether the emitter needs an unpruned mode -- is its own task and I am recording it as one.

What I can and cannot check here: this machine has no PPU SDK, so I can compile with nvcc through
dev/fold_derivation/syntax_check.sh but I cannot time a real hgcc build. The k=1/2/4/8 timing with JOBS fixed and
peak memory recorded has to happen on the box; leave the knob and say in the commit what still needs measuring
rather than asserting a default is best.

Two things to preserve that the tooling will not tell you about:

  * ci/check_dense_tactic_table.py regenerates the table from the arguments the table's own header declares. If
    the .inc's shape changes at all, that gate and the header must move together.
  * ci/check_generated_include_edges.py (new today) extracts `#include "x.inc"` from file(WRITE) literals and
    requires each to resolve. A new generated unit body -- lowbit_dense_unit.inc or whatever you call it -- is
    covered by it automatically, which is the point; just make sure the include is a literal and not built by
    interpolation, because the checker errors out on interpolation rather than guessing.

Commit and push to origin/develop when the local tier is green, no Co-Authored-By trailer. If a gate fails for a
reason you did not cause, say so rather than working around it.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu` ×8
- `/root/marlin_ppu/quactlize/quactlize/csrc/TacticTableUnits.cmake` ×5
- `/tmp/quactlize-overlay-87i98w4_/src/lowbit_dense_configs.inc` ×4
- `/root/marlin_ppu/quactlize/ci/check_dense_unit_generator.py` ×4
- `/root/marlin_ppu/quactlize/build.sh` ×3
- `/root/marlin_ppu/quactlize/dev/fold_derivation/syntax_check.sh` ×2
- `/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in` ×1
- `/root/marlin_ppu/quactlize/benchmarks/lowbit_dense_unit.inc` ×1
- `/root/marlin_ppu/quactlize/ci/local_gates.py` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/syntax_baseline/lowbit_dense_unit_0.cu.txt` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/syntax_baseline/lowbit_dense_unit_157.cu.txt` ×1

## Last assistant conclusions

### 2026-08-06 11:01 UTC

Implemented dense-only batching; MoE and the tactic table remain unchanged.

Key results:

- Strict reusable CMake parser/batcher: [TacticTableUnits.cmake](/root/marlin_ppu/quactlize/quactlize/csrc/TacticTableUnits.cmake:1)
- k-config generated units, default `LOWBIT_DENSE_CONFIGS_PER_UNIT=4`: [CMakeLists.txt.in](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:194)
- Wrapper-pointer registry replaces BODY dispatch: [test_lowbit_dense_bench.cu](/root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu:503)
- Generated unit body: [lowbit_dense_unit.inc](/root/marlin_ppu/quactlize/benchmarks/lowbit_dense_unit.inc:1)
- Fail-closed generator controls: [check_dense_unit_generator.py](/root/marlin_ppu/quactlize/ci/check_dense_unit_generator.py:1)
- `build.sh` forwards the batch knob.

Validation:

- 632 wrappers / 158 TUs at k=4
- k=1/2/4/8 produce 632/316/158/79 TUs
- All 158 generated TUs passed nvcc front-end compilation with zero error signatures
- Dense table regeneration, generated include edges, overlay configure, and dense stub box build passed
- Full tier: 80/86

The six failures are pre-existing recorded blockers: `l103` fmt1/3/4, `l112`, untracked `test_int1_sweep.cu`, and four pytest setup errors. I did not work around them.

Because you conditioned commit/push on a green full tier, nothing was committed or pushed. If these known failures should be accepted as the baseline, tell me to proceed with commit and push. The commit will explicitly state that k=1/2/4/8 hgcc time and peak-memory measurements at fixed `JOBS` remain outstanding; k=4 is not claimed as measured-best.

Also, my earlier push-policy warning came from `/root/llama.cpp` while locating the repository; it does not apply to this quactlize tree.
