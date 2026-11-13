# Repo /root/marlin_ppu/quactlize. FULL LOCAL ACCESS, and /root/llama.cpp is readable. DO NOT EDIT ANY FILE.

This is a follow-up to your Task B answer. I am pushing back on part of my own summary of it, and I want you to
push back on me.

THE CORRECTION. I told my user "we don't really support the native scale, so the three bands need designing from
scratch." That was wrong and they caught it. The facts:

  * The Q4_K native scale decode IS implemented: cutlass/gguf_packed_scale.h (group_pair_of_words) plus
    packed_decode_stage() in ppu_mma_aiu_multistage_mixed_input.hpp.
  * It is NUMERICALLY VALIDATED on real Q4_K bytes from a checkpoint -- rowA/rowB/rowC all MATCH against a native
    CPU golden (tests/test_q4k_packed_gemm.cu, fixture tests/data/q4k_packed.bin).
  * It sits behind `#if defined(PPU_PACKED_SCALE) && (PPU_PACKED_SCALE != 0)`, off by default. I read that as
    "not supported". My user reads it as staging an experiment before it ships. I now think they are right.
  * It covers Q4_K only: kPackedScaleBias=0, kPackedHasMin=true, kPackedZMul=8 are hardcoded.
  * The open problem is PERFORMANCE: the native path measured ~12.9% slower than fp16 scale planes at the decode
    band, cause unknown.

THE QUESTION I WANT ARGUED, not summarised:

1. Given the above, is "redesign the native scale path" ever the right call, or is the correct work exactly two
   things -- (a) find the 12.9%, (b) parameterise those three constants for Q2/Q3/Q5/Q6? Argue for whichever you
   believe. If you think there IS a structural reason the current shape cannot reach parity in the mid band, say
   what it is and what measurement would settle it.

2. You listed concrete structural candidates for the 12.9%: an extra raw-scale shared staging round trip (48 bytes
   vs 32 per unit per stage), and decode+stores sitting on the cp_async_wait-to-barrier critical path. RANK them,
   and for each say the CHEAPEST EXPERIMENT that would confirm or kill it. I have a working ablation harness
   (benchmarks/run_batch.sh, variants base/pack/packnop/packsplit/splitnop) and acu counters on the box. Design the
   experiments against what that harness can already do.

3. Is there any evidence in the repo that the 12.9% is NOT a real effect? Same-config run-to-run spread is
   documented at ~13%. Read benchmarks/run_batch.sh and the recorded numbers and tell me whether the measurement
   protocol actually separates a 12.9% effect from that noise. If it does not, say so plainly -- that would make
   "find the 12.9%" the wrong first step.

Be specific, cite file:line. If my correction of my own correction is still wrong, say that.

- **Thread ID:** `019fbda2-f6c0-7420-985c-02e0216c823f`
- **Started / last event:** 2026-08-01 14:03 UTC → 2026-08-01 14:14 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T22-03-21-019fbda2-f6c0-7420-985c-02e0216c823f.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "f7e9a92ad87d86fd7d886466eec22c54c41833cf", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-01 14:03 UTC

Repo /root/marlin_ppu/quactlize. FULL LOCAL ACCESS, and /root/llama.cpp is readable. DO NOT EDIT ANY FILE.

This is a follow-up to your Task B answer. I am pushing back on part of my own summary of it, and I want you to
push back on me.

THE CORRECTION. I told my user "we don't really support the native scale, so the three bands need designing from
scratch." That was wrong and they caught it. The facts:

  * The Q4_K native scale decode IS implemented: cutlass/gguf_packed_scale.h (group_pair_of_words) plus
    packed_decode_stage() in ppu_mma_aiu_multistage_mixed_input.hpp.
  * It is NUMERICALLY VALIDATED on real Q4_K bytes from a checkpoint -- rowA/rowB/rowC all MATCH against a native
    CPU golden (tests/test_q4k_packed_gemm.cu, fixture tests/data/q4k_packed.bin).
  * It sits behind `#if defined(PPU_PACKED_SCALE) && (PPU_PACKED_SCALE != 0)`, off by default. I read that as
    "not supported". My user reads it as staging an experiment before it ships. I now think they are right.
  * It covers Q4_K only: kPackedScaleBias=0, kPackedHasMin=true, kPackedZMul=8 are hardcoded.
  * The open problem is PERFORMANCE: the native path measured ~12.9% slower than fp16 scale planes at the decode
    band, cause unknown.

