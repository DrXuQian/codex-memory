# Resume brief: Repo /root/marlin_ppu/quactlize, branch dev. FULL LOCAL ACCESS. Read the tree directly and RUN things.
DO NOT EDIT ANY FILE -- this is a pre-push review. Report only.

Review the STAGED diff (`git diff --cached`): a new pre-flight check dev/fold_derivation/overlay_targets_check.py,
plus its wiring into build.sh and ci/local_gates.py.

CONTEXT. build.sh overlays this repo's sources into third_party/actlize/examples/99_kernels_w4a16_compare/ and
builds there. quactlize/csrc/CMakeLists.txt.in registers 33 targets by naming source files. Nothing compared the
registered source list against the overlaid file set until cmake ran on the accelerator -- and a source CMake names
but the overlay lacks is a CONFIGURE-time error, so it fails for EVERY target at once. That has now cost two box
round-trips. The new check is supposed to make that class of failure local and impossible to reach the box.

ARGUE, do not summarise. Be specific, cite file:line, run commands.

1. Construct a way for the CMake registrations and the overlay to disagree that this check does NOT catch. Actually
   try it (edit in a scratch copy under /tmp, never in the repo) and show the check passing while cmake would fail.
   The registration parser, overlay_basenames(), and build_sh_dirs_agree() are all hand-rolled models of what
   build.sh and CMake do -- find where a model diverges from the thing it models.
2. Is REQUIRED = (test_moe_splitk_bench, test_q4k_packed_gemm, test_moe_grouped_verify) actually the right set?
   Read benchmarks/run_batch.sh and say what it really needs.
3. The check is wired into build.sh with `|| exit 1` and into ci/local_gates.py. Is a false positive here worse than
   the bug it prevents? One earlier version DID false-positive (it compared build.sh's literal _src_dirs against an
   exported list that has dev/ appended). Find another false-positive path.
4. ppu_w4a16_executable() in CMakeLists.txt.in now SKIPS a target whose sources are absent, and the 8
   target_compile_options() calls that follow are wrapped in if(TARGET). Is that skip-and-continue right, or does it
   trade a loud configure error for a silently smaller build? What would you do instead?
5. Run `python3 ./ci/local_gates.py` and `python3 -m pytest tests/ -q`. Report anything green that measures nothing.

If a design decision is wrong, say so plainly.

