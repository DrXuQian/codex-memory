# Repo /root/marlin_ppu/quactlize, branch dev. FULL LOCAL ACCESS. Read the tree directly and RUN things.
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

---

## User · 2026-08-01 11:53 UTC

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

## Assistant · 2026-08-01 11:53 UTC

I’ll treat this as an adversarial pre-push review: inspect the staged patch and surrounding build/CMake scripts, reproduce model gaps only in `/tmp`, then run both requested test commands. I won’t modify the repository.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"git status --short --branch && git diff --cached --stat && git diff --cached -- build.sh ci/local_gates.py dev/fold_derivation/overlay_targets_check.py quactlize/csrc/CMakeLists.txt.in","workdir":" …`
- `exec: const cmds = [ ["build", "nl -ba build.sh | sed -n '1,240p'"], ["cmake", "nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '1,360p'"], ["batch", "nl -ba benchmarks/run_batch.sh | sed -n '1,300p'"], ["gates", "nl -ba ci/local_gates.py | sed  …`
- `exec: const cmds = [ ["cmake1", "nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '19,190p'"], ["cmake2", "nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '190,420p'"], ["batch1", "nl -ba benchmarks/run_batch.sh | sed -n '1,220p'"], ["batch2", " …`

</details>

## Assistant · 2026-08-01 11:54 UTC

The first important tension is already visible: the staged checker treats non-required skipped targets as acceptable, while the CMake wrapper also suppresses missing-source registrations. I’m now testing whether those two “skip” policies hide real configure breakage or silently remove build products, and I’m checking `run_batch.sh` from its actual target invocations rather than trusting the checker’s comment.

<details><summary>9 tool call(s)</summary>

- `exec: const cmds = [ ["regs", "rg -n -C 4 'ppu_w4a16_executable|target_compile_(options|definitions)|target_include_directories|if\\(TARGET|endif\\(' quactlize/csrc/CMakeLists.txt.in"], ["batch_targets", "rg -n 'build_one|test_[A-Za-z0-9_]+' benc …`
- `exec: const r = await tools.exec_command({"cmd":"set -e\nscratch=$(mktemp -d /tmp/quactlize-overlay-review.XXXXXX)\nmkdir -p \"$scratch/root\"\ncp -a build.sh quactlize tests benchmarks dev ci \"$scratch/root/\"\nprintf '%s\\n' \"$scratch\"","wor …`
- `exec: const p = load("scratch"); const rel = "../../../" + p.replace(/^\//,"") + "/root/quactlize/csrc/CMakeLists.txt.in"; const patch = '*** Begin Patch\n*** Update File: ${rel}\n@@\n-ppu_w4a16_executable(\n+PPU_W4A16_EXECUTABLE(\n test_fpA_intB …`
- `exec: const p = load("scratch"); const base = "../../../" + p.replace(/^\//,"") + "/root"; const patch = '*** Begin Patch\n*** Update File: ${base}/quactlize/csrc/CMakeLists.txt.in\n@@\n-PPU_W4A16_EXECUTABLE(\n+ppu_w4a16_executable(\n test_fpA_in …`
- `exec: const p = load("scratch"); const r = await tools.exec_command({ cmd:'set -e python3 root/dev/fold_derivation/overlay_targets_check.py --list mkdir -p actual_overlay/gemv_lowbit shopt -s nullglob files=() for d in quactlize/include tests ben …`
- `exec: const p = load("scratch"); const base = "../../../" + p.replace(/^\//,""); const patch = '*** Begin Patch\n*** Add File: ${base}/CMakeLists.txt\n+cmake_minimum_required(VERSION 3.16)\n+project(overlay_model_gap LANGUAGES CXX)\n+\n+function( …`
- `exec: const p = load("scratch"); const r = await tools.exec_command({"cmd":"cmake -S . -B cmake-build","workdir":p,"yield_time_ms":30000,"max_output_tokens":12000}); text('exit=${r.exit_code}\n${r.output}');`
- `exec: const cmds = [ ["batch_head", "nl -ba benchmarks/run_batch.sh | sed -n '1,120p'"], ["cmake_generated", "nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '380,430p;735,810p'"], ["localgates", "nl -ba ci/local_gates.py | sed -n '1,220p'"], [" …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba ci/local_gates.py | sed -n '80,215p' && nl -ba tests/test_layouts.py | sed -n '360,470p' && nl -ba tests/test_preprocess_ops.py | sed -n '1,75p;350,375p'","workdir":"/root/marlin_ppu/quactli …`

</details>

## Assistant · 2026-08-01 11:57 UTC

The scratch reproduction is conclusive: adding `dev/dev_model_gap.cpp` and registering it made the checker print “33 target(s) … present,” but `build.sh`’s real dev glob did not copy `.cpp`; CMake then skipped the target and failed on its unguarded `target_compile_options`. Separately, the unmodified tree has an even more immediate configure bug: the wrapper prefixes already-absolute generated source paths, so it skips the generated split-K target that `run_batch.sh` requires. I’m running the requested gates now and will distinguish actual coverage from skips/vacuity.

