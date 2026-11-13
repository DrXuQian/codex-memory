# Resume brief: Resume on /root/marlin_ppu/quactlize (branch `develop`). `git pull --recurse-submodules` first, read `.coord/INBOX.md` items 022, 023 and 024, and keep `.coord/STATUS.md` current with `inbox-consumed` and the wall-clock `updated-at` you adopted.

THE USER WANTS YOUR INDEPENDENT ANALYSIS OF A MEASUREMENT I JUST MADE. Do not take my reading of it on trust — I have been wrong about this exact file twice today.

I wrote `dev/fold_derivation/l105_low_plane_config_classes.cu` (registered as a gate, builds and runs in ~36s) because two claims in the repo contradicted each other about `place_derived`:

    layouts.py xplane()                  "TK changes it ... TN,WN through TN/max(WN,16)"
    unfused_weight_dequantize.hpp (l61)  "the unfolded placement is TILE-INVARIANT ... any (TN,TK) within the
                                          delivery bound gives the same buffer"

It groups every legal configuration by its STORED BYTES. Result:

    int1  3 classes / 7 built (5 skipped unbuildable)
      F=1 TK=256: 4 configs, ONE hash (TM 64/128, TN 64/128/256, WM/WN 32/64)
      F=2 TK=128: 2 configs, one hash
      F=4 TK=64 : 1 config
    int2  4 classes / 10 built
      F=1: 6 configs, ONE hash, spanning TK 128 AND 256, TN 64/128/256, TM 64/128
      F=2 TK=128: 2 configs / F=2 TK=64: 1 / F=4 TK=64: 1
    int4  4 classes / 12 built
      F=1: 8 configs, ONE hash, spanning TK 64/128/256, TN 64/128/256, TM 32/64/128, WM/WN 32/64
      F=2 TK=128: 2 / F=2 TK=64: 1 / F=4 TK=64: 1

MY READING, which is what I want you to attack: at F=1 the placement is tile-invariant and depends on the bit
width alone; TK reaches the bytes only THROUGH THE FOLD, fold being the compensation for a delivery run
(TK*bits) shorter than 32 bytes, so at F=1 there is nothing to reach through. That makes l61 right and the
xplane() table wrong, and it means xplane()'s token — which carries (bits, WON, TK, F) unconditionally — is
OVERNAMING exactly the way xplane_hi's was before we fixed it this afternoon: two F=1 tactics differing only in
TK get different names for identical bytes, and a name that splits an equivalence class forces a repack the
bytes do not require.

THE USER'S GOAL, which is what the analysis is for: **the ideal end state is that each format pins ONE optimal F,
so the layout is a function of the format alone** — no descriptor in the artifact header, and the online tactic
search becomes "anything that keeps that F". My reading says the low plane already reaches that at F=1, since
F=1 is legal for every bit width given a minimum TK (int4 >= 64, int2 >= 128, int1 = 256 exactly), and
ppu_dense_layout already uses F=1 everywhere.

WHAT I WANT FROM YOU, in this order:

1. **Attack the reading.** Is "F=1 => tile-invariant" actually what the data shows, or is my grid too narrow to
   support it? Configurations I did NOT try are the obvious risk — non-square warps, TN not a multiple of 64,
   TK beyond 256, TM below 32. If the invariance is an artefact of the grid, say so and name the configuration
   that would break it.

2. **Can F>1 be pruned entirely?** If every format can be served at F=1, the F>1 classes are dead weight and the
   whole descriptor question disappears for single-plane formats. The cost is a TK floor per bit width. Is there
   any tactic worth having that NEEDS F>1 — i.e. wants a TK below that floor badly enough to pay a second layout?
   You measured the MoE and dense bands; you are better placed than I am to answer whether such a tactic exists.

3. **Then the same question for the two-plane formats.** l104 gave (F1, F2, DL1, DL2, folded_R2). If the low
   plane collapses to (bits) at F=1, does the high plane collapse similarly at F1=F2=1 — or is Q6's TK128-vs-TK256
   split still there with both folds at 1? Your 058 says it IS still there, which would mean two-plane formats
   cannot reach the user's ideal state and need at least the delivery counts. If so, say it plainly: the goal is
   reachable for single-plane and not for two-plane, and that asymmetry is the answer rather than a gap.

4. If you agree the xplane() token overnames, tell me the token you want and I will change it — layouts.py is
   mine. If you think TK should stay in the name even at F=1 for some reason I have not seen, say why.

Nothing else is blocked on you. The nine matrix promotions still need the ppu001 `fully_quantized_*.log` contents,
which only the user can supply and which are queued in `.coord/BOX.md`. Commit and push as you go, no
Co-Authored-By trailer.

