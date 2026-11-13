# Agent instructions for this repository

This repository is a read-only memory pack exported from Codex and Claude Code on the AutoDL PPU box
(`connect.weste.seetacloud.com`, home `/root`). It is not a code project. Do not modify the exported
content unless the user asks.

- To find or resume earlier work, use the `codex-history` skill (`.devin/skills/codex-history/SKILL.md`).
- Start from `sessions/codex/INDEX.md` or `sessions/codex/index.jsonl`, then read the thread's resume
  brief under `sessions/codex/resume/`. Open transcripts only around grep hits; some are larger than 20 MB.
- Domain skills from Codex and Claude Code live in `.devin/skills/` (PPU cold GEMV tuning, PPU17/Hopper
  porting, PPU CUTLASS mixed GEMM, PPU PTX, Codex collaboration).
- Project-level AGENTS.md / CLAUDE.md / SKILL.md files are mirrored at their original absolute paths under
  `project-rules/`. See `project-rules/INDEX.md`.
- `raw/` holds Git LFS archives of the original data. Do not extract them unless the user asks.
- Paths such as `/root/marlin_ppu/quactlize` refer to the remote box. Verify the current state there before
  acting on anything recorded in history.
- Secrets were redacted as `<REDACTED...>`. Never try to reconstruct them.
