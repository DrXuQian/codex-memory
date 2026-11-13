# Resume brief: You are reviewing an ENGINEERING ARGUMENT, not just code. Be adversarial: your job is to find where the
reasoning is wrong, where a number is attributed to the wrong cause, and what experiment was never run.
Say "I cannot tell from this" rather than inventing agreement.

CONTEXT. A CUTLASS-3 style mixed-input grouped GEMM (W4A16, MoE, batch-1 decode) on a non-NVIDIA
accelerator (PPU / T-Head ZW810, SM80-like, HBM peak ~2766 GB/s, 64 CUs, 256 KB shared memory per CU).
Weights are GGUF Q4_K: 4-bit codes plus, per 256-element superblock per column, a 16-byte unit holding
fp16 d, fp16 dmin and sixteen 6-bit codes (8 group scales + 8 group mins, gs=32).

THE CHANGE UNDER REVIEW. Previously an offline step pre-multiplied those codes into TWO fp16 planes
(scale and zero, 4 bytes per group per column) which cp.async streamed into shared memory. The change
streams the NATIVE 16-byte units instead (2 bytes per group per column, half the traffic) and decodes them
on-device into the same two fp16 shared planes, once per column per k-tile, by one thread per column.

MEASURED, same kernel both sides, same config pinned by grid/block fingerprint (8,16,1)x(256,1,1),
L=64 experts top-k 8, N=K=2048, gs=32, TileShape 16x128x256, warp 16x16, Stages=2:
  baseline (fp16 planes) 20.11 us, 34,191 cycles, 102 registers
  packed  (native units) 22.70 us, 38,588 cycles,  98 registers      -> +12.9%
Identical on both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960;
smem.ld 31,744; vmem.acp.commit.grp 19,456.
Deltas (packed minus base): v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944;
v.and.i +64,512; v.fma.f16 +36,864; tsm.st (shared store) +71,680 with +73,728 bank conflicts and 1.83
transactions per store instruction; shared LOAD +4,608; "shared store from global load" (i.e. cp.async's
own smem writes) -9,216 (-38%); scalar bookkeeping ~+150K. Total ~+699K instructions on a ~4.4M baseline.

QUESTIONS. Attack each.

Q1. Is "the decode costs ~+700K instructions and that is simply +12.9% of time" a sound reading? The kernel
    is at ~1.04 TB/s of a 2766 GB/s peak (38%) and ~14 warps/CU. If it is latency-bound rather than
    issue-bound, added instructions in a loader phase might have been HIDDEN and were not. What in the
    counters distinguishes "issue-bound" from "the decode sits on the critical path between a cp_async_wait
    and a __syncthreads and therefore cannot overlap"? Note the decode runs between cp_async_wait and
    __syncthreads, so ALL warps wait for it. Does that alone explain 12.9% better than instruction count
    does, and what measurement would separate them?

Q2. The claimed benefit was halved scale traffic. Scale+zero is 4.19 MB of ~21 MB total traffic; halving it
    saves 2.1 MB, ~10% of traffic, on a kernel at 38% of peak bandwidth. Was the benefit ever reachable at
    all, i.e. is saving traffic on a kernel that is not bandwidth-bound simply worth zero? If so, what
    should have been measured BEFORE building this?

Q3. Three separate sweeps say occupancy does not help: TileN 32/64/128 (512/256/128 CTAs) -- fewest blocks
    ties or wins; TileK 64/128/256 -- 128 loses by 6.5% and s4 beats s2 despite a larger pipeline-fill
    share; split-K S=1/2/4/8 -- monotonically worse past 28 warps/CU, 0.938x overall, with HBM utilisation
    stuck at 31-35% in EVERY row. What single mechanism is consistent with all three? Is
    "the int4->fp16 dequant pipeline is 1,898,496 instructions against 131,072 mma, i.e. 43% of the kernel,
    and by the closed form cvt-elements-per-mma = 128/WarpM it cannot be reduced by any of those knobs"
    the right conclusion, or is something else (L2 reuse of B, the AIU bulk-load path, epilogue) a better
    explanation? Note WarpM <= TileM and decode uses TileM=16 because only 1 row per expert is real.

Q4. Given Q1-Q3, is the honest conclusion "do this conversion ONCE in a separate load-time kernel and keep
    the GEMM untouched" -- trading 11% more weight bytes in device memory (160 vs 144 bytes per 256
    weights) for 0% runtime -- or is there a version of the in-GEMM decode that would actually pay? What
    would it have to look like? Consider: decode fewer times (the same column is decoded once per k-tile
    but the unit covers exactly one k-tile, so there is no reuse to exploit), decode into registers instead
    of shared memory (tried: +64 registers, refused), or an intermediate on-device format that is
    byte-aligned (int8 codes + fp16 d = 148 bytes per 256 weights, +2.8%) so the decode has no bit
    extraction at all.

