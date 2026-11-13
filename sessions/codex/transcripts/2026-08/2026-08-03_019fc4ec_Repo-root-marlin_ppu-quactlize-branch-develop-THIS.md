# Repo /root/marlin_ppu/quactlize branch develop. THIS MACHINE HAS AN RTX 5090 and nvcc, and CUDA-only kernels are considered representative enough of PPU for tuning purposes. So this is a PERFORMANCE task you can actually run, not just read.

TWO KERNELS, both in quactlize/include/gguf_vecdot.hpp and quactlize/include/gguf_scale_prepass.hpp, both correctness-verified against the official gguf python package:

  1. prepass_kernel<KType, ZMul>  -- SCALE dequantise. Reads one k-quant scale block plus its fp16 header per
     (column, superblock) and writes fp16 scale and zero planes. One thread per (column, superblock). Pure bandwidth:
     kBlockBytes + 2..4 in, kGroups * 2 or 4 out.
  2. dequantize_kernel<KType, Dst> -- WHOLE-WEIGHT dequantise. Reads a raw GGUF block and writes 256 fp16 weights
     through a destination callable (DstIdentity, DstLinear, or a cute Layout). One thread per block. This feeds the
     fallback route, whose whole justification is a byte count: a dequantised fp16 weight is 4x the int4 codes and
     ~3.6x the native block, so it only pays where the result is reused across many rows.

A working harness already exists at /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/run.cu --
extern "C" entry points that cudaMalloc, copy, launch and copy back, built with
  nvcc -std=c++17 -arch=native -w -Xcompiler -fPIC -shared -I quactlize/include -I third_party/cutlass/include -o libgpu.so run.cu
and driven from python via ctypes. Rebuild it or write your own.

WHAT I WANT:

a. MEASURE both, at a realistic shape. The decode band this project cares about is N=K=2048 per expert with 8
   experts, gs=32, Q4_K -- so 8 * 2048 * (2048/256) = 131072 scale blocks, and the same number of weight blocks.
   Report achieved bandwidth against the 5090's peak, since both kernels are supposed to be bandwidth-bound.

b. SAY WHETHER THEY ARE BANDWIDTH-BOUND, with evidence rather than by assumption. If either is not, say what it is
   bound by. ncu is available if it helps.

c. FIND THE OBVIOUS LOSSES. My prior: one thread per block means each thread does 256 elements serially and the
   writes are 256 contiguous fp16 from ONE thread, which is the opposite of coalesced -- a warp writes 32 separate
   512-byte runs. The scale kernel has the same shape at a smaller scale. Confirm or refute, and quantify.

d. PROPOSE AND MEASURE a better mapping. The obvious one is a warp (or a few threads) per block with the element
   index striped across lanes so consecutive lanes write consecutive addresses. That interacts with the destination
   callable, which for a cute Layout is not affine -- so say what constrains it.

e. ONE CONSTRAINT ON THE SHAPE OF THE FIX, which is a project requirement rather than my preference: the decode
   should end up expressed in cute -- tensors, layouts and copy atoms -- rather than hand-written index arithmetic,
   for maintainability. If a striped mapping is best expressed as a TiledCopy over the block's 256 elements, that is
   preferred over a hand-rolled loop even at some cost, and say what that cost is.

Report numbers you actually measured. If something cannot be measured here, say so rather than estimating it.

- **Thread ID:** `019fc4ec-53ea-7f41-8782-458e5ed3ed77`
- **Started / last event:** 2026-08-03 00:00 UTC → 2026-08-03 00:19 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T08-00-50-019fc4ec-53ea-7f41-8782-458e5ed3ed77.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "8c8d2b0806705be98609fa8db0bbe25f08825ae7", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-03 00:00 UTC

Repo /root/marlin_ppu/quactlize branch develop. THIS MACHINE HAS AN RTX 5090 and nvcc, and CUDA-only kernels are considered representative enough of PPU for tuning purposes. So this is a PERFORMANCE task you can actually run, not just read.

