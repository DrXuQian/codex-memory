# Resume brief: DIAGNOSIS TASK, analysis-first. Work in /root/marlin_ppu/quactlize. There is ANOTHER codex session running in this same tree right now, working on quactlize/include/gguf_vecdot.hpp and tests/gguf_cuda_probe.cu — DO NOT TOUCH THOSE TWO FILES, and do not run the 5090 GEMV benchmarks. Your subject is the PPU packed-scale collective and the benchmark scaffolding around it.

*** HEARTBEAT, mandatory, same file the other session uses — prefix your lines with [DIAG] so they can be told apart ***
    echo "[DIAG $(date +%H:%M:%S)] <what you just did>" >> /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Every meaningful step, and at least every ~5 minutes. Numbers in the lines.

THE QUESTION: why does `packfuse` measure the same as `pack`?

THE DATA. A box run of ./benchmarks/run_batch.sh perf, paired ratios against base, n=10 blocks:
    bdqnop     19.94 us   -10.9%   CI 0.885 .. 0.897
    base       22.38       0.0%
    splitnop   23.80      +6.4%    CI 1.057 .. 1.070
    swz        23.82      +6.4%    CI 1.059 .. 1.070
    packnop    24.35      +8.8%    CI 1.079 .. 1.097
    packfuse   25.17     +12.5%    CI 1.118 .. 1.131
    pack       25.25     +12.8%    CI 1.118 .. 1.139
    packsplit  25.49     +13.9%    CI 1.132 .. 1.146
packfuse and pack are indistinguishable. The whole point of PPU_PACKED_SCALE_FUSED is to replace two 16-bit plane stores with one interleaved 32-bit (scale, zero) store so 32 lanes hit all 32 banks once, removing +73,728 shared-store bank conflicts. An earlier box round reported the conflicts unchanged at 81,920 (+0.00%).

WHAT I HAVE ALREADY ESTABLISHED — do not redo this, start from it:
1. `kFusedScaleZero` (ppu_mma_aiu_multistage_mixed_input.hpp:624) IS properly guarded by `#if defined(PPU_PACKED_SCALE_FUSED) && (PPU_PACKED_SCALE_FUSED != 0)`, so the macro is genuinely consumed. It is not a dead define at the header level.
2. Its other conjuncts are `kPackedScaleOn && (KernelConversionMode == ConvertAndScaleWithZero) && !kScaleSwizzleOk`.
3. `kScaleSwizzleOk` is false unless PPU_SCALE_SWIZZLE is set, and the packfuse variant does not set it — so `!kScaleSwizzleOk` is TRUE and that conjunct is not the blocker.
4. `kPackedScaleOn` requires `Scale_TileK == PackedUnit::kGroups` (== 8 at gs=32). The pinned bench row is `16x128:256 w16x16 s2` at gs=32. VERIFY whether that row's Scale_TileK is 8 — if it is not, neither pack nor packfuse is on the packed path at all and the +12.8% is something else entirely.
5. The header itself, at line 723-731, records this EXACT failure once before: "PPU_PACKED_SCALE_FUSED shipped to the box in a state where the only translation unit that used it could not compile, the define was reported as a WARNING nobody's gate checked, the binary built without it, correctness passed, and acu reported the store conflicts unchanged at 81,920 (+0.00%)." It also asserts that shared bytes, instruction counts and results are identical either way BY DESIGN, and that the only reliable test is to ask the TYPE — `is_fused_scale_zero`, checked by dev/fold_derivation/l100_fused_active.cu.

I am not certain point 5's claim about INSTRUCTION COUNTS is right, and that matters: replacing two 16-bit stores with one 32-bit store should halve the shared-store instruction count even though the bytes are identical. Settle that from the source rather than from the comment — read what the fused store path actually emits versus the two-plane path. If the instruction count really is unchanged, say why; if it should change, then acu's shared-store INSTRUCTION count (not the conflict count) is a valid probe after all and the earlier round's evidence was read wrongly.

