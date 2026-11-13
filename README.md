# codex-memory

从 AutoDL PPU 机器（`/root`）导出的 Codex / Claude Code 记忆、历史和 skills，已转换成 Devin 可以直接读取的格式。

## 内容

| 路径 | 内容 |
|---|---|
| `.devin/skills/` | Devin skills：5 个原有 skill（Codex: `ppu-cold-gemv-tuning`, `ppu17-hopper-porting`；Claude: `codex-collaboration`, `ppu-cutlass-mixed-gemm`, `ppu-ptx`），以及新增的 `codex-history`（用来检索和续接历史） |
| `AGENTS.md` | 在本仓库里启动 Devin 时自动加载的规则 |
| `sessions/codex/INDEX.md` / `index.jsonl` | 114 个 Codex 主线程的索引（subagent 线程不导出） |
| `sessions/codex/resume/` | 每个线程一份 resume brief：原始需求、所有后续需求、改过的文件、最后结论 |
| `sessions/codex/transcripts/` | 完整的 user/assistant 对话；工具调用压缩成一行，不含工具输出和加密 reasoning |
| `sessions/claude/` | 2 个 Claude Code 会话，结构同上 |
| `history/` | Codex / Claude 中输入过的全部 prompt |
| `project-rules/` | 服务器上各项目的 AGENTS.md / CLAUDE.md / SKILL.md（已去重，按原绝对路径存放） |
| `codex-config/` | Codex 的 `config.toml` 和命令白名单 `default.rules` |
| `raw/`（Git LFS） | 原始数据：主线程 rollout jsonl（917MB，拆成 3 个分包）以及 config/skills/sqlite 快照/Claude 数据（122MB） |
| `tools/` | 转换脚本、安装脚本、原始数据还原脚本 |

Codex 自带的 memory 数据库（`memories_1.sqlite`）本来就是空的，所以"记忆"实际上来自 skills、项目 AGENTS.md 和会话历史。
文本内容里的密码、token、JWT 已替换为 `<REDACTED...>`；**`raw/` 里的原始数据没有脱敏**。

## 在 Devin 中使用

**方式 1：在本仓库里打开 Devin（不用安装）**

```bash
git clone https://github.com/<you>/<repo>.git && cd <repo>    # 不需要原始数据时，用 GIT_LFS_SKIP_SMUDGE=1 跳过 LFS 下载
devin
```

Devin 会自动加载 `AGENTS.md` 和 `.devin/skills/*`。然后可以直接问：

- `/codex-history 找一下 Strata 适配 PPU 的线程，告诉我停在哪一步`
- `用 codex-history 找 K-pack4 grouped dequant 的最终结论和改过的文件`
- `读 sessions/codex/resume/2026-11-06_01a1aebf_适配-Strata-到-PPU.md，然后去 /root/... 继续这个任务`

**方式 2：安装为全局 skill（任何目录都能用）**

```powershell
powershell -ExecutionPolicy Bypass -File tools\install-devin.ps1     # Windows，装到 %APPDATA%\devin\skills
```
```bash
bash tools/install-devin.sh                                          # Linux / macOS / Git Bash，装到 ~/.config/devin/skills
```

安装脚本会把本仓库的路径写进 `codex-history`，这样在任何项目里都能 `/codex-history ...`。

**方式 3：放到服务器上，接着在原项目里干活**

把本仓库 clone 到 AutoDL 机器上，执行 `bash tools/install-devin.sh`，然后在原项目目录（例如 `/root/marlin_ppu/quactlize`）启动 Devin。
这样项目里的 AGENTS.md / CLAUDE.md 会被原生加载，`codex-history` 也能读到历史。Devin 本身就会读取 `~/.codex/skills` 和 `.claude/skills`，所以服务器上原来的 skill 不需要转换。

> Devin 不能直接导入 Codex 的 rollout 做原生 `devin --resume`（`devin migrate` 只支持 Windsurf 的 hooks/workflows）。
> 续接的方式是：用 resume brief 加 transcript 开一个新的 Devin 会话。之后这个会话就可以用 `devin -r <id>` 正常 resume。

## 还原原始数据

```bash
git lfs pull --include "raw/*"
bash tools/restore-raw.sh     # 校验 SHA256，合并分包，解压到 restore/root/
```

## 重新生成

在服务器上执行 `python3 tools/convert_codex_to_devin.py`（脚本里写死了 `/root/autodl-tmp/codex-export` 下的路径，需要先准备 `db/` 快照和 `main_sessions.list`）。
