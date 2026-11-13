# Resume brief: Task: tune `vecdot_rows_kernel` in `/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp`. It has never been timed. You have a local RTX 5090 (sm_120, nvcc 12.8, DRAM peak 1.792 TB/s). Work in /root/marlin_ppu/quactlize.

CONTEXT — what this kernel is for. It is the native-GGUF decode GEMV: M=1 activation vector in fp16/fp32, weight stays in raw k-quant blocks, scale decoded in registers, nothing materialised. It is the FULLY_QUANTIZED x GEMV route in schemes.py. Do NOT confuse it with quactlize/include/gemv_lowbit/ — that one is validated and already tuned, but it consumes PRE-MATERIALISED fp16 scale/zero planes (SCALE_FIRST), so it does not cover this band. Both must continue to exist.

CURRENT SHAPE, and the strong prior on what is wrong with it:
    int const r = blockIdx.x * blockDim.x + threadIdx.x;   // one OUTPUT ROW per thread
    for (int b = 0; b < blocks_per_row; ++b)
        acc += vecdot_block<T>(blocks + (r*blocks_per_row + b)*block_bytes, x + b*kQK);
One thread owns a whole row, so 32 lanes read addresses `blocks_per_row*block_bytes` apart — 1152 B for Q4_K at 8 superblocks. Every load instruction touches 32 separate 32-byte sectors for a handful of useful bytes. This is the SAME pathology already measured and fixed on the STORE side of `dequantize_kernel_warp` in the same header (6.25% sector utilisation, exactly 16x worse; the fix took it 779.4 -> 58.4 us, 13.4x, 82.2% of peak). Read that kernel's comment block before you start — it is the worked example. The obvious direction is a warp (or a few lanes) cooperating on one row with lanes striding the k axis so consecutive lanes touch consecutive bytes, then a warp reduction; but MEASURE, do not assume, and consider rows-per-warp variants since a whole warp on one row may under-use it at small blocks_per_row.

HARD CONSTRAINTS:
1. **dp4a is forbidden.** Explicit standing instruction from the user, not negotiable. It would also quantise the activation, and this path serves decode where there is no second chance at the error. Weights dequantised into registers, fp16/fp32 activation, fma — the TRT-LLM weight-only shape. `vecdot_block` is already that shape.
2. All five k-quants must stay correct: Q2_K, Q3_K, Q4_K, Q5_K, Q6_K. The reference is the CPU `vecdot_block<T>` in the same header, itself checked against the official gguf package in tests/test_gguf_golden.py (test_vecdot_matches_llama_cpp, ~line 429). Any reassociation of the sum needs a summation-order tolerance, and say so explicitly rather than widening a tolerance silently.
3. Must remain reachable from Python through the existing op `quactlize::gguf_vecdot` (quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp:169). Note that op's CPU arm is a REFERENCE, not a fallback — it refuses above kCpuReferenceRowLimit.
4. Keep it portable: it compiles under both nvcc and hgcc (PPU). No sm_90+ intrinsics, no cp.async.bulk, no NVIDIA-only builtins outside a guarded branch — ci/local_gates.py has a portability check that will catch you.

MEASUREMENT TRAPS ALREADY PAID FOR IN THIS REPO — do not re-pay them:
- Time the KERNEL, not the bus. The first harness here wrapped cudaMalloc and 350 MB of transfers inside the timed region and reported 0.95x. Use cuda events around the launch only, plus an explicit L2 flush between iterations.
- A reported bandwidth ABOVE DRAM peak is evidence the measurement leaks, not evidence of speed. A previous cooperative-prepass number came back 2.138 TB/s on a 1.792 TB/s part — dirty writeback landing in the untimed flush. If you compute a number above peak, find the leak.
- Coalescing without partitioning is worth nothing: the first warp dequantiser had every lane run the whole traversal and keep its 32nd share. Stores coalesced, loads and arithmetic replicated 32x, 1.2x instead of 13.4x. Make sure the WORK is partitioned, not just the writes.
- Report cold AND warm (L2-resident) timings. The old one-thread-per-block dequantiser was never DRAM-bound — warming its data moved it 2.3% — while the fixed one went 61.4 us cold to 25.5 us warm. That gap is how you tell which roof you are under.

