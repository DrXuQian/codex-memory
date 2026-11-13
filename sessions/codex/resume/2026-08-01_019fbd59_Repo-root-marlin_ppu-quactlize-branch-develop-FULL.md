# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop. FULL LOCAL ACCESS -- read files, run commands.
DO NOT EDIT ANY FILE. Report only.

Also readable locally, and you should USE them rather than recall:
  /root/llama.cpp/ggml/src/ggml-cuda/   (mmq.cuh, mmvq.cu, vecdotq.cuh, dequantize.cuh, convert.cu, ggml-common.h)
  /root/marlin_ppu/Kernels/moe_ffn/w4a16/vllm/   (a subset; vLLM's GGUF plugin itself is NOT here -- say so if you
  cannot read it, do not reconstruct it from memory)

TWO SEPARATE TASKS. Answer both, keep them clearly separated.

== TASK A: code cleanliness and maintainability ==

Review for clean code, not for bugs (a separate review already covered bugs). Cover at least:
  quactlize/layouts.py, quactlize/formats.py, quactlize/__init__.py
  quactlize/csrc/preprocess/weight_layout.h, quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp
  ci/local_gates.py, ci/registry.py, dev/fold_derivation/overlay_targets_check.py
  build.sh, benchmarks/run_batch.sh, quactlize/csrc/CMakeLists.txt.in
  tests/

Be concrete and ranked. I care most about:
  - duplication that will drift (two places holding one fact)
  - comments that explain history where the code should just be obvious, vs comments that genuinely carry a
    non-recoverable fact. This tree deliberately records WHY in comments; tell me where that has become noise.
  - things that are hard to change: a new quant format, a new layout step, a new gate -- how many files does each
    touch, and which of those should it not have to?
  - anything a reader would have to run to understand
This repo is about to be published. Judge it as a stranger reading it for the first time.

== TASK B: how else could the NATIVE scale be loaded? ==

Our problem: GGUF k-quants store scales in a packed native form. For Q4_K that is 16 bytes per 256-weight block:
half d, half dmin, uint8 scales[12] (eight 6-bit scale/min pairs). Expanding those to fp16 planes costs +11.1% of
stored bytes for Q4_K (+52.4% Q2_K, +16.4% Q3_K, +9.1% Q5_K, +6.7% Q6_K) -- see quactlize/formats.py, which computes
these -- and the product constraint is that an offline reorder is allowed but an increase in STORED bytes is not.

Our current implementation: decode the 16-byte unit INSIDE the GEMM mainloop
  third_party/actlize/include/cutlass/gguf_packed_scale.h  (group_pair_of_words<G, ZMul, ScaleBias>)
  third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp (kPackedScaleOn etc.)
  quactlize/include/gguf_scale_layout.hpp  (the block described as cute Layouts)
Measured: the native-format path is ~12.9% SLOWER than fp16 scale planes at the decode band, and the reason is not
understood. In-GEMM decode is also redundant by a factor of the number of m-tiles: every CTA decodes its n-tile's
scales for all k, so M=1 costs 1.125x the work and M=2048 with TileM=128 costs 16x.

READ how llama.cpp actually does it -- MMQ, MMVQ/vec_dot, and the dequantize path -- and tell me what SCHEMES exist
for getting a native packed scale to the math, beyond what we do. For each scheme: where the decode happens, what it
is amortised over, what it costs in registers/shared memory, and which of our three bands it suits (decode M=1,
mid M~128, prefill M>=512). Say plainly which one you would choose for each band and why.

I am NOT asking for a code patch. I am asking whether our in-GEMM decode is the right shape at all.

