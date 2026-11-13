# Resume brief: Repo /root/marlin_ppu/quactlize, branch dev. Review commit HEAD (the layout naming scheme) plus quactlize/layouts.py,
quactlize/csrc/preprocess/weight_layout.h, tests/test_layouts.py, and the changed entry point in
quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp.

ARGUE, do not summarise. Where is this wrong?

1. The naming rule is "a layout's name is the ordered join of its step tokens". Does that actually hold up? Find a
   real arrangement in this tree it cannot express, or a case where two genuinely different arrangements would
   collide on one name.
2. The step vocabulary is <consumer><parameter> with consumers mma/mem/aiu/cvt/layout. Is "layout" (used for the
   transpose) a hole in that scheme? Are there reorderings in quactlize/include/ (xplane_offline.hpp,
   fold_traits.hpp, gguf_scale_layout.hpp) that the vocabulary cannot name?
3. The C++ table in weight_layout.h and the python registry are cross-checked by parsing the header with a regex.
   That parse is itself untested. What breaks it, and is there a better shape?
4. I claim runtime transforms (bank swizzle, hardware swzl) must stay OUT of this vocabulary because they never
   touch a stored byte. Argue against that: is there a case where a runtime transform must be named alongside a
   stored one for the pair to be checkable?
5. preprocess_weights_to_layout validates the element width and the shape multiple. What else can silently produce a
   different arrangement than the name promises? Cite the code path.

Be specific, cite files/lines. If a design decision is wrong, say so plainly.

