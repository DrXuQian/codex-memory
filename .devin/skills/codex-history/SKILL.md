---
name: codex-history
description: Search and resume past Codex / Claude Code work exported from the AutoDL PPU box (quactlize, marlin_ppu, SageAttention int8, llama.cpp PPU backend, KDA, Strata, FlashInfer/flare). Use when the user mentions earlier Codex work, asks to "resume"/"continue" an old thread, or needs prior decisions, measurements, or commands.
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
---

You have a read-only knowledge pack exported from Codex and Claude Code. Its root is the repository that contains this skill (the directory holding `AGENTS.md`, `sessions/`, `history/`). If this skill was installed globally, the root is recorded on the next line:

PACK_ROOT: {{PACK_ROOT}}

## Layout

| Path | What it is |
|---|---|
| `sessions/codex/INDEX.md` | One row per Codex main thread (newest first): title, cwd, user-turn count, links |
| `sessions/codex/index.jsonl` | Same index as JSON lines (`id`, `title`, `start`, `end`, `cwd`, `model`, `user_turns`, `transcript`, `resume`) |
| `sessions/codex/resume/*.md` | Resume briefs: metadata, original request, every follow-up request, files edited, last conclusions |
| `sessions/codex/transcripts/YYYY-MM/*.md` | Full user/assistant dialogue; tool calls collapsed to one line each; no tool output, no reasoning |
| `sessions/claude/` | Same structure for Claude Code sessions |
| `history/codex-prompt-history.md` | Every prompt typed into Codex, grouped by session |
| `project-rules/root/...` | AGENTS.md / CLAUDE.md / project SKILL.md files from the box, at their original absolute paths |
| `codex-config/` | Codex `config.toml` and approved command rules |

## Workflow

1. Locate candidates: grep `sessions/codex/index.jsonl` (and `sessions/claude/INDEX.md`) for keywords, the working directory, a date, or a thread id prefix. Titles are often Chinese; also grep `history/codex-prompt-history.md` for the user's own wording.
2. Read the resume brief first. It is small and contains the request chain and the final state.
3. Open the transcript only for specifics. Transcripts can be 20+ MB: grep for the term and read a bounded line range around the hit instead of reading the whole file.
4. When the work touches a repository, check `project-rules/` for the AGENTS.md / CLAUDE.md that governed it.
5. Report what you found with thread id, date, and file path so the user can follow up.

## Resuming a thread

- Treat the brief + transcript as history, not ground truth. Before acting, verify the current branch, commits, and files on the machine you are working on; paths like `/root/...` refer to the AutoDL box.
- Codex's encrypted reasoning, compacted context, and subagent threads were not exported. If a detail is missing, say so instead of guessing.
- Secrets were redacted (`<REDACTED...>`). Ask the user for credentials when needed; never try to recover them.
