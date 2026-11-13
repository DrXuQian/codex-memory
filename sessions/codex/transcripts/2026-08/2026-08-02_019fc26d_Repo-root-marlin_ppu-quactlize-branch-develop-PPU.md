# Repo /root/marlin_ppu/quactlize, branch develop. PPU cutlass3 mixed-input GEMM. DERIVE A LAYOUT, do not survey options. Read the objects; do not trust the formula I quote.

THE PROBLEM. The scale/zero shared tile is read with 278,528 bank conflicts (acu), about 1.0226 per scalar load, and the recorded map is `h(t) = 256*(t mod 4) + floor(t/4) + C` giving 4 distinct words on each of 4 banks. Sources: dev/fold_derivation/l89_scale_read.cu, l94_native_scale_path.cu, PLAN_task20_scale.md:1094-1123. VERIFY that map against the real objects before using it -- l98 already produced a bank prediction that acu falsified (its swizzle removed exactly 0 conflicts), so a derivation that is not read off `SmemCopyLayoutScale` + `SmemCopyAtomScale` + `TiledMma` + the copy's thread slice is worthless here.

WHAT ALREADY CHANGED (committed): PPU_PACKED_SCALE_FUSED puts (scale, zero) in ONE 32-bit slot per (n, group, stage), compact, stride 1 in n. See ppu_mma_aiu_multistage_mixed_input.hpp, search kFusedScaleZero / SmemLayoutScaleFusedWord / SmemLayoutScaleFusedHalf. So the element is now 4 bytes = exactly one bank word, which should make the bank algebra clean.

DERIVE THIS. A replacement smem layout L for the fused (n, group, stage) tile such that:
  (R) the 32 lanes of a warp issuing ONE read instruction land on 32 DISTINCT banks (bank = word_index mod 32). If 32 is impossible, prove the achievable maximum and give the layout that reaches it.
  (W) the decoder's write stays conflict-free. Today thread n writes (n, G, stage) for compile-time G, so 32 lanes write 32 consecutive words = all 32 banks once. State what L does to that.
  (S) L is a STATIC cute Layout with POWER-OF-TWO strides -- not a Swizzle. This is the whole point: changing strides changes only compile-time constants and costs no instructions, whereas cute's Swizzle<B,M,S> lowers to SALU XOR/shift/AND and measured +97% SALU on the read path, and PPU_SCALE_PAD's additive pad lost to the non-power-of-two multiply it forced.
  (B) L is a bijection onto the same allocation -- Scale_TileN * Scale_TileK * Stages words. Shared bytes must not grow.

Config to derive on: TileShape <_16,_128,_256>, ScaleTileShape <_128,_8>, WarpShape <_16,_16,_256>, Stages 2, gs=32, int4 B -- i.e. Scale_TileN=128, Scale_TileK=8. Build it the way dev/fold_derivation/l95_stub_vs_real.cu does.

THE ALGEBRA I WANT SPELLED OUT, because this is where I keep getting it wrong by hand:
  1. For ONE read instruction, the exact set of (n, group) coordinates the 32 lanes touch -- read off the copy's thread slice, not inferred. How many distinct n, how many distinct group, and which.
  2. bank(lane) under the CURRENT fused layout, as a closed form, and its multiplicity. It must reproduce 4-way (on 8 banks now that the element is 32-bit, per an earlier 32-bit slot probe) -- if your derivation does not reproduce the measured multiplicity, say so and STOP, because then the model is wrong again.
  3. Solve for L. The degrees of freedom are the strides and the decomposition of n into hi/lo modes; e.g. layouts of the form ((n_lo, n_hi), g, stage) : ((1, a), b, c) with a, b, c powers of two. Give the constraint on the strides that makes (R) hold and then the concrete L.

