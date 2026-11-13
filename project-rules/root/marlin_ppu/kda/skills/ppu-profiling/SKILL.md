---
name: ppu-profiling
description: Analyze PPU performance with ACU and Asys. Use for kernel counters, native instruction and stall diagnosis, memory traffic, occupancy, device timelines, launch gaps and matched candidate comparisons.
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# PPU Profiling

Connect measured evidence to the next KDA candidate. Start with the task's
question and existing reports, then read only the relevant reference.

| Question | Reference |
|---|---|
| Where does time go across launches, copies and waits? | [Asys timeline](references/timeline.md) |
| How do I collect or import a kernel report? | [ACU collection](references/collection.md) |
| Which counters or native-instruction queries exist? | [ACU metrics](references/metrics.md) |
| Why is this kernel slow, and what should change? | [Kernel diagnosis](references/analysis.md) |

## Workflow

1. Identify the numerically valid baseline, specialization, inputs and question.
2. Record source/binary, SDK/tool version, device or model, selected range and
   cache/replay policy in the task's `profile/<run>/` directory.
3. Reuse its capture harness or existing report. Include preparation, helpers
   and reductions when the contract measures the complete operation. Confirm
   the intended device bodies and activity count before interpreting timing.
4. Use Asys for time attribution and ACU for the selected kernel's counters.
   Inspect actual schemas, definitions and units; missing data is unavailable.
5. Compare the baseline and candidate at equal scope. Separate observed changes
   from proposed causes and rank experiments by potential complete-call impact.
6. Write `REPORT.md` with identity/scope, measurements and units, findings,
   remaining uncertainty, next experiment and the keep/revise/reject decision.
   Feed the result into `docs/plan.md` in the implementation workspace.

## Measurement boundaries

ACU replay, clean event/API timing, Asys activity durations and simulator cycles
are different measurements. Concurrent kernel sums are not elapsed time; host
API rows are not device activities. Static ISA, dynamic execution counts and
stall-per-issue ratios do not directly measure wall-time shares.

Use the selected SDK's CLI/report API or a discovered MCP exposing it. See
[tool access](../../docs/ppu-tooling.md). MCP is optional. A single-invocation
simulator contract requires its own trace protocol instead of profiler replay.

Sources: [S04, S06, S08, S10, S14](../ppu-kernel-knowledge/references/sources.md).
Adapted Quactlize guidance retains Apache-2.0; see
[notices](../../THIRD_PARTY_NOTICES.md).