<details><summary>6 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"python3 ./ci/local_gates.py","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"13","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"13","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"14","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"14","yield_time_ms":10000,"max_tokens":20000}`

</details>

## Assistant · 2026-08-01 11:58 UTC

The local tier is still compiling its host/device-front-end gates and buffers output until completion. While it runs, the critical evidence is already stronger than the proposed check’s claim: the present CMake wrapper turns absolute generated paths such as `${_SK_SRCS}` into `${CMAKE_CURRENT_SOURCE_DIR}/<absolute-path>`, judges them missing, and then line 401 errors because the target was never created. This affects a required batch target in the unmodified tree.

<details><summary>23 tool call(s)</summary>

- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"15","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"15","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"16","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"16","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.exec_command({"cmd":"ps -o pid,ppid,etime,stat,cmd -C python3 -C bash -C nvcc -C cicc -C g++ | tail -30","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":5000}); text(r.output);`
- `exec: const p = load("scratch"); const base = "../../../" + p.replace(/^\//,"") + "/root"; const patch = '*** Begin Patch\n*** Update File: ${base}/build.sh\n@@\n-_src_dirs=(quactlize/include tests benchmarks)\n+_src_dirs=("quactlize/include" "te …`
- `exec: const p = load("scratch"); const r = await tools.exec_command({"cmd":"python3 root/dev/fold_derivation/overlay_targets_check.py; rc=$?; printf 'checker exit=%s\\n' \"$rc\"\nbash -c '_src_dirs=(\"quactlize/include\" \"tests\" \"benchmarks\") …`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"20","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"20","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.exec_command({"cmd":"ps -o pid,ppid,etime,stat,cmd -C python3 -C bash -C nvcc -C cicc -C g++ | tail -20","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":4000}); text(r.output);`
- `exec: const r = await tools.exec_command({"cmd":"sed -n '52,82p' ci/local_gates.py | nl -ba","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":5000}); text(r.output);`
- `exec: const r = await tools.exec_command({"cmd":"git status --short && git diff --cached --check && git diff --check","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":5000}); text(r.output);`
- `exec: const p = load("scratch"); const r = await tools.exec_command({ cmd:'set +e cmake -S . -B cmake-build-concise -DGEMV_GROUPS=i4-native -DSPLITK_CFGS=16,32,256,16,16,2 -DMOE_TM_LIST=16 -DMOE_TN_LIST=16 -DMOE_WM_LIST=16 -DMOE_FORMATS=i4 >cmake …`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"25","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"25","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.exec_command({"cmd":"python3 -m pytest tests/ -q","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"26","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"26","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.write_stdin({"session_id":98942,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`

</details>

## Assistant · 2026-08-01 12:04 UTC

The standalone pytest run is green only in the qualified sense: `64 passed, 42 skipped`. Those 42 are not coverage; the extension-backed operator tests skip when `quactlize/_C*.so` is absent, and the CUDA-device refusal case also cannot run here. I’m collecting the exact skip reasons while the longer local tier continues.

<details><summary>20 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"python3 -m pytest tests/ -q -rs","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":30000,"max_output_tokens":12000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"28","yield_time_ms":10000,"max_tokens":12000}`
- `wait: {"cell_id":"28","yield_time_ms":10000,"max_tokens":12000}`
- `exec: const r = await tools.write_stdin({"session_id":65699,"chars":"","yield_time_ms":30000,"max_output_tokens":12000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"30","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"30","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.exec_command({"cmd":"ps -o pid,ppid,etime,stat,cmd --ppid 4431; ps -o pid,ppid,etime,stat,cmd -C python3 | tail -10","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":4000}); text(r.outpu …`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"32","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"32","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.exec_command({"cmd":"ps -o pid,ppid,etime,stat,cmd --ppid 4431","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":3000}); text(r.output);`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"34","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"34","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.exec_command({"cmd":"ps -o pid,ppid,etime,stat,cmd --ppid 4431","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":3000}); text(r.output);`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`
- `wait: {"cell_id":"36","yield_time_ms":10000,"max_tokens":20000}`
- `wait: {"cell_id":"36","yield_time_ms":10000,"max_tokens":20000}`
- `exec: const r = await tools.write_stdin({"session_id":66829,"chars":"","yield_time_ms":30000,"max_output_tokens":20000}); text(r.output); if (r.session_id) text('SESSION_ID=${r.session_id}');`

</details>

## Assistant · 2026-08-01 12:11 UTC

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

- The “swizzle alone” verifier is explicitly admitted to be vacuous because `Stages=3` disables the swizzle at [run_batch.sh:179](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:179).
- `verify_default` records and prints its exit code at line 173 but never increments `fails` when it is nonzero. The overall correctness result can therefore remain green while that control fails.

The repository was not modified; all mutations and CMake outputs were confined to `/tmp`.
