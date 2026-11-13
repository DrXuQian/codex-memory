# Repo /root/marlin_ppu/quactlize, branch develop. FULL LOCAL ACCESS -- read files, run commands.
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

---

## User · 2026-08-01 12:43 UTC

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

## Assistant · 2026-08-01 12:43 UTC

I’ll treat these as two independent reviews: first, map the maintenance “sources of truth” and change surfaces; second, trace each native-scale loading strategy through the local llama.cpp CUDA code and compare it with this repository’s GEMM path. I’ll only run read-only commands and will not edit the tree.

<details><summary>8 tool call(s)</summary>

- `exec: const p = await tools.update_plan({plan:[ {step:"Inspect repository structure, status, and all Task A target files/tests",status:"in_progress"}, {step:"Trace duplication and change surfaces for formats, layouts, gates, build scripts, and te …`
- `exec: const r = await tools.exec_command({"cmd":"pwd && git branch --show-current && git status --short && rg --files -g 'AGENTS.md' -g '!third_party/**' -g '!build/**' && rg --files quactlize ci dev/fold_derivation tests benchmarks | sed -n '1,2 …`
- `exec: const r = await tools.exec_command({"cmd":"find .. -name AGENTS.md -print\nrg --files quactlize ci dev/fold_derivation tests benchmarks | sed -n '1,320p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":3000 …`
- `exec: const r = await tools.exec_command({"cmd":"wc -l quactlize/layouts.py quactlize/formats.py quactlize/__init__.py quactlize/csrc/preprocess/weight_layout.h quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp ci/local_gates.py ci/registr …`
- `exec: const r = await tools.exec_command({"cmd":"rg --files /root/llama.cpp/ggml/src | rg '/ggml-common\\.h$|/ggml-cuda/(mmq|mmvq|vecdotq|dequantize|convert)' \nrg --files /root/marlin_ppu/Kernels/moe_ffn/w4a16/vllm | sed -n '1,240p'","workdir":" …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/layouts.py\nnl -ba quactlize/formats.py\nnl -ba quactlize/__init__.py","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":50000}); text(r.output)`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/formats.py","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":30000}); text(r.output)`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/csrc/preprocess/weight_layout.h\nnl -ba quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":5 …`

</details>

## Assistant · 2026-08-01 12:44 UTC

The first maintenance pattern is already clear: layout identity is intentionally modeled as data in Python, but then manually copied into C++ and partially bypassed by the public Python wrapper. I’m checking whether the tests and gates truly make that duplication safe, and how many other registries repeat the same facts.

<details><summary>10 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"nl -ba ci/registry.py\nnl -ba ci/local_gates.py\nnl -ba dev/fold_derivation/overlay_targets_check.py","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":50000}); text( …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba build.sh | sed -n '1,220p'\nnl -ba build.sh | sed -n '221,420p'\nnl -ba benchmarks/run_batch.sh","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":50000}); tex …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba build.sh | sed -n '210,370p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":30000}); text(r.output)`
- `exec: const r = await tools.exec_command({"cmd":"rg -n '^#|^function|^endfunction|cutlass_example_add_executable|target_compile_(options|definitions)|foreach|set\\(' quactlize/csrc/CMakeLists.txt.in","workdir":"/root/marlin_ppu/quactlize","yield_ …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '1,150p'\nnl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '146,280p'\nnl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '276,460p'\nnl -ba quactlize …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba tests/test_layouts.py\nnl -ba tests/test_formats.py\nnl -ba tests/test_preprocess_ops.py","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":50000}); text(r.out …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba tests/test_formats.py\nnl -ba tests/test_layouts.py | sed -n '300,500p'\nnl -ba tests/test_preprocess_ops.py | sed -n '1,100p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000," …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n '^#include|^#define|^template|^struct |^static |^int main|CHECK|MATCH|MISMATCH|fopen|ifstream|usage:' tests/*.cu tests/*.h tests/*.hpp","workdir":"/root/marlin_ppu/quactlize","yield_time_ms": …`
- `exec: const r = await tools.exec_command({"cmd":"diff -u tests/test_w1a16_diag.cu tests/test_w2a16_diag.cu | sed -n '1,240p'\ndiff -u tests/test_w2a16_diag.cu tests/test_w4a16_diag.cu | sed -n '1,240p'\ndiff -u tests/test_w1a16_grouped.cu tests/t …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n 'MIXED_GEMM|preprocess_weights_(for_mixed_gemm|to_layout)|mmarow|mixed_gemm_aiu|QuantType|FUSED_NATIVE_SCALE|HARNESS_PATHS|HARNESSES|GATES|SYNTAX|REQUIRED|test_q4k_packed_gemm|PPU_PACKED_SCAL …`

