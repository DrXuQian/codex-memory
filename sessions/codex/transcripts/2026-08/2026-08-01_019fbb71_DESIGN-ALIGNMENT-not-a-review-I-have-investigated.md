# DESIGN ALIGNMENT, not a review. I have investigated and I want your judgement on the plan and on the risks I have
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

---

## User · 2026-08-01 03:49 UTC

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

## Assistant · 2026-08-01 03:49 UTC

I’ll trace the build scripts, toolchain helpers, kernel launch/error paths, preprocessing registration, and benchmark generation before judging each finding and proposal. I’ll keep this to design alignment—no edits.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"pwd && rg --files -g 'AGENTS.md' -g '!third_party/**' -g 'build.sh' -g 'CMakeLists.txt' -g 'setup.py' -g 'PPUToolchain.cmake' -g 'weight_preprocess_ops.cpp' -g 'cutlass_preprocessors.cpp' -g 'fpA_int …`
- `exec: const r = await tools.exec_command({cmd:"git status --short --branch && git submodule status && sed -n '1,260p' build.sh && sed -n '1,320p' CMakeLists.txt && sed -n '220,350p' third_party/actlize/cmake/PPUToolchain.cmake","workdir":"/root/m …`
- `exec: const r = await tools.exec_command({cmd:"wc -l quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp && rg -n \"RegisterOperators|TORCH_LIBRARY|preprocess_weights|symmet …`

</details>

## Assistant · 2026-08-01 03:50 UTC

The first correction is already concrete: the preprocessing code is present and unbuilt, but the Python façade and registrations do not fully agree. Several registered names are private (`acext::_permute...`, `acext::_add_bias...`), while `quactlize/__init__.py` calls the non-underscored forms. I’m checking whether this is only naming drift or reflects deeper device/CPU assumptions.

<details><summary>10 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"sed -n '1,470p' quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp && sed -n '1,140p' quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.h && sed -n '1,130p' quactlize/__init__.py  …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '1,180p' quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp && rg -n \"__global__|cuda|hgg|ppu|half|bfloat|memcpy|parallel|throw|assert|exit|arch|aiu|PACKED_INT2\" quactlize/c …`
- `exec: const r = await tools.exec_command({cmd:"rg --files quactlize/csrc | rg 'th_utils|cuda_utils' && sed -n '1,260p' quactlize/include/fpA_intB_ppu.cuh && sed -n '260,560p' quactlize/include/fpA_intB_ppu.cuh","workdir":"/root/marlin_ppu/quactli …`
- `exec: const r = await tools.exec_command({cmd:"rg --files third_party/actlize | rg '/(th_utils|cuda_utils)\\.h$' | head -30; sed -n '1,300p' quactlize/include/fpA_intB_ppu.cuh; sed -n '300,620p' quactlize/include/fpA_intB_ppu.cuh","workdir":"/roo …`
- `exec: const r = await tools.exec_command({cmd:"find . -type f \\( -name 'th_utils.h' -o -name 'cuda_utils.h' \\) -print; rg -n \"#define CHECK_CPU|FT_CHECK_WITH_INFO|FT_CHECK\\(\" third_party/actlize quactlize/csrc -g '*.h' -g '*.hpp' -g '*.cuh'  …`
- `exec: const r = await tools.exec_command({cmd:"find quactlize/csrc -maxdepth 5 -type f -print | sort && git show --stat --oneline c39d6a2 && git show --format=fuller --find-renames c39d6a2 -- quactlize/csrc quactlize/__init__.py | sed -n '1,260p' …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '1,220p' pyproject.toml; rg -n \"PPUToolchain|CUTLASS_PPU|ppu::runtime|ppu::driver|ppu::hgrtc|add_library\\(|find_package|HGGC|HGG|RPATH|WHOLE_ARCHIVE|--no-as-needed|dlopen|hggc\" third_party/ …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '1,230p' third_party/actlize/cmake/PPUToolchain.cmake; sed -n '250,360p' third_party/actlize/CMakeLists.txt; sed -n '1,100p' third_party/actlize/examples/CMakeLists.txt; rg -n \"function\\(cut …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '45,150p' third_party/actlize/CMakeLists.txt; sed -n '150,250p' third_party/actlize/CMakeLists.txt; rg -n \"CUTLASS_ENABLE_(EXAMPLES|TOOLS|TESTS|PROFILER|LIBRARY)|BUILD_TESTING|CMAKE_CXX_STAND …`
- `exec: const r = await tools.exec_command({cmd:"for p in /sim/eec/shared/junfu.qx/PPU_SDK /usr/local/PPU_SDK; do if [ -x \"$p/bin/hgcc\" ]; then echo \"SDK $p\"; \"$p/bin/hgcc\" --version | head -20; fi; done; find third_party/actlize -maxdepth 3  …`