THE QUESTION I WANT ARGUED, not summarised:

1. Given the above, is "redesign the native scale path" ever the right call, or is the correct work exactly two
   things -- (a) find the 12.9%, (b) parameterise those three constants for Q2/Q3/Q5/Q6? Argue for whichever you
   believe. If you think there IS a structural reason the current shape cannot reach parity in the mid band, say
   what it is and what measurement would settle it.

2. You listed concrete structural candidates for the 12.9%: an extra raw-scale shared staging round trip (48 bytes
   vs 32 per unit per stage), and decode+stores sitting on the cp_async_wait-to-barrier critical path. RANK them,
   and for each say the CHEAPEST EXPERIMENT that would confirm or kill it. I have a working ablation harness
   (benchmarks/run_batch.sh, variants base/pack/packnop/packsplit/splitnop) and acu counters on the box. Design the
   experiments against what that harness can already do.

3. Is there any evidence in the repo that the 12.9% is NOT a real effect? Same-config run-to-run spread is
   documented at ~13%. Read benchmarks/run_batch.sh and the recorded numbers and tell me whether the measurement
   protocol actually separates a 12.9% effect from that noise. If it does not, say so plainly -- that would make
   "find the 12.9%" the wrong first step.

Be specific, cite file:line. If my correction of my own correction is still wrong, say that.

## Assistant · 2026-08-01 14:03 UTC

I’ll audit the implementation, test evidence, harness, and recorded benchmark data directly. I’ll treat the 12.9% as a hypothesis to validate statistically before assuming there’s a code-path defect.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"pwd && rg --files -g 'AGENTS.md' -g 'cutlass/gguf_packed_scale.h' -g 'ppu_mma_aiu_multistage_mixed_input.hpp' -g 'tests/test_q4k_packed_gemm.cu' -g 'benchmarks/run_batch.sh' -g 'benchmarks/**' -g ' …`
- `exec: const r = await tools.exec_command({"cmd":"rg --files | rg '(^|/)gguf_packed_scale\\.h$|ppu_mma_aiu_multistage_mixed_input\\.hpp$|run_batch|bench.*(txt|log|csv|md|json)|result|Task|task' | sed -n '1,260p'\nrg -n \"12\\.9|13%|PACKED_SCALE|pa …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba benchmarks/run_batch.sh | sed -n '1,260p'\nnl -ba docs/CHECKPOINT.md | sed -n '35,125p'\nnl -ba dev/fold_derivation/HANDOFF_packed_scale.md | sed -n '1,90p;100,180p;215,245p'\nnl -ba dev/fol …`

</details>

## Assistant · 2026-08-01 14:04 UTC

The repository already contains a material contradiction to the premise: a later same-batch measurement found `pack − base = +2.4%`, while the earlier pinned result was `+12.9%`; the recorded write-up explicitly says the native-format tax is undetermined. I’m now checking whether the batch structure itself provides pairing/repetition strong enough to rescue either estimate—it currently appears not to.

