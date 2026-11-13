# Resume brief: DEBATE, ROUND 1. I will push back in round 2, so state positions you are willing to defend rather than hedged ones.
Read the code and the data. Do not summarise code back to me.

Repos: /root/marlin_ppu/Kernels (ppu_dev) and its third_party/actlize submodule (ppu-w4a16-dev). The full argument is
in general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md, last section.

FRESH DATA, one run, one binary set, six splitk binaries verified byte-distinct, one pinned row
(16x128:256 w16x16 s2, S=1, band L=64 top-k 8 N=K=2048 gs=32, batch-1 MoE decode on a 72-CU PPU):

  base       23.67 us   888.9 GB/s
  swz        25.33      830.5      PPU_SCALE_SWIZZLE=1
  bdqnop     21.05      999.2      PPU_B_DEQUANT_NOP=1
  pack       24.23      868.3      PPU_PACKED_SCALE=1
  packnop    24.78      848.9      PPU_PACKED_SCALE=1 PPU_PACKED_SCALE_NOP=1
  packsplit  26.92      781.4      PPU_PACKED_SCALE=1 PPU_PACKED_SPLIT_GROUPS=1

Correctness: test_q4k_packed_gemm passes five consecutive runs with PPU_PACKED_SCALE=1, and passes with
+PPU_PACKED_SPLIT_GROUPS=1 and with +PPU_SCALE_SWIZZLE=1. But test_moe_grouped_verify with PPU_SCALE_SWIZZLE=1 ALONE
dies with a device-side assert -- `Assertion 'false' failed`, block [0,10,7] thread [48,0,0], reported at line 104,
inside copy_B_and_extra_info.

MY FIVE CONCLUSIONS. Attack each; say which you would defend to the point of betting on it.

C1. The swizzle does not ship. It asserts on hardware in a configuration test_q4k_packed_gemm does not exercise, so a
    view of that buffer does not carry it or a copy contract breaks -- and both my enumeration and your own review
    concluded "every live address is swizzled", on the TN=128/Stages=2 shape only. It is also 7% slower where it runs.

C2. base - bdqnop = 2.62 us = 11.1% is the honest ceiling for every dequant idea including TODO #18. The 43%-of-
    dynamic-instructions figure is 11% of time, so those instructions do issue in memory's shadow.

C3. The placement hypothesis is dead. packsplit is 11% WORSE than pack with identical decode count, stores, bank
    conflicts and ownership, so the publication barrier's critical path is not what the packed path pays for -- and
    the persistent-kernel line, which rested on the same reasoning, goes with it.

C4. The packed decode's arithmetic costs nothing: packnop is SLOWER than pack. So whatever pack - base is, it is
    transport and stores, not the f16x2 arithmetic.

C5. base is 23.67 here against 20.11 in the earlier pinned acu run -- the same pinned configuration, 17% apart, wider
    than the ~13% spread on record. So cross-run comparison is void, and the native-format tax (+2.4% here, +12.9%
    there) is not determined at all.

Also answer, because I cannot: why would packnop be SLOWER than pack? It removes the per-group decode arithmetic and
keeps everything else. Give mechanisms, ranked, and say which are testable with what is already in the tree.