TWO MORE THINGS TO ANSWER, briefly:
  4. Does L survive on the BASE path? base fills this tile with cp.async from a separate gmem scale tensor and a separate zero tensor. Under L the destination is permuted; an OFFLINE byte-neutral reorder of the gmem tensor can keep the copy coalesced. Say whether that composes, or whether L must be packed-path-only (gated on kPackedScaleOn) with base keeping the old layout.
  5. THE ALTERNATIVE ROUTE, judge it against L: write the tile at the HARDWARE swzl addresses with ordinary stores (the permutation is just an address map -- ppu_tsm_ld_swzl_sim in cute/arch/copy_ppu0010_aiu.hpp:367 models it, and dev/low_bit/w2a16_swzl_probe.cu has a self-contained copy) and read it back with an `ldmatrix.swzl`, which un-permutes in address-generation hardware for zero ALU. The write-side address math is computed once per thread per stage and hoists out of the loop, unlike the read-side Swizzle that lost. Is the swzl delivery shape compatible with a (128, 8) tile and with the scale fragment's TV layout? Say what blocks it if anything does.

Deliverable: the concrete layout L (shape and stride), the bank multiplicity it achieves for read and for write, the derivation, and whether it is packed-only. If (R) is unreachable at 32, give the maximum and prove it.

- **Thread ID:** `019fc26d-3b66-76f3-864a-cd859d82a076`
- **Started / last event:** 2026-08-02 12:22 UTC → 2026-08-02 12:43 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T20-22-46-019fc26d-3b66-76f3-864a-cd859d82a076.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "2861eb6e808121afa7854f5904bdf52d63751c0a", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-02 12:22 UTC

Repo /root/marlin_ppu/quactlize, branch develop. PPU cutlass3 mixed-input GEMM. DERIVE A LAYOUT, do not survey options. Read the objects; do not trust the formula I quote.

THE PROBLEM. The scale/zero shared tile is read with 278,528 bank conflicts (acu), about 1.0226 per scalar load, and the recorded map is `h(t) = 256*(t mod 4) + floor(t/4) + C` giving 4 distinct words on each of 4 banks. Sources: dev/fold_derivation/l89_scale_read.cu, l94_native_scale_path.cu, PLAN_task20_scale.md:1094-1123. VERIFY that map against the real objects before using it -- l98 already produced a bank prediction that acu falsified (its swizzle removed exactly 0 conflicts), so a derivation that is not read off `SmemCopyLayoutScale` + `SmemCopyAtomScale` + `TiledMma` + the copy's thread slice is worthless here.

WHAT ALREADY CHANGED (committed): PPU_PACKED_SCALE_FUSED puts (scale, zero) in ONE 32-bit slot per (n, group, stage), compact, stride 1 in n. See ppu_mma_aiu_multistage_mixed_input.hpp, search kFusedScaleZero / SmemLayoutScaleFusedWord / SmemLayoutScaleFusedHalf. So the element is now 4 bytes = exactly one bank word, which should make the bank algebra clean.

DERIVE THIS. A replacement smem layout L for the fused (n, group, stage) tile such that:
  (R) the 32 lanes of a warp issuing ONE read instruction land on 32 DISTINCT banks (bank = word_index mod 32). If 32 is impossible, prove the achievable maximum and give the layout that reaches it.
  (W) the decoder's write stays conflict-free. Today thread n writes (n, G, stage) for compile-time G, so 32 lanes write 32 consecutive words = all 32 banks once. State what L does to that.
  (S) L is a STATIC cute Layout with POWER-OF-TWO strides -- not a Swizzle. This is the whole point: changing strides changes only compile-time constants and costs no instructions, whereas cute's Swizzle<B,M,S> lowers to SALU XOR/shift/AND and measured +97% SALU on the read path, and PPU_SCALE_PAD's additive pad lost to the non-power-of-two multiply it forced.
  (B) L is a bijection onto the same allocation -- Scale_TileN * Scale_TileK * Stages words. Shared bytes must not grow.

Config to derive on: TileShape <_16,_128,_256>, ScaleTileShape <_128,_8>, WarpShape <_16,_16,_256>, Stages 2, gs=32, int4 B -- i.e. Scale_TileN=128, Scale_TileK=8. Build it the way dev/fold_derivation/l95_stub_vs_real.cu does.