A PRIOR WORTH TESTING RATHER THAN ASSUMING: on PPU, an already-decoded low-bit GEMV measured ALU-BOUND, not bandwidth-bound (22.27 us cuda-core GEMV vs 20.74 us tensor-core GEMM; int1 and int4 took the SAME time while moving 4x different bytes — so per-element op count set the time, and split-K was therefore useless). The native GGUF path has MORE per-element work than that (6-bit packed scales, Q3_K's inverted hmask, Q5_K/Q6_K's high-bit planes), so the decode arithmetic may well be the ceiling here too rather than the loads. If it is, the lever is op count per element — e.g. hoisting the affine term to per-group instead of per-element — not more bandwidth. Establish which regime you are in FIRST (ncu, or the cold/warm gap), then optimise for that regime. Say which one you found.

DELIVERABLE, in this order:
1. A timing harness for vecdot_rows_kernel. tests/gguf_cuda_probe.cu is the existing local-5090 pattern — extend it or mirror it. NOTE: `*_cuda_probe.*` is deliberately excluded from the PPU build overlay in build.sh, because it is host-CUDA that hgcc cannot compile. Keep that property; do not let a new probe file leak into the overlay.
2. A BASELINE number for the current kernel before you change anything, for all five formats. This is the datum that does not exist today.
3. The regime finding (bandwidth-bound vs ALU-bound), with the evidence.
4. The tuned kernel, correctness re-checked against the CPU reference for all five, plus the speedup and the achieved fraction of the appropriate roof.

Report incrementally as you go — after the baseline, after the regime finding, after the tuned version — rather than one dump at the end. If something blocks you, say what and keep going on the rest. Do not ask me questions; make the call and state the assumption.

