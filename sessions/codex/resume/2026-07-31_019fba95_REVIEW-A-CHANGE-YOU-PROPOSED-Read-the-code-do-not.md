# Resume brief: REVIEW A CHANGE YOU PROPOSED. Read the code; do not answer from this description. Your job is to find what is WRONG
with it, not to confirm it. Say "I cannot tell from the tree" where that is the truth.

In your last review of this repo you proposed splitting the packed scale decode by GROUP rather than by column,
on the observation that mma() wraps the thread index before partitioning
(`thread_idx % (Scale_GmemCopyThrLayoutH * Scale_GmemCopyThrLayoutW)`), so threads n and n + Scale_TileN are
duplicate owners of the same column -- each issuing its cp.async and each waiting on a copy it issued itself.

That is now implemented as PPU_PACKED_SPLIT_GROUPS, off by default, in
  third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp
in packed_decode_stage. Read the whole function and both of its call sites in mma().

ATTACK IT ON THESE POINTS, and add any I have not thought of.

A. OWNERSHIP. The invariant is that between the per-thread cp_async_wait and the CTA-wide __syncthreads that
   publishes the stage, a thread may only read shared bytes IT ITSELF copied. Verify the duplicate-owner claim from
   the code rather than from my summary: trace `thread_idx` from mma() through partition_extra_inputs, through
   gmem_tiled_copy_scale_packed.get_slice, to the destination byte each thread writes, and confirm that thread
   t + Scale_TileN really copies the SAME bytes to the SAME address as thread t, for every stage and every
   scale_load_k. If the two writes are merely to the same tile but not the same address, the split is a race.
   Check also the PROLOGUE call site, where the load index is 0 rather than scale_load_k, and the residue path.

B. THE GATE. kSplitGroups requires kThreads == 2*kTN, kWrapTh == kTN, kOwnTh == kTN and kGrp % 2 == 0. Are those the
   right conditions and are they sufficient? Find a shape in the splitk bench's config list (see
   general/w4a16_gemm/cutlass_w4a16/CMakeLists.txt, _SPLITK_CFGS) where the gate passes but the split is wrong, or
   where it fails but the split would have been safe and is therefore silently lost. Note the bench compiles many
   shapes into ONE binary, so a wrong gate is a wrong kernel, not a build error.

C. THE PREDICATE. The loop keeps `if (n >= residue_n) continue;`. Under the split, is the residue still handled
   correctly for BOTH halves? And is the loop bound right -- `for (n = thread_idx % kTN; n < kTN; n += kTN)` runs
   exactly once when the gate holds, but is that true for every shape the gate admits?

D. DOES IT ACTUALLY REBALANCE? The claim is eight warps decoding four groups each instead of four warps decoding
   eight. Check what the compiler is likely to do with the `if (thread_idx < kTN)` branch around two for_each bodies:
   both halves are instantiated, so the code size doubles, and within a warp the branch is uniform (warps 0-3 take
   one side, 4-7 the other) -- confirm that from the thread indexing rather than assuming it. Also: the second raw
   16 B shared read per column is new. Price it against what is saved.

E. WHAT IT CANNOT ANSWER. If this makes the packed path faster, what exactly has been proved, and what has not?
   If it makes no difference, same question. Be precise about the alternative explanations that survive each outcome.

F. Separately, and unrelated to the split: the same file now has PPU_B_DEQUANT_NOP, which routes every
   cute::transform in transform_B_kblock through a bdq_transform wrapper and replaces convert_tensor with a single
   32-bit move. It is meant to keep the B s2r loads, the scale/zero smem reads, the mma count and every barrier while
   removing the int4->fp16 conversion and the affine chain, so that baseline_time - nop_time prices the dequant
   pipeline. Check that it does not accidentally let the compiler delete the loads it is supposed to preserve, that
   the one-element form really keeps both fragments live, and that the mma still sees finite values rather than
   whatever was in the registers. Say whether the resulting number would actually mean what I want it to mean.

Report file:line and a concrete failure scenario for anything you find.

