# Resume brief: Align MoE's search space with dense's. The user asked for this specifically and wants me reviewing rather than implementing.

WHAT I MEASURED TODAY, so you do not repeat it:

  * Pruning is now OPT-IN and off by default (benchmarks/emit_tactic_configs.cpp, pushed). primary/guard is a
    heuristic, not legality: it was dropping 532 of 1164 rows, 46%, and this repository has twice had a
    heuristic hide a measured optimum (the sub-four-warp quarantine hid 65.7% dense; the 1/2/4 compact-A
    whitelist hid capacity 8). `--prune=primary-guard` still narrows for anyone who wants it.
  * dense and grouped spaces are IDENTICAL: 1164 rows each, unpruned, byte-for-byte the same table.
    dense_kernel_exclusion and grouped_kernel_exclusion are both just common_kernel_exclusion.
  * The axes match: emitter emits TM {16,32,64,128,256}, TN {16,32,64,128}, WM {16,32,64} -- the same values as
    _MOE_TM_LIST / _MOE_TN_LIST / _MOE_WM_LIST. The ONE difference is WarpN: _MOE_FORMATS hand-writes a narrower
    per-format subset (q3/q5 pinned to 64, q6 to 32,64) while the emitter DERIVES the same constraint from
    LowDelivery/HighDelivery. So the emitted set should be a superset there, not a subset.
  * benchmarks/lowbit_grouped_configs.inc now exists (unpruned, 1164). Nothing consumes it.

THE CLASSIFICATION I want you to check rather than accept. The variable belongs in the config row only if it
changes the instantiation:

    row fields     TM, TN, TacticTileK, WM, WN, Stages, A_COMPACT_ROWS
    table identity bits/high_bits (the format), ArtifactTileK
    runtime        group size, M, router mode / expert distribution, and split-K's S -- moe_splitk_unit.inc says
                   "the S ladder is a runtime loop inside it, because split-K does not change the instantiation"

If that is wrong anywhere, say so before building on it. In particular _MOE_FORMATS looks like an axis and I
claim it is table identity -- five formats means five emitted tables, not five rows of one.

THE JOB, in this order, and the order is the point:

  1. Emit one unpruned table per format, with bits/high_bits read from quactlize/include/ppu_format_config.inc
     rather than written out again.
  2. Expand _MOE_FORMATS x _MOE_TM_LIST x _MOE_TN_LIST x _MOE_WM_LIST x per-format WarpN x _MOE_STAGES into a row
     set.
  3. SET-DIFFERENCE BOTH WAYS, and report the two numbers. Emitted-minus-product is coverage we gain;
     product-minus-emitted is coverage we would LOSE, and every row in it is either a legality predicate being
     stricter than the hand-written product or an axis the emitter's grid does not reach -- both are findings
     about the space, not about MoE.
  4. ONLY IF product-minus-emitted is empty, wire the MoE bench to the tables and remove the CMake axis lists.

DO NOT delete _MOE_TM_LIST or anything else before step 3 says it is safe. The user's instruction was explicit:
"如果本来也是搜索范围，不能删掉，我们先求全" -- if it is search range, it does not get deleted, completeness
first. I proposed deleting before measuring and was corrected; do not repeat it.

Note the MoE side today generates every combination and lets moe_ok<> compile the illegal ones to empty
functions, while the emitter filters before generating. So a correct migration should REDUCE compile volume
without touching coverage -- if it does not, something in step 3 is being missed.

Not in scope, though the user raised it and it is real: dense has no split-K while MoE does, and
fpA_intB_ppu.cuh already carries a split_k parameter plus a [F4] note about the epilogue builder wanting
ClusterShape. "要有都应该有" -- it should be aligned too, but as a separate change after this one.

Report steps 1-3 with the numbers before doing step 4. Commit and push what you land; I will review.