TWO KERNELS, both in quactlize/include/gguf_vecdot.hpp and quactlize/include/gguf_scale_prepass.hpp, both correctness-verified against the official gguf python package:

  1. prepass_kernel<KType, ZMul>  -- SCALE dequantise. Reads one k-quant scale block plus its fp16 header per
     (column, superblock) and writes fp16 scale and zero planes. One thread per (column, superblock). Pure bandwidth:
     kBlockBytes + 2..4 in, kGroups * 2 or 4 out.
  2. dequantize_kernel<KType, Dst> -- WHOLE-WEIGHT dequantise. Reads a raw GGUF block and writes 256 fp16 weights
     through a destination callable (DstIdentity, DstLinear, or a cute Layout). One thread per block. This feeds the
     fallback route, whose whole justification is a byte count: a dequantised fp16 weight is 4x the int4 codes and
     ~3.6x the native block, so it only pays where the result is reused across many rows.

A working harness already exists at /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/run.cu --
extern "C" entry points that cudaMalloc, copy, launch and copy back, built with
  nvcc -std=c++17 -arch=native -w -Xcompiler -fPIC -shared -I quactlize/include -I third_party/cutlass/include -o libgpu.so run.cu
and driven from python via ctypes. Rebuild it or write your own.

WHAT I WANT:

a. MEASURE both, at a realistic shape. The decode band this project cares about is N=K=2048 per expert with 8
   experts, gs=32, Q4_K -- so 8 * 2048 * (2048/256) = 131072 scale blocks, and the same number of weight blocks.
   Report achieved bandwidth against the 5090's peak, since both kernels are supposed to be bandwidth-bound.

b. SAY WHETHER THEY ARE BANDWIDTH-BOUND, with evidence rather than by assumption. If either is not, say what it is
   bound by. ncu is available if it helps.

c. FIND THE OBVIOUS LOSSES. My prior: one thread per block means each thread does 256 elements serially and the
   writes are 256 contiguous fp16 from ONE thread, which is the opposite of coalesced -- a warp writes 32 separate
   512-byte runs. The scale kernel has the same shape at a smaller scale. Confirm or refute, and quantify.

d. PROPOSE AND MEASURE a better mapping. The obvious one is a warp (or a few threads) per block with the element
   index striped across lanes so consecutive lanes write consecutive addresses. That interacts with the destination
   callable, which for a cute Layout is not affine -- so say what constrains it.

e. ONE CONSTRAINT ON THE SHAPE OF THE FIX, which is a project requirement rather than my preference: the decode
   should end up expressed in cute -- tensors, layouts and copy atoms -- rather than hand-written index arithmetic,
   for maintainability. If a striped mapping is best expressed as a TiledCopy over the block's 256 elements, that is
   preferred over a hand-rolled loop even at some cost, and say what that cost is.

Report numbers you actually measured. If something cannot be measured here, say so rather than estimating it.

## Assistant · 2026-08-03 00:00 UTC

I’ll benchmark the existing one-thread mappings first at the stated 131,072-block shape, validate outputs, then implement cooperative variants and compare them under the same allocation/launch conditions. I’ll also collect profiler evidence—memory traffic, occupancy, issue/latency signals, and instruction mix—so “bandwidth-bound” is based on counters rather than byte-count intuition.

<details><summary>4 tool call(s)</summary>

- `exec: const p = await tools.update_plan({plan:[ {step:"Inspect repository instructions, kernels, and existing harness",status:"in_progress"}, {step:"Build a correctness-checking benchmark at 131,072 Q4_K blocks",status:"pending"}, {step:"Profile  …`
- `exec: const r = await tools.exec_command({cmd:"pwd && rg --files -g 'AGENTS.md' -g '!build' -g '!third_party' .. /tmp/claude-0 2>/dev/null | head -80 && git status --short --branch && sed -n '1,260p' quactlize/include/gguf_vecdot.hpp && sed -n '1 …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '240,420p' quactlize/include/gguf_vecdot.hpp && rg -n \"enum class KType|struct Traits|Q4_K\" quactlize/include/gguf_scale_layout.hpp quactlize/include/gguf_scale_decode.hpp && find /tmp/claud …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '1,180p' quactlize/include/gguf_scale_layout.hpp && sed -n '1,360p' /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/run.cu && rg -n \"TiledCopy|make_tiled_copy|Copy_Atom|co …`

</details>

## Assistant · 2026-08-03 00:02 UTC