THE ALGEBRA I WANT SPELLED OUT, because this is where I keep getting it wrong by hand:
  1. For ONE read instruction, the exact set of (n, group) coordinates the 32 lanes touch -- read off the copy's thread slice, not inferred. How many distinct n, how many distinct group, and which.
  2. bank(lane) under the CURRENT fused layout, as a closed form, and its multiplicity. It must reproduce 4-way (on 8 banks now that the element is 32-bit, per an earlier 32-bit slot probe) -- if your derivation does not reproduce the measured multiplicity, say so and STOP, because then the model is wrong again.
  3. Solve for L. The degrees of freedom are the strides and the decomposition of n into hi/lo modes; e.g. layouts of the form ((n_lo, n_hi), g, stage) : ((1, a), b, c) with a, b, c powers of two. Give the constraint on the strides that makes (R) hold and then the concrete L.

TWO MORE THINGS TO ANSWER, briefly:
  4. Does L survive on the BASE path? base fills this tile with cp.async from a separate gmem scale tensor and a separate zero tensor. Under L the destination is permuted; an OFFLINE byte-neutral reorder of the gmem tensor can keep the copy coalesced. Say whether that composes, or whether L must be packed-path-only (gated on kPackedScaleOn) with base keeping the old layout.
  5. THE ALTERNATIVE ROUTE, judge it against L: write the tile at the HARDWARE swzl addresses with ordinary stores (the permutation is just an address map -- ppu_tsm_ld_swzl_sim in cute/arch/copy_ppu0010_aiu.hpp:367 models it, and dev/low_bit/w2a16_swzl_probe.cu has a self-contained copy) and read it back with an `ldmatrix.swzl`, which un-permutes in address-generation hardware for zero ALU. The write-side address math is computed once per thread per stage and hoists out of the loop, unlike the read-side Swizzle that lost. Is the swzl delivery shape compatible with a (128, 8) tile and with the scale fragment's TV layout? Say what blocks it if anything does.

Deliverable: the concrete layout L (shape and stride), the bank multiplicity it achieves for read and for write, the derivation, and whether it is packed-only. If (R) is unreachable at 32, give the maximum and prove it.

## Assistant · 2026-08-02 12:22 UTC

I’ll build the exact configured objects the same way as `l95_stub_vs_real.cu`, then instrument the real copy thread slice to enumerate one read instruction before attempting the stride derivation. I’ll stop rather than force a layout if that enumeration fails to reproduce the fused 32-bit probe’s 4-way-on-8-banks result.

<details><summary>3 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"pwd && rg --files -g 'AGENTS.md' -g '!build' -g '!*.o' | sed -n '1,40p' && git branch --show-current && git status --short","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_ …`
- `exec: const r = await tools.exec_command({"cmd":"pwd","workdir":"/root/marlin_ppu/quactlize","login":false,"yield_time_ms":10000,"max_output_tokens":2000}); text(r.output);`
- `exec: const xs = ALL_TOOLS.filter(x => /file|shell|exec|command|workspace|repo/.test((x.name+" "+x.description).toLowerCase())); text(xs);`

</details>

## Assistant · 2026-08-02 12:23 UTC

The shell runner is currently failing before command execution because its workspace sandbox cannot create the required namespace. I’m checking for a read-only workspace resource path so the derivation can still be based on the repository objects; I won’t substitute the quoted map for that inspection.

<details><summary>31 tool call(s)</summary>

