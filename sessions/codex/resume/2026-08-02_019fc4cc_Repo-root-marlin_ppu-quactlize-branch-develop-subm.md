# Resume brief: Repo /root/marlin_ppu/quactlize branch develop (submodule third_party/actlize branch ppu-w4a16-dev at 840e9fc9). Verify tonight's work adversarially. Cite file:line. Do not accept my framing; I have been wrong repeatedly in this session and want the wrong parts found rather than confirmed.

WHAT WAS BUILT, in four pieces:

1. THE ONLINE SCALE PRE-PASS. quactlize/include/gguf_scale_prepass.hpp -- native k-quant scale metadata to fp16
   (scale, zero) planes in a workspace, weights untouched. Torch ops gguf_scale_prepass / gguf_scale_block_shape.
   ZMul (the CONSUMER converter's centre correction, 8 for int4) is a template parameter beside the format, no
   default.

2. PURE CUDA-CORE DECODE. quactlize/include/gguf_vecdot.hpp -- one traversal visit<T> shared by three consumers:
   vecdot_block (MMVQ shape), dequantize_block_to (fp16 weights, destination is any callable so a cute Layout goes
   straight in), unpack_block (codes/scale/zero for the offline packers). __global__ kernels exist and were RUN on a
   local 5090. dp4a is ruled out by decision.

3. THE PPU SEAM. quactlize/csrc/preprocess/thop/ppu_backend.{h,cpp} -- the extension is host gcc and dlopens an
   hgcc-built libquactlize_ppu.so; ops forward when it loads. Backend is queryable; a stub library with sentinel
   entry points is driven in a test.

4. THE PACKED PATH GENERALISED. cutlass/gguf_packed_scale.h gained Fmt/UnitTraits/Unit<F> with a static_assert that
   the general bit rule reproduces the shipped Q4_K positions; the collective derives kPackedScaleUnit,
   kPackedScaleOn, kPackedScaleBias, kPackedHasMin, kPackedUnitWords, the cp.async width and kPackedPairFast from it.
   All five formats now pass the nvcc front-end gate.

THE ORACLE: the official gguf python package. Since gguf.quants exposes only dequantize() and no scale accessor, the
scale is INVERTED out of the reference -- dmin=0 kills the affine term, code fills of 0x00 and 0xFF (the only bytes
uniform in every bit) give two points, scale = (w_hi - w_lo)/qmax, and c_lo = w_lo/our_scale is asserted integral so
the code offset is DISCOVERED. Derived: Q2 [0,3], Q3 [-4,3], Q4 [0,15], Q5 [0,31], Q6 [-32,31].

ATTACK THESE SPECIFICALLY:

a. The packed unit generalisation. Unit<F>::bit_of lays fields group-major within a run of kRunGroups = kGroups/2 for
   min formats and kGroups otherwise. Is that self-contained claim actually true for Q2_K (16 groups, 4+4 bits) and
   Q6_K (16 groups, 8+0)? A "run" is supposed to be readable by a k-tile covering PART of a superblock -- check
   whether the run size matches what Scale_TileK can actually be for each format, or whether I have made runs that no
   tiling ever asks for.

b. kPackedColsPerThread = 2 for the 2-mod-4 units (Q3_K 14 B, Q6_K 18 B). I claim a thread copying a PAIR and
   decoding that same pair preserves the ownership invariant. Verify against the actual thread layout that
   GmemTiledCopyScalePacked now builds (Scale_TileN/cpt threads, kPackedCopySpan values) and the rewritten decode
   loop in packed_decode_stage. Does the copy really give thread t columns [t*cpt, t*cpt+cpt)? And does
   PPU_PACKED_SPLIT_GROUPS still work, since its wrap modulus assumed one column per thread?

c. kPackedUnitWords rounds UP now and the register load assembles a partial last word byte-by-byte when the unit is
   not a multiple of 4. Is the staging tile actually padded to whole words, as my comment claims? If not, the
   byte-wise loop is fine but the comment is wrong, and worse, some other reader may still do a 4-byte read.

d. code_from_words gained a Bits parameter defaulting to 6 and the straddle test became off > 32 - Bits. Check that
   for Bits=8 byte-aligned fields and Bits=4 the condition and the second-word read are right, and that no call site
   still passes a 6-bit assumption for a format whose fields are not 6 bits.

e. THE ORACLE'S SOUNDNESS. Is the two-fill extraction valid for every format, and is the integer-code assertion
   actually discriminating? I already accept it is offset DISCOVERY rather than proof of scale, with the relative
   comparison being the real check.

f. WHAT IS OVERCLAIMED. schemes.py was rewritten tonight; check each changed entry against what the code can
   actually do. In particular I say the k-quant GEMV is "wiring rather than a kernel" because the offline chain
   reaches gemv_lowbit and the row permutation was measured to stay inside its own 32-block -- is that enough to
   claim it, or is there something in gemv_lowbit that a k-quant still cannot satisfy?

g. Anything in the four-route agreement test (test_all_routes_agree_with_llama_cpp) that makes it weaker than it
   looks -- in particular whether route 2 reconstructing weights from codes*scale+zero in numpy is really testing
   the pre-pass or is testing numpy.

- **Thread ID:** `019fc4cc-5f27-7073-b01e-e2189b1d2a97`
- **Started / last event:** 2026-08-02 23:25 UTC → 2026-08-02 23:45 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T07-25-55-019fc4cc-5f27-7073-b01e-e2189b1d2a97.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "0e9bb52f4053e959e250c83bf66e15e3cc99d0c5", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-02_019fc4cc_Repo-root-marlin_ppu-quactlize-branch-develop-subm.md](../transcripts/2026-08/2026-08-02_019fc4cc_Repo-root-marlin_ppu-quactlize-branch-develop-subm.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize branch develop (submodule third_party/actlize branch ppu-w4a16-dev at 840e9fc9). Verify tonight's work adversarially. Cite file:line. Do not accept my framing; I have been wrong repeatedly in this session and want the wrong parts found rather than confirmed.

WHAT WAS BUILT, in four pieces:

1. THE ONLINE SCALE PRE-PASS. quactlize/include/gguf_scale_prepass.hpp -- native k-quant scale metadata to fp16
   (scale, zero) planes in a workspace, weights untouched. Torch ops gguf_scale_prepass / gguf_scale_block_shape.
   ZMul (the CONSUMER converter's centre correction, 8 for int4) is a template parameter beside the format, no
   default.

2. PURE CUDA-CORE DECODE. quactlize/include/gguf_vecdot.hpp -- one traversal visit<T> shared by three consumers:
   vecdot_block (MMVQ shape), dequantize_block_to (fp16 weights, destination is any callable so a cute Layout goes
   straight in), unpack_block (codes/scale/zero for the offline packers). __global__ kernels exist and were RUN on a
   local 5090. dp4a is ruled out by decision.

3. THE PPU SEAM. quactlize/csrc/preprocess/thop/ppu_backend.{h,cpp} -- the extension is host gcc and dlopens an
   hgcc-built libquactlize_ppu.so; ops forward when it loads. Backend is queryable; a stub library with sentinel
   entry points is driven in a test.

4. THE PACKED PATH GENERALISED. cutlass/gguf_packed_scale.h gained Fmt/UnitTraits/Unit<F> with a static_assert that
   the general bit rule reproduces the shipped Q4_K positions; the collective derives kPackedScaleUnit,
   kPackedScaleOn, kPackedScaleBias, kPackedHasMin, kPackedUnitWords, the cp.async width and kPackedPairFast from it.
   All five formats now pass the nvcc front-end gate.

THE ORACLE: the official gguf python package. Since gguf.quants exposes only dequantize() and no scale accessor, the
scale is INVERTED out of the reference -- dmin=0 kills the affine term, code fills of 0x00 and 0xFF (the only bytes
uniform in every bit) give two points, scale = (w_hi - w_lo)/qmax, and c_lo = w_lo/our_scale is asserted integral so
the code offset is DISCOVERED. Derived: Q2 [0,3], Q3 [-4,3], Q4 [0,15], Q5 [0,31], Q6 [-32,31].

ATTACK THESE SPECIFICALLY:

a. The packed unit generalisation. Unit<F>::bit_of lays fields group-major within a run of kRunGroups = kGroups/2 for
   min formats and kGroups otherwise. Is that self-contained claim actually true for Q2_K (16 groups, 4+4 bits) and
   Q6_K (16 groups, 8+0)? A "run" is supposed to be readable by a k-tile covering PART of a superblock -- check
   whether the run size matches what Scale_TileK can actually be for each format, or whether I have made runs that no
   tiling ever asks for.

b. kPackedColsPerThread = 2 for the 2-mod-4 units (Q3_K 14 B, Q6_K 18 B). I claim a thread copying a PAIR and
   decoding that same pair preserves the ownership invariant. Verify against the actual thread layout that
   GmemTiledCopyScalePacked now builds (Scale_TileN/cpt threads, kPackedCopySpan values) and the rewritten decode
   loop in packed_decode_stage. Does the copy really give thread t columns [t*cpt, t*cpt+cpt)? And does
   PPU_PACKED_SPLIT_GROUPS still work, since its wrap modulus assumed one column per thread?

c. kPackedUnitWords rounds UP now and the register load assembles a partial last word byte-by-byte when the unit is
   not a multiple of 4. Is the staging tile actually padded to whole words, as my comment claims? If not, the
   byte-wise loop is fine but the comment is wrong, and worse, some other reader may still do a 4-byte read.

d. code_from_words gained a Bits parameter defaulting to 6 and the straddle test became off > 32 - Bits. Check that
   for Bits=8 byte-aligned fields and Bits=4 the condition and the second-word read are right, and that no call site
   still passes a 6-bit assumption for a format whose fields are not 6 bits.

e. THE ORACLE'S SOUNDNESS. Is the two-fill extraction valid for every format, and is the integer-code assertion
   actually discriminating? I already accept it is offset DISCOVERY rather than proof of scale, with the relative
   comparison being the real check.

f. WHAT IS OVERCLAIMED. schemes.py was rewritten tonight; check each changed entry against what the code can
   actually do. In particular I say the k-quant GEMV is "wiring rather than a kernel" because the offline chain
   reaches gemv_lowbit and the row permutation was measured to stay inside its own 32-block -- is that enough to
   claim it, or is there something in gemv_lowbit that a k-quant still cannot satisfy?

g. Anything in the four-route agreement test (test_all_routes_agree_with_llama_cpp) that makes it weaker than it
   looks -- in particular whether route 2 reconstructing weights from codes*scale+zero in numpy is really testing
   the pre-pass or is testing numpy.

## Last assistant conclusions

### 2026-08-02 23:45 UTC

Verdict: I would not accept tonight’s work as verified. The scale arithmetic/oracle is mostly sound, but the packed pair path has a real ownership error, Q2 has the wrong consumer correction, and the PPU seam does not honor its declared contract.

## Findings

1. **Critical — the paired CuTe copy does not give thread `t` columns `[2t, 2t+1]`.**

   The copy uses thread layout `(Scale_TileN/2, 1)` and value layout `(1, 2*unit)` ([collective:302](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:302)). CuTe constructs the logical tiler as `product_each(shape(raked_product(...)))` ([copy_atom.hpp:481](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/atom/copy_atom.hpp:481)), so that is a `(TN/2, 2*unit)` tile, not `(TN, unit)`.

   The source and destination tensors remain logically `(TN, unit)` ([collective:912](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:912), [collective:1384](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1384)). Nothing gives the first mode a stride of two or recasts it as paired columns. Thread `t` therefore starts at logical column `t`, while the decode assumes `base = t*2` ([collective:1636](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1636)). The claimed per-thread wait/ownership guarantee does not hold.

   The gate does not expose this: it compiles the Q4 fixture ([local_gates.py:69](/root/marlin_ppu/quactlize/ci/local_gates.py:69)), whose row C has `Scale_TileK==8` ([test_q4k_packed_gemm.cu:208](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:208)). For Q2/Q3/Q6, `PackedUnit::kGroups==16`, so `kPackedScaleOn` is false in that configuration ([collective:245](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:245)). Their decoder and partial-word path are not actually instantiated as active code.

2. **Critical — Q2_K would receive an erroneous `+8*scale`.**

   The collective still hardcodes `kPackedZMul = 8` for every selected format ([collective:1510](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1510)). But the actual uint2 converter emits unsigned `0..3` and explicitly has no bias ([fast_numeric_conversion_for_mix_gemm.h:628](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:628)). Q2 therefore needs `ZMul=0`, not 8.

   If a real Q2 configuration turns `kPackedScaleOn` on, its weights will be shifted by `8*scale`. The current front-end gate hides this by retaining the int4/Q4 fixture and an inactive 16-group branch.

3. **High — the PPU seam’s vecdot ABI disagrees with the Torch op, and dequantize never forwards.**

   The declared ABI has one activation vector shared across output rows: `x[blocks_per_row*256]` ([ppu_backend.h:26](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.h:26)). The reference device kernel implements exactly that ([gguf_vecdot.hpp:331](/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp:331)).

   The Torch op instead requires `x[rows,256]`, uses `x[r]` in the CPU arm, but forwards with `blocks_per_row=1` ([gguf_prepass_ops.cpp:167](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp:167), [gguf_prepass_ops.cpp:183](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp:183)). A backend implementing the declared ABI will use the first activation slice for every output row.

   Separately, `Api::dequantize` is required to load, but `gguf_dequantize` contains no backend call at all ([gguf_prepass_ops.cpp:224](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp:224)). The stub exports dequantize but the test asserts sentinels only for vecdot and prepass ([test_gguf_golden.py:450](/root/marlin_ppu/quactlize/tests/test_gguf_golden.py:450), [test_gguf_golden.py:490](/root/marlin_ppu/quactlize/tests/test_gguf_golden.py:490)).

   Also, `zmul` validation occurs after the PPU branch, so the PPU backend accepts values the CPU backend rejects ([gguf_prepass_ops.cpp:126](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp:126)).

4. **High — the multi-block dequantization kernel does not compose general layouts correctly.**

   `dequantize_block_to` genuinely accepts any callable. But `dequantize_kernel` maps block `b` as:

   `b*256 + dst(i)`

   via `DstLayoutShifted` ([gguf_vecdot.hpp:243](/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp:243), [gguf_vecdot.hpp:345](/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp:345)). For a column-major map the required address is `dst(b*256+i)`, e.g. `n + (b*256+i)*ld`, not `b*256+n+i*ld`. Hierarchical CuTe layouts have the same problem.

   Thus “a CuTe Layout goes straight in” is true only for the single-block helper or a specially block-local repeating layout, not for the advertised whole-tensor kernel.

5. **Medium — `schemes.py` contains multiple false or stale claims.**

   - Q2’s blocker says the collective still hardcodes unit size, copy width, `Scale_TileK`, and word count ([schemes.py:99](/root/marlin_ppu/quactlize/quactlize/schemes.py:99)); those facts are no longer true.
   - The all-k-quant GEMV note claims `gguf_unpack -> pack_int4 -> preprocess...` reaches the launcher ([schemes.py:145](/root/marlin_ppu/quactlize/quactlize/schemes.py:145)). The only tested chain is explicitly Q4_K and `pack_int4` ([test_gguf_golden.py:400](/root/marlin_ppu/quactlize/tests/test_gguf_golden.py:400)). Q2 needs int2 packing; Q3/Q5/Q6 need plane splitting and signed-offset folding.
   - Calling FULLY_QUANTIZED GEMV “wire gemv_lowbit” is a category error ([schemes.py:165](/root/marlin_ppu/quactlize/quactlize/schemes.py:165)). `gemv_lowbit` unconditionally interprets scales and zeros as fp16 and vector-loads those planes ([gemv_kernel.hpp:97](/root/marlin_ppu/quactlize/quactlize/include/gemv_lowbit/gemv_kernel.hpp:97), [gemv_kernel.hpp:153](/root/marlin_ppu/quactlize/quactlize/include/gemv_lowbit/gemv_kernel.hpp:153)). Wiring it produces SCALE_FIRST, not native-scale FULLY_QUANTIZED execution.
   - The validation cross-check calls format-only `registry.coverage()` ([schemes.py:203](/root/marlin_ppu/quactlize/quactlize/schemes.py:203)), despite the registry explicitly providing path-sensitive `coverage_by_path()` because format-only evidence is insufficient ([registry.py:28](/root/marlin_ppu/quactlize/ci/registry.py:28), [registry.py:100](/root/marlin_ppu/quactlize/ci/registry.py:100)).

6. **Medium — “four-route agreement” is materially weaker than its name.**

   Route 2 does exercise the pre-pass outputs; it is not merely testing NumPy. But it reconstructs with raw codes and `ZMul=0`, so it does not exercise the mixed-input collective, converter correction, reordered code layout, or device placement ([test_gguf_golden.py:579](/root/marlin_ppu/quactlize/tests/test_gguf_golden.py:579)).

   Route 3 never produces a dot product and is absent from the final comparison loop. It only checks that the host packer and host unit decoder return the same planes ([test_gguf_golden.py:595](/root/marlin_ppu/quactlize/tests/test_gguf_golden.py:595), [test_gguf_golden.py:605](/root/marlin_ppu/quactlize/tests/test_gguf_golden.py:605)). Those host helpers duplicate the unit formula in [gguf_packed_unit.hpp:57](/root/marlin_ppu/quactlize/quactlize/include/gguf_packed_unit.hpp:57); the device collective reads the separate submodule definition. Therefore this is not a test of the packed collective.

## Direct answers to a–e

- **a. Runs:** Q2’s two eight-group runs are byte-self-contained; Q6’s single sixteen-group run is also self-contained. The comme
… [truncated 2969 chars]
