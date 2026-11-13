# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop. ATTACK this conclusion. It is the one piece of the current analysis that has never been reviewed, and it is load-bearing: it is why dev/fold_derivation/TODO.md says the +9.2% publication cost is STRUCTURAL and cannot be absorbed by scheduling.

THE DATA. acu Launch Statistics for the pinned decode row (config "16x128:256 w16x16 s2", BAND 64 8 2048 2048 32 3), Current = swz, Baseline = pack:

    Grid Size 128 blocks (+0.00%)      Block Size 256      Threads 32,768
    Waves Per CU 0.44 (+0.00%)         Stack Size 120 B/thread
    Registers Per Thread 104 (+6.12%)
    Static Shared/Block 0              Dynamic Shared/Block 57.36 KB (-6.64%)   [so pack = 61.44 KB]
    Driver Shared/Block 0
    acu advisory ("Small Grid"): "If you execute __syncthreads() to synchronize the threads of a block, it is
    recommended to have at least two blocks per CU (compared to the currently executed 1.8 blocks)"

MY READING, attack each step:

(1) 0.44 = 128 CTAs / (72 CUs x 4 blocks/CU), where 4 blocks/CU is what 61,440 B buys against the 256 KB per-CU cap.
    1.8 = 128/72 is the executed blocks per CU. So the launch fills less than half of ONE wave, and the limiter is
    the GRID, not any per-block resource: shared allows 4, registers 104*256 = 26,624 allows 131072/26624 = 4, warps
    8/block against 64 allows 8.

(2) This EXPLAINS every flat occupancy experiment recorded in TODO.md. They all raised the blocks/CU that RESOURCES
    PERMIT -- PPU_A_PACK 4 -> 12, A-smem stride-0 9 -> 23, PPU_MAXREG -- while the grid supplied 1.8. Slots with no
    blocks to put in them are not a lever, so those measuring ~nothing was necessary, not a failure of execution.

(3) The one lever that raises the RESIDENT count was measured and loses: split-K S=1 -> S=2 gives achieved warps/CU
    14.02 -> 26.84 (1.9x) for 20.18 -> 20.96 us, -4%, recorded at TODO.md "split-K is settled". TileN ladder is
    1.066x. 16x32:64 s4 at 38 warps/CU is 19% SLOWER than 16x32:256 s2 at 18. So acu's advisory has the diagnosis
    right and its remedy is already refuted on this kernel; do not re-run it.

(4) THE CONSEQUENCE, which is the part I most want attacked: at 0.44 waves nothing is hidden, so work is paid ~1:1
    in BOTH directions -- added work costs full price (which is why the swizzle's address math cost ~7% while
    removing zero conflicts) and removed work is refunded at full price (so conflict removal is worth face value,
    not zero). And therefore the +9.2% "transport + stores + barrier" cost of the packed publication is STRUCTURAL:
    no scheduling or occupancy change can absorb it, and the only mechanism left is a shorter critical path.

SPECIFIC THINGS TO CHECK:
  a. Is "Waves Per CU" on this tool really grid / (CUs * blocks-per-CU-limit)? 0.44 * 72 * 4 = 126.7, not 128, so my
     reconstruction is off by 1%. Find the actual definition or say the reconstruction is unverified. Does the repo
     record the CU count as 72 (docs/CHECKPOINT.md) and is that the right number for this part?
  b. Is the blocks/CU limit really 4? 262144/61440 = 4.27 and 131072/26624 = 4.92. Check whether stack size
     (120 B/thread) or anything else enters the occupancy calculation on this hardware, and whether acu reports a
     limiter directly in the Occupancy section that I should have asked for instead of inferring.
  c. Does 1.8 blocks/CU actually imply "no latency cover"? With 1.8 blocks and 8 warps per block that is ~14 warps
     per CU, which is not one warp -- warp-level ILP and multiple warps within a block can still hide latency at a
     barrier. Is my "nothing is hidden" too strong? The recorded split-K experiment says Memory Dependency stalls
     DOUBLED when warps/CU went 14 -> 26.8, which suggests the machine is already at a memory-path limit rather
     than starved for warps. Does that reading change conclusion (4)?
  d. Is the symmetry claim in (4) sound -- that removed work is refunded at the same rate added work is charged? Give
     the condition under which it fails.
  e. Does anything in the repo contradict "the +9.2% is structural"? Look for a recorded experiment where a
     placement or scheduling change moved the publication cost.

