# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 056 and do it. This supersedes nothing in 055; if you are mid-055, finish it first and say so.

The user asked why TileK is a fixed value and said it is not 256. Chasing that found something worse than an inconsistency: TileK is decided in FOUR independent places and the shipping library runs a value NO measurement supports, while the offline packer packs for that same unmeasured value — so those two agree with each other and disagree with everything else. My new local gate passed for exactly that reason: it compared the two copies that were wrong together.

  bench (test_lowbit_dense_bench.cu:105-120)   int1 -> 256, int2 -> 128, int4 -> 64
        and its comments give the derivation: the AIU 32-byte delivery floor is TK*bits/8 % 32 == 0, so those
        are the MINIMUM legal values per width, not preferences. Every recorded winner comes from here — the
        grouped winner "i4 64x128:64 w64x16 s6" has TileK 64 in it.
  tools/pack_gguf.py:_tile_k(qtype)            Q6_K -> 128, everything else -> 256
  ppu_dense_backend.cu dense dispatch          explicit 256 (Q6_K 128)
  ppu_dense_backend.cu grouped dispatch        template <..., int TileK = 256> and NO call site passes one
  emit_tactic_configs <bits> <tile_k>          an argument; our 227-row table is (bits=4, tk=64)

So the sweep picks winners at TileK 64, the library runs 256, and a tactic name carries no TileK to notice with.

Three asks, in order:

① ONE SOURCE for TileK per format, read by the library, the packer and the bench. Four copies is why this went unnoticed. Where it lives is yours — ppu_tactic_space.hpp already holds the delivery arithmetic and fold_for's floor is the same 32-byte rule, so the minimum-legal TileK per width is derivable rather than tabulated.

② THE CONFIG RECORD MUST CARRY ITS TileK. quactlize_ppu_config_v1 has tile_m/tile_n/warp_m/warp_n/stages and no tile_k, so a tactic chosen from a TileK-64 sweep can be handed to a TileK-256 library and both sides think they agree. It also lets the tuner ask the library which offline layout it needs, which is the only way the manifest and the runtime can be checked against each other at all.

③ GROUPED MUST STOP USING A TEMPLATE DEFAULT. Pass it explicitly like dense does. A default no call site overrides is not a decision.

IMPORTANT — I do NOT know that 256 is wrong for the shipping path. It is legal for every width, and a larger TileK may well be right for the fully-quantized entry, which is a different kernel from the bench's. What I know is that nothing measured it and nothing recorded the choice. If you have evidence that 256 is deliberate, say so and I will record it as a decision rather than change it. That is a better outcome than changing it on my say-so.

This also settles a design point for the whole tactic mechanism, so it is worth stating plainly: TileK is the ONE config axis that changes the offline layout (prepare_dense_for_tile takes tile_k; formats.py derives fold from (bits, tile_k)). The user's constraint is that a search must never move the bytes on disk, so TileK cannot be selected per M like the other axes — it is a per-format, possibly per-tensor, OFFLINE decision made once by measurement and recorded, while (TileM, TileN, WarpM, WarpN, stages) vary with M inside it. Anything you build for ② should make that split explicit rather than implicit.

Same process requests: commit per item; inbox-consumed as soon as read; blocked-on in STATUS.md and keep going on the rest.