<details><summary>14 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"nl -ba dev/fold_derivation/HANDOFF_packed_scale.md | sed -n '15,82p;105,138p;225,234p'\nnl -ba dev/fold_derivation/PLAN_task20_scale.md | sed -n '700,805p;830,862p;1128,1202p'\nnl -ba docs/README.m …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '1,275p'\nnl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '170,270 …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '180,255p'\nnl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multist …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '245,360p'\nnl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1125, …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '920,1090p'\nnl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multis …`
- `exec: const r = await tools.exec_command({"cmd":"find . -maxdepth 5 -type f \\( -iname '*.report' -o -iname '*.csv' -o -iname '*.log' -o -iname '*acu*' -o -iname '*batch*' \\) -print | sed -n '1,260p'\nrg -n \"38,588|34,191|Shared Store From Glob …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba docs/CHECKPOINT.md | sed -n '98,117p'\nnl -ba benchmarks/test_moe_splitk_bench.cu | sed -n '1,135p'\nnl -ba benchmarks/moe_splitk_bench_common.hpp | sed -n '1,225p'\nnl -ba benchmarks/lowbit …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '118,153p'\nrg -n \"inline double time_it|double time_it\" benchmarks/lowbit_moe_bench.hpp\nnl -ba benchmarks/moe_splitk_bench_common.hpp | sed -n '1 …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"typedef struct.*block_q[23456]_K|block_q2_K|block_q3_K|block_q4_K|block_q5_K|block_q6_K\" ggml/src ggml/include | sed -n '1,260p'\nrg -n \"load_tiles_q[23456]_K|get_scale_min_k4|K_SCALE_SIZ …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba ggml/src/ggml-common.h | sed -n '270,365p'\nnl -ba ggml/src/ggml-quants.c | sed -n '895,935p;1235,1275p;1460,1490p;1660,1694p;1870,1908p'\nnl -ba ggml/src/ggml-cuda/mmq.cuh | sed -n '1628,16 …`
- `exec: const r = await tools.exec_command({"cmd":"rg --files | rg 'gguf_scale_(layout|decode)\\.hpp$|q[2356].*real|bconcat' | sed -n '1,240p'\nnl -ba gguf_scale_layout.hpp | sed -n '1,280p' 2>/dev/null || true\nnl -ba quactlize/csrc/gguf_scale_lay …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/include/gguf_scale_layout.hpp | sed -n '1,175p'\nnl -ba quactlize/include/gguf_scale_decode.hpp | sed -n '1,155p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"PPU_PACKED_SCALE|gguf_packed|kPackedScale\" third_party/actlize/include quactlize/include tests benchmarks --glob '!**/build/**' | sed -n '1,360p'\nrg -n \"kSymBias2Plane|ScaleBias|Q[2356]_ …`
- `exec: const r = await tools.exec_command({"cmd":"git status --short\nstat -c '%y %s %n' benchmarks/run_batch.sh\nnl -ba benchmarks/run_batch.sh | sed -n '1,65p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":120 …`

</details>

## Assistant · 2026-08-01 14:06 UTC

One important wrinkle: `benchmarks/run_batch.sh` is currently modified in the working tree. Its present version has just added `REPS=3` and per-variant repetition, while the recorded 12.9% and 2.4% results came from the old one-sample protocol. I will evaluate both: the historical evidence under the old protocol, and whether the new uncommitted protocol is actually sufficient. I am not touching either version.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"git diff -- benchmarks/run_batch.sh\nnl -ba benchmarks/run_batch.sh | sed -n '180,275p'\ngit -C third_party/actlize status --short 2>/dev/null | sed -n '1,120p'\ngit -C third_party/actlize diff --s …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"splitnop|difference of differences|diff.*diff|REPS|interleav\" dev/fold_derivation docs README.md benchmarks/run_batch.sh | sed -n '1,360p'\ngit log --oneline --all -- benchmarks/run_batch. …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp | sed -n '285,315p;395,438p'\nnl -ba tests/test_q65_bconcat_real.cu | sed -n '100,125p;175,194p'\nnl -b …`

</details>

## Assistant · 2026-08-01 14:09 UTC

There is stronger evidence against treating `12.9%` as a real effect than mere variance: the benchmark source says the historical pack-vs-base figures timed different scale/zero values, and the later corrected same-batch run produced only `+2.4%`. I’m tracing the commit ordering now so I can distinguish “invalid workload comparison” from “noisy but like-for-like comparison.”

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"git show -s --format='%h %ci %s' 80dfeec f55c205 745ee5e\ngit show --stat --oneline 80dfeec\ngit show 80dfeec -- benchmarks/test_moe_splitk_bench.cu | sed -n '1,240p'\ngit log --format='%h %ci %s'  …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba ci/local_gates.py | sed -n '50,68p'\nnl -ba benchmarks/run_batch.sh | sed -n '145,177p;193,234p'\nnl -ba docs/CHECKPOINT.md | sed -n '40,82p;103,116p'\nnl -ba benchmarks/test_moe_splitk_benc …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba dev/fold_derivation/PLAN_task20_scale.md | sed -n '1094,1139p'\nnl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '224,248p;566,583p; …`

</details>

## Assistant · 2026-08-01 14:14 UTC

Your first correction is substantially right: this is an implemented, hardware-exercised experimental path, not “unsupported.” But your correction-of-the-correction is still wrong in two important ways:

1. There is no validly established 12.9% effect to “find.”
2. Extending to Q2/Q3/Q5/Q6 requires more than parameterizing three arithmetic constants.

## 1. Redesign or parameterize?

