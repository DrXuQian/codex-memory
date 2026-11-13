# Resume brief: Repo: /root/marlin_ppu/quactlize, branch dev. Review the last two commits (3e9f0b4 and 00523c6) with `git show`.

Context: I built the HOST half of the preprocessing as an operator-only torch .so, before any device work, against
your earlier advice that put "establish the target PPU torch's ABI/stream/runtime identity" first and the
TORCH_LIBRARY .so at step 4 of the landing order.

ARGUE, do not summarise. Take a position on each and say where I am wrong:

1. I inverted your landing order: host half first, no PPU access at all. My justification is the payoff -- ASAN over
   the host chain (ci/asan_preprocess_probe.cpp) found two out-of-bounds, one in the vendor's own
   permute_B_rows_for_mixed_gemm, and neither failed where it happened. Was inverting right, or did I get lucky and
   skip a step that costs more later?

2. quactlize/formats.py makes the format readiness table executable: capability sets modelled on vLLM's GGUF plugin,
   storage growth computed from block struct fields. Is putting dispatch policy (DENSE_CROSSOVER_ROWS, GEMV_MAX_ROWS)
   in the same file as format metadata a mistake? Where does this break when the device half lands and tactic
   selection becomes real?

3. I changed ColumnsInterleaved in my mixed_gemm_B_layout.h shim from a hardcoded 256 to
   ElementsPerCacheLine/ThreadblockK. That shim declares the PHYSICAL LAYOUT the kernels assume. Is deriving it from
   a 128-byte cache line the right model for the PPU's AIU, or have I copied NVIDIA's answer into a tree whose
   accelerator differs? What evidence would settle it?

4. tests/test_preprocess_ops.py claims its oracles do not call the code under test. Find any place where that claim
   is false, or where an "independent" oracle is a re-derivation sharing a misconception.

Be specific, cite files/lines. If a change I made is wrong, say so plainly.

