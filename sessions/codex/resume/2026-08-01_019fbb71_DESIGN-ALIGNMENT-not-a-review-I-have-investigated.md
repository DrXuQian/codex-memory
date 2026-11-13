# Resume brief: DESIGN ALIGNMENT, not a review. I have investigated and I want your judgement on the plan and on the risks I have
probably missed. Read the code; correct me where the findings below are wrong.

GOAL: build quactlize's kernels as a TORCH EXTENSION for the T-Head PPU, so the GEMM is reachable as
torch.ops.quactlize.* the way IST-DASLab/qutlass reaches torch.ops._qutlass_C. This unblocks three things that are
currently impossible: binding the GEMM at all, using torch as an INDEPENDENT accuracy oracle instead of a golden baked
into a .bin fixture, and driving perf runs from python with repetition and statistics.

REPO /root/marlin_ppu/quactlize (branch dev), submodule third_party/actlize (ppu-w4a16-dev).

WHAT I FOUND, and it is better than I expected. Check each:

F1. The tree ALREADY contains TensorRT-LLM's mixed-gemm preprocessing, ported and registered as torch ops:
    quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp uses torch::RegisterOperators under `acext::`
    (preprocess_weights_for_mixed_gemm, permute_B_rows_for_mixed_gemm, _subbyte_transpose,
    add_bias_and_interleave_int4s/int8s, symmetric_quantize_last_axis_of_batched_matrix, the int4/int8 pack pair).
    1384 lines with cutlass_preprocessors.cpp. There is NO build for it -- it has been parked unbuilt.

F2. third_party/actlize/cmake/PPUToolchain.cmake already supports what I thought it did not:
      - cutlass_build_dev_kernels compiles each .cu to .o with hgcc through add_custom_command, and passes -fPIC
        unconditionally (line 269). So device objects are already position independent.
      - cutlass_add_library(NAME SHARED ...) exists (line 285): it splits .cu from .cpp, sends .cu through hgcc,
        .cpp through normal CMake CXX, and calls add_library(... SHARED ...).
    So a .so containing PPU device code is already a supported shape. I had claimed the opposite.

F3. What actually blocks it is the BUILD MODEL, not the toolchain. build.sh overlays our sources INTO actlize's
    examples/ tree, flattening three directories into one, edits actlize's examples/CMakeLists.txt, restores it with
    git checkout on exit, and rm -rf's one shared build directory every run. It produces executables from an example
    directory. It cannot produce a python extension, and concurrent runs race.

WHAT I PROPOSE. Attack it.

