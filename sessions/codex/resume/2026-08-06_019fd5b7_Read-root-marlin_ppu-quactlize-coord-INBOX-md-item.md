# Resume brief: Read /root/marlin_ppu/quactlize/.coord/INBOX.md items 079-082 — 082 is the new work; 079/080/081 are the handover from the actlize extraction and are still unconsumed per your STATUS. If your shell cannot read files (it failed at bwrap sandbox init last time), the substance is below and is self-contained.

FACTS I ESTABLISHED TODAY, so you do not re-derive them:

  ppu_tactic_space.hpp:262,271          compact_rows must be 1, 2 or 4; EIGHT is rejected as CompactARowExtent
  quactlize_mma_mixed_input.hpp:468-472 the collective has no such ladder — only kACompactRows <= TileM and
                                        TileM % kACompactRows == 0, so 8 is legal at TileM=16
  fpA_intB_ppu.cuh:101-106              a compact build REFUSES m > capacity: prints, returns false, no fallback
  fpA_intB_ppu.cuh:140                  RequireUniversalFallback static_asserts compact_a_rows == 0

The user wants small-M (M<=8) served by compact A. "Default it on" is wrong — a compact binary cannot serve prefill at all — but within the small-M regime I can find no downside: it is bit-exact below capacity, the AIU was already fetching only the real rows (AiuDesc dim_h from M, padz), so what compact buys is smem footprint (49152 -> 768 B) against a dense path that is shared-limited to 4 blocks/CU, and A's whole chain is 0.6% of the instruction stream. Nothing about that is measured: BACKTEST has no compact-A performance row at all.

TWO THINGS, and I want the second answered before either of us writes code.

1. WHY WAS THE LADDER 1/2/4? I will not widen a predicate whose justification I cannot read. If it was smem arithmetic, common_topology_exclusion_with_a_rows already takes compact_rows and should be deciding it. If it was the padding-row aliasing, the collective's own divisibility assert already states the condition. If it was a measurement, it belongs in the kernel as a named static_assert rather than a host-side list — we deleted the sub-four-warp quarantine for exactly that shape and it turned out to be hiding the measured optimum. Do you know which it was?

2. SHOULD CAPACITY BE A CONFIG-ROW FIELD RATHER THAN A WHOLE-BINARY MACRO? compact_a_rows today is a build switch, which is precisely the defect TileK had: a per-config property expressed per-binary, so one binary cannot hold both and the sweep cannot compare them in one run. D4's 16x32:256 was unreachable for months for exactly that reason. The shape that fixes it: capacity joins the tactic row, one binary carries {0,1,2,4,8}, and `m > capacity` stops being a refusal and becomes the selection predicate — narrowest capacity that covers M, ordinary path above the largest.

   Two things I cannot judge from the host side:
   (a) does one binary holding five capacities cost more in compile time or register pressure than it buys, with the dense table already at 632 rows?
   (b) is the refusal load-bearing anywhere — does any caller RELY on a compact build declining, as opposed to merely never being selected?

If the per-config axis is right, say so and I will make the emitter carry the field and the sweep search it; that half is mine. If you think the build switch should stay and M<=8 is just a wider ladder, say that instead and I will have the sweep A/B two binaries — but I want that stated rather than discovered. Argue against the axis if you think it is wrong.

PRIORITY CONTEXT: M=1 dense on the box today is 17.98 us / 42.2% HBM at 16x16x256:16x16:s2 (now BACKTEST D6), measured with compact A OFF because it is off by default. The tensor-core M=1 path has never been measured with it.

Do not write code yet — answer (1) and give your position on (2).