- **Thread ID:** `019fba95-e2e4-7ee2-9b15-d12d0555bc18`
- **Started / last event:** 2026-07-31 23:50 UTC → 2026-08-01 00:00 UTC
- **Working dir:** `/root/marlin_ppu/Kernels`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T07-50-12-019fba95-e2e4-7ee2-9b15-d12d0555bc18.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "fac73de53b54d9785b636de004f66404f759162a", "branch": "ppu_dev", "repository_url": "git@github.com:DrXuQian/Kernels.git"}`

Full transcript: [2026-07-31_019fba95_REVIEW-A-CHANGE-YOU-PROPOSED-Read-the-code-do-not.md](../transcripts/2026-07/2026-07-31_019fba95_REVIEW-A-CHANGE-YOU-PROPOSED-Read-the-code-do-not.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

REVIEW A CHANGE YOU PROPOSED. Read the code; do not answer from this description. Your job is to find what is WRONG
with it, not to confirm it. Say "I cannot tell from the tree" where that is the truth.

In your last review of this repo you proposed splitting the packed scale decode by GROUP rather than by column,
on the observation that mma() wraps the thread index before partitioning
(`thread_idx % (Scale_GmemCopyThrLayoutH * Scale_GmemCopyThrLayoutW)`), so threads n and n + Scale_TileN are
duplicate owners of the same column -- each issuing its cp.async and each waiting on a copy it issued itself.

That is now implemented as PPU_PACKED_SPLIT_GROUPS, off by default, in
  third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp
in packed_decode_stage. Read the whole function and both of its call sites in mma().

ATTACK IT ON THESE POINTS, and add any I have not thought of.

A. OWNERSHIP. The invariant is that between the per-thread cp_async_wait and the CTA-wide __syncthreads that
   publishes the stage, a thread may only read shared bytes IT ITSELF copied. Verify the duplicate-owner claim from
   the code rather than from my summary: trace `thread_idx` from mma() through partition_extra_inputs, through
   gmem_tiled_copy_scale_packed.get_slice, to the destination byte each thread writes, and confirm that thread
   t + Scale_TileN really copies the SAME bytes to the SAME address as thread t, for every stage and every
   scale_load_k. If the two writes are merely to the same tile but not the same address, the split is a race.
   Check also the PROLOGUE call site, where the load index is 0 rather than scale_load_k, and the residue path.

B. THE GATE. kSplitGroups requires kThreads == 2*kTN, kWrapTh == kTN, kOwnTh == kTN and kGrp % 2 == 0. Are those the
   right conditions and are they sufficient? Find a shape in the splitk bench's config list (see
   general/w4a16_gemm/cutlass_w4a16/CMakeLists.txt, _SPLITK_CFGS) where the gate passes but the split is wrong, or
   where it fails but the split would have been safe and is therefore silently lost. Note the bench compiles many
   shapes into ONE binary, so a wrong gate is a wrong kernel, not a build error.

C. THE PREDICATE. The loop keeps `if (n >= residue_n) continue;`. Under the split, is the residue still handled
   correctly for BOTH halves? And is the loop bound right -- `for (n = thread_idx % kTN; n < kTN; n += kTN)` runs
   exactly once when the gate holds, but is that true for every shape the gate admits?

D. DOES IT ACTUALLY REBALANCE? The claim is eight warps decoding four groups each instead of four warps decoding
   eight. Check what the compiler is likely to do with the `if (thread_idx < kTN)` branch around two for_each bodies:
   both halves are instantiated, so the code size doubles, and within a warp the branch is uniform (warps 0-3 take
   one side, 4-7 the other) -- confirm that from the thread indexing rather than assuming it. Also: the second raw
   16 B shared read per column is new. Price it against what is saved.

E. WHAT IT CANNOT ANSWER. If this makes the packed path faster, what exactly has been proved, and what has not?
   If it makes no difference, same question. Be precise about the alternative explanations that survive each outcome.

F. Separately, and unrelated to the split: the same file now has PPU_B_DEQUANT_NOP, which routes every
   cute::transform in transform_B_kblock through a bdq_transform wrapper and replaces convert_tensor with a single
   32-bit move. It is meant to keep the B s2r loads, the scale/zero smem reads, the mma count and every barrier while
   removing the int4->fp16 conversion and the affine chain, so that baseline_time - nop_time prices the dequant
   pipeline. Check that it does not accidentally let the compiler delete the loads it is supposed to preserve, that
   the one-element form really keeps both fragments live, and that the mma still sees finite values rather than
   whatever was in the registers. Say whether the resulting number would actually mean what I want it to mean.

Report file:line and a concrete failure scenario for anything you find.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/Kernels/.review_scale_map.cu` ×2

## Last assistant conclusions

### 2026-08-01 00:00 UTC

The change has two concrete correctness/measurement failures. The duplicate-owner claim is correct for full N tiles, but it breaks on N residue. `PPU_B_DEQUANT_NOP` also feeds uninitialized/arbitrary fp16 bits to MMA and does not preserve all scale/zero reads.

## Findings

1. Packed residue uses the wrong ownership predicate

[`ppu_mma_aiu_multistage_mixed_input.hpp:1096`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1096) derives `scale_valid` from the legacy scale-copy layout, while [`:1122`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1122) partitions the packed copy per column.

For `TN=128, SK=8`, CUTE maps legacy thread `p` to:

```text
legacy first coordinate = (8 * (p % 16), p / 16)
packed coordinate       = column p
```

But [`:1138`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1138) uses the former N coordinate to predicate the latter copy at [`:1060-1067`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1060).

Concrete failure: config `16,128,256,16,16,2`, gs=32, final N tile with `residue_n=20`.

- Threads 3 and 131 own packed column 3, which is valid.
- Their legacy coordinate is N=24, so `scale_valid == false`.
- Neither issues the packed `cp.async`.
- Both enter decode because [`:1338`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1338) sees `3 < 20`.
- They read stale/uninitialized staging bytes that they did not copy.

