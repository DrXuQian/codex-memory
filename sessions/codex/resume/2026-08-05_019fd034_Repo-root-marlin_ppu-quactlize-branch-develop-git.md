# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 066. There are first box numbers and a structural finding, and the first item may be worth 4.4 points of MFU.

FIRST VALIDATED DENSE MEASUREMENT, ever, after your fix:

    2048x4096x4096  gs=32   cfg=128x64:64x16:s4
    226.88 us | 302.9 TFLOP/s | 60.6% MFU

Against BACKTEST A1 — 211.33 us / 65.0%, same shape and gs, from test_scalefirst_bench (I renamed q3_bconcat; it runs the grouped route). Dense is 7.4% slower and I believe the cause is structural:

    the recorded int4 optimum is (64,64,64) w64x32 -> (64/64)*(64/32) = 2 warps
    that is DenseSubFourWarpDeviceAbort, so dense cannot launch it
    the 227-row dense table has ZERO rows with WM=64 WN=32 at TM=64 TN=64
    test_scalefirst_bench has FIVE int4 w64x32 rows and its winner is one of them

So the quarantine excludes the measured optimum at compile time and dense's best reachable geometry is different (w64x16, TN/WN=4).

① THE QUESTION THAT MAY GIVE THE 65% BACK. Your own comment says "Keep the dense boundary conservative UNTIL THE DENSE KERNEL/EPILOGUE ASSERT SITE IS IDENTIFIED", and the exclusion's clause says "dense SplitKSerial". Dense carries a split_k axis, grouped does not, and the 10 rows I just quarantined out of test_fpA_intB_ppu all carry split_k (spk 1..32). If the abort is SPLIT-K-specific rather than warp-count-specific, split_k=1 two-warp rows are legal on dense and the optimum returns. Identifying the assert site is worth doing before anyone tunes around the restriction, because tuning around a boundary wider than it needs to be bakes in the loss.

② PPU_B_CHUNK IS NOT AVAILABLE TO DENSE int4 AT ALL — I had this wrong twice. It is not "off": the ordinary one-plane collective has ZERO occurrences of PPU_B_CHUNK, prepare_atom or transform_B_atom, and int4 at TK=64 is F=1 so it runs there. Your parity map already says exactly this. Its priority depends on ①: if the optimum becomes reachable, chunk is ordinary optimisation; if it does not, chunk is how dense closes the gap.

I have read DENSE_GROUPED_PARITY_061.md and accept both reframings: PPU_B_CHUNK is provider drift across three copied bodies rather than an operator asymmetry, and the gs ladder was launcher drift before the common builder. "Grouped has it, dense does not" was the wrong axis and I will stop using it.

ON THE EXTRACTION ORDER — I agree with it and with stopping before step 1 for review. Two things I want to raise rather than approve silently:

First, your Axis 3 flags something that outranks the whole extraction and I want it treated as such: "Scale-copy thread coverage ... A formerly admitted two-warp shape loaded only half its groups until the two-plane copy was fixed. THE CURRENT TACTIC GATE MASKS THAT EXACT ROW; CHANGING THE CANDIDATE SET CAN REVIVE IT." We are about to change the candidate set — that is what the sweep and ① both do. So that row needs a static guard now, before either lands, not after the extraction reaches Axis 3. If ① widens the dense boundary, it may re-admit precisely the shape that loaded half its groups.

Second, "12 assert(false) sites" each in fold and two-plane. The ordinary one cost this project a day and surfaced as an unrelated occupancy failure. Twenty-four more of the same are live. Your step 2 covers them, but if step 2 is far away I would rather convert them to dependent static_asserts as a standalone change first — it is mechanical and it removes a class of failure that is expensive to diagnose.

Everything else in the map I accept as written, including that the compiled tactic inventories stay separate with the enumeration ABI as the loud mechanism.