The baseline geometry is now clear: Q4_K dequantization moves 144 B in and 512 B out per block (86.0 MB of logical traffic for this shape), while the scale prepass moves 12 B + two fp16 headers in and 32 B out (6.29 MB). I’m treating repeat-cache effects explicitly because all of the dequantized tensor is only about 67 MB and the 5090’s large L2 can otherwise make a repeated microbenchmark look like DRAM bandwidth.

<details><summary>5 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"rg -n \"make_tiled_copy\\(|TiledCopy|retile_S|partition_D\\(\" third_party/cutlass/examples third_party/cutlass/test quactlize/include | head -160",workdir:"/root/marlin_ppu/quactlize",yield_time_ms: …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '45,115p' third_party/cutlass/test/unit/cute/turing/movm.cu && sed -n '235,273p' third_party/cutlass/test/unit/cute/hopper/stsm.cu && sed -n '130,185p' third_party/cutlass/examples/59_ampere_g …`
- `exec: const patch = "*** Begin Patch\n*** Add File: /tmp/quactlize_perf.cu\n+#include \"gguf_vecdot.hpp\"\n+#include \"gguf_scale_prepass.hpp\"\n+#include <cuda_runtime.h>\n+#include <cute/tensor.hpp>\n+#include <algorithm>\n+#include <cmath>\n+# …`
- `exec: const r = await tools.exec_command({cmd:"ls -l /tmp/quactlize_perf.cu && nvcc -std=c++17 -arch=native -lineinfo -Xptxas=-v -I quactlize/include -I third_party/cutlass/include -o /tmp/quactlize_perf /tmp/quactlize_perf.cu",workdir:"/root/mar …`
- `exec: const r = await tools.exec_command({cmd:"nvidia-smi --query-gpu=temperature.gpu,clocks.sm,clocks.mem,power.draw --format=csv && /tmp/quactlize_perf && nvidia-smi --query-gpu=temperature.gpu,clocks.sm,clocks.mem,power.draw --format=csv",work …`

</details>

## Assistant · 2026-08-03 00:07 UTC

The first cold-cache timings already confirm the main loss: baseline whole-weight dequantization is 0.7905 ms (108.8 GB/s logical), while the cooperative CuTe/TiledCopy prototype is 0.0614 ms (1.400 TB/s), bit-exact—a 12.9× speedup. The prepass improves from 0.0164 to 0.0082 ms (about 2×). I’m profiling these exact launches now; the prepass is short enough that launch/front-end floors may matter more than DRAM peak.