- **Thread ID:** `019fbbc1-7511-7bf3-aea8-f701ce44422d`
- **Started / last event:** 2026-08-01 05:17 UTC → 2026-08-01 05:31 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/01/rollout-2026-08-01T13-17-25-019fbbc1-7511-7bf3-aea8-f701ce44422d.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "df986a8ad358df0883fee0da8042c13ee72289eb", "branch": "dev", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-01_019fbbc1_Repo-root-marlin_ppu-quactlize-branch-dev-Review-c.md](../transcripts/2026-08/2026-08-01_019fbbc1_Repo-root-marlin_ppu-quactlize-branch-dev-Review-c.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch dev. Review commit HEAD (the layout naming scheme) plus quactlize/layouts.py,
quactlize/csrc/preprocess/weight_layout.h, tests/test_layouts.py, and the changed entry point in
quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp.

ARGUE, do not summarise. Where is this wrong?

1. The naming rule is "a layout's name is the ordered join of its step tokens". Does that actually hold up? Find a
   real arrangement in this tree it cannot express, or a case where two genuinely different arrangements would
   collide on one name.
2. The step vocabulary is <consumer><parameter> with consumers mma/mem/aiu/cvt/layout. Is "layout" (used for the
   transpose) a hole in that scheme? Are there reorderings in quactlize/include/ (xplane_offline.hpp,
   fold_traits.hpp, gguf_scale_layout.hpp) that the vocabulary cannot name?
3. The C++ table in weight_layout.h and the python registry are cross-checked by parsing the header with a regex.
   That parse is itself untested. What breaks it, and is there a better shape?
4. I claim runtime transforms (bank swizzle, hardware swzl) must stay OUT of this vocabulary because they never
   touch a stored byte. Argue against that: is there a case where a runtime transform must be named alongside a
   stored one for the pair to be checkable?
5. preprocess_weights_to_layout validates the element width and the shape multiple. What else can silently produce a
   different arrangement than the name promises? Cite the code path.

Be specific, cite files/lines. If a design decision is wrong, say so plainly.

## Last assistant conclusions

### 2026-08-01 05:31 UTC

Plainly: the central claim is false. The code joins token strings, but those tokens do not uniquely identify the transformations. Worse, the registered int2 name currently promises a bias that the implementation explicitly does not perform.

### 1. “Ordered join” is not an injective naming rule

`Layout.name` mechanically joins strings, but that proves only formatting, not uniqueness ([layouts.py:111](/root/marlin_ppu/quactlize/quactlize/layouts.py:111)).

There are concrete collisions:

- `mma_row(32)` always produces `mmarow`; it has no parameter for which 32-row permutation is used ([layouts.py:56](/root/marlin_ppu/quactlize/quactlize/layouts.py:56)). The implementation has two genuinely different 32-row maps selected by `is_int8_mma`: the comments list both maps, and the loop uses different formulas ([cutlass_preprocessors.cpp:143](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:143), [cutlass_preprocessors.cpp:218](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:218)). They are both called `mmarow`. Today the complete W4A8 name happens to differ because another gate also removes `cvtword_bias`; that accidental correlation does not make the row token unambiguous.

- `code_bias(amount)` discards `amount` and always returns `bias` ([layouts.py:94](/root/marlin_ppu/quactlize/quactlize/layouts.py:94)). The real +8 and +128 operations are different ([cutlass_preprocessors.cpp:407](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:407), [cutlass_preprocessors.cpp:428](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:428)). The amount can only be inferred from some other token, contradicting “a step’s parameter is in the name.”

- `mem_cacheline_col_tile(interleave, tile_rows)` omits `tile_rows` from `clN` ([layouts.py:69](/root/marlin_ppu/quactlize/quactlize/layouts.py:69)), even though the address map uses both `rows_per_tile` and `interleave` ([cutlass_preprocessors.cpp:544](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:544)). `ColumnMajorTileInterleave<64,4>` and `<128,4>` would collide as `cl4`.

- The strongest existing-tree collision is `cvt_plane_fold(planes)`: every two-plane format becomes `plane2` ([layouts.py:100](/root/marlin_ppu/quactlize/quactlize/layouts.py:100)). But Q3 is int2+int1, Q5 is int4+int1, and Q6 is int4+int2; the stored high-plane map is parameterized by `LowBits`, `HiBits`, `F1`, `F2`, and all five tile dimensions ([xplane_offline.hpp:132](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:132), [xplane_offline.hpp:139](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:139)). These are real, different byte placements that the proposed token collapses to one name.

Collisions are also silently hidden: `_add` assigns directly into `LAYOUTS[lay.name]`, so a later colliding registration overwrites the earlier one ([layouts.py:134](/root/marlin_ppu/quactlize/quactlize/layouts.py:134)). It should at least reject duplicate canonical names and aliases.

There is also a producible but unregistered arrangement. The retained boolean op accepts `is_int8_mma=true, use_aiu_interleaved=true`; nothing rejects that combination ([weight_preprocess_ops.cpp:152](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:152)). The lower chain applies the W4A8 row map, then AIU, then skips converter/bias ([cutlass_preprocessors.cpp:660](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:660)). No corresponding layout is registered. The claim that unregistered arrangements “do not exist” is therefore wrong.

Finally, semantic changes inside a step do not automatically change any token. Fixing a lane map while retaining `mmarow` leaves the name unchanged. A version or mapping-contract digest is still required unless every semantic change is manually reflected in a token.

### 2. `layout` is a hole, and the stated token grammar is fiction

A consumer answers “who interprets this mapping?” `layout` answers nothing; it is the category being named. The transpose is ultimately required by a loader/iterator/MMA contract, not by “layout.”

The token does not even follow the documented syntax: its consumer field is `"layout"` while its token is merely `"tr"` ([layouts.py:63](/root/marlin_ppu/quactlize/quactlize/layouts.py:63)). The same disconnect exists for:

- consumer `mem`, token `cl4`;
- consumer `aiu`, token `foldn2`;
- consumer `cvt`, tokens `bias` and `plane2`.

The test verifies only that the separate `consumer` field belongs to an allowlist; it never verifies that the token contains that consumer or all parameters ([test_layouts.py:116](/root/marlin_ppu/quactlize/tests/test_layouts.py:116)).

The include-side arrangements cannot be represented by this vocabulary:

- Fold placement is not determined by `F`. `FoldTraits` derives it from `Bits`, `TN`, `TK`, and indirectly `WN`; even the physical row count, run width, and codes per word change ([fold_traits.hpp:49](/root/marlin_ppu/quactlize/quactlize/include/fold_traits.hpp:49)). The file explicitly distinguishes whole-word and bit-granular packers, with `WN > 32` requiring multiple columns inside one word ([fold_traits.hpp:88](/root/marlin_ppu/quactlize/quactlize/include/fold_traits.hpp:88), [fold_traits.hpp:126](/root/marlin_ppu/quactlize/quactlize/include/fold_traits.hpp:126)). `foldn2` does not name that distinction.

- Xplane placement depends on the complete copy/MMA/converter geometry, not merely “two planes” ([xplane_offline.hpp:47](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:47), [xplane_offline.hpp:159](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:159)).

- GGUF scale blocks are stored-byte arrangements too. Q4/Q5 use one 12-byte field map, while Q3 uses another 12-byte map with different grouping and bias ([gguf_scale_layout.hpp:39](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:39), [gguf_scale_layout.hpp:61](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:61)). Q2 and Q6 are both 16 bytes but differ in field width, signedness, and presence of minima ([gguf_scale_layout.hpp:82](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:82), [gguf_scale_layout.hpp:98](/root/marlin_ppu/quactlize/quactlize/include/gguf_scale_layout.hpp:98)). The vocabulary has no scale/decoder consumer and no way to name byte-and-bit field maps.

If this registry is intended only for this one mixed-GEMM preprocessor, say that and remove the misleading fold/xplane constructors. If it is intended to name stored tensor arrangements generally, the model is materially incomplete.

### 3. The regex cross-check is fail-open

The parser is indirectly exercised against today’s formatting, but its correctness boundary is not tested. It accepts matching substrings and ignores everything else ([test_layouts.py:24](/root/marlin_ppu/quactlize/tests/test_layouts.py:24)).

Innocent C++ changes break it:

- `{ "logical", ... }` fails because the regex requires `{"` with no whitespace.
- Comments between fields fail because `\s*` does not consume comments.
- Constants, hexadecimal values, digit separators, or expressions fail because integers must be `-?\d+`.
- Renaming or reformatting `kTable = {` breaks the exact `index`.
- A comment or string containing `};` truncates the body at the wrong place.

More seriously, it can pass while disagreeing with compiled C++:

- It matches row-shaped text inside comments and `#if 0`.
- An active row formatted `{ "extra", ... }` is ignored. If an inactive/commented row retains the expected compact spelling, the Python tests see the expected table while C++ compiles the other one.
- An extra active row using constants or macros is invisible to `finditer`.

The better design is
… [truncated 5934 chars]