Q5. What is the strongest thing you can say that this analysis has NOT considered? Name experiments, not
    adjectives.

READ THESE FILES for the full argument and the code:
  fold_derivation/PLAN_task20_scale.md          (last three sections)
  fold_derivation/HANDOFF_packed_scale.md       (sections 3, 4, 9, 10)
  ../../../third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp
      (packed_decode_stage, its two call sites in mma(), GmemTiledCopyScalePacked)
  ../../../third_party/actlize/include/cutlass/gguf_packed_scale.h
  fold_derivation/README.md                     (the converter-amortisation closed form)

- **Thread ID:** `019fb859-a205-7d62-9012-200941b6e323`
- **Started / last event:** 2026-07-31 13:25 UTC → 2026-07-31 13:34 UTC
- **Working dir:** `/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/07/31/rollout-2026-07-31T21-25-09-019fb859-a205-7d62-9012-200941b6e323.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "1d3d3dd5640856e1832e27ea784fad3fc11a481d", "branch": "ppu_dev", "repository_url": "git@github.com:DrXuQian/Kernels.git"}`

Full transcript: [2026-07-31_019fb859_You-are-reviewing-an-ENGINEERING-ARGUMENT-not-just.md](../transcripts/2026-07/2026-07-31_019fb859_You-are-reviewing-an-ENGINEERING-ARGUMENT-not-just.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

You are reviewing an ENGINEERING ARGUMENT, not just code. Be adversarial: your job is to find where the
reasoning is wrong, where a number is attributed to the wrong cause, and what experiment was never run.
Say "I cannot tell from this" rather than inventing agreement.

CONTEXT. A CUTLASS-3 style mixed-input grouped GEMM (W4A16, MoE, batch-1 decode) on a non-NVIDIA
accelerator (PPU / T-Head ZW810, SM80-like, HBM peak ~2766 GB/s, 64 CUs, 256 KB shared memory per CU).
Weights are GGUF Q4_K: 4-bit codes plus, per 256-element superblock per column, a 16-byte unit holding
fp16 d, fp16 dmin and sixteen 6-bit codes (8 group scales + 8 group mins, gs=32).

THE CHANGE UNDER REVIEW. Previously an offline step pre-multiplied those codes into TWO fp16 planes
(scale and zero, 4 bytes per group per column) which cp.async streamed into shared memory. The change
streams the NATIVE 16-byte units instead (2 bytes per group per column, half the traffic) and decodes them
on-device into the same two fp16 shared planes, once per column per k-tile, by one thread per column.

MEASURED, same kernel both sides, same config pinned by grid/block fingerprint (8,16,1)x(256,1,1),
L=64 experts top-k 8, N=K=2048, gs=32, TileShape 16x128x256, warp 16x16, Stages=2:
  baseline (fp16 planes) 20.11 us, 34,191 cycles, 102 registers
  packed  (native units) 22.70 us, 38,588 cycles,  98 registers      -> +12.9%
Identical on both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960;
smem.ld 31,744; vmem.acp.commit.grp 19,456.
Deltas (packed minus base): v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944;
v.and.i +64,512; v.fma.f16 +36,864; tsm.st (shared store) +71,680 with +73,728 bank conflicts and 1.83
transactions per store instruction; shared LOAD +4,608; "shared store from global load" (i.e. cp.async's
own smem writes) -9,216 (-38%); scalar bookkeeping ~+150K. Total ~+699K instructions on a ~4.4M baseline.

QUESTIONS. Attack each.

Q1. Is "the decode costs ~+700K instructions and that is simply +12.9% of time" a sound reading? The kernel
    is at ~1.04 TB/s of a 2766 GB/s peak (38%) and ~14 warps/CU. If it is latency-bound rather than
    issue-bound, added instructions in a loader phase might have been HIDDEN and were not. What in the
    counters distinguishes "issue-bound" from "the decode sits on the critical path between a cp_async_wait
    and a __syncthreads and therefore cannot overlap"? Note the decode runs between cp_async_wait and
    __syncthreads, so ALL warps wait for it. Does that alone explain 12.9% better than instruction count
    does, and what measurement would separate them?

Q2. The claimed benefit was halved scale traffic. Scale+zero is 4.19 MB of ~21 MB total traffic; halving it
    saves 2.1 MB, ~10% of traffic, on a kernel at 38% of peak bandwidth. Was the benefit ever reachable at
    all, i.e. is saving traffic on a kernel that is not bandwidth-bound simply worth zero? If so, what
    should have been measured BEFORE building this?

Q3. Three separate sweeps say occupancy does not help: TileN 32/64/128 (512/256/128 CTAs) -- fewest blocks
    ties or wins; TileK 64/128/256 -- 128 loses by 6.5% and s4 beats s2 despite a larger pipeline-fill
    share; split-K S=1/2/4/8 -- monotonically worse past 28 warps/CU, 0.938x overall, with HBM utilisation
    stuck at 31-35% in EVERY row. What single mechanism is consistent with all three? Is
    "the int4->fp16 dequant pipeline is 1,898,496 instructions against 131,072 mma, i.e. 43% of the kernel,
    and by the closed form cvt-elements-per-mma = 128/WarpM it cannot be reduced by any of those knobs"
    the right conclusion, or is something else (L2 reuse of B, the AIU bulk-load path, epilogue) a better
    explanation? Note WarpM <= TileM and decode uses TileM=16 because only 1 row per expert is real.

Q4. Given Q1-Q3, is the honest conclusion "do this conversion ONCE in a separate load-time kernel and keep
    the GEMM untouched" -- trading 11% more weight bytes in device memory (160 vs 144 bytes per 256
    weights) for 0% runtime -- or is there a version of the in-GEMM decode that would actually pay? What
    would it have to look like? Consider: decode fewer times (the same column is decoded once per k-tile
    but the unit covers exactly one k-tile, so there is no reuse to exploit), decode into registers instead
    of shared memory (tried: +64 registers, refused), or an intermediate on-device format that is
    byte-aligned (int8 codes + fp16 d = 148 bytes per 256 weights, +2.8%) so the decode has no bit
    extraction at all.

