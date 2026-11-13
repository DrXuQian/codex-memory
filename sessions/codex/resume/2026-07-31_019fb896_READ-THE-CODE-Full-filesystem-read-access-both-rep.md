# Resume brief: READ THE CODE. Full filesystem read access; both repos are here. Say "I cannot tell from the tree" rather than
inventing. Two questions, and the second is the one I care more about because nobody has ever looked at it.

REPOS
  /root/marlin_ppu/Kernels                      branch ppu_dev
  /root/marlin_ppu/Kernels/third_party/actlize  branch ppu-w4a16-dev

CONTEXT. Mixed-input W4A16 grouped GEMM (MoE, batch-1 decode) on the PPU (T-Head ZW810, SM80-like, 72 CUs, 256 KB
shared per CU, HBM peak ~2766 GB/s). Weights GGUF Q4_K, gs=32. Two ways to feed the per-group scale/zero:
  BASELINE  an offline step pre-multiplies into two fp16 planes (scale, zero: 4 B per group per column), cp.async'd
            straight into shared memory. 20.11 us.
  PACKED    the gguf's own 16 B unit per (superblock, column) -- fp16 d, fp16 dmin, sixteen 6-bit codes -- is
            cp.async'd in raw (2 B per group per column, half the traffic) and decoded on device into the SAME two
            fp16 shared planes, one thread per column, between cp_async_wait and __syncthreads. 22.70 us.
Both numerically correct now. Same kernel, pinned fingerprint grid (8,16,1) block (256,1,1), TileShape 16x128x256,
warp 16x16, Stages 2. Identical on both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960;
smem.ld 31,744; vmem.acp.commit.grp 19,456. Registers 102 -> 98.

