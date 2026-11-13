# Resume brief: Resume kernel work on /root/marlin_ppu/quactlize (branch `develop`). Your previous session ended after heartbeat 082. THREE INBOX ITEMS ARE UNREAD — your STATUS.md still says `inbox-consumed: 014`.

FIRST: `git pull --recurse-submodules`, then read `.coord/INBOX.md` items **015, 016 and 017**. Also re-read `.coord/PROTOCOL.md` if you need it. Then overwrite `.coord/STATUS.md` with `inbox-consumed: 017` and keep it current at every checkpoint — Claude has no way to tell "working" from "idle" except that file and your heartbeat log at /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log. Append numbered heartbeats there every few minutes.

WHAT THE THREE ITEMS SAY, in short:

**015** — Claude corrected l103 (it hardcoded `tuple<int4b_t,half,half>` for every format, so fmt2 reported Q2_K ACTIVE while instantiating a Q4 weight — your 079 diagnosis). It now derives types AND tactic per format and is registered once per format; all five compile and activate. ONE GAP LEFT FOR YOU: the gate reads `Mainloop::PackedUnit::kUnitBytes` and gets 14 (Q3) / 18 (Q6) — the per-superblock size — while your 080 says the COPYABLE unit traits are 16/20/28/36. So the gate does NOT check the PAIRING, which is the one thing Q3/Q6 newly required. Tell Claude which trait/member exposes the copyable/paired size and he will assert on it, or say the check belongs in a gate of yours. Do not let him guess a member name.

**016 + 017 — THE MAIN WORK, approved by the user.** Weights exist once in HBM, so kernels we switch between at run time must read the same bytes. Three arrangements exist today:
    A raw GGUF blocks — DEQUANT_FIRST and FULLY_QUANTIZED's two GEMVs
    B code planes + PACKED scale units — FULLY_QUANTIZED dense/grouped
    C code planes + fp16 scale/zero planes — SCALE_FIRST, all four shapes
B and C already share their WEIGHT bytes; they differ ONLY in the scale channel. So C stops being a stored arrangement and becomes a derivation of B into a workspace, and a GEMV/MoE-GEMV that reads the merged BC removes A from residency too. This drops the offline-format debt from fifteen (qtype, layout) pairs to five.

YOURS (kernels):
  1. **dequant-scale FROM THE PACKED UNIT** — today's prepass goes raw → fp16 planes; the merge needs packed unit → fp16 scale/zero planes. This is also the standing entry requirement (INBOX 004): every format owes dequant-all AND dequant-scale, and after the merge BC *is* the format.
  2. **GEMV and MoE-GEMV on BC** — the CUDA-core decode path reads raw blocks today.

MEASURE THIS FIRST, because it can invalidate the shape of everything after it: **does the GEMV lose anything reading placed code planes instead of raw blocks?** The placement exists for the AIU's 32-byte delivery and the GEMV is CUDA-core, so it may not want that arrangement at all. If it costs measurably, "A stays resident for decode" is a legitimate answer — two arrangements with a reason rather than three by accident — and the user should get that trade explicitly rather than have it absorbed. Report the number either way.

BUILD NOW, SWITCH LATER: write and locally gate the pieces, but do NOT repoint `prepare_scale_first`'s producer at BC until the five FULLY_QUANTIZED cells have passed their ppu001 oracles. B is unproven on the device; moving C behind it would make any later failure ambiguous between the merge and its target.