</details>

## Assistant · 2026-08-01 03:51 UTC

The build helper is real, but it is less turnkey than P1 implies. `cutlass_add_library(... SHARED ...)` can emit the `.so`; it does not by itself inherit Torch’s compile/link contract, and when invoked outside the actlize directory it also does not inherit actlize’s directory-scoped runtime linkage. I’m separating “shared library mechanically possible” from “loadable Torch operator library.”

<details><summary>24 tool call(s)</summary>

- `exec: const r = await tools.web__run({search_query:[{q:"site:github.com/IST-DASLab/qutlass setup.py torch.ops _qutlass_C"},{q:"site:github.com/IST-DASLab/qutlass _qutlass_C TORCH_LIBRARY setup.py"}],response_length:"long"}); text(r);`
- `exec: const r = await tools.web__run({open:[{ref_id:"https://github.com/IST-DASLab/qutlass"},{ref_id:"https://raw.githubusercontent.com/IST-DASLab/qutlass/main/setup.py"},{ref_id:"https://raw.githubusercontent.com/IST-DASLab/qutlass/main/CMakeLis …`
- `exec: const r = await tools.web__run({open:[{ref_id:"https://raw.githubusercontent.com/IST-DASLab/qutlass/main/qutlass/csrc/bindings.cpp"},{ref_id:"https://raw.githubusercontent.com/IST-DASLab/qutlass/main/qutlass/__init__.py"},{ref_id:"https://r …`
- `exec: const r = await tools.exec_command({cmd:"python3 - <<'PY'\ntry:\n import torch, sys\n print('python', sys.version.split()[0])\n print('torch', torch.__version__)\n print('torch_file', torch.__file__)\n print('abi', getattr(torch._C, '_GLIBC …`
- `exec: const r = await tools.exec_command({cmd:"git log --all --oneline -- tools/acext_preprocess quactlize/csrc/preprocess | head -40; rg -n \"acext_preprocess|preprocess_weights_for_mixed_gemm|th_utils|cuda_utils\" README.md docs ci tests benchm …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '1,340p' quactlize/include/unfused_weight_dequantize.hpp; sed -n '1,140p' docs/FORMATS_AND_REORDER.md; git show 8dab003:tools/acext_preprocess/thop/weight_preprocess_ops.cpp >/dev/null && echo …`
- `exec: const r = await tools.web__run({search_query:[{"q":"T-Head PPU PyTorch hggc torch PPU backend current stream extension"},{"q":"site:github.com hggcStream_t torch PPU extension"},{"q":"site:github.com \"torch.ppu\" T-Head"},{"q":"site:github …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"GENERATED \\.cu|_UNIT_SRCS|file\\(WRITE \\\"\\$\\{_.*\\.cu|ppu_w4a16_executable\\(\" quactlize/csrc/CMakeLists.txt.in; sed -n '240,920p' quactlize/csrc/CMakeLists.txt.in","workdir":"/root/mar …`
- `exec: const r = await tools.exec_command({cmd:"find third_party/actlize/include -path '*mixed_gemm_B_layout.h' -o -path '*cuda_utils.h' -o -path '*th_utils.h'; find third_party/cutlass -path '*mixed_gemm_B_layout.h' -o -path '*cuda_utils.h' -o -p …`
- `exec: const r = await tools.exec_command({cmd:"find . -type f -name 'mixed_gemm_B_layout.h' -print; rg -n \"ColumnMajorTileInterleave|OpMultiplyAddDequantizeInterleavedBToA\" third_party/actlize/include third_party/cutlass/include | head -80; git …`
- `exec: const r = await tools.exec_command({cmd:"find quactlize/csrc/preprocess/utils -maxdepth 5 -type f -print -exec sed -n '1,80p' {} \\; ; stat -c '%n %y' quactlize/csrc/preprocess/utils quactlize/csrc/preprocess/utils/* 2>/dev/null; git status …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"cutlass_add_library\\(\" third_party/actlize --glob 'CMakeLists.txt' --glob '*.cmake'; rg -n \"add_library\\([^\\n]*SHARED|SHARED\" third_party/actlize --glob 'CMakeLists.txt' --glob '*.cmake …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '80,180p' third_party/actlize/tools/library/CMakeLists.txt; sed -n '1,80p' third_party/actlize/test/unit/CMakeLists.txt; git -C third_party/actlize log -1 --format=fuller -- cmake/PPUToolchain …`
- `exec: const r = await tools.exec_command({cmd:"find /root /usr/local /usr/include -type f \\( -name 'mixed_gemm_B_layout.h' -o -name 'th_utils.h' \\) -print 2>/dev/null | head -100; rg -n \"#define FT_CHECK|FT_CHECK_WITH_INFO|CHECK_CPU|CHECK_CONT …`
- `exec: const r = await tools.exec_command({cmd:"git status --short; find quactlize/csrc/preprocess -maxdepth 7 -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\\n' | sort; find /root/marlin_ppu/Kernels/general/w4a16_gemm/fpA_intB_standalone/cpp/tensorr …`
- `exec: const r = await tools.exec_command({cmd:"find /root/marlin_ppu/Kernels/general/w4a16_gemm/fpA_intB_standalone/cpp/tensorrt_llm -type f \\( -name 'th_utils.h' -o -name 'cuda_utils.h' \\) -print | head -30; find /root/marlin_ppu/Kernels/moe_f …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '600,690p' quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp; sed -n '690,860p' quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp; sed -n '170,420p' quactli …`
- `exec: const r = await tools.exec_command({cmd:"python3 - <<'PY'\nimport torch, pathlib\np=pathlib.Path(torch.utils.cmake_prefix_path)/'Torch'/'TorchConfig.cmake'\nprint(p)\nfor i,line in enumerate(p.read_text().splitlines(),1):\n if 'TORCH_CXX_FL …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"TORCH_CXX_FLAGS|GLIBCXX_USE_CXX11_ABI\" /root/miniconda3/lib/python3.12/site-packages/torch/share/cmake /root/miniconda3/lib/python3.12/site-packages/torch/include/torch | head -80; python3 - …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"GLIBCXX_USE_CXX11_ABI|_GLIBCXX\" /root/miniconda3/lib/python3.12/site-packages/torch/utils/cpp_extension.py | head -40; sed -n '1620,1660p' /root/miniconda3/lib/python3.12/site-packages/torch …`
- `exec: const r = await tools.exec_command({cmd:"rg -n \"CXX11_ABI\" /root/miniconda3/lib/python3.12/site-packages/torch | head -80","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":10000}); text(r.output);`
- `exec: const r = await tools.web__run({search_query:[{"q":"site:pytorch.org/docs torch.ops.load_library custom C++ operators shared library TORCH_LIBRARY"},{"q":"site:docs.pytorch.org custom C++ operators TORCH_LIBRARY load_library"},{"q":"site:py …`
- `exec: const r = await tools.web__run({search_query:[{"q":"site:docs.pytorch.org cpp_extension ABI compiler _GLIBCXX_USE_CXX11_ABI"},{"q":"site:pytorch.org cpp extension _GLIBCXX_USE_CXX11_ABI undefined symbol"}],"response_length":"medium"}); text …`
- `exec: const r = await tools.exec_command({cmd:"sed -n '1,220p' tests/test_fpA_intB_ppu.cu; sed -n '430,810p' benchmarks/bench_cutlass_w4a16.cu; sed -n '300,345p' quactlize/include/moe_grouped_ppu.cuh; sed -n '250,285p' benchmarks/lowbit_moe_bench …`