Do not redesign Q4_K now. First establish whether a performance tax exists at all.

The current architectural shape is defensible: copy one native-code unit per column, decode each `(column, group)` once, publish fp16 scale/zero in shared memory, and let all consumers reuse it. That is much better than the already-tried per-lane decoder, which multiplied decode work.

There is, however, a genuine structural handicap that could eventually justify redesign:

- Baseline cp.async writes the two final fp16 planes directly.
- Packed mode cp.async’s a raw 16-byte unit, reads it back from shared memory, decodes it, and explicitly stores the two fp16 planes.
- The source itself describes the shared footprint as going from two tiles to three ([ppu_mma...hpp:231](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:231)).
- That decode and publication are unambiguously between `cp_async_wait` and `__syncthreads`, both during prefetch and steady state ([ppu_mma...hpp:983](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:983), [ppu_mma...hpp:1017](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1017)).

That does not prove it costs wall time; extra work can be hidden. The decisive measurement is a faithful `packnop`:

- If `packnop − base` remains positive with a paired confidence interval excluding zero, while ACU confirms `packnop` retains the same raw shared loads and decoded-plane stores as `pack`, then optimizing decode arithmetic or format constants cannot reach parity. The publication shape itself costs, and redesign becomes justified.
- If `packnop ≈ base`, the current shape can hide its transport/publication and redesign is not justified.

There is a caveat: the current NOP consumes only `u[0]`, and the code warns that `u[1..3]` may be eliminated ([ppu_mma...hpp:1474](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1474)). Therefore a `packnop` timing without corresponding ACU instruction/load counts is not a valid structural ablation.

### Three constants are not enough

Those constants cover only Q4_K arithmetic ([ppu_mma...hpp:1323](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1323)). The collective also hardcodes:

- 16 bytes per unit and exactly one 128-bit cp.async ([ppu_mma...hpp:212](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:212), [ppu_mma...hpp:240](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:240)).
- Eight groups per unit through `Scale_TileK == 8` ([ppu_mma...hpp:224](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:224)).
- Four 32-bit words and `kGrp = Scale_TileK` ([ppu_mma...hpp:1382](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1382)).
- Six-bit extraction ([gguf_packed_scale.h:62](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:62)).
- A paired fast path that requires two six-bit fields, a min channel, and zero scale bias ([gguf_packed_scale.h:232](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:232), [gguf_packed_scale.h:252](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:252)).

The repository already describes the actual format differences:

- Q4/Q5: eight groups, 12 code bytes, scale+min.
- Q3: sixteen groups, 12 code bytes, scale-only, bias 32.
- Q2: sixteen groups, 16 code bytes, scale+min, four-bit fields.
- Q6: sixteen groups, 16 code bytes, scale-only, signed eight-bit scales.

See [gguf_scale_layout.hpp:39](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:39), [gguf_scale_layout.hpp:61](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:61), [gguf_scale_layout.hpp:82](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:82), and [gguf_scale_layout.hpp:97](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:97).

Q5 can reuse Q4’s scale-code layout, but Q3/Q5/Q6 execute through the separate two-plane collective ([ppu_mma_aiu_mixed_input_2plane.hpp:294](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp:294)). There is currently no packed-scale plumbing there.

So the right extension is a trait-driven generalization of the existing staging skeleton—unit layout, unit bytes, groups, extraction, header fields, decoded plane count, converter bias—not merely three constants. That is still not “design from scratch”; much of the format trait/decode work already exists in [gguf_scale_decode.hpp:78](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_decode.hpp:78).

One further precision point: the Q4 path consumes native scale codes, but not the original 12-byte on-disk GGUF packing. It uses a custom reordered 16-byte unit because the GGUF packing is not half-separable ([gguf_packed_scale.h:9](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:9)). The test constructs that unit from fixture fields using `put_code` ([test_q4k_packed_gemm.cu:66](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:66)). “Native codes, hardware-oriented repacking” is the exact description.

Also, only rowC exercises packed decode; rowA and rowB are controls on the fp16 path ([test_q4k_packed_gemm.cu:242](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:242), [test_q4k_packed_gemm.cu:256](/root/marlin_ppu/quactlize/tests/test_q4k_packed_gemm.cu:256)). The validation is real, but “all three rows validate the packed decoder” would be wrong.

## 2. Candidate ranking and cheapest experiments

Before both candidates, rank “measurement artifact” as candidate zero.