- **Thread ID:** `019fc54e-0540-7453-a2f4-a846690fcb3f`
- **Started / last event:** 2026-08-03 01:47 UTC → 2026-08-03 02:31 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T09-47-32-019fc54e-0540-7453-a2f4-a846690fcb3f.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "a3297b314627c936c9d8508534e33659c2ce315c", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-03_019fc54e_Task-tune-vecdot_rows_kernel-in-root-marlin_ppu-qu.md](../transcripts/2026-08/2026-08-03_019fc54e_Task-tune-vecdot_rows_kernel-in-root-marlin_ppu-qu.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Task: tune `vecdot_rows_kernel` in `/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp`. It has never been timed. You have a local RTX 5090 (sm_120, nvcc 12.8, DRAM peak 1.792 TB/s). Work in /root/marlin_ppu/quactlize.

CONTEXT — what this kernel is for. It is the native-GGUF decode GEMV: M=1 activation vector in fp16/fp32, weight stays in raw k-quant blocks, scale decoded in registers, nothing materialised. It is the FULLY_QUANTIZED x GEMV route in schemes.py. Do NOT confuse it with quactlize/include/gemv_lowbit/ — that one is validated and already tuned, but it consumes PRE-MATERIALISED fp16 scale/zero planes (SCALE_FIRST), so it does not cover this band. Both must continue to exist.

CURRENT SHAPE, and the strong prior on what is wrong with it:
    int const r = blockIdx.x * blockDim.x + threadIdx.x;   // one OUTPUT ROW per thread
    for (int b = 0; b < blocks_per_row; ++b)
        acc += vecdot_block<T>(blocks + (r*blocks_per_row + b)*block_bytes, x + b*kQK);
One thread owns a whole row, so 32 lanes read addresses `blocks_per_row*block_bytes` apart — 1152 B for Q4_K at 8 superblocks. Every load instruction touches 32 separate 32-byte sectors for a handful of useful bytes. This is the SAME pathology already measured and fixed on the STORE side of `dequantize_kernel_warp` in the same header (6.25% sector utilisation, exactly 16x worse; the fix took it 779.4 -> 58.4 us, 13.4x, 82.2% of peak). Read that kernel's comment block before you start — it is the worked example. The obvious direction is a warp (or a few lanes) cooperating on one row with lanes striding the k axis so consecutive lanes touch consecutive bytes, then a warp reduction; but MEASURE, do not assume, and consider rows-per-warp variants since a whole warp on one row may under-use it at small blocks_per_row.

HARD CONSTRAINTS:
1. **dp4a is forbidden.** Explicit standing instruction from the user, not negotiable. It would also quantise the activation, and this path serves decode where there is no second chance at the error. Weights dequantised into registers, fp16/fp32 activation, fma — the TRT-LLM weight-only shape. `vecdot_block` is already that shape.
2. All five k-quants must stay correct: Q2_K, Q3_K, Q4_K, Q5_K, Q6_K. The reference is the CPU `vecdot_block<T>` in the same header, itself checked against the official gguf package in tests/test_gguf_golden.py (test_vecdot_matches_llama_cpp, ~line 429). Any reassociation of the sum needs a summation-order tolerance, and say so explicitly rather than widening a tolerance silently.
3. Must remain reachable from Python through the existing op `quactlize::gguf_vecdot` (quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp:169). Note that op's CPU arm is a REFERENCE, not a fallback — it refuses above kCpuReferenceRowLimit.
4. Keep it portable: it compiles under both nvcc and hgcc (PPU). No sm_90+ intrinsics, no cp.async.bulk, no NVIDIA-only builtins outside a guarded branch — ci/local_gates.py has a portability check that will catch you.

MEASUREMENT TRAPS ALREADY PAID FOR IN THIS REPO — do not re-pay them:
- Time the KERNEL, not the bus. The first harness here wrapped cudaMalloc and 350 MB of transfers inside the timed region and reported 0.95x. Use cuda events around the launch only, plus an explicit L2 flush between iterations.
- A reported bandwidth ABOVE DRAM peak is evidence the measurement leaks, not evidence of speed. A previous cooperative-prepass number came back 2.138 TB/s on a 1.792 TB/s part — dirty writeback landing in the untimed flush. If you compute a number above peak, find the leak.
- Coalescing without partitioning is worth nothing: the first warp dequantiser had every lane run the whole traversal and keep its 32nd share. Stores coalesced, loads and arithmetic replicated 32x, 1.2x instead of 13.4x. Make sure the WORK is partitioned, not just the writes.
- Report cold AND warm (L2-resident) timings. The old one-thread-per-block dequantiser was never DRAM-bound — warming its data moved it 2.3% — while the fixed one went 61.4 us cold to 25.5 us warm. That gap is how you tell which roof you are under.

A PRIOR WORTH TESTING RATHER THAN ASSUMING: on PPU, an already-decoded low-bit GEMV measured ALU-BOUND, not bandwidth-bound (22.27 us cuda-core GEMV vs 20.74 us tensor-core GEMM; int1 and int4 took the SAME time while moving 4x different bytes — so per-element op count set the time, and split-K was therefore useless). The native GGUF path has MORE per-element work than that (6-bit packed scales, Q3_K's inverted hmask, Q5_K/Q6_K's high-bit planes), so the decode arithmetic may well be the ceiling here too rather than the loads. If it is, the lever is op count per element — e.g. hoisting the affine term to per-group instead of per-element — not more bandwidth. Establish which regime you are in FIRST (ncu, or the cold/warm gap), then optimise for that regime. Say which one you found.

DELIVERABLE, in this order:
1. A timing harness for vecdot_rows_kernel. tests/gguf_cuda_probe.cu is the existing local-5090 pattern — extend it or mirror it. NOTE: `*_cuda_probe.*` is deliberately excluded from the PPU build overlay in build.sh, because it is host-CUDA that hgcc cannot compile. Keep that property; do not let a new probe file leak into the overlay.
2. A BASELINE number for the current kernel before you change anything, for all five formats. This is the datum that does not exist today.
3. The regime finding (bandwidth-bound vs ALU-bound), with the evidence.
4. The tuned kernel, correctness re-checked against the CPU reference for all five, plus the speedup and the achieved fraction of the appropriate roof.

Report incrementally as you go — after the baseline, after the regime finding, after the tuned version — rather than one dump at the end. If something blocks you, say what and keep going on the rest. Do not ask me questions; make the call and state the assumption.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp` ×9
- `/root/marlin_ppu/quactlize/tests/gguf_cuda_probe.cu` ×5
- `/root/marlin_ppu/quactlize/tests/test_gguf_golden.py` ×5
- `/root/marlin_ppu/quactlize/build.sh` ×1
- `/root/marlin_ppu/quactlize/docs/HANDOFF_gguf_pipeline.md` ×1
- `/root/marlin_ppu/quactlize/quactlize/schemes.py` ×1

## Last assistant conclusions

### 2026-08-03 02:31 UTC

Implemented and tuned `vecdot_rows_kernel`.

| Format | Baseline cold/warm | Tuned cold/warm | Cold speedup | Useful BW | Warm-roof fraction |
|---|---:|---:|---:|---:|---:|
| Q2_K | 126.976 / 83.392 µs | 53.248 / 38.240 µs | 2.39× | 0.208 TB/s | 71.8% |
| Q3_K | 159.744 / 157.248 µs | 51.200 / 49.728 µs | 3.12× | 0.283 TB/s | 97.1% |
| Q4_K | 223.232 / 222.432 µs | 42.976 / 35.904 µs | 5.19× | 0.441 TB/s | 83.5% |
| Q5_K | 403.456 / 400.736 µs | 49.152 / 45.472 µs | 8.21× | 0.471 TB/s | 92.5% |
| Q6_K | 163.840 / 155.904 µs | 53.248 / 46.272 µs | 3.08× | 0.518 TB/s | 86.9% |

The kernel now uses two rows per warp for Q3/Q6 and four for Q2/Q4/Q5. Lane subgroups partition the k-axis without duplicated element work; subgroup leaders decode block multipliers and each scale pair once. `dp4a` is not used.

The cold/warm evidence identifies decode/instruction throughput as the main roof, with Q2/Q4 becoming mixed memory/compute cases after tuning. Useful bandwidth reaches 11.6–28.9% of DRAM peak and never exceeds it. Nsight counters were unavailable due `ERR_NVGPUCTRPERM`, so the regime finding uses the requested L2-residency gap.

Key changes:

- Tuned kernel and launch geometry: [gguf_vecdot.hpp](/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp:329)
- Launch-only cold/warm harness and rows-per-warp sweep: [gguf_cuda_probe.cu](/root/marlin_ppu/quactlize/tests/gguf_cuda_probe.cu:167)
- Five-format CPU-reference golden: [test_gguf_golden.py](/root/marlin_ppu/quactlize/tests/test_gguf_golden.py:425)
- Host-CUDA probes excluded from the PPU overlay: [build.sh](/root/marlin_ppu/quactlize/build.sh:52)
- Capability documentation updated: [schemes.py](/root/marlin_ppu/quactlize/quactlize/schemes.py:185)

Validation:

- All five CUDA kernels match the CPU `vecdot_block` reference; worst relative difference is `1.44e-7`.
- The explicit reassociation tolerance is `2e-6`.
- Selected kernels use 38–40 registers/thread with no local memory.
- `45/45` GGUF golden tests and `45/45` route/scheme tests pass.
- PPU portability and overlay gates pass; the probe does not leak into the hgcc overlay.
- A real hgcc binary was unavailable locally, so actual PPU compilation/performance remains unverified. The pre-existing `libquactlize_ppu.so` launcher/export is also still the remaining device-library wiring step; the Python op and its reference/device ABI remain intact.