</details>

## Assistant · 2026-08-01 04:00 UTC

The largest missed risk is not ABI—it is semantic layout drift. The parked Torch preprocessing path is not currently the preprocessing path the working harnesses validate: the latter replaced the old five-stage transform with `xplane::place_derived`, while the parked code still contains the older transform. Worse, its Python `arch` argument is presently passed into a C++ `bool is_int8_mma` slot, and the PPU `aiu_interleaved` path is not exposed. I’m folding that into the landing order because otherwise the first Torch accuracy test will diagnose the wrong layer.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"nl -ba quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp | sed -n '1,230p'; nl -ba quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp | sed -n '400,450p'; nl -ba quactlize/csrc/preproces …`
- `exec: const r = await tools.exec_command({cmd:"nl -ba third_party/actlize/cmake/PPUToolchain.cmake | sed -n '135,215p'; nl -ba third_party/actlize/cmake/PPUToolchain.cmake | sed -n '238,325p'; nl -ba third_party/actlize/CMakeLists.txt | sed -n '6 …`
- `exec: const r = await tools.exec_command({cmd:"git status --short; find quactlize/csrc/preprocess -maxdepth 7 -type f -newermt '2026-08-01 11:50:00 +0800' -printf '%p\\n' | sort","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_o …`

</details>

