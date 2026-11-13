# Read the code. Two questions, and a hard constraint that changes how to weigh the answers.

REPO /root/marlin_ppu/quactlize (branches main, dev) and its third_party/actlize submodule (ppu-w4a16-dev), which
holds the collective (include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp) and the converter
(include/cutlass/fast_numeric_conversion_for_mix_gemm.h).

THE CONSTRAINT, which is new and binding: the product must support GGUF k-quants, GPTQ and AWQ. An OFFLINE REORDER of
the weights is allowed. AN INCREASE IN STORED BYTES IS NOT -- not for the weights, not for the scales, not for the
zeros. Any design that materialises a wider scale representation on device is disqualified however fast it is. Judge
everything below against that.

Q1. WHAT IN THIS CODE IS HACKY -- informal, one-off, or maintained only by the person who wrote it -- and what would
    you rewrite rather than patch? Be concrete, file:line. I am not asking for style. I am asking which constructs
    will produce a WRONG NUMBER or an unbuildable tree when someone extends them, and which are merely ugly. Rank by
    that difference. Things I already suspect, so disagree with me if you can:
      - the scale channel's positional cute::tuple with mode-dependent indices
      - two layouts named sS over one buffer
      - #if-gated members whose users sit outside the #if
      - the generated-.cu-per-configuration sweep machinery
      - build.sh's overlay-into-actlize's-example-tree model
      - the offline python in tools/ versus the device-side decode in gguf_packed_scale.h: one bit map or two?
    Say which of these are symptoms of ONE structural cause.

Q2. STRUCTURE. Compare against TensorRT-LLM's mixed-input W4A16 path -- cutlass_extensions' fpA_intB gemm, its
    interleaved weight-only preprocessing (preprocess_weights_for_mixed_gemm / the row-major-to-tile-interleave
    permutations), its per-format QuantOp taxonomy and its launcher/tile-config selection. If you cannot read it from
    here, say so and reason from what a reader of that codebase would expect instead of inventing details.
    What does TRT-LLM get structurally right that this tree does not, specifically for supporting SEVERAL quantised
    formats behind one kernel? Name the abstraction boundaries: where does format-specific knowledge live there, and
    where does it leak here?

Q3. Given the constraint, which of these can be supported with NO stored-byte increase, and what is missing for each:
      GGUF Q4_K (int4, gs=32, affine d/dmin, 12 B of 6-bit codes per superblock)
      GGUF Q3_K (int2+int1 planes, gs=16, symmetric, scale = d*(sc6-32))
      GGUF Q5_K (int4+int1), GGUF Q6_K (int4+int2, signed int8 scales), GGUF Q2_K (affine, 4+4 bit)
      GPTQ int4 (symmetric, gs=128, q_signed = q-8, g_idx possible)
      AWQ int4 (asymmetric, gs=128, zero-point as int4, its own interleave)
    For each say: does the DEVICE path already exist, does the OFFLINE reorder exist, is it validated against an
    independent golden, and what specifically is missing. Where the answer is "the scale must be decoded on device
    because storing it widened would breach the constraint", say so -- that is the interesting case and it is the one
    I have been treating as optional.

Do not restate architecture. Findings, and a judgement.

- **Thread ID:** `019fbb39-f5af-79b3-8a04-ee5fb3eabc9d`
- **Started / last event:** 2026-08-01 02:49 UTC → 2026-08-01 03:03 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T10-49-25-019fbb39-f5af-79b3-8a04-ee5fb3eabc9d.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "80dfeec20d06741227fd30a1c54ee7a167d64df6", "branch": "dev", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-01 02:49 UTC

Read the code. Two questions, and a hard constraint that changes how to weigh the answers.

REPO /root/marlin_ppu/quactlize (branches main, dev) and its third_party/actlize submodule (ppu-w4a16-dev), which
holds the collective (include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp) and the converter
(include/cutlass/fast_numeric_conversion_for_mix_gemm.h).

THE CONSTRAINT, which is new and binding: the product must support GGUF k-quants, GPTQ and AWQ. An OFFLINE REORDER of
the weights is allowed. AN INCREASE IN STORED BYTES IS NOT -- not for the weights, not for the scales, not for the
zeros. Any design that materialises a wider scale representation on device is disqualified however fast it is. Judge
everything below against that.

