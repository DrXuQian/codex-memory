# Resume brief: READ THE CODE FIRST -- you have full filesystem read access, use it. A previous attempt at this review could not
open any file and answered from a prose description; do not repeat that.

A bisect has just narrowed a numeric MISMATCH to twenty lines. Find the bug.

SYMPTOM. Target test_q4k_packed_gemm has three rows. rowA and rowB (TileK=128) MATCH. rowC (TileShape 16x128x256,
so Scale_TileK == 8 and the "packed" scale path is ENABLED) MISMATCHes: bad=724/4096, max_rel=3.5e+05, and an
earlier run of a slightly different variant gave bad=128/4096 -- i.e. PARTIAL and possibly not deterministic, not
"everything is wrong".

BISECT RESULT, just measured on the real hardware: building with -DPPU_PACKED_PAIR=0 makes rowC MATCH again.
That macro selects, in packed_decode_stage, cutlass::gguf_packed::group_of_words (scalar, long-standing, known
good) instead of cutlass::gguf_packed::group_pair_of_words (new, packs both 6-bit fields of a group into the two
halves of one 32-bit register). Everything else -- the native 16-byte gmem->smem transport, the shared-memory
stores, the loop structure -- is identical in both builds. So the defect is inside group_pair_of_words or in what
it depends on.

WHAT IS ALREADY KNOWN AND SHOULD NOT BE RE-DERIVED. A host-side gate,
general/w4a16_gemm/cutlass_w4a16/fold_derivation/l96_packed_pair.cu, compares group_pair_of_words against
group_of_words over 32768 REAL Q4_K groups and reports 0 bad, bit-for-bit. But it runs under nvcc, where the guard
CUTLASS_GGUF_PACKED_F16X2_ASM (defined as __HGGCCC__ && !__NVCC__) selects the SCALAR FALLBACK. So the host gate
proves the arithmetic and proves nothing about the two inline-asm instructions the device build actually uses:
    ppu.sub.f16x2      %0, %1, %2
    ppu.fma.rtte.f16x2 %0, %1, %2, %3
Reference uses of both mnemonics exist in include/cutlass/fast_numeric_conversion_for_mix_gemm.h.

YOUR TASK.
1. Read third_party/actlize/include/cutlass/gguf_packed_scale.h -- functions sub_f16x2, fma_f16x2, pack_h2,
   lo_h2, hi_h2, mul2_of_words, code_pair_from_words, group_pair_of_words, and the constants kMagic1152x2 and
   kNegZeroX2.
2. Read third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp,
   packed_decode_stage and its two call sites in mma().
3. Find the defect. Rank hypotheses by whether they predict a PARTIAL failure (roughly 18% of outputs) rather
   than a total one -- that asymmetry is the strongest clue and any hypothesis that predicts "everything wrong"
   must explain why most outputs survive.
   Consider at least: inline-asm constraints and clobbers ("=r" outputs versus inputs, missing earlyclobber,
   volatile, whether the compiler may reorder or CSE these across the loop); whether an output register may alias
   an input; operand ORDER against the reference uses; signed zero, denormal flushing and the claim
   fma(x, m, -0) == x*m; whether the +0x64806480 fold can carry between the two 16-bit lanes for any reachable
   input; the straddle condition `off > 26` in code_pair_from_words for EVERY (G, which) bit position that
   bit_of() produces for Q4_K; whether any index into the u[] register array is runtime rather than
   compile-time; and whether kPackedPairFast/kPackedZMul/kPackedScaleBias are what the call site thinks.
4. For the top hypothesis, give the exact input that triggers it, and the smallest device-side probe that would
   confirm it. Say plainly if you cannot tell.

Report file:line and a concrete failure scenario. Do not summarise the code back to me.