- **Thread ID:** `019fbaf7-f0be-7ae1-bca5-ea1f56b23e84`
- **Started / last event:** 2026-08-01 01:37 UTC → 2026-08-01 01:47 UTC
- **Working dir:** `/root/marlin_ppu/Kernels`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T09-37-19-019fbaf7-f0be-7ae1-bca5-ea1f56b23e84.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "79120d2e63d47e9cf024a3b8df3e492bad99c2ae", "branch": "ppu_dev", "repository_url": "git@github.com:DrXuQian/Kernels.git"}`

Full transcript: [2026-08-01_019fbaf7_DEBATE-ROUND-1-I-will-push-back-in-round-2-so-stat.md](../transcripts/2026-08/2026-08-01_019fbaf7_DEBATE-ROUND-1-I-will-push-back-in-round-2-so-stat.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

DEBATE, ROUND 1. I will push back in round 2, so state positions you are willing to defend rather than hedged ones.
Read the code and the data. Do not summarise code back to me.

Repos: /root/marlin_ppu/Kernels (ppu_dev) and its third_party/actlize submodule (ppu-w4a16-dev). The full argument is
in general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md, last section.

FRESH DATA, one run, one binary set, six splitk binaries verified byte-distinct, one pinned row
(16x128:256 w16x16 s2, S=1, band L=64 top-k 8 N=K=2048 gs=32, batch-1 MoE decode on a 72-CU PPU):

  base       23.67 us   888.9 GB/s
  swz        25.33      830.5      PPU_SCALE_SWIZZLE=1
  bdqnop     21.05      999.2      PPU_B_DEQUANT_NOP=1
  pack       24.23      868.3      PPU_PACKED_SCALE=1
  packnop    24.78      848.9      PPU_PACKED_SCALE=1 PPU_PACKED_SCALE_NOP=1
  packsplit  26.92      781.4      PPU_PACKED_SCALE=1 PPU_PACKED_SPLIT_GROUPS=1

Correctness: test_q4k_packed_gemm passes five consecutive runs with PPU_PACKED_SCALE=1, and passes with
+PPU_PACKED_SPLIT_GROUPS=1 and with +PPU_SCALE_SWIZZLE=1. But test_moe_grouped_verify with PPU_SCALE_SWIZZLE=1 ALONE
dies with a device-side assert -- `Assertion 'false' failed`, block [0,10,7] thread [48,0,0], reported at line 104,
inside copy_B_and_extra_info.

MY FIVE CONCLUSIONS. Attack each; say which you would defend to the point of betting on it.

C1. The swizzle does not ship. It asserts on hardware in a configuration test_q4k_packed_gemm does not exercise, so a
    view of that buffer does not carry it or a copy contract breaks -- and both my enumeration and your own review
    concluded "every live address is swizzled", on the TN=128/Stages=2 shape only. It is also 7% slower where it runs.

C2. base - bdqnop = 2.62 us = 11.1% is the honest ceiling for every dequant idea including TODO #18. The 43%-of-
    dynamic-instructions figure is 11% of time, so those instructions do issue in memory's shadow.

C3. The placement hypothesis is dead. packsplit is 11% WORSE than pack with identical decode count, stores, bank
    conflicts and ownership, so the publication barrier's critical path is not what the packed path pays for -- and
    the persistent-kernel line, which rested on the same reasoning, goes with it.

C4. The packed decode's arithmetic costs nothing: packnop is SLOWER than pack. So whatever pack - base is, it is
    transport and stores, not the f16x2 arithmetic.

C5. base is 23.67 here against 20.11 in the earlier pinned acu run -- the same pinned configuration, 17% apart, wider
    than the ~13% spread on record. So cross-run comparison is void, and the native-format tax (+2.4% here, +12.9%
    there) is not determined at all.

Also answer, because I cannot: why would packnop be SLOWER than pack? It removes the per-group decode arithmetic and
keeps everything else. Give mechanisms, ranked, and say which are testable with what is already in the tree.

## Last assistant conclusions

### 2026-08-01 01:47 UTC

I defend the no-ship decision for C1 and the cross-run objection in C5. I partially defend C2 as a row-local planning bound. I reject C3 and C4.

| Conclusion | Position I would bet on |
|---|---|
| C1 | Swizzle stays off. The asserted causal diagnosis is wrong. |
| C2 | TODO #18 gains less than ~11% on this row, probably low single digits. “Every dequant idea” is too broad. |
| C3 | This split implementation is dead. Placement and persistence are not. |
| C4 | Not established. The NOP is not a clean arithmetic-only ablation. |
| C5 | Cross-run magnitude is unusable. I would still bet the native path has a positive tax; its size is unknown. |

### C1

The swizzle does not ship, but not because of that assert.

The failing verifier uses `gs=128` by default and hardcodes `Stages=3` ([test_moe_grouped_verify.cu](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/test_moe_grouped_verify.cu:23)). The swizzle is enabled only when `Stages` is a power of two ([ppu_mma_aiu_multistage_mixed_input.hpp](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:477)). Therefore the alleged “swizzle-only” failing launch does not swizzle any address.

Its crash has a direct explanation: the coarse scale-copy path performs the copy and then reaches an unconditional `if constexpr(false) … else assert(false)` ([same header](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1661)). The default build of that same verifier should die identically. `run_batch.sh` never built that control.

So:

- I bet strongly against “a view lost the swizzle” as the explanation.
- The packed+swizzle rowC pass is actual correctness evidence for the s2/TN=128 swizzle.
- I still bet strongly on no-ship: it loses 7% on the exact target row and lacks useful coverage on other applicable s2 shapes.

### C2

`2.62 us` is a useful generous envelope for this row, not an honest universal ceiling.

The ablation removes all conversion, almost all affine applications, and likely most scale/zero fragment loads. The batch script itself correctly calls this out ([run_batch.sh](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/run_batch.sh:107)). It also adds a one-time fill of the MMA fragment and leaves one transformed element alive. Consequently, `base - bdqnop` is not the isolated cost of the 43% instruction population.

I would defend these stronger formulations:

- Completely deleting the current dequant/application machinery is worth about 11% on this row.
- TODO #18, which removes only part of that machinery, will be below 11%; I would bet on low single digits.
- A layout change or rewrite that also changes register thresholds, load count, or latency structure is not bounded rigorously by 11%.
- The qualitative conclusion is sound: much of the 43% instruction population is off the critical path or overlaps memory waiting.

I would not say “43% of instructions equals 11% of time.” Overlapped pipelines do not permit that additive attribution.

### C3

The result kills `PPU_PACKED_SPLIT_GROUPS` as an optimization. It does not kill placement.

The measured equation is effectively:

```text
packsplit - pack
  = duplicated 16-B unit reads
  + duplicated header/setup
  - benefit from halving the per-warp decode chain
  + scheduling interactions
  = +2.69 us
