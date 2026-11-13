# Resume brief: `git pull --rebase --autostash origin develop` 之后读 `.coord/INBOX.md` 的 `## 094` 和 `## 095`。你那 4 个 commit 还在本地没推,连同下面的修改一起推。inbox-consumed 写成 095。

**先做 094(小),做完把这一轮全部推上去。**

我自己跑了验收,不是照抄你的回报:#52-2、090、089 三条通过(依据写在 094 里)。A3/A8/A9 你拒绝改谓词去掩盖,这个判断我认同。

**#52-1 退回一条**:你去掉"超 HBM 峰值就判没跑"是对的(cache-hot 合法行不该消失),但你删掉的注释自己写着这道网为什么存在 —— bench 曾把一个 6.6 TB/s(峰值 2.77)的 q5 行报成最快。而 **MoE perf bench 没有任何正确性校验**(我 grep 过,verify/golden/mismatch 全无,正确性在独立的 `test_moe_grouped_verify`)。所以"launch 成功但什么都没算"这一类现在**一个网都没有**,只剩一行 warning,verdict 照样会把它排第一。补一条 **cache 状态无关**的判据 —— 我建议 launch 前后对 D 取校验和,用它做排除,超-HBM 那条留作 warning。你若认为 D-checksum 有别的问题,说出来换判据,但不能停在"只警告"。

还有:你说"local tier 4 项红灯都是 `66a5994` 已有的 stale fixture/环境问题" —— **把那 4 项的名字和判定依据写出来**(例如在 `66a5994` 上 checkout 跑同一项也红)。我这边 local_gates 还在跑,会自己核。没有证据的"本来就坏的"不能用。

**然后做 095,但那条只要结论不要代码。** persistent 在 actlize 里是成套现成的(kernel 层 4 个 + 3 个 tile scheduler,含给 MoE 的 `ppu_tile_scheduler_group.hpp`),我们这条路一行没接。095 里问了三个问题:MoE 还是 dense 先做、`MainloopPPUAiu` 与 `MainloopPPUAiuMixedInput` 的接线代价(读出来别推)、persistent 改变 grid 之后 `report()` 里 blk/wav/cta/grid_wrp 这些诊断怎么办。**先只回答这三点并附证据,同意之后再写代码。**