Q1. WHAT IN THIS CODE IS HACKY -- informal, one-off, or maintained only by the person who wrote it -- and what would
    you rewrite rather than patch? Be concrete, file:line. I am not asking for style. I am asking which constructs
    will produce a WRONG NUMBER or an unbuildable tree when someone extends them, and which are merely ugly. Rank by
    that difference. Things I already suspect, so disagree with me if you can:
      - the scale channel's positional cute::tuple with mode-dependent indices
      - two layouts named sS over one buffer
      - #if-gated members whose users sit outside the #if
      - the generated-.cu-per-configuration sweep machinery
      - build.sh's overlay-into-actlize's-example-tree model
      - the offline python in tools/ versus the device-side decode in gguf_packed_scale.h: one bit map or two?
    Say which of these are symptoms of ONE structural cause.

Q2. STRUCTURE. Compare against TensorRT-LLM's mixed-input W4A16 path -- cutlass_extensions' fpA_intB gemm, its
    interleaved weight-only preprocessing (preprocess_weights_for_mixed_gemm / the row-major-to-tile-interleave
    permutations), its per-format QuantOp taxonomy and its launcher/tile-config selection. If you cannot read it from
    here, say so and reason from what a reader of that codebase would expect instead of inventing details.
    What does TRT-LLM get structurally right that this tree does not, specifically for supporting SEVERAL quantised
    formats behind one kernel? Name the abstraction boundaries: where does format-specific knowledge live there, and
    where does it leak here?

Q3. Given the constraint, which of these can be supported with NO stored-byte increase, and what is missing for each:
      GGUF Q4_K (int4, gs=32, affine d/dmin, 12 B of 6-bit codes per superblock)
      GGUF Q3_K (int2+int1 planes, gs=16, symmetric, scale = d*(sc6-32))
      GGUF Q5_K (int4+int1), GGUF Q6_K (int4+int2, signed int8 scales), GGUF Q2_K (affine, 4+4 bit)
      GPTQ int4 (symmetric, gs=128, q_signed = q-8, g_idx possible)
      AWQ int4 (asymmetric, gs=128, zero-point as int4, its own interleave)
    For each say: does the DEVICE path already exist, does the OFFLINE reorder exist, is it validated against an
    independent golden, and what specifically is missing. Where the answer is "the scale must be decoded on device
    because storing it widened would breach the constraint", say so -- that is the interesting case and it is the one
    I have been treating as optional.

Do not restate architecture. Findings, and a judgement.

## Assistant · 2026-08-01 02:49 UTC

I’ll inspect both branches and the pinned submodule, including history/build tooling where it bears on “maintained only by the author.” I’ll anchor the judgment to exact file:line references and treat any widened on-device scale/zero materialization as disqualifying.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"git status --short --branch && git branch -avv && git submodule status && rg --files -g 'AGENTS.md' -g '!third_party/**' .. | head -50","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000, …`
- `exec: const r = await tools.exec_command({"cmd":"find . -maxdepth 3 -type f | sort | sed -n '1,240p' && git log --oneline --decorate --graph --all -30 && git -C third_party/actlize status --short --branch && git -C third_party/actlize branch -avv …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"PPU_|Packed|GGUF|Q[23456]_K|GPTQ|AWQ|QuantOp|preprocess_weights|interleave|sS|scale|zero|g_idx\" quactlize benchmarks tools CMakeLists.txt build.sh README.md docs third_party/actlize/includ …`

</details>

## Assistant · 2026-08-01 02:49 UTC

The first pass already exposes an important split: `main` contains the shippable wrapper/tests, while `dev` adds a very large derivation/sweep record; the Actlize pin is at the remote tip, with its local branch label one commit behind. I’m now separating production defects from experimental scaffolding, because several alarming constructs are intentionally confined to `dev/` while others sit on the live include path.

