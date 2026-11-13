# Resume brief: Read the code. Two questions, and a hard constraint that changes how to weigh the answers.

REPO /root/marlin_ppu/quactlize (branches main, dev) and its third_party/actlize submodule (ppu-w4a16-dev), which
holds the collective (include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp) and the converter
(include/cutlass/fast_numeric_conversion_for_mix_gemm.h).

THE CONSTRAINT, which is new and binding: the product must support GGUF k-quants, GPTQ and AWQ. An OFFLINE REORDER of
the weights is allowed. AN INCREASE IN STORED BYTES IS NOT -- not for the weights, not for the scales, not for the
zeros. Any design that materialises a wider scale representation on device is disqualified however fast it is. Judge
everything below against that.

Q1. WHAT IN THIS CODE IS HACKY -- informal, one-off, or maintained only by the person who wrote it -- and what would
    you rewrite rather than patch? Be concrete, file:line. I am not asking for style. I am asking which constructs
    will produce a WRONG NUMBER or an unbuildable tree when someone extends them, and which are merely ugly. Rank by
    that difference. Things I already suspect, so disagree with me if you can:
      - the scale channel's positional cute::tuple with mode-dependent indices
      - two layouts named sS over one buffer
      - #if-gated members whose users sit outside the #if
      - the generated-.cu-per-configuration sweep machinery
      - build.sh's overlay-into-actlize's-example-tree model
      - the offline python in tools/ versus the device-side decode in gguf_packed_scale.h: one bit map or two?
    Say which of these are symptoms of ONE structural cause.

Q2. STRUCTURE. Compare against TensorRT-LLM's mixed-input W4A16 path -- cutlass_extensions' fpA_intB gemm, its
    interleaved weight-only preprocessing (preprocess_weights_for_mixed_gemm / the row-major-to-tile-interleave
    permutations), its per-format QuantOp taxonomy and its launcher/tile-config selection. If you cannot read it from
    here, say so and reason from what a reader of that codebase would expect instead of inventing details.
    What does TRT-LLM get structurally right that this tree does not, specifically for supporting SEVERAL quantised
    formats behind one kernel? Name the abstraction boundaries: where does format-specific knowledge live there, and
    where does it leak here?

Q3. Given the constraint, which of these can be supported with NO stored-byte increase, and what is missing for each:
      GGUF Q4_K (int4, gs=32, affine d/dmin, 12 B of 6-bit codes per superblock)
      GGUF Q3_K (int2+int1 planes, gs=16, symmetric, scale = d*(sc6-32))
      GGUF Q5_K (int4+int1), GGUF Q6_K (int4+int2, signed int8 scales), GGUF Q2_K (affine, 4+4 bit)
      GPTQ int4 (symmetric, gs=128, q_signed = q-8, g_idx possible)
      AWQ int4 (asymmetric, gs=128, zero-point as int4, its own interleave)
    For each say: does the DEVICE path already exist, does the OFFLINE reorder exist, is it validated against an
    independent golden, and what specifically is missing. Where the answer is "the scale must be decoded on device
    because storing it widened would breach the constraint", say so -- that is the interesting case and it is the one
    I have been treating as optional.

Do not restate architecture. Findings, and a judgement.

