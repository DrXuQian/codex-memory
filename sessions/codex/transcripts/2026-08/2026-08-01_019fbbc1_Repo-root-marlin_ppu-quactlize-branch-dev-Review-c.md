# Repo /root/marlin_ppu/quactlize, branch dev. Review commit HEAD (the layout naming scheme) plus quactlize/layouts.py,
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

---

## User · 2026-08-01 05:17 UTC

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

## Assistant · 2026-08-01 05:17 UTC

I’ll inspect the commit diff and the requested Python/C++ paths, then trace the include-side reorderings and validation call path. I’ll treat the naming claims adversarially and cite exact lines.

<details><summary>2 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"pwd && rg --files -g 'AGENTS.md' -g '!build' -g '!dist' .. /root 2>/dev/null | head -80 && git status --short --branch && git log -1 --oneline --decorate && git show --stat --oneline --decorate HEA …`
- `exec: const r = await tools.exec_command({"cmd":"pwd","workdir":"/root/marlin_ppu/quactlize","login":false,"yield_time_ms":10000,"max_output_tokens":2000}); text(r.output);`

</details>

## Assistant · 2026-08-01 05:17 UTC

The shell sandbox cannot initialize in this environment (`bwrap` is denied), so I’m switching to the available read-only repository interfaces rather than guessing from filenames.

<details><summary>16 tool call(s)</summary>

- `exec: const xs = ALL_TOOLS.filter(x => /file|repo|git|code|search|read/i.test(x.name+" "+x.description)); text(xs);`
- `exec: const ns = ALL_TOOLS.map(x=>x.name).filter(n=>/github|file|repo|git|search|read/i.test(n)); text(ns.join("\n"));`
- `exec: const want = new Set([ "mcp__codex_apps__github_list_repositories", "mcp__codex_apps__github_search_repositories", "mcp__codex_apps__github_fetch_file", "mcp__codex_apps__github_fetch_commit", "mcp__codex_apps__github_compare_commits", "mcp …`
- `exec: const r = await tools.mcp__codex_apps__github_search_repositories({query:"quactlize", per_page:20}); text(r);`
- `exec: const names=["mcp__codex_apps__github_search_branches","mcp__codex_apps__github_fetch","mcp__codex_apps__github_fetch_commit"]; for (const x of ALL_TOOLS) if(names.includes(x.name)) text(x.name+"\n"+x.description);`
- `exec: const r = await tools.mcp__codex_apps__github_search_branches({owner:"DrXuQian",repo_name:"quactlize",query:"dev",page_size:20}); text(r);`
- `exec: const paths=[ "quactlize/layouts.py", "quactlize/csrc/preprocess/weight_layout.h", "tests/test_layouts.py", "quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp", "quactlize/include/xplane_offline.hpp", "quactlize/include/fold_traits.h …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_commit({repo_full_name:"DrXuQian/quactlize",commit_sha:"dev"}); text(r);`
- `exec: const path="quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const s=r.structuredContent?.content …`
- `exec: const qs=["preprocess_weights_for_mixed_gemm","mem_cacheline_col_tile_interleave","permute_B_rows_for_mixed_gemm","subbyte_transpose"]; for(const q of qs){ const r=await tools.mcp__codex_apps__github_search({query:q,repository_name:"DrXuQia …`
- `exec: const paths=[ "quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp", "quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.h", "quactlize/csrc/preprocess/cutlass_preprocessors.cpp", "quactlize/csrc/preprocess/cutl …`
- `exec: const path="quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredCon …`
- `exec: const path="quactlize/csrc/preprocess/cutlass_extensions/gemm/kernel/mixed_gemm_B_layout.h"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); text(r);`
- `exec: const path="quactlize/include/xplane_offline.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredContent?.content||"").split("\n"); …`
- `exec: const path="quactlize/include/fold_traits.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredContent?.content||"").split("\n"); te …`
- `exec: const path="quactlize/include/fold_traits.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredContent?.content||"").split("\n"); te …`

</details>

## Assistant · 2026-08-01 05:21 UTC

A first concrete failure is already visible: `mmarow` does not identify the row permutation. The same 32-row token is used for two different formulas selected by `is_int8_mma`; I’m now checking whether the surrounding steps happen to mask that collision and whether the fold/xplane formats expose stronger counterexamples.

<details><summary>12 tool call(s)</summary>

- `exec: const r=await tools.mcp__codex_apps__github_fetch_commit({repo_full_name:"DrXuQian/quactlize",commit_sha:"dev"}); const c=r.structuredContent?.commit||{}; text(Object.keys(c)); for(const k of Object.keys(c)) if(k!=="diff") text(k+": "+JSON. …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_commit({repo_full_name:"DrXuQian/quactlize",commit_sha:"dev"}); text((r.structuredContent?.commit?.files||[]).map(x=>x.filename).join("\n"));`
- `exec: const path="tests/test_layouts.py"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredContent?.content||"").split("\n"); text('line_cou …`
- `exec: const path="quactlize/layouts.py"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredContent?.content||"").split("\n"); text(ls.map((v, …`
- `exec: const path="quactlize/include/gguf_scale_layout.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredContent?.content||"").split("\n …`
- `exec: const path="quactlize/csrc/preprocess/cutlass_extensions/gemm/kernel/mixed_gemm_B_layout.h"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.st …`
- `exec: const path="quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredCon …`
- `exec: const path="quactlize/csrc/preprocess/weight_layout.h"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path,ref:"dev",encoding:"utf-8"}); const ls=(r.structuredContent?.content||"").split(" …`
- `exec: const r=await tools.web__run({open:[{ref_id:"https://api.github.com/repos/DrXuQian/quactlize/git/trees/dev?recursive=1"}],response_length:"long"}); text(r);`
- `exec: const r=await tools.web__run({open:[{ref_id:"https://github.com/DrXuQian/quactlize/tree/dev/quactlize/include"}],response_length:"long"}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",path:"quactlize/include",ref:"dev",encoding:"utf-8"}); text(r);`
- `exec: for(const q of ["bank swizzle","BankSwizzle","swizzle","SWZL","SmemLayoutScale","scale layout"]){ const r=await tools.mcp__codex_apps__github_search({query:q,repository_name:"DrXuQian/quactlize",topn:50}); text(q+": "+JSON.stringify(r.struc …`