<details><summary>18 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"git diff --stat main..dev && git diff --name-status main..dev && git ls-tree -r --name-only main | sort && git ls-tree -r --name-only dev | sort | sed -n '1,360p'","workdir":"/root/marlin_ppu/quact …`
- `exec: const r = await tools.exec_command({"cmd":"wc -l third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h third_party/actlize/inclu …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1,280p;430,760p;920,1270p;1270,1645p;1645,1935p'","workdir":"/root/marlin_ppu/quactlize", …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '438,755p' && nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multi …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '710,1010p' && nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mult …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1003,1174p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tok …`
- `exec: const r = await tools.exec_command({"cmd":"git -C third_party/actlize blame -L 1657,1702 -- include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp && git -C third_party/actlize show 71a4b630:include/cutlass/gemm/collective/p …`
- `exec: const r = await tools.exec_command({"cmd":"git -C third_party/actlize show 71a4b630:include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | rg -n -C 15 \"if constexpr \\(false\\)\" && rg -n \"if constexpr \\(false\\).*else| …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n 'assert.false|if constexpr.*false' third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp && git -C third_party/actlize show 71a4b630:include/cutlass/gemm/ …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '1,360p' && nl -ba quactlize/include/gguf_scale_layout.hpp | sed -n '1,220p' && nl -ba quactlize/include/gguf_scale_decode.hp …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"pack|scale|bit|shift|Q[23456]_K|q[23456]k|gold|reference|assert|compare|bad|g_idx|GPTQ|AWQ|zero\" tools/*.py quactlize/include/xplane_offline.hpp quactlize/include/unfused_weight_dequantize …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/include/fpA_intB_ppu.cuh | sed -n '1,240p'; nl -ba quactlize/include/moe_grouped_ppu.cuh | sed -n '1,460p'; nl -ba quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp | sed -n '1, …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/include/moe_grouped_ppu.cuh | sed -n '35,220p' && nl -ba quactlize/include/moe_grouped_ppu.cuh | sed -n '220,420p' && nl -ba quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp |  …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/include/moe_grouped_ppu.cuh | sed -n '258,405p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":30000}); text(r.output);`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '1,330p' && nl -ba third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '33 …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"PlaneB2|MixGemm2PlaneFor|NoZero|ptr_B2|dB2|kSymBias2Plane\" third_party/actlize/include/cutlass quactlize/include | sed -n '1,360p' && git -C third_party/actlize log --format='%h %an %s' -- …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba build.sh | sed -n '1,340p'; nl -ba CMakeLists.txt | sed -n '1,300p'; nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '1,360p'; nl -ba dev/sweep.sh | sed -n '1,360p'; rg -n \"generate|\\.cu| …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba CMakeLists.txt; nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '1,230p'; nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '530,750p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms" …`

</details>

## Assistant · 2026-08-01 02:52 UTC

A hard-constraint consequence is becoming clear: most of the advertised GGUF support is currently a widened intermediate (`fp16 scale [+ zero]`), so it does not qualify. The only native-byte scale consumer is a Q4_K-only macro path, and even that decodes into fp16 shared-memory planes inside the kernel (temporary shared memory, not stored model bytes); I’m treating that as allowed because it does not materialize a persistent device/HBM representation.

<details><summary>6 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"rg --files tests benchmarks tools quactlize/include | sort && rg -n \"gold|MATCH|bad=|reference|independent|Q[23456]|q[23456]|GPTQ|AWQ|packed\" tests benchmarks tools quactlize/include | sed -n '1, …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba tests/rwmoep_loader.hpp | sed -n '1,300p'; nl -ba tests/test_q4k_packed_gemm.cu | sed -n '1,310p'; nl -ba tests/test_q4k_native_scale.cu | sed -n '1,280p'; nl -ba tests/test_q3_bconcat_real. …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba tests/test_q4k_packed_gemm.cu | sed -n '190,285p'; nl -ba tests/test_q4k_native_scale.cu | sed -n '1,260p'; nl -ba tests/test_q3_bconcat_real.cu | sed -n '1,180p'","workdir":"/root/marlin_pp …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba tests/test_lowbit_grouped.cu | sed -n '1,330p'; nl -ba quactlize/include/gemv_lowbit/gemv_wformat.hpp | sed -n '1,260p'; nl -ba quactlize/include/gemv_lowbit/gemv_launcher.hpp | sed -n '1,26 …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"real_q2|Q2_K|q2k\" tests tools benchmarks quactlize/include | sed -n '1,260p' && nl -ba tests/test_lowbit_grouped.cu | sed -n '195,330p' && nl -ba tools/dump_real_weights.py | sed -n '50,28 …`
- `exec: const cmds = [ { cmd: "git ls-tree main third_party/actlize && git ls-tree dev third_party/actlize && git diff --stat main..dev && git diff --name-status main..dev | sed -n '1,120p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10 …`

