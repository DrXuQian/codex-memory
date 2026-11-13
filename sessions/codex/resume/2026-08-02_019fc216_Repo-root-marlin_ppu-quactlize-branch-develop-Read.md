# Resume brief: Repo /root/marlin_ppu/quactlize (branch develop). Read files. DO NOT EDIT ANY FILE.

acu is in, and it changes the picture twice. Attack both readings.

MEASURED (base = fp16-plane path, pack = native packed scale; identical grid (8,16,1)x(256,1,1), 131,072 mma both):

  time            base 20.05 us    packnop 21.57    pack 22.54
  regs            base 102         pack 98
  Shared Load     441,344 inst / 1,908,736 trans / 278,528 BC      IDENTICAL in base and pack (+0.00%)
  Shared Store    base 12,288 inst /  50,176 trans /  8,192 BC
                  pack 83,992 inst / 181,272 trans / 81,920 BC     -> +71,704 inst, +73,728 BC
  g2s Store       base 24,192 inst   pack 14,976                   -> pack does 9,216 FEWER
  tsm.ld          base 272,384       pack 276,992                  -> +4,608
  tsm.ld.swzl     168,960 both
  vmem.ld.tsm     base 18,432        pack 9,216                    -> pack halves it
  s.wait          base 253,312       pack 270,208
  Speed of Light  compute ~39.5%, memory ~31.7%, DRAM ~31.7%       neither saturated

The packnop-vs-pack capture separately showed EVERY memory counter identical (tsm.ld, tsm.ld.swzl, tsm.st,
smem.ld, vmem.acp.commit.grp all 0%), so the NOP ablation is structurally sound and pack-packnop really is the
decoder arithmetic.

TWO THINGS I WANT ARGUED, and I have probably got at least one wrong:

1. THE STORE CONFLICTS. +71,704 store instructions produce +73,728 conflicts -- ratio 1.03, i.e. essentially every
   added store conflicts, and transactions per added store are 131,096/71,704 = 1.83. My reading: the decoder forms
   half2(d*sc, -dmin*mn) in ONE register (gguf_packed_scale.h:270) then SPLITS it with lo_h2/hi_h2 and stores the
   halves as two separate 16-bit values into two separate planes (ppu_mma...hpp:1503-1504). 32 lanes x 2 bytes land
   on 16 four-byte banks -> structural 2-way conflict on every store. Proposed fix: store y2 as ONE 32-bit value
   into a single interleaved half2 plane -- halves the store count and makes it conflict-free by construction, and
   removes the zero tile (elements_per_smem_zero() currently ignores kPackedScaleOn, so shared is 57,344 -> 61,440).
   Is that reading right? Is the fix right? What breaks on the READ side, and how big is that change really?

2. THE LOAD CONFLICTS ARE BIGGER AND I ALMOST MISSED THEM. Shared Load BC = 278,528, IDENTICAL in both variants, so
   it is not a native-format problem at all -- it is in the baseline. Shared Load = tsm.ld (272,384) + tsm.ld.swzl
   (168,960). swzl is hardware-interleaved and should be conflict-free, so if it is ~1 transaction/instruction the
   plain tsm.ld carries 1,739,776 transactions over 272,384 instructions = 6.39 transactions per instruction and
   1.02 conflicts per instruction. That is 3.8x LARGER than the store conflicts we were about to optimise, and it is
   in BOTH paths.
   - Is that decomposition sound, or am I mis-attributing swzl's transactions?
   - What are those plain tsm.ld actually reading? I believe it is the mainloop reading sS and sZ per (n, group).
   - There is recorded history: an l98 analysis found the scale read has 4-way bank conflicts, and the
     PPU_SCALE_SWIZZLE fix measured +7.0% WORSE (CI 1.053..1.087). Why would a swizzle that provably removes the
     conflicts make it slower? That is the part I cannot explain.
   - Does the same half2-interleaved-plane change fix the LOAD side too -- one 32-bit read instead of two 16-bit
     reads from two planes? If so the fix is worth ~4x more than I said.