- **Thread ID:** `019fbb9e-548e-7271-9fea-634f2ad31f57`
- **Started / last event:** 2026-08-01 04:39 UTC → 2026-08-01 04:48 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T12-39-03-019fbb9e-548e-7271-9fea-634f2ad31f57.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "00523c66d535d62fee651bd3d48aae214c4cc661", "branch": "dev", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-01_019fbb9e_Repo-root-marlin_ppu-quactlize-branch-dev-Review-t.md](../transcripts/2026-08/2026-08-01_019fbb9e_Repo-root-marlin_ppu-quactlize-branch-dev-Review-t.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo: /root/marlin_ppu/quactlize, branch dev. Review the last two commits (3e9f0b4 and 00523c6) with `git show`.

Context: I built the HOST half of the preprocessing as an operator-only torch .so, before any device work, against
your earlier advice that put "establish the target PPU torch's ABI/stream/runtime identity" first and the
TORCH_LIBRARY .so at step 4 of the landing order.

ARGUE, do not summarise. Take a position on each and say where I am wrong:

1. I inverted your landing order: host half first, no PPU access at all. My justification is the payoff -- ASAN over
   the host chain (ci/asan_preprocess_probe.cpp) found two out-of-bounds, one in the vendor's own
   permute_B_rows_for_mixed_gemm, and neither failed where it happened. Was inverting right, or did I get lucky and
   skip a step that costs more later?

2. quactlize/formats.py makes the format readiness table executable: capability sets modelled on vLLM's GGUF plugin,
   storage growth computed from block struct fields. Is putting dispatch policy (DENSE_CROSSOVER_ROWS, GEMV_MAX_ROWS)
   in the same file as format metadata a mistake? Where does this break when the device half lands and tactic
   selection becomes real?

3. I changed ColumnsInterleaved in my mixed_gemm_B_layout.h shim from a hardcoded 256 to
   ElementsPerCacheLine/ThreadblockK. That shim declares the PHYSICAL LAYOUT the kernels assume. Is deriving it from
   a 128-byte cache line the right model for the PPU's AIU, or have I copied NVIDIA's answer into a tree whose
   accelerator differs? What evidence would settle it?

4. tests/test_preprocess_ops.py claims its oracles do not call the code under test. Find any place where that claim
   is false, or where an "independent" oracle is a re-derivation sharing a misconception.

Be specific, cite files/lines. If a change I made is wrong, say so plainly.

## Last assistant conclusions

### 2026-08-01 04:48 UTC

My position: host-first was the right correction to the landing order, but you have overclaimed what it proves. There is also one live host OOB, one wrong storage entry, and an unproven NVIDIA-derived layout presented as PPU fact.

## 1. Host first: right, but only for the pure host core

You were right to invert the order for the preprocessing algorithm. Establishing the PPU Torch ABI is not a prerequisite for running ASAN over pure C++ indexing. Finding two real OOBs proves this was engineering leverage, not luck. My earlier ordering was too rigid on that point.

You did not, however, eliminate the ABI step. `CppExtension` compiles against whichever Torch happens to be imported at build time ([setup.py:25](/root/marlin_ppu/quactlize/setup.py:25)), and your own build instructions acknowledge that the target-installed Torch must supply the ABI ([pyproject.toml:1](/root/marlin_ppu/quactlize/pyproject.toml:1)). Operator-only avoids `PyInit_*`; it does not avoid libtorch’s C++ ABI, dispatcher ABI, `_GLIBCXX_USE_CXX11_ABI`, compiler/STL, or vendor-ScalarType differences. A `.so` built on this host is a test artifact, not a deployable PPU artifact.

The bigger correction: ASAN does not cover the entire host half. Its executable links only `cutlass_preprocessors.cpp` ([asan_preprocess_probe.cpp:13](/root/marlin_ppu/quactlize/ci/asan_preprocess_probe.cpp:13)) and calls the raw quantize/preprocess chain ([asan_preprocess_probe.cpp:52](/root/marlin_ppu/quactlize/ci/asan_preprocess_probe.cpp:52)). It excludes the Torch-facing packers—and those contain another OOB:

- `pack_int8_tensor_to_packed_int4` allocates `ceil(n/2)` bytes but unconditionally reads elements `2*i` and `2*i+1` ([weight_preprocess_ops.cpp:319](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:319)).
- The unsigned packer repeats the bug at [weight_preprocess_ops.cpp:354](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:354).

For odd final dimensions, the last `elt_1` is out of bounds. Since unpacking always doubles the dimension, the honest fix is probably to reject odd lengths, not silently pad.

So: keep the host core first and separately sanitizable. Before distributing the Torch `.so` or binding device operations, establish the target Torch identity and rebuild/load-test there. That deferred step is cheap if host and device libraries remain separate; it becomes expensive if you freeze a single combined `_C` artifact prematurely.

## 2. `formats.py`: metadata and capabilities can coexist; tactic policy should not

Putting format identity, block structure, and declarative capability sets together is defensible. Putting `DENSE_CROSSOVER_ROWS` and actual selection policy there is a mistake.

The file itself admits that 512 was not measured as a crossover—only that 2048 beat fused by 2.1× ([formats.py:144](/root/marlin_ppu/quactlize/quactlize/formats.py:144)). A real crossover depends on at least device revision, kernel build, M/N/K, group size, batch/expert shape, activation dtype, alignment, workspace and resident/cached weights. `select_path(qtype, num_rows)` cannot represent that ([formats.py:153](/root/marlin_ppu/quactlize/quactlize/formats.py:153)).

There are already two concrete semantic errors:

- `GPTQ_INT4_ASYM` has growth `0.0` merely because GPTQ scales are fp16 ([formats.py:110](/root/marlin_ppu/quactlize/quactlize/formats.py:110)). That ignores asymmetric GPTQ’s packed zero points. vLLM models them as packed `int32` `qzeros`, separate from fp16 scales ([vLLM source](https://github.com/vllm-project/vllm/blob/124154a8843d1f8e4d4e2d5d466e2d3ebc3716da/vllm/model_executor/layers/quantization/auto_gptq.py#L404-L445)). Expanding those zeros is not free. `0.0` is wrong; it should be shape/group-size-dependent or conservatively `None`, like AWQ.

- Storage admissibility is not enforced by selection. `needs_native_scale(Q3_K)` says the fp16 route violates the storage constraint, yet `select_path(Q3_K, 1)` deliberately returns `"fused_fp16_scale"` ([test_formats.py:87](/root/marlin_ppu/quactlize/tests/test_formats.py:87)). The selector confuses “a kernel exists” with “the required representation exists and is allowed.”

The registry compounds this: it reduces evidence to `format -> any harness` and then uses that to approve every path containing the format ([registry.py:76](/root/marlin_ppu/quactlize/ci/registry.py:76), [registry.py:138](/root/marlin_ppu/quactlize/ci/registry.py:138)). A Q4_K native-decode test can therefore greenlight Q4_K GEMV, fused-fp16 and dense fallback without testing those paths.

Keep `formats.py` for storage descriptors and perhaps declarative capabilities. Put tactics in a PPU backend registry whose entries implement something like `supports(problem, representation, device)`; put measured thresholds/autotuning in a device-and-kernel-version-specific policy layer.

## 3. `ColumnsInterleaved`: 256 was wrong; the replacement is NVIDIA-correct, not PPU-proven

Your statement that these are “the PPU’s, not NVIDIA’s” is plainly unsupported ([mixed_gemm_B_layout.h:12](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_extensions/gemm/kernel/mixed_gemm_B_layout.h:12)).

In fact, the formula is NVIDIA’s exact formula: TensorRT-LLM defines `ElementsPerCacheLine = 128*8/bits` and divides it by `ThreadblockK` for `uint8` and `uint4` B operands ([NVIDIA source](https://github.com/NVIDIA/TensorRT-LLM/blob/09b6bea1642aed3b533cbb6b71db586e19d5f300/cpp/tensorrt_llm/cutlass_extensions/include/cutlass_extensions/gemm/kernel/mixed_gemm_B_layout.h#L87-L120)). Your hardcoded `ThreadblockK = 64` and results 2/4/8 reproduce that design ([mixed_gemm_B_layout.h:73](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_extensions/gemm/kernel/mixed_gemm_B_layout.h:73)).

That makes the change memory-safe and likely correct for the NVIDIA-derived consumer. It does not prove it is the PPU AIU’s physical layout. Cache-line size alone cannot determine a swizzle; lane mapping, load width, MMA K tile and the consumer’s address calculation do.

Worse, the host actually composes two layouts: the NVIDIA-style column interleave first, then the PPU-specific 256-row AIU interleave ([cutlass_preprocessors.cpp:663](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:663)). The AIU test compares that result against `plain`, which already contains the NVIDIA transform ([test_preprocess_ops.py:203](/root/marlin_ppu/quactlize/tests/test_preprocess_ops.py:203)). Thus it cannot detect a wrong base interleave.

What settles it:

- The device kernel’s B-load offset/lane map or vendor preprocessing contract for the exact kernel.
- An end-to-end PPU test using basis/unique-pattern weights and a CPU dense golden, across nondegenerate K/N shapes.
- Ideally, an offset-by-offset comparison between host preprocessing and the device iterator’s expected addresses.

Until then, call this layout “NVIDIA-derived, memory-safe, PPU-unverified.” Calling it the physical layout the PPU kernels assume is wrong.

## 4. The oracle-independence claim is false

Several examples:

- “Each is the other’s oracle” for pack/unpack explicitly runs two operations from the code under test ([test_preprocess_ops.py:60](/root/marlin_ppu/quactlize/tests/test_preprocess_ops.py:60)). They can share reversed nibble order and remain perfect inverses.
- The supposedly strongest transpose oracle uses the production packer for both input and expected output ([test_preprocess_ops.py:89](/root/marlin_ppu/quactlize/tests/test_preprocess_ops.py:89)). Torch’s transpose is independent; the packed-byte convention is not.
- The quantizer comparison decodes `got` with the production unpacker ([test_preprocess_ops.py:255](/root/marlin_ppu/quactlize/tests/test_preprocess_ops.py:255)). The quantizer and unpacker both encode low-nibble-first, so that misconception can cancel.
- The AIU oracle explicitly re-derives the production inde
… [truncated 1127 chars]
