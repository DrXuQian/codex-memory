# CODE QUALITY REVIEW. Read the code. Judge it as code someone else has to maintain and extend, not for correctness or
performance -- both have had their own reviews. Be specific and concrete: name files and lines, and prefer "this
invites bug X" over "this is unclean".

REPO: /root/marlin_ppu/quactlize, branches main and dev. Also /root/marlin_ppu/quactlize/third_party/actlize, branch
ppu-w4a16-dev, which holds the collective this is built around
(include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp, ~1900 lines) and its converter
(include/cutlass/fast_numeric_conversion_for_mix_gemm.h).

The repo was just reorganised for release, modelled on IST-DASLab/qutlass's discipline:
  quactlize/include/   kernels: launchers, format definitions, traits
  tests/               correctness harnesses, C++ mains, each with an independent oracle
  benchmarks/          timing harnesses plus generated-unit machinery
  tools/               offline python
  docs/
  dev branch adds dev/ -- probes, ablations, and fold_derivation/ (1676 files of derivation record)

WHAT TO JUDGE, and I have named the things I already suspect so you can disagree with me rather than agree.

1. COMMENT DENSITY. I write the REASONING into the code -- why a constant is what it is, what was measured, what was
   refuted, what bug a line prevents. Some functions are more comment than code. Argue whether that is maintainable
   or whether it has become a liability: does it age badly, does it hide the code, would a reader find the actual
   control flow? If you would cut it, say WHAT class of comment to cut and what to keep.

2. THE MACRO SPRAWL. Fifteen macros gate ablations and bisects: PPU_PACKED_SCALE, PPU_PACKED_SCALE_NOP,
   PPU_PACKED_PAIR, PPU_F16X2_EARLYCLOBBER, PPU_PACKED_SPLIT_GROUPS, PPU_B_DEQUANT_NOP, PPU_SCALE_SWIZZLE,
   PPU_SCALE_PAD, PPU_SCALE_PREFETCH, PPU_A_PACK, PPU_A_CPASYNC, PPU_B_CHUNK, SK_QUANT, MOEG_*, PPU_FORCE_INSTANTIATE.
   They are #if inside a 1900-line class. What is the right structure for "I need to measure this path with and
   without X" in a CUTLASS-style collective, and what would it cost to move to it?

3. THE PATTERNS THAT HAVE ACTUALLY PRODUCED BUGS in this codebase. Judge whether the code invites them:
   - cute::tuple returned from partition_extra_inputs / partition_extra_mma_info and consumed POSITIONALLY as
     get<0>..get<5>, with the index depending on the conversion mode. Adding an element shifts every consumer.
   - the same buffer viewed through two layouts, both called sS (SmemLayoutScale and SmemCopyLayoutScale), which has
     faulted once as "TSM out of range" and again as a swizzle applied to one view and not the other.
   - two names for one thing: SmemLayoutScalePackedStaged and SmemLayoutScaleRawStaged are the same layout.
   - a definition inside #if A and its use outside it (PPU_SCALE_PAD broke exactly this way).
   - `if constexpr` on a CLASS constant, which does not discard, so both branches instantiate.
   Say which of these are symptoms of one underlying structural problem.

4. TESTS AND BENCHMARKS. tests/ are C++ mains that print MATCH/MISMATCH and return a code; benchmarks/ generate one
   translation unit per configuration through CMake. Is that a reasonable shape? What breaks as the number of formats
   grows? Note run_batch.sh, which exists because the manual procedure had five separate ways to silently measure the
   wrong binary.

5. WHAT WOULD YOU REFACTOR FIRST, and what is the smallest change with the largest effect on maintainability? Rank by
   (effect / risk), not by how much you dislike something. For each: what breaks if it is done wrong, and what test
   in the tree would catch it.

Do not restate the architecture back to me. Findings only.

- **Thread ID:** `019fbb1f-470e-7fd3-920f-220ded56c027`
- **Started / last event:** 2026-08-01 02:20 UTC → 2026-08-01 02:42 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T10-20-17-019fbb1f-470e-7fd3-920f-220ded56c027.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "358f985095087f225d812923c35956d276138b44", "branch": "dev", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-01 02:20 UTC

CODE QUALITY REVIEW. Read the code. Judge it as code someone else has to maintain and extend, not for correctness or
performance -- both have had their own reviews. Be specific and concrete: name files and lines, and prefer "this
invites bug X" over "this is unclean".

REPO: /root/marlin_ppu/quactlize, branches main and dev. Also /root/marlin_ppu/quactlize/third_party/actlize, branch
ppu-w4a16-dev, which holds the collective this is built around
(include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp, ~1900 lines) and its converter
(include/cutlass/fast_numeric_conversion_for_mix_gemm.h).

The repo was just reorganised for release, modelled on IST-DASLab/qutlass's discipline:
  quactlize/include/   kernels: launchers, format definitions, traits
  tests/               correctness harnesses, C++ mains, each with an independent oracle
  benchmarks/          timing harnesses plus generated-unit machinery
  tools/               offline python
  docs/
  dev branch adds dev/ -- probes, ablations, and fold_derivation/ (1676 files of derivation record)

WHAT TO JUDGE, and I have named the things I already suspect so you can disagree with me rather than agree.

1. COMMENT DENSITY. I write the REASONING into the code -- why a constant is what it is, what was measured, what was
   refuted, what bug a line prevents. Some functions are more comment than code. Argue whether that is maintainable
   or whether it has become a liability: does it age badly, does it hide the code, would a reader find the actual
   control flow? If you would cut it, say WHAT class of comment to cut and what to keep.

2. THE MACRO SPRAWL. Fifteen macros gate ablations and bisects: PPU_PACKED_SCALE, PPU_PACKED_SCALE_NOP,
   PPU_PACKED_PAIR, PPU_F16X2_EARLYCLOBBER, PPU_PACKED_SPLIT_GROUPS, PPU_B_DEQUANT_NOP, PPU_SCALE_SWIZZLE,
   PPU_SCALE_PAD, PPU_SCALE_PREFETCH, PPU_A_PACK, PPU_A_CPASYNC, PPU_B_CHUNK, SK_QUANT, MOEG_*, PPU_FORCE_INSTANTIATE.
   They are #if inside a 1900-line class. What is the right structure for "I need to measure this path with and
   without X" in a CUTLASS-style collective, and what would it cost to move to it?