P1. Stop overlaying. Give quactlize its own CMake project that consumes actlize as a library:
      find/add_subdirectory actlize -> use PPUToolchain -> cutlass_add_library(quactlize_C SHARED <our .cu> <thop .cpp>)
    and let setup.py drive that CMake (qutlass's setup.py drives a third_party cmake the same way).
P2. Register the GEMM as torch ops beside the existing acext:: ones, with the launcher taking typed pointers and
    REPORTING failure -- today fpA_intB_ppu.cuh returns silently on can_implement/workspace/initialize failure and the
    caller reads stale output.
P3. Keep the C++ harnesses. They are the only thing that works today and they must keep working while this lands.

RISKS I WANT YOUR JUDGEMENT ON -- and add the ones I have not thought of:

R1. ABI. hgcc "forwards unknown host flags" to a host compiler. Torch extensions are sensitive to
    _GLIBCXX_USE_CXX11_ABI and to the exact libstdc++. Does the device .o produced by hgcc participate in that at all,
    or is it opaque? What breaks first if the ABI disagrees, and how would it present?
R2. Symbol visibility and static registration. torch::RegisterOperators relies on static initialisers running at
    dlopen. Device objects linked into the same .so -- do they bring their own initialisers or runtime dependency
    (ppu::runtime, ppu::driver, ppu::hgrtc are IMPORTED targets) that must also be linked or preloaded?
R3. Two runtimes. If torch on the device already links the PPU runtime, does linking it again into our .so cause a
    duplicate-registration or double-initialisation problem?
R4. The generated-unit sweep. benchmarks/ currently generates one .cu per configuration through CMake. Inside an
    extension that becomes hundreds of device compiles per build. What is the right shape -- a small runtime-selected
    set, or keep the sweep out of the extension entirely?
R5. Is a torch extension even the right first step, or should the first step be a plain .so plus a ctypes/pybind
    shim, so that the torch ABI is not in the critical path of getting ANY python entry working?

Answer R5 explicitly -- if you think I should not start with a torch extension, say so and say what instead.

- **Thread ID:** `019fbb71-1ba6-7b01-be7c-b3243556865b`
- **Started / last event:** 2026-08-01 03:49 UTC → 2026-08-01 04:04 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T11-49-39-019fbb71-1ba6-7b01-be7c-b3243556865b.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "c39d6a2ee521fdf6de10725902dedb2f38abc232", "branch": "dev", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-01_019fbb71_DESIGN-ALIGNMENT-not-a-review-I-have-investigated.md](../transcripts/2026-08/2026-08-01_019fbb71_DESIGN-ALIGNMENT-not-a-review-I-have-investigated.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

DESIGN ALIGNMENT, not a review. I have investigated and I want your judgement on the plan and on the risks I have
probably missed. Read the code; correct me where the findings below are wrong.

GOAL: build quactlize's kernels as a TORCH EXTENSION for the T-Head PPU, so the GEMM is reachable as
torch.ops.quactlize.* the way IST-DASLab/qutlass reaches torch.ops._qutlass_C. This unblocks three things that are
currently impossible: binding the GEMM at all, using torch as an INDEPENDENT accuracy oracle instead of a golden baked
into a .bin fixture, and driving perf runs from python with repetition and statistics.

REPO /root/marlin_ppu/quactlize (branch dev), submodule third_party/actlize (ppu-w4a16-dev).

WHAT I FOUND, and it is better than I expected. Check each:

F1. The tree ALREADY contains TensorRT-LLM's mixed-gemm preprocessing, ported and registered as torch ops:
    quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp uses torch::RegisterOperators under `acext::`
    (preprocess_weights_for_mixed_gemm, permute_B_rows_for_mixed_gemm, _subbyte_transpose,
    add_bias_and_interleave_int4s/int8s, symmetric_quantize_last_axis_of_batched_matrix, the int4/int8 pack pair).
    1384 lines with cutlass_preprocessors.cpp. There is NO build for it -- it has been parked unbuilt.

F2. third_party/actlize/cmake/PPUToolchain.cmake already supports what I thought it did not:
      - cutlass_build_dev_kernels compiles each .cu to .o with hgcc through add_custom_command, and passes -fPIC
        unconditionally (line 269). So device objects are already position independent.
      - cutlass_add_library(NAME SHARED ...) exists (line 285): it splits .cu from .cpp, sends .cu through hgcc,
        .cpp through normal CMake CXX, and calls add_library(... SHARED ...).
    So a .so containing PPU device code is already a supported shape. I had claimed the opposite.

F3. What actually blocks it is the BUILD MODEL, not the toolchain. build.sh overlays our sources INTO actlize's
    examples/ tree, flattening three directories into one, edits actlize's examples/CMakeLists.txt, restores it with
    git checkout on exit, and rm -rf's one shared build directory every run. It produces executables from an example
    directory. It cannot produce a python extension, and concurrent runs race.

WHAT I PROPOSE. Attack it.

P1. Stop overlaying. Give quactlize its own CMake project that consumes actlize as a library:
      find/add_subdirectory actlize -> use PPUToolchain -> cutlass_add_library(quactlize_C SHARED <our .cu> <thop .cpp>)
    and let setup.py drive that CMake (qutlass's setup.py drives a third_party cmake the same way).
P2. Register the GEMM as torch ops beside the existing acext:: ones, with the launcher taking typed pointers and
    REPORTING failure -- today fpA_intB_ppu.cuh returns silently on can_implement/workspace/initialize failure and the
    caller reads stale output.
P3. Keep the C++ harnesses. They are the only thing that works today and they must keep working while this lands.

RISKS I WANT YOUR JUDGEMENT ON -- and add the ones I have not thought of:

R1. ABI. hgcc "forwards unknown host flags" to a host compiler. Torch extensions are sensitive to
    _GLIBCXX_USE_CXX11_ABI and to the exact libstdc++. Does the device .o produced by hgcc participate in that at all,
    or is it opaque? What breaks first if the ABI disagrees, and how would it present?
R2. Symbol visibility and static registration. torch::RegisterOperators relies on static initialisers running at
    dlopen. Device objects linked into the same .so -- do they bring their own initialisers or runtime dependency
    (ppu::runtime, ppu::driver, ppu::hgrtc are IMPORTED targets) that must also be linked or preloaded?
R3. Two runtimes. If torch on the device already links the PPU runtime, does linking it again into our .so cause a
    duplicate-registration or double-initialisation problem?
R4. The generated-unit sweep. benchmarks/ currently generates one .cu per configuration through CMake. Inside an
    extension that becomes hundreds of device compiles per build. What is the right shape -- a small runtime-selected
    set, or keep the sweep out of the extension entirely?
R5. Is a torch extension even the right first step, or should the first step be a plain .so plus a ctypes/pybind
    shim, so that the torch ABI is not in the critical path of getting ANY python entry working?

Answer R5 explicitly -- if you think I should not start with a torch extension, say so and say what instead.

## Last assistant conclusions

### 2026-08-01 04:04 UTC

## Verdict

Proceed with P1–P3, but not literally as written.

- F2 and F3 are substantially correct.
- F1 correctly identifies valuable source, but overstates how ready or aligned it is.
- P1 is the right architectural move, with several CMake/linking corrections.
- P2 is necessary and should be implemented through a Torch-free status-returning launcher.
- P3 is non-negotiable.
- R5: start with a Torch extension, not ctypes. More precisely, build an operator-only `.so` loaded by `torch.ops.load_library()`, without pybind or a Python module initializer.

## Findings

### F1 — source exists, but it is not presently a usable PPU preprocessing library

The 1,384-line count is exact across the two implementation files and header: 441 + 860 + 83.

The registrations exist at [weight_preprocess_ops.cpp](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:406), but there are material problems:

- The exact public names differ from your list. `permute_B_rows_for_mixed_gemm`, `add_bias_and_interleave_int4s`, and the int8 equivalent are registered with leading underscores. The Python façade calls the non-underscored names at [__init__.py](/root/marlin_ppu/quactlize/quactlize/__init__.py:50), so those calls cannot work.

- The Python `preprocess_weights_for_mixed_gemm(..., arch=80)` API does not match the registered C++ function. Its parameters are two booleans—`is_int8_mma` and `use_aiu_interleaved`—not an architecture integer ([weight_preprocess_ops.cpp](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:111)). Operator schema inference cannot recover C++ default arguments, so the Python call either has the wrong arity or treats `80` as the first boolean; it never means `arch`.

- The actual PPU interleave is compiled only under `USE_AIU` and requires `aiu_interleaved=true` ([cutlass_preprocessors.cpp](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:651)). The Python surface exposes neither correctly.

- These are CPU-only preprocessing ops—the code explicitly checks `CHECK_CPU`. That is reasonable for an offline reorder, but worth stating.

- The parked implementation is no longer the canonical production preprocessing code. The working harnesses use the newer derived placement in [unfused_weight_dequantize.hpp](/root/marlin_ppu/quactlize/quactlize/include/unfused_weight_dequantize.hpp:197). The comments say it replaced the old five-stage transform and corrected cases that the old formulation could mishandle. Before exposing the parked path, require randomized byte-for-byte equality against `xplane::place_derived` for every supported W4 shape.

- `symmetric_quantize_last_axis_of_batched_matrix` produces per-column scales, not general `group_size=128` GPTQ scales. It is not directly the producer for the proposed default GEMM API.

- The statement in `__init__.py` that every preprocessing op is a permutation is false: symmetric quantization changes representation, pack/unpack changes shape, and bias/interleave changes values.

At the start of inspection, tracked `dev` also lacked `thop/th_utils.h`, `utils/cuda/cuda_utils.h`, and `cutlass_extensions/.../mixed_gemm_B_layout.h`, so the parked code was not self-contained. Untracked shims for these paths and a `setup.py` appeared while I was inspecting; I did not create or assess that moving WIP. The semantic mismatches above remain regardless.

So: F1 is right as source archaeology, wrong if interpreted as “the preprocessing half is already ready to build and call.”

### F2 — correct, with important limits

Yes:

- `.cu` sources are compiled with hgcc through custom commands.
- `-fPIC` is unconditional at [PPUToolchain.cmake](/root/marlin_ppu/quactlize/third_party/actlize/cmake/PPUToolchain.cmake:260).
- `cutlass_add_library(... SHARED ...)` exists and combines normal C++ compilation with hgcc objects at [PPUToolchain.cmake](/root/marlin_ppu/quactlize/third_party/actlize/cmake/PPUToolchain.cmake:285).
- Actlize’s own library machinery also explicitly creates shared libraries from hgcc objects, so this is an intended build shape.

The limits are:

- `cutlass_add_library` does not accept `DEV_COMPILE_FLAGS`, unlike `cutlass_add_executable`. Target include directories, compile definitions, and Torch ABI flags do not automatically reach the hgcc custom command.
- The custom command tracks only the `.cu` as `MAIN_DEPENDENCY`; included headers do not trigger rebuilds. Today the clean rebuild hides this defect. Once builds become incremental, stale device objects become a correctness risk. Add hgcc depfiles or explicit header dependencies.
- `-fPIC` on the device object does not prove every PPU SDK archive linked into the `.so` is PIC. If any of `hggcrt1`, wrappers, or runtime libraries resolve to non-PIC static archives, the shared link can still fail.
- The helper creates the shape, but does not establish the Torch compile/link/load contract.

Therefore F2 is correct: the toolchain is not the fundamental blocker.

### F3 — correct

As written, [build.sh](/root/marlin_ppu/quactlize/build.sh:20):

- flattens `quactlize/include`, `tests`, and `benchmarks`;
- edits the submodule’s example list;
- restores it with `git checkout`;
- deletes one common example directory and one common build directory;
- drives executable targets only.

Concurrent invocations can remove each other’s overlay, overwrite the same CMake edit, or delete the other build. It cannot produce a packaged extension without being structurally rewritten.

## Judgment on the proposals

### P1 — yes, but treat actlize as headers/toolchain, not a conventional library

Use quactlize’s own top-level CMake project and an isolated setuptools build directory.

The target should explicitly:

- disable actlize examples, tests, tools, profiler, and generated library targets before `add_subdirectory(... EXCLUDE_FROM_ALL)`;
- `find_package(Torch CONFIG REQUIRED)`;
- compile Torch-facing `.cpp` with Torch’s include directories and exact C++ ABI setting;
- compile explicit kernel-instantiation `.cu` files through hgcc;
- link `Torch`, `CUTLASS`, `ppu::runtime`, and `ppu::driver` explicitly;
- set shared-library RPATH/load behavior intentionally;
- produce one operator library with no benchmark sources.

Do not rely on actlize’s directory-scoped `link_libraries(ppu::runtime)` at [actlize/CMakeLists.txt](/root/marlin_ppu/quactlize/third_party/actlize/CMakeLists.txt:275). A target created back in the parent quactlize directory will not inherit it. Also, the existing “RPATH” handling changes only `CMAKE_EXE_LINKER_FLAGS` and does not actually specify an RPATH, so it does not solve shared-library loading.

One comparison correction: current qutlass uses `CUDAExtension` for the actual extension; its preliminary CMake invocation mainly configures/populates CUTLASS. It is useful precedent for packaging, but not proof that its CMake builds the extension itself. See its [current setup.py](https://github.com/IST-DASLab/qutlass/blob/main/setup.py).

### P2 — yes, through a Torch-free core boundary

Do not make `fpA_intB_ppu.cuh` throw `TORCH_CHECK` directly. That would infect the harnesses and hgcc translation unit with Torch dependencies.

Use this layering:

1. An explicit-instantiation `.cu` exports a narrow C-compatible launch/query API using raw typed pointers, dimensions, workspace, and `hggcStream_t`.
2. It returns a project-owned status code plus the underlying `cutlass::Status`.
3. The Torch wrapper translates failure to `TORCH_CHECK`.
4. The C++ harness translates it to its existing failure accounting.

Propagate failure through the whole call chain:

- unsupported group/shape;
- `can_implement`;
- required workspace greater than available;
- `initialize`;
- `run`, which is currently ignored at [fpA_intB_ppu.cuh](/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh:128);
- immediate runtime launch error, if HGGC provides a non-synchronizing equivalent of
… [truncated 9011 chars]
