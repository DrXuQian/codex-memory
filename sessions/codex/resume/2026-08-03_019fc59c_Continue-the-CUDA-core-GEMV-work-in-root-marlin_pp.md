# Resume brief: Continue the CUDA-core GEMV work in /root/marlin_ppu/quactlize. Your whole-group rewrite is committed (f18ec9e) and I re-measured it independently — the numbers reproduce. This round has two targets, both diagnosed rather than guessed.

*** HEARTBEAT, mandatory. Also `tail` this file at start and after each build — I write into it too ***
    echo "[$(date +%H:%M:%S)] <what you just did>" >> /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Every meaningful step, at least every ~5 minutes, numbers in the lines.

*** FIRST, THE METRIC. Stop optimising % of peak; optimise ELEMENT RATE. ***
%peak = (elements/s) x (bytes/element), and only the first factor is under the kernel's control. Before your rewrite the element rate varied only 1.24x across formats, so %peak was almost pure byte density — that is why the old ordering was strictly by bit width. After the rewrite it varies 2.19x and now dominates:

  fmt   %peak  =  Gelem/s  x  B/elem  | groups  kernel        decode
  Q2_K  40.7%  =    2222   x  0.328   |   16    whole-group   2bit  1plane +min
  Q3_K  37.0%  =    1542   x  0.430   |   16    whole-group   2+1bit 2plane no-min
  Q4_K  38.1%  =    1214   x  0.562   |    8    SLICE         4bit  1plane +min
  Q5_K  39.0%  =    1016   x  0.688   |    8    SLICE         4+1bit 2plane +min
  Q6_K  56.6%  =    1237   x  0.820   |   16    whole-group   4+2bit 2plane no-min

Read that table properly: Q6_K's 56.6% is not the best kernel, it is the highest byte density (0.820) on a decent element rate. Q2_K at 2222 Gelem/s is by far the best kernel and looks worst on %peak only because its codes are 2 bits. Report Gelem/s alongside everything from now on.

*** TARGET 1: Q4_K and Q5_K are the two SLOWEST per element, and they are the two still on the slice kernel. ***
You measured whole-group regressing them 13.0% / 20.2% and reverted. That result is about ONE mapping, not about the idea, and the byte map says exactly why. With gs=32 and 8 groups against 8 lanes, lane L owns group L, and code_at_group<Q4_K> reads `qs[(g/2)*32 + j] >> (4*(g%2))`:

  lane 0 (g0): qs[0..31]  nibble 0
  lane 1 (g1): qs[0..31]  nibble 1     <- SAME 32 bytes as lane 0
  lane 2 (g2): qs[32..63] nibble 0
  lane 3 (g3): qs[32..63] nibble 1     <- SAME 32 bytes as lane 2
  ...
Eight lanes cover only four distinct 32-byte runs; every byte is fetched twice, once per nibble. That is the regression. Contrast gs=16, where lane 0 takes qs[0..15] and lane 1 takes qs[16..31] — distinct bytes.

THE FIX TO TRY: give each lane a PAIR of adjacent groups (2g, 2g+1) so it owns whole BYTES and uses both nibbles itself. Four lanes then cover the whole 128-byte plane with no duplication, or eight lanes each take a pair from a doubled row assignment — your call, but state the mapping and show the resulting per-lane byte map the way I did above. Q5_K is the same shape plus its qh plane (`(qh[j] >> g) & 1`), which is indexed by j alone and shared across g, so pairing does not disturb it.

If pairing still loses, say so with the byte map and the timing, and then the answer is that gs=32 genuinely wants slice ownership — but the current evidence does not show that, it shows one mapping that duplicates every load.

*** TARGET 2: code_at is the largest remaining term for every format. ***
Your own probe: 28.8 / 52.9 / 51.9 / 59.7 / 61.3% of runtime for Q2/Q3/Q4/Q5/Q6. The scale/min unpack is ~0 except Q5 (12.4%), and the reduction is handled. So per-element code extraction is the whole remaining budget.