- **Thread ID:** `019fbd59-987b-7991-acf5-d1bfedd48a0b`
- **Started / last event:** 2026-08-01 12:43 UTC → 2026-08-01 13:01 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T20-43-13-019fbd59-987b-7991-acf5-d1bfedd48a0b.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "f7e9a92ad87d86fd7d886466eec22c54c41833cf", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-01_019fbd59_Repo-root-marlin_ppu-quactlize-branch-develop-FULL.md](../transcripts/2026-08/2026-08-01_019fbd59_Repo-root-marlin_ppu-quactlize-branch-develop-FULL.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop. FULL LOCAL ACCESS -- read files, run commands.
DO NOT EDIT ANY FILE. Report only.

Also readable locally, and you should USE them rather than recall:
  /root/llama.cpp/ggml/src/ggml-cuda/   (mmq.cuh, mmvq.cu, vecdotq.cuh, dequantize.cuh, convert.cu, ggml-common.h)
  /root/marlin_ppu/Kernels/moe_ffn/w4a16/vllm/   (a subset; vLLM's GGUF plugin itself is NOT here -- say so if you
  cannot read it, do not reconstruct it from memory)

TWO SEPARATE TASKS. Answer both, keep them clearly separated.

== TASK A: code cleanliness and maintainability ==

Review for clean code, not for bugs (a separate review already covered bugs). Cover at least:
  quactlize/layouts.py, quactlize/formats.py, quactlize/__init__.py
  quactlize/csrc/preprocess/weight_layout.h, quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp
  ci/local_gates.py, ci/registry.py, dev/fold_derivation/overlay_targets_check.py
  build.sh, benchmarks/run_batch.sh, quactlize/csrc/CMakeLists.txt.in
  tests/

Be concrete and ranked. I care most about:
  - duplication that will drift (two places holding one fact)
  - comments that explain history where the code should just be obvious, vs comments that genuinely carry a
    non-recoverable fact. This tree deliberately records WHY in comments; tell me where that has become noise.
  - things that are hard to change: a new quant format, a new layout step, a new gate -- how many files does each
    touch, and which of those should it not have to?
  - anything a reader would have to run to understand
This repo is about to be published. Judge it as a stranger reading it for the first time.

== TASK B: how else could the NATIVE scale be loaded? ==

Our problem: GGUF k-quants store scales in a packed native form. For Q4_K that is 16 bytes per 256-weight block:
half d, half dmin, uint8 scales[12] (eight 6-bit scale/min pairs). Expanding those to fp16 planes costs +11.1% of
stored bytes for Q4_K (+52.4% Q2_K, +16.4% Q3_K, +9.1% Q5_K, +6.7% Q6_K) -- see quactlize/formats.py, which computes
these -- and the product constraint is that an offline reorder is allowed but an increase in STORED bytes is not.

Our current implementation: decode the 16-byte unit INSIDE the GEMM mainloop
  third_party/actlize/include/cutlass/gguf_packed_scale.h  (group_pair_of_words<G, ZMul, ScaleBias>)
  third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp (kPackedScaleOn etc.)
  quactlize/include/gguf_scale_layout.hpp  (the block described as cute Layouts)
Measured: the native-format path is ~12.9% SLOWER than fp16 scale planes at the decode band, and the reason is not
understood. In-GEMM decode is also redundant by a factor of the number of m-tiles: every CTA decodes its n-tile's
scales for all k, so M=1 costs 1.125x the work and M=2048 with TileM=128 costs 16x.

READ how llama.cpp actually does it -- MMQ, MMVQ/vec_dot, and the dequantize path -- and tell me what SCHEMES exist
for getting a native packed scale to the math, beyond what we do. For each scheme: where the decode happens, what it
is amortised over, what it costs in registers/shared memory, and which of our three bands it suits (decode M=1,
mid M~128, prefill M>=512). Say plainly which one you would choose for each band and why.

I am NOT asking for a code patch. I am asking whether our in-GEMM decode is the right shape at all.

## Last assistant conclusions

### 2026-08-01 13:01 UTC

# Task A — code cleanliness and maintainability

Publication verdict: the code records its reasoning unusually well, but it currently reads partly as a laboratory notebook. The main risk is not naming or intent; it is that several supposedly canonical facts have multiple writable representations, and some have already diverged.

## Ranked findings

1. The build overlay has two implementations of one manifest, and the gate validates only one

[`build.sh --print-overlay`](/root/marlin_ppu/quactlize/build.sh:35) enumerates the source globs independently from the real copy path at [`build.sh:135`](/root/marlin_ppu/quactlize/build.sh:135). The extension whitelist occurs repeatedly, and `_overlay_dirs` is declared twice.

[`overlay_targets_check.py`](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:84) correctly asks `build.sh` for its manifest and lets CMake parse CMake, but that means it proves the print implementation—not that the later copy implementation agrees with it. This is exactly the kind of duplication the comments say the gate eliminates.

The same build configuration has already drifted:

- `build.sh` defaults to tile `32×32`, warp `16×16`, stages `3` at [`build.sh:260`](/root/marlin_ppu/quactlize/build.sh:260).
- CMake’s comment says those are the stock defaults, but its actual defaults are `64×64`, `32×32`, stages `4` at [`CMakeLists.txt.in:87`](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:87).

Recommendation: make `--print-overlay` and copying consume one manifest-producing function. Give CMake or the shell—not both—ownership of tuning defaults.

2. Format, layout, and gate metadata are all multi-registry systems

Layouts have a Python registry at [`layouts.py:198`](/root/marlin_ppu/quactlize/quactlize/layouts.py:198) and a handwritten C++ registry at [`weight_layout.h:30`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/weight_layout.h:30). The compiled cross-check is useful, but it detects rather than prevents drift. The C++ introductory example is already stale: it says `mmarow_tr...` rather than the current `mmarow32_tr...` at [`weight_layout.h:4`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/weight_layout.h:4).

Format facts are split across:

- `QuantType`, block arithmetic and four capability sets in [`formats.py`](/root/marlin_ppu/quactlize/quactlize/formats.py:26).
- `HARNESS_PATHS`, `HARNESSES`, `FORMATS`, and `FORMAT_TO_QUANT_TYPE` in [`ci/registry.py`](/root/marlin_ppu/quactlize/ci/registry.py:37).
- GEMV format rows in [`CMakeLists.txt.in:154`](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:154).
- MoE format rows in [`CMakeLists.txt.in:612`](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:612).

`HARNESS_PATHS` and `HARNESSES` themselves duplicate every harness key. Missing path metadata is silently treated as an empty list through `.get()`.

Gate definitions similarly span `GATES`, `SYNTAX`, and the separate `GATE_FLAGS` at [`local_gates.py:41`](/root/marlin_ppu/quactlize/ci/local_gates.py:41), while dispatch is a manual kind chain at [`local_gates.py:174`](/root/marlin_ppu/quactlize/ci/local_gates.py:174).

Recommendation: introduce declarative `FormatSpec`, `LayoutSpec`, `HarnessSpec`, and `GateSpec` records and derive the lookup tables. A small checked-in JSON/TOML/Python manifest could generate the C++ and CMake fragments.

3. The public Python API contradicts the named-layout architecture

The C++ layer declares `preprocess_weights_to_layout` as the supported entry point and registers the boolean form under an underscore at [`weight_preprocess_ops.cpp:500`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:500).

The package does the reverse: it publicly exports the two-boolean function at [`__init__.py:58`](/root/marlin_ppu/quactlize/quactlize/__init__.py:58), does not wrap the named-layout operation, and the tests mostly call raw `torch.ops` rather than exercise the public wrapper. That makes the clean abstraction visible in the implementation but unavailable through the package’s intended surface.

`matmul_w4a16` is also exported despite always raising `NotImplementedError` at [`__init__.py:135`](/root/marlin_ppu/quactlize/quactlize/__init__.py:135). For a newly published package, capability discovery is cleaner than presenting a callable-looking permanent stub.

4. Historical comments have crossed from rationale into incident diary

The valuable comments are those that preserve facts a reader could not recover locally:

- Ordered layout-token naming.
- The `F*TK*bits >= 256` hardware delivery floor at [`layouts.py:127`](/root/marlin_ppu/quactlize/quactlize/layouts.py:127).
- Device and host compilation requiring separate definitions at [`CMakeLists.txt.in:5`](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:5).
- Why an overlay is necessary.
- Why missing optional sources and skipped AIU transforms must fail loudly.

The noise is the recurring chronology: “first version did X,” exact box-round counts, personal hypotheses, old failure counts, and measurements no longer used by control flow. Examples include the full xplane incident narrative at [`layouts.py:102`](/root/marlin_ppu/quactlize/quactlize/layouts.py:102), AIU call history at [`weight_preprocess_ops.cpp:170`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:170), and extensive generator/performance notebooks beginning around [`CMakeLists.txt.in:585`](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:585).

The packed-scale collective demonstrates the danger: comments say the zero tile disappears, while actual storage retains both decoded fp16 planes and adds raw staging at [`ppu_mma…mixed_input.hpp:549`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:549). Another nearby comment correctly describes three tiles. The narrative now contains multiple generations of the design.

Move experiment chronology and exact measurements into dated `docs/experiments/` records. Keep one short invariant comment plus a link or experiment ID. Also remove publication blemishes such as `to每 code` at [`layouts.py:171`](/root/marlin_ppu/quactlize/quactlize/layouts.py:171) and `only模型` at [`overlay_targets_check.py:24`](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:24).

5. `CMakeLists.txt.in` is a target registry, experiment notebook, and code generator in one 894-line file

`ppu_w4a16_executable` is a useful central wrapper at [`CMakeLists.txt.in:33`](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:33), but nearly every target still repeats a multiline registration followed by `target_compile_options(... -w)`. The latter belongs in the wrapper if it is genuinely universal.

GEMV, split-K, and MoE each implement similar row parsing, field validation, `.cu.in` generation, declaration assembly, and `copy_if_different` logic. Extracting the generator to a small script would make it directly testable and leave CMake responsible for build graph construction. `MOE_CORES` being reused for the GEMV generator at [`CMakeLists.txt.in:245`](/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:245) is one symptom of their accidental coupling.

6. The preprocessing operator file contains mechanical duplication

Argument validation and logical-shape recovery repeat across the permutation, transpose, and full preprocessing paths at [`weight_preprocess_ops.cpp:55`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:55).

Signed and unsigned int4 packers are nearly identical, including a duplicated 11-line odd-dimension explanation at [`weight_preprocess_ops.cpp:360`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:360) and [`weight_preprocess_ops.cpp:407`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:407). The 
… [truncated 13089 chars]