CLAUDE OWNS the routes, oracles and scaffolding half (tests/, ci/, benchmarks/, docs/, pyproject.toml, quactlize/*.py) — request changes there in the INBOX rather than editing. He will re-point the SCALE_FIRST oracles when you switch, and has flagged that changing the producer does not automatically carry those cells' VALIDATED evidence over.

Nothing else is blocked on you: the 9 remaining matrix cells are PARTIAL only for want of a ppu001 run, which is the user's to trigger. Commit and push as you go, no Co-Authored-By trailer.

- **Thread ID:** `019fc758-5e8c-79a0-8ff7-ffc0747a947a`
- **Started / last event:** 2026-08-03 11:18 UTC → 2026-08-03 12:30 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T19-18-05-019fc758-5e8c-79a0-8ff7-ffc0747a947a.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "8ab06a6725f4e401c097059bdfcb701b19339f2c", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-03_019fc758_Resume-kernel-work-on-root-marlin_ppu-quactlize-br.md](../transcripts/2026-08/2026-08-03_019fc758_Resume-kernel-work-on-root-marlin_ppu-quactlize-br.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Resume kernel work on /root/marlin_ppu/quactlize (branch `develop`). Your previous session ended after heartbeat 082. THREE INBOX ITEMS ARE UNREAD — your STATUS.md still says `inbox-consumed: 014`.

FIRST: `git pull --recurse-submodules`, then read `.coord/INBOX.md` items **015, 016 and 017**. Also re-read `.coord/PROTOCOL.md` if you need it. Then overwrite `.coord/STATUS.md` with `inbox-consumed: 017` and keep it current at every checkpoint — Claude has no way to tell "working" from "idle" except that file and your heartbeat log at /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log. Append numbered heartbeats there every few minutes.

WHAT THE THREE ITEMS SAY, in short:

**015** — Claude corrected l103 (it hardcoded `tuple<int4b_t,half,half>` for every format, so fmt2 reported Q2_K ACTIVE while instantiating a Q4 weight — your 079 diagnosis). It now derives types AND tactic per format and is registered once per format; all five compile and activate. ONE GAP LEFT FOR YOU: the gate reads `Mainloop::PackedUnit::kUnitBytes` and gets 14 (Q3) / 18 (Q6) — the per-superblock size — while your 080 says the COPYABLE unit traits are 16/20/28/36. So the gate does NOT check the PAIRING, which is the one thing Q3/Q6 newly required. Tell Claude which trait/member exposes the copyable/paired size and he will assert on it, or say the check belongs in a gate of yours. Do not let him guess a member name.

**016 + 017 — THE MAIN WORK, approved by the user.** Weights exist once in HBM, so kernels we switch between at run time must read the same bytes. Three arrangements exist today:
    A raw GGUF blocks — DEQUANT_FIRST and FULLY_QUANTIZED's two GEMVs
    B code planes + PACKED scale units — FULLY_QUANTIZED dense/grouped
    C code planes + fp16 scale/zero planes — SCALE_FIRST, all four shapes
B and C already share their WEIGHT bytes; they differ ONLY in the scale channel. So C stops being a stored arrangement and becomes a derivation of B into a workspace, and a GEMV/MoE-GEMV that reads the merged BC removes A from residency too. This drops the offline-format debt from fifteen (qtype, layout) pairs to five.

YOURS (kernels):
  1. **dequant-scale FROM THE PACKED UNIT** — today's prepass goes raw → fp16 planes; the merge needs packed unit → fp16 scale/zero planes. This is also the standing entry requirement (INBOX 004): every format owes dequant-all AND dequant-scale, and after the merge BC *is* the format.
  2. **GEMV and MoE-GEMV on BC** — the CUDA-core decode path reads raw blocks today.

MEASURE THIS FIRST, because it can invalidate the shape of everything after it: **does the GEMV lose anything reading placed code planes instead of raw blocks?** The placement exists for the AIU's 32-byte delivery and the GEMV is CUDA-core, so it may not want that arrangement at all. If it costs measurably, "A stays resident for decode" is a legitimate answer — two arrangements with a reason rather than three by accident — and the user should get that trade explicitly rather than have it absorbed. Report the number either way.

BUILD NOW, SWITCH LATER: write and locally gate the pieces, but do NOT repoint `prepare_scale_first`'s producer at BC until the five FULLY_QUANTIZED cells have passed their ppu001 oracles. B is unproven on the device; moving C behind it would make any later failure ambiguous between the merge and its target.

CLAUDE OWNS the routes, oracles and scaffolding half (tests/, ci/, benchmarks/, docs/, pyproject.toml, quactlize/*.py) — request changes there in the INBOX rather than editing. He will re-point the SCALE_FIRST oracles when you switch, and has flagged that changing the producer does not automatically carry those cells' VALIDATED evidence over.

Nothing else is blocked on you: the 9 remaining matrix cells are PARTIAL only for want of a ppu001 run, which is the user's to trigger. Commit and push as you go, no Co-Authored-By trailer.

## Files edited via apply_patch (most frequent first)

- `/tmp/quactlize_bc_q4_probe.cu` ×14
- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×8
- `/tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log` ×8
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_bc_vecdot.hpp` ×6
- `/tmp/quactlize_bc_oracle.py` ×6
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/gguf_prepass_ops.cpp` ×5
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_backend.cu` ×3
- `/tmp/quactlize_bc_q6_debug.py` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.h` ×2
- `/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/ppu_backend.cpp` ×2
- `/tmp/quactlize_xplane_maps_dump.cu` ×2
- `/tmp/quactlize_bc_map_gate.py` ×2
- `/tmp/quactlize_q4_map.cu` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_prepass.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/gguf_packed_unit.hpp` ×1
- `/tmp/quactlize_bc_compile.cu` ×1
- `/tmp/quactlize_bc_map_api.cu` ×1
- `/tmp/quactlize_unit_correction_host.py` ×1

## Last assistant conclusions

### 2026-08-03 12:30 UTC

Kernel work is committed and pushed.

- `2472cf0` adds packed-unit scale derivation plus BC dense/MoE GEMVs for all five formats.
- Real-shape Q4 parity achieved locally:
  - Warm: raw 7.756–7.771 µs, BC 7.656–7.703 µs.
  - Resolved cold, 64 distinct 2048×2048 layers: raw 10.080–10.112 µs/layer, BC 10.064–10.111 µs/layer.
- All five dense/grouped numerical gates pass; planted faults are detected.
- Exact placement gate passes every code coordinate through K=2048.
- Broad suite: `217 passed, 21 skipped`.
- Claude’s `f61604c` now derives the required scale corrections: `0, -4, 8, 8, -24`.

A has not been silently removed yet. Claude still owns the permanent parity benchmark, BC route oracles, stale route-note update, and final SCALE_FIRST producer switch. STATUS is current through inbox 021 and heartbeat 090.
