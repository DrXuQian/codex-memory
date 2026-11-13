# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop. FULL LOCAL ACCESS. DO NOT EDIT ANY FILE. Pre-commit review.

Review `git diff --cached`. Context, and it is a failure story you should attack rather than accept:

The box could not build. Symptoms: "No rule to make target test_moe_splitk_bench" plus "cmake did not report
PPU_EXTRA_DEFS". Cause: build.sh registers our example in actlize's examples/CMakeLists.txt foreach list, and a
refactor of mine three commits earlier DELETED that step -- the splice that replaced the overlay copy path took the
registration with it. Restored, with its original guard.

The part I care about is why nothing caught it:
  * dev/fold_derivation/overlay_targets_check.py cmakes the overlay DIRECTLY, so it proves our CMakeLists
    configures and is blind to whether anything reaches it.
  * running build.sh against an incomplete stub SDK died in PPUToolchain's find_library, BEFORE the example is
    processed.
So both local checks were green over a path that stops before the failure point.

The new ci/box_build_dryrun.sh builds a stub SDK (hgcc that exits 0, five empty .so for the find_library names, two
directories) and runs the REAL build.sh, asserting: PPU_EXTRA_DEFS was printed (our CMakeLists was reached), the
target's build.make exists (created in the real build system), and -D<define> is on its compile command. It stops at
the compile, which the stub cannot do. Verified to fail when the registration is removed and pass when restored.

ARGUE:
1. Find a way build.sh can break on the box that this dry-run still would NOT catch. Be concrete; construct it if
   you can (in a scratch copy under /tmp, never in the repo).
2. Is a stub SDK that lets cmake configure a hazard in itself -- can it mask a REAL toolchain problem, or make a
   check pass that should fail? What would you constrain?
