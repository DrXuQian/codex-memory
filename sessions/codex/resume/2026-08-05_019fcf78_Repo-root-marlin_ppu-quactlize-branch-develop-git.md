# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Your 053 is in; thank you, and your judgement on GroupedSpace not diverging is accepted — "the grouped-only scheduler and pointer-array epilogue alter routing, not legal tile geometry" is a better statement of it than mine was, and checking the comparator at TileK 32/64/128/256 rather than just 64 is the part I had not done.

Read INBOX 055 and do it. It comes from reading the REAL TensorRT-LLM (cloned from NVIDIA/TensorRT-LLM main, not the standalone extract in Kernels/ — that extract is missing the selection layer entirely, which is what led me to give you a wrong instruction in 049 that 054 withdrew).

Most of the comparison says we are already right. TRT-LLM's MoE and dense use the IDENTICAL M axis — total tokens, power-of-two buckets, round down — and separate FC1/FC2 by custom-op name only because both calls pass the same tensors; our key includes (n,k) so they separate by construction. Two things we lack, both properties of the compiled kernels and so yours:

① A PER-SHAPE VALIDITY QUERY. Their TunableRunner has get_valid_tactics(inputs, profile): the tuner asks which tactics are legal FOR THESE INPUTS and profiles only those, with an explicit docstring saying they deliberately have no separate can_implement — the returned tactics must be valid. quactlize_ppu_list_configs() returns the whole compiled set with no knowledge of m/n/k/group_size, so an offline tuner will profile configs that cannot run, and on this device an illegal launch is an unconditional device assert that poisons the context. That is the same failure the four-warp gate prevents, one level up and at run time. Shape is yours: filtered list, per-config predicate, or a flag in the record — ppu_tactic_space.hpp has the arithmetic but it is compile-time and the caller needs it at run time.

② THE DEFAULT MUST PROVABLY IMPLEMENT ANY SHAPE. tactic -1 in their design is documented as "the fallback kernel which should be able to implement any shapes", and that is precisely what makes tuning optional. Our defaults are dense 64x64:32x32:s3 and grouped 16x128:16x16:s2. Is either guaranteed at n=32, or at a group size where its stages overrun shared memory? If the default cannot cover the whole domain, I would rather the contract say "default covers X" than carry an unqualified promise nobody checked — because "declines to the compiled default" declining into something that also cannot run is worse than the abort it replaced.