Conversely, thread 32 has legacy N=0, so it copies packed column 32 even though only columns 0–19 exist, causing an out-of-bounds global read.

Thus the split predicate treats both halves symmetrically, but it occurs after the faulty copy predicate. This bug exists with the split off too, but under the split it directly falsifies the stated ownership invariant.

2. `PPU_B_DEQUANT_NOP` leaves most of the MMA B fragment uninitialized

`tCrB_mma` is allocated without initialization at [`:782`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:782). The NOP writes only one 32-bit word at [`:1654-1657`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1654), and each affine wrapper writes only element zero at [`:1610-1611`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1610).

The first invocation has no “previous k-tile’s already-converted halves”; those registers have never been converted. Later invocations merely reuse prior undefined values.

Each MMA atom consumes four 32-bit B registers—eight fp16 values—per [`mma_ppu0010.hpp:43-45`](/root/marlin_ppu/Kernels/third_party/actlize/include/cute/arch/mma_ppu0010.hpp:43). Most are therefore indeterminate when passed to [`cute::gemm` at :973](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:973).

The one copied word is not safe either: it is packed int4 bits reinterpreted as two fp16 values. A legal packed word such as `0x7e007c00` becomes NaN/+Inf. Only its first half is touched by `bdq_transform`; the second remains NaN. The claim that MMA sees finite values is false.

3. The NOP does not preserve the baseline scale/zero shared-read traffic

`bdq_transform` keeps only `b(0)` live. The scale copies at [`:1554-1558`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1554), [`:1694`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1694), and [`:1773-1775`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1773) use `DefaultCopy`, which is ordinary non-volatile assignment. After inlining, loads feeding unused fragment elements are dead and may be removed.

Therefore it keeps one scale scalar and one zero scalar live, not both complete fragments or their baseline load count. I cannot tell from the tree exactly how many the PPU optimizer deletes; emitted assembly is required.

The B s2r instruction is better protected: [`copy_B_and_extra_info():1535`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1535) reaches a `TSM_LD_SWZL` implemented as `asm volatile`, for example [`copy_ppu0010_aiu.hpp:426-431`](/root/marlin_ppu/Kernels/third_party/actlize/include/cute/arch/copy_ppu0010_aiu.hpp:426). Its instruction calls should remain even when most outputs are unused. The MMA loop and barriers also remain syntactically.

## Split ownership and gate

For a full N tile, the duplicate-owner claim is correct:

- [`mma():714-715`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:714) passes `p = thread_idx % ((TN/8)*SK)`.
- Packed mode requires `SK=8`, so the gate’s `kWrapTh == TN` makes `p = thread_idx % TN`.
- [`partition_extra_inputs():1122-1125`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1122) then gives packed slice `p`.
- Source address is `base + 16*p + 16*N*load_index`.
- Destination address is `smem_base + 16*p + 16*TN*stage`.

Therefore `t` and `t+TN` copy exactly the same 16 bytes to exactly the same address for every stage and for both the literal-zero and `scale_load_k` source-index arms. Both decode calls—[`mma():895`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:895) and [`:925`](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:925)—use that same ownership.

There is still an unproved hardware assumption: one owner can finish its per-thread wait and start reading while the paired owner’s identical asynchronous write remains outstanding. The bytes are identical, but the tree does not specify whether PPU permits that overlapping shared read/write. I cannot tell from the tree.

I found no bad gate instance in the default `_SPLITK_CFGS` list:

| TK=256 shape | Threads | Result |
|---|---:|---|
| TN=32, WN=16 | 64 = 2×TN | passes correctly |
| TN=64, WN=16 | 128 = 2×TN | passes correctly |
| TN=128, WN=16 | 256 = 2×TN | passes correctly |
| TN=64/128, WN=32 | TN | fails correctly: no duplicate owner |
| TK=64/128 rows | — | packed path is off |

The gate is sufficient for the exact two-way mapping, apart from residue and the outstanding-writer assumption. It is not a complete applicability test:

- A legal `TN=16`, one-warp shape could satisfy `kThreads=2*TN`, but `thread_idx<TN` would split a warp rather than being uniform.
- A custom `32,32,256,16,16,2` shape has 128 threads, four duplicate owner sets for TN=32. A four-way two-groups-per-owner split would be safe, but the current gate silently falls back. No such four-owner shape appears in the default list.

The loop itself runs exactly once per admitted thread: `thread_idx % TN` is in `[0,TN)`, and the increment is `TN`. Both halves apply the same decode-side residue test.

## Rebalancing and cost

For the claimed TN=128/WN=16 shape, thread indexing really gives eight 32-thread warps: warps 0–3 take groups 0–3 and warps 4–7 take groups 4–7. The listed TN=32 and TN=64 variants similarly split on warp boundaries.

The “code size doubles” claim is not established. The baseline instantiates G=0…7 once. The split instantiates G=0…3 in one branch and G=4…7 in the other—still eight distinct decode bodies, not sixteen. It adds branch/control-flow layout, but actual machine-code size
… [truncated 1388 chars]