</details>

## Assistant · 2026-08-01 02:56 UTC

The comparison point is now clear enough to verify against NVIDIA’s own source: TRT-LLM makes quantization mode and preprocessing explicit, while this tree infers both from tuple shape and build flags. I’m checking exact upstream boundaries and then I’ll give the per-format verdict without crediting synthetic tests as independent validation.

<details><summary>13 tool call(s)</summary>

- `exec: const r = await tools.web__run({search_query:[ {q:"site:github.com/NVIDIA/TensorRT-LLM \"preprocess_weights_for_mixed_gemm\""}, {q:"site:github.com/NVIDIA/TensorRT-LLM \"fpA_intB\" \"QuantOp\""}, {q:"site:github.com/NVIDIA/TensorRT-LLM \"Cu …`
- `exec: const r = await tools.exec_command({ cmd: "trt_checkout=$(mktemp -d /tmp/trtllm-source.XXXXXX) && test -n \"$trt_checkout\" && git clone --depth 1 --filter=blob:none --sparse https://github.com/NVIDIA/TensorRT-LLM.git \"$trt_checkout\" && g …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"preprocess_weights_for_mixed_gemm|fpA_intB|QuantOp|CutlassGemmConfig|weightOnly|interleav\" cpp/tensorrt_llm -g '*.{h,hpp,cpp,cu,cuh}' | sed -n '1,360p'", workdir: "/tmp/trtllm-source.5wQw0 …`
- `exec: const r = await tools.exec_command({ cmd: "git rev-parse HEAD; nl -ba cpp/tensorrt_llm/cutlass_extensions/include/cutlass_extensions/weight_only_quant_op.h; nl -ba cpp/tensorrt_llm/kernels/cutlass_kernels/cutlass_preprocessors.cpp | sed -n  …`
- `exec: const cmds = [ { cmd: "nl -ba include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp | sed -n '160,205p;405,515p;675,760p;1040,1135p;1270,1375p'", workdir: "/root/marlin_ppu/quactlize/third_party/actlize", yield_time_ms: 10000,  …`
- `exec: const cmds = [ { cmd: "git diff --name-status main..dev | rg -v '^.[[:space:]]+dev/fold_derivation' | sed -n '1,160p'; git log --format='%h %an %s' --all --max-count=30", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_outp …`
- `exec: const cmds = [ { cmd: "nl -ba include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '115,175p;190,255p;425,510p;550,620p;680,755p'", workdir: "/root/marlin_ppu/quactlize/third_party/actlize", yield_time_ms: 10000,  …`
- `exec: const cmds = [ { cmd: "nl -ba build.sh | sed -n '1,220p'; nl -ba CMakeLists.txt; nl -ba quactlize/csrc/CMakeLists.txt.in | sed -n '1,230p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 25000 }, { cmd: "nl …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '710,748p;1114,1262p;1318,1402p;1494,1520p'", workdir: "/root/marlin_ppu/quactlize/third_party/actlize", yield …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba include/cutlass/gguf_packed_scale.h | sed -n '1,112p;145,225p;245,305p'; nl -ba include/cutlass/fast_numeric_conversion_for_mix_gemm.h | sed -n '50,165p;230,285p;742,970p'", workdir: "/root/ …`
- `exec: const r = await tools.exec_command({ cmd: "git blame -L 1668,1700 -- include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp; git log -L 1680,1695:include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp --oneli …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n \"NDEBUG|CMAKE_BUILD_TYPE|Release\" CMakeLists.txt cmake examples/CMakeLists.txt | sed -n '1,160p'", workdir: "/root/marlin_ppu/quactlize/third_party/actlize", yield_time_ms: 10000, max_outpu …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba benchmarks/run_batch.sh | sed -n '84,104p'; nl -ba tests/test_q3_bconcat_real.cu | sed -n '1,32p;65,100p;200,228p'; nl -ba tests/test_q65_bconcat_real.cu | sed -n '1,25p;60,90p;102,130p;160, …`