3. THE PATTERNS THAT HAVE ACTUALLY PRODUCED BUGS in this codebase. Judge whether the code invites them:
   - cute::tuple returned from partition_extra_inputs / partition_extra_mma_info and consumed POSITIONALLY as
     get<0>..get<5>, with the index depending on the conversion mode. Adding an element shifts every consumer.
   - the same buffer viewed through two layouts, both called sS (SmemLayoutScale and SmemCopyLayoutScale), which has
     faulted once as "TSM out of range" and again as a swizzle applied to one view and not the other.
   - two names for one thing: SmemLayoutScalePackedStaged and SmemLayoutScaleRawStaged are the same layout.
   - a definition inside #if A and its use outside it (PPU_SCALE_PAD broke exactly this way).
   - `if constexpr` on a CLASS constant, which does not discard, so both branches instantiate.
   Say which of these are symptoms of one underlying structural problem.

4. TESTS AND BENCHMARKS. tests/ are C++ mains that print MATCH/MISMATCH and return a code; benchmarks/ generate one
   translation unit per configuration through CMake. Is that a reasonable shape? What breaks as the number of formats
   grows? Note run_batch.sh, which exists because the manual procedure had five separate ways to silently measure the
   wrong binary.

5. WHAT WOULD YOU REFACTOR FIRST, and what is the smallest change with the largest effect on maintainability? Rank by
   (effect / risk), not by how much you dislike something. For each: what breaks if it is done wrong, and what test
   in the tree would catch it.

Do not restate the architecture back to me. Findings only.

## Assistant · 2026-08-01 02:20 UTC

I’ll review this as a maintenance-risk audit, not a correctness pass. I’ll compare `main`/`dev`, trace the named bug patterns through their actual producers and consumers, and rank refactors by effect-to-risk with specific existing tests that would detect mistakes.

<details><summary>2 tool call(s)</summary>

- `exec: const p = await tools.update_plan({plan:[ {step:"Read repository guidance and map branches/files under review", status:"in_progress"}, {step:"Inspect collective/converter for comments, macros, and recurring bug patterns", status:"pending"}, …`
- `exec: const r = await tools.exec_command({cmd:"git rev-parse --short main dev origin/main origin/dev\ngit log --oneline --decorate --graph --max-count=18 --all\ngit diff --stat main..dev\ngit diff --name-status main..dev\ngit -C third_party/actli …`

</details>

## Assistant · 2026-08-01 02:20 UTC

The requested third-party branch is exactly the checked-out `e70deb02` tip, and the top-level tree is clean on `dev`; `main` is its release subset while `dev` is overwhelmingly the added derivation/probe corpus. I’m treating generated derivation artifacts separately from source-quality findings so they do not distort the review.

<details><summary>7 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"find . -path './.git' -prune -o -path './third_party/actlize/.git' -prune -o -path './dev/fold_derivation' -prune -o -type f -print | sort\n\ngit ls-tree -r --name-only main | sed -n '1,240p'\n\nfind …`
- `exec: const r = await tools.exec_command({cmd:"core=third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp\nconv=third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h\nwc -l \"$core\" \"$co …`
- `exec: const r = await tools.exec_command({cmd:"rg -n 'PPU_(PACKED_SCALE|PACKED_SCALE_NOP|PACKED_PAIR|F16X2_EARLYCLOBBER|PACKED_SPLIT_GROUPS|B_DEQUANT_NOP|SCALE_SWIZZLE|SCALE_PAD|SCALE_PREFETCH|A_PACK|A_CPASYNC|B_CHUNK|FORCE_INSTANTIATE)|SK_QUANT| …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1,520p'",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:50000}) …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '520,1050p'",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:5000 …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1050,1560p'",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:500 …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1560,1969p'",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:500 …`

</details>

## Assistant · 2026-08-01 02:22 UTC

The collective’s comments are already showing “sediment” rather than just density: some are now false or duplicated. For example, the packed channel is labeled “TYPES ONLY … nothing below consumes them” at lines 193–195 despite extensive consumers later; the old non-`cp.async` design explanation at 1369–1372 is duplicated at 1533–1536 after the code moved to staged `cp.async`; and the same 20-line rationale appears twice at 1351 and 1515. I’m distinguishing these from short invariant comments, which are often the strongest part of the file.