- **Thread ID:** `019fd5b7-017f-7b70-a350-0db6efc615c6`
- **Started / last event:** 2026-08-06 06:16 UTC → 2026-08-06 06:26 UTC
- **Working dir:** `/root`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/06/rollout-2026-08-06T14-16-08-019fd5b7-017f-7b70-a350-0db6efc615c6.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-08-06_019fd5b7_Read-root-marlin_ppu-quactlize-coord-INBOX-md-item.md](../transcripts/2026-08/2026-08-06_019fd5b7_Read-root-marlin_ppu-quactlize-coord-INBOX-md-item.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Read /root/marlin_ppu/quactlize/.coord/INBOX.md items 079-082 — 082 is the new work; 079/080/081 are the handover from the actlize extraction and are still unconsumed per your STATUS. If your shell cannot read files (it failed at bwrap sandbox init last time), the substance is below and is self-contained.

FACTS I ESTABLISHED TODAY, so you do not re-derive them:

  ppu_tactic_space.hpp:262,271          compact_rows must be 1, 2 or 4; EIGHT is rejected as CompactARowExtent
  quactlize_mma_mixed_input.hpp:468-472 the collective has no such ladder — only kACompactRows <= TileM and
                                        TileM % kACompactRows == 0, so 8 is legal at TileM=16
  fpA_intB_ppu.cuh:101-106              a compact build REFUSES m > capacity: prints, returns false, no fallback
  fpA_intB_ppu.cuh:140                  RequireUniversalFallback static_asserts compact_a_rows == 0

The user wants small-M (M<=8) served by compact A. "Default it on" is wrong — a compact binary cannot serve prefill at all — but within the small-M regime I can find no downside: it is bit-exact below capacity, the AIU was already fetching only the real rows (AiuDesc dim_h from M, padz), so what compact buys is smem footprint (49152 -> 768 B) against a dense path that is shared-limited to 4 blocks/CU, and A's whole chain is 0.6% of the instruction stream. Nothing about that is measured: BACKTEST has no compact-A performance row at all.

TWO THINGS, and I want the second answered before either of us writes code.

1. WHY WAS THE LADDER 1/2/4? I will not widen a predicate whose justification I cannot read. If it was smem arithmetic, common_topology_exclusion_with_a_rows already takes compact_rows and should be deciding it. If it was the padding-row aliasing, the collective's own divisibility assert already states the condition. If it was a measurement, it belongs in the kernel as a named static_assert rather than a host-side list — we deleted the sub-four-warp quarantine for exactly that shape and it turned out to be hiding the measured optimum. Do you know which it was?

2. SHOULD CAPACITY BE A CONFIG-ROW FIELD RATHER THAN A WHOLE-BINARY MACRO? compact_a_rows today is a build switch, which is precisely the defect TileK had: a per-config property expressed per-binary, so one binary cannot hold both and the sweep cannot compare them in one run. D4's 16x32:256 was unreachable for months for exactly that reason. The shape that fixes it: capacity joins the tactic row, one binary carries {0,1,2,4,8}, and `m > capacity` stops being a refusal and becomes the selection predicate — narrowest capacity that covers M, ordinary path above the largest.

   Two things I cannot judge from the host side:
   (a) does one binary holding five capacities cost more in compile time or register pressure than it buys, with the dense table already at 632 rows?
   (b) is the refusal load-bearing anywhere — does any caller RELY on a compact build declining, as opposed to merely never being selected?

If the per-config axis is right, say so and I will make the emitter carry the field and the sweep search it; that half is mine. If you think the build switch should stay and M<=8 is just a wider ladder, say that instead and I will have the sweep A/B two binaries — but I want that stated rather than discovered. Argue against the axis if you think it is wrong.

PRIORITY CONTEXT: M=1 dense on the box today is 17.98 us / 42.2% HBM at 16x16x256:16x16:s2 (now BACKTEST D6), measured with compact A OFF because it is off by default. The tensor-core M=1 path has never been measured with it.

Do not write code yet — answer (1) and give your position on (2).

## Last assistant conclusions

### 2026-08-06 06:26 UTC

My position: the 1/2/4 ladder was workload scope accidentally encoded as kernel legality, and capacity should become a per-config axis.

1. Why 1/2/4?

History answers this. Commit `9fd5074` introduced `CompactARowExtent`. In that same commit:

- The fixed workload axis was `{1,2,4,64,2048,4096}`.
- The documentation explicitly framed the work as “covering M in {2,4}.”
- The predicate parameter was named `problem_m`, not `compact_rows`.
- Capacities 2 and 4 were described as compile-tested but not device-measured.

The later router fixture reinforced that scope: Mmax `1/2/3` mapped to capacities `1/2/4`. There was no M=8 workload, so no capacity 8 was built or inventoried.

Therefore 1/2/4 was neither smem arithmetic, an aliasing invariant, nor a measured optimum. It was the then-required workload ladder. Renaming `problem_m` to `compact_rows` preserved the list and made a workload enumeration look like a kernel law.

Capacity 8 should be admitted. The legality rule should be only:

- capacity > 0;
- capacity ≤ TileM;
- TileM % capacity == 0;
- selected collective supports compact A;
- the resulting compiled shared storage fits.

The set of capacities actually emitted—currently `{1,2,4,8}`—belongs in the emitter/config inventory, not in `ppu_tactic_space.hpp` as an architectural exclusion.

2. Per-config axis?

Yes. Capacity changes `SmemLayoutA`, `SharedStorageSize`, and therefore the instantiated collective type. That makes it a kernel configuration property, exactly like TileK and stages—not a whole-binary mode.

I would implement the policy as:

- Capacity `0` means ordinary unrestricted A.
- Positive capacity means the compact specialization.
- Normal selection chooses the narrowest compiled capacity covering M.
- M above 8 selects capacity 0.
- The default/universal row remains capacity 0, preserving the current `RequireUniversalFallback` contract.
- Ordinary capacity 0 remains a sweep competitor at small M until the compact result is measured.

Do not encode “narrowest” as kernel legality: every capacity ≥ M satisfying the layout constraints is correct. Narrowest is a dispatch/pruning policy.

On the two concerns:

(a) Compile time and registers

Holding several kernels in one binary does not combine their register pressure. Register allocation is per kernel entry point; another capacity specialization elsewhere in the binary cannot increase this kernel’s registers. The current `SmemLayoutAFrag` also deliberately preserves logical TileM, so moving the capacity from a macro to a template/config field does not itself alter the MMA fragment/register geometry.

Compile time and code size are real. A naïve full cross-product changes the 632-row table into at most `632 × 5 = 3,160` instantiations. That could be roughly a fivefold frontend/code-generation burden and may stress hgcc. That argues for pruning or splitting compilation units, not for retaining the binary macro. Measure that cost, but do not let it determine the semantic model.

(b) Is refusal load-bearing?

It is load-bearing as a per-specialization safety check, not as a whole-binary contract.

The backend’s `QueryOnly` path calls the actual launcher to determine config validity, and `list_valid_*` filters configs using that answer. Direct launch APIs can also be called without a preceding query. Therefore an explicitly selected capacity-4 row at M=8 must still decline defensively.

What should disappear is the binary-wide outcome where every row declines above one build-time capacity. Normal dispatch should filter insufficient rows and reach another compact row or capacity 0. Keep the launcher guard for invalid explicit selection, and keep `RequireUniversalFallback` proving that the default row is ordinary.

So the answer for your half is: carry capacity in the emitted config identity and let the sweep search it. Do not A/B whole binaries. Also keep capacity 0 in the small-M comparison—the M=1 compact path still has no performance measurement.

No files were changed. The shell still failed at `bwrap`; I read the pushed `develop` versions of 079–082, STATUS, current dispatch, and the introducing commit through the repository connector.