## Assistant · 2026-08-01 04:04 UTC

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
- immediate runtime launch error, if HGGC provides a non-synchronizing equivalent of “peek last error.”

Do not throw C++ exceptions across the hgcc/C++ boundary, and do not pass `std::string`, `std::vector`, Torch types, or CUTLASS template types across it.

One further correction: the candidate `fpA_intB_ppu` launcher is not yet a verified production kernel. Its own test says outputs are “garbage-by-design” and it does not test correctness ([test_fpA_intB_ppu.cu](/root/marlin_ppu/quactlize/tests/test_fpA_intB_ppu.cu:1)). Binding it is a good way to obtain the missing oracle, but the first Torch milestone must be described as validation, not shipping.

### P3 — yes

Keep `build.sh` and the current harness targets until the same kernel instantiation passes through both entry points.

The shared core launcher must remain Torch-free so that:

- harnesses continue to compile without libtorch;
- Torch integration failures stay distinguishable from kernel failures;
- both paths exercise identical arguments, preprocessing, stream, and status handling.

Only retire the overlay after equivalent native CMake harness targets are green.

## Risks R1–R5

### R1 — hgcc objects are not ABI-opaque

The embedded device image may be opaque, but the `.o` also contains host launch stubs and likely device-registration glue. That host portion participates in the C++ ABI.

If the `.cu` sees no Torch headers and communicates through a C/POD boundary, `_GLIBCXX_USE_CXX11_ABI` has little practical effect on that boundary. It remains critical for every Torch-facing `.cpp`.

Failure presentation, roughly in order:

- link-time unresolved symbols;
- `dlopen` failure with missing `c10`/`torch` symbols or `std::__cxx11` in the mangled name;
- `GLIBCXX_x.y.z not found` when the compiler emitted references newer than the runtime libstdc++;
- crashes or corrupted exceptions/strings if mismatched C++ types actually cross a boundary.

Build against the target machine’s PPU Torch, query `torch.compiled_with_cxx11_abi()`, and pass that exact value explicitly. Also record hgcc’s host compiler from `hgcc -v`. Never solve this with a statically linked second libstdc++.

### R2 — static registration should work, but explicit linkage and artifact inspection are required

