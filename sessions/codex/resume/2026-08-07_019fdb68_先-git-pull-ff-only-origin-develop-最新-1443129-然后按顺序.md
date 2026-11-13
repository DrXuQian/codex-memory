# Resume brief: 先 `git pull --ff-only origin develop`(最新 1443129),然后按顺序做,每个 sub-item 一个 commit,`git add` 只用显式路径。开始前把 .coord/STATUS.md 的 inbox-consumed 写成 092。

**你之前 blocked 的三处我已经全部解开了(commit `592536d`)**,STATUS 里那行 blocked-on 已经过期:

1. `ci/check_dense_tactic_table.py` 现在从重建命令行解析并**重放 `--m-max`**。我逐张跑过,**十一张表全绿**(6 full + 你那 5 张 decode)。
2. `dev/fold_derivation/gen_moe_units_check.sh` 的行正则改成不数字段个数,期望的 unit 名带上了 `_bc`。现在 **1119 units / 4380 rows,dispatcher 1119/1119**。
3. `benchmarks/bench_samples.hpp` 的 `Sample` 加了 `bc` 和 `bc_eff`(三种记录 a/s/x 都写);`benchmarks/analyse.py` 的 `CONFIG_KEYS` 加了 `bc`、没加 `bc_eff`(后者是导出量,不该进 key)。

所以:

**① 先提交并推送 088 的 ②**(五张 m-max=3 decode 表 + CMake 双 target)。跑完十一张表的门禁再提交。

**② 然后做 INBOX 092 —— 这是用户在 box 上实测撞到的回归,优先级最高。** 你把 `bc%d->%d` 加到 shape 串尾部之后,任何带 stage 的 `MOE_ONLY`(比如 `"i4 64x128:64 w64x16 s6"`)都选不中任何行,259 个 unit 一个都不跑,而行确实在表里。机制和建议的修法都写在 092 里。连带把那个"filter 完全等于某个 tag 就必须选中至少一行"的检查加上,并把 `no legal row ran (filtered, or MOE_ONLY excluded it)` 拆成两句 —— 现在它把"被过滤"和"非法"说成同一件事。

**③ 092 里还有两条是我写的、归我,但文件在你手上,你顺手做掉更省事**:`test_lowbit_moe_bench.cu:265` 的 banner 和 `lowbit_moe_bench.hpp:293` 的注释还在讲 padded A / "traffic is LOCKED",而 `dfl` 的 A 项今天已经换成 `total*K*2`,那段文字描述的是一个不存在的实现。另外用户主诉**打印太多**:结果前有 ~25 行前言,数据只有一行 —— 把解释性段落收到 `MOE_VERBOSE=1` 后面,默认只留身份行、每候选行、verdict。

之后还有 INBOX 089(dense 只有一张 bits=4 表)、090(PPU_A_PACK 声明 R<=16 实际 R>8 就撞,我已经把 gate 写好推了:`ci/check_a_pack_bound.py`,它现在是红的且理应是红的)、091 里转述的 #52 五个确定性错误。**先别开这三个**,做完 ①②③ 回报,我再排序。