- **Thread ID:** `019fb86e-5d0f-7051-96df-16e3ef0970e1`
- **Started / last event:** 2026-07-31 13:47 UTC → 2026-07-31 13:59 UTC
- **Working dir:** `/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/07/31/rollout-2026-07-31T21-47-48-019fb86e-5d0f-7051-96df-16e3ef0970e1.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "1d3d3dd5640856e1832e27ea784fad3fc11a481d", "branch": "ppu_dev", "repository_url": "git@github.com:DrXuQian/Kernels.git"}`

Full transcript: [2026-07-31_019fb86e_READ-THE-CODE-FIRST-you-have-full-filesystem-read.md](../transcripts/2026-07/2026-07-31_019fb86e_READ-THE-CODE-FIRST-you-have-full-filesystem-read.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

READ THE CODE FIRST -- you have full filesystem read access, use it. A previous attempt at this review could not
open any file and answered from a prose description; do not repeat that.

A bisect has just narrowed a numeric MISMATCH to twenty lines. Find the bug.

SYMPTOM. Target test_q4k_packed_gemm has three rows. rowA and rowB (TileK=128) MATCH. rowC (TileShape 16x128x256,
so Scale_TileK == 8 and the "packed" scale path is ENABLED) MISMATCHes: bad=724/4096, max_rel=3.5e+05, and an
earlier run of a slightly different variant gave bad=128/4096 -- i.e. PARTIAL and possibly not deterministic, not
"everything is wrong".

BISECT RESULT, just measured on the real hardware: building with -DPPU_PACKED_PAIR=0 makes rowC MATCH again.
That macro selects, in packed_decode_stage, cutlass::gguf_packed::group_of_words (scalar, long-standing, known
good) instead of cutlass::gguf_packed::group_pair_of_words (new, packs both 6-bit fields of a group into the two
halves of one 32-bit register). Everything else -- the native 16-byte gmem->smem transport, the shared-memory
stores, the loop structure -- is identical in both builds. So the defect is inside group_pair_of_words or in what
it depends on.

WHAT IS ALREADY KNOWN AND SHOULD NOT BE RE-DERIVED. A host-side gate,
general/w4a16_gemm/cutlass_w4a16/fold_derivation/l96_packed_pair.cu, compares group_pair_of_words against
group_of_words over 32768 REAL Q4_K groups and reports 0 bad, bit-for-bit. But it runs under nvcc, where the guard
CUTLASS_GGUF_PACKED_F16X2_ASM (defined as __HGGCCC__ && !__NVCC__) selects the SCALAR FALLBACK. So the host gate
proves the arithmetic and proves nothing about the two inline-asm instructions the device build actually uses:
    ppu.sub.f16x2      %0, %1, %2
    ppu.fma.rtte.f16x2 %0, %1, %2, %3
Reference uses of both mnemonics exist in include/cutlass/fast_numeric_conversion_for_mix_gemm.h.

YOUR TASK.
1. Read third_party/actlize/include/cutlass/gguf_packed_scale.h -- functions sub_f16x2, fma_f16x2, pack_h2,
   lo_h2, hi_h2, mul2_of_words, code_pair_from_words, group_pair_of_words, and the constants kMagic1152x2 and
   kNegZeroX2.
2. Read third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp,
   packed_decode_stage and its two call sites in mma().
3. Find the defect. Rank hypotheses by whether they predict a PARTIAL failure (roughly 18% of outputs) rather
   than a total one -- that asymmetry is the strongest clue and any hypothesis that predicts "everything wrong"
   must explain why most outputs survive.
   Consider at least: inline-asm constraints and clobbers ("=r" outputs versus inputs, missing earlyclobber,
   volatile, whether the compiler may reorder or CSE these across the loop); whether an output register may alias
   an input; operand ORDER against the reference uses; signed zero, denormal flushing and the claim
   fma(x, m, -0) == x*m; whether the +0x64806480 fold can carry between the two 16-bit lanes for any reachable
   input; the straddle condition `off > 26` in code_pair_from_words for EVERY (G, which) bit position that
   bit_of() produces for Q4_K; whether any index into the u[] register array is runtime rather than
   compile-time; and whether kPackedPairFast/kPackedZMul/kPackedScaleBias are what the call site thinks.
4. For the top hypothesis, give the exact input that triggers it, and the smallest device-side probe that would
   confirm it. Say plainly if you cannot tell.

Report file:line and a concrete failure scenario. Do not summarise the code back to me.

## Last assistant conclusions

### 2026-07-31 13:59 UTC

The only defect consistent with a partial, build-sensitive failure is the original inline-asm constraint: both wrappers used `=r`, allowing the destination to alias any input.

On the bisected revision these were `gguf_packed_scale.h:170` and `:180`; the current tree already shows the proposed `=&r` correction at [gguf_packed_scale.h:197](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gguf_packed_scale.h:197) and [gguf_packed_scale.h:207](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gguf_packed_scale.h:207).

Why it fits: `m2` is reused across eight unrolled groups at [ppu_mma_aiu_multistage_mixed_input.hpp:1300](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1300). It remains live through G0–G6 but dies at G7. Consequently the allocator can select a different overlap for the final FMA—for example destination == `m2`. A bad overlap therefore corrupts only selected groups/register-allocation patterns, naturally producing partial and variant-dependent GEMM failures. `volatile` prevents removal/CSE but does not prevent operand aliasing; no memory clobber is needed.

This is not proven solely from source: if PPU guarantees every destination/source overlap is legal, `=r` was valid. The reference uses attest the operand order and probably destination == source 1, but do not specifically attest destination == source 2 or 3. I cannot tell whether those overlaps are legal without a device probe or emitted assembly.

A concrete real input is fixture unit `(e=0,b=0,n=0)`, G7:

```text
u    = {09640172, fecf4ffa, 4d6dd62f, db5d68cb}
sc=50, mn=54
sub inputs: 64b664b2, 64806480       expected 00360032
fma inputs: 00360032, 89640172, 80008000
expected fma: a08c1484
```

The smallest confirmation is one thread forcing destination == FMA source 2:

```cpp
__global__ void probe(uint32_t* out) {
  uint32_t x = 0x00360032u, m = 0x89640172u, z = 0x80008000u;

  uint32_t separate;
  asm volatile("ppu.fma.rtte.f16x2 %0,%1,%2,%3;"
               : "=&r"(separate) : "r"(x), "r"(m), "r"(z));

  uint32_t alias_m = m;
  asm volatile("ppu.fma.rtte.f16x2 %0,%1,%0,%2;"
               : "+r"(alias_m) : "r"(x), "r"(z));

  out[0] = separate;
  out[1] = alias_m;  // both must be 0xa08c1484
}
```

Ranking the alternatives:

1. Destination/input aliasing: best fit for partial and possibly unstable failure.
2. Device-compiler mislowering of the two straddles: would affect only G1-min and G6-scale and hence could be partial, but the source condition is correct. Starts are `(32,56),(38,62),(44,68),(50,74),(80,104),(86,110),(92,116),(98,122)`; only offsets 30 and 28 straddle, while offset 26 ends exactly at bit 31.
3. FTZ: there is genuine exposure—3914/4864 fixture `d` values are subnormal—but it is a poor symptom match. Simulating loss of those subnormal inputs against this exact fixture produces roughly 3997/4096 bad outputs, not 724. If only subnormal results flush, none of the `d*sc` products are subnormal. Do not identify `.noftz` as root without the device probe.
4. Operand order, lane order, signed zero, carry, constants, or call-site arguments: effectively excluded. The order matches [fast_numeric_conversion_for_mix_gemm.h:303](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:303); `0x6480+63=0x64bf` cannot carry between lanes; all decode indices are compile-time; and the call uses `PairFast=true`, `ZMul=8`, `ScaleBias=0`, `HasMin=true` correctly at [ppu_mma_aiu_multistage_mixed_input.hpp:1207](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1207).