3. The three checks now overlap (overlay_targets_check, box_build_dryrun, build.sh's own PPU_DEFS verification).
   Should any be deleted, or do they cover genuinely different things? Say which, plainly.
4. Anything else in the staged diff that is wrong.

- **Thread ID:** `019fc05a-ccb3-7d41-a5bd-e251b2ccf543`
- **Started / last event:** 2026-08-02 02:43 UTC → 2026-08-02 02:55 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T10-43-23-019fc05a-ccb3-7d41-a5bd-e251b2ccf543.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "e732deae625e9a8be0d65010e1e7803fdb170776", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-02_019fc05a_Repo-root-marlin_ppu-quactlize-branch-develop-FULL.md](../transcripts/2026-08/2026-08-02_019fc05a_Repo-root-marlin_ppu-quactlize-branch-develop-FULL.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop. FULL LOCAL ACCESS. DO NOT EDIT ANY FILE. Pre-commit review.

Review `git diff --cached`. Context, and it is a failure story you should attack rather than accept:

The box could not build. Symptoms: "No rule to make target test_moe_splitk_bench" plus "cmake did not report
PPU_EXTRA_DEFS". Cause: build.sh registers our example in actlize's examples/CMakeLists.txt foreach list, and a
refactor of mine three commits earlier DELETED that step -- the splice that replaced the overlay copy path took the
registration with it. Restored, with its original guard.

The part I care about is why nothing caught it:
  * dev/fold_derivation/overlay_targets_check.py cmakes the overlay DIRECTLY, so it proves our CMakeLists
    configures and is blind to whether anything reaches it.
  * running build.sh against an incomplete stub SDK died in PPUToolchain's find_library, BEFORE the example is
    processed.
So both local checks were green over a path that stops before the failure point.

The new ci/box_build_dryrun.sh builds a stub SDK (hgcc that exits 0, five empty .so for the find_library names, two
directories) and runs the REAL build.sh, asserting: PPU_EXTRA_DEFS was printed (our CMakeLists was reached), the
target's build.make exists (created in the real build system), and -D<define> is on its compile command. It stops at
the compile, which the stub cannot do. Verified to fail when the registration is removed and pass when restored.

ARGUE:
1. Find a way build.sh can break on the box that this dry-run still would NOT catch. Be concrete; construct it if
   you can (in a scratch copy under /tmp, never in the repo).
2. Is a stub SDK that lets cmake configure a hazard in itself -- can it mask a REAL toolchain problem, or make a
   check pass that should fail? What would you constrain?
3. The three checks now overlap (overlay_targets_check, box_build_dryrun, build.sh's own PPU_DEFS verification).
   Should any be deleted, or do they cover genuinely different things? Say which, plainly.
4. Anything else in the staged diff that is wrong.

## Files edited via apply_patch (most frequent first)

- `/tmp/quactlize-review.NFnzdE/build.sh` ×2
- `/tmp/quactlize-review.NFnzdE/quactlize/csrc/CMakeLists.txt.in` ×1

## Last assistant conclusions

### 2026-08-02 02:55 UTC

Verdict: request changes. The registration restoration is correct, but the new dry-run has a demonstrated false-positive path and destructive safety problems.

## Findings

- **P1 — The dry-run does not prove compilation was reached.**  
  [box_build_dryrun.sh:68](/root/marlin_ppu/quactlize/ci/box_build_dryrun.sh:68) accepts any failure matching a normal Make recipe error. In `/tmp`, I added a target prerequisite whose command was `/bin/false`. Configuration succeeded, the correct `build.make` contained `-DPPU_PACKED_SCALE=1`, and Make failed before any `hgcc` invocation. The script nevertheless exited 0:

  ```text
  [ok] box_build_dryrun: ... only the stub hgcc compile fails
  ```

  Require a unique sentinel emitted by the stub `hgcc`, preferably with `JOBS=1`, and accept failure only when that sentinel proves the selected target’s compile command ran. Do not classify generic `make: *** [...] Error` as success. Also, the current stub exits 0, so the expected failure is actually missing-object/link failure, not “hgcc compile fails.”

- **P1 — `BOX_DRYRUN_SDK` can delete arbitrary data.**  
  [box_build_dryrun.sh:33](/root/marlin_ppu/quactlize/ci/box_build_dryrun.sh:33) accepts a caller-controlled path, then [line 38](/root/marlin_ppu/quactlize/ci/box_build_dryrun.sh:38) recursively deletes it. Pointing it at a real SDK or the repository would destroy that directory. The fixed default also makes concurrent runs race. Always create a private `mktemp -d`, clean it via a trap, and never recursively remove a caller-supplied existing path.

- **P1 — The “dry-run” mutates and destroys the active build workspace.**  
  It invokes the real script in-place at [box_build_dryrun.sh:51](/root/marlin_ppu/quactlize/ci/box_build_dryrun.sh:51). That deletes the existing real build tree at [build.sh:286](/root/marlin_ppu/quactlize/build.sh:286), replaces it with a stub-generated tree, and cleanup resets the entire tracked examples list at [build.sh:158](/root/marlin_ppu/quactlize/build.sh:158), discarding any pre-existing edits to that file. Run this integration check in an isolated scratch checkout, or provide isolated overlay/build paths and restore the exact original file rather than `git checkout`.

- **P2 — The only registration-aware gate may still be green without running.**  
  Missing `gcc`/CMake returns 2, which [local_gates.py:207](/root/marlin_ppu/quactlize/ci/local_gates.py:207) maps to `SKIP`; skipped checks do not fail the aggregate at [line 229](/root/marlin_ppu/quactlize/ci/local_gates.py:229). That is acceptable for an exploratory local tier, but CI/pre-commit enforcement must reject a skipped `boxdry`, or the original deleted-registration regression can again produce a green exit status.

- **P2 — Define verification is a substring check.**  
  [box_build_dryrun.sh:66](/root/marlin_ppu/quactlize/ci/box_build_dryrun.sh:66) and [build.sh:356](/root/marlin_ppu/quactlize/build.sh:356) would accept `-DSK_QUANT=20` when expecting `-DSK_QUANT=2`. Verify complete shell arguments rather than arbitrary substrings.

- **P3 — Registration presence is also an unscoped substring check.**  
  [build.sh:272](/root/marlin_ppu/quactlize/build.sh:272) can be satisfied by the example name appearing in a comment or outside the `foreach` list. The integration gate should catch the resulting failure, but the local assertion itself overclaims. Match an exact list entry or parse/assert the relevant block.

## Stub SDK assessment

Yes, it necessarily masks real toolchain failures: missing/wrong SDK headers, incompatible libraries, rejected compiler flags, architecture support, linker ABI, and `hgcc` behavior are all outside its coverage. It also supplies optional `libhgrtc` even though [PPUToolchain.cmake:178](/root/marlin_ppu/quactlize/third_party/actlize/cmake/PPUToolchain.cmake:178) treats it as optional, potentially enabling a graph absent on the real box.

That is acceptable only if the check is explicitly constrained to “repository build-graph wiring.” Use the minimum guaranteed SDK surface, omit optional components by default, isolate it completely, and retain a separate real-box toolchain smoke test covering version, headers, compile, and link.

## Should any check be deleted?

No. They cover genuinely different contracts:

| Check | Distinct coverage |
|---|---|
| `overlay_targets_check.py` | Exact overlay contents, direct CMake semantics, broad target creation without an SDK |
| `box_build_dryrun.sh` | Reachability through actlize registration and the generated real build system |
| `build.sh` verification | The actual requested target and definitions on a successful real-SDK build |

Keep all three. The implementation can be consolidated—for example, move the authoritative `build.make` verification before `make` and have the dry-run consume its hard-failure result—but none of the contracts should be removed.

I made no repository changes. The adversarial copy was created under `/tmp` and removed; `bash -n`, Python syntax parsing, and `git diff --cached --check` passed.