Torch registration initializers run when the `.so` is loaded. Prefer modern `TORCH_LIBRARY`/`TORCH_LIBRARY_IMPL` rather than adding more deprecated `torch::RegisterOperators`; these APIs are the standard backend-specific registration mechanism. [PyTorch registration documentation](https://docs.pytorch.org/cppdocs/api/library/registration.html).

Device objects probably contain their own HGGC registration initializers, analogous to CUDA fat-binary registration, but that cannot be proven from CMake source. Verify the built artifact with:

- `readelf` for `.init_array`;
- `readelf -d` for all expected `DT_NEEDED` entries;
- `ldd -r` for unresolved relocations;
- an actual load-and-one-launch test.

Link `ppu::runtime` and `ppu::driver`. Do not link `ppu::hgrtc` unless runtime compilation is actually used; it is optional and not part of the current kernel path.

Directly linking hgcc objects into the `.so` avoids archive dead-stripping. If they are later hidden inside a static archive, add an explicit anchor or whole-archive handling.

### R3 — dynamic linkage normally does not create a second runtime

If Torch and the extension depend on the same shared library/SONAME, the dynamic loader reuses the existing mapping. Linking it from two DSOs is normal and should not cause a second initialization.

The actual hazards are:

- Torch built against SDK version A while the extension links SDK version B;
- two copies with different SONAMEs or paths;
- a runtime statically embedded in either component;
- ELF symbol interposition between incompatible runtime versions;
- bundling PPU runtime libraries into the wheel.

Use the exact SDK used to build the PPU Torch distribution. Compare `ldd`, SONAMEs, build IDs, and `/proc/self/maps` after loading Torch and the extension. Do not use `LD_PRELOAD` as the default solution; it can conceal version skew.

### R4 — keep the sweeps entirely out of the extension

This is larger than “hundreds.” With current default axes, the CMake template generates:

- 42 GEMV translation units;
- 15 split-K units;
- 600 MoE units before compile-time legality filtering.

The extension should contain a small, finite set of compiled production tactics and select among them at runtime. “Runtime-selected” still means every candidate is compiled ahead of time.

Keep all sweeps as separate benchmark targets. Their output should generate or inform a versioned tactic table consumed by the extension. Start with one correctness-proven W4A16 configuration, then add a decode and prefill winner only when data justifies them.

### R5 — start with the Torch extension

Do not make ctypes or pybind the first Python path.

A ctypes wrapper taking `tensor.data_ptr()` integers would not safely solve:

- current device selection;
- current Torch stream;
- allocator lifetime;
- workspace lifetime;
- multi-device execution;
- error integration.

A pybind wrapper that accepts Torch tensors puts the Torch ABI back into the path anyway, while adding Python ABI and module-initializer concerns.

The best first shape is an operator-only shared library:

- register `torch.ops.quactlize.*` with `TORCH_LIBRARY`;
- omit pybind and `Python.h`;
- load it from `quactlize/__init__.py` using `torch.ops.load_library(path)`.

PyTorch explicitly supports this pattern for custom operators without a Python module initializer. [Official custom-operator tutorial](https://docs.pytorch.org/tutorials/advanced/cpp_custom_ops.html).

A tiny non-shipping C ABI `.so` smoke test is worthwhile to isolate HGGC shared-link/runtime failures, but it should not become the public Python interface.

## Important risks missing from the list

1. **Torch stream integration.** The launcher currently accepts `nullptr` streams in harnesses. The extension must launch on Torch’s current stream, not merely the default HGGC stream, and must install the correct device guard.

2. **Workspace/output allocation.** Allocate output and workspace through Torch on the input device. A temporary raw HGGC allocation may synchronize on destruction, distort benchmarks, or race an asynchronous kernel.

3. **Preprocessing identity.** Define exactly whether the op accepts logical packed W4 or already-`aiu256`-interleaved W4. A tensor’s dtype and shape cannot identify that physical format. Use an unambiguous operator/API name and version the layout contract.

4. **Namespace collision.** `acext::` may already be owned by a vendor package in the PPU Torch process. Duplicate registration can abort library loading. Register the shipped surface under `quactlize::`; provide compatibility aliases only after proving they cannot collide. PyTorch likewise recommends project-specific namespaces to avoid collisions. [torch.library documentation](https://docs.pytorch.org/docs/stable/library.html).

5. **Incremental-build correctness.** Stopping clean rebuilds exposes the missing hgcc header dependency tracking and the fact that target properties do not reach device custom commands.

6. **Build isolation.** The current [pyproject.toml](/root/marlin_ppu/quactlize/pyproject.toml:1) does not make Torch available to an isolated build. Initially require `pip install --no-build-isolation`, or implement a backend that deliberately discovers the already-installed vendor Torch. Adding generic PyPI `torch` as a build requirement risks selecting the wrong runtime.

7. **Oracle independence.** Compute the reference from the original logical quantized values using pure Torch dequantization plus preferably FP32 matmul. Do not use the extension’s preprocessing/dequantization code to reconstruct the expected result.

8. **Performance synchronization.** Python wall-clock timing of asynchronous launches is meaningless without events or synchronization. Warm up, use the current PPU/Torch event API if available, and synchronize outside the operator—not inside every launch.

## Recommended landing order

1. Establish the target PPU Torch’s device type, current-stream API, C++ ABI, SDK runtime identity, and compiler versions.
2. Refactor one W4A16 launcher to return complete status, shared by the existing harness.
3. Build one hgcc kernel into a standalone shared-library smoke artifact and inspect its linkage/initializers.
4. Build `quactlize_ops.so` with one `TORCH_LIBRARY` op, load it with `torch.ops.load_library`, and launch one fixed tactic.
5. Port or validate the canonical `xplane` preprocessing path byte-for-byte; do not expose the parked API unchanged.
6. Add randomized Torch-oracle correctness tests, then Python event-based perf tests.
7. Add only proven production tactics. Keep all generators and sweeps in separate benchmark targets.
8. Retire the overlay only after the native-CMake harnesses have parity.

No device build was run here because this checkout does not have the PPU SDK/hgcc available.
