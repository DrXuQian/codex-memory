# Resume brief: Read /root/marlin_ppu/quactlize/.coord/INBOX.md items 079 through 082 — 082 is the new work, 079/080/081 are the handover from the actlize extraction and are still marked unconsumed in your STATUS. If your shell cannot read the file (it failed with a bwrap error last time), the substance of 082 is below.

CONTEXT: the user wants the compact-A path (PPU_A_CPASYNC) to serve M<=8, and asked whether it should default on. I established these facts today:

  ppu_tactic_space.hpp:262,271  — compact_rows must be 1, 2 or 4; 8 is rejected as CompactARowExtent
  quactlize_mma_mixed_input.hpp:468-472 — the collective itself only requires kACompactRows <= TileM and TileM % kACompactRows == 0, so 8 is legal at TileM=16
  fpA_intB_ppu.cuh:101-106 — a compact build REFUSES m > capacity (prints, returns false, no fallback)
  fpA_intB_ppu.cuh:140 — RequireUniversalFallback static_asserts compact_a_rows == 0

So "default it on" is wrong: a compact binary cannot serve prefill. And the ladder is the only thing blocking M<=8.

TWO THINGS I NEED FROM YOU.

1. Admit capacity 8. But I could not find the justification for the 1/2/4 ladder anywhere — if it was smem arithmetic, common_topology_exclusion_with_a_rows already takes compact_rows and should decide it; if it was the padding aliasing, the collective's divisibility assert already states it; if it was a measurement, it belongs in the kernel as a named static_assert rather than a host-side list. We deleted the sub-four-warp quarantine for exactly that shape and it was hiding the measured optimum. Do you know why it was 1/2/4?

2. Your view BEFORE either of us builds: compact_a_rows is a whole-binary compile-time constant, which is the same defect TileK had — a per-config property as a build switch, so one binary cannot hold both and the sweep cannot compare them in one run. D4's 16x32:256 was unreachable for months for exactly that. Should capacity become a field on the tactic row, one binary carrying {0,1,2,4,8}, with `m > capacity` becoming the SELECTION predicate instead of a refusal? Two things I cannot judge host-side: (a) does one binary holding five capacities cost more in compile time or register pressure than it buys, given the dense table is already 632 rows; (b) is the refusal load-bearing anywhere — does any caller RELY on a compact build declining rather than on it being unreachable?

If the per-config axis is right, say so and I will make the emitter carry the field and the sweep search it — that half is mine. If you think the build switch should stay and M<=8 is just a wider ladder, say that, and I will have the sweep A/B two binaries instead.

Argue against the per-config axis if you think it is wrong. Do not write code yet — I want the answer to (1) and your position on (2) first.

For priority: M=1 dense on the box today is 17.98 us / 42.2% HBM at 16x16x256:16x16:s2 (BACKTEST D6), measured with compact A OFF because it is off by default. The tensor-core M=1 path has never been measured with it, and BACKTEST has no compact-A performance row at all.

- **Thread ID:** `019fd5b4-5312-7ab1-ac64-7cb053db40ba`
- **Started / last event:** 2026-08-06 06:13 UTC → 2026-08-06 06:14 UTC
- **Working dir:** `/root`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/06/rollout-2026-08-06T14-13-12-019fd5b4-5312-7ab1-ac64-7cb053db40ba.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-08-06_019fd5b4_Read-root-marlin_ppu-quactlize-coord-INBOX-md-item.md](../transcripts/2026-08/2026-08-06_019fd5b4_Read-root-marlin_ppu-quactlize-coord-INBOX-md-item.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Read /root/marlin_ppu/quactlize/.coord/INBOX.md items 079 through 082 — 082 is the new work, 079/080/081 are the handover from the actlize extraction and are still marked unconsumed in your STATUS. If your shell cannot read the file (it failed with a bwrap error last time), the substance of 082 is below.

CONTEXT: the user wants the compact-A path (PPU_A_CPASYNC) to serve M<=8, and asked whether it should default on. I established these facts today:

  ppu_tactic_space.hpp:262,271  — compact_rows must be 1, 2 or 4; 8 is rejected as CompactARowExtent
  quactlize_mma_mixed_input.hpp:468-472 — the collective itself only requires kACompactRows <= TileM and TileM % kACompactRows == 0, so 8 is legal at TileM=16
  fpA_intB_ppu.cuh:101-106 — a compact build REFUSES m > capacity (prints, returns false, no fallback)
  fpA_intB_ppu.cuh:140 — RequireUniversalFallback static_asserts compact_a_rows == 0

So "default it on" is wrong: a compact binary cannot serve prefill. And the ladder is the only thing blocking M<=8.

TWO THINGS I NEED FROM YOU.

1. Admit capacity 8. But I could not find the justification for the 1/2/4 ladder anywhere — if it was smem arithmetic, common_topology_exclusion_with_a_rows already takes compact_rows and should decide it; if it was the padding aliasing, the collective's divisibility assert already states it; if it was a measurement, it belongs in the kernel as a named static_assert rather than a host-side list. We deleted the sub-four-warp quarantine for exactly that shape and it was hiding the measured optimum. Do you know why it was 1/2/4?

2. Your view BEFORE either of us builds: compact_a_rows is a whole-binary compile-time constant, which is the same defect TileK had — a per-config property as a build switch, so one binary cannot hold both and the sweep cannot compare them in one run. D4's 16x32:256 was unreachable for months for exactly that. Should capacity become a field on the tactic row, one binary carrying {0,1,2,4,8}, with `m > capacity` becoming the SELECTION predicate instead of a refusal? Two things I cannot judge host-side: (a) does one binary holding five capacities cost more in compile time or register pressure than it buys, given the dense table is already 632 rows; (b) is the refusal load-bearing anywhere — does any caller RELY on a compact build declining rather than on it being unreachable?

If the per-config axis is right, say so and I will make the emitter carry the field and the sweep search it — that half is mine. If you think the build switch should stay and M<=8 is just a wider ladder, say that, and I will have the sweep A/B two binaries instead.

Argue against the per-config axis if you think it is wrong. Do not write code yet — I want the answer to (1) and your position on (2) first.

For priority: M=1 dense on the box today is 17.98 us / 42.2% HBM at 16x16x256:16x16:s2 (BACKTEST D6), measured with compact A OFF because it is off by default. The tensor-core M=1 path has never been measured with it, and BACKTEST has no compact-A performance row at all.

## Last assistant conclusions

### 2026-08-06 06:13 UTC

I’ll read the four coordination items and trace the ladder’s history plus every compact-A refusal/selection call path. I’ll keep this strictly to the design answer—no edits or builds.

### 2026-08-06 06:13 UTC

The sandbox hit the same namespace failure. I’m switching to the workspace file interface so I can still inspect the handover and repository without changing anything.