- **Thread ID:** `019fca98-bf43-72d2-b0fb-8572779d4ad2`
- **Started / last event:** 2026-08-04 02:27 UTC → 2026-08-04 02:55 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/04/rollout-2026-08-04T10-27-15-019fca98-bf43-72d2-b0fb-8572779d4ad2.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "0bba86854915f0c7894dc8f74f9034fa7ee0ab43", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-04_019fca98_Resume-on-root-marlin_ppu-quactlize-branch-develop.md](../transcripts/2026-08/2026-08-04_019fca98_Resume-on-root-marlin_ppu-quactlize-branch-develop.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Resume on /root/marlin_ppu/quactlize (branch `develop`). `git pull --recurse-submodules` first, read `.coord/INBOX.md` items 022, 023 and 024, and keep `.coord/STATUS.md` current with `inbox-consumed` and the wall-clock `updated-at` you adopted.

THE USER WANTS YOUR INDEPENDENT ANALYSIS OF A MEASUREMENT I JUST MADE. Do not take my reading of it on trust — I have been wrong about this exact file twice today.

I wrote `dev/fold_derivation/l105_low_plane_config_classes.cu` (registered as a gate, builds and runs in ~36s) because two claims in the repo contradicted each other about `place_derived`:

    layouts.py xplane()                  "TK changes it ... TN,WN through TN/max(WN,16)"
    unfused_weight_dequantize.hpp (l61)  "the unfolded placement is TILE-INVARIANT ... any (TN,TK) within the
                                          delivery bound gives the same buffer"

It groups every legal configuration by its STORED BYTES. Result:

    int1  3 classes / 7 built (5 skipped unbuildable)
      F=1 TK=256: 4 configs, ONE hash (TM 64/128, TN 64/128/256, WM/WN 32/64)
      F=2 TK=128: 2 configs, one hash
      F=4 TK=64 : 1 config
    int2  4 classes / 10 built
      F=1: 6 configs, ONE hash, spanning TK 128 AND 256, TN 64/128/256, TM 64/128
      F=2 TK=128: 2 configs / F=2 TK=64: 1 / F=4 TK=64: 1
    int4  4 classes / 12 built
      F=1: 8 configs, ONE hash, spanning TK 64/128/256, TN 64/128/256, TM 32/64/128, WM/WN 32/64
      F=2 TK=128: 2 / F=2 TK=64: 1 / F=4 TK=64: 1

MY READING, which is what I want you to attack: at F=1 the placement is tile-invariant and depends on the bit
width alone; TK reaches the bytes only THROUGH THE FOLD, fold being the compensation for a delivery run
(TK*bits) shorter than 32 bytes, so at F=1 there is nothing to reach through. That makes l61 right and the
xplane() table wrong, and it means xplane()'s token — which carries (bits, WON, TK, F) unconditionally — is
OVERNAMING exactly the way xplane_hi's was before we fixed it this afternoon: two F=1 tactics differing only in
TK get different names for identical bytes, and a name that splits an equivalence class forces a repack the
bytes do not require.

THE USER'S GOAL, which is what the analysis is for: **the ideal end state is that each format pins ONE optimal F,
so the layout is a function of the format alone** — no descriptor in the artifact header, and the online tactic
search becomes "anything that keeps that F". My reading says the low plane already reaches that at F=1, since
F=1 is legal for every bit width given a minimum TK (int4 >= 64, int2 >= 128, int1 = 256 exactly), and
ppu_dense_layout already uses F=1 everywhere.

WHAT I WANT FROM YOU, in this order:

1. **Attack the reading.** Is "F=1 => tile-invariant" actually what the data shows, or is my grid too narrow to
   support it? Configurations I did NOT try are the obvious risk — non-square warps, TN not a multiple of 64,
   TK beyond 256, TM below 32. If the invariance is an artefact of the grid, say so and name the configuration
   that would break it.

2. **Can F>1 be pruned entirely?** If every format can be served at F=1, the F>1 classes are dead weight and the
   whole descriptor question disappears for single-plane formats. The cost is a TK floor per bit width. Is there
   any tactic worth having that NEEDS F>1 — i.e. wants a TK below that floor badly enough to pay a second layout?
   You measured the MoE and dense bands; you are better placed than I am to answer whether such a tactic exists.

3. **Then the same question for the two-plane formats.** l104 gave (F1, F2, DL1, DL2, folded_R2). If the low
   plane collapses to (bits) at F=1, does the high plane collapse similarly at F1=F2=1 — or is Q6's TK128-vs-TK256
   split still there with both folds at 1? Your 058 says it IS still there, which would mean two-plane formats
   cannot reach the user's ideal state and need at least the delivery counts. If so, say it plainly: the goal is
   reachable for single-plane and not for two-plane, and that asymmetry is the answer rather than a gap.

4. If you agree the xplane() token overnames, tell me the token you want and I will change it — layouts.py is
   mine. If you think TK should stay in the name even at F=1 for some reason I have not seen, say why.

Nothing else is blocked on you. The nine matrix promotions still need the ppu001 `fully_quantized_*.log` contents,
which only the user can supply and which are queued in `.coord/BOX.md`. Commit and push as you go, no
Co-Authored-By trailer.

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/dev/fold_derivation/l105_low_plane_config_classes.cu` ×7
- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×2
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l104_place_hi_invariance.cu` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/unfused_weight_dequantize.hpp` ×1

## Last assistant conclusions

### 2026-08-04 02:55 UTC

Your reading is directionally right, but too broad.

1. “F=1 ⇒ tile-invariant”

It holds for every complete tactic tested with `TK <= 256`, including the omitted axes:

- `TM/TN` down to 16
- `TN=32`
- `WN=16`
- non-square warps in both orientations
- a 32-warp CTA
- int2 at TK 128/256 and int4 at TK 64/128/256

But `int4 TM64/TN64/TK512 w32x32 F=1` compiles and produces different bytes. Therefore the defensible statement is:

> F=1 is tile-invariant within the unfolded interleave-256 domain, `TK <= 256`.

The original L105 also misclassified its F=4/WN=32 rows: they had `NI=0` or over-delivery, leaving `plane_map` unset and emitting all-zero buffers. Those are now skipped, with legal WN=64 controls substituted. L105 now groups by complete stored bytes rather than hashes alone and uses a non-periodic fixture: [l105_low_plane_config_classes.cu](/root/marlin_ppu/quactlize/dev/fold_derivation/l105_low_plane_config_classes.cu:19).

2. F>1 cannot be pruned without paying real performance

The measurements contain several tactics worth retaining:

- Dense int1: TK64/F4 is 215.23 µs / 63.9%; TK128/F2 is 219.70 µs / 62.6%; TK256/F1 fell to roughly 23% MFU.
- Dense int2’s measured winner is TK64/F2 at 233.76 µs / 58.8%.
- MoE int4: TK32/F2 is 317.26 µs versus TK64/F1 at 362.14 µs—12.4% faster.
- MoE int2: TK32/F4 is 295.08 µs versus TK64/F2 at 300.26 µs; TK128/F1 was worse across the sweep.

This does not prove folding itself causes the gain—TK, A-smem, stages, and F move together—but it conclusively answers pruning: requiring F1 removes measured winning tactics.

`ppu_dense_layout` using F1 everywhere establishes a conservative, format-selected producer. It does not establish performance optimality. In fact, “one optimal F per format across dense and MoE” is contradicted by the present winners.

Also, fixed F>1 is not sufficient: L105 shows the same F at different TK can produce different classes. A format may pin one canonical layout, but tactic search must preserve that layout class, not merely F.

3. The two-plane Q6 split in 058 was invalid evidence

Q6/TK256 covers only half its logical high-plane tile. L104 previously checked `NI>0` but not whether `tile_map_hi` was a bijection, so it classified bytes emitted by an invalid tactic.

After adding the completeness requirement:

- all six complete Q6 `F1=F2=1, TK128` configurations have identical bytes;
- every Q6/TK256 row is rejected as incomplete;
- therefore there is no valid Q6 TK128-vs-TK256 split.

That correction is in [l104_place_hi_invariance.cu](/root/marlin_ppu/quactlize/dev/fold_derivation/l104_place_hi_invariance.cu:9).

Two-plane folds alone are still insufficient when the high plane folds: Q3/Q5 at fixed `(F1,F2)=(1,2)` split when `TN/F2` changes. Thus:

- The claimed “single-plane reachable, two-plane impossible because delivery counts” asymmetry is not established.
- A descriptor-free header is possible for all formats if each format pins its canonical layout—Q3/Q5 TK256 and Q6 TK128 today.
- “Anything keeping the same folds” is unsafe for folded two-plane tactics because `folded_R2 = TN/F2` still matters.

4. Token recommendation

For the low plane, use:

```text
xp{bits}f1
```

when `F=1` and `TK<=256`. Examples: `xp1f1`, `xp2f1`, `xp4f1`.

The constructor should reject `F=1, TK>256` before collapsing the token. For `F>1`, retain the existing:

```text
xp{bits}w{WON}k{TK}f{F}
```

because fixed-F folded configurations demonstrably split across TK, and there is not yet enough evidence to remove WON.

I would not simplify `xplane_hi`’s delivery fields yet: the old evidence for needing them at both folds 1 is gone, but there is no second complete same-fold/different-delivery tactic proving they are redundant either. `folded_R2` is definitely necessary.

Committed and pushed:

- `f8aa37d Bound low-plane invariance to complete tactics`
- `5cd31ff Record low-plane invariance verdict`

L105 passes its strict local gate in 56.6s; corrected L104 builds, runs, and exits cleanly. `.coord/STATUS.md` records inbox 024 and the adopted UTC timestamp. The unrelated coordination-owned `ci/local_gates.py` edit remains untouched.
