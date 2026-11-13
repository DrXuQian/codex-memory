# Resume brief: 读 /root/marlin_ppu/quactlize/.coord/INBOX.md 的 `## 088`,按里面的顺序做 ① 和 ②。开始前先把 .coord/STATUS.md 的 inbox-consumed 写成 088。每个 sub-item 一个 commit,推到 origin/develop。

分工提醒:benchmarks/ ci/ docs/ tools/ pyproject.toml quactlize/*.py 是 claude 的,但这次 088 明确把 emit_tactic_configs.cpp / TacticTableUnits.cmake / CMakeLists.txt.in / 两个 bench 的改动交给你 —— 我不会同时改这些文件。git add 只用显式路径,不要 -A。

先跑 `git pull --ff-only origin develop`,最新是 `841ee08` 之后的 INBOX 088 那个 commit。

- **Thread ID:** `019fdb28-8da7-75a3-8629-ef56b42107c3`
- **Started / last event:** 2026-08-07 07:38 UTC → 2026-08-07 08:18 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/07/rollout-2026-08-07T15-38-15-019fdb28-8da7-75a3-8629-ef56b42107c3.jsonl`
- **Subagents spawned:** 6 (not exported)
- **Git:** `{"commit_hash": "c404de8ea19c2896d8b7e858fc7097b790d72d1f", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-07_019fdb28_读-root-marlin_ppu-quactlize-coord-INBOX-md-的-088-按.md](../transcripts/2026-08/2026-08-07_019fdb28_读-root-marlin_ppu-quactlize-coord-INBOX-md-的-088-按.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

读 /root/marlin_ppu/quactlize/.coord/INBOX.md 的 `## 088`,按里面的顺序做 ① 和 ②。开始前先把 .coord/STATUS.md 的 inbox-consumed 写成 088。每个 sub-item 一个 commit,推到 origin/develop。

分工提醒:benchmarks/ ci/ docs/ tools/ pyproject.toml quactlize/*.py 是 claude 的,但这次 088 明确把 emit_tactic_configs.cpp / TacticTableUnits.cmake / CMakeLists.txt.in / 两个 bench 的改动交给你 —— 我不会同时改这些文件。git add 只用显式路径,不要 -A。

先跑 `git pull --ff-only origin develop`,最新是 `841ee08` 之后的 INBOX 088 那个 commit。

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×5
- `/root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in` ×5
- `/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp` ×3
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_tactic_space.hpp` ×2
- `/root/marlin_ppu/quactlize/benchmarks/emit_tactic_configs.cpp` ×2
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu` ×2
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_moe_bench.cu` ×2
- `/root/marlin_ppu/quactlize/quactlize/csrc/TacticTableUnits.cmake` ×1
- `/root/marlin_ppu/quactlize/benchmarks/lowbit_dense_unit.inc` ×1
- `/root/marlin_ppu/quactlize/benchmarks/moe_bench_unit.inc` ×1
- `/root/marlin_ppu/quactlize/.coord/BOX.md` ×1

## Last assistant conclusions

### 2026-08-07 08:18 UTC

① 已完成并推送：`1a3f097 Make PPU_B_CHUNK a tactic row axis`。

② 已在本地实现并验证：

- full 表保持完整；新增五张 `m-max=3` decode 表。
- full 1119 units，decode 80 units。
- T=1/2/4/64 实际 Mmax=1/2/3/12；decode guard 检查实际路由分布。
- CMake 双 target、独立 main 路径、前端语法和代表性 Q3 bc1 unit 均通过。
- 六张原表 provenance gate 全绿；五张 decode 表手工精确重建一致。

尚未提交②：Claude 所属的 `ci/check_dense_tactic_table.py` 不重放 `--m-max`，会错误地把 46 行 Q3 decode 表重建成 404 行 full 表。JSONL 也缺少 `PPU_B_CHUNK` 身份字段。

请让 Claude 补这些 gate/JSONL 改动，或明确授权我跨 ownership 修改；之后我会跑完十一张表门禁，单独提交②并推送。
