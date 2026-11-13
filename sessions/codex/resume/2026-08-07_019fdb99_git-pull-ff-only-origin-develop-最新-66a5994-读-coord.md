# Resume brief: `git pull --ff-only origin develop`(最新 `66a5994`),读 `.coord/INBOX.md` 的 `## 093`,按里面给的顺序做 1→2→3→4。开始前把 STATUS 的 inbox-consumed 写成 093。一个 sub-item 一个 commit,`git add` 只用显式路径。

093 里有三条新事实会改变判断依据,别跳过:C1/D4 两个 BACKTEST 锚点已在 box 上精确复现(卡的问题排除);我**撤回**了"每次 timed call 有 723us 固定开销"那个推断(拟合用错了自变量,已在 093 里说明为什么),你 review 第 8 条本身仍成立但那个量级是我编的、不要引用;M=1 decode 实测 `S=19.9%`。

顺序:

1. **#52-1 `moe_row_ran()` 会把合法行判成 DID NOT RUN** —— 唯一会让数据消失的。
2. **#52-2 `sb` 对 ScaleOnly 多算一倍**,连带 `ceil(K/gs)` 和 `dce` 还留在 `ntile*a_pad`。
3. **INBOX 090 `PPU_A_PACK` 的 R 界**(gate 已就位:`ci/check_a_pack_bound.py`,现在红着)。
4. **INBOX 089 dense 分格式表**。

做完 1 和 2 先回报一次,那两条直接挡着下一次全格式扫。

另外用户明确要求:**后面要把 q3/q5/q6/i2 全部放开扫**,不能只扫 i4。所以做 1、2 的时候顺手确认一件事并在回报里写清楚 —— 现在全格式一起编、TileK 和 bc 都进了行字段之后,full 表是 1119 units、decode 表 80 units,`MOE_CORES=192` 下 full 要 6 波编译。**如果一次全格式扫在编译时间上不可行,那本身是要解决的问题(不是让用户只扫 i4 的理由)**,给我一个可执行的方案:是靠 #29(并行 build)、还是 decode/full 分开扫、还是别的。不要自己替用户把格式砍掉。