</details>

## Assistant · 2026-08-01 12:45 UTC

For Task B I’m separating three genuinely different shapes: direct per-dot decode (MMVQ/vec-dot), CTA-cooperative decode into shared state (MMQ), and a separate dequantization kernel/materialized workspace. That distinction—not merely the bit-unpack formula—determines whether work is repeated across M tiles.

<details><summary>12 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"rg -n 'block_q[23456]_K|get_scale_min_k4|K_SCALE_SIZE|QK_K|scales\\[' /root/llama.cpp/ggml/src/ggml-common.h | sed -n '1,260p'\nrg -n 'q4_K|Q4_K|block_q4_K|get_scale_min_k4|scales' /root/llama.cpp/ …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-common.h | sed -n '80,180p'\nnl -ba /root/llama.cpp/ggml/src/ggml-common.h | sed -n '280,365p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '1,30 …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n 'load_tiles\\(|x_tile|shared|__shared__|blockIdx|mmq_x|mmq_y' /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | tail -n 180\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '3560,3890p' …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '3440,3540'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '3925,3965'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '3440,3540p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '3925,3965p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-cuda/vecdotq.cuh | sed -n '500,570p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/vecdotq.cuh | sed -n '840,920p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmvq. …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n 'mul_mat_vec_q|vec_dot\\(' /root/llama.cpp/ggml/src/ggml-cuda/mmvq.cu | sed -n '1,160p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmvq.cu | sed -n '700,930p'\nnl -ba /root/llama.cpp/ggml/src …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmvq.cu | sed -n '455,705p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":40000}); text(r.output)`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-cuda/dequantize.cuh\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/convert.cu | sed -n '130,315p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/convert.cu | sed -n '52 …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n 'scale|dequant|qweight|zero|g_idx|group' /root/marlin_ppu/Kernels/moe_ffn/w4a16/vllm/marlin/include /root/marlin_ppu/Kernels/moe_ffn/w4a16/vllm/marlin/src /root/marlin_ppu/Kernels/moe_ffn/w4a …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n 'sh_s|scales_ptr|zp_ptr|cp_async|fetch_to_shared|FragS|scale\\(' /root/marlin_ppu/Kernels/moe_ffn/w4a16/vllm/marlin/include/marlin_template.h | sed -n '1,300p'\nnl -ba /root/marlin_ppu/Kernel …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h\nnl -ba quactlize/include/gguf_scale_layout.hpp\nnl -ba quactlize/include/gguf_scale_decode.hpp","workdir":"/root/marlin_ppu/quactlize …`

</details>

## Assistant · 2026-08-01 12:52 UTC

I’ve finished the first structural pass. The clearest publication risks are already concrete: the overlay manifest is implemented twice inside `build.sh`, CMake’s kernel defaults disagree with `build.sh`, and format/layout/gate metadata is spread across multiple registries. I’m now pinning down the exact native-scale dataflow and resource costs before ranking the report.

<details><summary>5 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '170,285p;1240,1515p'\nnl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | se …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '310,430p;1350,1475p;1530,1670p'\nrg -n \"smem_scale_packed|smem_scale_raw|SmemLayoutScale …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '418,600p;1475,1525p;960,1030p;1100,1235p'","workdir":"/root/marlin_ppu/quactlize","yield_ …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-common.h | sed -n '80,95p;275,365p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '2070,2245p;3435,3535p;3920,3970p'\nnl -ba /root/llama.cpp/ggml/ …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba /root/llama.cpp/ggml/src/ggml-cuda/vecdotq.cuh | sed -n '500,532p;860,910p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | sed -n '3940,3970p'\nnl -ba /root/llama.cpp/ggml/src/ggml-cud …`