- **Thread ID:** `019fdb68-3ee2-7062-8a9d-c9abc17973bd`
- **Started / last event:** 2026-08-07 08:47 UTC → 2026-08-07 09:13 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/07/rollout-2026-08-07T16-47-49-019fdb68-3ee2-7062-8a9d-c9abc17973bd.jsonl`
- **Subagents spawned:** 3 (not exported)
- **Git:** `{"commit_hash": "14431292ac672eee2a4bd2598d95d03a5971ffa7", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-07_019fdb68_先-git-pull-ff-only-origin-develop-最新-1443129-然后按顺序.md](../transcripts/2026-08/2026-08-07_019fdb68_先-git-pull-ff-only-origin-develop-最新-1443129-然后按顺序.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

先 `git pull --ff-only origin develop`(最新 1443129),然后按顺序做,每个 sub-item 一个 commit,`git add` 只用显式路径。开始前把 .coord/STATUS.md 的 inbox-consumed 写成 092。

**你之前 blocked 的三处我已经全部解开了(commit `592536d`)**,STATUS 里那行 blocked-on 已经过期:

1. `ci/check_dense_tactic_table.py` 现在从重建命令行解析并**重放 `--m-max`**。我逐张跑过,**十一张表全绿**(6 full + 你那 5 张 decode)。
2. `dev/fold_derivation/gen_moe_units_check.sh` 的行正则改成不数字段个数,期望的 unit 名带上了 `_bc`。现在 **1119 units / 4380 rows,dispatcher 1119/1119**。
3. `benchmarks/bench_samples.hpp` 的 `Sample` 加了 `bc` 和 `bc_eff`(三种记录 a/s/x 都写);`benchmarks/analyse.py` 的 `CONFIG_KEYS` 加了 `bc`、没加 `bc_eff`(后者是导出量,不该进 key)。

所以:

**① 先提交并推送 088 的 ②**(五张 m-max=3 decode 表 + CMake 双 target)。跑完十一张表的门禁再提交。

**② 然后做 INBOX 092 —— 这是用户在 box 上实测撞到的回归,优先级最高。** 你把 `bc%d->%d` 加到 shape 串尾部之后,任何带 stage 的 `MOE_ONLY`(比如 `"i4 64x128:64 w64x16 s6"`)都选不中任何行,259 个 unit 一个都不跑,而行确实在表里。机制和建议的修法都写在 092 里。连带把那个"filter 完全等于某个 tag 就必须选中至少一行"的检查加上,并把 `no legal row ran (filtered, or MOE_ONLY excluded it)` 拆成两句 —— 现在它把"被过滤"和"非法"说成同一件事。

**③ 092 里还有两条是我写的、归我,但文件在你手上,你顺手做掉更省事**:`test_lowbit_moe_bench.cu:265` 的 banner 和 `lowbit_moe_bench.hpp:293` 的注释还在讲 padded A / "traffic is LOCKED",而 `dfl` 的 A 项今天已经换成 `total*K*2`,那段文字描述的是一个不存在的实现。另外用户主诉**打印太多**:结果前有 ~25 行前言,数据只有一行 —— 把解释性段落收到 `MOE_VERBOSE=1` 后面,默认只留身份行、每候选行、verdict。

之后还有 INBOX 089(dense 只有一张 bits=4 表)、090(PPU_A_PACK 声明 R<=16 实际 R>8 就撞,我已经把 gate 写好推了:`ci/check_a_pack_bound.py`,它现在是红的且理应是红的)、091 里转述的 #52 五个确定性错误。**先别开这三个**,做完 ①②③ 回报,我再排序。

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp` ×8
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_moe_bench.cu` ×3
- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×2
- `/root/marlin_ppu/quactlize/benchmarks/bench_select.hpp` ×2
- `/root/marlin_ppu/quactlize/benchmarks/analyse.py` ×2
- `/root/marlin_ppu/quactlize/tests/test_bench_selection.py` ×2
- `/root/marlin_ppu/quactlize/benchmarks/moe_only_filter.hpp` ×1
- `/root/marlin_ppu/quactlize/ci/local_gates.py` ×1
- `/root/marlin_ppu/quactlize/tests/test_moe_only_filter.py` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/gen_stub/moe_bench_band.inc` ×1
- `/root/marlin_ppu/quactlize/benchmarks/xcheck_select.cpp` ×1

## Last assistant conclusions

### 2026-08-07 09:13 UTC

已完成并推送到 `origin/develop`，远端与本地均为 `d1f4b16`。

提交顺序：

- `c985fa2`：5 张 `m-max=3` decode 表、full/decode 双 target。
- `6b9ee48`：补齐 088 的 `bc`/`bc_eff` JSONL 契约及分析器交叉检查。
- `967e525`：修复带 stage 的 `MOE_ONLY`；增加 exact-tag 门禁、区分未匹配/非法/未运行，空匹配返回非零。
- `d1f4b16`：修正文案；默认只保留身份、候选、verdict，解释性输出改由 `MOE_VERBOSE=1` 开启。

验证全绿：

- 11/11 张 tactic 表精确重建。
- full：1119 units / 4380 rows，dispatcher 1119/1119；decode：80 units。
- exact/stage-bearing `MOE_ONLY` gate。
- MoE bench syntax、overlay、PPU portability。
- analyser self-test、selection 与 bench-floor 测试。

`.coord/STATUS.md` 已更新为 `inbox-consumed: 092`、`blocked-on: none`。当前仅 `.coord/BOX.md` 与 `.coord/STATUS.md` 保持未提交；代码工作区干净。089/090/091 未展开。