Q5. What is the strongest thing you can say that this analysis has NOT considered? Name experiments, not
    adjectives.

READ THESE FILES for the full argument and the code:
  fold_derivation/PLAN_task20_scale.md          (last three sections)
  fold_derivation/HANDOFF_packed_scale.md       (sections 3, 4, 9, 10)
  ../../../third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp
      (packed_decode_stage, its two call sites in mma(), GmemTiledCopyScalePacked)
  ../../../third_party/actlize/include/cutlass/gguf_packed_scale.h
  fold_derivation/README.md                     (the converter-amortisation closed form)

## Last assistant conclusions

### 2026-07-31 13:34 UTC

Bottom line: the packed implementation is a demonstrated 2.59 μs regression. The stronger causal story is not demonstrated. The evidence supports “extra ALU and conflicted shared-store work is exposed in a synchronized main-loop phase,” but it does not establish that instruction count alone caused the 12.9%, nor that bandwidth savings were inherently worthless.

One limitation: the workspace reader failed with a namespace error, and these files are not publicly indexed. I therefore could not independently verify the source beyond the implementation facts in the prompt. Claims about exact call-site placement are conditional on your description.

## Q1 — “+700K instructions simply became +12.9% time”

No.

First, the numbers are not even proportional:

- Instructions: roughly \(1 + 699K/4.4M = 1.159\), or +15.9%.
- Cycles: \(38,588/34,191 = 1.1286\), or +12.9%.

If the counters are comparable dynamic counts, the packed kernel actually executes about 2.7% more counted instructions per cycle. That is inconsistent with a literal “instruction percentage equals time percentage” reading.

More importantly, “+700K” is the net instruction delta of the packed build, not a measured decoder duration. It combines decoding, explicit shared writes, bookkeeping, removed async copies, and possibly compiler scheduling changes.

The critical-path argument is stronger, but still incomplete. The baseline already has the synchronization. Inserting decode between `cp_async_wait` and `__syncthreads` delays the last arrivals at that existing barrier. That prevents within-CTA consumer work from overlapping the decode. It does not prevent:

- Other resident CTAs from issuing.
- Independent hardware pipelines from overlapping.
- Outstanding copies for later stages from making progress, depending on wait semantics.
- Some decoder latency from being hidden by scheduling among its active warps.

Thus the barrier explains why decoder time is likely exposed; it does not explain why it is exactly 4,397 cycles. The instructions, shared conflicts, and placement are parts of the same mechanism, not competing explanations.

A useful decomposition is:

\[
\Delta T =
T_{\text{decode exposed}}
+ \Delta T_{\text{shared stores}}
+ \Delta T_{\text{scheduling}}
- T_{\text{saved memory, critical}}
\]

None of the supplied counters separates those terms.

What would separate issue saturation from synchronization exposure:

1. Record issued slots per cycle, eligible/runnable warps, and no-eligible-warp cycles, plus stall attribution for barrier, async wait, dependency, execution-pipeline throttle, and shared-store replay/conflicts.

2. Timestamp phase boundaries in-kernel: before/after async wait, decoder, barrier, and MMA. Subtract an instrumented baseline control.