3. And a reframing my user gave me that I think is right: comparing pack against base is comparing against a kernel
   whose input CANNOT LEGALLY EXIST -- the fp16 planes cost +11.1% stored bytes and the product constraint forbids
   that. The legal comparison is (dequant-scale prepass + base) vs pack alone. Prepass moves 6.29 MB (read 2.10
   native + write 4.19 fp16); base itself achieves 1046 GB/s effective. So prepass+base is 22.3 us at DRAM peak and
   26.1 us at base's own rate, against pack's 22.54. Is that accounting right, and does it hold at other M?

Be specific, cite file:line, run things if useful. Say plainly where I am wrong.

- **Thread ID:** `019fc216-5f1a-7b62-852b-055234aaf6b1`
- **Started / last event:** 2026-08-02 10:47 UTC → 2026-08-02 11:05 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T18-47-53-019fc216-5f1a-7b62-852b-055234aaf6b1.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "553bf119f1744ed07022f038828e206df07dd901", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-02_019fc216_Repo-root-marlin_ppu-quactlize-branch-develop-Read.md](../transcripts/2026-08/2026-08-02_019fc216_Repo-root-marlin_ppu-quactlize-branch-develop-Read.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize (branch develop). Read files. DO NOT EDIT ANY FILE.

acu is in, and it changes the picture twice. Attack both readings.

MEASURED (base = fp16-plane path, pack = native packed scale; identical grid (8,16,1)x(256,1,1), 131,072 mma both):

  time            base 20.05 us    packnop 21.57    pack 22.54
  regs            base 102         pack 98
  Shared Load     441,344 inst / 1,908,736 trans / 278,528 BC      IDENTICAL in base and pack (+0.00%)
  Shared Store    base 12,288 inst /  50,176 trans /  8,192 BC
                  pack 83,992 inst / 181,272 trans / 81,920 BC     -> +71,704 inst, +73,728 BC
  g2s Store       base 24,192 inst   pack 14,976                   -> pack does 9,216 FEWER
  tsm.ld          base 272,384       pack 276,992                  -> +4,608
  tsm.ld.swzl     168,960 both
  vmem.ld.tsm     base 18,432        pack 9,216                    -> pack halves it
  s.wait          base 253,312       pack 270,208
  Speed of Light  compute ~39.5%, memory ~31.7%, DRAM ~31.7%       neither saturated

The packnop-vs-pack capture separately showed EVERY memory counter identical (tsm.ld, tsm.ld.swzl, tsm.st,
smem.ld, vmem.acp.commit.grp all 0%), so the NOP ablation is structurally sound and pack-packnop really is the
decoder arithmetic.

TWO THINGS I WANT ARGUED, and I have probably got at least one wrong:

1. THE STORE CONFLICTS. +71,704 store instructions produce +73,728 conflicts -- ratio 1.03, i.e. essentially every
   added store conflicts, and transactions per added store are 131,096/71,704 = 1.83. My reading: the decoder forms
   half2(d*sc, -dmin*mn) in ONE register (gguf_packed_scale.h:270) then SPLITS it with lo_h2/hi_h2 and stores the
   halves as two separate 16-bit values into two separate planes (ppu_mma...hpp:1503-1504). 32 lanes x 2 bytes land
   on 16 four-byte banks -> structural 2-way conflict on every store. Proposed fix: store y2 as ONE 32-bit value
   into a single interleaved half2 plane -- halves the store count and makes it conflict-free by construction, and
   removes the zero tile (elements_per_smem_zero() currently ignores kPackedScaleOn, so shared is 57,344 -> 61,440).
   Is that reading right? Is the fix right? What breaks on the READ side, and how big is that change really?

2. THE LOAD CONFLICTS ARE BIGGER AND I ALMOST MISSED THEM. Shared Load BC = 278,528, IDENTICAL in both variants, so
   it is not a native-format problem at all -- it is in the baseline. Shared Load = tsm.ld (272,384) + tsm.ld.swzl
   (168,960). swzl is hardware-interleaved and should be conflict-free, so if it is ~1 transaction/instruction the
   plain tsm.ld carries 1,739,776 transactions over 272,384 instructions = 6.39 transactions per instruction and
   1.02 conflicts per instruction. That is 3.8x LARGER than the store conflicts we were about to optimise, and it is
   in BOTH paths.
   - Is that decomposition sound, or am I mis-attributing swzl's transactions?
   - What are those plain tsm.ld actually reading? I believe it is the mainloop reading sS and sZ per (n, group).
   - There is recorded history: an l98 analysis found the scale read has 4-way bank conflicts, and the
     PPU_SCALE_SWIZZLE fix measured +7.0% WORSE (CI 1.053..1.087). Why would a swizzle that provably removes the
     conflicts make it slower? That is the part I cannot explain.
   - Does the same half2-interleaved-plane change fix the LOAD side too -- one 32-bit read instead of two 16-bit
     reads from two planes? If so the fix is worth ~4x more than I said.

3. And a reframing my user gave me that I think is right: comparing pack against base is comparing against a kernel
   whose input CANNOT LEGALLY EXIST -- the fp16 planes cost +11.1% stored bytes and the product constraint forbids
   that. The legal comparison is (dequant-scale prepass + base) vs pack alone. Prepass moves 6.29 MB (read 2.10
   native + write 4.19 fp16); base itself achieves 1046 GB/s effective. So prepass+base is 22.3 us at DRAM peak and
   26.1 us at base's own rate, against pack's 22.54. Is that accounting right, and does it hold at other M?

Be specific, cite file:line, run things if useful. Say plainly where I am wrong.

## Last assistant conclusions

### 2026-08-02 11:05 UTC

Plainly:

- Your store-conflict diagnosis is mostly right, but storing raw `y2` would be numerically wrong, and interleaving does not save shared-memory capacity.
- Your load-transaction decomposition is wrong because `tsm.ld.swzl` is intrinsically wide. The plain loads are indeed scale/zero loads, but a half2 plane does not remove their bank conflicts.
- The prepass byte accounting is right. The two timing estimates are scenarios, not reliable bounds, and they do not extrapolate directly across M.

## 1. Store conflicts

The structural diagnosis is correct. The packed decoder currently emits separate stores here:

- scale: [ppu_mma_aiu_multistage_mixed_input.hpp:1503](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1503)
- zero: [ppu_mma_aiu_multistage_mixed_input.hpp:1504](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1504)

For each decoder warp, 32 adjacent 16-bit stores occupy 16 four-byte banks. Stores cannot broadcast, so that is structurally conflicted. The exact expected decoder count is:

```text
4 decoder warps × 8 groups × 2 planes × 9 publications × 128 CTAs
= 73,728 conflicted store instructions
```

That exactly matching the +73,728 conflict counter is stronger evidence than the `73,728 / 71,704` ratio. The instruction delta is a net aggregate: the packed path also removes/skips other stores, notably the zero-plane clear at [line 1254](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1254). Therefore dividing conflict delta by net store-instruction delta is not a valid per-store ratio.

One correction: you cannot store raw `y2`. It initially holds `(d·sc, -dmin·mn)` at [gguf_packed_scale.h:266](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:266), but after splitting it the decoder changes zero to:

```text
zero = -dmin·mn + 8·scale
```

at [line 272](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:272), with `kPackedZMul = 8` at [mainloop line 1329](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1329). Storing raw `y2` would omit the converter-bias cancellation and produce wrong results. You must repack the final `sz.scale, sz.zero`, or reform the arithmetic so the final pair stays packed.

A final 32-bit `(scale,zero)` store is otherwise the right store-side design:

```text
73,728 decoder stores → 36,864
73,728 decoder conflict events → 0
```

Thirty-two consecutive 4-byte stores cover all 32 banks once. Use an explicitly 32-bit store and verify hgcc does not split it back into two half stores.

But it does not reduce shared-memory bytes. For this configuration:

```text
decoded scale + zero today: 4 KiB + 4 KiB = 8 KiB
combined half2 tile:                           8 KiB
raw packed staging:                           4 KiB
```

So the packed allocation remains 61,440 bytes. You can remove the member named `smem_zero`, but the combined tile must grow to 8 KiB. The current code indeed ignores `kPackedScaleOn` when sizing zero at [lines 535–542](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:535), while also allocating the raw staging buffer at [line 582](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:582). The comments claiming zero elements are stale relative to the implementation.

## 2. Load conflicts

Your attribution of `tsm.ld` to scale/zero is right. On this FINE ScaleZero configuration the hot path executes the two reloads at [lines 1905–1908](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1905). The count also reconciles:

```text
272,384 / 131,072 logical copy calls = 2.08 tsm.ld per copy call
```

The transaction decomposition is not right, however. A `tsm.ld.swzl` instruction writes four 32-bit registers per lane, as shown by the ISA wrapper at [copy_ppu0010_aiu.hpp:445](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/arch/copy_ppu0010_aiu.hpp:445). Its CUTE source layout is 128 bits per lane at [copy_traits_ppu0010_aiu.hpp:113](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/atom/copy_traits_ppu0010_aiu.hpp:113).

Thus one warp instruction moves:

```text
32 lanes × 16 bytes = 512 bytes
```

A conflict-free wide instruction is therefore not a one-transaction operation. In the profiler’s apparent 128-byte bank-service units, four transactions is the natural minimum.

Consequently:

```text
swzl minimum ≈ 168,960 × 4 = 675,840 transactions
plain maximum = 1,908,736 − 675,840 = 1,232,896
plain maximum / 272,384 = 4.53 transactions/instruction
```

So 6.39 cannot be obtained by assigning only one transaction to each swizzled load. A consistent decomposition is approximately:

```text
plain tsm.ld:       272,384 × 4    = 1,089,536
tsm.ld.swzl:        remaining        819,200
swzl transactions/instruction         4.85
```

The aggregate counters do not uniquely prove that split, but they rule out your split.

Likewise, `278,528 / 272,384 = 1.02` should not be interpreted as “one excess bank transaction per instruction” or necessarily as 2-way. The existing static probe shows the plain layout is 4-way on four banks. The conflict counter appears closer to “this instruction conflicted/replayed” than to a count of every excess bank word.

### Does half2 interleaving fix the reads?

No, not the bank conflict itself.

I ran the existing [l98 probe](/root/marlin_ppu/quactlize/dev/fold_derivation/l98_scale_swizzle.cu:58) unchanged, then ran an in-memory variant using a 32-bit slot and `Copy_Atom<DefaultCopy,uint32_t>`; no repository file was changed. At TN=128:

```text
current half plane:  plain 4-way on 4 banks
half2 word plane:    plain 4-way on 8 banks
```

The word layout uses twice as many banks, but still places four distinct words on each participating bank. The decoder store is conflict-free because decoder lanes own consecutive `n`. The MMA consumer has a different lane→`n` map with the concentrating 256-element thread stride, so the read remains 4-way.

Interleaving may nevertheless halve the logical load channel:

```text
two copies per group: scale + zero
one copy per group:   packed (scale,zero)
```

Best-case ISA effect:

```text
tsm.ld saved: about 272,384 / 2 = 136,192
tsm.st saved:                         36,864
ratio:                                  3.69×
```

So your “roughly 4× larger” intuition is reasonable as an instruction-count upper bound—but because two channels become one, not because the read becomes conflict-free. Conflict events would roughly halve, not fall to zero.

It is also not a two-line read-side change. Currently the collective constructs separate half fragments and copy views at [lines 1556–1601](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1556). Downstream arithmetic expects SoA registers:

```text
(scale_n, scale_n+...)
(zero_n,  zero_n+...)
```

A shared half2 tile delivers AoS registers:

```text
(scale_n, zero_n)
```

You either:

- expose even/odd halfword views and hope hgcc merges the adjacent loads, or
- issue an explicit 32-bit copy and deinterleave the registers yourself.

The second guarantees the shared-load reduction but may add register shuffles, interfere with existing half2 vectorization, and increase registers. It touches coarse reloads, FINE reloads, prefetch reloads, fragment setup, and both transform operands. This is a medium-sized collective-layout change, not merely replacing lines 1503–1504.

## Why the proven swizzle is slower

The l98 result proves a static address property: for its modeled instruction, the XOR layo
… [truncated 3762 chars]
