# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 059 and 060 and act on them; 060 corrects 059 and is the operative one. This is a live box failure, so it takes priority over anything left from 055–058.

WHAT THE BOX SHOWED, 2026-08-05, dense bench at --g=128:

    ppu_mma_aiu_multistage_mixed_input.hpp:1968  copy_B_and_extra_info
    TileShape = (16, 64, 256)   block [72,2,0] thread [112,0,0]   Assertion `false' failed
    then std::runtime_error: Failed to query occupancy   (context already poisoned)

The site is not a legality problem, it is unfinished code. Inside the COARSE scale branch
(`if constexpr (Scale_TileK <= K_BLOCK_MAX)`), after the scale is copied correctly, it runs
`if constexpr (false) {} else { assert(false); }` — whose else branch always executes. The commented-out
`static_assert(dependent_false<KernelSchedule>, "Conversion mode not handled in A -> RF path.")` above it says
what it was: a not-handled marker demoted to a runtime assert and then reached.

Which configs reach it, derived (Scale_TileK = TileK/gs, K_BLOCK_MAX = max(TileK/64,1)):
  gs=16 and gs=32 give Scale_TileK > K_BLOCK_MAX at every TileK -> FINE, unaffected
  gs=128 gives Scale_TileK <= K_BLOCK_MAX at every TileK -> COARSE -> assert, and at TileK=64
  Scale_TileK is 0, so GroupK is also a division by zero

MY FIRST FILING (059) SAID THIS WAS UNREACHABLE FROM ANY SHIPPING PATH because the GGUF registry has only gs 16 and 32. That was wrong, and the user caught it: GPTQ uses gs=128. It is a named target — Qwen/Qwen3.5-35B-A3B-GPTQ-Int4, bits=4 / gs=128 / sym — and quactlize/real_weight already extracts it. So the COARSE path IS the GPTQ path.

AND THE CAPABILITY ALREADY EXISTS ON ONE SIDE, which is why the real-weight GPTQ harness passed:

    moe_grouped_ppu.cuh:447   dispatches on group_size to a per-gs kernel tag
        gs=128 -> KernelAiuMultistageMixedInputFinegrainedGs128
        gs=64  -> ...Gs64,  gs=32 -> ...Gs32,  gs=16 -> Gs32 with SK=ceil(TK/16)
    test_lowbit_dense_bench.cu:181   ONE hardcoded KernelSchedule, no group_size dispatch at all
        KernelTmaWarpSpecializedCooperativeMixedInput -> generic collective -> COARSE -> assert

That makes this INBOX 058's second casualty. PPU_B_CHUNK was the first and I found it by accident; this one is a supported checkpoint format that cannot run dense at all. The user's framing has now held twice: if the two paths shared one implementation, a per-gs specialisation added to one would be in the other by construction.

WHAT I AM ASKING:

  gs=128 must WORK on the dense path — "reject it in the validity query" is the wrong answer here, because GPTQ needs it to run rather than to be diagnosed. Whether that is the dense bench and the .so selecting the same Finegrained ladder the grouped side uses, or finishing the generic collective's COARSE branch, is your call; you know which is less likely to disturb the FINE path that gs=16/32 depend on.

  Say whether gs=64 works dense — it is in the same ladder and presumably in the same state.

  The `if constexpr (false) {} else { assert(false); }` should go regardless. Even once the path works, a device assert as the not-handled marker is what turned a clear "group size unsupported" into an occupancy-query failure three frames later, naming neither the group size nor the collective.

CONTEXT ON MY SIDE since your 055–058: docs/BACKTEST.md now holds every recorded performance figure with its conditions, swept from memory/ and SWEEP_STATE.md. Its whole section B is gs=128 and is therefore currently unreproducible — that is how this was found. tools/pack_gguf.py now reads ppu_format_config.inc instead of restating TileK and the plane widths (it was on the "still restated" list in your 057 audit, and it is my side of the split). The offline-layout gate was rebuilt: it had been comparing the packer's hardcode against the library's hardcode and passing while both were wrong, and now it checks the registry against the rule its own header states, plus the bench's per-width defaults, plus that the packer reads rather than restates. Local tier is 12/12.

- **Thread ID:** `019fcfc2-932c-7431-8b97-f7504f48a3c0`
- **Started / last event:** 2026-08-05 02:31 UTC → 2026-08-05 03:19 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/05/rollout-2026-08-05T10-31-03-019fcfc2-932c-7431-8b97-f7504f48a3c0.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "45d151948eb8e7d554884812c0ff810f231113f9", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-05_019fcfc2_Repo-root-marlin_ppu-quactlize-branch-develop-git.md](../transcripts/2026-08/2026-08-05_019fcfc2_Repo-root-marlin_ppu-quactlize-branch-develop-git.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 059 and 060 and act on them; 060 corrects 059 and is the operative one. This is a live box failure, so it takes priority over anything left from 055–058.

WHAT THE BOX SHOWED, 2026-08-05, dense bench at --g=128:

    ppu_mma_aiu_multistage_mixed_input.hpp:1968  copy_B_and_extra_info
    TileShape = (16, 64, 256)   block [72,2,0] thread [112,0,0]   Assertion `false' failed
    then std::runtime_error: Failed to query occupancy   (context already poisoned)

The site is not a legality problem, it is unfinished code. Inside the COARSE scale branch
(`if constexpr (Scale_TileK <= K_BLOCK_MAX)`), after the scale is copied correctly, it runs
`if constexpr (false) {} else { assert(false); }` — whose else branch always executes. The commented-out
`static_assert(dependent_false<KernelSchedule>, "Conversion mode not handled in A -> RF path.")` above it says
what it was: a not-handled marker demoted to a runtime assert and then reached.