3. Insert a calibrated synthetic copy of the decoder instruction stream:

   - In the current wait-to-barrier slot.
   - In a phase overlapping an outstanding copy.
   - In a noncritical epilogue or prologue slot.

   If location radically changes the cycle slope, placement is decisive. If cycles rise similarly and issue utilization is saturated everywhere, global issue pressure is decisive.

4. Run “baseline planes + dummy decoder writing volatile shared scratch.” That measures the decoder/store penalty without receiving the packed traffic benefit.

The 1.83 transactions per store and +73,728 conflict events make shared-store serialization a serious suspect, but conflict events are not cycle attribution. I cannot tell from those counters how much of the 4,397 cycles they caused.

## Q2 — Was halving traffic ever valuable?

Potentially—but 38% of theoretical HBM peak does not answer this.

“Not at peak bandwidth” is not equivalent to “memory is off the critical path.” A workload can be limited by memory latency, request granularity, insufficient outstanding requests, partition imbalance, L2 bandwidth, or the async/bulk-load path while reporting a modest fraction of theoretical HBM bandwidth.

Also, 21 MB / 20.11 μs = 1.04 TB/s is logical bandwidth unless an HBM read-byte counter confirms it. Repeatedly benchmarking the same eight experts may serve much of B from L2. In that case comparison to 2,766 GB/s is largely meaningless.

The bounds are informative but not predictive:

- Removing 2.1 MB from 21 MB reduces logical bytes by 10%.
- Under a purely byte-proportional model, the best possible runtime reduction is about 10%.
- At 1.04 TB/s, 2.1 MB corresponds to roughly 2.0 μs of serialized transfer.
- At peak HBM bandwidth it is about 0.76 μs.

Neither number is the expected gain because the scale requests may be cached or overlapped.

The benefit is approximately zero only if those scale requests are completely noncritical and do not contend for any relevant cache/copy/memory resource. That was never established.

The experiment to run before implementing decode was a traffic-removal oracle:

- Use a synthetic model with constant scales/zeros.
- Remove all scale-plane copies while preserving the rest of the GEMM.
- Then add unused but non-eliminable scale copies of 2, 4, and 8 bytes per group.
- Measure runtime, actual HBM bytes, L2 bytes/hit rate, memory stalls, and copy-path utilization.

Also sweep HBM clock at fixed core clock and core clock at fixed HBM clock. That gives much stronger causal evidence than percentage-of-peak.

## Q3 — What do the occupancy sweeps establish?

Only this: increasing parallelism through those particular, confounded transformations did not help.

They are not clean occupancy experiments:

- TileN changes CTA count, launch/wave overhead, epilogue count, and possibly copy transaction shape.
- TileK changes loop count, barriers, pipeline fill/drain, stage addressing, and compiler scheduling.
- Split-K adds reduction work, duplicate setup/epilogues, and shorter per-CTA K loops.

Split-K getting worse is therefore not surprising even if occupancy would otherwise help.

The common mechanism consistent with all three is broad: an invariant per-weight on-chip throughput bottleneck is already saturated, while extra CTAs add overhead. Dequant ALU issue fits that description—but so do the AIU/bulk-copy path, shared-memory throughput, or a warm-L2 service bottleneck.

The closed form \(128/\text{WarpM}\) can correctly show that these knobs do not reduce the algorithmic number of B conversions per MMA at fixed WarpM. It does not show that conversion consumes 43% of time.

The “43% of instructions” argument is weak because:

- MMA and integer/vector instructions do not have equal throughput or latency.
- They may use different pipelines and overlap.
- Predicate/lane counting may differ between counter classes.
- Shared-memory dependencies and barriers can dominate despite modest instruction counts.
- Increasing WarpM could improve the ratio merely by performing more useless MMA work on padded rows; that would not reduce absolute conversion work.

Stage 4 beating stage 2 despite more fill overhead is positive evidence that scheduling and overlap matter. That cuts against a purely instruction-count explanation.

Among the alternatives:

- L2 reuse is plausible across repeated launches, not naturally within one launch because B tiles partition the weights. Run cold-cache versus warm-cache and randomize selected experts.
- AIU/copy-path saturation is fully plausible and needs busy/queue-stall counters or an exact copy-only microbenchmark.
- Epilogue overhead can explain some TileN and split-K degradation, but not the TileK/stage behavior by itself.
- Dequant throughput is plausible, but needs a no-dequant oracle or pipeline utilization—not an instruction fraction.

To test occupancy itself, keep the same binary, tile shape, CTA count, and work while varying only residency, for example through unused shared-memory reservation or a hardware CTA-per-CU limit. Then inspect eligible warps and stall cycles.

## Q4 — What should ship?

For this exact batch-1 workload, the evidence supports converting once at load time and ret
… [truncated 4320 chars]