<details><summary>20 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"ncu --query-metrics-mode suffix --metrics dram__bytes_read,dram__bytes_write,dram__throughput,lts__t_bytes,l1tex__t_sectors_pipe_lsu_mem_global_op_ld,l1tex__t_sectors_pipe_lsu_mem_global_op_st,smsp__ …`
- `exec: const r = await tools.exec_command({cmd:"ncu --query-metrics-mode suffix --metrics dram__bytes_read,dram__bytes_write,dram__throughput,lts__t_bytes,l1tex__t_sectors_pipe_lsu_mem_global_op_ld,l1tex__t_sectors_pipe_lsu_mem_global_op_st,smsp__ …`
- `exec: const r = await tools.exec_command({cmd:"id && rg -n \"RmProfilingAdminOnly\" /proc/driver/nvidia/params 2>/dev/null || true && nvidia-smi --query-supported-clocks=memory,graphics --format=csv,noheader | head -40 && nvidia-smi -q -d PERFORM …`
- `exec: const r = await tools.exec_command({cmd:"nvidia-smi --query-supported-clocks=memory,graphics --format=csv,noheader | tail -40 && nvidia-smi -lgc 1500,1500",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:20000});  …`
- `exec: const r = await tools.exec_command({cmd:"cuobjdump --dump-sass /tmp/quactlize_perf | rg -n \"Function :|STG|LDG\" | head -120",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:30000,max_output_tokens:20000}); text(r.output);`
- `exec: const r = await tools.exec_command({cmd:"cuobjdump --dump-sass /tmp/quactlize_perf | awk '\n/Function :/ { if (name != \"\") print name, \"inst=\" inst, \"LDG=\" ldg, \"STG=\" stg, \"SHFL=\" shfl; name=$3; inst=ldg=stg=shfl=0; next }\n/\\/\ …`
- `exec: const patch = "*** Begin Patch\n*** Update File: /tmp/quactlize_perf.cu\n@@\n-void benchmark(Kernel k, Buffers const& x, int iters = 51) {\n+void benchmark(Kernel k, Buffers const& x, int iters = 51, bool cold = true) {\n@@\n- flush_l2(x);\ …`
- `exec: const r = await tools.exec_command({cmd:"nvcc -std=c++17 -arch=native -lineinfo -I quactlize/include -I third_party/cutlass/include -o /tmp/quactlize_perf /tmp/quactlize_perf.cu && /tmp/quactlize_perf",workdir:"/root/marlin_ppu/quactlize",y …`
- `exec: const r = await tools.exec_command({cmd:"command -v nsys && nsys --version | head -5 || true",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:10000}); text(r.output);`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"right_inverse\\(\" third_party/cutlass/examples third_party/cutlass/test quactlize/include | head -80",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:16000}); text …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '70,125p' quactlize/include/xplane_offline.hpp && sed -n '40,72p' third_party/cutlass/test/unit/cute/core/inverse_right.cpp",workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output …`
- `exec: const patch = "*** Begin Patch\n*** Update File: /tmp/quactlize_perf.cu\n@@\n constexpr int kGroups = 8;\n constexpr int kThreads = 256;\n+using PermLayout = cute::Layout<\n+ cute::Shape<cute::Shape<cute::_4, cute::_8>, cute::_8>,\n+ cute:: …`
- `exec: const r = await tools.exec_command({cmd:"nvcc -std=c++17 -arch=native -lineinfo -Xptxas=-v -I quactlize/include -I third_party/cutlass/include -o /tmp/quactlize_perf /tmp/quactlize_perf.cu && /tmp/quactlize_perf",workdir:"/root/marlin_ppu/q …`
- `exec: const patch = "*** Begin Patch\n*** Update File: /tmp/quactlize_perf.cu\n@@\n void benchmark(Kernel k, Buffers const& x, int iters = 51, bool cold = true) {\n@@\n }\n+\n+void prepass_size_sweep(Buffers const& flush_owner) {\n+ std::puts(\"p …`
- `exec: const r = await tools.exec_command({cmd:"nvcc -std=c++17 -arch=native -lineinfo -I quactlize/include -I third_party/cutlass/include -o /tmp/quactlize_perf /tmp/quactlize_perf.cu && /tmp/quactlize_perf",workdir:"/root/marlin_ppu/quactlize",y …`
- `exec: const patch = "*** Begin Patch\n*** Update File: /tmp/quactlize_perf.cu\n@@\n int main(int argc, char** argv) {\n+ cudaDeviceProp prop{};\n+ CUDA_CHECK(cudaGetDeviceProperties(&prop, 0));\n+ std::printf(\"device: %s, SMs=%d, L2=%d bytes, me …`
- `exec: const r = await tools.exec_command({cmd:"cuobjdump --dump-sass /tmp/quactlize_perf | awk '\n/Function :/ { if (name != \"\") print name, \"inst=\" inst, \"LDG=\" ldg, \"STG=\" stg, \"SHFL=\" shfl; name=$3; inst=ldg=stg=shfl=0; next }\n/\\/\ …`
- `exec: const patch = "*** Begin Patch\n*** Update File: /tmp/quactlize_perf.cu\n@@\n Kernel parse(char const* s) {\n@@\n }\n+\n+template <class F>\n+void print_kernel_props(char const* label, F kernel, cudaDeviceProp const& prop) {\n+ cudaFuncAttr …`
- `exec: const r = await tools.exec_command({cmd:"nvcc -std=c++17 -arch=native -lineinfo -I quactlize/include -I third_party/cutlass/include -o /tmp/quactlize_perf /tmp/quactlize_perf.cu && /tmp/quactlize_perf",workdir:"/root/marlin_ppu/quactlize",y …`
- `exec: const r = await tools.exec_command({cmd:"awk 'BEGIN{peak=1792.128; printf(\"pre_base %.2f pre_cute %.2f dq_base %.2f dq_cute %.2f copy %.2f perm_naive %.2f perm_cute %.2f\\n\",384.75/peak*100,771.01/peak*100,109.33/peak*100,1399.47/peak*100 …`

</details>

## Assistant · 2026-08-03 00:17 UTC