Conditional on proving a real tax:

### 1. Raw staging plus explicit publication stores

This is the leading structural candidate.

The ACU evidence confirms actual additional machinery:

- Raw packed read: `+4,608` shared-load instructions, clean but eight transactions each.
- Decoded-plane stores: `+73,728` store conflicts, explained exactly by adjacent 16-bit stores.

See [PLAN_task20_scale.md:1110](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1110).

Cheapest experiment:

1. Run repeated, interleaved `base`, `packnop`, and `pack` blocks on the pinned row.
2. Capture ACU once for each—not for timing—and verify:

   - `packnop` retains `pack`’s raw cp.async traffic.
   - Its raw shared-load and `tsm.st` counts match `pack`.
   - Only decoder ALU disappears.

3. Read:

   - `packnop − base`: transport, shared round trip, stores, and publication slot.
   - `pack − packnop`: decode arithmetic.

Confirm it if `packnop − base` is reproducibly positive and `pack − packnop` is approximately zero. Kill it if `packnop ≈ base` with faithful counter equivalence. If the counters differ, the NOP is not faithful and the experiment is inconclusive.

### 2. Wait-to-barrier critical path

The placement is structurally real, but less supported as the cause. Four warps currently decode eight groups while four wait; `packsplit` makes all eight decode four groups but adds another 16-byte raw read per column ([ppu_mma...hpp:1409](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1409)).

The cheapest valid experiment is already encoded in the four variants:

\[
\Delta_{\text{placement}}
= (\text{packsplit}-\text{pack})
- (\text{splitnop}-\text{packnop})
\]

- A reproducibly negative delta means splitting shortened the decode critical path after subtracting the duplicated-read/setup cost.
- A narrow result around zero kills the placement hypothesis.
- A positive result means splitting harms scheduling even after the overhead subtraction.

Use ACU to verify that `packsplit − pack` and `splitnop − packnop` contain the same duplicated raw-load/setup counters. Otherwise compiler elimination invalidates the subtraction.

The recorded claim that “placement is dead” used only `packsplit − pack` ([PLAN_task20_scale.md:1177](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1177)). That does not distinguish “no placement benefit” from “benefit smaller than duplicated-read cost.” `splitnop` was added precisely to remove that confound, and no recorded four-way result exists.

## 3. Is 12.9% real?

Plainly: no repository evidence establishes a real 12.9% penalty.

It is worse than “12.9% is within 13% noise”:

- The benchmark now explicitly states that every quoted `pack`-versus-`base` figure compared different scale/zero arithmetic ([test_moe_splitk_bench.cu:89](/root/marlin_ppu/quactlize/benchmarks/test_moe_splitk_bench.cu:89)). Commit `80dfeec` corrected that after the `+12.9%` and `+2.4%` numbers were recorded.
- The two historical results disagree: `+12.9%` versus `+2.4%`, while the corresponding base measurements differ by 17% ([CHECKPOINT.md:78](/root/marlin_ppu/quactlize/docs/CHECKPOINT.md:78)).
- The repository itself concludes that the tax is undetermined and requires repeated interleaved runs ([PLAN_task20_scale.md:1191](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1191)).
- There are no recorded post-`80dfeec`, like-for-like performance numbers.

The historical protocol did not separate a 12.9% effect. Each process timing averages 20 launches, but it still produced one process-level sample per variant, with no paired repetition or error estimate ([lowbit_moe_bench.hpp:136](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:136)).

The current uncommitted `run_batch.sh` is better, but still insufficient:

- It performs all repetitions of one variant before moving to the next, so it is not interleaved ([run_batch.sh:199](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:199)).
- It reports the minimum and max–min range from only three samples ([run_batch.sh:202](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:202)).
- Comparing minima is unpaired and tail-sensitive; a three-point range is not an error bar.
- It discards the individual observations, preventing a paired confidence interval.

Use at least 10–20 randomized or ABBA-style blocks—`base, pack, pack, base`—and retain every observation. Analyze per-block `pack/base` ratios, preferably log ratios, and report a median/mean paired effect with a bootstrap confidence interval. For the four-way placement test, rotate or reverse the variant order per block.

So the correct first step is not “find the 12.9%.” It is “measure whether any native-path penalty exists under the corrected like-for-like workload.” Only then rank causes or authorize a redesign.

No files were edited.