Be concrete, cite file:line, and tell me which steps do not survive.

- **Thread ID:** `019fc298-92ad-77f2-b24a-976b0b26ec0a`
- **Started / last event:** 2026-08-02 13:10 UTC → 2026-08-02 13:23 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T21-10-06-019fc298-92ad-77f2-b24a-976b0b26ec0a.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "0cc6ace77d179c6bb732885b990c9e102916c8ef", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-02_019fc298_Repo-root-marlin_ppu-quactlize-branch-develop-ATTA.md](../transcripts/2026-08/2026-08-02_019fc298_Repo-root-marlin_ppu-quactlize-branch-develop-ATTA.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop. ATTACK this conclusion. It is the one piece of the current analysis that has never been reviewed, and it is load-bearing: it is why dev/fold_derivation/TODO.md says the +9.2% publication cost is STRUCTURAL and cannot be absorbed by scheduling.

THE DATA. acu Launch Statistics for the pinned decode row (config "16x128:256 w16x16 s2", BAND 64 8 2048 2048 32 3), Current = swz, Baseline = pack:

    Grid Size 128 blocks (+0.00%)      Block Size 256      Threads 32,768
    Waves Per CU 0.44 (+0.00%)         Stack Size 120 B/thread
    Registers Per Thread 104 (+6.12%)
    Static Shared/Block 0              Dynamic Shared/Block 57.36 KB (-6.64%)   [so pack = 61.44 KB]
    Driver Shared/Block 0
    acu advisory ("Small Grid"): "If you execute __syncthreads() to synchronize the threads of a block, it is
    recommended to have at least two blocks per CU (compared to the currently executed 1.8 blocks)"

MY READING, attack each step:

(1) 0.44 = 128 CTAs / (72 CUs x 4 blocks/CU), where 4 blocks/CU is what 61,440 B buys against the 256 KB per-CU cap.
    1.8 = 128/72 is the executed blocks per CU. So the launch fills less than half of ONE wave, and the limiter is
    the GRID, not any per-block resource: shared allows 4, registers 104*256 = 26,624 allows 131072/26624 = 4, warps
    8/block against 64 allows 8.

(2) This EXPLAINS every flat occupancy experiment recorded in TODO.md. They all raised the blocks/CU that RESOURCES
    PERMIT -- PPU_A_PACK 4 -> 12, A-smem stride-0 9 -> 23, PPU_MAXREG -- while the grid supplied 1.8. Slots with no
    blocks to put in them are not a lever, so those measuring ~nothing was necessary, not a failure of execution.

(3) The one lever that raises the RESIDENT count was measured and loses: split-K S=1 -> S=2 gives achieved warps/CU
    14.02 -> 26.84 (1.9x) for 20.18 -> 20.96 us, -4%, recorded at TODO.md "split-K is settled". TileN ladder is
    1.066x. 16x32:64 s4 at 38 warps/CU is 19% SLOWER than 16x32:256 s2 at 18. So acu's advisory has the diagnosis
    right and its remedy is already refuted on this kernel; do not re-run it.

(4) THE CONSEQUENCE, which is the part I most want attacked: at 0.44 waves nothing is hidden, so work is paid ~1:1
    in BOTH directions -- added work costs full price (which is why the swizzle's address math cost ~7% while
    removing zero conflicts) and removed work is refunded at full price (so conflict removal is worth face value,
    not zero). And therefore the +9.2% "transport + stores + barrier" cost of the packed publication is STRUCTURAL:
    no scheduling or occupancy change can absorb it, and the only mechanism left is a shorter critical path.

SPECIFIC THINGS TO CHECK:
  a. Is "Waves Per CU" on this tool really grid / (CUs * blocks-per-CU-limit)? 0.44 * 72 * 4 = 126.7, not 128, so my
     reconstruction is off by 1%. Find the actual definition or say the reconstruction is unverified. Does the repo
     record the CU count as 72 (docs/CHECKPOINT.md) and is that the right number for this part?
  b. Is the blocks/CU limit really 4? 262144/61440 = 4.27 and 131072/26624 = 4.92. Check whether stack size
     (120 B/thread) or anything else enters the occupancy calculation on this hardware, and whether acu reports a
     limiter directly in the Occupancy section that I should have asked for instead of inferring.
  c. Does 1.8 blocks/CU actually imply "no latency cover"? With 1.8 blocks and 8 warps per block that is ~14 warps
     per CU, which is not one warp -- warp-level ILP and multiple warps within a block can still hide latency at a
     barrier. Is my "nothing is hidden" too strong? The recorded split-K experiment says Memory Dependency stalls
     DOUBLED when warps/CU went 14 -> 26.8, which suggests the machine is already at a memory-path limit rather
     than starved for warps. Does that reading change conclusion (4)?
  d. Is the symmetry claim in (4) sound -- that removed work is refunded at the same rate added work is charged? Give
     the condition under which it fails.
  e. Does anything in the repo contradict "the +9.2% is structural"? Look for a recorded experiment where a
     placement or scheduling change moved the publication cost.

Be concrete, cite file:line, and tell me which steps do not survive.

## Last assistant conclusions

### 2026-08-02 13:23 UTC

The load-bearing conclusion does not survive. The +9.2% is a sound measurement of the current `packnop` implementation, but “STRUCTURAL and unschedulable” is not established. The notes directly contradict both “NOTHING is hidden” and the claimed added/removed-work symmetry.

| Step | Verdict |
|---|---|
| (1) Grid limits achieved residency | Mostly survives |
| (2) Resource-only occupancy changes cannot help this pinned grid | Survives narrowly, not universally |
| (3) Current split-K is a losing remedy | Survives; the causal generalization does not |
| (4) Nothing is hidden; costs/refunds are symmetric; +9.2% is structural | Fails |

### (1) Waves, CU count, and the block limit

The actual `acu` definition is unverified: the repository contains the value and reconstructions, but no `acu` manual or metric formula.

The arithmetic is nevertheless exactly consistent after display rounding:

```text
128 / (72 × 4) = 0.444444… → displayed as 0.44
```

Multiplying the rounded `0.44` back gives 126.72; that is not a 1% occupancy discrepancy, just two-decimal information loss.

The 72-CU count is well supported. The hardware checkpoint says 72 CUs and 256 KiB shared/CU at [CHECKPOINT.md:14](/root/marlin_ppu/quactlize/docs/CHECKPOINT.md:14). The prior adversarial review independently corrected the analysis to 72 and notes that 128 CTAs are 1.78 one-block-per-CU dispatch waves at [PLAN_task20_scale.md:1037](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1037). The advisory’s `128/72 = 1.777… → 1.8` independently matches it.

Four blocks/CU is also the right inferred limit, but the current `swz` kernel is tied on two resources:

```text
shared:    floor(262144 / ~57344)       = 4
registers: floor(131072 / (104 × 256)) = 4
warps:     floor(64 / 8)                = 8
```

For baseline `pack`, 61,440 B gives four blocks, while the inferred 98 registers/thread permit five. Thus:

- `pack`: shared-memory limited at four.
- `swz`: shared memory and registers both limit at four.
- The grid then limits actual S=1 residency to an average 1.78 CTAs/CU.

So “the achieved resident count is grid-limited” survives. “No per-block resource is a limiter” does not: resources define the four-block theoretical ceiling used by the wave calculation.

Nothing in the repo documents stack as an occupancy input. If 120 B/thread were pooled with shared memory, each block would consume another 30,720 B and the combined limit would be two, contradicting `0.44` under the proposed formula. That strongly suggests stack is not charged to the shared-memory occupancy pool, but the hardware rule remains unverified.

Yes, you should have captured the Occupancy section rather than inferred it. `acu` directly reports `Block Limit SMem / Registers` elsewhere in this repo at [TODO.md:375](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:375).

One terminology trap: `0.44` means less than half a *full-theoretical-residency* wave of `72 × 4` blocks. It does not mean fewer than one one-block-per-CU dispatch wave; the same grid is 1.78 of those. “Less than half of ONE wave” is therefore misleading without defining wave.

### (2) The flat resource experiments

This survives for the pinned S=1 launch: increasing capacity beyond four blocks/CU cannot create CTAs absent from a 128-CTA grid. The direct PPU_A_PACK row supports it: `16x128:256 s2` reduces shared memory from 57,344 to 43,904 B and changes time only 22.40 → 22.33 µs at [TODO.md:1444](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:1444).

But “every flat experiment necessarily measured nothing” overstates the record:

- The same PPU_A_PACK change speeds a genuinely smem-limited `16x64:256 s4` from 32.48 to 23.56 µs, 1.38×, at [TODO.md:1447](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:1447).
- The repo explicitly retracts TileN as an occupancy/concurrency axis: every TileN row launches the same 1,024 warps; it merely repackages them into differently sized CTAs [PLAN_task20_scale.md:1027](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1027).
- `16x32:64 s4` versus `16x32:256 s2` changes TileK and pipeline depth as well as theoretical occupancy. It is not a clean occupancy ablation.
- PPU_MAXREG can raise theoretical occupancy while achieved residency remains grid-capped. Calling that “raised occupancy” without distinguishing theoretical from achieved is exactly the mistake already identified at [PLAN_task20_scale.md:1040](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1040).

So step (2) is valid as a pinned-row capacity argument, not as three independent occupancy experiments.

### (3) Split-K and latency cover

The split-K measurement is real and important:

- Achieved warps/CU: 14.02 → 26.84.
- Memory Dependency: 0.98 → 1.772.
- DRAM: 38.65% → 41.48%.
- Time: 20.18 → 20.96 µs.

Those numbers are recorded at [TODO.md:1462](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:1462).

What survives is: **this split-K implementation is not a profitable way to obtain more warps on this tile. Do not repeat the same test.**

What does not survive is treating it as a pure test of occupancy or acu’s exact remedy:

- Split-K also changes K ownership, partial-output traffic, synchronization, and invokes a reduction kernel. It is not “same work, more resident CTAs.”
- The advisory asks for at least two blocks/CU, versus 1.8 now—a roughly 12.5% increase. S=2 doubles the grid to 3.56 blocks/CU and introduces split-K overhead. It is a much larger and structurally different intervention.
- TileN is not an additional resident-count result, and the TileK/stage comparison is confounded.

Most importantly, 1.8 CTAs/CU means about 14.2 warps/CU, not “no latency cover.” Warps within a CTA can issue independently before reaching the barrier; on 56 of 72 CUs a second CTA can also run. Once all resident CTAs align at the barrier, cover disappears, but that is a phase-specific claim—not a launch-wide fact.

The doubled Memory Dependency is more consistent with “the existing warps already put substantial pressure on this request path, and further warps add queueing” than with “nothing was hidden.” It supports rejecting more global occupancy; it does not support zero overlap.

### (4) The structural/symmetry conclusion

This step fails on three direct contradictions.

First, the file explicitly records hidden work:

> `s.wait` rises by 9,216 when decode arithmetic is removed, so the arithmetic was partly hidden in an existing stall window.

That is [TODO.md:8](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:8). Seventy-four lines later, the same file says “NOTHING is hidden” [TODO.md:82](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:82). Both cannot be true.

Second, the claimed proof that swizzle address math “cost 7%” was expressly disallowed earlier in the same document. `swz` versus `pack` differs in g2s channels, decoder stores, and register allocation; the notes say pricing the XOR requires `swz` versus `base` counters that were not captured [TODO.md:44](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:44). Therefore the sentence at [TODO.md:83](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:83) uses a number the analysis itself says not to quote.

Third, the repository’s direct placement test contradicts “the only mechanism left is a shorter critical path.” `PPU_PACKED_SPLIT_GROUPS` changed four publisher warps × eight groups into eight warps × four groups, keeping decode/store/conflict counts constant but adding one read/setup. It was 11% slower, and the recorded conclusion was that the publication barrier’s critical path was not what the packed path pays for [PLAN_task20_scale.md:1177](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1177). That test is confounded by its added read/setup, so it does not prove placement can never work—but it certainly does not support “shorter critical path is the only mechanism.”

The symmetry
… [truncated 2774 chars]