- **Thread ID:** `019fdbd0-38cb-7ed1-bacd-988f070f5866`
- **Started / last event:** 2026-08-07 10:41 UTC → 2026-08-07 11:15 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/07/rollout-2026-08-07T18-41-24-019fdbd0-38cb-7ed1-bacd-988f070f5866.jsonl`
- **Subagents spawned:** 3 (not exported)
- **Git:** `{"commit_hash": "dcf4ceb24ff9b07ef3ba7b2ca429e9e5b0e53137", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-07_019fdbd0_git-pull-rebase-autostash-origin-develop-之后读-coord.md](../transcripts/2026-08/2026-08-07_019fdbd0_git-pull-rebase-autostash-origin-develop-之后读-coord.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

`git pull --rebase --autostash origin develop` 之后读 `.coord/INBOX.md` 的 `## 094` 和 `## 095`。你那 4 个 commit 还在本地没推,连同下面的修改一起推。inbox-consumed 写成 095。

**先做 094(小),做完把这一轮全部推上去。**

我自己跑了验收,不是照抄你的回报:#52-2、090、089 三条通过(依据写在 094 里)。A3/A8/A9 你拒绝改谓词去掩盖,这个判断我认同。

**#52-1 退回一条**:你去掉"超 HBM 峰值就判没跑"是对的(cache-hot 合法行不该消失),但你删掉的注释自己写着这道网为什么存在 —— bench 曾把一个 6.6 TB/s(峰值 2.77)的 q5 行报成最快。而 **MoE perf bench 没有任何正确性校验**(我 grep 过,verify/golden/mismatch 全无,正确性在独立的 `test_moe_grouped_verify`)。所以"launch 成功但什么都没算"这一类现在**一个网都没有**,只剩一行 warning,verdict 照样会把它排第一。补一条 **cache 状态无关**的判据 —— 我建议 launch 前后对 D 取校验和,用它做排除,超-HBM 那条留作 warning。你若认为 D-checksum 有别的问题,说出来换判据,但不能停在"只警告"。

还有:你说"local tier 4 项红灯都是 `66a5994` 已有的 stale fixture/环境问题" —— **把那 4 项的名字和判定依据写出来**(例如在 `66a5994` 上 checkout 跑同一项也红)。我这边 local_gates 还在跑,会自己核。没有证据的"本来就坏的"不能用。

**然后做 095,但那条只要结论不要代码。** persistent 在 actlize 里是成套现成的(kernel 层 4 个 + 3 个 tile scheduler,含给 MoE 的 `ppu_tile_scheduler_group.hpp`),我们这条路一行没接。095 里问了三个问题:MoE 还是 dense 先做、`MainloopPPUAiu` 与 `MainloopPPUAiuMixedInput` 的接线代价(读出来别推)、persistent 改变 grid 之后 `report()` 里 blk/wav/cta/grid_wrp 这些诊断怎么办。**先只回答这三点并附证据,同意之后再写代码。**

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp` ×5
- `/root/marlin_ppu/quactlize/dev/094_moe_unit_probe.cu` ×4
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_moe_bench.cu` ×3
- `/root/marlin_ppu/quactlize/dev/fold_derivation/syntax_baseline/094_moe_unit_probe.cu.txt` ×2
- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×2

## Last assistant conclusions

### 2026-08-07 11:15 UTC

已完成并推送，当前 `develop == origin/develop == f5aad2c`，工作区 clean。095 没写 persistent 代码，`inbox-consumed` 已是 095。

### 094

代码提交 `dc32052`：

- 不直接比较相邻 checksum：不同 tactic 正确地写出相同 D 时也会相等。
- 每个参与排名的 row 计时前把完整 D poison 为 half NaN `0x7f7f`，计时后设备端扫描完整 D。
- 任一 poison 残留（未写/部分写）或固定 fixture 下整块全零都会排除；超 HBM 仍只 warning。
- poison、扫描、两字回读都在计时外。
- `MOE_ACU=1` 跳过 guard，保持单 kernel 采集语义。
- 扫描先做 block reduction，每 row 最多 512 次全局 atomic。

实现见 [lowbit_moe_bench.hpp](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:228) 和 [test_lowbit_moe_bench.cu](/root/marlin_ppu/quactlize/benchmarks/test_lowbit_moe_bench.cu:43)。

验证通过：

- 默认 ScaleZero syntax
- `LOWBIT_QMODE=1` syntax
- 一个真实 i4 generated-unit 实例化：0 accepted noise
- PPU portability

本机没有 PPU SDK/device，因此尚未做目标端运行验证。

### 四项 local tier 红灯证据

在 clean detached `66a5994` worktree 重跑，submodule 固定为 actlize `c48cb105`、cutlass `f94ec46`：

- `gate/l107_moe_router_fixture`：同样失败，调用了已删除的 `minimum_compact_capacity`。属于 stale gate。
- `syntax/test_int1_sweep.cu`：同样是 40 次 `mixed policy: tactic violates ... search-space rules`。看到 096 的“66a 是 0”后我又独立重跑了 clean `66a5994` 和 clean `6b4f927`，两者均 exit 1、同样 40 次；不是本轮未提交修改造成的。
- `pytest/torch op tests`：`66a5994` 同样红；核心 `ppu_backend_cuda` fixture 编译 `ppu_unit_pack.cpp` 时在 NVIDIA stand-in 环境报 `int4/uint4/float4` 未声明。隔离 worktree 因没有主树 `_C.so` 还多出其他失败，所以不能声称完整输出逐字相同。
- `lint/includes the CMake generator writes into generated sources resolve`：`66a5994` 同样误报 `moe_bench_band.inc`；它实际由 CMake 写入生成目录。该 checker 假阳性现已由 `a7fd909` 修复，当前此项通过。

所以准确分类是：两个 stale gate/fixture、一个 stand-in 环境失败、一个 checker 假阳性；此前笼统说“四个都是 stale fixture/环境”不严谨。当前 post-`a7fd909` 的完整 local tier 没有重跑，我不沿用旧的 80/84 总数。

### 095 三点结论

1. **MoE 先，dense 后。** MoE 当前 wrapper 已携带 grouped scheduler 参数和取下一 work 的 helper；dense 仍硬编码 `SplitKSerialScheduler`：[grouped kernel](/root/marlin_ppu/quactlize/quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp:147)、[dense launcher](/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh:112)。

   但不能直接沿用 vendor 默认 grid：它是 `P=min(CU,T)`，即最多一 CTA/CU，[源码](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/kernel/tile_scheduler_params.h:1662)；这条路已有 `grid=72`、3.1% occupancy 的失败记录，[记录](/root/marlin_ppu/quactlize/quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp:195)。首版应限定 `split_k=1`，比较 `P=CU` 与 `P=min(T, CU*B)`，其中 `B` 是该实例化 kernel 的 resident CTA/CU。

2. **不是换一个模板参数；需要 mixed-aware persistent kernel body。** 普通 persistent body 只接 `KernelAiuMultistagePersistent`，并调用普通 `mainloop(accum,gA,gB,...)` 接口：[persistent kernel](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/kernel/ppu_aiu_gemm_persistent.hpp:55)。Mixed mainloop 必须每个 work tile 重新 `load_init()` 出 A/B/S/Z tuple，再走另一套 operator：[mixed mainloop](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:351)。

   因此需要 persistent 循环体，但 MoE 可以局部接在现有 `ppu_aiu_gemm_mixed_input_group.hpp`，不必复制三套 collective 或必然新建整份文件。第一阶段只做非-overlap chaining；overlap-prologue 需要额外重构。

3. **诊断必须拆逻辑工作与物理 launch。**

| 旧字段 | persistent 后应报告 |
|---|---|
| `blk` | `cap_blk/CU=B`，从准确 occupancy API 查询 |
| `wrp/CU` | `cap_wrp/CU=B*W` |
| `cta` | 分成 `tile=T`、`pcta=P` |
| `grid_wrp/CU` | 分成 `work_wrp/CU=T*W/C`、`launch_wrp/CU=P*W/C` |
| `wav` | `eq_work_wav=T/(C*B)`，另报 `slot_fill=P/(C*B)`、`rounds=T/P` |
| 固定 `CU=72` | 使用 runtime `hw_info.cu_count` |

实际 grid 和 occupancy 可分别取自 `Gemm::get_grid_shape(gemm.params())` 与 `Gemm::maximum_active_blocks()`：[adapter](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/device/gemm_universal_adapter.h:250)。

结论：同意后建议实现范围为“MoE、`split_k=1`、non-overlap、resident-CTA grid 轴、同步改 telemetry”；dense 和 overlap 放后续。
