---
name: ppu17-hopper-porting
description: Port, review, debug, simulate, and optimize CUDA/CUTLASS SM90 Hopper kernels on PPU1.7. Use for ACOMPUTE10700 feature differences, FlashAttention integration, single-launch simulation, and model-specific tuning; not for PPU1.0/1.5 AIU ports.
---

# Hopper → PPU1.7

Preserve the user's CUDA/C++ + CuTe/CUTLASS implementation and arithmetic.
Start from the existing Hopper path; adapt verified backend seams instead of
rewriting a working collective or sending it through the legacy AIU path.
SM90 source compatibility is a starting point, not proof of native execution,
numerical correctness, or Hopper-equivalent performance.

## Select the work

- **Hopper feature differences or FP8/FP4 speedup review:** read
  [feature-delta.md](references/feature-delta.md). Separate backend extensions,
  implemented kernel paths, and measured hardware capability.
- **Mapping or source integration:** read [hopper-mapping.md](references/hopper-mapping.md).
  Resolve the exact backend/toolchain first; enumerate build, runtime, atom,
  layout, pipeline and scheduler seams before editing.
- **Build failures, numerics or simulation:** read
  [debug-and-simulate.md](references/debug-and-simulate.md).
  Prove the selected device body and preserve the single-target-launch rule.
- **Speed/MFU optimization:** read [performance.md](references/performance.md)
  after the mapped candidate has passed the available correctness gates.
  When a proposed change touches a mapping/lifetime, read the mapping reference
  too. Do not import PPU1.0 optimization rules by architecture name alone.

## Essential boundaries

1. Keep **CUDA source/assembly**, **native PPU compile**, **simulator correctness**,
   **simulated performance**, and **physical-device results** as separate
   statuses. An unavailable SDK/model is SKIP with a reason, not PASS.
2. Never fake `__CUDA_ARCH__`, silently select a legacy target, or remove an
   unsupported operation's body to make a build green. Test actual generated
   specializations, not only parsed headers.
3. In the user's PPU1.7 simulation workflow, run **one target invocation per
   process**, no warmup/repeat/profiler replay, and **CPU-only reference**.
   PyTorch is allowed. Audit GPU initialization and auxiliary kernels as well
   as the explicit call. A different simulation contract needs user agreement.
4. The original model was **20 SM / 32 MiB LLC**; the later S1024 FP16 run
   reports **40 SM**. Record the current run's model inputs, not a universal
   PPU1.7 constant. A grid/expected-SM assertion does not partition hardware.
5. Keep admitted dtypes, layouts, rounding, masks and ABI fixed for a
   delivery-only change. Expand scope explicitly; fail unsupported requests
   before launch instead of silently choosing another implementation.

## Work and handoff

Use an isolated source branch/build directory. Keep artifacts under an explicit
`/workspace/<task>` directory created with `mkdir`, not `/tmp` or `mktemp`.
Record parent/source/backend/SDK hashes and true UTC checkpoints in STATUS or
the task's existing resume file. Preserve unrelated work and use explicit
pathspecs for commits. This skill does not authorize remote builds, GPU jobs,
hardware partitioning, publication or default-route changes beyond the task.

Deliver the mapping/change list, exact local checks and negative controls,
remaining unsupported features, simulator input command, and the status of
each evidence tier. For tuning include the original/candidate modeled cycles
at identical model settings and numerics; keep unsuccessful hypotheses visible.