- **Thread ID:** `019fcf84-54b0-78b3-8577-1405b558253d`
- **Started / last event:** 2026-08-05 01:23 UTC → 2026-08-05 01:25 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/05/rollout-2026-08-05T09-23-03-019fcf84-54b0-78b3-8577-1405b558253d.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "ae8dbe377a66e8c45cbc21282736fef72f450d1e", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-05_019fcf84_Repo-root-marlin_ppu-quactlize-branch-develop-git.md](../transcripts/2026-08/2026-08-05_019fcf84_Repo-root-marlin_ppu-quactlize-branch-develop-git.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 056 and do it. This supersedes nothing in 055; if you are mid-055, finish it first and say so.

The user asked why TileK is a fixed value and said it is not 256. Chasing that found something worse than an inconsistency: TileK is decided in FOUR independent places and the shipping library runs a value NO measurement supports, while the offline packer packs for that same unmeasured value — so those two agree with each other and disagree with everything else. My new local gate passed for exactly that reason: it compared the two copies that were wrong together.

  bench (test_lowbit_dense_bench.cu:105-120)   int1 -> 256, int2 -> 128, int4 -> 64
        and its comments give the derivation: the AIU 32-byte delivery floor is TK*bits/8 % 32 == 0, so those
        are the MINIMUM legal values per width, not preferences. Every recorded winner comes from here — the
        grouped winner "i4 64x128:64 w64x16 s6" has TileK 64 in it.
  tools/pack_gguf.py:_tile_k(qtype)            Q6_K -> 128, everything else -> 256
  ppu_dense_backend.cu dense dispatch          explicit 256 (Q6_K 128)
  ppu_dense_backend.cu grouped dispatch        template <..., int TileK = 256> and NO call site passes one
  emit_tactic_configs <bits> <tile_k>          an argument; our 227-row table is (bits=4, tk=64)

So the sweep picks winners at TileK 64, the library runs 256, and a tactic name carries no TileK to notice with.

Three asks, in order:

① ONE SOURCE for TileK per format, read by the library, the packer and the bench. Four copies is why this went unnoticed. Where it lives is yours — ppu_tactic_space.hpp already holds the delivery arithmetic and fold_for's floor is the same 32-byte rule, so the minimum-legal TileK per width is derivable rather than tabulated.

② THE CONFIG RECORD MUST CARRY ITS TileK. quactlize_ppu_config_v1 has tile_m/tile_n/warp_m/warp_n/stages and no tile_k, so a tactic chosen from a TileK-64 sweep can be handed to a TileK-256 library and both sides think they agree. It also lets the tuner ask the library which offline layout it needs, which is the only way the manifest and the runtime can be checked against each other at all.

③ GROUPED MUST STOP USING A TEMPLATE DEFAULT. Pass it explicitly like dense does. A default no call site overrides is not a decision.

IMPORTANT — I do NOT know that 256 is wrong for the shipping path. It is legal for every width, and a larger TileK may well be right for the fully-quantized entry, which is a different kernel from the bench's. What I know is that nothing measured it and nothing recorded the choice. If you have evidence that 256 is deliberate, say so and I will record it as a decision rather than change it. That is a better outcome than changing it on my say-so.

This also settles a design point for the whole tactic mechanism, so it is worth stating plainly: TileK is the ONE config axis that changes the offline layout (prepare_dense_for_tile takes tile_k; formats.py derives fold from (bits, tile_k)). The user's constraint is that a search must never move the bytes on disk, so TileK cannot be selected per M like the other axes — it is a per-format, possibly per-tensor, OFFLINE decision made once by measurement and recorded, while (TileM, TileN, WarpM, WarpN, stages) vary with M inside it. Anything you build for ② should make that split explicit rather than implicit.

Same process requests: commit per item; inbox-consumed as soon as read; blocked-on in STATUS.md and keep going on the rest.

## Last assistant conclusions

### 2026-08-05 01:23 UTC

The worktree confirms 055 is still in progress: it contains uncommitted runtime-validity-query work, and `STATUS.md` explicitly says “055 item 1.” I’ll finish and commit 055 first as requested, then consume and implement 056. I’m reading both inbox entries now so the boundary and acceptance criteria remain exact.

### 2026-08-05 01:25 UTC

The 055 implementation was still being written into the shared worktree during my inspection (the backend files changed after the initial status check). I’ve now found the complete shape: exact compiled-kernel shared-memory checks for dense/grouped plus the CUDA MoE predicate. I’m letting the writes settle, then I’ll run the local ABI/compile gates and commit 055 cleanly before touching TileK.
