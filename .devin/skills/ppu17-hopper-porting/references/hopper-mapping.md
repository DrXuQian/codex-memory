# Mapping the real Hopper path

## Establish the authorities

Inspect the selected source, dependency revision, SDK target list and build
commands. A directory named `cutlass3.6.0` is not an ABI contract: the legacy
FlashAttention fork and the newer PPU backend can report the same version but
have different pipeline constructors, epilogue selectors and hardware fields.

Known local starting points, to revalidate rather than assume on another host:

- FlashAttention-for-SAIL has an existing `hopper/` forward implementation.
- `/root/cutlass3-3.6.0` resolved to PPU backend commit
  `023e82d03e80b4d5982f664925e15499033df314` during the 2026-09-24 integration.
  Its `build.sh` maps **ACOMPUTE_VERSION=10700 → 90a**.
- `include/ppu/ppu_include_10700.hpp` selects target-specific arch/atom
  extensions. Follow their use for the **actual dtype**, not every advertised
  atom. The initial BF16/FP16 path uses SM90 GMMA/TMA; special low-bit/FP8
  extensions do not imply BF16 needs a new multiply implementation.
- SDK2.1.1-a5c56e exposed only PPU1.0/1.5 in the inspected installation. Its
  CUDA wrapper accepted a request for SM90a but selected PPU001 / arch800.
  Re-query a different SDK; do not generalize that limitation forever.

## Mapping table

For each row classify it as reused, adapted, unsupported or unverified, with
the relevant source definition and a check. Do not label all rows equivalent
merely because the frontend accepts SM90 syntax.

| Hopper component | PPU1.7 starting point | What must be checked |
|---|---|---|
| Build target and dispatch | `ACOMPUTE_VERSION=10700`, real SM90a device compile, `cutlass::arch::Sm90` | Compile the selected generated units; require compiler-provided arch900 + SM90-all feature. A launch wrapper with an empty guarded body is a failure. |
| QK / PV GEMM | Existing `CollectiveMainloopFwdSm90`, CuTe GMMA BF16/FP16 and FP32 accumulators | Match instruction shape, SS/RS operand roles, scale modes, fragment ownership and accumulator lifetime. Inspect emitted WGMMA in every admitted specialization. |
| Global → shared | Existing TMA tensor map and SM90 copy traits | Match element size, strides in bytes/elements, descriptor base, swizzle, alignment, bounds, barrier transaction bytes and stage lifetime. Validate on the model/native target. |
| Shared/register → GMMA | CuTe descriptors/atoms used by the Hopper mainloop | Preserve producer placement and consumer interpretation together. No arbitrary AIU.swzl/ld.swzl substitution from PPU1.0. |
| Async pipeline | SM90 TMA barriers + WGMMA commit/wait + producer/consumer roles | Barrier initial counts must equal actual arrivals. TMA completion, WGMMA operand retirement, phase wrap and stage reuse are separate obligations. |
| Named barriers | Target CUTLASS `NamedBarrier` overloads | Preserve reserved vs user barrier IDs and exact participant counts; old `ppu.bar.*` must not leak into a CUDA SM90 input. |
| Online softmax | Existing FP32 max/sum/exp2 and declared output conversion | Keep scale, causal masking, renormalization, LSE convention and conversion boundaries unchanged. A newer math intrinsic is not a free numeric substitution. |
| Epilogue | Hopper TMA output store / matching store atom | Prove output ownership, tails and live TMA writeback. Guarding out a store can leave a compilable no-output kernel. |
| Runtime and hardware info | CUDA-compatible stream/launch layer and `sm_count` | Do not reinterpret a CUDA stream as a legacy HGGC stream for this path. Query/validate SM count; do not inherit 72/132 from another device. |
| Scheduler | Existing Hopper persistent scheduler and its work queue | Check grid, causal work ordering, head/GQA mapping, tile coverage, cache section and semaphore initialization. Warpgroup is not a multi-CTA cluster. |
| Cluster / advanced features | Feature-specific target support | Do not assume cluster multicast, paged/append KV, FP8, backward or packed GQA just because fixed BF16 forward compiles. Extend with separate admission. |

## Concrete integration traps to retain

In the inspected SAIL fork, `USE_PPU` selects the **legacy AIU algorithm**,
not every PPU generation. It disables the Hopper GEMM helper and TMA output
path. The new path uses its own `FLASHATTN_PPU17` guard and does not define
`USE_PPU`/`USE_AIU`. Verify these meanings before reusing them in another repo.

The selected PPU CUTLASS3.6 differs from the fork's dependency:

- `KernelHardwareInfo::sm_count`, not `cu_count`.
- Accumulator store selector has two template arguments, not the fork's three.
- `PipelineTmaAsync` has a three-argument constructor. For cluster1, its
  empty-barrier arrival count and signalling predicate already match one
  arrival per consumer warpgroup. Reuse the **matched pair**; transplanting
  only the newer no-cluster workaround is unsafe.
- Legacy PPU exp2, cp.async, barrier and auxiliary-header definitions can leak
  into a build even when their runtime feature is disabled. Isolate the parse
  graph as well as the selected execution graph; assemble the resulting code.

Local CUDA12.8 checking needed explicit
`-gencode=arch=compute_90a,code=sm_90a`. `-arch=sm_90a` also created a generic
compute90 pass, which correctly failed an SM90-all-only gate. Inspect actual
frontend passes rather than weakening the guard or defining feature macros.

## Evidence-bearing implementation

In the source-integration branch of FlashAttention-for-SAIL, inspect:

- `hopper/ppu17_build.py`: explicit six-unit FP16/BF16 D64/128/256 manifest.
- `hopper/backend_runtime.h`: new/legacy runtime boundary.
- `dev/ppu17/compiler_target.cu`: real device target probe.
- `tools/check_ppu17_source.py`: per-entry WGMMA/TMA check, assembly and
  optional real host-dispatch/internal-link closure.
- `dev/ppu17/README.md`: admitted features and toolchain limits.

Locate the active checkout before using these paths; do not silently substitute
another worktree's generated file or binary. A newer integration may expand
scope, so the source manifest remains the authority.