- **Thread ID:** `019fbb39-f5af-79b3-8a04-ee5fb3eabc9d`
- **Started / last event:** 2026-08-01 02:49 UTC → 2026-08-01 03:03 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T10-49-25-019fbb39-f5af-79b3-8a04-ee5fb3eabc9d.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "80dfeec20d06741227fd30a1c54ee7a167d64df6", "branch": "dev", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-01_019fbb39_Read-the-code-Two-questions-and-a-hard-constraint.md](../transcripts/2026-08/2026-08-01_019fbb39_Read-the-code-Two-questions-and-a-hard-constraint.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Read the code. Two questions, and a hard constraint that changes how to weigh the answers.

REPO /root/marlin_ppu/quactlize (branches main, dev) and its third_party/actlize submodule (ppu-w4a16-dev), which
holds the collective (include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp) and the converter
(include/cutlass/fast_numeric_conversion_for_mix_gemm.h).

THE CONSTRAINT, which is new and binding: the product must support GGUF k-quants, GPTQ and AWQ. An OFFLINE REORDER of
the weights is allowed. AN INCREASE IN STORED BYTES IS NOT -- not for the weights, not for the scales, not for the
zeros. Any design that materialises a wider scale representation on device is disqualified however fast it is. Judge
everything below against that.

Q1. WHAT IN THIS CODE IS HACKY -- informal, one-off, or maintained only by the person who wrote it -- and what would
    you rewrite rather than patch? Be concrete, file:line. I am not asking for style. I am asking which constructs
    will produce a WRONG NUMBER or an unbuildable tree when someone extends them, and which are merely ugly. Rank by
    that difference. Things I already suspect, so disagree with me if you can:
      - the scale channel's positional cute::tuple with mode-dependent indices
      - two layouts named sS over one buffer
      - #if-gated members whose users sit outside the #if
      - the generated-.cu-per-configuration sweep machinery
      - build.sh's overlay-into-actlize's-example-tree model
      - the offline python in tools/ versus the device-side decode in gguf_packed_scale.h: one bit map or two?
    Say which of these are symptoms of ONE structural cause.

Q2. STRUCTURE. Compare against TensorRT-LLM's mixed-input W4A16 path -- cutlass_extensions' fpA_intB gemm, its
    interleaved weight-only preprocessing (preprocess_weights_for_mixed_gemm / the row-major-to-tile-interleave
    permutations), its per-format QuantOp taxonomy and its launcher/tile-config selection. If you cannot read it from
    here, say so and reason from what a reader of that codebase would expect instead of inventing details.
    What does TRT-LLM get structurally right that this tree does not, specifically for supporting SEVERAL quantised
    formats behind one kernel? Name the abstraction boundaries: where does format-specific knowledge live there, and
    where does it leak here?

Q3. Given the constraint, which of these can be supported with NO stored-byte increase, and what is missing for each:
      GGUF Q4_K (int4, gs=32, affine d/dmin, 12 B of 6-bit codes per superblock)
      GGUF Q3_K (int2+int1 planes, gs=16, symmetric, scale = d*(sc6-32))
      GGUF Q5_K (int4+int1), GGUF Q6_K (int4+int2, signed int8 scales), GGUF Q2_K (affine, 4+4 bit)
      GPTQ int4 (symmetric, gs=128, q_signed = q-8, g_idx possible)
      AWQ int4 (asymmetric, gs=128, zero-point as int4, its own interleave)
    For each say: does the DEVICE path already exist, does the OFFLINE reorder exist, is it validated against an
    independent golden, and what specifically is missing. Where the answer is "the scale must be decoded on device
    because storing it widened would breach the constraint", say so -- that is the interesting case and it is the one
    I have been treating as optional.

Do not restate architecture. Findings, and a judgement.

## Last assistant conclusions

### 2026-08-01 03:03 UTC

The judgement: this is a capable derivation/benchmark tree, but not yet a safe multi-format product path. Under the new constraint, the only currently qualifying format is restricted GPTQ symmetric without `g_idx`. The Q4_K packed implementation is not qualifying: it preserves global-memory bytes, then expands them into fp16 scale/zero shared-memory tiles.

Both `main` and `dev` pin Actlize at `323b9dd6`; the kernel findings apply to both. `dev` mainly adds derivation/sweep artifacts and benchmark changes.

## Q1 — what is actually dangerous

### Rank 0: wrong, disqualified, or liable to silently compute nothing

1. **The packed-scale path has no format identity.**

   [`kPackedScaleOn`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:224) is selected by a global macro plus `Scale_TileK == 8`. It does not say “Q4_K”. Later, [`ptr_S` is reinterpreted as bytes and given a hard-coded 16-byte Q4_K shape](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:724).

   That is a latent wrong-number bug as soon as another gs/tile combination also has eight scale groups. Q2_K at gs=16/TK=128 is an obvious collision. This must be rewritten around a typed metadata format, not extended with more macros.

2. **The Q4_K device path violates the new constraint.**

   The code explicitly says it decodes native bytes into “the SAME fp16 smem planes” at [lines 1357–1367](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1357), constructs fp16 `sS`/`sZ` arrays at [1389–1391](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1389), and fills them at [1500–1504](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1500).

   That is a materialised wider scale representation on device. The generic `Superblock` decoder would do the same in an object containing `GroupScale g[kGroups]` at [gguf_scale_decode.hpp:83](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_decode.hpp:83). Both are disqualified. Decode must feed the scale/zero values directly to the MMA fragment that consumes them, without an expanded array or tile.

3. **There is a live unconditional assertion in the coarse scale path.**

   After the valid scale/zero copy, [`if constexpr(false) ... assert(false)`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1691) always executes. Actlize defaults to Release, so `NDEBUG` hides it. A Debug build aborts whenever coarse scale reload occurs. It is not merely ugly; it makes a normal configuration dependent on build type.

4. **Physical weight layout is inferred again at launch instead of carried with the preprocessed buffer.**

   [`il = n % 256 == 0 && k % 256 == 0`](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:352) decides how the kernel reads B. The buffer has no layout tag. The Q4 harness itself documents that handing an interleaved buffer to the non-interleaved branch produces deterministic garbage at [test_q4k_packed_gemm.cu:50](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:50).

   This also becomes unsafe with K slicing: `filter_and_run` chooses from sliced `k`, while downstream stride construction can use `k_full`. The offline plan, buffer, and launcher need one shared layout ID.

5. **The dense wrapper silently no-ops.**

   [`can_implement`, workspace, and initialization failures simply return](/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh:128). The caller can then consume unchanged/stale output. TRT-LLM throws on these failures. Silent refusal is a product correctness defect.

### Rank 1: extension traps that have already produced OOBs or unbuildable variants

6. **The positional `cute::tuple` scale channel should be replaced, not patched.**

   The mode is inferred from tuple positions at [lines 127–149](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:127). Different stages return different positional contracts at [736–743](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:736) and [1242–1256](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1242).

   The strongest indictment is the dead `sSp` object: it cannot be deleted because doing so would move tuple indices, so it was repointed while deliberately kept dead at [1572–1601](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1572). That is an interface which no compiler can validate semantically.

7. **Two layouts over the same scale buffer are a correctness hazard, not naming ugliness.**

   The write view is `(n, group, stage)`; the read view flattens to `(n, 1, stage*Scale_TileK+group)` at [1561–1568](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1561). The code records that using the wrong one already produced “TSM out of range” at [1500–1502](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1500).

   Two views are legitimate; two separately reconstructed layout types with an informal equivalence are not. There should be one scale-storage accessor that produces both views and statically verifies address equality.

8. **I partly disagree about the current `#if` member/use defect.**

   The specific `ScaleSwizzle` definition used outside its branch has been repaired: the declarations are now outside the branch at [489–498](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:489). So that particular suspicion is historical, not live at this pin.

   The systemic problem remains: macro combinations are not instantiated by the normal build. [`PPU_FORCE_INSTANTIATE`](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:148) exists precisely because ordinary parsing misses dependent template failures, while `main` silently lacks the `dev/fold_derivation` checks at [build.sh:70](/root/marlin_ppu/quactlize/build.sh:70). New macro combinations remain an unbuildable-tree risk.

9. **The build overlay should be rewritten.**

   [`build.sh`](/root/marlin_ppu/quactlize/build.sh:9) copies and flattens sources into the submodule, edits its `examples/CMakeLists.txt`, restores it with `git checkout`, deletes the overlay at [41–47](/root/marlin_ppu/quactlize/build.sh:41), and deletes one shared build directory on every run at [191–193](/root/marlin_ppu/quactlize/build.sh:191). Concurrent builds race; an edit to the submodule example list is overwritten; new extensions can disappear from the whitelist.

   The root [CMakeLists.txt](/root/marlin_ppu/quactlize/CMakeLists.txt:1) does not build any device code, so a clean root configure proves almost nothing. This needs an out-of-tree Actlize target or supported external-example hook.

### Rank 2: ugly or experimental, but not itself a reason for wrong numbers

- **Generated `.cu` per configuration:** the concept is defensible. Device compilers often need TU sharding. What should change is the string-table/config generation and the checked-in `dev/fold_derivation/.moe_units_check` forest. Generate from one typed manifest into the build directory. Do not rewrite the sharding merely because it is generated.
- **Ablation macros and forensic comments:** noisy and single-maintainer in flavour, but harmless if excluded from product builds. Flags such as `PPU_B_DEQUANT_NOP` can deliberately produce nonsense and therefore must never share rele
… [truncated 9809 chars]