Direction with precedent IN THIS PROJECT: the MMQ port found `__byte_perm` whole-word rearrangement essential for the IQ4 LUT. Extract FOUR codes from one 32-bit word instead of one shift+mask each. Under whole-group ownership a lane already walks a contiguous run in each plane, so it can load 32 bits at a time — that is the enabling change your rewrite just made. Q3_K/Q5_K/Q6_K additionally merge a high-bit plane, and they are the ones at 52-61%.

Note alignment: the runs are 16 or 32 bytes at plane-relative offsets, so a 32-bit load is aligned when the block base is. Check it rather than assume it, and keep a scalar fallback for any tail.

*** A NUMBER TO NOT CHASE — I retract it on your behalf ***
Your final report gave "per-element / hoisted affine = Q2 0.850/0.765", implying 15-23% available from reverting the affine hoist for Q2_K. It does NOT reproduce on the shipped kernel. I re-ran the A/B at rows=131072 on f18ec9e: Q2 120.83 vs 120.83 (0.0 ticks), Q3 174.08 vs 176.13 (1 tick, hoisted wins), Q4/Q5/Q6 identical. That 0.850 was measured on the pre-whole-group structure. There is nothing there; do not spend time on it.

*** INSTRUMENT DISCIPLINE, unchanged ***
rows=131072 (the 2.048 us event quantum is then <1%); cold cannot batch launches, warm can; NOP-style probes must keep every lane's value live (a `return v` lets the compiler delete 7/8 of the work and fake a win); report cold AND warm and the cold/warm ratio.

*** HARD CONSTRAINTS, unchanged ***
CUDA cores only — no tensor cores, no MMA. dp4a forbidden. All five k-quants correct against the CPU vecdot_block reference; vecdot_rows_kernel_serial retained. Compiles under nvcc AND hgcc — no NVIDIA-only intrinsic outside a guarded branch, and note __byte_perm is exactly the kind of thing to check for a PPU equivalent or guard. Reachable from Python via quactlize::gguf_vecdot.

DELIVERABLE: target 1 attempted with the byte map shown either way, target 2 taken as far as it goes, and a final table in Gelem/s and % of peak, cold and warm, for all five. Negative results are results — say what you tried and what it cost.

Do not ask me questions; make the call and state the assumption in the log.