Not yours, so you can ignore them: the bucket set and round rule go in the tactic table schema (mine), and the EP/TP deflation before lookup (their round_rule does x // ep_size under data parallel; our 122B target is TP=2) belongs to the caller.

Same process requests: commit per item; write inbox-consumed as soon as you have read; blocked-on in STATUS.md and keep going on the rest.

One more thing I want your judgement on rather than agreement: ① could equally be argued to belong in the offline tuner rather than the library — the tuner could re-implement the legality arithmetic from ppu_tactic_space.hpp in Python. I think that is wrong because it is a second copy of a predicate that must agree with what the kernels actually do, and this repo has been bitten by exactly that shape more than once. But you know the arithmetic better than I do; if a runtime query is expensive or awkward for a reason I cannot see, say so and propose the alternative.

- **Thread ID:** `019fcf78-2c1d-7b23-af9c-570ac08f406d`
- **Started / last event:** 2026-08-05 01:09 UTC → 2026-08-05 02:09 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/05/rollout-2026-08-05T09-09-47-019fcf78-2c1d-7b23-af9c-570ac08f406d.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "cf07d7f5bc0901d5deafb6753ab0a9e3e8429305", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-05_019fcf78_Repo-root-marlin_ppu-quactlize-branch-develop-git.md](../transcripts/2026-08/2026-08-05_019fcf78_Repo-root-marlin_ppu-quactlize-branch-develop-git.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Your 053 is in; thank you, and your judgement on GroupedSpace not diverging is accepted — "the grouped-only scheduler and pointer-array epilogue alter routing, not legal tile geometry" is a better statement of it than mine was, and checking the comparator at TileK 32/64/128/256 rather than just 64 is the part I had not done.

Read INBOX 055 and do it. It comes from reading the REAL TensorRT-LLM (cloned from NVIDIA/TensorRT-LLM main, not the standalone extract in Kernels/ — that extract is missing the selection layer entirely, which is what led me to give you a wrong instruction in 049 that 054 withdrew).

Most of the comparison says we are already right. TRT-LLM's MoE and dense use the IDENTICAL M axis — total tokens, power-of-two buckets, round down — and separate FC1/FC2 by custom-op name only because both calls pass the same tensors; our key includes (n,k) so they separate by construction. Two things we lack, both properties of the compiled kernels and so yours:

① A PER-SHAPE VALIDITY QUERY. Their TunableRunner has get_valid_tactics(inputs, profile): the tuner asks which tactics are legal FOR THESE INPUTS and profiles only those, with an explicit docstring saying they deliberately have no separate can_implement — the returned tactics must be valid. quactlize_ppu_list_configs() returns the whole compiled set with no knowledge of m/n/k/group_size, so an offline tuner will profile configs that cannot run, and on this device an illegal launch is an unconditional device assert that poisons the context. That is the same failure the four-warp gate prevents, one level up and at run time. Shape is yours: filtered list, per-config predicate, or a flag in the record — ppu_tactic_space.hpp has the arithmetic but it is compile-time and the caller needs it at run time.

② THE DEFAULT MUST PROVABLY IMPLEMENT ANY SHAPE. tactic -1 in their design is documented as "the fallback kernel which should be able to implement any shapes", and that is precisely what makes tuning optional. Our defaults are dense 64x64:32x32:s3 and grouped 16x128:16x16:s2. Is either guaranteed at n=32, or at a group size where its stages overrun shared memory? If the default cannot cover the whole domain, I would rather the contract say "default covers X" than carry an unqualified promise nobody checked — because "declines to the compiled default" declining into something that also cannot run is worse than the abort it replaced.

Not yours, so you can ignore them: the bucket set and round rule go in the tactic table schema (mine), and the EP/TP deflation before lookup (their round_rule does x // ep_size under data parallel; our 122B target is TP=2) belongs to the caller.

Same process requests: commit per item; write inbox-consumed as soon as you have read; blocked-on in STATUS.md and keep going on the rest.

One more thing I want your judgement on rather than agreement: ① could equally be argued to belong in the offline tuner rather than the library — the tuner could re-implement the legality arithmetic from ppu_tactic_space.hpp in Python. I think that is wrong because it is a second copy of a predicate that must agree with what the kernels actually do, and this repo has been bitten by exactly that shape more than once. But you know the arithmetic better than I do; if a runtime query is expensive or awkward for a reason I cannot see, say so and propose the alternative.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×14
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_backend.cu` ×11
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×3
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_tactic_space.hpp` ×3
- `/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh` ×3
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_ppu_config.h` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_backend.cu` ×3
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_unit_pack.cpp` ×2
- `/root/marlin_ppu/quactlize/dev/fold_derivation/SHIPPING_DECISION_AUDIT_057.md` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_dense_configs.inc` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_grouped_configs.inc` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_format_config.inc` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_format_config.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_layout.cu` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/MAINLOOP_SPLIT_READING_058.md` ×1

## Last assistant conclusions

### 2026-08-05 02:09 UTC

Done. Pulled `develop` first and completed INBOX 055–058.

Key outcomes:

- Added library-owned per-shape validity queries with exact shared-storage checks. They are host-only, launch-free, and cheap; duplicating the predicate in Python would be the wrong boundary.
- Proved defaults cover the documented resident ABI domain. `n=32` is outside that domain; N/K must be positive multiples of 256.
- Unified per-format TileK decisions and exposed truthful TileK through the v2 validity records.
- Audited shipping decision ownership in [SHIPPING_DECISION_AUDIT_057.md](/root/marlin_ppu/quactlize/dev/fold_derivation/SHIPPING_DECISION_AUDIT_057.md).
- Completed the three-mainloop reading in [MAINLOOP_SPLIT_READING_058.md](/root/marlin_ppu/quactlize/dev/fold_derivation/MAINLOOP_SPLIT_READING_058.md).

My 058 judgment: one shared pipeline driver is correct, but three B-provider policies alone are insufficient. A loading, B layout/lifetime, metadata sourcing, and eager-versus-chunked conversion are orthogonal policies. The split has already caused correctness drift, including scale-copy coverage and two-plane consume-stage hazards.

Commits were separated per item:

- `aa7654b`, `c56563d` — 055
- `c337afa`, `f0fbf19`, `978a742` — 056
- `23cb896` — 057
- `d37d0ff` — 058

Branch is currently one commit ahead of `origin/develop`. Only the live `.coord/STATUS.md` checkpoint remains uncommitted, as intended by the coordination protocol.
