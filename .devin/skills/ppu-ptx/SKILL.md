---
name: ppu-ptx
description: >
  Reference for writing/debugging GPU kernels on the Alibaba T-Head PPU (ZW810 / chip ppu001,
  an NVIDIA-SM80-PTX-compatible accelerator, HBM peak ~2766 GB/s). Covers the ppu.* inline-asm
  mnemonics (ppu.mma, ppu.ldmatrix.swzl, the AIU bulk load, plain cp.async), the CC-8.0 occupancy
  limits, the build target, and hard-won gotchas. Invoke when writing PPU CUDA/PTX kernels
  (FlashAttention, GEMV, convert, GEMM), debugging "Cannot select intrinsic" / wrong-operand bugs,
  or doing PPU kernel perf work. The canonical, tested asm lives in the llama.cpp PPU fork's
  ppu_tests/*.cu and ggml/src/ggml-cuda/*-ppu.cuh -- this skill points to them.
---

# PPU kernel reference (T-Head ZW810 / ppu001)

The PPU is **SM80-PTX-compatible**: plain CUDA + standard PTX (cp.async, mma via the `ppu.` family) compile and
run. It reports **compute capability 8.0**. You **cannot build or run on macOS** (no nvcc) — edit locally, build/run
on the box (host `aiswu95`, repo `/sim/eec/shared/junfu.qx/llama.cpp`). The standalone microbenches in
`ppu_tests/*.cu` are the fastest way to validate an asm/perf idea in isolation before touching ggml.

## Build target (get this wrong and m8n16 won't compile)

- **Target = ppu001, and the ONLY way to get it is `CMAKE_CUDA_ARCHITECTURES=OFF` (no -arch).** ppu001 is nvcc's
  **default** device target (full ISA: `swzl` ldmatrix, `m8n16k16` mma). **Any forced NVIDIA `sm_XX` routes through
  a compat table onto ppu0015** — verified ON-DEVICE by the real build: **BOTH `sm_80` AND `sm_89` → ppu0015**, and
  ppu0015's SASS pass rejects the ppu001-only asm → hard error. So the PPU fork's `ggml-cuda/CMakeLists.txt` now
  **defaults `set(CMAKE_CUDA_ARCHITECTURES OFF)` when `GGML_USE_PPU` is on and no arch is passed** — a plain build
  targets ppu001, no flag needed. This skips both the NVIDIA auto-arch block (which appends `89-real` → ppu0015)
  AND the `GGML_NATIVE` native-detect path (picks the box GPU as ppu0015). **CRITICAL: `-DCMAKE_CUDA_ARCHITECTURES=80`
  (or `80-real`) does NOT give ppu001 — it lands on ppu0015 and fails. The earlier "`sm_80 → ppu001`" was an
  `nvcc --dryrun` (ptxas mcpu) artifact, WRONG for the real device compile. Use `OFF`, never a pinned `sm_XX`.**
  Re-configure needs `rm -rf build` (CMAKE_CUDA_ARCHITECTURES is a cache var; incremental reconfigure doesn't re-run
  the arch logic). Symptom of a wrong arch: `inline-ptx: error: unsupported ldmatrix in arch ppu0015: ppu.ldmatrix...swzl`
  (or `Cannot select ...m8n16k16`). A benign `N warnings generated when compiling for ppu0015` with NO `error:` is
  just clang's per-TU line and is unrelated to this.
- **Why it matters:** the toolchain lowers a recognized `ppu.mma` inline asm to an LLVM intrinsic, then `llc`
  selects it. `llc`'s ISel has `m16n16k16` on both chips but **`m8n16k16` only on ppu001** — on ppu0015 it errors
  `Cannot select: intrinsic llvm.ppu.mma.*.m8n16k16`. The *assembler* supports m8n16 on both, so standalone
  `.cu→PTX→assembler` microbenches compile m8n16 regardless of chip, but the kernel build (`.cu→.bc→llc`) does
  not. `asm volatile` does NOT prevent the intrinsic lowering.

## Occupancy limits (CC 8.0, per CU) — the numbers for any occupancy math

| resource | limit |
|---|---|
| **Shared memory / CU** | **262144 B = 256KB (HARD max, not configurable higher)**; alloc unit 128 B |
| Registers / CU | 131072; **max 256 regs/thread**; alloc granularity = warp, unit 64 |
| Max warps / CU | 64 (32 threads/warp → 2048 threads/CU); max 64 blocks/CU; warp granularity 8 |

Occupancy = min(shared-, register-, warp/block-limited) blocks. **A kernel using exactly 64KB shared → 256/64 = 4
blocks with ZERO slack** (e.g. FlashAttention d128); any extra shared drops it to 3. There is no carveout above 256KB.

## The `ppu.*` inline-asm mnemonics

All are raw `asm volatile` (NOT SDK intrinsics like `tsm_load_cube`/`awmma::load_matrix_sync` — chasing those was a
dead end; the `"no viable alternative at 'cp.async.a'"` error was just a missing `ppu.` prefix). **Canonical, tested
implementations: `ppu_tests/fa_ppu.cu`** (`aiu_load`, `aiu_load_linear`, `ld_swzl`, `ld_swzl_trans`, `mma_f32`,
`mma_f16`) and `ggml/src/ggml-cuda/ppu-aiu.cuh`. Full AIU API + params: **`ppu_tests/AIU_NOTES.md`**.

### Tensor core — `ppu.mma.sync.aligned.m16n16k16`
```
// f32 acc: D[8 f32] += A[4 half2] @ B[4 half2]^T (C input == D). row.col.
ppu.mma.sync.aligned.m16n16k16.row.col.f32.f16.f16.f32 {d0..d7}, {a0..a3}, {b0..b3}, {d0..d7};
// f16 acc: D[4 half2] += A @ B^T (half the regs; for an O accumulator that would otherwise spill).
ppu.mma.sync.aligned.m16n16k16.row.col.f16.f16.f16.f16 {d0..d3}, {a0..a3}, {b0..b3}, {d0..d3};
```
- **m8n16k16** (query on M=8) for **ncols==8** (small batch / GQA decode) — halves wasted work vs m16n16 there;
  **ppu001-only** (see build target). Use m16n16 for larger ncols. `mma_tile_sizes`/`cols_per_thread` switch on it.

### Shared→register operand read — `ppu.ldmatrix.swzl` (reads an AIU-swizzled TSM cube)
```
// non-trans (K, Q): TSM cube -> 4 vregs == ggml mma::tile<16,8,half2> EXACTLY (vreg[l]==tile.x[l], TL/TR/BL/BR=0/1/2/3)
ppu.ldmatrix.sync.aligned.m8n8.x4.swzl.shared.b16 {v0,v1,v2,v3}, [cube_base], {0, coord_h, 1, cube_h, 1, cbo};
// trans (V): TSM cube (kv x dv) -> V^T operand tile
ppu.ldmatrix.sync.aligned.m16n16.x1.swzl.trans.shared.b16 {v0,v1,v2,v3}, [cube_base], {0, coord_h, 1, cube_h, 1, cbo};
//   cube_base = raw 64-bit "l" pointer; cbo = coord_w * sizeof(half). The swzl frag drops straight into ppu.mma,
//   no reorder -> the permuted-K / get_half2 / de-interleave hacks are unnecessary on the AIU path.
```
- **`ppu.ldmatrix.m8n8.x2` CAVEAT:** its register distribution does NOT match the NVIDIA m8n8 address formula for
  `tile<8,8>` / `tile<16,4>`. Load those **element-wise** (`get_i`/`get_j` / load_generic), not via x2 — getting it
  wrong silently corrupts the operand (broke every m8n16 KQ until fixed).

### Bulk async global→shared — the **AIU** (`ppu.cp.async.aiu.bulk.tensor...`)
```
// swzl: lays data out for the swzl ldmatrix above. cube_w MUST == 64 (b16 128B swizzle).
ppu.cp.async.aiu.bulk.tensor.shared.global.padz.swzl.2d.b16   [smem], [gmem],
    {1, dim_h, dim_w, 0, coord_h, coord_w}, {1, cube_h, cube_w, 1};
// linear: same operands, ROW-MAJOR (non-swizzled) -> for element-wise reads (e.g. a mask tile), NOT mma operands.
ppu.cp.async.aiu.bulk.tensor.shared.global.padz.linear.2d.b16 [smem], [gmem], {...}, {...};
//   smem = 32-bit cvta'd ("r"), gmem = 64-bit ("l"), padz = zero-fill OOB. Fenced with ORDINARY cp.async.commit_group
//   / cp.async.wait_group (it rides the cp.async group stack). cube_h up to 128 works (the Q load uses 128).
```
- **AIU = single-thread bulk DMA (`ThrID = Layout<_1>`), sized for big 16×64 cubes.** Only ONE thread issues it;
  all threads still `cp.async.commit_group` to keep the group stack consistent. **Use it ONLY for FlashAttention
  mma-operand tiles** (where the swizzle buys 0-bank-conflict ldmatrix). A thin R×64 cube (e.g. GEMV) can't amortize
  its setup → gemv AIU ran 38% HBM vs 70-76% for the alternatives. **ppu001 = ACOMPUTE_VERSION 10000.**

### General streaming — plain **cp.async == SM80, verbatim**
```
cp.async.cg.shared.global [dst], [src], 16;   // dst = __cvta_generic_to_shared(ptr); 16B copy
cp.async.commit_group;
cp.async.wait_group N;   // or cp.async.wait_all;
```
Identical to ggml-cuda `cp-async.cuh` (`cp_async_cg_16`, `CP_ASYNC_AVAILABLE`). **Distinct from the AIU.** Use plain
cp.async for general global→shared streaming (GEMV weights, GEMM mainloop); the AIU swzl is *only* for FA tiles.

## Rules of thumb / hard-won gotchas

- **Bandwidth-bound streaming (GEMV decode, convert) → occupancy is king, NOT per-thread ILP.** Vectorize (uint4
  16B ld/st, 8 elems/thread) and launch MANY blocks (1 chunk/thread). A grid-stride **U-unroll HURTS** here — it cuts
  the block count, dropping occupancy below HBM saturation (benched: convert U1 best, U8 worst). EXCEPTION: GEMV is
  **reduction-bound** (1 output row/block → block count capped at M), so there U-unroll DOES help (ILP hides latency).
  Decode GEMV winner = cuBLAS's structure: 1 row/block, 128 thr, lean register LDG, NO shared/cp.async/split-K (~82% HBM).
- **Method that cracks perf: ncu-diff against a reference kernel** (cuBLAS / FA2) via "Add Baseline" — block dims +
  stall breakdown + instruction mix reveal the reference's structure. Watch Warp State (Memory Dependency = un-hidden
  load latency; Stall Tensor Pipe Busy = genuinely tensor-bound). Instruction COUNT misleads (mma are few but heavy).
- **FlashAttention is TENSOR-bound** (~70% TENSOR FP16), not scalar-bound. Winning config (all required): f32 O acc
  (mma_f32 for QK AND PV) + **Q persistent in shared** (re-read each QK, frees regs for f32 O) + K/V single-buffer
  (Q32+K16+V16 = 64KB = 4 blocks) + **mma-identity P-convert** (1 mma w/ per-lane identity weight 0x3c00, replaces 16
  shuffles) + **`__expf`** (bare SFU; `exp2f()` adds an IEEE-range-check wrapper = +27M cmp/csel; `asm ex2.approx`
  blocks scheduling) + **`template<bool MASK>`** (non-causal+aligned elides all mask int ops) + **boundary-only mask**
  (only edge/diagonal tiles read the mask) + **causal early-exit + LPT grid order** (heaviest blocks first; the PPU
  scheduler is greedy → balances the triangular load → causal 1.28× vs FA2's 1.12×). d256 also needs q-block-clustered
  grid order (L2 locality) + read-ahead operand loads (NQB=1 has no 2nd q-block to hide just-in-time reads).
- **The FA mask-tensor read is latency-bound and can't be made occupancy-free.** Reading an external mask per S
  element stalls warps on Memory Dependency (tensor 41%→11%); AIU-prefetching the mask tile to shared halves the stall
  but the +16KB crosses the 64KB→4-block cliff (NET WORSE). Fix = **causal hint**: route pure-causal masks
  (`causal_attn && max_bias==0 && !is_swa && !kv_unified`) to a POSITIONAL kernel that reads ZERO mask
  (`ggml_flash_attn_ext_set_causal`, wired in `llm_graph_context::build_attn_mha`). Also **skip the KV_max mask-scan
  on the causal path** — the causal kernel computes its kv-loop bound from positions and ignores KV_max, so the scan
  is pure wasted mask traffic (it was 2× the kernel).
- **Convert (f32↔f16↔bf16):** ggml's `convert_unary` is scalar (1 elem/thread) → latency-bound. Vectorize: 8
  elems/thread via a `float[8]` staging (wide ld per src + wide st per dst). bf16↔f32 is exact (no rounding);
  f32→f16/bf16 uses `__float22half2_rn`/`__float22bfloat162_rn` (matches the scalar cast bit-for-bit).
- **Decode stays on ggml's vec path** (`fattn-vec.cuh`) — plain-PTX FMA, no `ppu.*`, runs as-is. Only the **prefill
  (mma) FA path** uses ppu.* and needs the port.
- **Integrating a PPU-only `*-ppu.cuh` (mmvf-ppu / fattn-ppu / convert-ppu) into the shared ggml-cuda:** the file's
  CODE is `#if defined(GGML_USE_PPU)`-gated, but its `#include <cuda_bf16.h>` (and other CUDA-only headers) sit
  OUTSIDE that guard. `ggml-cuda.cu` is compiled for **CUDA / HIP / MUSA**, and `cuda_bf16.h` does NOT exist on
  HIP/MUSA → an UNCONDITIONAL `#include "ggml-cuda/mmvf-ppu.cuh"` breaks those builds. So guard the include SITE too:
  `#if defined(GGML_USE_PPU)` / `#include "…-ppu.cuh"` / `#endif`. Same for the dispatch call site (put the
  `ggml_cuda_*_ppu_supported()` gate + `_ppu()` call inside a `#if defined(GGML_USE_PPU)` block, generic path as the
  `#else`/fallback). Applies to every `*-ppu.cuh` include (fattn.cu's `#include "fattn-ppu.cuh"` needs the same).

- **The AIU + `ldmatrix.swzl` path CARRIES INT4** (measured, `marlin_ppu/aiu_int4_smoke.cu`). Both move b16, and
  `.x4` hands a lane one 32-bit reg from each of FOUR different 8x8 matrices — NOT the four consecutive int32 a
  Marlin-style dequant wants. The map is bijective and inverts, and the required repack is **LOCAL and TILEABLE**, so
  it folds into the load-time repack for free. Within a 16x16 b16 tile:
  `reg j of lane L -> row = L/4 + 8*(j/2), cols = 2*(L%4) + 8*(j%2) and +1`.
  A 16x16 b16 tile = 256 b16 = 128 int32 = 32 lanes x 4 regs = exactly one Marlin B tile (1 ktile x 64 columns), and
  Marlin's four ints are its four n-blocks, so the four swzl registers land on j=0..3 directly.
- **A warp grid is NOT transferable between kernels when the fragment width changes.** The fp16 MoE GEMM uses 4 warps
  in n (NI=2, 32 columns each); with an INT4 B one `ld_swzl` feeds a warp **64** columns, so n is pinned at BN/64 = 2
  warps and m takes the rest. Carrying the fp16 grid over put a column index at 320 against N=256 — an illegal access,
  not a wrong number. Neither did its NST transfer (4 beat 6, because the Q4_K B cube is half the bytes so the
  stage-depth/occupancy balance differs). **Assume no tuning constant carries across a dtype change.**
- **In the Marlin family, `b_sh_wr_iters != thread_k_blocks`** — it is `8*NB*KB/threads`, which is 2 for every config
  in the CALL_IF list while thread_k_blocks is 4 or 8. **WARPS SPLIT THE K DIMENSION** (that is what
  `thread_block_reduce()` undoes), so a thread's k-block is `(k % b_sh_wr_iters) * NWK + warp_k` with
  `NWK = (threads/32)/(thread_n_blocks/4)`, exactly as `a_sh_rd` encodes it. **Any new per-k quantity must use that
  expression**; using `k` alone silently makes every warp read the stage's first group.
- **The A-fragment register order differs between NVIDIA and PPU** (the same v1<->v2 swap `ppu_ldmatrix_x4` does for
  free): NVIDIA row bit = `l%2`, k bit = `l/2`; **PPU swaps them**. Code that hardcodes NVIDIA's order passes on a
  5090 and returns rel~1.2 garbage on the PPU.
- **Achieved occupancy is often GRID-limited, not register-limited — do the arithmetic before optimizing.** acu
  reported theoretical 62.5% (registers) against achieved 41.3% for a GEMV; 1024 blocks / 72 CU = 14.2 blocks = 28.4
  of 64 warps = 44%, i.e. the grid was the floor and the register ceiling was never reached. Capping registers would
  have done nothing. Conversely, when shared memory is the limit acu says so directly (`Block Limit Shared Mem`), and
  for an INT4 B the A tile dominates shared ~4:1 (A is fp16, B is packed), so the m-tile height drives occupancy far
  harder than in an all-fp16 kernel.
- **A 5090 is NOT a performance proxy for the PPU.** Correctness ports; performance does not. Three consecutive
  optimizations looked right on a 5090 and were wrong or BACKWARDS on the PPU (`_scale_perm` on a GEMV, a flush
  rewritten in half, a larger block target). Do not report a local measurement as evidence about the PPU.
- **Isolate with a bracket, and check what the compiler removed with it.** The reliable method here is a
  `-D` build that deletes exactly ONE thing and keeps the rest (`MARLIN_MINS_NOAPPLY`, `MOE_SCALE_CONST`,
  `GEMV_KTPG`, `MOE_NO_A_LDSWZL`). Two traps: (1) an unread value gets **dead-code-eliminated along with its load**,
  so a probe meant to drop only the arithmetic drops the load too — add a third point that keeps the arithmetic and
  drops the load instead; (2) **instruction count is not the critical path** — acu had `v.cnvt` as the most-executed
  opcode at +295% and cutting two thirds of it moved nothing.
- **Any percentage over 100 or identically zero is a broken denominator, not a result** (242% MFU, 114.5% HBM on a
  1792 GB/s part, a column of 0.0%). Also: for a masked/padded kernel, report BOTH useful and ISSUED throughput —
  masked rows burn mma cycles, so a 115 TFLOP/s "useful" line and acu's 50% tensor utilisation are the same fact.

## Adding a PPU-optimized operator (the selective-override pattern)

The PPU is NOT integrated like MUSA/HIP. **MUSA reuses ALL of ggml-cuda via API retargeting** (a `vendors/musa.h`
that `#define`s `cuda*`→`musa*`, GLOBs `ggml-cuda/*.cu`, compiles with mcc; its only own op is `ggml-musa/mudnn.cu`).
The PPU instead runs **native CUDA PTX** (nvcc/cuda_bf16/cublas all work) so it needs NO vendor retarget — it just
**selectively swaps specific hot kernels for PPU-tuned ones**. That is a different pattern:

**Key idea: ggml-cuda is ALREADY a per-op multi-kernel dispatcher** (`ggml_cuda_flash_attn_ext` picks mma/vec/tile/
wmma; `ggml_cuda_mul_mat` picks mmvf/mmq/cublas). A PPU override is just **one more branch in that existing
dispatch**, gated `#if defined(GGML_USE_PPU)`, with the kernel isolated in a `*-ppu.cuh`. Not an #ifdef hack —
an extension of the dispatch that's already there.

**The pattern (one hook per override):** at the right dispatch point,
`#if defined(GGML_USE_PPU)` → `if (ggml_cuda_X_ppu_supported(...)) { ggml_cuda_X_ppu(...); } else` → `#endif` →
`generic_X(...);`. Keep the `_supported` gate + the kernel in the `*-ppu.cuh`; the shared code only gets the hook.

**Granularity decides WHERE you hook (unavoidable):**
- **Whole-op override** (e.g. FlashAttention) → hook at the op dispatch (`ggml_cuda_flash_attn_ext` in fattn.cu).
  If many whole-op overrides pile up, funnel them through ONE top-level hook in the op switch.
- **Sub-case override** (the decision lives INSIDE a generic function) → hook right there, you can't lift it to the
  op level: **GEMV** is only the vec sub-case of `ggml_cuda_mul_mat` (which also does GEMM/cublas); **convert** is
  the contiguous f32↔f16/bf16 sub-case of `convert_unary_cont_cuda` (which also does quant/strided).

**Current overrides (copy their shape for a new one, e.g. a PPU rope/rms_norm):**
| op | hook point | granularity | kernel |
|---|---|---|---|
| decode GEMV | `ggml_cuda_mul_mat` (ggml-cuda.cu) | sub-case (vec, ne[1]==1) | `mmvf-ppu.cuh` |
| FlashAttention (prefill) | `ggml_cuda_flash_attn_ext` (fattn.cu) | whole-op | `fattn-ppu.cuh` |
| convert f32↔f16/bf16 | `convert_unary_cont_cuda` (convert.cu) | sub-case (contiguous) | `convert-ppu.cuh` |

Only reach for a separate `ggml-ppu/` dir (à la `ggml-musa/`: GLOB ggml-cuda + `*-ppu.cu` + a top-level override
module) if the override count/build-glue gets heavy — with a handful and PTX-compatibility, in-tree `#if GGML_USE_PPU`
is lighter and correct. See [[frameworks-index]] for where ggml-musa lives to copy its CMake/GLOB pattern.

## Canonical implementations in the repo (the source of truth — read these, don't reinvent)

| what | file |
|---|---|
| FA asm helpers (aiu_load/+linear, ld_swzl/+trans, mma_f32/f16), standalone FA bench | `ppu_tests/fa_ppu.cu` |
| AIU full API reference + params + integration notes | `ppu_tests/AIU_NOTES.md`, `ppu_tests/README.md` |
| AIU/ldmatrix microbenches (verify an asm idea in isolation) | `ppu_tests/test_aiu_*.cu`, `test_ldmatrix_*.cu`, `test_mma_*.cu` |
| ggml FA kernel + launcher + dispatch | `ggml/src/ggml-cuda/fattn-ppu.cuh`, `fattn.cu` |
| ggml AIU header / mma helpers | `ggml/src/ggml-cuda/ppu-aiu.cuh`, `mma.cuh` |
| decode GEMV (register-streaming) + standalone bench | `ggml/src/ggml-cuda/mmvf-ppu.cuh`, `ppu_tests/gemv_ppu.cu` |
| vectorized convert + standalone bench | `ggml/src/ggml-cuda/convert-ppu.cuh`, `ppu_tests/convert_ppu.cu` |

**Source of truth OUTSIDE the repo (this Mac):** AIU copy atoms in
`/Users/qianxu/holmes/third_party/cutlass3/include/ppu/cute/arch/copy_acompute10000_aiu.hpp` (and `...10500...`);
FA2 PPU reference in `/Users/qianxu/flash-attention` (branches like `v2.7.2_ppu_1v6_preview`, `PPU_AIU_LOAD` /
`PPU_TSM_LD_SWZL` CopyAtoms gated by `USE_AIU`); cutlass CUDA-core mainloop (plain cp.async, NOT AIU) in
`include/ppu/cutlass/gemm/collective/acompute_simt_mma_multistage.hpp`.

## Verifying perf claims

The PPU HBM peak is **~2766 GB/s**. A **>100% "of peak"** result means the buffer was served from **LLC, not HBM** —
size the working set well past the LLC (sweep up to 256MB) to measure real HBM bandwidth. The standalone benches
(`*_ppu.cu`) have `*_NCU=1` env toggles for 1-launch/kernel clean ncu capture (`GEMV_NCU`, `FA_NCU`, `CONVERT_NCU`).
Validate FA2 numbers with `python fa_tflops.py` (flop = 4·B·Lq·Lkv·DIM, 8th arg = causal) — directly comparable to
the standalone perf lines.