- **Thread ID:** `019fc59c-5ba2-7871-a3a6-14964d5471db`
- **Started / last event:** 2026-08-03 03:13 UTC → 2026-08-03 04:49 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T11-13-06-019fc59c-5ba2-7871-a3a6-14964d5471db.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "f18ec9edf175cb4a725e43ca841fd7d4e26507ea", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-03_019fc59c_Continue-the-CUDA-core-GEMV-work-in-root-marlin_pp.md](../transcripts/2026-08/2026-08-03_019fc59c_Continue-the-CUDA-core-GEMV-work-in-root-marlin_pp.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Continue the CUDA-core GEMV work in /root/marlin_ppu/quactlize. Your whole-group rewrite is committed (f18ec9e) and I re-measured it independently — the numbers reproduce. This round has two targets, both diagnosed rather than guessed.

*** HEARTBEAT, mandatory. Also `tail` this file at start and after each build — I write into it too ***
    echo "[$(date +%H:%M:%S)] <what you just did>" >> /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Every meaningful step, at least every ~5 minutes, numbers in the lines.

*** FIRST, THE METRIC. Stop optimising % of peak; optimise ELEMENT RATE. ***
%peak = (elements/s) x (bytes/element), and only the first factor is under the kernel's control. Before your rewrite the element rate varied only 1.24x across formats, so %peak was almost pure byte density — that is why the old ordering was strictly by bit width. After the rewrite it varies 2.19x and now dominates:

  fmt   %peak  =  Gelem/s  x  B/elem  | groups  kernel        decode
  Q2_K  40.7%  =    2222   x  0.328   |   16    whole-group   2bit  1plane +min
  Q3_K  37.0%  =    1542   x  0.430   |   16    whole-group   2+1bit 2plane no-min
  Q4_K  38.1%  =    1214   x  0.562   |    8    SLICE         4bit  1plane +min
  Q5_K  39.0%  =    1016   x  0.688   |    8    SLICE         4+1bit 2plane +min
  Q6_K  56.6%  =    1237   x  0.820   |   16    whole-group   4+2bit 2plane no-min

Read that table properly: Q6_K's 56.6% is not the best kernel, it is the highest byte density (0.820) on a decent element rate. Q2_K at 2222 Gelem/s is by far the best kernel and looks worst on %peak only because its codes are 2 bits. Report Gelem/s alongside everything from now on.

*** TARGET 1: Q4_K and Q5_K are the two SLOWEST per element, and they are the two still on the slice kernel. ***
You measured whole-group regressing them 13.0% / 20.2% and reverted. That result is about ONE mapping, not about the idea, and the byte map says exactly why. With gs=32 and 8 groups against 8 lanes, lane L owns group L, and code_at_group<Q4_K> reads `qs[(g/2)*32 + j] >> (4*(g%2))`:

  lane 0 (g0): qs[0..31]  nibble 0
  lane 1 (g1): qs[0..31]  nibble 1     <- SAME 32 bytes as lane 0
  lane 2 (g2): qs[32..63] nibble 0
  lane 3 (g3): qs[32..63] nibble 1     <- SAME 32 bytes as lane 2
  ...
Eight lanes cover only four distinct 32-byte runs; every byte is fetched twice, once per nibble. That is the regression. Contrast gs=16, where lane 0 takes qs[0..15] and lane 1 takes qs[16..31] — distinct bytes.

THE FIX TO TRY: give each lane a PAIR of adjacent groups (2g, 2g+1) so it owns whole BYTES and uses both nibbles itself. Four lanes then cover the whole 128-byte plane with no duplication, or eight lanes each take a pair from a doubled row assignment — your call, but state the mapping and show the resulting per-lane byte map the way I did above. Q5_K is the same shape plus its qh plane (`(qh[j] >> g) & 1`), which is indexed by j alone and shared across g, so pairing does not disturb it.

If pairing still loses, say so with the byte map and the timing, and then the answer is that gs=32 genuinely wants slice ownership — but the current evidence does not show that, it shows one mapping that duplicates every load.

*** TARGET 2: code_at is the largest remaining term for every format. ***
Your own probe: 28.8 / 52.9 / 51.9 / 59.7 / 61.3% of runtime for Q2/Q3/Q4/Q5/Q6. The scale/min unpack is ~0 except Q5 (12.4%), and the reduction is handled. So per-element code extraction is the whole remaining budget.

Direction with precedent IN THIS PROJECT: the MMQ port found `__byte_perm` whole-word rearrangement essential for the IQ4 LUT. Extract FOUR codes from one 32-bit word instead of one shift+mask each. Under whole-group ownership a lane already walks a contiguous run in each plane, so it can load 32 bits at a time — that is the enabling change your rewrite just made. Q3_K/Q5_K/Q6_K additionally merge a high-bit plane, and they are the ones at 52-61%.

Note alignment: the runs are 16 or 32 bytes at plane-relative offsets, so a 32-bit load is aligned when the block base is. Check it rather than assume it, and keep a scalar fallback for any tail.

*** A NUMBER TO NOT CHASE — I retract it on your behalf ***
Your final report gave "per-element / hoisted affine = Q2 0.850/0.765", implying 15-23% available from reverting the affine hoist for Q2_K. It does NOT reproduce on the shipped kernel. I re-ran the A/B at rows=131072 on f18ec9e: Q2 120.83 vs 120.83 (0.0 ticks), Q3 174.08 vs 176.13 (1 tick, hoisted wins), Q4/Q5/Q6 identical. That 0.850 was measured on the pre-whole-group structure. There is nothing there; do not spend time on it.

*** INSTRUMENT DISCIPLINE, unchanged ***
rows=131072 (the 2.048 us event quantum is then <1%); cold cannot batch launches, warm can; NOP-style probes must keep every lane's value live (a `return v` lets the compiler delete 7/8 of the work and fake a win); report cold AND warm and the cold/warm ratio.

*** HARD CONSTRAINTS, unchanged ***
CUDA cores only — no tensor cores, no MMA. dp4a forbidden. All five k-quants correct against the CPU vecdot_block reference; vecdot_rows_kernel_serial retained. Compiles under nvcc AND hgcc — no NVIDIA-only intrinsic outside a guarded branch, and note __byte_perm is exactly the kind of thing to check for a PPU equivalent or guard. Reachable from Python via quactlize::gguf_vecdot.

DELIVERABLE: target 1 attempted with the byte map shown either way, target 2 taken as far as it goes, and a final table in Gelem/s and % of peak, cold and warm, for all five. Negative results are results — say what you tried and what it cost.

Do not ask me questions; make the call and state the assumption in the log.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp` ×25
- `/root/marlin_ppu/quactlize/docs/HANDOFF_gguf_pipeline.md` ×11
- `/root/marlin_ppu/quactlize/tests/test_gguf_golden.py` ×6
- `/root/marlin_ppu/quactlize/benchmarks/gemv_bench.py` ×4
- `/root/marlin_ppu/quactlize/third_party/actlize/examples/CMakeLists.txt` ×4
- `/root/marlin_ppu/quactlize/quactlize/schemes.py` ×3
- `/root/marlin_ppu/quactlize/tests/gguf_cuda_probe.cu` ×3
- `/root/marlin_ppu/quactlize/quactlize/routes.py` ×3
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp` ×2
- `/root/marlin_ppu/quactlize/ci/local_gates.py` ×2
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h` ×2
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp` ×2
- `/root/marlin_ppu/quactlize/tests/test_gguf_routes.py` ×2
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h` ×1
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.h` ×1
- `/root/marlin_ppu/quactlize/quactlize/__init__.py` ×1

## Last assistant conclusions

### 2026-08-03 04:49 UTC

Implemented and committed. Main commit: `9380148`; shared actlize converter: `0b10f9e5`. Worktrees are clean and synchronized.

### Target 1: Q4/Q5 paired ownership

The shipped mapping assigns adjacent groups to one owner lane:

| lane | groups | low-plane bytes | decoding |
|---:|---:|---|---|
| 0 | 0, 1 | `qs[0..31]` | low nibble → g0, high → g1 |
| 1 | 2, 3 | `qs[32..63]` | low nibble → g2, high → g3 |
| 2 | 4, 5 | `qs[64..95]` | low nibble → g4, high → g5 |
| 3 | 6, 7 | `qs[96..127]` | low nibble → g6, high → g7 |

Q5 loads each corresponding `qh` word once and selects both group bits. At rpw4, lanes 4–7 in the eight-lane row subgroup are inactive owners; the byte map remains unchanged.

Pairing alone moved Q4 from 221.184 to 190.464 µs, a 1.161× improvement. Q5 pairing alone was neutral/slightly worse, but pairing plus packed-word extraction was decisive: final cold times are 129.024 µs Q4 and 143.360 µs Q5.

### Target 2: packed extraction

[gguf_vecdot.hpp](/root/marlin_ppu/quactlize/quactlize/include/gguf_vecdot.hpp:390) now:

- Loads four adjacent packed bytes at once.
- Merges high planes while codes remain byte-packed.
- Uses CUTE field layouts with exact-plane-tiling assertions.
- Uses aligned `uint32_t` loads for Q2/Q4/Q5.
- Uses two aligned `uint16_t` loads on odd Q3/Q6 blocks, with byte fallback and an explicit scalar tail.
- Converts four bytes through shared actlize `MixGemmByte4ToHalf<Bias,Interleave>`.
- Accumulates products, group sums, row totals, and the final butterfly in fp16/half2.

The shared converter in [fast_numeric_conversion_for_mix_gemm.h](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:327) uses guarded CUDA `__byte_perm` and PPU `ppu.prmt.b32`. Exhaustive CUDA tests passed for every byte value, Bias 0/4/32, logical order, and historical GEMM interleave.

Final live-lane CODE_NOP cold shares are still 30.8/56.1/19.0/50.0/51.9% for Q2–Q6. That probe now removes the physical code-plane loads as well as extraction, so particularly for two-plane formats it includes irreducible weight traffic and is no longer an extraction-only ALU budget.

### Final rows=131072, bpr=8, 50 samples

| format | cold µs | cold Gelem/s | cold peak | warm µs | warm Gelem/s | warm peak | cold/warm |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q2_K | 79.872 | **3360.8** | 61.91% | 58.752 | **4569.0** | 84.16% | 1.359 |
| Q3_K | 116.736 | **2299.5** | 55.39% | 110.048 | **2439.3** | 58.76% | 1.061 |
| Q4_K | 129.024 | **2080.5** | 65.53% | 125.856 | **2132.9** | 67.18% | 1.025 |
| Q5_K | 143.360 | **1872.5** | 72.04% | 142.688 | **1881.3** | 72.38% | 1.005 |
| Q6_K | 161.792 | **1659.1** | 76.13% | 160.544 | **1672.0** | 76.72% | 1.008 |

Cold speedups over `f18ec9e`: 1.513×, 1.491×, 1.714×, 1.843×, and 1.342×.

Q3–Q6 exceed L2 at this shape, so near-one ratios mean both measurements are DRAM-fed. Q2’s smaller footprint can benefit from L2, hence its 84.16% effective warm result.

At rows=2048 the runtime dispatcher produces cold/warm Gelem/s of:

- Q2: 410 / 916
- Q3: 293 / 591
- Q4: 293 / 540
- Q5: 228 / 397
- Q6: 293 / 550

### Collective comparison

Grid supply explains most, but not all, of the former SIMT advantage. With equal MoE-sized work and 128 CTAs, Q4 SIMT at fixed rpw16 reaches 36.9% cold versus collective Memory 29.87% / Compute 38.99%. The saturated 65.5%-versus-29.9% comparison was substantially grid-confounded.

The collective’s 0.44 waves comes from its tile count: eight active experts × sixteen N tiles = 128 CTAs. Its four-block/CU capacity is shared-memory-limited at 57,344 bytes/CTA; registers admit that point. Smaller TileN can increase the grid, but the measured TN ladder found TN128—the fewest-CTA configuration—fastest.

Packed-word merge, the shared converter, CUTE plane descriptions, and the conditioned error metric transfer to the collective. Whole-group ownership does not: AIU requires a fixed interleaved register fragment and swizzled delivery order, so native GGUF input still needs an offline relayout or a measured gather/transpose.

### Validation

- 199 Python tests passed.
- All five CUDA formats pass the official fp64 oracle with conditioned error below `2^-11`; observed 1.05e-4–2.02e-4.
- `vecdot_rows_kernel_serial` retained.
- No dp4a, MMA, WMMA, or tensor-core operations in the GEMV.
- nvcc builds and all hgcc-shaped syntax checks pass.
- Actual hgcc is unavailable locally; the new PPU branch therefore still needs its runtime guard probe checked on `ppu001`.
- The Python fp16 ABI and dlopen seam are wired; the real `libquactlize_ppu.so` launcher remains the outstanding hardware integration.

The complete record is in [HANDOFF_gguf_pipeline.md](/root/marlin_ppu/quactlize/docs/HANDOFF_gguf_pipeline.md:139), and the reproducible command is [gemv_bench.py](/root/marlin_ppu/quactlize/benchmarks/gemv_bench.py:1).
