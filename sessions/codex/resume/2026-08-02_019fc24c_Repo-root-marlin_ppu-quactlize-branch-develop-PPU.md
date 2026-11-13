# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop. PPU cutlass3 mixed-input GEMM, Q4_K native packed scale. I want you to ATTACK this plan before I write code, and tell me what is impossible or already contradicted by the tree. Cite file:line.

BACKGROUND FACTS (established, do not re-derive):
- Load bank conflicts 278,528 are the FINE scale/zero reload, identical in base and pack because pack decodes INTO the same two fp16 planes and leaves the read side untouched (collective:574, PLAN_task20_scale.md:1094). Read map h(t) = 256*(t mod 4) + floor(t/4) + C -> 4 distinct words on each of 4 banks. Whole-channel value bounded at 0.8-2.3% (PLAN_task20_scale.md:1123).
- pack ADDS 73,728 store conflicts: `sS(n,G,stage)=sz.scale; sZ(n,G,stage)=sz.zero;` at collective:1500-1502, 32 lanes x 2 B covering 16 of 32 banks, stores cannot broadcast.
- PPU_SCALE_SWIZZLE (in-kernel XOR) removed ZERO conflicts and cost ~7%, with Inst Executed Pipe SALU +97% of peak. Being deleted.
- Waves Per CU = 0.44 (128 CTAs / (72 CU x 4 blocks/CU)); nothing is hidden, work is paid ~1:1 both directions.
- The repo's constraint: an OFFLINE reorder is allowed, an increase in STORED BYTES is not.

THE PLAN -- do it OFFLINE (host-side, byte-neutral) instead of with in-kernel address math. Two independent transforms:

T1. INTERLEAVE (scale, min) into one 32-bit element.
  - packed path: the decoder writes ONE 32-bit store instead of two 16-bit stores. 32 lanes x 4 adjacent bytes = 32 banks exactly once -> the +73,728 goes to ~0. Ownership-safe because a thread derives BOTH halves from its OWN column's unit -- unlike the column-pairing attempt that raced (collective:1400-1406).
  - base path: offline interleave the two gmem fp16 planes (ptr_S, ptr_Z) into one half2 plane -> ONE cp.async channel instead of two, one smem tile.
  - consumer reads one 32-bit word and splits into the existing tCrS/tCrZ half fragments, so bdq_transform is untouched.
  - shared bytes unchanged (4 KiB + 4 KiB = 8 KiB either way). Known trap: cannot store raw y2, because zero += 8*scale (kPackedZMul, collective:1329) is applied after the split.

T2. OFFLINE PERMUTATION sigma of the (n, group) scale tile to kill the LOAD conflicts.
  - cp.async copies a contiguous run, so permuting gmem permutes smem identically. Pre-permute offline so the 32 lanes of a warp land on 32 distinct banks. ZERO runtime address math, which is exactly what PPU_SCALE_SWIZZLE failed on.
  - Same technique the repo already uses for sub-byte B (pi = frag.layout()^-1).

ATTACK THESE SPECIFICALLY:
1. Is T2 even possible? sigma must simultaneously satisfy ALL 8 N-warps, all 8 groups, both stages, AND every reader: the FINE per-group reload (collective:1877-1878, 1907-1908), the coarse reload (1685-1689), the prefetch reload (1880-1881), and fragment setup. If two readers of the same element want it in different banks there is no sigma. Read the actual partitioning and say whether the readers share ONE thread->element map.
2. T1 and T2 INTERACT on the packed path. T1 fixes the stores by making them 32-bit and contiguous in n. T2 permutes n, which may scatter those stores and REINTRODUCE store conflicts. Can sigma be restricted to a form that preserves 32-contiguity of the store (e.g. permuting only whole 32-element runs, or only the group axis)? If sigma must touch n within a 32-run, T1 and T2 are incompatible and I need to pick one.
3. For the packed path the scale is DERIVED in-kernel from the 16-byte unit, so there is no offline scale array to permute -- sigma would have to be applied by the decoder's store index. Is that free (compile-time constant index) or does it become the same address arithmetic that sank the swizzle?
4. Does sigma bake TileN and the warp shape into the stored weight? The repo builds many tile shapes into one binary (collective:462-470 discusses exactly this for the swizzle) and quactlize/layouts.py requires parameters to appear in the layout NAME. Is a tile-shape-specific scale tensor acceptable, or does it break the multi-unit binary?
5. base has 8,192 Shared Store bank conflicts and base does NOT store scale from registers. What are they? Find them.
6. Given the 0.8-2.3% bound on the whole load channel, and that T1 halves the read INSTRUCTION count (~136,192 fewer tsm.ld), is T2 worth doing at all, or is T1 alone the whole realistic win? Give me a ranked recommendation with the numbers you can support.