<details><summary>7 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '1,360p'",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:50000}); text(r.output) …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '360,700p'",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:50000}); text(r.outpu …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '700,968p'\n\nnl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '1,260p'",workdir:"/ro …`
- `exec: const r = await tools.exec_command({cmd:"git diff --name-status main..dev -- . ':(exclude)dev/fold_derivation/**'\ngit diff --stat main..dev -- . ':(exclude)dev/fold_derivation/**'\n\nfor f in third_party/actlize/include/cutlass/gemm/collec …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba quactlize/include/fold_traits.hpp | sed -n '1,360p'\nnl -ba quactlize/include/moe_grouped_ppu.cuh | sed -n '1,430p'",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens: …`
- `exec: const r = await tools.exec_command({cmd:"rg -n '^\\s*#\\s*(define|undef)\\s+(MOEG_|PPU_)' quactlize/include third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp third_party/actlize/include/cutlass/fast_ …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba benchmarks/run_batch.sh | sed -n '1,180p'\nnl -ba build.sh | sed -n '1,330p'\nrg -n 'enable_testing|add_test|ctest|MATCH|MISMATCH|return [0-9]|ppu_w4a16_executable|file\\(WRITE|execute_process …`

</details>

## Assistant · 2026-08-01 02:23 UTC

One concrete test-shape problem is stronger than “these are standalone mains”: several correctness programs print `MISMATCH` but still return success. `test_w4a16_diag.cu`, `test_w2a16_diag.cu`, and `test_w1a16_diag.cu` compute `bad`, print it, then unconditionally `return 0`; `test_w2a16_real.cu` does the same. Those cannot become reliable CTest/CI gates without fixing exit semantics first, and `run_batch.sh` currently pipes/greps output in ways that also discard the program status.

<details><summary>13 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"for f in tests/*.cu; do echo \"--- $f\"; rg -n 'int main|bad[[:space:]]*=|MISMATCH|PASS|FAIL|return ' \"$f\" | tail -35; done",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_toke …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba tests/test_fpA_intB_ppu.cu | sed -n '1,180p'\nnl -ba tests/test_moe_gemm_ppu.cu | sed -n '1,100p'\nnl -ba tests/test_moe_grouped_ppu.cu | sed -n '1,180p'\nnl -ba tests/test_w4a16_diag.cu | sed …`
- `exec: const r = await tools.exec_command({cmd:"rg -n 'run_batch|PIPESTATUS|pipefail' . --glob '!third_party/**' --glob '!dev/fold_derivation/.moe_units_check*/**'\n\nnl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '220,390p'\nnl -ba quactlize/cs …`
- `exec: const r = await tools.exec_command({cmd:"for f in quactlize/csrc/CMakeLists.txt.in build.sh benchmarks/run_batch.sh; do awk 'BEGIN{c=0;b=0;x=0} /^[[:space:]]*#/{c++} /^[[:space:]]*$/{b++} !/^[[:space:]]*(#|$)/{x++} END{printf \"%5d comment- …`
- `exec: const r = await tools.exec_command({cmd:"rg -n 'QuantMode::|QM::|PerCol|FinegrainedScaleOnly|FinegrainedScaleZero' tests/*.cu benchmarks/*.cu benchmarks/*.hpp | sed -n '1,420p'\n\nrg -n 'using QuantMode|enum class QuantMode|is_finegrained'  …`
- `exec: const r = await tools.exec_command({cmd:"for f in third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_fold.hpp third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp; do echo \"--- $f\"; wc -l \"$ …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba build.sh | sed -n '168,260p'\nnl -ba CMakeLists.txt | sed -n '1,60p'\nnl -ba README.md | sed -n '1,95p'\nrg -n 'TARGET=' build.sh | sed -n '1,100p'\nrg -n 'test_(w1|w2|w4|q4k|lowbit|moe_groupe …`
- `exec: const r = await tools.exec_command({cmd:"git show --stat --oneline 12af255\ngit show --format=fuller --no-ext-diff 12af255 -- build.sh | sed -n '1,300p'\n\ngit blame -L 50,165 -- build.sh | sed -n '1,140p'\n\ntest -e fold_derivation && echo …`
- `exec: const p = await tools.update_plan({explanation:"Repository/branch mapping and the core collective/converter pass are complete. I found additional release-reorg and test-gating risks that directly affect maintainability, so I am incorporatin …`
- `exec: const r = await tools.exec_command({cmd:"bash -n build.sh benchmarks/run_batch.sh dev/sweep.sh\nif command -v shellcheck >/dev/null 2>&1; then shellcheck -S warning build.sh benchmarks/run_batch.sh dev/sweep.sh; else echo 'shellcheck unavai …`
- `exec: const r = await tools.exec_command({cmd:"git -C third_party/actlize log --oneline --follow -- include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1,120p'\nfor f in include/cutlass/gemm/collective/ppu_mma_aiu_mul …`
- `exec: const r = await tools.exec_command({cmd:"rg -n 'real_weight/|fold_derivation/|tests/data|data/' tests benchmarks tools build.sh quactlize/include third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp thi …`
- `exec: const r = await tools.exec_command({cmd:"rg -n 'MOE_STAGES|MOE_TK|MOE_.*LIST' quactlize/csrc/CMakeLists.txt.in build.sh benchmarks | sed -n '1,220p'\nrg -n 'set\\(_MOE_ST|UNIT_ST|STAGES' benchmarks/moe_bench_unit.inc benchmarks/lowbit_moe_b …`

</details>

## Assistant · 2026-08-01 02:30 UTC

The release reorganization itself has left several maintainability traps: `build.sh` still looks for checks under the now-nonexistent root `fold_derivation/`, while the files live under `dev/fold_derivation/`; its checkout-equivalence check compares flattened overlay files against repository-root basenames, and will compare the overlaid device `CMakeLists.txt` against the unrelated root tooling `CMakeLists.txt`. Separately, six test defaults/comments still point at removed `real_weight/` paths instead of `tests/data/` and `tools/`. These are exactly the kind of path drift the new structure was meant to prevent.

<details><summary>1 tool call(s)</summary>

- `exec: const p = await tools.update_plan({explanation:"The tests/benchmarks and release-reorganization review is complete, including static validation of exit handling, overlay path checks, generated-unit growth, and main/dev branch skew. I am now …`

</details>

## Assistant · 2026-08-01 02:32 UTC

I’ve finished the static inspection. The sharpest issue is not comment volume or even macro count by itself; it is that several release-facing checks can report success without having tested the intended code, while the collective’s scale channel has no single typed owner.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.update_plan({explanation:"Static review and branch comparison complete; synthesizing findings with exact locations and effect/risk ordering.",plan:[{step:"Map main/dev and the actlize branch, including release-reorgani …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"regs_measured_offset|The following is a retraction|retraction|occupancy\" quactlize/include third_party/actlize/include | head -40\nrg --files quactlize/include | rg 'fold_traits|gemv_lowbit' …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '720,750p;1100,1260p;1338,1412p;1508,1598p;1600,1692p;1785,1910p'\nnl -ba third_party/actliz …`

</details>

## User · 2026-08-01 02:34 UTC

DEBATE, ROUND 2. I verified your two structural findings against the tree and both hold, so I concede more than I
defend. Where I push back I say what evidence I have.

VERIFIED, AND I WITHDRAW ACCORDINGLY:
* test_moe_splitk_bench.cu:87 fills hSc with 0.0625 and hZr with -0.0625. The bench never sees the real fixture, so
  d = dmin = 0.0625, normal. My "packnop timed the denormal path" fix rests on a false premise and I have to correct
  the record. That is the second time I attached the 80.5%-subnormal-d fact to the wrong effect.
* tests/test_moe_grouped_verify.cu hardcodes Stages = 3, and the swizzle gate requires a power of two, so the swizzle
  was never active in that launch. My C1 mechanism ("a view lost the swizzle") is wrong, and my gate_swz_only row
  measured nothing at all.
* C4 concede: the full decoder consumes all four u[] words and the NOP only u[0], so "keeps everything else" is false
  regardless of values.
* C3 concede as stated: packsplit adds duplicated unit reads and per-column setup, so its loss does not price the
  placement benefit at zero. Your difference-of-differences is better than anything I proposed.

WHERE I PUSH BACK, and what would settle each.

P1. "The default build of that verifier should die identically" is a PREDICTION, not a finding. It is one build to
    check and run_batch.sh never built that control -- I will add it. But if the default build does NOT die, your
    explanation fails and mine is back on the table. Which do you actually expect, and what in the code decides it?
    Give the exact condition under which line 1661's assert is reached, in terms of gs, TileK and Scale_TileK, and say
    which shapes in _SPLITK_CFGS and which verifier invocations satisfy it.

P2. I still hold one piece of positive evidence you have not addressed: test_q4k_packed_gemm with
    PPU_PACKED_SCALE=1 + PPU_SCALE_SWIZZLE=1 PASSES rowC, and that row is TN=128 Stages=2, i.e. the swizzle IS active
    there. So the swizzle is not simply broken. Does that change your no-ship position, or is 7% on the target row
    enough on its own? Be concrete about what coverage would be needed to reconsider.

P3. On C2 we may be closer than the wording suggests. I do not need "43% of instructions equals 11% of time" -- I need
    the decision-relevant claim, which is that TODO #18 cannot be worth more than about 11% on this row and is
    probably low single digits. You appear to agree. Say plainly whether you do, and if so what the remaining
    disagreement actually is, because I do not want to argue about a formulation neither of us needs.

NOW THE THING I WANT MOST, and your answer was cut off mid-sentence.

You began constructing a clean synthetic input: d = dmin = x, every sc = 1, every mn = 7, so the full Q4_K decode
gives scale = x and zero = 8x - 7x = x. Finish it. I want a bench input for which the packed path and the fp16-plane
path compute the SAME values, so pack against base is a like-for-like timing comparison instead of two kernels
computing different numbers. Specify:
  - the exact byte layout the packed path needs so that reinterpreting it yields those codes, given
    gguf_packed_scale.h's bit map;
  - what the fp16-plane buffer must contain so both paths agree;
  - where in test_moe_splitk_bench.cu it goes, and what breaks if the two buffers are sized differently;
  - and whether the resulting timing is then honest, or whether some other difference still makes it not so.

Then give me the exact run_batch.sh variant list you would build next, including your splitnop and the missing
default-build verifier control. Names and defines, ready to paste.

## Assistant · 2026-08-01 02:34 UTC

I’ll resolve P1 from the instantiated conditions, then trace the packed-byte decoder against the benchmark’s allocations and produce a paste-ready variant matrix. I’ll treat the rowC pass as positive but scoped evidence, not fold it into a generic swizzle verdict.

<details><summary>5 tool call(s)</summary>

- `exec: const p = await tools.update_plan({plan:[{step:"Derive the exact coarse/fine scale branch and assert reachability for every split-K and verifier shape","status":"in_progress"},{step:"Trace the GGUF packed-scale bit map and construct byte-id …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"_SPLITK_CFGS|splitnop|packnop|gate_swz|PPU_SCALE_SWIZZLE|PPU_PACKED|run_variant|VARIANT|test_moe_grouped_verify|test_moe_splitk_bench\" benchmarks tests CMakeLists.txt build.sh quactlize/incl …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"if constexpr \\(false\\)|assert\\(false\\)|FINE|COARSE|Scale_TileK|K_BLOCK_MAX|transform_B_kblock\" third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp  …`
- `exec: const r = await tools.exec_command({cmd:"rg --files | rg 'CMakeLists\\.txt\\.in$|moe_splitk_units|gguf_packed_scale|splitk.*cmake|gen_moe'\nrg -n \"_SPLITK_CFGS|SPLITK_CFGS\" . --glob '!dev/fold_derivation/**'\nnl -ba third_party/actlize/in …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '230,390p'\nnl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '1,280p'\nnl -ba tests/test_q4k_packed_gemm.cu | sed -n '1,285p'\n …`

</details>

## Assistant · 2026-08-01 02:35 UTC

## Highest-risk findings

1. The release-facing correctness gate can silently pass failures.

   [run_batch.sh:17](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:17) enables only `set -u`. In `do_check`, executables are piped through `grep`, `tr`, and `tail` at [run_batch.sh:77](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:77). Without `pipefail`, the executable’s status is lost; `MISMATCH` or a crash can still leave `do_check` successful and allow `all` to proceed to timing. The binary copying, define inspection, and MD5-distinctness checks are valuable, but the most important signal is currently discarded.

   Four diagnostic programs independently have the same problem: they print `MISMATCH` and return zero:

   - [test_w4a16_diag.cu:80](/root/marlin_ppu/quactlize/tests/test_w4a16_diag.cu:80)
   - [test_w2a16_diag.cu:79](/root/marlin_ppu/quactlize/tests/test_w2a16_diag.cu:79)
   - [test_w1a16_diag.cu:82](/root/marlin_ppu/quactlize/tests/test_w1a16_diag.cu:82)
   - [test_w2a16_real.cu:77](/root/marlin_ppu/quactlize/tests/test_w2a16_real.cu:77)

   This is the smallest change with the largest maintainability effect: make mismatch exit nonzero, preserve executable status separately from log filtering, and aggregate failures. No existing test checks the harness itself; it needs a shell-level test with stub binaries returning 0, 1, and crashing.

2. Several build-time “release discipline” checks are not examining the paths they claim to examine.

   [build.sh:56](/root/marlin_ppu/quactlize/build.sh:56) looks for checks under `fold_derivation/`. On `dev`, they are under `dev/fold_derivation/`; on `main`, they are absent. Consequently these checks silently do nothing.

   The overlay verification at [build.sh:137](/root/marlin_ppu/quactlize/build.sh:137) flattens files to basenames, then compares against `$HERE/$basename`. Most canonical files live under `include/`, `tests/`, or `benchmarks/`, so they are skipped. `CMakeLists.txt` can instead be compared with the unrelated root CMake file. This invites exactly the stale-overlay/wrong-binary problem the script is intended to prevent.

3. Release `main` still contains two byte-identical copies of all nine GEMV headers:

   - `quactlize/include/gemv_lowbit/`
   - `quactlize/include/gemv/gemv_lowbit/`

   `dev` deletes the nested copy. On `main`, a future fix can land in one path while a consumer includes the other. If the old include path is public, leave forwarding headers; do not retain two implementations.

## Comment density

The density itself is defensible. I would not impose a percentage target. The converter’s comments often turn difficult layout reasoning into maintained contracts:

- [fast_numeric_conversion_for_mix_gemm.h:87](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:87) derives `MixGemmEmit` and checks bijectivity.
- [fast_numeric_conversion_for_mix_gemm.h:138](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:138) pins the int4 composition with a `static_assert`.
- [fast_numeric_conversion_for_mix_gemm.h:216](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:216) centralizes chunk placement.

Those comments should stay because they state invariants, units, mappings, ownership, and the consequence of changing them.

The liability is chronological sediment mixed into control flow:

- [collective:193](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:193) says the packed channel is “types only”; it is now consumed extensively.
- [collective:1351](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1351) and [collective:1515](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1515) duplicate essentially the same long explanation.
- [collective:1369](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1369) says the channel is no longer `cp.async`; the current implementation stages raw packed bytes with `cp.async`.
- [converter:734](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:734) names the retired `MixGemmInt1Emit`, while the call is to `MixGemmChunkEmit`.
- [fold_traits.hpp:171](/root/marlin_ppu/quactlize/quactlize/include/fold_traits.hpp:171) explains why the occupancy model ceased to fit later evidence, yet the file still exports `regs_measured_offset` at [fold_traits.hpp:201](/root/marlin_ppu/quactlize/quactlize/include/fold_traits.hpp:201).

Many comments cite `fold_derivation/lXX`, but that evidence is absent from release `main`, and the actual `dev` path is `dev/fold_derivation`. Release readers cannot follow the references.

Cut or move:

- Experiment timelines, session narratives, refuted alternatives, shape-specific percentages, profiler transcripts, and “this used to…” histories.
- Command recipes and references to unshipped paths.

Keep inline:

- Layout equations and units.
- Buffer ownership and synchronization requirements.
- Preconditions and failure consequences.
- Short explanations of why an apparently simpler edit is invalid.
- Bug explanations backed by a nearby assertion or named test.

A particularly important comment that should become code is [collective:560](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:560): `smem_b` alignment is said to hold “by arithmetic, not declaration.” A preceding member-size change can revive the TSM fault. Encode the alignment or assert the offset.

## Macro sprawl

The named macros are not one category:

- `SK_QUANT` is benchmark configuration.
- `PPU_FORCE_INSTANTIATE` is a useful build-validation hook at [moe_grouped_ppu.cuh:148](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:148).
- `PPU_B_CHUNK` lives in the separate fold collective.
- Several `MOEG_*` controls are launch/diagnostic plumbing.

Those are reasonable at translation-unit boundaries. The dangerous macros are the ones that independently alter types, shared storage, layouts, and control flow inside the collective.

There is already an invalid-combination hazard: `PPU_A_CPASYNC` affects layout selection at [collective:401](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:401), while `PPU_A_PACK` affects storage at [collective:554](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:554). Later sites give each flag different precedence. Defining both produces a hybrid path; there is no central rejection. Likewise, packed-scale sub-flags silently do nothing without `PPU_PACKED_SCALE`.

The CUTLASS-style replacement should be a typed policy selected at the outer instantiation boundary, with separate components such as:

- A transport
- Scale transport
- Scale physical layout
- Scale decode
- B conversion
- Diagnostic/ablation behavior

The generated translation unit can still define macros temporarily; one compatibility header should translate them into one policy type and reject impossible combinations. Do not generate a whole collective for every Cartesian combination.

A full conversion is medium-high risk: every kernel type changes, all instantiations rebuild, and the three related collectives must share the same components. A staged migration is much cheaper:

1. Centralize macro normalization and `static_assert` invalid combinations.
2. Introduce one policy type without changing implementation.
3. Move one feature family at a time behind specialized helpers.
4. Keep ablation-only aliases under benchmarks/dev.

There is also ordinary macro leakage in a public header: [moe_grouped_ppu.cuh:360](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:360) defines `MOEG_SCHED`, `MOEG_CALL`, and `MOEG_FG`, but only `MOEG_CALL` is undefined at line 391. `MOEG_SCHED`, `MOEG_FG`, and the stringification macros at line 32 remain visible to includers.

## Bug-producing structural patterns

These are two underlying problems, not one.

First: the scale channel has no typed semantic owner.

- `partition_extra_inputs` returns five or seven positional elements at [collective:1242](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1242).
- Consumers calculate mode-dependent indices at [collective:1121](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1121).
- `partition_extra_mma_info` repeats the pattern at [collective:1540](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1540).
- A dead/repointed `sSp` object is retained around [collective:1575](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1575) specifically to avoid shifting tuple positions.

That is direct evidence the representation is controlling the implementation. Replace these tuples with named aggregates such as `ScaleLoadPartitions` and `ScaleMmaPartitions`. Members can remain CUTE tensors; no physical layout need change.

The same missing owner explains the dual `sS` views. The write view is constructed at [collective:1186](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1186), while the MMA view is reconstructed independently around [collective:1554](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1554). Both variables are called `sS`, hiding their different coordinate meanings. A `ScaleSmemChannel` should own the physical buffer and derive explicitly named `write_view()` and `mma_view()` objects.

`SmemLayoutScaleRawStaged` and `SmemLayoutScalePackedStaged` at [collective:236](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:236) are identical. The second should at least alias the first; two independent spellings invite one to acquire padding or swizzling without the other.

Second: feature configuration cuts across declaration, storage, and use boundaries.

That is the common cause of the `#if A` definition / outside use failure and the hybrid macro paths. Features should select complete components, not expose partially conditional local names.

I disagree with the `if constexpr` diagnosis as written at [collective:1351](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1351). Standard C++ does discard a false `if constexpr` branch; a class constant does not generally prevent that. The same file relies successfully on class constants to select different return types at [collective:736](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:736). If hgcc/EDG behaves differently, document it as a compiler-specific limitation with a minimal reproducer and version. Otherwise the current explanation is folklore and has encouraged unconditional superset tuples—the exact representation making the code fragile.

One especially suspicious residue is [collective:1684](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1684): an `if constexpr(false)` followed by an unconditional `assert(false)` alternative. Either it is reachable and debug builds fail, or it is dead code obscuring supported modes.

## Tests and benchmarks

Independent C++ mains are reasonable for a specialized toolchain, but only with strict exit semantics and an aggregate runner. There is no `enable_testing()` or `add_test()` in the tree, so additions are registered manually and nothing checks suite completeness.

Three files under `tests/` explicitly perform timing rather than correctness:

- [test_fpA_intB_ppu.cu:1](/root/marlin_ppu/quactlize/tests/test_fpA_intB_ppu.cu:1)
- [test_moe_gemm_ppu.cu:1](/root/marlin_ppu/quactlize/tests/test_moe_gemm_ppu.cu:1)
- [test_moe_grouped_ppu.cu:1](/root/marlin_ppu/quactlize/tests/test_moe_grouped_ppu.cu:1)

That weakens the release promise that `tests/` means an independent oracle.

One translation unit per configuration is a sound choice here; it isolates compiler work and permits parallel builds. The scaling problem is configuration enumeration. [benchmarks/device/CMakeLists.txt.in:255](/root/marlin_ppu/quactlize/benchmarks/device/CMakeLists.txt.in:255) and [benchmarks/device/CMakeLists.txt.in:561](/root/marlin_ppu/quactlize/benchmarks/device/CMakeLists.txt.in:561) contain separate string-based Cartesian generators. Each new format expands compile/link volume and requires edits in multiple tables, labels, dispatch lists, fixtures, and oracles. Runtime filters do not reduce that build cost.

Keep per-TU generation, but move the format/configuration schema into one validated manifest that emits the units and CMake source list. The existing generator checks under `dev/fold_derivation` should become release tooling.

Several tests also default to stale `real_weight/...` paths, for example [test_q4k_packed_gemm.cu:44](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:44) and [test_w2a16_real.cu:27](/root/marlin_ppu/quactlize/tests/test_w2a16_real.cu:27), although fixtures moved under `tests/data`. New maintainers following the source comments will test the wrong location or conclude fixtures are missing.

## Refactor order by effect/risk

1. **Make gates honest and repair release paths.**  
   Risk: stricter status handling may expose existing failures; careless `pipefail` use can make optional `grep` output fatal.  
   Catch: no existing harness self-test; add stub-based shell coverage. Existing oracle tests then become meaningful.

2. **Replace positional extra-input/MMA tuples with named aggregates, without changing layouts.**  
   Risk: misassigning scale/zero/packed members or modes.  
   Catch: `test_q4k_packed_gemm`, `test_moe_grouped_verify`, `test_q65_bconcat_real`, and `test_lowbit_grouped`.

3. **Give scale shared memory one owner and derive named write/read views from it; collapse the duplicate staged-layout names.**  
   Risk: stage/group coordinate or swizzle mismatch, shared-memory overrun.  
   Catch: packed Q4 rows covering both scale-only and scale-with-zero, grouped scale-swizzle builds, plus the existing hardware TSM verifier.

4. **Add centralized configuration validation, then introduce the typed-policy compatibility bridge.**  
   Risk: an ablation becomes silently inactive or selects the wrong storage specialization.  
   Catch: `run_batch.sh`’s binary/hash/define checks once fixed, forced-instantiation builds, packed Q4, grouped verification, and B-chunk tests.

5. **Move historical commentary into decision records and repair all surviving references.**  
   Risk: deleting the only record of a synchronization or layout invariant.  
   Catch: no runtime test; require every retained bug-prevention comment to point to an assertion, test, or stable document.

6. **Replace duplicated CMake configuration tables with one validated manifest while retaining one TU per configuration.**  
   Risk: omitted, duplicate, or mislabeled instantiations.  
   Catch: move the generator-check scripts into release tooling and compare generated unit names/counts deterministically.

This was a static maintainability review; I did not execute the PPU-dependent binaries.

<details><summary>8 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '30,120p;120,250p'\nnl -ba tests/test_q4k_packed_gemm.cu | sed -n '25,210p'\nrg -n \"struct Band|dSc|dZr|scale_k\" benchmarks/l …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '900,1065p'\nrg -n \"K_ATOM_PER_COPY|K_BLOCK_MAX|TilerB|SmemCopyAtomB|GmemTiledCopyB\" third …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"CMAKE_BUILD_TYPE|NDEBUG|DNDEBUG|assert\" build.sh quactlize/csrc/CMakeLists.txt.in third_party/actlize/CMakeLists.txt third_party/actlize/cmake third_party/actlize/tools 2>/dev/null | head -2 …`
- `exec: const r = await tools.exec_command({cmd:"find third_party/actlize/build_w4a16_compare -path '*test_moe_grouped_verify.dir*' -type f \\( -name flags.make -o -name build.make \\) -print 2>/dev/null | head -20\nfor f in $(find third_party/actl …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"function\\(ppu_w4a16_executable|ppu_w4a16_executable|CMAKE_CXX_FLAGS|CMAKE_BUILD_TYPE|PPU_EXTRA_DEFS|hgcc\" quactlize/csrc/CMakeLists.txt.in third_party/actlize/CMakeLists.txt third_party/act …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/cmake/PPUToolchain.cmake | sed -n '130,180p;235,280p;315,375p'\nrg -n \"NDEBUG|CMAKE_BUILD_TYPE|CONFIG\" third_party/actlize/cmake/PPUToolchain.cmake third_party/actlize/cm …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '130,205p'\nrg -n \"ScaleSwizzleFor\" third_party/actlize/include/cutlass/gemm/collective/pp …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"TODO #18|#18|TODO.*18\" . --glob '!dev/fold_derivation/**' --glob '!third_party/actlize/docs/**' | head -100\nrg -n \"43%|11%|low single|bdqnop|dequant\" docs benchmarks/run_batch.sh third_pa …`

</details>

## Assistant · 2026-08-01 02:40 UTC

P1 is now mechanically determined: the offending assert is on the coarse scale path, and the current split-K batch at `gs=32` never enters that path. The verifier’s default `gs=128` does. The device compile command also does not inherit CMake’s Release `-DNDEBUG`, so I expect the unmodified verifier control to assert too.

<details><summary>2 tool call(s)</summary>

- `exec: const r = await tools.update_plan({explanation:"Derived branch reachability, decoded the packed format byte-for-byte, and mapped the benchmark pointer-selection requirement and next build matrix.",plan:[{step:"Derive the exact coarse/fine s …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba benchmarks/run_batch.sh | sed -n '20,145p'\ngit status --short","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":18000}); text(r.output)`

</details>

## Assistant · 2026-08-01 02:42 UTC

## P1 — I expect the default verifier to die too

The relevant code has shifted to [the collective at line 1691](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1691). The assert is reached when all of these are true:

1. `ModeHasScales`.
2. The coarse path is selected:

   ```cpp
   Scale_TileK <= K_BLOCK_MAX
   ```

3. A new scale group starts:

   ```cpp
   k_block % GroupK == 0
   GroupK = K_BLOCK_MAX / Scale_TileK
   ```

For these int4 shapes, the B copy step is 64 K elements, so:

```text
K_BLOCK_MAX = TileK / 64
Scale_TileK = ceil(TileK / gs)
```

Therefore the decisive condition is:

```text
ceil(TileK / gs) <= TileK / 64
```

Once that condition holds, `k_block == 0` is inevitably presented: the prefetch explicitly calls the function with zero when there is an RF pipeline, and the one-block loop wraps back to zero otherwise. Thus the assert is not intermittent once reached.

For `_SPLITK_CFGS`:

| `gs` | TK=64 | TK=128 | TK=256 | Assert? |
|---:|---:|---:|---:|---|
| 16 | SK=4, KBM=1 | SK=8, KBM=2 | SK=16, KBM=4 | No; fine path |
| 32 | SK=2, KBM=1 | SK=4, KBM=2 | SK=8, KBM=4 | No; fine path |
| 64 | SK=1, KBM=1 | SK=2, KBM=2 | SK=4, KBM=4 | Yes; all rows |
| 128 | SK=1, KBM=1 | SK=1, KBM=2 | SK=2, KBM=4 | Yes; all rows |

So the current `run_batch.sh` band at `gs=32` reaches the assert in none of the fifteen configurations in [the configuration table](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:255).

The verifier is different:

- `./test_moe_grouped_verify 8 1` defaults to `gs=128`.
- It selects `TileK=128`.
- `Scale_TileK=1`, `K_BLOCK_MAX=2`.
- It is `FinegrainedScaleOnly`, so `ModeHasScales=true`.
- It enters the coarse path and asserts at the first group boundary.

Other verifier cases:

- `gs=128`: assert.
- `gs=64`: `TileK=64`, SK=1, KBM=1 — assert.
- `gs=32`: `TileK=64`, SK=2, KBM=1 — fine path, no assert.
- `L`, `Mb`, and raggedness do not change this branch, provided the launch is accepted.

I still expect the default verifier binary to die identically. Although CMake defaults to Release, the hgcc custom command at [PPUToolchain.cmake:263](/root/marlin_ppu/quactlize/third_party/actlize/cmake/PPUToolchain.cmake:263) does not forward the Release flags or `-DNDEBUG`. The bare `assert(false)` should therefore survive device compilation.

If the default build does not die:

- First establish whether hgcc implicitly defines `NDEBUG`. If it does, neither build should reach this assert.
- If only the `PPU_SCALE_SWIZZLE=1` build dies, my assert explanation fails.
- But C1 does not come back: `Stages=3` makes the explicit power-of-two test false at [line 481](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:481), so the swizzle type is not selected. That result would instead indicate macro-sensitive code generation or latent undefined behavior.

## P2 — the rowC pass changes the correctness verdict

Yes: rowC passing with packed scale plus active swizzle refutes “the swizzle is simply broken.” It validates the two swizzled views for exactly:

```text
ScaleZero, packed decode, TN=128, TK=256, SK=8, Stages=2
```

I withdraw the correctness-based no-ship claim. The present status should be “not enabled by default,” for performance and incomplete coverage—not “known incorrect.”

The reported 7% loss is enough to reject the optimization only if it repeats. A single 7% result is not decisive against the recorded 13–17% run dispersion. If alternating or randomized base/swizzle runs across multiple independently built binary pairs still show roughly −7%, that alone is enough not to ship it as a default: it has no functional benefit that could compensate for a target-row regression.

Minimum correctness coverage before reconsidering:

- `PPU_SCALE_SWIZZLE=1` without packed scale on `test_q4k_packed_gemm` rowC. This exercises the active swizzle on the fp16 planes.
- Packed scale plus swizzle on rowC, repeatedly because rowC has been intermittent.
- ScaleOnly as well as ScaleZero under an active swizzle.
- Stages 2 and 4.
- Each enabled specialization: TN 32, 64, and 128.
- One N residue, rather than only `N % TileN == 0`.
- At least one split-K run.

Alternatively, narrow the production gate to the one validated configuration. Then the TN32/TN64/Stages4 coverage is unnecessary because those configurations cannot select it.

## P3 — yes, I agree with the decision-relevant claim

I agree that approximately 11% is the upper bound for TODO #18 on this row, assuming the `base − bdqnop` result survives repetition. TODO #18 retains part of the pipeline that `bdqnop` removes, so its realizable gain must be smaller and low single digits is a reasonable planning estimate.

The remaining disagreement is only evidentiary: “probably low single digits” is not yet a measurement. `bdqnop` removes more than the constants TODO #18 would fold, including almost all elementwise conversion/affine work. The 43%-of-instructions observation does not partition the measured 11% among those operations. Implementation or a narrower ablation would settle the exact gain. It should not block prioritization.

## Like-for-like synthetic packed input

Choose:

```text
x = 0.0625 = fp16 bits 0x2c00
d = dmin = x
sc[g] = 1
mn[g] = 7
```

Then for every group:

```text
scale = d * sc = x
zero  = 8*scale - dmin*mn = 8x - 7x = x
```

The bit positions are defined by [gguf_packed_scale.h:38](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:38):

```text
bit(g, which) = 32 + 6*(g % 4) + 48*(g / 4) + 24*which
which=0: sc
which=1: mn
```

Four six-bit values of `1` pack to the 24-bit little-endian value `0x041041`, or:

```text
41 10 04
```

Four values of `7` pack to `0x1c71c7`, or:

```text
c7 71 1c
```

Thus every 16-byte unit is exactly:

```text
00 2c  00 2c  41 10 04  c7 71 1c  41 10 04  c7 71 1c
^^^^^  ^^^^^  ^^^^^^^^  ^^^^^^^^  ^^^^^^^^  ^^^^^^^^
 d      dmin    sc 0–3    mn 0–3    sc 4–7    mn 4–7
```

The global physical order must be:

```text
[L][nsb][N][16]
offset(e,b,n,byte) = (((e * nsb + b) * N + n) * 16 + byte)
nsb = scale_k / 8 = K / 256        // for gs=32
```

That matches the tensor strides created at [the collective’s packed input construction](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:729).

The fp16 planes must contain:

```cpp
hSc[...] = half_t(0.0625f);
hZr[...] = half_t(0.0625f);  // positive x, not the present -0.0625
```

Their physical indexing remains:

```text
[L][scale_k][N]
((e * scale_k + g) * N + n)
```

### Where it belongs

Construct both representations where [test_moe_splitk_bench.cu currently initializes `hSc` and `hZr`](/root/marlin_ppu/quactlize/benchmarks/test_moe_splitk_bench.cu:84):

```cpp
#include "cutlass/gguf_packed_scale.h"

// Require this only for a packed-scale measurement.
if (bd.scale_k % 8 != 0) {
  std::printf("packed-scale synthetic input needs scale_k %% 8 == 0\n");
  return 1;
}

half_t const x(0.0625f);
std::fill(hSc.begin(), hSc.end(), x);
std::fill(hZr.begin(), hZr.end(), x);

size_t const nsb = size_t(bd.scale_k / 8);
std::vector<uint8_t> hPk(size_t(bd.L) * nsb * bd.N * 16, 0);

for (int e = 0; e < bd.L; ++e)
  for (size_t b = 0; b < nsb; ++b)
    for (int n = 0; n < bd.N; ++n) {
      uint8_t* u = hPk.data() + ((size_t(e) * nsb + b) * bd.N + n) * 16;
      uint16_t const xb = x.raw();
      std::memcpy(u + 0, &xb, 2);
      std::memcpy(u + 2, &xb, 2);
      for (int g = 0; g < 8; ++g) {
        cutlass::gguf_packed::put_code(u, g, 0, 1);
        cutlass::gguf_packed::put_code(u, g, 1, 7);
      }
    }

cutlass::DeviceAllocation<uint8_t> dPk(hPk.size());
dPk.copy_from_host(hPk.data());
```

Pointer selection cannot safely happen only in `main()`. One generated binary contains both TK256 packed configurations and TK64/TK128 fallback configurations. Under `PPU_PACKED_SCALE`, the latter still require the fp16 plane.

Add a packed pointer to `SkCtx` at [moe_splitk_bench_common.hpp:97](/root/marlin_ppu/quactlize/benchmarks/moe_splitk_bench_common.hpp:97), assign it near [test_moe_splitk_bench.cu:128](/root/marlin_ppu/quactlize/benchmarks/test_moe_splitk_bench.cu:128), and select it per generated row before [the launch at line 123](/root/marlin_ppu/quactlize/benchmarks/moe_splitk_bench_common.hpp:123):

```cpp
// SkCtx
half_t const* dPackedScale;

// main()
cx.dPackedScale = reinterpret_cast<half_t const*>(dPk.get());

// sk_row()
half_t const* scale_ptr = bd.dSc;
#if defined(PPU_PACKED_SCALE) && (PPU_PACKED_SCALE != 0)
if constexpr (SK_QUANT != 0) {
  if ((TK + bd.gs - 1) / bd.gs == 8)
    scale_ptr = cx.dPackedScale;
}
#endif
```

Then pass `scale_ptr`, not `bd.dSc`, to `launch_splitk`.

For this specific representation the byte sizes are exactly equal:

```text
packed bytes = L * (scale_k/8) * N * 16
             = L * scale_k * N * 2
fp16 scale bytes = L * scale_k * N * sizeof(half_t)
                 = L * scale_k * N * 2
```

That equality is not optional if one allocation is reinterpreted as both. If it ceases to hold, `DeviceAllocation<half_t>::copy_from_host` can overread the packed host vector, or the kernel’s 16-byte copies can walk beyond the device allocation. Separate allocations plus the per-row selector make the requirement explicit.

The resulting `pack − base` timing is honest as an end-to-end representation comparison: both kernels compute the same values from the same A and B. It still includes the intended differences—half the global scale traffic, packed staging, decode arithmetic, explicit shared stores, different shared-storage footprint, barriers, and resulting compiler schedule. It does not isolate arithmetic alone. `packnop` remains deliberately unlike-for-like, and the new input does not cure its dead-load/code-generation confounds.

## Next `run_batch.sh` builds

Performance variants:

```bash
VARIANTS=(
  "base:SK_QUANT=2"
  "swz:SK_QUANT=2 PPU_SCALE_SWIZZLE=1"
  "bdqnop:SK_QUANT=2 PPU_B_DEQUANT_NOP=1"
  "pack:SK_QUANT=2 PPU_PACKED_SCALE=1"
  "packnop:SK_QUANT=2 PPU_PACKED_SCALE=1 PPU_PACKED_SCALE_NOP=1"
  "packsplit:SK_QUANT=2 PPU_PACKED_SCALE=1 PPU_PACKED_SPLIT_GROUPS=1"
  "splitnop:SK_QUANT=2 PPU_PACKED_SCALE=1 PPU_PACKED_SPLIT_GROUPS=1 PPU_PACKED_SCALE_NOP=1"
)
```

The useful decomposition is:

```text
packsplit - pack                       total split effect
splitnop  - packnop                    duplicate-read/setup effect without full decode
(packsplit-pack) - (splitnop-packnop)  placement/critical-path interaction
```

Correctness and diagnostic builds:

```bash
build_one gate_pack \
  "PPU_PACKED_SCALE=1" \
  test_q4k_packed_gemm || ok=0

build_one gate_split \
  "PPU_PACKED_SCALE=1 PPU_PACKED_SPLIT_GROUPS=1" \
  test_q4k_packed_gemm || ok=0

# Active swizzle on the fp16-plane rowC.
build_one gate_swz_fp16 \
  "PPU_SCALE_SWIZZLE=1" \
  test_q4k_packed_gemm || ok=0

# Active swizzle on the packed rowC.
build_one gate_swz_packed \
  "PPU_PACKED_SCALE=1 PPU_SCALE_SWIZZLE=1" \
  test_q4k_packed_gemm || ok=0

# P1 controls: both use the verifier's hardcoded Stages=3.
build_one verify_default \
  "" \
  test_moe_grouped_verify || ok=0

build_one verify_swz \
  "PPU_SCALE_SWIZZLE=1" \
  test_moe_grouped_verify || ok=0
```

Because `verify_default` has no defines, make the define-verification check conditional:

```bash
if [ -n "$defs" ] && ! grep -q "PPU_DEFS verified on $tgt" "$log"; then
  echo "    FAILED: defines did not reach the device compile"; return 1
fi
```

Run the P1 pair exactly alike:

```bash
"$OUT/test_moe_grouped_verify__verify_default" 8 1
"$OUT/test_moe_grouped_verify__verify_swz"     8 1
```

My prediction is that both assert. If they do, remove the unconditional assert before using this verifier as any swizzle gate.