</details>

## Assistant · 2026-08-01 03:00 UTC

I’m treating the new constraint literally: a decoded scalar in a register at the instruction that consumes it is unavoidable, but an expanded fp16 scale/zero array in HBM or a shared-memory tile is a “materialised wider representation.” On that reading, the existing Q4_K packed path is functionally interesting but disqualified because it decodes into fp16 shared-memory planes.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.web__run({open:[ {ref_id:"https://github.com/NVIDIA/TensorRT-LLM/blob/09b6bea1642aed3b533cbb6b71db586e19d5f300/cpp/tensorrt_llm/cutlass_extensions/include/cutlass_extensions/weight_only_quant_op.h#L27-L43"}, {ref_id:"h …`
- `exec: const r = await tools.web__run({open:[ {ref_id:"https://raw.githubusercontent.com/NVIDIA/TensorRT-LLM/09b6bea1642aed3b533cbb6b71db586e19d5f300/cpp/tensorrt_llm/cutlass_extensions/include/cutlass_extensions/weight_only_quant_op.h"}, {ref_id: …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba docs/FORMATS_AND_REORDER.md | sed -n '1,82p'; nl -ba quactlize/include/gguf_scale_layout.hpp | sed -n '35,165p'; nl -ba quactlize/include/gguf_scale_decode.hpp | sed -n '30,135p'; nl -ba too …`

</details>

## Assistant · 2026-08-01 03:03 UTC

The judgement: this is a capable derivation/benchmark tree, but not yet a safe multi-format product path. Under the new constraint, the only currently qualifying format is restricted GPTQ symmetric without `g_idx`. The Q4_K packed implementation is not qualifying: it preserves global-memory bytes, then expands them into fp16 scale/zero shared-memory tiles.

Both `main` and `dev` pin Actlize at `323b9dd6`; the kernel findings apply to both. `dev` mainly adds derivation/sweep artifacts and benchmark changes.

## Q1 — what is actually dangerous

### Rank 0: wrong, disqualified, or liable to silently compute nothing

1. **The packed-scale path has no format identity.**

   [`kPackedScaleOn`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:224) is selected by a global macro plus `Scale_TileK == 8`. It does not say “Q4_K”. Later, [`ptr_S` is reinterpreted as bytes and given a hard-coded 16-byte Q4_K shape](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:724).

   That is a latent wrong-number bug as soon as another gs/tile combination also has eight scale groups. Q2_K at gs=16/TK=128 is an obvious collision. This must be rewritten around a typed metadata format, not extended with more macros.

2. **The Q4_K device path violates the new constraint.**

   The code explicitly says it decodes native bytes into “the SAME fp16 smem planes” at [lines 1357–1367](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1357), constructs fp16 `sS`/`sZ` arrays at [1389–1391](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1389), and fills them at [1500–1504](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1500).

   That is a materialised wider scale representation on device. The generic `Superblock` decoder would do the same in an object containing `GroupScale g[kGroups]` at [gguf_scale_decode.hpp:83](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_decode.hpp:83). Both are disqualified. Decode must feed the scale/zero values directly to the MMA fragment that consumes them, without an expanded array or tile.

3. **There is a live unconditional assertion in the coarse scale path.**

   After the valid scale/zero copy, [`if constexpr(false) ... assert(false)`](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1691) always executes. Actlize defaults to Release, so `NDEBUG` hides it. A Debug build aborts whenever coarse scale reload occurs. It is not merely ugly; it makes a normal configuration dependent on build type.

4. **Physical weight layout is inferred again at launch instead of carried with the preprocessed buffer.**

   [`il = n % 256 == 0 && k % 256 == 0`](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:352) decides how the kernel reads B. The buffer has no layout tag. The Q4 harness itself documents that handing an interleaved buffer to the non-interleaved branch produces deterministic garbage at [test_q4k_packed_gemm.cu:50](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:50).

   This also becomes unsafe with K slicing: `filter_and_run` chooses from sliced `k`, while downstream stride construction can use `k_full`. The offline plan, buffer, and launcher need one shared layout ID.

5. **The dense wrapper silently no-ops.**

   [`can_implement`, workspace, and initialization failures simply return](/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh:128). The caller can then consume unchanged/stale output. TRT-LLM throws on these failures. Silent refusal is a product correctness defect.

### Rank 1: extension traps that have already produced OOBs or unbuildable variants

6. **The positional `cute::tuple` scale channel should be replaced, not patched.**

   The mode is inferred from tuple positions at [lines 127–149](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:127). Different stages return different positional contracts at [736–743](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:736) and [1242–1256](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1242).

   The strongest indictment is the dead `sSp` object: it cannot be deleted because doing so would move tuple indices, so it was repointed while deliberately kept dead at [1572–1601](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1572). That is an interface which no compiler can validate semantically.

7. **Two layouts over the same scale buffer are a correctness hazard, not naming ugliness.**

   The write view is `(n, group, stage)`; the read view flattens to `(n, 1, stage*Scale_TileK+group)` at [1561–1568](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1561). The code records that using the wrong one already produced “TSM out of range” at [1500–1502](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1500).

   Two views are legitimate; two separately reconstructed layout types with an informal equivalence are not. There should be one scale-storage accessor that produces both views and statically verifies address equality.

8. **I partly disagree about the current `#if` member/use defect.**

   The specific `ScaleSwizzle` definition used outside its branch has been repaired: the declarations are now outside the branch at [489–498](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:489). So that particular suspicion is historical, not live at this pin.

   The systemic problem remains: macro combinations are not instantiated by the normal build. [`PPU_FORCE_INSTANTIATE`](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:148) exists precisely because ordinary parsing misses dependent template failures, while `main` silently lacks the `dev/fold_derivation` checks at [build.sh:70](/root/marlin_ppu/quactlize/build.sh:70). New macro combinations remain an unbuildable-tree risk.

9. **The build overlay should be rewritten.**

   [`build.sh`](/root/marlin_ppu/quactlize/build.sh:9) copies and flattens sources into the submodule, edits its `examples/CMakeLists.txt`, restores it with `git checkout`, deletes the overlay at [41–47](/root/marlin_ppu/quactlize/build.sh:41), and deletes one shared build directory on every run at [191–193](/root/marlin_ppu/quactlize/build.sh:191). Concurrent builds race; an edit to the submodule example list is overwritten; new extensions can disappear from the whitelist.

   The root [CMakeLists.txt](/root/marlin_ppu/quactlize/CMakeLists.txt:1) does not build any device code, so a clean root configure proves almost nothing. This needs an out-of-tree Actlize target or supported external-example hook.

### Rank 2: ugly or experimental, but not itself a reason for wrong numbers

- **Generated `.cu` per configuration:** the concept is defensible. Device compilers often need TU sharding. What should change is the string-table/config generation and the checked-in `dev/fold_derivation/.moe_units_check` forest. Generate from one typed manifest into the build directory. Do not rewrite the sharding merely because it is generated.
- **Ablation macros and forensic comments:** noisy and single-maintainer in flavour, but harmless if excluded from product builds. Flags such as `PPU_B_DEQUANT_NOP` can deliberately produce nonsense and therefore must never share release configuration.
- **`MixGemmEmit`, `MixGemm2Plane`, and `xplane::place_derived`:** keep these. The central emission map at [fast_numeric_conversion_for_mix_gemm.h:56](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:56), general two-plane converter at [746](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/fast_numeric_conversion_for_mix_gemm.h:746), and byte-exact offline placement at [xplane_offline.hpp:217](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:217) are among the few genuinely reusable boundaries here.

On the bit maps: there should be **two physical maps**—native GGUF and kernel-reordered—and one explicit permutation between them. Today there are more than two authorities: native traits in [gguf_scale_layout.hpp:39](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:39), repeated native extraction in [dump_packed_scale.py:45](/root/marlin_ppu/quactlize/tools/dump_packed_scale.py:45), and the reordered `PackBits` map in [gguf_packed_scale.h:33](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:33). The test constructs the destination with the destination decoder’s own `put_code`, so that round-trip is not an independent proof of the destination map.

The tuple, dual scale views, macro/member incidents, and map drift are symptoms of one cause: **there is no first-class quantized storage/decode contract**. The sweep generator and overlay are a second cause: **there is no first-class build/configuration registry**.

## Q2 — what TRT-LLM gets structurally right

I read NVIDIA’s current source at commit `09b6bea`. One correction: TRT-LLM’s `WeightOnlyQuantOp` is not an on-disk-format taxonomy. It names arithmetic modes—per-column scale, fine-grained scale, and fine-grained scale-plus-zero ([source](https://github.com/NVIDIA/TensorRT-LLM/blob/09b6bea1642aed3b533cbb6b71db586e19d5f300/cpp/tensorrt_llm/cutlass_extensions/include/cutlass_extensions/weight_only_quant_op.h#L27-L43)). It does not itself distinguish GGUF, GPTQ, and AWQ storage.

What it gets right is separation:

- Preprocessing owns physical B layout. `preprocess_weights_for_mixed_gemm` selects the architecture layout and performs row permutation, sub-byte transpose, tile interleave, and register interleave as one same-byte transform ([source](https://github.com/NVIDIA/TensorRT-LLM/blob/09b6bea1642aed3b533cbb6b71db586e19d5f300/cpp/tensorrt_llm/kernels/cutlass_kernels/cutlass_preprocessors.cpp#L570-L629)).
- `QuantOp` owns dequant arithmetic, rather than being inferred from tuple arity.
- The runner owns typed pointers and validates which pointers may be null. Failure is reported, not converted into a silent no-op ([source](https://github.com/NVIDIA/TensorRT-LLM/blob/09b6bea1642aed3b533cbb6b71db586e19d5f300/cpp/tensorrt_llm/kernels/cutlass_kernels/fpA_intB_gemm/fpA_intB_gemm_template.h#L132-L179)).
- Tile/split-K/schedule selection is a separate `CutlassGemmConfig` axis and `getConfigs()` path ([source](https://github.com/NVIDIA/TensorRT-LLM/blob/09b6bea1642aed3b533cbb6b71db586e19d5f300/cpp/tensorrt_llm/kernels/cutlass_kernels/fpA_intB_gemm/fpA_intB_gemm_template.h#L552-L568)). Formats do not become accidental tile conditions.

Where knowledge leaks here:

- Storage semantics: tuple member presence and `NoZero`.
- Metadata format: global macro plus `Scale_TileK`.
- Weight format: element types and plane widths.
- Layout: recalculated from `n`/`k`.
- Group semantics: wrapper switches on 16/32/64/128.
- Offline format decode: Python fixtures and C++ traits.
- Product configuration: CMake strings and generated filenames.

Do not copy TRT-LLM literally: its runner still assumes `ScaleZeroType*` arrays, normally widened fp16, so it does not satisfy this constraint for GGUF or AWQ either. Copy the boundaries and introduce a richer contract:

1. `FormatTraits<GGUF_Q4_K/GPTQ_SYM/AWQ/...>`: native block bytes, planes, group mapping, signedness, scale/min/zero encoding.
2. `PreprocessPlan<Format, KernelLayout>`: a pure permutation with explicit input/output byte counts and a layout ID.
3. `MetadataLoader<Format>`: reads native/reordered metadata and decodes only the values needed by the current MMA fragment into registers.
4. `KernelConfig`: tile, stages, split-K and interleave, independent of format; launcher verifies that the preprocessed layout ID matches it.

The existing document’s proposed universal `(int4, fp16 scale [+zero])` intermediate at [FORMATS_AND_REORDER.md:18–23](/root/marlin_ppu/quactlize/docs/FORMATS_AND_REORDER.md:18) is now invalid and should be deleted, not amended.

## Q3 — byte-neutral support verdict

All listed formats are supportable in principle without increasing stored bytes. Only restricted GPTQ has a qualifying path now.

| Format | Device path now | Offline reorder now | Independent validation | What is missing |
|---|---|---|---|---|
| **GGUF Q4_K** | Int4 and a native 16-byte loader exist, but **non-compliant**: it expands into fp16 `sS/sZ` tiles. Q4-only constants are hard-coded at [1322–1329](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1322). | Weight reorder exists. A byte-neutral 16-byte metadata packing exists only inside [test_q4k_packed_gemm.cu:66](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:66), after Python has already expanded the codes. | Real native CPU golden exists, but the packed row is explicitly intermittent with unknown cause at [run_batch.sh:91](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:91). Not shippably validated. | Production native-to-reordered importer, typed format, and decode-at-consumption with no expanded fp16 tile. |
| **GGUF Q3_K** | Two-plane int2+int1 conversion exists and is real-weight tested. Metadata is supplied as widened fp16 `dl/-4dl` at [test_q3_bconcat_real.cu:71–90](/root/marlin_ppu/quactlize/tests/test_q3_bconcat_real.cu:71), so the full path is non-compliant. | Exact-byte weight-plane reorder exists. Native 14-byte metadata transport—`d` plus 12 code bytes—does not. | Yes for the two-plane/widened-metadata path against a CPU native GGUF golden; no validation of a compliant native metadata channel. | Decode `d*(sc6-32)` on device at point of use and connect it to the two-plane collective without materialising 16 fp16 scales. |
| **GGUF Q5_K** | Generic int4+int1 converter exists; only synthetic mechanics are tested. No native metadata path. | Low/high-plane placement primitives exist. No real Q5_K importer. Its 16-byte metadata uses the same map as Q4_K at [gguf_scale_layout.hpp:58](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:58). | Synthetic only; [test_q65_bconcat_real.cu](/root/marlin_ppu/quactlize/tests/test_q65_bconcat_real.cu:1) is not real despite its name. | Native Q5 parser, exact 16-byte metadata reorder, and on-use affine `d*sc*q-dmin*min` decode attached to int4+int1. |
| **GGUF Q6_K** | Generic int4+int2 and bias-32 symmetric conversion exist; metadata is synthetic fp16. | Weight-plane primitives exist; no native Q6 importer. | Synthetic only. | Preserve exactly 18 metadata bytes per superblock—2-byte `d` plus 16 signed int8 scales—with no padding. Decode `d*int8_scale` at consumption. Aggregate blocks for aligned transfers rather than padding each block. |
| **GGUF Q2_K** | Int2 and affine arithmetic exist, but real test loads expanded fp16 scale/zero at [test_w2a16_real.cu:34–56](/root/marlin_ppu/quactlize/tests/test_w2a16_real.cu:34). Non-compliant overall. | Exact-byte weight reorder and a real Q2 parser/test path exist. No native metadata reorder/channel. | Yes for int2 plus widened metadata against a CPU native golden; none for a compliant channel. | Transport exactly 20 metadata bytes—16 packed 4+4 codes plus `d/dmin`—and decode scale/min on device at use. |
| **GPTQ int4 symmetric** | **Yes for `desc_act=false`/no effective `g_idx`.** Int4 converter plus fp16 scales already match checkpoint storage; no scale widening is required. Constant zero 8 can remain implicit. | Yes, through the existing int4 preprocessing, byte-for-byte. The extractor verifies qzeros are all 8 at [dump_real_weights.py:250–273](/root/marlin_ppu/quactlize/tools/dump_real_weights.py:250). | Yes for the restricted real GPTQ path against a CPU dequant golden. | The tool explicitly rejects `desc_act` at [416–419](/root/marlin_ppu/quactlize/tools/dump_real_weights.py:416). For arbitrary `g_idx`, either consume the existing stored `g_idx` during scale selection, or perform an activation-aware whole-model permutation. Reordering weights alone is insufficient because it changes K’s correspondence with A. |
| **AWQ int4 asymmetric** | No compliant path. Current affine arithmetic could express AWQ, but it expects an fp16 additive-zero array. Widening packed int4 zero points is forbidden. | No AWQ importer/interleave in this tree. | None. | Preserve packed int4 zero points, apply the AWQ-specific exact-byte weight/zero permutation offline, and decode `scale*(q-z4)` on device at consumption. Scales may remain in their original fp16 representation. |

The practical rewrite order is therefore:

1. Introduce the typed format/layout contract.
2. Replace the scale/zero tuple subsystem with a native-metadata loader that produces only per-use register values.
3. Qualify Q3_K first—the existing two-plane weight path and real golden make it the cleanest proof.
4. Port Q2_K, Q4_K/Q5_K, then Q6_K.
5. Keep GPTQ as the control path and add `g_idx`.
6. Add AWQ only after packed zero-point loading is a first-class policy.

Patching more format constants into `gguf_packed_scale.h` or adding tuple members would deepen the structural defect and still fail the binding constraint.
