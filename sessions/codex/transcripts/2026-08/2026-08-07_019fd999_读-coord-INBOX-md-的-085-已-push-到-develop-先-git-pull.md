# 读 .coord/INBOX.md 的 ## 085(已 push 到 develop,先 git pull)。这条 prompt 是自足的,但 085 有完整细节。

先做一件事:把 `inbox-consumed: 085` 和 wall-clock 时间戳写进 .coord/STATUS.md,**开工前**写,不是做完之后。

## 撤回

我上一轮(usage-limit 死掉的那轮)给你的 prompt 里说 "dense has no split-K while MoE does",要你去对齐。**反了,作废,不要做。**逐条读出来的:
- quactlize/include/fpA_intB_ppu.cuh:127 建的是 GemmUniversal<..., cutlass::gemm::SplitKSerialScheduler>
- tests/test_fpA_intB_ppu.cu(活的 target)调 fpa_intb_ppu::filter_and_run,扫 split_k{1,2,4}
- 它自己的注释:split_k "does not exist for the grouped ProblemShape -- but it does for the dense one"
- moe_splitk_ppu.cuh:18:那个 serial kernel "is dense-only",MoE 才另写了 fp32 的 moe_splitk_reduce.cuh

split-K 是 dense 独有,MoE 是绕出来的。

## 你 STATUS 里的三个 blocker

1. optional includes:我修了两个 —— benchmarks/moe_bench_unit.inc 和 benchmarks/moe_splitk_unit.inc(commit 480c870)。C0.5 part 1 给了 9 个主 TU,但主 TU 只有生成的声明,CollectiveMma 全从 per-unit body 出来。剩下 5 个还在,我没逐个编过。
2. dense table hash:重新 emit 了(ba28d75),内容逐字节相同,只有 EMITTER_FNV1A64 变了。
3. test_int1_sweep / pytest:没碰。

## 我越线改的一处(你那半边)

quactlize/include/unfused_weight_dequantize.hpp 的 get_bits_in_quant_type 加了 inline。dense 分片后 291 个 TU 各定义一份,链接报 multiple definition。一个词,不改编不过。有意见直接改回去并告诉我。

其它我改的:moe_bench_unit.inc 用 UNIT_TK 而非 MOE_TK(表的 tactic TileK 是 Q3/Q5=256、Q6/i2=128、i4=64,MOE_TK=64,moe_ok 吃 TK,所以 415 个 unit 里 312 个编成空函数;box 实测 483s→1607s);TacticTableUnits.cmake 的 qz_parse_tactic_xmacro 加了 cmake_policy(SET CMP0007 NEW);build.sh 加了 -DFETCHCONTENT_FULLY_DISCONNECTED=ON。

## 请你做的一件事

跑一遍 full tier,报告还有哪些红的:73/83 现在是多少,剩下的是不是都属于 "predate this work"。

约束:
- 每个子项一个 commit,别攒;push 你 land 的东西。
- git add 只用显式路径。tests/ ci/ benchmarks/ docs/ quactlize/*.py 是我的半边,我的工作树是干净的。
- 不要 git add -A。
- 额度是滚动窗口且 credits 余额为 0,重活可能再撞限。先报增量结果再继续,别一口气跑到死。

- **Thread ID:** `019fd999-7afe-7be2-a2dd-c186ade3b0fb`
- **Started / last event:** 2026-08-07 00:22 UTC → 2026-08-07 00:22 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/07/rollout-2026-08-07T08-22-22-019fd999-7afe-7be2-a2dd-c186ade3b0fb.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "0197f2b5a9425cc01bdcffa89f719f81ed3a266d", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-07 00:22 UTC

读 .coord/INBOX.md 的 ## 085(已 push 到 develop,先 git pull)。这条 prompt 是自足的,但 085 有完整细节。

先做一件事:把 `inbox-consumed: 085` 和 wall-clock 时间戳写进 .coord/STATUS.md,**开工前**写,不是做完之后。

## 撤回

我上一轮(usage-limit 死掉的那轮)给你的 prompt 里说 "dense has no split-K while MoE does",要你去对齐。**反了,作废,不要做。**逐条读出来的:
- quactlize/include/fpA_intB_ppu.cuh:127 建的是 GemmUniversal<..., cutlass::gemm::SplitKSerialScheduler>
- tests/test_fpA_intB_ppu.cu(活的 target)调 fpa_intb_ppu::filter_and_run,扫 split_k{1,2,4}
- 它自己的注释:split_k "does not exist for the grouped ProblemShape -- but it does for the dense one"
- moe_splitk_ppu.cuh:18:那个 serial kernel "is dense-only",MoE 才另写了 fp32 的 moe_splitk_reduce.cuh

split-K 是 dense 独有,MoE 是绕出来的。

## 你 STATUS 里的三个 blocker

1. optional includes:我修了两个 —— benchmarks/moe_bench_unit.inc 和 benchmarks/moe_splitk_unit.inc(commit 480c870)。C0.5 part 1 给了 9 个主 TU,但主 TU 只有生成的声明,CollectiveMma 全从 per-unit body 出来。剩下 5 个还在,我没逐个编过。
2. dense table hash:重新 emit 了(ba28d75),内容逐字节相同,只有 EMITTER_FNV1A64 变了。
3. test_int1_sweep / pytest:没碰。

## 我越线改的一处(你那半边)

quactlize/include/unfused_weight_dequantize.hpp 的 get_bits_in_quant_type 加了 inline。dense 分片后 291 个 TU 各定义一份,链接报 multiple definition。一个词,不改编不过。有意见直接改回去并告诉我。

其它我改的:moe_bench_unit.inc 用 UNIT_TK 而非 MOE_TK(表的 tactic TileK 是 Q3/Q5=256、Q6/i2=128、i4=64,MOE_TK=64,moe_ok 吃 TK,所以 415 个 unit 里 312 个编成空函数;box 实测 483s→1607s);TacticTableUnits.cmake 的 qz_parse_tactic_xmacro 加了 cmake_policy(SET CMP0007 NEW);build.sh 加了 -DFETCHCONTENT_FULLY_DISCONNECTED=ON。

## 请你做的一件事

跑一遍 full tier,报告还有哪些红的:73/83 现在是多少,剩下的是不是都属于 "predate this work"。

约束:
- 每个子项一个 commit,别攒;push 你 land 的东西。
- git add 只用显式路径。tests/ ci/ benchmarks/ docs/ quactlize/*.py 是我的半边,我的工作树是干净的。
- 不要 git add -A。
- 额度是滚动窗口且 credits 余额为 0,重活可能再撞限。先报增量结果再继续,别一口气跑到死。
