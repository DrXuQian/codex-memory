# You are reviewing an ENGINEERING ARGUMENT, not just code. Be adversarial: your job is to find where the
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

- **Thread ID:** `019fb862-df2a-7922-aed0-e7da2d6ec5dd`
- **Started / last event:** 2026-07-31 13:35 UTC → 2026-07-31 13:43 UTC
- **Working dir:** `/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/07/31/rollout-2026-07-31T21-35-15-019fb862-df2a-7922-aed0-e7da2d6ec5dd.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "1d3d3dd5640856e1832e27ea784fad3fc11a481d", "branch": "ppu_dev", "repository_url": "git@github.com:DrXuQian/Kernels.git"}`

---

## User · 2026-07-31 13:35 UTC

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

## Assistant · 2026-07-31 13:35 UTC

I’ll trace the argument back to the cited counters, derivation, and synchronization points, then answer each question with explicit limits on what the existing measurements establish.

<details><summary>1 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"pwd && rg --files -g 'AGENTS.md' -g 'fold_derivation/PLAN_task20_scale.md' -g 'fold_derivation/HANDOFF_packed_scale.md' -g 'fold_derivation/README.md' -g 'ppu_mma_aiu_multistage_mixed_input.hpp' -g ' …`

</details>

## Assistant · 2026-07-31 13:35 UTC

The shell sandbox failed before running the read-only search (`bwrap` could not create its namespace). I’m retrying without login-shell setup; if the environment still blocks file access, I’ll distinguish the review I can make from the supplied evidence from claims that require inspecting the cited code.