- **Thread ID:** `019fdb99-5c3c-7e31-8c0f-b947ebed4425`
- **Started / last event:** 2026-08-07 09:41 UTC → 2026-08-07 10:32 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/07/rollout-2026-08-07T17-41-28-019fdb99-5c3c-7e31-8c0f-b947ebed4425.jsonl`
- **Subagents spawned:** 6 (not exported)
- **Git:** `{"commit_hash": "66a5994ae024341c0f07cde90b8d8f80cd34ce93", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-07_019fdb99_git-pull-ff-only-origin-develop-最新-66a5994-读-coord.md](../transcripts/2026-08/2026-08-07_019fdb99_git-pull-ff-only-origin-develop-最新-66a5994-读-coord.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

`git pull --ff-only origin develop`(最新 `66a5994`),读 `.coord/INBOX.md` 的 `## 093`,按里面给的顺序做 1→2→3→4。开始前把 STATUS 的 inbox-consumed 写成 093。一个 sub-item 一个 commit,`git add` 只用显式路径。

093 里有三条新事实会改变判断依据,别跳过:C1/D4 两个 BACKTEST 锚点已在 box 上精确复现(卡的问题排除);我**撤回**了"每次 timed call 有 723us 固定开销"那个推断(拟合用错了自变量,已在 093 里说明为什么),你 review 第 8 条本身仍成立但那个量级是我编的、不要引用;M=1 decode 实测 `S=19.9%`。

顺序:

1. **#52-1 `moe_row_ran()` 会把合法行判成 DID NOT RUN** —— 唯一会让数据消失的。
2. **#52-2 `sb` 对 ScaleOnly 多算一倍**,连带 `ceil(K/gs)` 和 `dce` 还留在 `ntile*a_pad`。
3. **INBOX 090 `PPU_A_PACK` 的 R 界**(gate 已就位:`ci/check_a_pack_bound.py`,现在红着)。
4. **INBOX 089 dense 分格式表**。

做完 1 和 2 先回报一次,那两条直接挡着下一次全格式扫。

另外用户明确要求:**后面要把 q3/q5/q6/i2 全部放开扫**,不能只扫 i4。所以做 1、2 的时候顺手确认一件事并在回报里写清楚 —— 现在全格式一起编、TileK 和 bc 都进了行字段之后,full 表是 1119 units、decode 表 80 units,`MOE_CORES=192` 下 full 要 6 波编译。**如果一次全格式扫在编译时间上不可行,那本身是要解决的问题(不是让用户只扫 i4 的理由)**,给我一个可执行的方案:是靠 #29(并行 build)、还是 decode/full 分开扫、还是别的。不要自己替用户把格式砍掉。

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/ci/local_gates.py` ×6
- `/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp` ×5
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu` ×3
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_moe_bench.cu` ×2
- `/root/marlin_ppu/quactlize/build.sh` ×2
- `/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in` ×2
- `/root/marlin_ppu/quactlize/benchmarks/emit_tactic_configs.cpp` ×2
- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/detail/ppu_a_pack.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp` ×1
- `/root/marlin_ppu/quactlize/ci/check_a_pack_bound.py` ×1
- `/root/marlin_ppu/quactlize/ci/check_backtest_configs.py` ×1
- `/root/marlin_ppu/quactlize/ci/check_dense_unit_generator.py` ×1

## Last assistant conclusions

### 2026-08-07 10:32 UTC

已按 1→2→3→4 完成，四个 sub-item 各一个 commit：

- `6b4f927` — 修复 `moe_row_ran()`：缓存命中导致的超 HBM 只警告，不再丢行。
- `519f465` — 修复 ScaleOnly `sb`、`ceil(K/gs)` 和 `dce` 的 A 流量。
- `ca7e7aa` — 将 `PPU_A_PACK` 真实边界收紧为 `1 <= R <= 8`。
- `c776d98` — 增加 dense i1/i2/i4 分格式表及完整门禁。

关键结果：

- M=1 原 `S=19.9%` 按新公式回算约为 `11.05%`；这不是新实测，需 box 重测后才能作为新基线。
- 撤回的固定开销推断没有作为判断依据。
- `PPU_A_PACK` gate：R=1、R=8 编译成功，R=9 在公开边界拒绝。
- dense/grouped 谓词没有分叉。i2 当前是 `1270 rows = 635 tactics × 2 bc`；默认按 bc 分组后为 318 个编译 unit。
- BACKTEST 现在是 `8 reachable / 3 missing / 5 unparsed / 0 NO TABLE`。A2、A4 已可达；A3/A8/A9 仍因历史 artifact TileK=64 与当前 canonical i1=256、i2=128 不同而缺失，不能靠改谓词掩盖。若要恢复这三条，需要把 artifact TileK 正式提升为表/build 维度。

全格式扫描选择“并行 build + decode/full 分开”，不删格式：

```bash
PPU_BUILD_DIR=build_ppu_moe_decode MOE_CORES=192 JOBS=192 \
  TARGET=test_lowbit_moe_decode_bench ./build.sh

PPU_BUILD_DIR=build_ppu_moe_full MOE_CORES=192 JOBS=192 \
  TARGET=test_lowbit_moe_bench ./build.sh
```

不要设置 `MOE_FORMATS`，因此 Q3/Q5/Q6/i2/i4 全部保留。当前 decode 为 80 units，full 为 1119 units；192 并发下 full 是 6 波。若 box 实测编译时间仍不可接受，下一步是约 6 shapes/TU 的自适应 batching，将 full 压到约 187 TUs、一波完成，而不是退回 i4-only。

定向门禁全部通过，包括三种 dense 语法、13 张表精确再生、uint1/uint2 build dry-run 和 dense unit generator。完整 local tier 为 80/84；四项红灯均来自 `66a5994` 已有的 stale fixture/环境问题，与这四个提交无关。

当前 `develop` 比 `origin/develop` ahead 4，未推送。工作树只剩原有协调文件改动；`.coord/STATUS.md` 的 `inbox-consumed` 已是 `093`。