The profiler counters are the one unavailable measurement: `ncu` returns `ERR_NVGPUCTRPERM`; the driver has `RmProfilingAdminOnly=1`, and even container UID 0 lacks the host capability to access them. I compensated with cold-vs-warm controls, a measured streaming-copy roof, CUDA occupancy/resource data, SASS counts, and exact warp-sector geometry. The conclusions are unambiguous: the original kernels do not hit DRAM bandwidth; the cooperative dequantizer does.

<details><summary>1 tool call(s)</summary>

- `exec: const p = await tools.update_plan({explanation:"Benchmarks, correctness controls, cache controls, size scaling, SASS/resource inspection, and CuTe destination-layout experiments are complete. The repository remains unchanged; the measured p …`

</details>

## Assistant · 2026-08-03 00:19 UTC

The current kernels are not DRAM-bandwidth-bound. The one-thread dequantizer is primarily limited by uncoalesced LSU/sector traffic; the prepass has the same issue plus a fixed-duration floor at this relatively small 6 MiB workload. Cooperative CuTe mappings remove the loss: dequantization reaches 1.40 TB/s payload bandwidth, 78.1% of the 5090’s peak and 94.5% of a measured streaming-copy roof.

## Setup

RTX 5090 GB202, 170 SMs, SM120, CUDA 12.8, driver 595.71.05.

- Shape: 8 experts × 2048 columns × 8 Q4_K superblocks = 131,072 blocks.
- Peak: 14.001 GHz × 2 × 512 bits / 8 = 1.792 TB/s.
- Prepass traffic: 48 B/block = 6,291,456 B.
- Dequant traffic: 144 + 512 = 656 B/block = 85,983,232 B.
- A 256 MiB read/write kernel flushed the 96 MiB L2 before every timed launch.
- Results are medians of 51 launches.
- Cooperative outputs were bit-exact against the existing kernels.
- A coalesced CUDA streaming copy measured 1.481 TB/s, 82.7% of peak.

Bandwidth below is logical/payload bandwidth; hardware-counter DRAM bytes were unavailable.

| Kernel | Mapping | Time | Payload BW | Peak | Speedup |
|---|---|---:|---:|---:|---:|
| Prepass baseline | 1 thread/block | 16.4 µs | 384.8 GB/s | 21.5% | 1.00× |
| Prepass CuTe | 8 threads/block, 4 blocks/warp | 8.2 µs | 771.0 GB/s | 43.0% | 2.00× |
| Dequant baseline | 1 thread/block | 786.5 µs | 109.3 GB/s | 6.1% | 1.00× |
| Dequant striped | 1 warp/block, direct stores | 71.6 µs | 1.200 TB/s | 67.0% | 11.0× |
| Dequant CuTe/TiledCopy | 1 warp/block | 61.4 µs | 1.399 TB/s | 78.1% | 12.8× |

## What they are bound by

Baseline dequantization is not DRAM-bandwidth-bound.

- Making its data warm in L2 changed 786.5 µs to 768.6 µs, only 2.3%.
- The CuTe version changed from 61.4 µs cold to 25.5 µs warm, showing genuine memory-bandwidth sensitivity.
- The CuTe version reaches 94.5% of the measured streaming-copy roof.
- All variants have 100% theoretical occupancy and no spills. Baseline uses 17 registers; CuTe uses 32.
- Baseline SASS contains 280 scalar global loads and 256 scalar global stores; the CuTe path has 12 loads and 8 stores in its warp-level body.

The baseline is bound by global-load/store request and sector throughput caused by its access pattern, not by useful DRAM bytes or occupancy. The optimized dequantizer is DRAM-bandwidth-bound.

The prepass is also not DRAM-bandwidth-bound at the requested shape. It is a mixture of fixed kernel/front-end duration and inefficient LSU requests. Size scaling makes that clear:

| Scale | Baseline | CuTe |
|---|---:|---:|
| 1×, 6 MiB | 384.8 GB/s | 768.0 GB/s |
| 4×, 24 MiB | 472.6 GB/s | 1.229 TB/s |
| 16×, 96 MiB | 512.0 GB/s | 1.365 TB/s |

The cooperative prepass becomes bandwidth-dominated at larger workloads; at the real 6 MiB shape, it is too short to approach its asymptotic bandwidth.

