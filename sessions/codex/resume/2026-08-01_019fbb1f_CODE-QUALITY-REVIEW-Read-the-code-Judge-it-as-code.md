# Resume brief: CODE QUALITY REVIEW. Read the code. Judge it as code someone else has to maintain and extend, not for correctness or
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

Full transcript: [2026-08-01_019fbb1f_CODE-QUALITY-REVIEW-Read-the-code-Judge-it-as-code.md](../transcripts/2026-08/2026-08-01_019fbb1f_CODE-QUALITY-REVIEW-Read-the-code-Judge-it-as-code.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

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

## Follow-up requests (chronological)

2. (2026-08-01 02:34 UTC) DEBATE, ROUND 2. I verified your two structural findings against the tree and both hold, so I concede more than I defend. Where I push back I say what evidence I have. VERIFIED, AND I WITHDRAW ACCORDINGLY: * test_moe_splitk_bench.cu:87 fills hSc with 0.0625 and hZr with -0.0625. The bench never sees the real fixture, so d = dmin = 0.0625, normal. My "packnop timed the denormal path" fix rests on a false premise and I have to correct the record. That is the second time I attached the 80.5%-subnormal-d fact to the wrong effect. * tests/test_moe_grouped_verify.cu hardcodes Stages = 3, and the swizzle gate requires a power of two, so the swizzle was never active in that launch. My C1 mechanism ( …

## Last assistant conclusions

### 2026-08-01 02:35 UTC

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

There is also ordinary macro leakage in a public header: [
… [truncated 7886 chars]

### 2026-08-01 02:42 UTC

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

Pointer selection cannot safely happen only in `main()`. One generated binary contains both TK256 packed configurations and TK64/TK128 fallback configurations. Under `PPU_PACKED_SC
… [truncated 3871 chars]
