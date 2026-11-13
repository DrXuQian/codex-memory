# PPU1.7 versus Hopper: decision-changing differences

Source anchor: PPU CUTLASS `023e82d03e80b4d5982f664925e15499033df314`
at `/root/cutlass3-3.6.0`, compared with NVIDIA CUTLASS v3.6.0.
Recheck these seams on a different revision. Source support is not hardware validation.
Detailed review: `PPU17_CUTLASS360_REVIEW.md` in that checkout.

## Do not erase these backend seams

| Seam | Verified source difference | Decision |
|---|---|---|
| Retained AIU / swizzled loads | `PPU_AIU_LOAD` and `PPU_TSM_LD_SWZL` dispatch to 10500 implementations for non10000; their HGGC device guards use `ACOMPUTE_VERSION >= 10500`, including10700 | WGMMA/TMA use does not mean AIU was removed. These private ops/AiuDesc are not standard Hopper interfaces; do not substitute them without proving placement, completion and lifetime. See `ppu/cute/arch/copy_ppu_aiu.hpp`, `copy_acompute10500_aiu.hpp`. Source retention is not native1.7 execution proof. |
| TF32 major mode | HGGC permits MN-major SS and adds transpose operands; Hopper WGMMA transpose is limited to F16/BF16 | Preserve the matched TF32 atom, descriptor and producer layout. See `builders/sm90_common.inl`, `mma_sm90_gmma.hpp`. |
| Shared descriptors | PPU adds B128A32 / `Swizzle<2,5,2>` and a third layout bit | Use backend traits, not hardcoded Hopper enum values. Existing B128/B64/B32 packed high bits remain equal; do not claim all descriptors differ. See `mma_sm90_desc.hpp`, `mma_traits_sm90_gmma.hpp`. |
| TMA | PPU has `.pos_swzl`; sub-byte wrappers convert FP4 coordinates to byte coordinates | Trace units through tensor map and copy atom. Do not convert twice. Builder alignment=1 does not waive the map's 16-byte base check. See `copy_sm90_tma.hpp`, `copy_traits_sm90_tma.hpp`. |
| Synchronization | Optional `.cluster_group` arrivals/drop and K-step synchronization exceed the standard Hopper cluster interface | Keep these distinct from `ClusterShape` and warpgroup. Preserve participant/lifetime rules; bind the macro state in A/B tests. See `barrier.h`, cooperative/pingpong kernels. |
| Scale ABI | This tree's `nv_float4_t` uses E2M1 + UE8M0/group16; FP8 uses UE8M0/group32 | Verify actual type/traits; neither `nv` nor `sm100` in a name proves NVIDIA NVFP4 or TMEM compatibility. |

BF16/FP16 reuse the Hopper WGMMA/TMA programming structure; do not route them
through legacy AIU merely because the device is PPU. Resource capacities,
cluster limits, latency and peak rates require the selected SDK/model/device;
header budgets are not hardware measurements. Missing evidence means unknown,
not unsupported. NVIDIA `sm_107*` is not PPU `ACOMPUTE_VERSION=10700`.

The uploaded CUTLASS4 archive `0eb6a3b...` (2026-09-28) is a concrete naming
trap too: its16 FP4 WGMMA sites in the10700 arch file all remain UE8M0, and
`nv_float4_t` still aliases UE8M0. The explicit E2M1/UE4M3/group16 example is
under `examples/ppu_20000`, built as20000/SM100a with TMEM/`tcgen05`. Its CUDA
assembly is not evidence of a1.7 NVFP4 interface; obtain the actual1.7
instruction contract rather than relabeling the target or changing a suffix.
SageAttention `dev/ppu_lowbit/docs/CUTLASS4_NVFP4_AUDIT.md` binds the archive
hash and same-file wrong-scale/wrong-target negatives. This source finding
does not establish that1.7 hardware lacks NVFP4.

## Interpret low-bit speedups precisely

- Ordinary FP8 and microscaling are separate from wide-K selection: this tree has ordinary FP8 K32
  SS/RS atoms matching Hopper's interface, ordinary K48 SS, and block-scaled K48 SS in
  `ppu/cute/arch/mma_acompute10700.hpp`. Do not infer scale support from K48 alone or call private K48
  opcode compatibility with stock Hopper; match the actual atom and scale ABI.
- FP8 K48 versus K32, or FP4 K96 versus K64, gives a **conditional 1.5× MMA
  issue-throughput ceiling**, only if each wide issue costs the same as a narrow
  issue and all K lanes contribute. This is not a device-to-device speedup.
- FP8 `48+48+32` and FP4 `96+96+64` yield 4/3× under that assumption.
  Removing their short tail offers 1.125× throughput / 11.11% less MMA time,
  before copy, scales, packing, synchronization and epilogue overhead.
- At this revision, wide atoms are SS; FP8 RS stays K32. Example 710 adds only
  the FP8 K96-atom path. It does not implement FP4 1.5×; a selector macro is
  not an admitted collective. Audit each format's scales and byte map separately.
- Compare equal logical inputs/shapes/output semantics. Record cluster,
  synchronization, stage and preparation changes; distinguish whole-scheme
  gains from instruction-only attribution. Validate image alignment before packing.

## Evidence boundary

The inspected local SDK2.1.1 has no PPU1.7 target. Its `-arch=vm_15` compile
produced `__CUDA_ARCH__=800` with SM90A disabled despite
`-DACOMPUTE_VERSION=10700`. Such a success proves template compatibility only;
mark native-1.7 compilation SKIP. Check real compiler-provided macros and live
device code under a different SDK; never define architecture macros to pass.