Which configs reach it, derived (Scale_TileK = TileK/gs, K_BLOCK_MAX = max(TileK/64,1)):
  gs=16 and gs=32 give Scale_TileK > K_BLOCK_MAX at every TileK -> FINE, unaffected
  gs=128 gives Scale_TileK <= K_BLOCK_MAX at every TileK -> COARSE -> assert, and at TileK=64
  Scale_TileK is 0, so GroupK is also a division by zero

MY FIRST FILING (059) SAID THIS WAS UNREACHABLE FROM ANY SHIPPING PATH because the GGUF registry has only gs 16 and 32. That was wrong, and the user caught it: GPTQ uses gs=128. It is a named target — Qwen/Qwen3.5-35B-A3B-GPTQ-Int4, bits=4 / gs=128 / sym — and quactlize/real_weight already extracts it. So the COARSE path IS the GPTQ path.

AND THE CAPABILITY ALREADY EXISTS ON ONE SIDE, which is why the real-weight GPTQ harness passed:

    moe_grouped_ppu.cuh:447   dispatches on group_size to a per-gs kernel tag
        gs=128 -> KernelAiuMultistageMixedInputFinegrainedGs128
        gs=64  -> ...Gs64,  gs=32 -> ...Gs32,  gs=16 -> Gs32 with SK=ceil(TK/16)
    test_lowbit_dense_bench.cu:181   ONE hardcoded KernelSchedule, no group_size dispatch at all
        KernelTmaWarpSpecializedCooperativeMixedInput -> generic collective -> COARSE -> assert

That makes this INBOX 058's second casualty. PPU_B_CHUNK was the first and I found it by accident; this one is a supported checkpoint format that cannot run dense at all. The user's framing has now held twice: if the two paths shared one implementation, a per-gs specialisation added to one would be in the other by construction.

WHAT I AM ASKING:

  gs=128 must WORK on the dense path — "reject it in the validity query" is the wrong answer here, because GPTQ needs it to run rather than to be diagnosed. Whether that is the dense bench and the .so selecting the same Finegrained ladder the grouped side uses, or finishing the generic collective's COARSE branch, is your call; you know which is less likely to disturb the FINE path that gs=16/32 depend on.

  Say whether gs=64 works dense — it is in the same ladder and presumably in the same state.

  The `if constexpr (false) {} else { assert(false); }` should go regardless. Even once the path works, a device assert as the not-handled marker is what turned a clear "group size unsupported" into an occupancy-query failure three frames later, naming neither the group size nor the collective.

CONTEXT ON MY SIDE since your 055–058: docs/BACKTEST.md now holds every recorded performance figure with its conditions, swept from memory/ and SWEEP_STATE.md. Its whole section B is gs=128 and is therefore currently unreproducible — that is how this was found. tools/pack_gguf.py now reads ppu_format_config.inc instead of restating TileK and the plane widths (it was on the "still restated" list in your 057 audit, and it is my side of the split). The offline-layout gate was rebuilt: it had been comparing the packer's hardcode against the library's hardcode and passing while both were wrong, and now it checks the registry against the rule its own header states, plus the bench's per-width defaults, plus that the packer reads rather than restates. Local tier is 12/12.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×6
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu` ×6
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp` ×3
- `/tmp/l63_coarse_predicate.cu` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_backend.cu` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_group_schedule.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/moe_gemm_ppu.cuh` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/DENSE_GROUPED_PARITY_061.md` ×1
- `/root/marlin_ppu/quactlize/.coord/BOX.md` ×1

## Last assistant conclusions

### 2026-08-05 03:19 UTC

Implemented and committed. Dense now supports gs=16/32/64/128 through the shared schedule selector, and the generic COARSE scale/zero path is complete.

Actual instantiated predicate:

```text
Scale_TileK <= size<2>(smem_thr_copy_B.retile_D(tCrB_load))
```

| Domain | copy-view K | gs16 | gs32 | gs64 | gs128 |
|---|---:|---|---|---|---|
| Dense/MoE, TileK=64 | 1 | FINE 4 | FINE 2 | COARSE 1 | COARSE 1 |
| MoE, TileK=128 | 2 | FINE 8 | FINE 4 | COARSE 2 | COARSE 1 |

The old dense bench omitted `ScaleTileShape`, defaulting it to 1. Therefore the observed gs32 failure was actually `1 <= 1`, not `2 <= 2`.

Yes, gs64 now works structurally on dense: it selects the gs64 schedule and exercises the completed COARSE branch. gs128 does the same. Ceil division prevents a zero `Scale_TileK`.

Changes:

- `a7a8ea91` in actlize: completed COARSE metadata copying and replaced ordinary-collective device asserts with compile-time diagnostics.
- `1d2a621`: shared gs selector used by dense, grouped, benchmark and `.so` launchers.
- `85976ac`: committed the requested pre-extraction [dense/grouped parity map](/root/marlin_ppu/quactlize/dev/fold_derivation/DENSE_GROUPED_PARITY_061.md).
- `b4cb807`: queued exact gs32/64/128 device validation in [.coord/BOX.md](/root/marlin_ppu/quactlize/.coord/BOX.md).

Focused CUDA syntax checks, all four schedule variants, the 227-row dense dispatch, and the focused local gate pass. Hardware execution remains pending on ppu001. The full local gate was 63/71, with unrelated pre-existing tactic/linker and pytest-environment failures.

`develop` is clean and three commits ahead of `origin/develop`; nothing was pushed. Extraction intentionally stops at the parity-map review checkpoint required by INBOX 061.