Q1. WHY IS THE NATIVE FORM SLOWER, mechanically? Not "it costs instructions" -- I have the deltas
    (v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944; v.and.i +64,512; v.fma.f16 +36,864;
    tsm.st +71,680; Shared Load +4,608; cp.async's own smem writes -9,216; scalar ~+150K; ~+699K total on ~4.4M).
    What I want is the STRUCTURAL reason, and specifically whether the placement is the problem rather than the
    volume: the decode sits between a per-thread cp_async_wait and the CTA-wide __syncthreads that publishes the
    stage, so every warp in the CTA waits for the slowest decoding warp, and only 128 of the 256 threads decode
    (one per column of Scale_TileN=128) while the other 128 idle at the barrier. Read packed_decode_stage and its
    two call sites in mma() and say whether that placement, the half-idle CTA, or the raw instruction volume best
    explains 2.59 us -- and what the cheapest experiment is that separates them. Also: is there a placement that
    would work (decode stage s+1 during stage s, warp specialisation, decoding in the epilogue of the previous
    iteration), or is the dependency structure genuinely serial here?

Q2. WHERE DO THE BANK CONFLICTS COME FROM? This is the part nobody has examined. The acu TSM table for the pinned
    pair, Current = packed, Baseline = the fp16-plane build:

      Shared Load                445,952 (+1.04%)   transactions 1,945,600 (+1.93%)   bank conflicts 278,528 (+0.00%)
      Shared Store                84,480 (+560%)    transactions   181,248 (+261%)    bank conflicts  81,920 (+900%)
      Shared Store From Global    14,976 (-38.10%)  transactions   516,096 (-12.50%)  bank conflicts       0 (+0.00%)
      Total                      545,408 (+14.02%)  transactions 2,642,944 (+3.70%)   bank conflicts 360,448 (+25.71%)

    So the BASELINE already has 278,528 shared-LOAD bank conflicts and 8,192 store conflicts, and the packed decode
    adds 73,728 store conflicts on top. THE LOAD CONFLICTS ARE THE BIG ONES AND THEY ARE NOT MINE -- they are in the
    shipped path. 278,528 against 445,952 load instructions is 0.62 conflicts per instruction, and 1,945,600 /
    445,952 = 4.36 transactions per load instruction.

    Find them. Which shared-memory READ in the mainloop produces them, with file:line: the A tile, the B tile, the
    scale tile, the zero tile, or the mma's own operand reads? Derive the bank map from the actual layouts rather
    than guessing -- SmemLayoutScale is tile_to_shape(Layout<Shape<_8,_1>>{}, (Scale_TileN, Scale_TileK, Stages)) and
    the scale is read through SmemCopyAtomScale into a fragment made by make_fragment_like(partition_fragment_B(...)),
    so the access pattern is the mma B operand's, not a linear sweep. Note the tree claims the scale fragment is
    deliberately k-broadcast, i.e. many lanes read the SAME address, and lanes sharing an address BROADCAST rather
    than conflict -- so count DISTINCT addresses per bank, not lanes per bank. There is a prior local analysis in
    fold_derivation/l94_native_scale_path.cu section (2) that claims 4-way conflicts on 4 banks for the fp16 scale
    read; check whether it is right and whether it accounts for 278,528.

    Then: for the PACKED decode specifically, which line produces the +73,728 store conflicts and the 1.83
    transactions per store, and what is the cheapest fix that does not break the invariant that a thread may only
    read shared bytes it copied itself (cp_async_wait is per-thread and the publishing __syncthreads comes after the
    decode)? A previous attempt to widen the store to 4 B by pairing two columns per thread violated exactly that
    invariant and had to be reverted.

    Finally: are the load conflicts worth attacking at all? 278,528 conflicts on a 34,191-cycle kernel across 128
    CTAs -- estimate the cycles they can plausibly cost and say whether this is a first-order term or noise.

FILES
  actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp   (mainloop, packed_decode_stage,
      partition_extra_inputs / partition_extra_mma_info, the four transform arms, SmemLayoutScale, SmemCopyAtomScale)
  actlize/include/cutlass/gguf_packed_scale.h
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/l94_native_scale_path.cu   (the prior bank analysis)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md      (the whole history)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/README.md

- **Thread ID:** `019fb896-c33f-7e20-bc3f-a295b51daf57`
- **Started / last event:** 2026-07-31 14:31 UTC → 2026-07-31 14:54 UTC
- **Working dir:** `/root/marlin_ppu/Kernels`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/07/31/rollout-2026-07-31T22-31-55-019fb896-c33f-7e20-bc3f-a295b51daf57.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "118865063de0f945630429afa171fe644e548a61", "branch": "ppu_dev", "repository_url": "git@github.com:DrXuQian/Kernels.git"}`

Full transcript: [2026-07-31_019fb896_READ-THE-CODE-Full-filesystem-read-access-both-rep.md](../transcripts/2026-07/2026-07-31_019fb896_READ-THE-CODE-Full-filesystem-read-access-both-rep.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

READ THE CODE. Full filesystem read access; both repos are here. Say "I cannot tell from the tree" rather than
inventing. Two questions, and the second is the one I care more about because nobody has ever looked at it.

REPOS
  /root/marlin_ppu/Kernels                      branch ppu_dev
  /root/marlin_ppu/Kernels/third_party/actlize  branch ppu-w4a16-dev

CONTEXT. Mixed-input W4A16 grouped GEMM (MoE, batch-1 decode) on the PPU (T-Head ZW810, SM80-like, 72 CUs, 256 KB
shared per CU, HBM peak ~2766 GB/s). Weights GGUF Q4_K, gs=32. Two ways to feed the per-group scale/zero:
  BASELINE  an offline step pre-multiplies into two fp16 planes (scale, zero: 4 B per group per column), cp.async'd
            straight into shared memory. 20.11 us.
  PACKED    the gguf's own 16 B unit per (superblock, column) -- fp16 d, fp16 dmin, sixteen 6-bit codes -- is
            cp.async'd in raw (2 B per group per column, half the traffic) and decoded on device into the SAME two
            fp16 shared planes, one thread per column, between cp_async_wait and __syncthreads. 22.70 us.
Both numerically correct now. Same kernel, pinned fingerprint grid (8,16,1) block (256,1,1), TileShape 16x128x256,
warp 16x16, Stages 2. Identical on both sides: v.mma 131,072; v.lop3.i 546,816; v.bfi.i 270,336; tsm.ld.swzl 168,960;
smem.ld 31,744; vmem.acp.commit.grp 19,456. Registers 102 -> 98.

Q1. WHY IS THE NATIVE FORM SLOWER, mechanically? Not "it costs instructions" -- I have the deltas
    (v.mul.f16 +73,728; v.add.f16 +73,728; v.shrl.i +72,704; v.or.i +82,944; v.and.i +64,512; v.fma.f16 +36,864;
    tsm.st +71,680; Shared Load +4,608; cp.async's own smem writes -9,216; scalar ~+150K; ~+699K total on ~4.4M).
    What I want is the STRUCTURAL reason, and specifically whether the placement is the problem rather than the
    volume: the decode sits between a per-thread cp_async_wait and the CTA-wide __syncthreads that publishes the
    stage, so every warp in the CTA waits for the slowest decoding warp, and only 128 of the 256 threads decode
    (one per column of Scale_TileN=128) while the other 128 idle at the barrier. Read packed_decode_stage and its
    two call sites in mma() and say whether that placement, the half-idle CTA, or the raw instruction volume best
    explains 2.59 us -- and what the cheapest experiment is that separates them. Also: is there a placement that
    would work (decode stage s+1 during stage s, warp specialisation, decoding in the epilogue of the previous
    iteration), or is the dependency structure genuinely serial here?

Q2. WHERE DO THE BANK CONFLICTS COME FROM? This is the part nobody has examined. The acu TSM table for the pinned
    pair, Current = packed, Baseline = the fp16-plane build:

      Shared Load                445,952 (+1.04%)   transactions 1,945,600 (+1.93%)   bank conflicts 278,528 (+0.00%)
      Shared Store                84,480 (+560%)    transactions   181,248 (+261%)    bank conflicts  81,920 (+900%)
      Shared Store From Global    14,976 (-38.10%)  transactions   516,096 (-12.50%)  bank conflicts       0 (+0.00%)
      Total                      545,408 (+14.02%)  transactions 2,642,944 (+3.70%)   bank conflicts 360,448 (+25.71%)

    So the BASELINE already has 278,528 shared-LOAD bank conflicts and 8,192 store conflicts, and the packed decode
    adds 73,728 store conflicts on top. THE LOAD CONFLICTS ARE THE BIG ONES AND THEY ARE NOT MINE -- they are in the
    shipped path. 278,528 against 445,952 load instructions is 0.62 conflicts per instruction, and 1,945,600 /
    445,952 = 4.36 transactions per load instruction.

    Find them. Which shared-memory READ in the mainloop produces them, with file:line: the A tile, the B tile, the
    scale tile, the zero tile, or the mma's own operand reads? Derive the bank map from the actual layouts rather
    than guessing -- SmemLayoutScale is tile_to_shape(Layout<Shape<_8,_1>>{}, (Scale_TileN, Scale_TileK, Stages)) and
    the scale is read through SmemCopyAtomScale into a fragment made by make_fragment_like(partition_fragment_B(...)),
    so the access pattern is the mma B operand's, not a linear sweep. Note the tree claims the scale fragment is
    deliberately k-broadcast, i.e. many lanes read the SAME address, and lanes sharing an address BROADCAST rather
    than conflict -- so count DISTINCT addresses per bank, not lanes per bank. There is a prior local analysis in
    fold_derivation/l94_native_scale_path.cu section (2) that claims 4-way conflicts on 4 banks for the fp16 scale
    read; check whether it is right and whether it accounts for 278,528.

    Then: for the PACKED decode specifically, which line produces the +73,728 store conflicts and the 1.83
    transactions per store, and what is the cheapest fix that does not break the invariant that a thread may only
    read shared bytes it copied itself (cp_async_wait is per-thread and the publishing __syncthreads comes after the
    decode)? A previous attempt to widen the store to 4 B by pairing two columns per thread violated exactly that
    invariant and had to be reverted.

    Finally: are the load conflicts worth attacking at all? 278,528 conflicts on a 34,191-cycle kernel across 128
    CTAs -- estimate the cycles they can plausibly cost and say whether this is a first-order term or noise.

FILES
  actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp   (mainloop, packed_decode_stage,
      partition_extra_inputs / partition_extra_mma_info, the four transform arms, SmemLayoutScale, SmemCopyAtomScale)
  actlize/include/cutlass/gguf_packed_scale.h
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/l94_native_scale_path.cu   (the prior bank analysis)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/PLAN_task20_scale.md      (the whole history)
  Kernels/general/w4a16_gemm/cutlass_w4a16/fold_derivation/README.md

## Last assistant conclusions

### 2026-07-31 14:54 UTC

At the current heads—Kernels `cbc472a`, actlize `67bb52e9`—the dominant load conflicts are the scale and zero reloads, while the packed regression is decode/store work placed directly on the stage-publication critical path. The half-idle CTA is real during decode, but the tree contains a cheap way to test it that has been overlooked.

## Q1 — Why packed is slower

The serialized chain is exactly:

```text
raw cp.async → per-thread wait → decode → fp16 shared stores → CTA sync → scale/zero consumers
```

Both call sites place it literally between wait and publication:

- Prologue: [ppu_mma_aiu_multistage_mixed_input.hpp:892](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:892)
- Steady state: [ppu_mma_aiu_multistage_mixed_input.hpp:924](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:924)

Only threads 0–127 enter the decoder loop at [line 1308](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1308). Thus four warps do the entire decode and four reach `__syncthreads()` almost immediately. The slowest decoding warp determines publication latency.

The best mechanical explanation is therefore not “placement versus volume” as two alternatives:

- The ~699K extra instructions are the payload and are quantitatively large enough to explain the regression: `699K/72 ≈ 9,708` extra dynamic instructions per CU against a 4,397-cycle increase, or about 2.2 added instructions/CU-cycle.
- Placement makes that payload exposed rather than overlappable.
- The half-idle CTA is an amplification of that placement; it does not add instructions. In fact, four full decoder warps are more issue-efficient than spreading the same lane work sparsely over eight warps.

So my ranking is: **decode plus explicit-store volume on a forced critical path**, with the half-idle barrier making its latency visible. The present A/B cannot tell how much belongs to each. The existing NOP decomposition at [lines 1321–1328](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1321) still needs to be run:

- `P − N`: decode arithmetic.
- `N − B`: raw transport, explicit stores, and critical-slot/barrier effects.

### The cheapest half-idle experiment

There are actually **two raw-copy owners per column** in the current tree.

For this shape, `(Scale_TileN/8) * Scale_TileK = 16*8 = 128`, and `mma()` passes `thread_idx % 128` into `partition_extra_inputs` at [line 715](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:715). The raw copy is also modulo its 128-thread layout at [line 1122](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1122).

Therefore threads `n` and `n+128` both cp.async the same column into the same location. Each thread’s wait covers a copy it issued itself. The ownership invariant permits both to read that unit.

The clean experiment is:

- Threads 0–127 decode groups 0–3 for column `thread_idx`.
- Threads 128–255 decode groups 4–7 for column `thread_idx-128`.

This gives all eight warps four groups each instead of four warps eight groups each. It preserves:

- The number of per-group decode operations.
- The total fp16 stores.
- The bank-conflict count.
- Correct ownership and publication ordering.

It adds only a second raw 16-byte shared read and header setup per column pair—small compared with the group arithmetic. If this improves materially, slowest-warp/barrier placement is important. If it does not, aggregate instruction/pipe demand is dominant. This is a cleaner placement test than moving the whole wait.

One related finding: the new inner modulo and `l97` comment describe an out-of-range call, but the actual caller already applied the modulo at line 715. `l97` tested unmodded `get_slice(t)` directly, not the call path in `mma()`. In the current call tree, the inner modulo is redundant; the second 128 threads were already duplicate owners.

### Can decode overlap stage s?

The dependency is serial only from raw arrival through publication:

```text
raw ready → decode → stores complete → CTA barrier → consumers
```

It is not necessary for the whole CTA to do no useful stage-s work during that interval. The next raw stage is issued at `k_block == 0`, while decode waits until the last `k_block`. Because stages are double-buffered, these are structurally possible:

- Decode `s+1` while non-owner warps finish compute on `s`.
- Issue the last stage-s MMA before decode/publication.
- Temporally specialize four warps as producers, then reunite at the existing barrier.

The complications are that raw scale, A, and other cp.async operations share commit/wait groups, and all eight warps own MMA N work—there are no spare dedicated producer warps. A true dedicated-warp design therefore requires a larger CTA or a different MMA partition. The duplicate-owner group split above obtains the useful half-idle test without that redesign.

“Epilogue of the previous iteration” works only if that means after an earlier stage-s MMA issue. The kernel epilogue after the entire K loop is too late.

## Q2 — Where the load conflicts come from

The dominant source is the **FINE scale and zero reload pair**:

- Scale: [line 1732](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1732)
- Zero: [line 1733](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1733)

For this pinned shape `Scale_TileK=8 > K_BLOCK_MAX=4`, so the coarse reads at lines 1512/1516 are not the active path.

The scale fragment is indeed shaped from B’s operand partition at [line 1185](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1185), and copied with `make_tiled_copy_B` at [line 1398](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1398).

The alternatives are:

- A shared read: [line 933](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:933), using `tsm.ld.swzl`.
- B shared read: [line 1493](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1493), also swizzled.
- MMA itself: [line 973](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:973), consuming registers, not shared memory.

The count decomposition is almost exact:

```text
441,344 total baseline Shared Loads
−168,960 A/B tsm.ld.swzl
=272,384 scalar scale/zero loads
```

Then:

```text
278,528 conflicts / 272,384 scale/zero loads = 1.0226
```

So essentially every scalar scale/zero load is reported conflicted. The aggregate table cannot assign the remaining 6,144 events between A and B; **I cannot tell from the tree** without per-PC counters.

### Actual scale bank map

The storage layout is `(128,8,2):(1,128,1024)` from [lines 417–419](/root/marlin_ppu/Kernels/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:417).

For the first distinct source value in warp 0, the actual B-copy TV layout gives, in half elements:

```text
h(t) = 256*(t mod 4) + floor(t/4) + C
```

where `C` is the group/stage base. Since a bank word is 4 bytes or two halves:

```text
word(t) = floor(h(t)/2)
bank(t) = word(t) mod 32
```

The 256-half thread stride is 128 bank words, exactly four 128-byte bank periods. Therefore it vanishes modulo 32. For `floor(t/4)=0..7`, the lanes land on banks:

```text
0,0,1,1,2,2,3,3
```

For each bank there are four distinct word addresses, corresponding to the four 
… [truncated 5036 chars]