</details>

## Assistant · 2026-08-01 12:53 UTC

The native-scale comparison is now clear: llama.cpp uses three distinct shapes, not one universal loader—register-local extraction for MMVQ, cooperative expansion into CTA shared memory for MMQ, and a separate full dequantization kernel. Your path is closest to MMQ, but its actual transient footprint is raw staging plus both decoded fp16 planes; several nearby comments still describe an older “zero tile disappears” design. I’m checking the publication-facing claims and gates against what the code actually exposes.

<details><summary>9 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/layouts.py | sed -n '1,290p'\nnl -ba quactlize/formats.py | sed -n '1,260p'\nnl -ba quactlize/__init__.py | sed -n '1,180p'\nnl -ba quactlize/csrc/preprocess/weight_layout.h | sed  …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/formats.py | sed -n '20,165p'\nnl -ba quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp | sed -n '45,215p;315,515p'\nnl -ba ci/registry.py | sed -n '1,220p'\nnl -ba ci/local …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba ci/registry.py | sed -n '1,115p'\nnl -ba quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp | sed -n '325,515p'\nnl -ba dev/fold_derivation/overlay_targets_check.py | sed -n '1,220p'\n …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba build.sh | sed -n '1,65p'\nnl -ba dev/fold_derivation/overlay_targets_check.py | sed -n '1,190p'\nnl -ba benchmarks/run_batch.sh | sed -n '1,245p'\nnl -ba quactlize/csrc/CMakeLists.txt.in |  …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '1,165p'\nnl -ba benchmarks/run_batch.sh | sed -n '75,230p'\nfind tests -maxdepth 2 -type f -printf '%P\\n' | sort\nwc -l tests/* 2>/dev/null | tail …`
- `exec: const jobs = await Promise.all([ tools.exec_command({cmd:"PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_formats.py tests/test_layouts.py",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:30000,max_output_tok …`
- `wait: {"cell_id":"41","yield_time_ms":30000,"max_tokens":15000}`
- `exec: const r = await tools.exec_command({"cmd":"ps -eo pid,etime,cmd | rg 'pytest|test_layouts' || true\ngit status --short\nfind . -maxdepth 3 -type f -mmin -3 -printf '%p\\n' | sort | head -80","workdir":"/root/marlin_ppu/quactlize","yield_tim …`
- `exec: const r = await tools.exec_command({"cmd":"ps -p 20620 -o pid=,etime=,stat=,cmd=","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":2000}); text(r.output);`

</details>

## Assistant · 2026-08-01 12:56 UTC

The local declaration checks are green (registry: 0 problems; overlay: 62 files, 33 targets, all required targets present), and both shell scripts parse. Those successes do not invalidate the maintainability findings: in particular, the overlay gate consumes `build.sh --print-overlay`, while the real copy path is a separate implementation, so the check can only validate the first one.

<details><summary>6 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_formats.py tests/test_layouts.py","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":30000,"max_output_tokens":5000} …`
- `wait: {"cell_id":"44","yield_time_ms":30000,"max_tokens":7000}`
- `exec: const r = await tools.write_stdin({"session_id":98438,"chars":"","yield_time_ms":30000,"max_output_tokens":7000}); text(JSON.stringify(r));`
- `exec: const r = await tools.exec_command({"cmd":"git status --short\ngit diff --stat\ngit diff -- quactlize layouts.py 2>/dev/null || true","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":3000}); text(r.output);`
- `exec: const r = await tools.update_plan({plan:[{step:"Inspect Task A targets and tests","status":"completed"},{step:"Trace duplicated facts and change surfaces","status":"completed"},{step:"Trace current and llama.cpp native-scale dataflows","sta …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"MMQ_X|mmq_x =|launch_mul_mat_q<\" /root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh | tail -80\nrg -n \"#define MMQ|MMQ_MMA_TILE_X_K_Q8_1|tile_x_sizes|GGML_TYPE_Q4_K\" /root/llama.cpp/ggml/src/ggm …`

</details>

## Assistant · 2026-08-01 13:01 UTC

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

Signed and unsigned int4 packers are nearly identical, including a duplicated 11-line odd-dimension explanation at [`weight_preprocess_ops.cpp:360`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:360) and [`weight_preprocess_ops.cpp:407`](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:407). The indentation around both copies is visibly broken.

A shared shape/packing loop with a signedness policy would reduce four implementations to one structural implementation plus small conversion policies.

7. Tests contain good evidence but too much independent machinery

The Python layout test embeds and compiles substantial C++ programs, and pins exact historical difference counts such as `6144/8192` and `6114/8192` at [`test_layouts.py:284`](/root/marlin_ppu/quactlize/tests/test_layouts.py:284). Those numbers prove a derivation but are not a useful public contract. A reader has to run the compiler probe to learn why they matter.

Other duplication includes:

- Extension-loading fixtures in both [`test_layouts.py:371`](/root/marlin_ppu/quactlize/tests/test_layouts.py:371) and [`test_preprocess_ops.py:42`](/root/marlin_ppu/quactlize/tests/test_preprocess_ops.py:42).
- Near-clone W1/W2/W4 diagnostic programs.
- Repeated device allocation, comparison, non-finite and vacuity checks across CUDA tests.
- Multiple bespoke binary-fixture readers; the four files in `tests/data/` have no common provenance/checksum manifest.

A shared test-support layer and fixture manifest would shorten the suite substantially without weakening its independent oracles.

8. Some CI checks are source-text heuristics presented as declarations

[`registry.py:136`](/root/marlin_ppu/quactlize/ci/registry.py:136) looks for strings such as `fopen`, `MISMATCH`, and `return bad`. It strips `//` comments but not block comments and cannot establish control flow. This is reasonable as a lint, but its documentation should not imply it verifies the semantic declaration.

The overlay check returns success when CMake is unavailable at [`overlay_targets_check.py:110`](/root/marlin_ppu/quactlize/dev/fold_derivation/overlay_targets_check.py:110), while `local_gates.py` converts any zero exit to `PASS`, losing `SKIP`. A structured status protocol would prevent this class of runner drift.

## Current change cost

| Change | Current touch surface | Unnecessary touches |
|---|---:|---|
| New quant format | Roughly 5–8 files: Python enum/storage/capabilities, CI format mapping and harness metadata, one or two CMake format tables, kernel traits, harness and target | CI spelling maps and CMake format catalogs should derive from one format specification |
| New layout step | Roughly 3–5 files: Python step/layout, C++ literal registry, preprocessing implementation/flags, compiled cross-check, possibly public API | The C++ registry should be generated; callers should only see the named-layout API |
| New device gate | Roughly 2–6 files: source, `GATES`/`SYNTAX`/`GATE_FLAGS`, CMake target, harness registry, `run_batch.sh` build/freshness/check lists, sometimes overlay `REQUIRED` | One `GateSpec` should drive build, invocation, fixtures, flags, and runner status |

## Readability without execution

A stranger currently has to run code to discover:

- The actual format/path coverage table (`python ci/registry.py`).
- Generated GEMV/MoE instantiation counts after CMake configuration.
- Whether device macros reached a target, by inspecting generated `build.make` or build logs.
- The meaning and origin of binary fixtures.
- Several xplane layout properties encoded only as compiler probes and exact byte-difference tests.

Those results should have generated, checked-in summaries or compact manifests; execution should validate them, not be the only way to learn them.

Verification performed without editing repository files:

- `69 passed` for `tests/test_formats.py` and `tests/test_layouts.py`.
- Registry check: `0 problem(s)`.
- Overlay check: 62 files, 33 targets, all three required targets present.
- `bash -n` passed for both shell scripts.
- The pre-existing `third_party/actlize` nested-worktree status remains; no files were edited.

# Task B — alternative native-scale loading schemes

## Bottom line

The current in-GEMM, CTA-shared decode is the right overall shape for the mid band around `M≈128`. It is the wrong shape for `M=1`, and it stops being the right amortization boundary once prefill spans several M tiles.

I would use:

- `M=1`: a native Q4_K GEMV with register-local scale extraction.
- `M≈128`: cooperative decode once per CTA weight tile into shared memory.
- `M>=512`: a transient prepass followed by dense GEMM—preferably full fp16 dequantization at genuinely large M; use scale-only expansion as the lower-workspace bridge if dense conversion has not crossed over.

The local vLLM subset does **not** contain vLLM’s GGUF plugin. It contains Marlin code consuming separate fp16 scales and packed zero points, e.g. [`marlin_template.h:63`](/root/marlin_ppu/Kernels/moe_ffn/w4a16/vllm/marlin/include/marlin_template.h:63). I therefore make no reconstructed claim about vLLM’s GGUF implementation.

## What the current path actually costs

For each Q4_K `(column, 256 K weights)` unit, the implementation:

1. `cp.async`s the reordered 16 native bytes into raw shared staging.
2. Loads four `uint32_t` words from that staging into registers.
3. Expands all eight scale/min pairs.
4. Stores eight fp16 scales plus eight fp16 zeros into the existing shared planes.

The load and stores are visible at [`ppu_mma…mixed_input.hpp:1439`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1439) and [`ppu_mma…mixed_input.hpp:1490`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1490).

That is, per unit per pipeline stage:

- 16 bytes raw shared staging.
- 32 bytes decoded fp16 scale/zero planes.
- 48 bytes total scale-related shared storage, versus 32 bytes for the fp16-plane baseline.
- Logical decoder state of four packed words, `d/-dmin`, a decoded pair and extraction temporaries. The file’s cited 186-register figure is whole-kernel pressure, not a clean incremental decoder count.

Decode happens after `cp_async_wait` and before the publishing barrier at [`ppu_mma…mixed_input.hpp:983`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:983). Thus native loading saves global scale bytes—16 rather than 32—but adds a raw shared read, 32 bytes of explicit shared stores, and arithmetic on the wait-to-barrier critical path. Those are concrete structural candidates for the 12.9% tax; the current ablation results do not yet identify which dominates.

Its decode is amortized across `TileM` rows, but repeated `ceil(M/TileM)` times.

## Schemes observed or directly enabled by the local code

| Scheme | Decode placement and amortization | Register/shared cost | Suitable band |
|---|---|---|---|
| MMVQ direct register extraction | Inside each native vec-dot fragment. Q4_K extracts only the two scale/min pairs needed by that fragment at [`vecdotq.cuh:864`](/root/llama.cpp/ggml/src/ggml-cuda/vecdotq.cuh:864). Repeated per token/dot; no cross-M reuse | Scale state is two `uint16_t` auxiliaries; surrounding dot has 2 q4 words, 4 q8 words, 2 activation scales and accumulators. No scale shared memory | Best for `M=1`; reasonable only for tiny batches |
| MMQ cooperative gmem→register→shared expansion | During CTA tile loading. Two lanes cooperate per Q4_K row, unpack scale/min words and store precombined `half2(d·scale, -dmin·min)` at [`mmq.cuh:2149`](/root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh:2149). Reused by all `mmq_x` M columns in the CTA; repeated across `ceil(M/mmq_x)` tiles | Modern MMA path stores 8 `half2`, or 32 scale bytes, per native block/weight row. DP4A retains `dm` plus decoded byte codes, about 20 bytes plus padding. No raw-scale shared staging, although its weight tile has other expanded data | Best around the mid band |
| Current async-staged CTA expansion | Native bytes first enter shared, then registers, then decoded shared planes. Reused across `TileM`; repeated across M tiles | 48 scale-related shared bytes per Q4_K unit per stage; four packed registers plus decode temporaries | Same mid-band family as MMQ, but with an extra shared staging round trip |
| Scale-only transient prepass | Decode every native scale unit once into global fp16 scale/zero planes, then run the existing fused fp16-plane GEMM. Decode is amortized across all M for that invocation | Decode kernel can use registers only; global workspace is 32 bytes per Q4_K block. Because the original 144-byte block remains resident, this is 22.2% additional transient workspace—not the 11.1% stored-format replacement growth | Poor at decode; plausible bridge from mid to prefill |
| Full dequantization then dense GEMM | `convert.cu` launches one block per 256-weight Q4_K block at [`convert.cu:204`](/root/llama.cpp/ggml/src/ggml-cuda/convert.cu:204). Each thread extracts two group pairs and writes fp16 weights; dense math never sees scales. Conversion is amortized across all M | No shared memory in this kernel; modest per-thread scale/product registers. Writes 512 fp16 bytes per 144-byte Q4_K source block, then dense GEMM reads them | Best for sufficiently large prefill |

One detail about llama.cpp’s full dequantizer: the scale-field extraction is not perfectly deduplicated inside the conversion block—eight threads sharing an `il` decode the same group pair for their different four-weight slices. Its important amortization win is instead that the completed fp16 weight is reused by the entire dense GEMM.

llama.cpp explicitly dispatches MMVQ only up to a maximum batch of eight at [`mmvq.cuh:3`](/root/llama.cpp/ggml/src/ggml-cuda/mmvq.cuh:3). MMQ selects M widths in multiples of eight up to 128 and grids them as `ceil(M/mmq_x)` at [`mmq.cuh:3958`](/root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh:3958) and [`mmq.cuh:4069`](/root/llama.cpp/ggml/src/ggml-cuda/mmq.cuh:4069). That dispatch split is the clearest evidence that scale loading should change shape by band.

## My band choices

### Decode, `M=1`

Choose MMVQ-style native GEMV.

There is no M reuse available, so paying for decoded shared planes, CTA barriers, and a tensor-core GEMM tile is unnecessary. Extract only the scale/min pair required by the current vec-dot fragment and keep it in registers. This repeats small bit extraction work across output fragments, but at `M=1` that is preferable to constructing a reusable object with no second consumer.

Do not transplant “decode in each MMA lane” into the existing GEMM. The collective’s own comments report that experiment multiplied work across lanes and warps. The successful shape is a specialized GEMV whose work decomposition gives each extracted pair directly to the dot that consumes it.

### Mid band, `M≈128`

Choose CTA-cooperative expansion into shared memory.

At `TileM=128`, decode occurs once for the whole band, so the user’s M-tile redundancy is absent. Shared publication gives the scale to all MMA consumers without per-lane extraction.

I would keep the current broad shape, but investigate its implementation against llama MMQ:

- llama reads native scales directly from global into registers and writes decoded shared values; it has no raw-scale shared stage.
- The current PPU version preserves asynchronous transport through raw staging, but consequently performs a second shared traversal and puts decode/stores immediately before the barrier.
- The repository records that a naïve direct synchronous version measured 24.17 µs versus a 20.2 µs baseline, so removing staging without a new overlap strategy is not justified.

The useful next comparison is therefore not “shared versus registers”; that has effectively been answered. It is “raw cp.async stage versus an overlapped cooperative direct loader,” while retaining one decoded shared result per CTA.

### Prefill, `M>=512`

Choose a transient prepass, normally full dequantization followed by dense GEMM.

At `TileM=128`, the current path decodes the same native scale four times at `M=512` and sixteen times at `M=2048`. A prepass performs the conversion once. The extra kernel and global workspace become increasingly cheap relative to reuse by the dense GEMM.

For very large M, full fp16 weight dequantization is the stronger choice because it removes packed-weight conversion from the GEMM as well as scale decoding. Your recorded 2.1× result at `M=2048` supports that direction, although [`DENSE_CROSSOVER_ROWS=512`](/root/marlin_ppu/quactlize/quactlize/formats.py:156) is explicitly unswept and `DEQUANT_THEN_DENSE` remains empty for lack of an independent harness.

A scale-only prepass is the sensible intermediate option when 512-byte-per-block fp16 weight workspace is undesirable or the fused packed-weight GEMM still wins. It preserves the product’s stored-byte constraint because the expansion exists only for one invocation.

So, plainly: the present in-GEMM decoder is a mid-band implementation, not a universal native-scale strategy. The 12.9% regression is worth optimizing there, but decode and prefill should not wait for that optimization—they want different kernels and different amortization boundaries.