- **Thread ID:** `019fd6cb-c7a7-7ae2-a301-df546c4cadac`
- **Started / last event:** 2026-08-06 11:18 UTC → 2026-08-07 00:21 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/06/rollout-2026-08-06T19-18-26-019fd6cb-c7a7-7ae2-a301-df546c4cadac.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-08-06_019fd6cb_Align-MoE-s-search-space-with-dense-s-The-user-ask.md](../transcripts/2026-08/2026-08-06_019fd6cb_Align-MoE-s-search-space-with-dense-s-The-user-ask.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Align MoE's search space with dense's. The user asked for this specifically and wants me reviewing rather than implementing.

WHAT I MEASURED TODAY, so you do not repeat it:

  * Pruning is now OPT-IN and off by default (benchmarks/emit_tactic_configs.cpp, pushed). primary/guard is a
    heuristic, not legality: it was dropping 532 of 1164 rows, 46%, and this repository has twice had a
    heuristic hide a measured optimum (the sub-four-warp quarantine hid 65.7% dense; the 1/2/4 compact-A
    whitelist hid capacity 8). `--prune=primary-guard` still narrows for anyone who wants it.
  * dense and grouped spaces are IDENTICAL: 1164 rows each, unpruned, byte-for-byte the same table.
    dense_kernel_exclusion and grouped_kernel_exclusion are both just common_kernel_exclusion.
  * The axes match: emitter emits TM {16,32,64,128,256}, TN {16,32,64,128}, WM {16,32,64} -- the same values as
    _MOE_TM_LIST / _MOE_TN_LIST / _MOE_WM_LIST. The ONE difference is WarpN: _MOE_FORMATS hand-writes a narrower
    per-format subset (q3/q5 pinned to 64, q6 to 32,64) while the emitter DERIVES the same constraint from
    LowDelivery/HighDelivery. So the emitted set should be a superset there, not a subset.
  * benchmarks/lowbit_grouped_configs.inc now exists (unpruned, 1164). Nothing consumes it.

THE CLASSIFICATION I want you to check rather than accept. The variable belongs in the config row only if it
changes the instantiation:

    row fields     TM, TN, TacticTileK, WM, WN, Stages, A_COMPACT_ROWS
    table identity bits/high_bits (the format), ArtifactTileK
    runtime        group size, M, router mode / expert distribution, and split-K's S -- moe_splitk_unit.inc says
                   "the S ladder is a runtime loop inside it, because split-K does not change the instantiation"

If that is wrong anywhere, say so before building on it. In particular _MOE_FORMATS looks like an axis and I
claim it is table identity -- five formats means five emitted tables, not five rows of one.

THE JOB, in this order, and the order is the point:

  1. Emit one unpruned table per format, with bits/high_bits read from quactlize/include/ppu_format_config.inc
     rather than written out again.
  2. Expand _MOE_FORMATS x _MOE_TM_LIST x _MOE_TN_LIST x _MOE_WM_LIST x per-format WarpN x _MOE_STAGES into a row
     set.
  3. SET-DIFFERENCE BOTH WAYS, and report the two numbers. Emitted-minus-product is coverage we gain;
     product-minus-emitted is coverage we would LOSE, and every row in it is either a legality predicate being
     stricter than the hand-written product or an axis the emitter's grid does not reach -- both are findings
     about the space, not about MoE.
  4. ONLY IF product-minus-emitted is empty, wire the MoE bench to the tables and remove the CMake axis lists.

DO NOT delete _MOE_TM_LIST or anything else before step 3 says it is safe. The user's instruction was explicit:
"如果本来也是搜索范围，不能删掉，我们先求全" -- if it is search range, it does not get deleted, completeness
first. I proposed deleting before measuring and was corrected; do not repeat it.

Note the MoE side today generates every combination and lets moe_ok<> compile the illegal ones to empty
functions, while the emitter filters before generating. So a correct migration should REDUCE compile volume
without touching coverage -- if it does not, something in step 3 is being missed.

Not in scope, though the user raised it and it is real: dense has no split-K while MoE does, and
fpA_intB_ppu.cuh already carries a split_k parameter plus a [F4] note about the epilogue builder wanting
ClusterShape. "要有都应该有" -- it should be aligned too, but as a separate change after this one.

Report steps 1-3 with the numbers before doing step 4. Commit and push what you land; I will review.

## Follow-up requests (chronological)

2. (2026-08-07 00:21 UTC) 读 .coord/INBOX.md 的 ## 085(已 push 到 develop,先 git pull)。这条 prompt 是自足的,但 085 有完整细节。 先做一件事:把 `inbox-consumed: 085` 和 wall-clock 时间戳写进 .coord/STATUS.md,**开工前**写,不是做完之后。 ## 撤回 我上一轮(usage-limit 死掉的那轮)给你的 prompt 里说 "dense has no split-K while MoE does",要你去对齐。**反了,作废,不要做。**逐条读出来的: - quactlize/include/fpA_intB_ppu.cuh:127 建的是 GemmUniversal<..., cutlass::gemm::SplitKSerialScheduler> - tests/test_fpA_intB_ppu.cu(活的 target)调 fpa_intb_ppu::filter_and_run,扫 split_k{1,2,4} - 它自己的注释:split_k "does not exist for the grouped ProblemShape -- but it does for the dense one" - moe_splitk_ppu.cuh:18:那个 serial kernel "is dense-only",MoE 才另写了 fp32 的 moe_splitk_reduce.cuh split-K 是 dense 独有,MoE 是绕出来的。 ## 你 STATUS 里的 …