- **Thread ID:** `019fbd2c-1612-7bb3-87ac-fecfb8b1e182`
- **Started / last event:** 2026-08-01 11:53 UTC → 2026-08-01 12:11 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T19-53-30-019fbd2c-1612-7bb3-87ac-fecfb8b1e182.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "80244175d69aa2ad79e56b5eaaa8525685cb7482", "branch": "dev", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-01_019fbd2c_Repo-root-marlin_ppu-quactlize-branch-dev-FULL-LOC.md](../transcripts/2026-08/2026-08-01_019fbd2c_Repo-root-marlin_ppu-quactlize-branch-dev-FULL-LOC.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch dev. FULL LOCAL ACCESS. Read the tree directly and RUN things.
DO NOT EDIT ANY FILE -- this is a pre-push review. Report only.

Review the STAGED diff (`git diff --cached`): a new pre-flight check dev/fold_derivation/overlay_targets_check.py,
plus its wiring into build.sh and ci/local_gates.py.

CONTEXT. build.sh overlays this repo's sources into third_party/actlize/examples/99_kernels_w4a16_compare/ and
builds there. quactlize/csrc/CMakeLists.txt.in registers 33 targets by naming source files. Nothing compared the
registered source list against the overlaid file set until cmake ran on the accelerator -- and a source CMake names
but the overlay lacks is a CONFIGURE-time error, so it fails for EVERY target at once. That has now cost two box
round-trips. The new check is supposed to make that class of failure local and impossible to reach the box.

ARGUE, do not summarise. Be specific, cite file:line, run commands.

1. Construct a way for the CMake registrations and the overlay to disagree that this check does NOT catch. Actually
   try it (edit in a scratch copy under /tmp, never in the repo) and show the check passing while cmake would fail.
   The registration parser, overlay_basenames(), and build_sh_dirs_agree() are all hand-rolled models of what
   build.sh and CMake do -- find where a model diverges from the thing it models.
2. Is REQUIRED = (test_moe_splitk_bench, test_q4k_packed_gemm, test_moe_grouped_verify) actually the right set?
   Read benchmarks/run_batch.sh and say what it really needs.
3. The check is wired into build.sh with `|| exit 1` and into ci/local_gates.py. Is a false positive here worse than
   the bug it prevents? One earlier version DID false-positive (it compared build.sh's literal _src_dirs against an
   exported list that has dev/ appended). Find another false-positive path.
4. ppu_w4a16_executable() in CMakeLists.txt.in now SKIPS a target whose sources are absent, and the 8
   target_compile_options() calls that follow are wrapped in if(TARGET). Is that skip-and-continue right, or does it
   trade a loud configure error for a silently smaller build? What would you do instead?
5. Run `python3 ./ci/local_gates.py` and `python3 -m pytest tests/ -q`. Report anything green that measures nothing.

If a design decision is wrong, say so plainly.

## Files edited via apply_patch (most frequent first)

- `/tmp/quactlize-overlay-review.wo3JtU/root/quactlize/csrc/CMakeLists.txt.in` ×2
- `/tmp/quactlize-overlay-review.wo3JtU/root/dev/dev_model_gap.cpp` ×1
- `/tmp/quactlize-overlay-review.wo3JtU/CMakeLists.txt` ×1
- `/tmp/quactlize-overlay-review.wo3JtU/dummy.cpp` ×1
- `/tmp/quactlize-overlay-review.wo3JtU/root/build.sh` ×1

## Last assistant conclusions

### 2026-08-01 12:11 UTC

Do not push this as-is. The fatal pre-flight check both misses real failures and rejects semantically equivalent build scripts. Worse, the current CMake wrapper already breaks required generated-source targets while the new gate reports green.

## Findings

1. **Blocker: the current tree’s generated targets are skipped, then CMake fails.**

The wrapper tests every source as:

`${CMAKE_CURRENT_SOURCE_DIR}/${_src}`

at [CMakeLists.txt.in:39](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:39). But `${_SK_SRCS}`, `${_GEMV_UNIT_SRCS}`, and `${_MOE_UNIT_SRCS}` expand to absolute build-tree paths. Prefixing an absolute path produces a nonexistent path such as:

```text
<overlay-dir>//tmp/.../splitk_unit_....cu
```

The wrapper therefore skips `test_moe_splitk_bench`, and the unconditional calls at [CMakeLists.txt.in:401](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:401) immediately fail.

Using the actual CMake file in a scratch overlay with only the actlize registration function stubbed, I got:

```text
cmake exit=1
-- ppu_w4a16: skipping test_moe_splitk_bench -- not in this overlay: /tmp/.../splitk_unit_16x32_256_w16x16_s2.cu
CMake Error at actual_overlay/CMakeLists.txt:401 (target_compile_options):
  ... target "test_moe_splitk_bench" ... not built by this project.
```

The staged checker explicitly discards `${...}` sources at [overlay_targets_check.py:60](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:60), so it reports all 33 targets present despite this configure failure. This is exactly the false confidence the check is supposed to eliminate.

2. **Requested counterexample: `overlay_basenames()` models a different dev overlay than `build.sh`.**

The checker applies the common `EXTS`, including `.cpp`, to `dev/` at [overlay_targets_check.py:76](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:76). The actual dev glob at [build.sh:117](/root/marlin_ppu/quactlize/build.sh:117) omits `.cpp`.

In `/tmp/quactlize-overlay-review.wo3JtU`, I:

- Added `dev/dev_model_gap.cpp`.
- Changed `test_fpA_intB_ppu` to register that source.
- Materialized an overlay using `build.sh`’s exact globs.

Results:

```text
[ok] overlay_targets: 33 target(s) have their sources in the overlay,
     0 skipped by design, 3 required target(s) present
actual build.sh-model overlay: dev_model_gap.cpp is absent
```

Then CMake:

```text
-- ppu_w4a16: skipping test_fpA_intB_ppu -- not in this overlay: dev_model_gap.cpp
CMake Error at actual_overlay/CMakeLists.txt:109 (target_compile_options):
  Cannot specify compile options for target "test_fpA_intB_ppu"
  which is not built by this project.
```

`build_sh_dirs_agree()` cannot catch this because it checks only the directory names and the presence of one literal `.cu` substring, not the extension globs it purports to model; see [overlay_targets_check.py:115](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:115).

The registration parser is similarly fragile: CMake command names are case-insensitive and tolerate formatting the regex does not. An uppercase or indented `PPU_W4A16_EXECUTABLE` can disappear from the checker while remaining valid CMake, provided some other registrations still parse.

3. **`REQUIRED` contains the right unique targets for full `run_batch.sh`, but its rationale and enforcement are wrong.**

For `run_batch.sh all`/`build`, the unique set is indeed:

- `test_moe_splitk_bench`: seven variants at [run_batch.sh:82](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:82).
- `test_q4k_packed_gemm`: four variants at [run_batch.sh:84](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:84).
- `test_moe_grouped_verify`: two variants at [run_batch.sh:88](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:88).

But `test_moe_splitk_bench` is not required by `do_check`; the fresh-binary list at [run_batch.sh:144](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:144) contains only the other two. Split-K is required for `do_perf`. Therefore “correctness gates cannot run” is false; the tuple describes the full batch workflow.

More seriously, `REQUIRED` does not establish that those registrations exist. It is consulted only while iterating registrations that the regex happened to parse at [overlay_targets_check.py:151](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:151). Removing or reformatting a required registration does not fail. The success message then prints `len(REQUIRED)` at [overlay_targets_check.py:176](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:176), not the number actually found. “3 required target(s) present” is currently a constant, not a measurement.

4. **The fatal wiring makes the checker’s false positives unacceptable.**

A false positive is cheaper than a box round-trip because it fails locally, but a syntax-sensitive false positive still blocks every build and quickly teaches users to bypass the check. This implementation is too brittle to be fatal.

I tested another false-positive path by changing only:

```bash
_src_dirs=(quactlize/include tests benchmarks)
```

to the semantically identical:

```bash
_src_dirs=("quactlize/include" "tests" "benchmarks")
```

Bash produced the same three values, but the checker failed:

```text
build.sh overlays ['"benchmarks"', '"quactlize/include"', '"tests"']
but this check assumed ['benchmarks', 'quactlize/include', 'tests']
checker exit=1
bash values=<quactlize/include tests benchmarks>
```

That comes from applying Python `.split()` to shell syntax at [overlay_targets_check.py:118](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:118). The `.cu` substring probe at line 125 has the same problem with harmless quoting or refactoring changes.

Also, `build.sh` validates the PPU SDK at [build.sh:35](/root/marlin_ppu/quactlize/build.sh:35) before reaching the “cheap local checks” at [build.sh:53](/root/marlin_ppu/quactlize/build.sh:53). On an SDK-less local machine, the new check does not run through `build.sh` at all.

5. **Skip-and-continue is the wrong policy.**

It trades a deterministic missing-source error for two inconsistent outcomes:

- Eight specially guarded dev probes disappear silently.
- The other targets are skipped and then fail on unguarded `target_compile_options` or `target_include_directories`.

Thus “skipped by design” in [overlay_targets_check.py:165](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:165) does not model CMake generally. The scratch `test_fpA_intB_ppu` failure proves it.

I would:

- Make missing registered literal sources a `FATAL_ERROR` in `ppu_w4a16_executable`.
- Handle absolute/generated sources correctly with `IS_ABSOLUTE`, checking them directly.
- Put optional dev probes behind one explicit feature/configuration conditional, with an all-eight-files assertion when enabled.
- Derive the copy manifest and checker input from one executable implementation, rather than independently parsing Bash and CMake.
- Assert every required target was actually parsed/registered.

## Commands requested

`python3 ./ci/local_gates.py` exited successfully:

```text
== 31/31 passed or skipped ==
```

But its new overlay row is green while the actual CMake wrapper fails required generated targets. That row presently measures agreement between handwritten models, not whether the overlay configures.

`python3 -m pytest tests/ -q` exited successfully:

```text
64 passed, 42 skipped in 39.14s
```

All 42 skipped tests require the absent `quactlize/_C*.so`: five extension-backed layout tests and 37 preprocessing-op tests. `local_gates.py` nevertheless labels the aggregate pytest item `[ok]` based solely on pytest’s zero exit status at [local_gates.py:111](/root/marlin_ppu/quactlize/ci/local_gates.py:111).

Two further green-but-vacuous paths already exist in `run_batch.sh`:

- The “swizzle alone” verifier is explicitly admitted to be vacuous because `Stages
… [truncated 391 chars]