ORDER OF WORK:
A. Run dev/fold_derivation/l100_fused_active.cu (or whatever it needs to build locally) and report whether `is_fused_scale_zero` is TRUE for the pinned configuration `16x128:256 w16x16 s2` at gs=32, SK_QUANT=2. This is the single most decisive local fact and it needs no box. If the gate does not cover exactly that configuration, make it cover it — a gate that answers for a different tile answers nothing.
B. Report `is_packed_scale` and `has_zero_channel` for the same configuration, so a false result can be attributed to the right conjunct.
C. Establish whether the define actually reaches the compile line in the packfuse build. build.sh prints "PPU_DEFS verified on <target>'s compile command" and run_batch.sh fails if that line is missing — check that the verification covers PPU_PACKED_SCALE_FUSED specifically and is not satisfied by some other define being present.
D. Check whether the packfuse and pack BINARIES can be distinguished at all. run_batch.sh's do_build prints md5 fingerprints for every variant and has a distinct-binary check. If the two binaries are byte-identical the macro changed no generated code and everything downstream is explained; if they differ, the code changed and the question is what it changed to.
E. Only then, write the exact acu invocation and name the counters that would settle it, given whatever you concluded in the instruction-count question above. The splitk bench has SPLITK_ACU=1 for one cold launch per row, plus SPLITK_ONLY / SPLITK_CFG / SPLITK_S; dev/fold_derivation/acu_capture.sh is the recorded invocation pattern for the MoE bench. I cannot run on the box, so this has to be a command someone can paste.

CONSTRAINT: you have no PPU SDK and no box here, so anything requiring hgcc or ppu001 must be delivered as a command plus the expected output, not run. Local nvcc front-end gates DO work and are the right tool for A and B.

DELIVERABLE: a verdict on why packfuse == pack, with the evidence for it, and — if the cause is that the path is inactive — what makes it active. If the path IS active and the effect is genuinely zero, say that instead, and say what that implies about the +73,728 conflicts (they would then not be coming from where the design assumed).

Do not ask me questions; make the call and state the assumption in the log.