<details><summary>6 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"pwd","workdir":"/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16","login":false,"yield_time_ms":10000,"max_output_tokens":2000}); text(r.output);`
- `exec: const hits = ALL_TOOLS.filter(x => /file|filesystem|read.*(text|file)|workspace|search.*file/i.test(x.name+" "+x.description)); text(hits);`
- `exec: text(ALL_TOOLS.map(x=>x.name).filter(n=>/^(?!mcp__codex_apps).*(file|read|workspace|shell|command|terminal|repo)/i.test(n)));`
- `exec: const r = await tools.web__run({search_query:[ {q:"\"PLAN_task20_scale.md\""}, {q:"\"HANDOFF_packed_scale.md\""}, {q:"\"ppu_mma_aiu_multistage_mixed_input.hpp\""}, {q:"\"gguf_packed_scale.h\""} ],response_length:"long"}); text(r);`
- `exec: text(ALL_TOOLS.map(x=>x.name).filter(n=>/github_(search|find|list.*repo|get.*repo)/i.test(n)));`
- `exec: for (const x of ALL_TOOLS.filter(x=>["mcp__codex_apps__github_search","mcp__codex_apps__github_search_installed_reposito_be740b6e4965","mcp__codex_apps__github_search_installed_repositories_v2","mcp__codex_apps__github_list_repositories"].i …`

</details>

## Assistant · 2026-07-31 13:39 UTC

The local sandbox remains inaccessible, so I’m checking whether the same repository is available through the configured GitHub connection. This is read-only and only to recover the cited source; I won’t treat a remote version as identical unless its revision can be matched.

<details><summary>5 tool call(s)</summary>

- `exec: const r = await tools.mcp__codex_apps__github_search({query:"ppu_mma_aiu_multistage_mixed_input.hpp",topn:20}); for (const c of (r.content||[])) if (c.type==="text") text(c.text);`
- `exec: const r = await tools.mcp__codex_apps__github_search({query:"HANDOFF_packed_scale",topn:20}); text(r.structuredContent ?? r);`
- `exec: const r = await tools.mcp__codex_apps__github_search({query:"ppu_mma_aiu_multistage_mixed_input.hpp",topn:20}); text(r.structuredContent ?? r);`
- `exec: const r = await tools.mcp__codex_apps__github_search_installed_reposito_be740b6e4965({query:"marlin",limit:50,option_enrich_code_search_index_availability:true}); text(r.structuredContent ?? r);`
- `exec: const vals = { dt_us:22.70-20.11, cycle_delta:38588-34191, time_pct:(22.70/20.11-1)*100, cycle_pct:(38588/34191-1)*100, inst_pct:699000/4400000*100, bytes_base_MB:21, bytes_packed_MB:21-2.1, bw_base_GBs:21e6/(20.11e-6)/1e9, bw_packed_GBs:18 …`

</details>

## Assistant · 2026-07-31 13:43 UTC

The regression is real; the causal story is not established. The data proves “this packed implementation is 12.9% slower for this configuration.” It does not prove “700K instructions caused 12.9% more time,” nor that dequantization explains the occupancy sweeps.

I could not inspect the requested local files: the read-only shell failed before executing because its `bwrap` namespace could not start, and the configured GitHub search found no copy of the repository. Therefore, code-specific points below rely on your description of the wait/decode/barrier placement. I cannot verify the two call sites, physical copy layout, or exact register experiment from this.

### Q1 — The 700K attribution is unsound

The arithmetic already warns against it:

- Time: 20.11 → 22.70 µs = **+12.88%**
- Cycles: 34,191 → 38,588 = **+12.86%**
- Instructions: approximately 4.4M → 5.1M = **+15.9%**

Instruction counters are not time counters. The added operations use different pipes and have different latency and throughput: half arithmetic, integer shifts, shared stores, scalar bookkeeping, and bank-conflict replays. Conversely, packed removes some cp.async work. Calling the net delta “decoder instructions” is reasonable; calling it the measured decoder cost is not.

The proposed distinction is also partly false: “issue-bound” and “on the critical path” are not alternatives. The decoder can be on the critical path, with its duration itself determined by issue throughput, dependency chains, shared-store bandwidth, or bank conflicts.

Placement between `cp_async_wait` and a CTA barrier establishes something important: the slowest decoding warp gates the CTA’s next phase. It prevents overlap with useful work by other warps in that CTA. It does not establish:

- How much decode overlapped with another resident CTA.
- Whether the decoder was limited by issue bandwidth or dependency latency.
- Whether the 1.83 shared transactions/store dominated.
- How much time was already saved by the reduced copy traffic.

The listed counters do not distinguish these cases. In particular, aggregate instruction totals and bank-conflict totals contain no temporal information.

The separating experiments are:

1. Add the same decoder instruction/store sequence to the baseline at the exact wait-to-barrier location while continuing to consume the predecoded planes.
2. Run the same synthetic work in an overlap-capable location—during the preceding stage or in producer warps while consumers execute MMA.
3. Timestamp, per stage, immediately before wait, after wait, after decode, after barrier, and after MMA.
4. Collect per-PC or phase-specific issue-active, eligible-warps, scoreboard/wait, barrier-stall, vector-pipe and shared-store-pipe utilization.

If the same work is expensive only in the wait-to-barrier slot, placement is causal. If it costs similarly wherever issued and saturates a pipe, issue throughput is causal. Both can be true.

“All warps wait for it” explains why the work is exposed inside the CTA. It does not explain the magnitude of 12.9%.

### Q2 — 38% of peak does not make traffic savings worthless

“Not at peak bandwidth” is not equivalent to “not bandwidth-bound.” A short, irregular, 128-CTA grouped workload may be limited by the bandwidth or memory-level parallelism attainable for that access pattern, even at 38% of the device’s streaming peak.

Conversely, if those loads are completely hidden behind a different bottleneck, saving them can indeed be worth nearly zero. The current evidence does not say which.

Some useful bounds:

- Baseline logical bandwidth: about **1.04 TB/s**.
- Packed logical bandwidth: about **0.83 TB/s** using 18.9 MB / 22.70 µs.
- At the baseline’s effective 1.04 TB/s, 2.1 MB corresponds to about **2.0 µs**.
- At 2766 GB/s, it corresponds to **0.76 µs**.
- Under a purely bandwidth-limited, constant-throughput model, removing 10% of bytes could reduce latency by about 10%.

Those are models, not measured savings. Under an additive illustration, the exposed decoder penalty could be roughly 2.6 µs if traffic saved nothing, or roughly 4.6 µs if it saved 2.0 µs before being outweighed. The real pipeline need not be additive.

More seriously, logical bytes are not physical HBM traffic. Halving payload does not necessarily halve DRAM sectors if alignment, cache-line granularity, or overfetch dominates. The reduced “cp.async shared-memory writes” counter does not prove a 2.1 MB HBM reduction.

Before implementing decode, the essential experiment was a marginal traffic-sensitivity test:

- Measure physical DRAM bytes/sectors and L2 hit/miss traffic.
- Benchmark the exact copy geometry without GEMM.
- Run baseline variants with scale traffic suppressed, duplicated, or padded while holding compute and synchronization constant.
- Plot time against actual scale bytes, not nominal total bytes.

If removing all 4.19 MB of scale-plane traffic barely moves time, a decoder cannot pay unless it is effectively free.

### Q3 — The sweeps reject occupancy; they do not identify dequantization

There is no unique “single mechanism” proven by the three sweeps.

They support this negative conclusion: **adding CTAs/warps does not cure the limiting resource in the tested range, and nominal HBM bandwidth saturation is unlikely.**

A fixed per-weight conversion/feeding bottleneck is consistent with all three:

- TileN does not reduce total weights converted.
- TileK does not reduce total weights converted.
- Split-K partitions the same weights and adds scheduling/reduction overhead.
- Extra occupancy therefore cannot reduce the invariant work.

But several other invariant resources are also consistent: instruction dispatch, vector integer/FP pipes, shared-memory load/store bandwidth, the AIU feed path, or a serialized stage barrier. Split-K also has its own reduction/epilogue costs, so its result is particularly weak evidence about dequantization.

The statement “1,898,496 instructions are 43% of the kernel” should be narrowed to **43% of dynamic instruction count**. It is not 43% of cycles. MMA, vector, scalar and shared-memory instructions are not interchangeable units.

The closed form also needs a useful-work qualification. With only one real M row, increasing WarpM may reduce conversion-per-counted-MMA by adding MMAs for padded rows. That lowers a ratio without reducing absolute conversion work or increasing useful GEMM work. The relevant denominator is useful output/MMA work, not all issued MMAs.

L2 reuse of B is not the leading explanation structurally: with one useful row and disjoint N/K partitions, each expert’s B tiles should largely be streamed once. But I cannot tell from the supplied counters whether the implementation duplicates, overfetches, or hits L2. The AIU path remains plausible unless its utilization/stalls were measured. Epilogue/reduction is especially plausible for the split-K degradation.

To identify dequantization causally:

- Replace dequant output with valid constants while preserving B traffic, MMA, and synchronization.
- Report instruction and pipe counters for every sweep row, not only HBM utilization.
- Measure AIU-feed, shared-memory, issue and barrier stalls.
- Benchmark split-K without final reduction/epilogue to quantify its added cost.
- Compare time against invariant dequant instruction counts across variants.

### Q4 — Keep the expanded format for this kernel, but do not call it “0% runtime”

For this exact workload, the defensible engineering decision is:

> Reject this native in-GEMM implementation and retain the pre-expanded scale planes.

A one-time device conversion is sensible for static weights reused over many tokens. But “11% more memory for 0% runtime” hides two costs:

- The conversion kernel has a one-time initialization cost that must be amortized.
- The 160-byte representation also reads 11.1% more weight data on every GEMM than the native 144-byte representation.

The measurement says that recurring extra traffic is still cheaper than this decoder. It does not make the traffic free. Model-capacity pressure, paging, cold-start cost, and number of generated tokens belong in the decision.

An in-GEMM version can pay only if:

\[
\text{exposed decode time} < \text{measured marginal time saved by fewer bytes}.
\]

Given that no K-tile reuse exists, it must reduce or hide the work rather than amortize it. Plausible designs are:

- Warp-specialized producer/consumer staging: decode stage \(s+1\) while consumer warps execute MMA for stage \(s\), using per-stage handoff rather than a full-CTA barrier.
- Fuse scale reconstruction into the existing int4 dequant path and never materialize two shared planes.
- Decode one group at a time into distributed registers with short live ranges and shuffles, rather than keeping the entire tile live. The failed +64-register version does not rule out this layout.
- Use conflict-free/interleaved scale-zero storage and 32-bit stores. The observed 1.83 transactions/store makes the current shared layout an explicit optimization target.
- Parallelize the serial per-column unpack across two threads per column or vectorize extraction.

The 148-byte intermediate is worth prototyping. Relative to 160 bytes it saves only **7.5%**, approximately **1.575 MB** here, not 2.1 MB. It removes bit extraction but retains int8-to-fp16 conversion, multiplication/FMA, synchronization, and likely explicit shared stores. A 20-byte metadata record can also straddle transaction boundaries, so its physical traffic must be measured; “148 logical bytes” is not enough.

### Q5 — Strongest missing experiment

The analysis never separately measured the two terms in its own trade:

1. Time saved by removing 2.1 MB.
2. Time added by decoding at that exact synchronization point.

The strongest missing experiment is therefore a matched ablation matrix:

| Variant | Traffic | Decode arithmetic | Shared stores | Placement |
|---|---:|---:|---:|---|
| Baseline | 4-byte/group | No | cp.async | Existing |
| Cost-only | Same as baseline | Yes | Yes | After wait |
| Transport-only | Native-sized | Minimal/constant | Yes | After wait |
| Arithmetic-only | Same traffic | Yes | No/checksum | After wait |
| Overlapped | Native-sized | Yes | Yes | Producer/previous stage |

For each, record physical DRAM sectors, L2 traffic, phase timestamps, issue utilization, eligible warps, barrier/scoreboard stalls, shared-store transactions, and AIU-feed utilization.

Other concrete omissions are:

- A conflict-free shared-store layout.
- A real 148-byte-format prototype.
- A producer/consumer decoder with no CTA-wide barrier.
- Randomized repeated A/B runs with variance and clock telemetry.
- Cold-cache versus warm-cache runs.
- Batch, K/N, top-k and number-of-active-expert sweeps.
- End-to-end load-time conversion amortization, including peak memory and paging behavior.

Until that ablation exists, the honest result is narrower: **the current packed decoder loses; the data does not yet say whether native metadata is fundamentally unsuitable for in-GEMM decoding.**