Be concrete. If a step is impossible say so and say why, with the line that proves it.

- **Thread ID:** `019fc24c-d479-7ee1-a1dd-42e917412bc6`
- **Started / last event:** 2026-08-02 11:47 UTC → 2026-08-02 12:03 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T19-47-22-019fc24c-d479-7ee1-a1dd-42e917412bc6.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "97cbe3324d050f872b9c539d9d58593bfb534f51", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-02_019fc24c_Repo-root-marlin_ppu-quactlize-branch-develop-PPU.md](../transcripts/2026-08/2026-08-02_019fc24c_Repo-root-marlin_ppu-quactlize-branch-develop-PPU.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop. PPU cutlass3 mixed-input GEMM, Q4_K native packed scale. I want you to ATTACK this plan before I write code, and tell me what is impossible or already contradicted by the tree. Cite file:line.

BACKGROUND FACTS (established, do not re-derive):
- Load bank conflicts 278,528 are the FINE scale/zero reload, identical in base and pack because pack decodes INTO the same two fp16 planes and leaves the read side untouched (collective:574, PLAN_task20_scale.md:1094). Read map h(t) = 256*(t mod 4) + floor(t/4) + C -> 4 distinct words on each of 4 banks. Whole-channel value bounded at 0.8-2.3% (PLAN_task20_scale.md:1123).
- pack ADDS 73,728 store conflicts: `sS(n,G,stage)=sz.scale; sZ(n,G,stage)=sz.zero;` at collective:1500-1502, 32 lanes x 2 B covering 16 of 32 banks, stores cannot broadcast.
- PPU_SCALE_SWIZZLE (in-kernel XOR) removed ZERO conflicts and cost ~7%, with Inst Executed Pipe SALU +97% of peak. Being deleted.
- Waves Per CU = 0.44 (128 CTAs / (72 CU x 4 blocks/CU)); nothing is hidden, work is paid ~1:1 both directions.
- The repo's constraint: an OFFLINE reorder is allowed, an increase in STORED BYTES is not.

THE PLAN -- do it OFFLINE (host-side, byte-neutral) instead of with in-kernel address math. Two independent transforms:

T1. INTERLEAVE (scale, min) into one 32-bit element.
  - packed path: the decoder writes ONE 32-bit store instead of two 16-bit stores. 32 lanes x 4 adjacent bytes = 32 banks exactly once -> the +73,728 goes to ~0. Ownership-safe because a thread derives BOTH halves from its OWN column's unit -- unlike the column-pairing attempt that raced (collective:1400-1406).
  - base path: offline interleave the two gmem fp16 planes (ptr_S, ptr_Z) into one half2 plane -> ONE cp.async channel instead of two, one smem tile.
  - consumer reads one 32-bit word and splits into the existing tCrS/tCrZ half fragments, so bdq_transform is untouched.
  - shared bytes unchanged (4 KiB + 4 KiB = 8 KiB either way). Known trap: cannot store raw y2, because zero += 8*scale (kPackedZMul, collective:1329) is applied after the split.

T2. OFFLINE PERMUTATION sigma of the (n, group) scale tile to kill the LOAD conflicts.
  - cp.async copies a contiguous run, so permuting gmem permutes smem identically. Pre-permute offline so the 32 lanes of a warp land on 32 distinct banks. ZERO runtime address math, which is exactly what PPU_SCALE_SWIZZLE failed on.
  - Same technique the repo already uses for sub-byte B (pi = frag.layout()^-1).

ATTACK THESE SPECIFICALLY:
1. Is T2 even possible? sigma must simultaneously satisfy ALL 8 N-warps, all 8 groups, both stages, AND every reader: the FINE per-group reload (collective:1877-1878, 1907-1908), the coarse reload (1685-1689), the prefetch reload (1880-1881), and fragment setup. If two readers of the same element want it in different banks there is no sigma. Read the actual partitioning and say whether the readers share ONE thread->element map.
2. T1 and T2 INTERACT on the packed path. T1 fixes the stores by making them 32-bit and contiguous in n. T2 permutes n, which may scatter those stores and REINTRODUCE store conflicts. Can sigma be restricted to a form that preserves 32-contiguity of the store (e.g. permuting only whole 32-element runs, or only the group axis)? If sigma must touch n within a 32-run, T1 and T2 are incompatible and I need to pick one.
3. For the packed path the scale is DERIVED in-kernel from the 16-byte unit, so there is no offline scale array to permute -- sigma would have to be applied by the decoder's store index. Is that free (compile-time constant index) or does it become the same address arithmetic that sank the swizzle?
4. Does sigma bake TileN and the warp shape into the stored weight? The repo builds many tile shapes into one binary (collective:462-470 discusses exactly this for the swizzle) and quactlize/layouts.py requires parameters to appear in the layout NAME. Is a tile-shape-specific scale tensor acceptable, or does it break the multi-unit binary?
5. base has 8,192 Shared Store bank conflicts and base does NOT store scale from registers. What are they? Find them.
6. Given the 0.8-2.3% bound on the whole load channel, and that T1 halves the read INSTRUCTION count (~136,192 fewer tsm.ld), is T2 worth doing at all, or is T1 alone the whole realistic win? Give me a ranked recommendation with the numbers you can support.

Be concrete. If a step is impossible say so and say why, with the line that proves it.

## Last assistant conclusions

### 2026-08-02 12:03 UTC

The core verdict: T1 is feasible and worth one measured implementation. T2 is impossible in the proposed “offline bytes only, unchanged readers” form. An offline permutation changes values at addresses; bank conflicts depend on the addresses themselves.

## 1. T2: the readers are compatible, but offline permutation cannot move their banks

All listed consumers use one thread-to-source map:

- `partition_extra_mma_info` creates one `smem_tiled_copy_S`, one thread slice, and `tCsS`; zero uses that same slice and layout ([collective:1557](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1557), [collective:1598](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1598)).
- Both normal and prefetch destinations are retiled from that same copy object ([collective:1627](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1627)).
- Coarse, FINE, and prefetch all read through `tCsS/tCsZ`; only their group/stage coordinate and destination fragment differ ([collective:1685](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1685), [collective:1827](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1827), [collective:1877](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1877), [collective:1907](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1907)).
- Fragment setup derives its register layout from the same MMA B partition ([collective:1284](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1284)).

So there is no “same element wants different banks” contradiction. The successful conflict-free swizzle already proves a single physical address permutation can serve these readers.

But an offline permutation with unchanged copy and read layouts cannot do that:

```text
offline reorder: value_at_address changes
bank conflict:   addresses_issued_by_warp matter
```

The reader still issues `h(t)`, so it still hits the same banks. Worse, it now reads the wrong `(n, group)` value. To preserve correctness, `sigma` must be composed into the smem destination and every reader view—the exact runtime-address operation used by `PPU_SCALE_SWIZZLE`. The tree explicitly distinguishes a stored-byte reorder from a runtime bank swizzle for this reason ([layouts.py:30](/root/marlin_ppu/quactlize/quactlize/layouts.py:30)).

Therefore: T2 as stated is impossible.

## 2. T1 and a real address permutation are not inherently incompatible

A group-only permutation cannot help: the group stride is a whole number of 32-bank periods, so changing group order leaves the bank unchanged.

A useful permutation must mix group bits into low `n`/bank bits. That is exactly what the existing swizzle does: its donor bits are group-index bits, inserted below into the bank-selecting portion of `n` ([collective:54](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:54)).

That does not necessarily break T1’s 32-bit stores. For fixed `G`, any bijection of the low five word-address bits still maps 32 lanes onto all 32 banks once. The addresses need not remain monotonically adjacent; they only need distinct banks.

So:

- “T2 must touch `n` within a 32-run” is true.
- “Therefore it reintroduces T1 store conflicts” is false.
- “Permute only whole runs or only groups” cannot fix the load conflicts.

However, once T1 changes the element from 16 to 32 bits, the old swizzle parameters are not reusable without a new bank proof. The existing table was measured per half-valued `TileN` ([collective:63](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:63)).

Practically, choose T1, because the only way to combine it with an effective T2 reintroduces runtime address work.

## 3. Packed T2 cannot be offline—and the decoder index is not free

The packed input is `[superblock][N][16]`: one unit contains one column’s shared `d/dmin` header and all eight groups’ codes ([collective:724](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:724)). The decoder reads that entire column-owned unit and shares its header across every group ([collective:1439](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1439)).

An effective sigma is group-dependent. Permuting whole 16-byte units gives every group the same `n` permutation, which cannot break the four-group collision. Building a destination unit from different source columns per group is generally impossible in the native format because those groups would require different `d/dmin` headers, but the unit has only one header.

Therefore the only viable packed implementation point is the decoded smem store.

Although `G` is compile-time at [collective:1450](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1450), `n` is runtime at [collective:1439](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1439). A constant XOR mask applied to a runtime `n` is still an executed address operation. Type-level `composition()` does not make that free; that is the same mechanism that produced the SALU increase ([collective:68](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:68)).

## 4. A stored sigma would be tile-specific and conflicts with current multi-unit ownership

The conflict-free mapping depends on `Scale_TileN`; the tree has separate entries for 32, 64, and 128 ([collective:54](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:54)). More generally the reader map comes from the MMA B TV layout, so warp shape can matter too.

The layout registry requires every byte-changing parameter in the name ([layouts.py:18](/root/marlin_ppu/quactlize/quactlize/layouts.py:18)). Existing offline B placement encodes the relevant `TN/WN` ratio, `TK`, and fold precisely because its stored bytes differ ([layouts.py:92](/root/marlin_ppu/quactlize/quactlize/layouts.py:92), [layouts.py:136](/root/marlin_ppu/quactlize/quactlize/layouts.py:136)).

More decisively, the current multi-unit benchmark owns:

- one shared scale allocation for rows with different `Scale_TileK`/tile shapes ([moe_splitk_bench_common.hpp:105](/root/marlin_ppu/quactlize/benchmarks/moe_splitk_bench_common.hpp:105));
- a separate, freshly placed B buffer per configuration because B placement is shape-dependent ([moe_splitk_bench_common.hpp:233](/root/marlin_ppu/quactlize/benchmarks/moe_splitk_bench_common.hpp:233)).

A tile-specific scale sigma would require the scale tensor to become per-unit like B. Holding all variants increases stored bytes; holding one variant makes the other compiled units incompatible. The binary can contain them, but one scale pointer cannot satisfy several differing sigmas.

T1 is shape-independent and avoids this problem. T2 does not.

## 5. The base 8,192 store conflicts are the epilogue staging stores

They are not decoded-scale stores. This kernel selects `EpiloguePtrArraySimtVectorized` ([moe_grouped_ppu.cuh:127](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:127)). That epilogue allocates a shared accumulator tile ([ppu_epilogue_vectorized_evt.hpp:111](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/epilogue
… [truncated 3445 chars]