- **Thread ID:** `019fc589-25f4-7a13-b7f3-7e842a5494ed`
- **Started / last event:** 2026-08-03 02:52 UTC → 2026-08-03 03:00 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/03/rollout-2026-08-03T10-52-07-019fc589-25f4-7a13-b7f3-7e842a5494ed.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "8e2288cd1013723a77e1bb784486ef67a98b0df1", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-03_019fc589_DIAGNOSIS-TASK-analysis-first-Work-in-root-marlin_.md](../transcripts/2026-08/2026-08-03_019fc589_DIAGNOSIS-TASK-analysis-first-Work-in-root-marlin_.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

DIAGNOSIS TASK, analysis-first. Work in /root/marlin_ppu/quactlize. There is ANOTHER codex session running in this same tree right now, working on quactlize/include/gguf_vecdot.hpp and tests/gguf_cuda_probe.cu — DO NOT TOUCH THOSE TWO FILES, and do not run the 5090 GEMV benchmarks. Your subject is the PPU packed-scale collective and the benchmark scaffolding around it.

*** HEARTBEAT, mandatory, same file the other session uses — prefix your lines with [DIAG] so they can be told apart ***
    echo "[DIAG $(date +%H:%M:%S)] <what you just did>" >> /tmp/claude-0/-root/a7d83a5d-10d6-445e-827f-6e082752c0a2/scratchpad/codex_gemv_progress.log
Every meaningful step, and at least every ~5 minutes. Numbers in the lines.

THE QUESTION: why does `packfuse` measure the same as `pack`?

THE DATA. A box run of ./benchmarks/run_batch.sh perf, paired ratios against base, n=10 blocks:
    bdqnop     19.94 us   -10.9%   CI 0.885 .. 0.897
    base       22.38       0.0%
    splitnop   23.80      +6.4%    CI 1.057 .. 1.070
    swz        23.82      +6.4%    CI 1.059 .. 1.070
    packnop    24.35      +8.8%    CI 1.079 .. 1.097
    packfuse   25.17     +12.5%    CI 1.118 .. 1.131
    pack       25.25     +12.8%    CI 1.118 .. 1.139
    packsplit  25.49     +13.9%    CI 1.132 .. 1.146
packfuse and pack are indistinguishable. The whole point of PPU_PACKED_SCALE_FUSED is to replace two 16-bit plane stores with one interleaved 32-bit (scale, zero) store so 32 lanes hit all 32 banks once, removing +73,728 shared-store bank conflicts. An earlier box round reported the conflicts unchanged at 81,920 (+0.00%).

WHAT I HAVE ALREADY ESTABLISHED — do not redo this, start from it:
1. `kFusedScaleZero` (ppu_mma_aiu_multistage_mixed_input.hpp:624) IS properly guarded by `#if defined(PPU_PACKED_SCALE_FUSED) && (PPU_PACKED_SCALE_FUSED != 0)`, so the macro is genuinely consumed. It is not a dead define at the header level.
2. Its other conjuncts are `kPackedScaleOn && (KernelConversionMode == ConvertAndScaleWithZero) && !kScaleSwizzleOk`.
3. `kScaleSwizzleOk` is false unless PPU_SCALE_SWIZZLE is set, and the packfuse variant does not set it — so `!kScaleSwizzleOk` is TRUE and that conjunct is not the blocker.
4. `kPackedScaleOn` requires `Scale_TileK == PackedUnit::kGroups` (== 8 at gs=32). The pinned bench row is `16x128:256 w16x16 s2` at gs=32. VERIFY whether that row's Scale_TileK is 8 — if it is not, neither pack nor packfuse is on the packed path at all and the +12.8% is something else entirely.
5. The header itself, at line 723-731, records this EXACT failure once before: "PPU_PACKED_SCALE_FUSED shipped to the box in a state where the only translation unit that used it could not compile, the define was reported as a WARNING nobody's gate checked, the binary built without it, correctness passed, and acu reported the store conflicts unchanged at 81,920 (+0.00%)." It also asserts that shared bytes, instruction counts and results are identical either way BY DESIGN, and that the only reliable test is to ask the TYPE — `is_fused_scale_zero`, checked by dev/fold_derivation/l100_fused_active.cu.

I am not certain point 5's claim about INSTRUCTION COUNTS is right, and that matters: replacing two 16-bit stores with one 32-bit store should halve the shared-store instruction count even though the bytes are identical. Settle that from the source rather than from the comment — read what the fused store path actually emits versus the two-plane path. If the instruction count really is unchanged, say why; if it should change, then acu's shared-store INSTRUCTION count (not the conflict count) is a valid probe after all and the earlier round's evidence was read wrongly.

ORDER OF WORK:
A. Run dev/fold_derivation/l100_fused_active.cu (or whatever it needs to build locally) and report whether `is_fused_scale_zero` is TRUE for the pinned configuration `16x128:256 w16x16 s2` at gs=32, SK_QUANT=2. This is the single most decisive local fact and it needs no box. If the gate does not cover exactly that configuration, make it cover it — a gate that answers for a different tile answers nothing.
B. Report `is_packed_scale` and `has_zero_channel` for the same configuration, so a false result can be attributed to the right conjunct.
C. Establish whether the define actually reaches the compile line in the packfuse build. build.sh prints "PPU_DEFS verified on <target>'s compile command" and run_batch.sh fails if that line is missing — check that the verification covers PPU_PACKED_SCALE_FUSED specifically and is not satisfied by some other define being present.
D. Check whether the packfuse and pack BINARIES can be distinguished at all. run_batch.sh's do_build prints md5 fingerprints for every variant and has a distinct-binary check. If the two binaries are byte-identical the macro changed no generated code and everything downstream is explained; if they differ, the code changed and the question is what it changed to.
E. Only then, write the exact acu invocation and name the counters that would settle it, given whatever you concluded in the instruction-count question above. The splitk bench has SPLITK_ACU=1 for one cold launch per row, plus SPLITK_ONLY / SPLITK_CFG / SPLITK_S; dev/fold_derivation/acu_capture.sh is the recorded invocation pattern for the MoE bench. I cannot run on the box, so this has to be a command someone can paste.

CONSTRAINT: you have no PPU SDK and no box here, so anything requiring hgcc or ppu001 must be delivered as a command plus the expected output, not run. Local nvcc front-end gates DO work and are the right tool for A and B.

DELIVERABLE: a verdict on why packfuse == pack, with the evidence for it, and — if the cause is that the path is inactive — what makes it active. If the path IS active and the effect is genuinely zero, say that instead, and say what that implies about the +73,728 conflicts (they would then not be coming from where the design assumed).

Do not ask me questions; make the call and state the assumption in 
… [truncated 8 chars]

## Last assistant conclusions

### 2026-08-03 03:00 UTC

## Verdict

`packfuse == pack` in the supplied round because the box built a stale `actlize` revision that did not contain the fused implementation. It was not disabled by `Scale_TileK`.

The exact `0.989..1.017` CI was recorded in commit `6c67281`, whose gitlink was `actlize@323b9dd6`. That revision contains zero occurrences of `PPU_PACKED_SCALE_FUSED`. The implementation first appears in `actlize@3b7ebbb9`; outer commit `d2f1504` subsequently bumped the gitlink. The current checkout is later still, at `actlize@6bf872d2`.

Thus the define reached the old compile line, but there was no code in that checkout to consume it. The unchanged `81,920` conflicts follow directly.

## Exact-row gate

`./ci/local_gates.py -k l100` passed for the actual pinned configuration defined in [l100_fused_active.cu](/root/marlin_ppu/quactlize/dev/fold_derivation/l100_fused_active.cu:30):

| Property | Result |
|---|---:|
| `Scale_TileK` | `ceil(256/32) = 8` |
| `is_packed_scale` | `true` |
| `has_zero_channel` | `true` |
| `is_fused_scale_zero` | `true` |

Output:

```text
[l100] fused (scale,zero) ACTIVE on the pinned row:
scale_elems=4096 zero_elems=0 (plain 2048)
word view stride n=1 g=128   half view stride n=2
```

The real dispatcher independently computes `SK=(TK+31)/32` for gs=32 in [moe_grouped_ppu.cuh](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:377), while `SK_QUANT=2` maps to `FinegrainedScaleZero`.

To activate it now requires:

```text
SK_QUANT=2
PPU_PACKED_SCALE=1
PPU_PACKED_SCALE_FUSED=1
Scale_TileK=8
PPU_SCALE_SWIZZLE unset/0
actlize revision containing 3b7ebbb9 or later
```

## Instruction-count contradiction

The header comment claiming instruction counts are identical is wrong.

The actual publication branch in [ppu_mma_aiu_multistage_mixed_input.hpp](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1734) emits:

```cpp
// fused: one uint32_t destination assignment
sSZw(...) = pack_h2(sz.scale, sz.zero);

// unfused Q4_K: two half destination assignments
sS(...) = sz.scale;
sZ(...) = sz.zero;
```

Therefore the source-level shared-store stream halves. For this launch:

```text
4 warps × 8 groups × 9 publications × 128 CTAs = 36,864
```

So `Shared Store / Inst` should fall by approximately `36,864`. The comment at lines 729–730 needs correcting to say that shared bytes, results, and the read side remain identical—not publication-store instruction counts.

A PPU backend could still lower the 32-bit assignment into two 16-bit stores, but that is precisely why ACU’s shared-store instruction count is a valid machine-code probe. Local NVCC cannot answer it because device code generation stops at the existing `cute::product` error.

## Build and binary checks

The current scaffolding checks the fused define specifically:

- [build.sh](/root/marlin_ppu/quactlize/build.sh:369) verifies every complete `-Dname=value` argument on the target’s generated device compile command.
- [run_batch.sh](/root/marlin_ppu/quactlize/benchmarks/run_batch.sh:150) independently requires the exact verification line for all three packfuse defines. Another define cannot satisfy it.
- The distinct-binary check identifies duplicate pairs and blocks the build stamp.

The historical binaries were byte-distinct:

```text
pack      c9acf2eb...
packfuse  2bb36d1b...
```

But that round is a concrete demonstration that differing MD5s are only a one-way check: the old header did not consume the macro, so those differing bytes did not prove that fused device code existed.

## Paste-ready ACU run

First ensure the fused submodule revision is actually present and rebuild:

```bash
cd /root/marlin_ppu/quactlize
git pull --recurse-submodules
git submodule update --init --recursive
git -C third_party/actlize merge-base --is-ancestor 3b7ebbb9 HEAD
FORCE=1 ./benchmarks/run_batch.sh build
```

The ancestry check should exit zero. The packfuse build log must contain all three lines:

```text
PPU_DEFS verified on test_moe_splitk_bench's compile command: -DSK_QUANT=2
PPU_DEFS verified on test_moe_splitk_bench's compile command: -DPPU_PACKED_SCALE=1
PPU_DEFS verified on test_moe_splitk_bench's compile command: -DPPU_PACKED_SCALE_FUSED=1
```

Then capture exactly one cold launch from each binary:

```bash
OUT="${OUT:-$HOME/ab}"

for variant in pack packfuse; do
  env \
    SPLITK_ACU=1 \
    SPLITK_CFG='16x128:256 w16x16 s2' \
    SPLITK_S=1 \
    acu -o "splitk_${variant}.report" --set full -f \
      "$OUT/test_moe_splitk_bench__${variant}" \
      64 8 2048 2048 32 3
done
```

The harness should print:

```text
[acu] ONE COLD launch (not a timing): i4 sz 16x128:256 w16x16 s2  S=1
```

Compare these counters under `Shared Store`, not `Shared Store From Global Load`:

- `Inst`
- `Trans`
- `Bank Conflicts`

Expected decisive outcomes:

- `Inst`: approximately `84,480 → 47,616` means the 32-bit store was emitted.
- `Inst` unchanged means stale/absent code or backend lowering to two half stores.
- With the static bank model, conflicts should be `81,920 → 8,192`.
- If instructions fall by `36,864` but conflicts remain `81,920`, the fused store is real and the assumed bank/event model is wrong.

No repository files were changed.