</details>

## Assistant · 2026-08-01 05:31 UTC

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

The better design is one source of truth. Use a small declarative registry and generate both the Python objects and a C++ `.inc`/header. If generation is undesirable, expose the compiled C++ registry through a host-only function and compare that result with Python; that checks the compiler’s preprocessed view rather than source-shaped text. A tiny host test needs neither Torch nor a device.

Keeping the parser would require a strict, anchored grammar that consumes the entire table and rejects every residual token. Even then, it cannot model `#if` correctly without using the preprocessor.

### 4. Runtime transforms sometimes must be part of the compatibility identity

“Does not modify stored bytes” is the wrong criterion. Compatibility concerns the composed address map, not which phase performs each permutation.

Xplane is the counterexample in this tree. Its offline placement is derived directly from the runtime `PPU0010_TSM_LD_SWZL` copy trait’s `LogicalTV` map ([xplane_offline.hpp:35](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:35), [xplane_offline.hpp:59](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:59)). The high-plane mapping also depends on the runtime converter’s `MixGemm2Plane` pairing ([xplane_offline.hpp:159](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:159)). The file explicitly says the kernel’s `hi_vreg0` change and the offline placement are “one change”; changing only one makes the result worse ([xplane_offline.hpp:122](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:122)).

Therefore, the same stored bytes paired with a different runtime swzl/converter map are incompatible even though neither runtime map rewrites the file.

That does not mean pretending the runtime operation is an offline step. Use a two-part contract:

- stored-layout ID;
- runtime-reader/copy-map ID.

Then compatibility checks the pair—or checks that their composition equals the expected logical map. Pure internal bank swizzles that are canceled entirely within a kernel can remain unnamed. The blanket exclusion is wrong for runtime maps that constrain offline placement.

### 5. The entry point does not establish that its output has the named arrangement

The current int2 entry is objectively false. Python registers:

`mmarow_tr_cl8_cvtword_bias` with `code_bias(2)` ([layouts.py:164](/root/marlin_ppu/quactlize/quactlize/layouts.py:164)); C++ repeats that name ([weight_layout.h:50](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/weight_layout.h:50)). But the actual int2 implementation says values are already unsigned and performs **no bias**, only the word permutation ([cutlass_preprocessors.cpp:480](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:480)). The shared outer gate calls a width-dispatched function; it does not guarantee that every width performs both stages ([cutlass_preprocessors.cpp:507](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:507), [cutlass_preprocessors.cpp:685](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:685)).

The cross-check encodes the false assumption that `bias` and `cvtword` always coexist ([test_layouts.py:63](/root/marlin_ppu/quactlize/tests/test_layouts.py:63)). It checks one description against another, not against the implementation.

The named Torch op cannot currently reach int2 at all: its scalar-type conversion recognizes only int8 and packed int4 ([weight_preprocess_ops.cpp:30](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:30)). So this is simultaneously a false registry entry and a dead advertised layout.

Three additional unchecked paths can silently mislabel output:

1. **Source layout is assumed, not validated.** The API accepts only a destination name. Passing an already-preprocessed tensor through `preprocess_weights_to_layout` again passes width and shape checks, then re-applies every transform and bias ([weight_preprocess_ops.cpp:119](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:119), [cutlass_preprocessors.cpp:656](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:656)). The resulting bytes are not the named layout. A checked transform needs both `source_layout` and `destination_layout`, with `logical` explicit.

2. **The named steps are conditionally selected from separate compile traits.** `mmarow`, `tr`, and `clN` run only if `uses_imma_ldsm`, `layoutB`, and `columns_interleaved` say so ([cutlass_preprocessors.cpp:645](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_kernels/cutlass_preprocessors.cpp:645)). `LayoutPlan` contains none of those expectations—only two booleans, width, and AIU multiple ([weight_layout.h:19](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/weight_layout.h:19)). A trait change can silently skip or alter a named step. The trait header itself admits that the mapping is NVIDIA-derived, PPU-unverified, and that the existing comparison is structurally blind to a wrong first interleave ([mixed_gemm_B_layout.h:12](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/cutlass_extensions/gemm/kernel/mixed_gemm_B_layout.h:12)).

3. **The name does not actually travel with the tensor.** The op returns a raw `Tensor`; it neither attaches nor returns the canonical `plan.name` ([weight_preprocess_ops.cpp:148](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/thop/weight_preprocess_ops.cpp:148)). It also accepts aliases in C++ resolution ([weight_layout.h:74](/root/marlin_ppu/quactlize/quactlize/csrc/preprocess/weight_layout.h:74)). A caller can serialize the alias, discard the name entirely, or relabel arbitrary bytes. None of the compatibility machinery is load-bearing until the artifact carries a canonical ID and the consumer checks it.
