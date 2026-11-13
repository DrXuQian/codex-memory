# Resume brief: Go ahead — implement your own proposal from the last exchange (compact-A capacity as a per-config axis, kernel + tactic space). The user approved it. Division as you stated: kernel and ppu_tactic_space.hpp are yours; I carry the field through the emitter and make the sweep search it.

Concretely, what I understood you to be committing to:

  * ppu_tactic_space.hpp: replace the 1/2/4 whitelist with the five real legality conditions — capacity > 0,
    capacity <= TileM, TileM % capacity == 0, the selected collective supports compact A, and the compiled shared
    storage fits. Admit 8. The SET of capacities we emit moves to the emitter and is not an exclusion.
  * Capacity 0 stays ordinary unrestricted A and stays the universal/default row, so RequireUniversalFallback's
    static_assert is untouched.
  * The launcher keeps its m > capacity guard as a per-specialisation defence (QueryOnly goes through the real
    launcher, and direct APIs can be called without a query) — what goes away is the binary-wide outcome where
    every row declines above one build-time capacity.
  * "Narrowest capacity covering M" is dispatch policy, not legality.

Two things I need from your side so my half lines up:

  1. THE ABI. Tell me exactly how capacity reaches the collective once it is not PPU_A_CPASYNC — a template
     parameter on MainloopPolicy, a field on the dispatch policy, something else. I have to emit it into
     benchmarks/lowbit_dense_configs.inc and into the X-macro the bench expands, and the two must agree or the
     table compiles into a kernel nobody asked for. That is the same seam that made ArtifactTileK correct only
     because MainloopPolicy took it explicitly.
  2. Whether PPU_A_CPASYNC survives as a compatibility spelling or is deleted. If it survives I keep it out of
     the sweep entirely; if it is deleted I have benchmarks and dev probes to migrate.

On the 5x instantiation cost you flagged: I think it prunes hard on my side without touching semantics. Capacity
is only useful when M <= capacity, and capacity <= TileM, so only rows with small TileM need a non-zero capacity
at all — a TileM=128 prefill row carries capacity 0 and nothing else. I will emit capacities only where TileM is
small enough for them to be selectable, and log what was dropped rather than silently truncating. If you think
that prune is wrong, say so before I build it.

Please also state the numerical claim you expect to hold, so I can gate it: at M <= capacity, is the compact path
bit-identical to capacity 0, or only equal within tolerance? `ppu-a-must-stay-in-smem` records bit-exact for the
one-row case; I want to know if that is still the claim at 2, 4 and 8 before I write a gate that asserts it.

- **Thread ID:** `019fd5c3-27af-7c80-91cf-65f395a980c1`
- **Started / last event:** 2026-08-06 06:29 UTC → 2026-08-06 06:40 UTC
- **Working dir:** `/root`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/06/rollout-2026-08-06T14-29-24-019fd5c3-27af-7c80-91cf-65f395a980c1.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-08-06_019fd5c3_Go-ahead-implement-your-own-proposal-from-the-last.md](../transcripts/2026-08/2026-08-06_019fd5c3_Go-ahead-implement-your-own-proposal-from-the-last.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Go ahead — implement your own proposal from the last exchange (compact-A capacity as a per-config axis, kernel + tactic space). The user approved it. Division as you stated: kernel and ppu_tactic_space.hpp are yours; I carry the field through the emitter and make the sweep search it.

Concretely, what I understood you to be committing to:

  * ppu_tactic_space.hpp: replace the 1/2/4 whitelist with the five real legality conditions — capacity > 0,
    capacity <= TileM, TileM % capacity == 0, the selected collective supports compact A, and the compiled shared
    storage fits. Admit 8. The SET of capacities we emit moves to the emitter and is not an exclusion.
  * Capacity 0 stays ordinary unrestricted A and stays the universal/default row, so RequireUniversalFallback's
    static_assert is untouched.
  * The launcher keeps its m > capacity guard as a per-specialisation defence (QueryOnly goes through the real
    launcher, and direct APIs can be called without a query) — what goes away is the binary-wide outcome where
    every row declines above one build-time capacity.
  * "Narrowest capacity covering M" is dispatch policy, not legality.

Two things I need from your side so my half lines up:

  1. THE ABI. Tell me exactly how capacity reaches the collective once it is not PPU_A_CPASYNC — a template
     parameter on MainloopPolicy, a field on the dispatch policy, something else. I have to emit it into
     benchmarks/lowbit_dense_configs.inc and into the X-macro the bench expands, and the two must agree or the
     table compiles into a kernel nobody asked for. That is the same seam that made ArtifactTileK correct only
     because MainloopPolicy took it explicitly.
  2. Whether PPU_A_CPASYNC survives as a compatibility spelling or is deleted. If it survives I keep it out of
     the sweep entirely; if it is deleted I have benchmarks and dev probes to migrate.

On the 5x instantiation cost you flagged: I think it prunes hard on my side without touching semantics. Capacity
is only useful when M <= capacity, and capacity <= TileM, so only rows with small TileM need a non-zero capacity
at all — a TileM=128 prefill row carries capacity 0 and nothing else. I will emit capacities only where TileM is
small enough for them to be selectable, and log what was dropped rather than silently truncating. If you think
that prune is wrong, say so before I build it.

Please also state the numerical claim you expect to hold, so I can gate it: at M <= capacity, is the compact path
bit-identical to capacity 0, or only equal within tolerance? `ppu-a-must-stay-in-smem` records bit-exact for the
one-row case; I want to know if that is still the claim at 2, 4 and 8 before I write a gate that asserts it.

## Last assistant conclusions

### 2026-08-06 06:40 UTC

I’m blocked from editing the workspace: every shell and `apply_patch` call fails before execution with `bwrap: No permissions to create a new namespace`. I made no local or remote changes.

The agreed ABI is:

```cpp
MainloopPolicy<..., ArtifactTileK, ACompactRows>
filter_and_run<..., ArtifactTileK, ACompactRows>
```

The X-macro row should therefore be:

```cpp
X(TM, TN, TK, WM, WN, ST, A_COMPACT_ROWS, BODY)
```

and the bench instantiation:

```cpp
MainloopPolicy<..., ElementB, void, kArtifactTileK, ACompactRows>
```

`ACompactRows == 0` is ordinary unrestricted A and preserves the universal-fallback assertion.

`PPU_A_CPASYNC=N` survives as a compatibility default for callers omitting the new argument. Explicit emitted capacities—including `0`—override it. Keep the macro out of the sweep.

The TileM prune is not semantically sound: `TileM=128` remains selectable for `M<=8`, and may benefit most from compacting. Such pruning is acceptable only as explicitly logged search-policy coverage loss, not legality.

The numerical contract should be bit-identical, not tolerance-based: for each capacity `C ∈ {1,2,4,8}` and every `1 <= M <= C`, compare the logical `M×N` output bytes against capacity 0 for the same tactic and inputs. Any difference is a kernel bug. Capacities 2/4/8 are presently an expected contract, not yet hardware-validated evidence.

Once the workspace sandbox is restarted/fixed, I can land and verify the kernel/tactic-space changes.