- **Thread ID:** `019fd034-c172-7db0-b427-6cb121ce6ef4`
- **Started / last event:** 2026-08-05 04:35 UTC → 2026-08-05 04:55 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/05/rollout-2026-08-05T12-35-46-019fd034-c172-7db0-b427-6cb121ce6ef4.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "ed0787b2d9abd43db9b501a1b629b283783544a7", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-05_019fd034_Repo-root-marlin_ppu-quactlize-branch-develop-git.md](../transcripts/2026-08/2026-08-05_019fd034_Repo-root-marlin_ppu-quactlize-branch-develop-git.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 066. There are first box numbers and a structural finding, and the first item may be worth 4.4 points of MFU.

FIRST VALIDATED DENSE MEASUREMENT, ever, after your fix:

    2048x4096x4096  gs=32   cfg=128x64:64x16:s4
    226.88 us | 302.9 TFLOP/s | 60.6% MFU

Against BACKTEST A1 — 211.33 us / 65.0%, same shape and gs, from test_scalefirst_bench (I renamed q3_bconcat; it runs the grouped route). Dense is 7.4% slower and I believe the cause is structural:

    the recorded int4 optimum is (64,64,64) w64x32 -> (64/64)*(64/32) = 2 warps
    that is DenseSubFourWarpDeviceAbort, so dense cannot launch it
    the 227-row dense table has ZERO rows with WM=64 WN=32 at TM=64 TN=64
    test_scalefirst_bench has FIVE int4 w64x32 rows and its winner is one of them

So the quarantine excludes the measured optimum at compile time and dense's best reachable geometry is different (w64x16, TN/WN=4).

① THE QUESTION THAT MAY GIVE THE 65% BACK. Your own comment says "Keep the dense boundary conservative UNTIL THE DENSE KERNEL/EPILOGUE ASSERT SITE IS IDENTIFIED", and the exclusion's clause says "dense SplitKSerial". Dense carries a split_k axis, grouped does not, and the 10 rows I just quarantined out of test_fpA_intB_ppu all carry split_k (spk 1..32). If the abort is SPLIT-K-specific rather than warp-count-specific, split_k=1 two-warp rows are legal on dense and the optimum returns. Identifying the assert site is worth doing before anyone tunes around the restriction, because tuning around a boundary wider than it needs to be bakes in the loss.

② PPU_B_CHUNK IS NOT AVAILABLE TO DENSE int4 AT ALL — I had this wrong twice. It is not "off": the ordinary one-plane collective has ZERO occurrences of PPU_B_CHUNK, prepare_atom or transform_B_atom, and int4 at TK=64 is F=1 so it runs there. Your parity map already says exactly this. Its priority depends on ①: if the optimum becomes reachable, chunk is ordinary optimisation; if it does not, chunk is how dense closes the gap.

I have read DENSE_GROUPED_PARITY_061.md and accept both reframings: PPU_B_CHUNK is provider drift across three copied bodies rather than an operator asymmetry, and the gs ladder was launcher drift before the common builder. "Grouped has it, dense does not" was the wrong axis and I will stop using it.

ON THE EXTRACTION ORDER — I agree with it and with stopping before step 1 for review. Two things I want to raise rather than approve silently:

First, your Axis 3 flags something that outranks the whole extraction and I want it treated as such: "Scale-copy thread coverage ... A formerly admitted two-warp shape loaded only half its groups until the two-plane copy was fixed. THE CURRENT TACTIC GATE MASKS THAT EXACT ROW; CHANGING THE CANDIDATE SET CAN REVIVE IT." We are about to change the candidate set — that is what the sweep and ① both do. So that row needs a static guard now, before either lands, not after the extraction reaches Axis 3. If ① widens the dense boundary, it may re-admit precisely the shape that loaded half its groups.

Second, "12 assert(false) sites" each in fold and two-plane. The ordinary one cost this project a day and surfaced as an unrelated occupancy failure. Twenty-four more of the same are live. Your step 2 covers them, but if step 2 is far away I would rather convert them to dependent static_asserts as a standalone change first — it is mechanical and it removes a class of failure that is expensive to diagnose.

Everything else in the map I accept as written, including that the compiled tactic inventories stay separate with the enumeration ABI as the loud mechanism.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp` ×2
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_fold.hpp` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh` ×1
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_tactic_space.hpp` ×1
- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×1
- `/root/marlin_ppu/quactlize/.coord/BOX.md` ×1

## Last assistant conclusions

### 2026-08-05 04:55 UTC

The split-K hypothesis is falsified: the original aborting benchmark instantiated plain `GemmUniversal<Problem,Main,Epi>` with no `SplitKSerialScheduler` or split axis. Therefore `split_k=1` is not a justified exception, and the dense quarantine remains intact. The exact device assertion still requires ppu001; a focused diagnostic is recorded in [BOX.md](/root/marlin_ppu/quactlize/.coord/BOX.md:285).

Completed and pushed to `develop`:

- Compile-time scale-copy coverage guards across ordinary, folded, and two-plane mainloops, asserted by both launchers.
- All 24 fold/two-plane `assert(false)` sites replaced with dependent `static_assert`s.
- Corrected the misleading “dense SplitKSerial” exclusion description in [ppu_tactic_space.hpp](/root/marlin_ppu/quactlize/quactlize/include/ppu_tactic_space.hpp:128).
- Accepted INBOX 067: no TK64 int4 chunk work; TK256 chunking remains a future searched tactic capability.
- Confirmed `fed082d`’s comparator matches the intended design: 891 declared differences, zero unexpected.

Validation passed: 12/12 strict lint, 3/3 dense compact-A variants, dense/MoE bench syntax, and Q3 two-plane syntax.

Root commits: `eae0f06`, `1017b1e`, `095085a`. Submodule commits: `148ecaf6`, `46a2b851`. The seven pre-existing modified files were preserved.