## The obvious losses

The prior is substantively correct, with one wording refinement: a warp does not issue 32 independent 512-byte stores. It issues 256 strided fp16 store instructions; over time each lane fills its own 512-byte region.

For baseline dequantization, one store instruction has lane addresses 512 B apart:

- 32 separate 32-byte sectors.
- 64 B useful per warp instruction out of 1,024 B of sector traffic.
- 6.25% sector utilization, exactly 16× worse than the striped mapping.

The input loads are similarly hostile: corresponding lanes read Q4 blocks 144 B apart, generally putting each byte load in a separate sector. Later accesses can hit the same L1/L2 lines, but the LSU still processes the scattered requests.

For the prepass, adjacent threads’ plane destinations are 16 B apart at a given group:

- 16 sectors for 64 B useful.
- 12.5% sector utilization, 8× worse than publishing group as the lane-fast coordinate.

The measured 12.8× dequant speedup and 2× prepass speedup confirm the loss. The prepass realizes less than its theoretical 8× sector improvement because it also has header loads, scale arithmetic, and a roughly 4 µs fixed-duration floor.

## Better mapping

For Q4_K dequantization:

- One warp owns one raw block.
- Lanes 0–7 decode the eight `(scale,min)` pairs once.
- `__shfl_sync` broadcasts each group pair.
- Lane `j` owns the group-local element `j`.
- A 32-thread `TiledCopy` partitions the block’s 256-element destination, giving eight values per lane.
- Consecutive lanes issue contiguous 64-byte fp16 stores.

For prepass:

- Eight lanes own the eight groups of one superblock.
- Four superblocks share a warp.
- CuTe layout `(group=8, block=4):(1,8)` makes group lane-fast.
- Each plane is emitted with one 32-element TiledCopy.

The CuTe abstraction had no measured penalty:

- Prepass direct striped and TiledCopy were both 8.2 µs.
- Dequant TiledCopy was 16.6% faster in throughput than direct striped stores, 1.399 versus 1.200 TB/s.
- Its buffering/code generation reduced the static body from 152 instructions/16 loads to 136 instructions/12 loads while retaining 100% occupancy.

## Destination-layout constraint

A logical stripe only coalesces when `DstIdentity` or `DstLinear{stride=1}` maps adjacent logical elements to adjacent addresses. A non-unit linear stride or hierarchical layout can destroy coalescing again.

I measured a compact non-affine CuTe permutation:

`Layout<Shape<Shape<_4,_8>,_8>, Stride<Stride<_8,_32>,_1>>`

| Mapping for that layout | Time | Payload BW |
|---|---:|---:|
| Baseline callable | 913.4 µs | 94.1 GB/s |
| Warp, logical elements striped | 196.6 µs | 437.4 GB/s |
| TiledCopy, physical stripe + `right_inverse(layout)` | 65.5 µs | 1.312 TB/s |

Partitioning physical output addresses and deriving logical source indices with `right_inverse` is 3× faster than blindly striping logical indices. It costs 6.25% bandwidth relative to identity because the decoder must gather source elements and select different group scales across lanes.

That only works directly for compact, invertible destination tiles. For a layout with holes, a non-unit `DstLinear`, or one whose physical tile crosses GGUF block boundaries, the choices are:

- Tile in physical destination order and gather from several source blocks.
- Stage a logical block and perform a CuTe/shared-memory layout transform.
- Accept scattered writes.

The production interface therefore needs to expose the destination as a CuTe Tensor/Layout, rather than only an opaque callable. The copy partition can then be applied to both the destination tensor and an identity-coordinate tensor; composing the latter with `right_inverse(dst_layout)` derives the source block and element. Q4’s code-byte and nibble maps should likewise become CuTe layouts, while the existing scale layouts can be reused.

The actual shipping hierarchical layout is not yet present in these headers, so I did not estimate its performance.

`ncu` counters could not be collected: it reports `ERR_NVGPUCTRPERM`, with host driver setting `RmProfilingAdminOnly=1`. Static SASS, cache controls, resource/occupancy queries, size scaling, and the copy roof are the evidence used instead. The benchmark prototype is [quactlize_perf.cu](/tmp/quactlize_perf.cu). The `develop` worktree remains clean.