```

Identical decode count, stores, conflicts, and ownership do not remove the first two terms. Therefore the experiment shows only that the added costs exceed the placement benefit. It does not show that the benefit is zero.

The clean discriminator already composes from existing flags:

```text
packnop
splitnop = PACKED_SCALE + PACKED_SCALE_NOP + PACKED_SPLIT_GROUPS
```

Then `(splitnop - packnop)` prices the duplicated read/setup and altered store placement without decoder arithmetic. The difference-of-differences against `(packsplit - pack)` is the best existing estimate of the arithmetic-chain placement benefit.

The persistent-kernel inference is weaker still. Persistence targets CTA prologue/drain amortization and the 128-CTA/72-CU tail; packsplit changes an intra-tile publication slot. I would bet against retiring persistence from this datum.

### C4 and why `packnop` is slower

C4 is not supported.

The most important discovery is that these timing binaries do not use the real Q4_K fixture. The benchmark fills `hSc` entirely with `0.0625` ([test_moe_splitk_bench.cu](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/test_moe_splitk_bench.cu:84)) and passes that buffer unchanged. The packed kernel reinterprets it as 16-byte native units. The allocation size happens to match exactly, so this is memory-safe, but it is not native-format data.

Thus the measured original NOP reads `d=dmin=0.0625`, both normal. The real fixture’s 80.5% subnormal `d` is genuine, but it cannot explain this `packnop` result.

Worse, the full decoder consumes all four `u[]` words, while NOP consumes only `u[0]`. The compiler may eliminate or narrow the other shared loads. Therefore the statement “keeps everything else” is false independently of numerical values.

My ranking for the observed +0.55 us:

1. **Timing/order noise.** The difference is 2.3%, well inside the documented dispersion. Test with the saved binaries in repeated `pack,nop,nop,pack` order and paired medians.

2. **Different compiler schedule/code shape.** Removing the unrolled decoder changes register allocation, instruction alignment, DCE and scheduling. Byte-distinctness proves only that the macro affected the binary. Test both as one-launch acu captures: registers, spills/local traffic, dynamic shared-load count, opcode delta and stall mix.

3. **Tighter shared-store bursts.** Removing ALU spacing may cause four warps to hit the conflicted stores in a denser burst and alter barrier/shared-pipe behavior. Test acu shared-store utilization, conflicts, Memory Dependency and barrier stalls.

4. **Different downstream operands.** Full and NOP feed different values through every later transform and MMA. The current synthetic values appear finite and normal, so I rank this below noise/codegen, but it prevents a causal arithmetic decomposition.

5. **Clock/thermal ordering.** Low probability, testable by repeated ABBA ordering and acu cycle-versus-duration counters.

The clean input is easy to construct with machinery already present: choose `d=dmin=x`, every `sc=1`, and every `mn=7`. The full Q4 decode then produces:

```text
scale = x
zero  = 8x - 7x = x
```

The raw-head NOP also produces `(x,x)`. Give the baseline fp16 planes `(x,x)` as well. All three paths then feed bit-identical normal values downstream. Use `put_code` from the existing packed fixture builder, and force all four `u[]` words live through an asm sink so the NOP really retains the same 16-byte shared read.

The current uncommitted “normal-valued NOP” edit is not yet that test: the timing input was already normal, it still consumes only `u[0]`, and on real data its zero can be bit pattern `0x0001`, itself subnormal.

### C5

I defend the comparison ban, but the 17%-versus-13% argument is not the reason.

The historical `20.11 us` is acu kernel Duration. The fresh `23.67 us` comes from `time_it(go, 20)`, which measures host wall time for launches plus an amortized synchronization ([moe_splitk_bench_common.hpp](/root/marlin_ppu/Kernels/general/w4a16_gemm/cutlass_w4a16/moe_splitk_bench_common.hpp:140)). The repository already records roughly a 17% gap between those two measurement definitions. Same geometry is not the same metric.

Also, the observed 13% range is not a confidence interval.

So I would bet on:

- The `20.11` versus `23.67` comparison being void.
- Neither `+2.4%` nor `+12.9%` being the determined tax.
- The native path probably having a positive tax on this row—both observations point that way and explicit decode/stores are structurally additional—but its magnitude remains unreso
… [truncated 375 chars]