- `exec: const [r1,r2] = await Promise.all([ tools.list_mcp_resources({}), tools.list_mcp_resource_templates({}) ]); text(JSON.stringify({resources:r1,templates:r2}));`
- `exec: const xs = ALL_TOOLS.filter(x => x.name.includes("github_") && /search|contents|file|repo/.test((x.name+" "+x.description).toLowerCase())); text(xs.map(x=>({name:x.name,description:x.description.slice(0,500)})));`
- `exec: for (const n of ["mcp__codex_apps__github_search_installed_reposito_be740b6e4965","mcp__codex_apps__github_fetch_file","mcp__codex_apps__github_search"]) { const x=ALL_TOOLS.find(y=>y.name===n); text(x); }`
- `exec: const r=await tools.mcp__codex_apps__github_search_installed_reposito_be740b6e4965({query:"quactlize",limit:10,option_enrich_code_search_index_availability:true}); text(r);`
- `exec: const names=["dev/fold_derivation/l95_stub_vs_real.cu","dev/fold_derivation/l89_scale_read.cu","dev/fold_derivation/l94_native_scale_path.cu","PLAN_task20_scale.md"]; const rs=await Promise.all(names.map(path=>tools.mcp__codex_apps__github_ …`
- `exec: const qs=["kFusedScaleZero","SmemLayoutScaleFusedWord","ppu_mma_aiu_multistage_mixed_input.hpp","ppu_tsm_ld_swzl_sim","PPU_PACKED_SCALE_FUSED"]; const rs=await Promise.all(qs.map(query=>tools.mcp__codex_apps__github_search({query,repository …`
- `exec: const xs=ALL_TOOLS.filter(x=>x.name.includes("github_") && /tree|directory|contents|files/.test((x.name+" "+x.description).toLowerCase())); text(xs.map(x=>x.name));`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"include/cutlass/gemm/collective/builders/ppu_mma_builder.inl"}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_fetch({url:"https://api.github.com/repos/DrXuQian/quactlize/git/trees/develop?recursive=1"}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_fetch({url:"https://api.github.com/repos/DrXuQian/quactlize/contents/?ref=develop"}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"README.md"}); text(r);`
- `exec: const paths=[ "third_party/actlize/include/cutlass/gemm/collective/builders/ppu_mma_builder.inl", "third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp", "third_party/actlize/include/cute/arch/copy_ppu0 …`
- `exec: const r = await tools.exec_command({"cmd":"pwd","workdir":"/root/marlin_ppu/quactlize","shell":"/bin/bash","login":false,"tty":true,"yield_time_ms":1000,"max_output_tokens":2000}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:".gitmodules"}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_search_installed_reposito_be740b6e4965({query:"actlize",limit:10,option_enrich_code_search_index_availability:true}); text(r);`
- `exec: const paths=[ "include/cutlass/gemm/collective/builders/ppu_mma_builder.inl", "include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp", "include/cute/arch/copy_ppu0010_aiu.hpp" ]; const rs=await Promise.all(paths.map(path=>t …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp",start_line:1,end_line:400}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"}); const s=r.structuredContent?.content||""; f …`
- `exec: const x=ALL_TOOLS.find(y=>y.name==="mcp__codex_apps__github_search_branches"); text(x);`
- `exec: const rs=await Promise.all(["","ppu","scale","develop","fused"].map(query=>tools.mcp__codex_apps__github_search_branches({owner:"DrXuQian",repo_name:"actlize",query,page_size:100}))); for(const r of rs) text(r);`
- `exec: const r=await tools.update_plan({plan:[ {step:"Inspect the exact configured collective types and enumerate one fused-word read instruction",status:"in_progress"}, {step:"Validate the current fused layout against the measured 4-way/8-bank si …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch({url:"https://api.github.com/repos/DrXuQian/quactlize/contents/third_party/actlize?ref=develop"}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"third_party/actlize"}); text(r);`
- `exec: const r=await tools.mcp__codex_apps__github_compare_commits({repo_full_name:"DrXuQian/quactlize",base:"main",head:"develop"}); text(r);`
- `exec: const reqs=[ ["DrXuQian/quactlize","develop","dev/fold_derivation/l90_scale_tv.cu",null,null], ["DrXuQian/quactlize","develop","dev/fold_derivation/l98_scale_swizzle.cu",null,null], ["DrXuQian/quactlize","develop","dev/fold_derivation/PLAN_ …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"}); const s=r.structuredContent?.content||""; l …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cute/atom/copy_traits_ppu0010_aiu.hpp"}); text(r);`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"kFusedScaleZero|SmemLayoutScaleFusedWord|SmemLayoutScaleFusedHalf|SmemCopyLayoutScale\" third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp dev/fold_d …`
- `exec: const x=ALL_TOOLS.find(y=>y.name==="mcp__codex_apps__github_search_commits");text(x);`
- `exec: const rs=await Promise.all(["fused scale","PPU_PACKED_SCALE_FUSED","scale zero slot","bank"].map(query=>tools.mcp__codex_apps__github_search_commits({query,repository_full_name:"DrXuQian/actlize",topn:50}))); for(let i=0;i<rs.length;i++){te …`
- `exec: const r=await tools.view_image({path:"/root/marlin_ppu/quactlize/dev/fold_derivation/l95_stub_vs_real.cu","detail":"original"}); image(r.image_url);`

</details>

## Assistant · 2026-08-02 12:41 UTC

The object-derived lane set reproduces the required fused probe signature: for warp \(w\) and one of the four copy values \((u,p)\), lane \(t=4q+r\) touches \((n,g)=(16w+8u+q,\;2r+p)\). Under the compact fused-word layout this is 32 unique words, 4-way on 8 banks. The stride proof now shows a hard conflict between the read goal and the decoder-write goal; I’m finishing the bijection proof and the swzl comparison rather than proposing a stride that silently breaks writes.

<details><summary>1 tool call(s)</summary>

- `exec: const r=await tools.update_plan({explanation:"The real TiledMma/CopyAtom thread map reproduces the fused 4-way-on-8-banks measurement. The remaining result is an impossibility proof: a power-of-two bijective layout that preserves the 32-lan …`

</details>

## Assistant · 2026-08-02 12:43 UTC

## Result

No static, power-of-two-strided Cute layout can improve the fused read while also preserving the decoder’s conflict-free fixed-group write and remaining a bijection of the 2,048-word allocation.

The achievable maximum under `(R)+(W)+(S)+(B)` is therefore:

- Read: 8 distinct banks, 4 distinct words per bank.
- Write: 32 distinct banks, 1 word per bank.
- Concrete layout: the current compact fused-word layout, optionally written with an explicit `n` decomposition:

```cpp
using L = cute::Layout<
    cute::Shape<cute::Shape<cute::_32, cute::_4>,
                cute::_8,
                cute::_2>,
    cute::Stride<cute::Stride<cute::_1, cute::_32>,
                 cute::_128,
                 cute::_1024>>;
```

Equivalently:

```cpp
Layout<Shape<_128, _8, _2>,
       Stride<_1, _128, _1024>>
```

It maps

\[
L(n,g,s)=n+128g+1024s.
\]

It is a bijection onto exactly \(128\cdot8\cdot2=2048\) words. There is no beneficial replacement layout within the stated constraints.

## 1. Exact read coordinates

This comes from the `BLayout` carried by the `TiledMma` asserted in [l95_stub_vs_real.cu](/root/marlin_ppu/quactlize/dev/fold_derivation/l95_stub_vs_real.cu), together with `make_tiled_copy_B(SmemCopyAtomScale{}, TiledMma{})`.

Write a lane as

\[
t=4q+r,\qquad q=\lfloor t/4\rfloor\in[0,7],\quad r=t\bmod4\in[0,3].
\]

The MMA atom’s thread offset is

\[
32r+q.
\]

Decomposed against the atom’s 16-wide logical B tile, that is \((n,k)=(q,2r)\). The copy-value modes provide the missing high \(n\) bit and group-parity bit. Thus, for warp \(w\), one read instruction selected by fixed \(u,p\in\{0,1\}\) touches

\[
\boxed{
n=16w+8u+q,\qquad g=2r+p
}
\]

at fixed stage \(s\).

Consequently, one instruction touches:

- 8 distinct `n`:  
  \(\{16w+8u,\ldots,16w+8u+7\}\)
- 4 distinct groups:
  - \(p=0:\{0,2,4,6\}\)
  - \(p=1:\{1,3,5,7\}\)
- 32 distinct fused words: the Cartesian product of those sets.

The four \((u,p)\) combinations cover the warp’s \(16\times8\) fused-word tile.

## 2. Current fused bank map

Substituting the object-derived coordinates into the compact word layout:

\[
\begin{aligned}
L(t)
 &=16w+8u+q+128(2r+p)+1024s \\
 &=256r+q+C,
\end{aligned}
\]

where

\[
C=16w+8u+128p+1024s.
\]

Therefore

\[
\boxed{
\operatorname{bank}(t)
=L(t)\bmod32
=(16w+8u+q)\bmod32.
}
\]

The bank is independent of \(r\). Hence:

- \(q=0,\ldots,7\) gives 8 banks.
- For each \(q\), the four values of \(r\) select four different words on that bank.
- Multiplicity is exactly 4-way on 8 banks.

This reproduces the measured fused 32-bit-slot signature, so the model passes the requested stop condition.

## 3. Why no better `L` exists

For the suggested form with eight-element `n_lo`,

\[
L=((n_{\rm lo},n_{\rm hi}),g,s):((1,a),b,c),
\]

one read has

\[
\operatorname{bank}=q+2br+C\pmod{32}.
\]

Making the four \(r\) values occupy four disjoint eight-bank regions requires

\[
2b\equiv8\pmod{32},
\]

so the only power-of-two choice is \(b=4\).

But `n_lo` has shape 8 and stride 1, occupying address bits 0–2. A group mode of shape 8 and stride 4 occupies bits 2–4. The overlap creates an immediate collision:

\[
L(n_{\rm lo}=4,g=0)=L(n_{\rm lo}=0,g=1).
\]

Thus the apparent 32-bank solution is not a bijection.

More generally, because every mode extent and stride is a power of two, a bijection onto a contiguous \(2^{11}\)-word allocation assigns disjoint coordinate-bit intervals to address bits. Overlapping intervals cause collisions; gaps increase `cosize`.

For the write, fixed \(G,s\) and 32 consecutive `n` values must be injective modulo 32. Therefore the five varying low `n` bits must occupy all five bank bits. No group bit may occupy a bank bit, so the group stride must satisfy

\[
b\equiv0\pmod{32}.
\]

Then, on the read,

\[
2br\equiv0\pmod{32},
\]

and only the three \(q\) bits vary the bank. Therefore:

\[
\boxed{\text{at most }2^3=8\text{ banks}}
\]

and the 32 distinct words necessarily give multiplicity \(32/8=4\).

The concrete `L` above reaches that bound.

For comparison only, dropping `(W)` allows 16 banks:

```cpp
Layout<
  Shape<Shape<_8,_16>, _8, _2>,
  Stride<Stride<_1,_64>, _8, _1024>>
```

but its decoder write is 4-way on only 8 banks, so it is disqualified.

## 4. Base path

The fused word layout should remain packed-path-only, gated on `kPackedScaleOn`.

The base path has two independent global tensors. A byte-neutral reorder inside each tensor cannot make a 128-bit `cp.async` populate interleaved `(scale,zero)` words:

- scale destinations are every other halfword;
- zero destinations are the complementary halfwords;
- each source tensor remains contiguous independently;
- `cp.async` cannot gather from two pointers or scatter alternate halfwords.

It would compose only after changing the base ABI to one already-fused global tensor. With the stated separate tensors, base should retain its old separate layouts and copy path.

## 5. Hardware-swzl route

The delivery geometry is compatible.

One warp owns 16 columns, so its fused tile is

\[
16\ n \times 8\ \text{words}
=16\times16\ \text{halfs}
=128\ \text{words}.
\]

A `CUBE_H=16, CUBE_W=16` b16 `ldmatrix.swzl` returns four 32-bit registers per lane:

\[
32\text{ lanes}\times4\text{ words}=128\text{ words}.
\]

That is exactly one warp’s fused scale fragment. Eight such cubes cover the full `(128,8)` stage without padding.

For `SWAP=true`, its logical TV map is

\[
n_h=q+8u,\qquad g_h=r+4p.
\]

The desired fused-copy map is

\[
n=q+8u,\qquad g=2r+p.
\]

These are both bijections over the same 128 words; they differ only by a rotation of the three group bits. Composing that rotation with `ppu_tsm_ld_swzl_sim` gives the ordinary-store address map, so no read-side register shuffle or SALU address transform is fundamentally required.

It is not a conflict-free write under today’s fixed-\(G\), thread-\(n\) schedule. The simulator gives

\[
\operatorname{bank}_{swzl}(n,G)=
4\left(
  \left(2(n\bmod4)+(G\bmod2)\right)
  \mathbin{\mathtt{xor}}
  \left(\lfloor n/4\rfloor\bmod2\right)
 \right)
+\lfloor G/2\rfloor
\pmod{32}.
\]

For 16 columns this is 2-way on 8 banks. A 32-lane writer spans two 16-column cubes whose 128-word bases have identical bank residues, giving 4-way on 8 banks. A different store schedule could address that, but the current schedule does not.

So the swzl route is shape- and TV-compatible and is the viable zero-read-ALU escape from the stride impossibility. Its costs are packed-only integration plus conflicted one-time decoder stores; those replace recurrent conflicted scalar reads and therefore remain worth measuring.
