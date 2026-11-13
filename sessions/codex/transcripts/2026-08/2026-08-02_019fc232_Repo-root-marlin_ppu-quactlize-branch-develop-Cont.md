# Repo: /root/marlin_ppu/quactlize (branch develop). Context: PPU (T-Head ZW810) cutlass3 mixed-input GEMM, Q4_K native packed scale. Attack my reading of a new acu capture — I want to be told where it is wrong, not confirmed.

VARIANTS (benchmarks/run_batch.sh:36-46). base = `SK_QUANT=2`. swz = `SK_QUANT=2 PPU_SCALE_SWIZZLE=1` (NOTE: no PPU_PACKED_SCALE — swz is the fp16-plane baseline plus the scale-tile swizzle). pack = `SK_QUANT=2 PPU_PACKED_SCALE=1`.

PREVIOUSLY MEASURED (20-block ABBA, paired log ratios, 95% CI, vs base): pack +13.1% (1.111..1.150), packnop +9.2%, pack/packnop +3.5%, swz +7.0% (1.053..1.087).
PREVIOUSLY CAPTURED counters: base Shared Load bank conflicts 278,528 and pack 278,528 (identical); base Shared Store BC 8,192, pack 81,920.

NEW acu capture, Current = swz, Baseline = pack, same launch shape (8,16,1)x(256,1,1), config "16x128:256 w16x16 s2" (Stages=2). Percentages are (current-baseline)/baseline.
  Shared Load:  Inst 441,344 (-1.03%)  Req 441,344 (-1.03%)  Trans 1,908,736 (-1.89%)  %Peak 18.52 (+4.47%)  BankConflicts 278,528 (+0.00%)
  Shared Store: Inst 12,800 (-84.85%)  Trans 50,176 (-72.32%)  %Peak 0.48 (-70.09%)  BankConflicts 8,192 (-90.00%)
  Shared Store From Global Load: Inst 24,192 (+61.54%)  Trans 589,824 (+14.29%)  %Peak 5.65 (+20.68%)  BC 0
  Total: Inst 478,336 (-12.30%)  Trans 2,548,736 (-3.56%)  %Peak 24.65 (+2.64%)  BC 286,720 (-20.45%)
  Time: swz 21.52 us / 36,576 cycles / 104 regs;  pack 22.54 us / 38,323 cycles / 98 regs.
  Compute (swz %peak, delta vs pack): WS Issue Active 46.00 (+19.08%); PU Pipe SALU Cycles Active 38.74 (+50.66%); Inst Executed Pipe SALU 18.70 (+97.47%); WE Pipe Tensor Cycles Active 14.04 (+6.25%); Inst Executed 13.93 (+22.64%); WE Pipe IALU 13.69 (+0.21%); WE Pipe FALU 12.82 (+8.50%); Inst Executed Pipe FALU FP16 10.89 (-4.44%); PU Pipe SLS 9.89 (+9.44%); Inst Executed Pipe LSU 4.85 (-7.73%).
  Memory: DRAM Throughput 35.34 (+16.38%); LLC Trans Load Pipe Fabric 14.38 (+15.95%); L2 Fabric2L2 Read 12.89 (+19.57%); AIU Transactions Load 4.66 (+23.31%).

MY READING, please attack each point:
(1) swz Shared Load BC = 278,528 = pack = base. So the swizzle removed ZERO load bank conflicts. Since 278,528 is invariant under BOTH swizzling the scale tile AND replacing the fp16 scale/zero planes with a packed unit + decode, it cannot be the scale read at all — l98 (the static probe that said "4-way on 4 banks -> Swizzle<2,3,5> gives 1-way on 16 banks", collective header lines 448-470) modelled an access that is not what generates these conflicts. This is pre-registered outcome (a) from dev/fold_derivation/TODO.md.
(2) swz Shared Store BC = 8,192 = base's. So the swizzle removed zero store conflicts too.
(3) Converting %peak to absolute using the cycle counts: Inst Executed 13.93*36576 vs (13.93/1.2264)*38323 = +17.0% absolute instructions; SALU 18.70*36576 vs (18.70/1.9747)*38323 = +88% absolute SALU instructions — swz issues ~1.9x pack's SALU while being the SIMPLER path (no decoder). SALU pipe at 38.74% is now the busiest compute pipe (Tensor is 14.04%). So the swizzle's XOR address math is the cost, and it bought nothing => complete explanation of the +7.0%, and PPU_SCALE_SWIZZLE should be abandoned.
(4) Consequence for the planned half2 scale/zero plane merge: it cannot touch load conflicts either (those are not in the scale tile). Its only attributable conflict target is the STORE side — pack's +73,728 store conflicts, of which the merge removes about half (36,864) by halving the publications. Plus channel count.
(5) Consistency: swz 21.52 vs pack 22.54 = -4.5%, and the ABBA ratios predict swz/pack = 1.070/1.131 = -5.4%. Same direction, close magnitude, so the acu run is not an outlier.

Specific things to check and push back on: is the %peak -> absolute conversion legitimate for this tool (does "% Peak" for Inst Executed normalise by cycles)? Could the swizzle instead be inert (kScaleSwizzleOk false for Stages=2 / this shape) with the SALU rise having another source — check the gate at collective lines 477-497 for this config? Is there any way 278,528 could still BE the scale read despite invariance (e.g. the counter attributing conflicts to tsm.ld.swzl of A/B, or the swizzle only permuting within a conflict class so 4-way stays 4-way)? Read the actual code. Be concrete and cite file:line.

- **Thread ID:** `019fc232-8b21-7d81-8f1b-ed3e9092d7c5`
- **Started / last event:** 2026-08-02 11:18 UTC → 2026-08-02 11:33 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T19-18-40-019fc232-8b21-7d81-8f1b-ed3e9092d7c5.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "693a976f9755bf8655efeef85fdb2b21577ec2c8", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-02 11:18 UTC

Repo: /root/marlin_ppu/quactlize (branch develop). Context: PPU (T-Head ZW810) cutlass3 mixed-input GEMM, Q4_K native packed scale. Attack my reading of a new acu capture — I want to be told where it is wrong, not confirmed.

VARIANTS (benchmarks/run_batch.sh:36-46). base = `SK_QUANT=2`. swz = `SK_QUANT=2 PPU_SCALE_SWIZZLE=1` (NOTE: no PPU_PACKED_SCALE — swz is the fp16-plane baseline plus the scale-tile swizzle). pack = `SK_QUANT=2 PPU_PACKED_SCALE=1`.

PREVIOUSLY MEASURED (20-block ABBA, paired log ratios, 95% CI, vs base): pack +13.1% (1.111..1.150), packnop +9.2%, pack/packnop +3.5%, swz +7.0% (1.053..1.087).
PREVIOUSLY CAPTURED counters: base Shared Load bank conflicts 278,528 and pack 278,528 (identical); base Shared Store BC 8,192, pack 81,920.

NEW acu capture, Current = swz, Baseline = pack, same launch shape (8,16,1)x(256,1,1), config "16x128:256 w16x16 s2" (Stages=2). Percentages are (current-baseline)/baseline.
  Shared Load:  Inst 441,344 (-1.03%)  Req 441,344 (-1.03%)  Trans 1,908,736 (-1.89%)  %Peak 18.52 (+4.47%)  BankConflicts 278,528 (+0.00%)
  Shared Store: Inst 12,800 (-84.85%)  Trans 50,176 (-72.32%)  %Peak 0.48 (-70.09%)  BankConflicts 8,192 (-90.00%)
  Shared Store From Global Load: Inst 24,192 (+61.54%)  Trans 589,824 (+14.29%)  %Peak 5.65 (+20.68%)  BC 0
  Total: Inst 478,336 (-12.30%)  Trans 2,548,736 (-3.56%)  %Peak 24.65 (+2.64%)  BC 286,720 (-20.45%)
  Time: swz 21.52 us / 36,576 cycles / 104 regs;  pack 22.54 us / 38,323 cycles / 98 regs.
  Compute (swz %peak, delta vs pack): WS Issue Active 46.00 (+19.08%); PU Pipe SALU Cycles Active 38.74 (+50.66%); Inst Executed Pipe SALU 18.70 (+97.47%); WE Pipe Tensor Cycles Active 14.04 (+6.25%); Inst Executed 13.93 (+22.64%); WE Pipe IALU 13.69 (+0.21%); WE Pipe FALU 12.82 (+8.50%); Inst Executed Pipe FALU FP16 10.89 (-4.44%); PU Pipe SLS 9.89 (+9.44%); Inst Executed Pipe LSU 4.85 (-7.73%).
  Memory: DRAM Throughput 35.34 (+16.38%); LLC Trans Load Pipe Fabric 14.38 (+15.95%); L2 Fabric2L2 Read 12.89 (+19.57%); AIU Transactions Load 4.66 (+23.31%).

MY READING, please attack each point:
(1) swz Shared Load BC = 278,528 = pack = base. So the swizzle removed ZERO load bank conflicts. Since 278,528 is invariant under BOTH swizzling the scale tile AND replacing the fp16 scale/zero planes with a packed unit + decode, it cannot be the scale read at all — l98 (the static probe that said "4-way on 4 banks -> Swizzle<2,3,5> gives 1-way on 16 banks", collective header lines 448-470) modelled an access that is not what generates these conflicts. This is pre-registered outcome (a) from dev/fold_derivation/TODO.md.
(2) swz Shared Store BC = 8,192 = base's. So the swizzle removed zero store conflicts too.
(3) Converting %peak to absolute using the cycle counts: Inst Executed 13.93*36576 vs (13.93/1.2264)*38323 = +17.0% absolute instructions; SALU 18.70*36576 vs (18.70/1.9747)*38323 = +88% absolute SALU instructions — swz issues ~1.9x pack's SALU while being the SIMPLER path (no decoder). SALU pipe at 38.74% is now the busiest compute pipe (Tensor is 14.04%). So the swizzle's XOR address math is the cost, and it bought nothing => complete explanation of the +7.0%, and PPU_SCALE_SWIZZLE should be abandoned.
(4) Consequence for the planned half2 scale/zero plane merge: it cannot touch load conflicts either (those are not in the scale tile). Its only attributable conflict target is the STORE side — pack's +73,728 store conflicts, of which the merge removes about half (36,864) by halving the publications. Plus channel count.
(5) Consistency: swz 21.52 vs pack 22.54 = -4.5%, and the ABBA ratios predict swz/pack = 1.070/1.131 = -5.4%. Same direction, close magnitude, so the acu run is not an outlier.

Specific things to check and push back on: is the %peak -> absolute conversion legitimate for this tool (does "% Peak" for Inst Executed normalise by cycles)? Could the swizzle instead be inert (kScaleSwizzleOk false for Stages=2 / this shape) with the SALU rise having another source — check the gate at collective lines 477-497 for this config? Is there any way 278,528 could still BE the scale read despite invariance (e.g. the counter attributing conflicts to tsm.ld.swzl of A/B, or the swizzle only permuting within a conflict class so 4-way stays 4-way)? Read the actual code. Be concrete and cite file:line.

## Assistant · 2026-08-02 11:18 UTC

I’ll inspect the variant wiring, the collective’s swizzle gate and access code, the profiler field semantics if documented locally, and the pre-registered derivation. I’ll treat each inference as a hypothesis to falsify and cite exact lines.

<details><summary>1 tool call(s)</summary>

- `exec: const r = await tools.exec_command({cmd:"pwd && rg --files -g 'AGENTS.md' -g '!build' -g '!**/.git/**' | sed -n '1,80p' && rg -n \"PPU_SCALE_SWIZZLE|PPU_PACKED_SCALE|kScaleSwizzleOk|Shared Store From Global Load|Inst Executed|%Peak|% Peak|t …`

</details>

## Assistant · 2026-08-02 11:18 UTC

The shell’s default sandbox wrapper is unavailable on this host, so I’m switching to the workspace’s read-only inspection path; I won’t make repository changes.

<details><summary>29 tool call(s)</summary>

- `exec: const meta = ALL_TOOLS.filter(x => /file|read|search|workspace|shell|command/i.test(x.name+" "+x.description)); text(meta);`
- `exec: const r = await tools.exec_command({cmd:"pwd","workdir":"/root/marlin_ppu/quactlize","login":false,"shell":"/bin/bash","yield_time_ms":10000,"max_output_tokens":1000}); text(r);`
- `exec: const xs=ALL_TOOLS.filter(x=>x.name.includes("github") && /read|fetch|search|branch|commit|tree|content/i.test(x.name+" "+x.description)).map(x=>x.name+" :: "+x.description.slice(0,180)); xs.forEach(text);`
- `exec: for (const n of ["mcp__codex_apps__github_search_installed_repositories_v2","mcp__codex_apps__github_fetch_file","mcp__codex_apps__github_search"]) { const x=ALL_TOOLS.find(y=>y.name===n); text(x?x.description:"missing "+n); }`
- `exec: const r=await tools.mcp__codex_apps__github_search_installed_repositories_v2({query:"quactlize",limit:20,include_search_index_status:true}); text(JSON.stringify(r));`
- `exec: const names=["AGENTS.md","benchmarks/run_batch.sh","dev/fold_derivation/TODO.md"]; for (const p of names){const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:p,encoding:"utf-8 …`
- `exec: const qs=["kScaleSwizzleOk","PPU_SCALE_SWIZZLE","Swizzle<2,3,5>","scale_fragment_layout","PPU_PACKED_SCALE"]; for (const q of qs){const r=await tools.mcp__codex_apps__github_search({query:q,repository_name:"DrXuQian/quactlize",topn:20}); te …`
- `exec: const x=ALL_TOOLS.find(y=>y.name==="mcp__codex_apps__github_compare_commits"); text(x.description);`
- `exec: const r=await tools.mcp__codex_apps__github_compare_commits({repo_full_name:"DrXuQian/quactlize",base:"main",head:"develop"}); text(JSON.stringify(r));`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"dev/fold_derivation/TODO.md",encoding:"utf-8"}); const c=r.structuredContent?.content||""; const keys=["pre-register","pre …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"dev/fold_derivation/TODO.md",encoding:"utf-8",start_line:1,end_line:90}); text(JSON.stringify(r));`
- `exec: ALL_TOOLS.filter(x=>x.name.includes("github")).map(x=>x.name).forEach(text);`
- `exec: const docs=["dev/fold_derivation/TODO.md","dev/fold_derivation/PLAN_task20_scale.md","dev/fold_derivation/HANDOFF_packed_scale.md","dev/fold_derivation/README.md"]; for(const p of docs){ const r=await tools.mcp__codex_apps__github_fetch_fil …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"build.sh",encoding:"utf-8"}); const c=r.structuredContent?.content||"";const ls=c.split("\n");ls.forEach((s,i)=>{if(/moe_g …`
- `exec: const x=ALL_TOOLS.find(y=>y.name==="mcp__codex_apps__github_fetch"); text(x.description);`
- `exec: const urls=["https://api.github.com/repos/DrXuQian/quactlize/contents/quactlize/include?ref=develop","https://api.github.com/repos/DrXuQian/quactlize/contents?ref=develop"]; for(const u of urls){const r=await tools.mcp__codex_apps__github_f …`
- `exec: const docs=["dev/fold_derivation/TODO.md","dev/fold_derivation/PLAN_task20_scale.md","dev/fold_derivation/HANDOFF_packed_scale.md","dev/fold_derivation/README.md","dev/fold_derivation/HANDOFF_TASK12.md"]; for(const p of docs){ const r=await …`
- `exec: const paths=[ "quactlize/include/ppu_mma_aiu_mixed_input_2plane.hpp", "quactlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp", "quactlize/include/cutlass_extensions/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp", …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"quactlize/include/moe_grouped_ppu.cuh",encoding:"utf-8"}); const c=r.structuredContent?.content||"";c.split("\n").forEach( …`
- `exec: const paths=["quactlize/include/ppu_include.hpp","quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp","quactlize/include/fold_traits.hpp"]; for(const p of paths){const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:".gitmodules",encoding:"utf-8"}); text(JSON.stringify(r));`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"third_party/actlize",encoding:"utf-8"}); text(JSON.stringify(r));`
- `exec: const r=await tools.mcp__codex_apps__github_search_installed_repositories_v2({query:"actlize",limit:20,include_search_index_status:true}); text(JSON.stringify(r));`
- `exec: const paths=[ "include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input.hpp", "include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp", "include/cutlass/gemm/collective/builders/ppu_mma_builder.inl", "include/ppu_include.hpp" ];  …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp",encoding:"utf-8",start_line:420,end_line:560}); te …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp",encoding:"utf-8"}); const c=r.structuredContent?.c …`
- `exec: const [a,b]=await Promise.all([tools.list_mcp_resources({}),tools.list_mcp_resource_templates({})]); text(JSON.stringify(a)); text(JSON.stringify(b));`
- `exec: const x=ALL_TOOLS.find(y=>y.name==="mcp__codex_apps__github_search_branches"); text(x.description);`
- `exec: for(const q of ["ppu","scale","swizzle","w4a16"]){const r=await tools.mcp__codex_apps__github_search_branches({owner:"DrXuQian",repo_name:"actlize",query:q,page_size:100}); text(q+"\n"+JSON.stringify(r));}`

</details>

## Assistant · 2026-08-02 11:22 UTC

The checked-out collective appears newer than the public submodule branch—the public copy lacks the swizzle macro—so I’m separating what the cited local gate establishes from what the counters alone establish. The first important crack is already visible: unchanged aggregate conflicts do not prove the conflicted instruction stream is unchanged.

<details><summary>25 tool call(s)</summary>

- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"dev/fold_derivation/l98_scale_swizzle.cu",encoding:"utf-8"}); const c=r.structuredContent.content; c.split("\n").forEach(( …`
- `exec: const x=ALL_TOOLS.find(y=>y.name==="mcp__codex_apps__github_search_commits"); text(x.description);`
- `exec: for(const q of ["scale swizzle","PPU_SCALE_SWIZZLE","packed scale","native scale"]){const r=await tools.mcp__codex_apps__github_search_commits({query:q,repository_full_name:["DrXuQian/actlize","DrXuQian/quactlize"],topn:50}); text(q+"\n"+JS …`
- `exec: const r=await tools.mcp__codex_apps__github_search_commits({query:"",repository_full_name:"DrXuQian/actlize",sort:"committer-date",order:"desc",topn:30}); text(JSON.stringify(r));`
- `exec: const x=ALL_TOOLS.find(y=>y.name==="mcp__codex_apps__github_fetch_commit"); text(x.description);`
- `exec: const r=await tools.mcp__codex_apps__github_compare_commits({repo_full_name:"DrXuQian/actlize",base:"v1.0.0",head:"ppu-w4a16-dev"}); text(JSON.stringify(r));`
- `exec: const p="include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:p,encoding:"utf-8"}); const c=r.struc …`
- `exec: const p="include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"; for(const [a,b] of [[180,260],[420,510],[1170,1260],[1280,1320],[1370,1520],[1540,1610],[1700,1760]]){ const r=await tools.mcp__codex_apps__github_fetch_file( …`
- `exec: const p="include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:p,encoding:"utf-8"}); const ls=r.stru …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp",encoding:"utf-8",start_line:45,end_line:80});  …`
- `exec: const p="include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:p,encoding:"utf-8"}); const ls=r.stru …`
- `exec: const p="include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"; for(const [a,b] of [[1608,1705],[1790,1925],[900,980],[760,850],[1080,1170]]){ const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"D …`
- `exec: const files=["dev/fold_derivation/TODO.md","dev/fold_derivation/PLAN_task20_scale.md","dev/fold_derivation/README.md","dev/fold_derivation/acu_capture.sh"]; for(const p of files){const r=await tools.mcp__codex_apps__github_fetch_file({repos …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"dev/fold_derivation/PLAN_task20_scale.md",encoding:"utf-8",start_line:1080,end_line:1210}); text(r.structuredContent.conte …`
- `exec: const vals={ instr:1.2264*36576/38323, salu_inst:1.9747*36576/38323, salu_active:1.5066*36576/38323, issue:1.1908*36576/38323, tensor:1.0625*36576/38323, ialu:1.0021*36576/38323, falu:1.0850*36576/38323, falu_fp16:0.9556*36576/38323, sls:1. …`
- `exec: for(const q of ['"PU Pipe SALU Cycles Active"','"Inst Executed Pipe SALU"','"WS Issue Active" ACU','"Shared Store From Global Load"']){const r=await tools.mcp__codex_apps__github_search({query:q,topn:20});text(q+"\n"+JSON.stringify(r));}`
- `exec: const p="include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:p,encoding:"utf-8"}); const ls=r.stru …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp",encoding:"utf-8"}); const ls=r.structuredConte …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:"include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp",encoding:"utf-8"}); const ls=r.structuredConte …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"benchmarks/run_batch.sh",encoding:"utf-8"}); const ls=r.structuredContent.content.split("\n"); for(let i=28;i<=50;i++) tex …`
- `exec: const p="include/cutlass/gemm/collective/builders/ppu_mma_builder.inl"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:p,encoding:"utf-8"}); const ls=r.structuredCont …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"quactlize/include/moe_grouped_ppu.cuh",encoding:"utf-8"}); const ls=r.structuredContent.content.split("\n");for(let i=90;i …`
- `exec: const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:"quactlize/include/moe_grouped_ppu.cuh",encoding:"utf-8"}); const ls=r.structuredContent.content.split("\n");for(let i=125; …`
- `exec: const paths=["benchmarks/moe_splitk_bench_common.hpp","benchmarks/test_moe_splitk_bench.cu"]; for(const p of paths){const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/quactlize",ref:"develop",path:p,encod …`
- `exec: const p="include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp"; const r=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:"DrXuQian/actlize",ref:"ppu-w4a16-dev",path:p,encoding:"utf-8"}); const ls=r.stru …`

</details>

## Assistant · 2026-08-02 11:33 UTC

Bottom line: your deployment decision is defensible—leave `PPU_SCALE_SWIZZLE` off—but the causal story is not. Points (1), (3), and (4) overreach; (2) targets the wrong store stream; (5) is a useful sanity check, not an outlier test.

**(1) The swizzle failed to reduce measured load conflicts, but “therefore these are not scale reads” is wrong.**

The key mistake is treating `pack` as removing the scale/zero consumer reads. It does not. The packed decoder writes reconstructed fp16 values into the same `smem_scale` and `smem_zero` planes, and the read side is deliberately unchanged: [collective](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:574), [decoder stores](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1389), [FINE consumer loads](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1901).

So base = pack at 278,528 is exactly what the implementation predicts if those conflicts are scale reads.

The new pack deltas reinforce this:

- Pack has 4,608 additional shared loads and 36,864 additional transactions—the packed-unit decoder reads—with zero additional load conflicts.
- The old fp16-plane scale/zero consumer loads remain in both variants.

The previous `sz` versus `pc` controlled comparison is still the strongest attribution evidence: adding the FINE scale/zero channel added roughly 272k loads and 252k conflicts while leaving A/B structurally unchanged. That decomposition is recorded at [PLAN_task20_scale.md:1094](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1094). Therefore wholesale reassignment of 278,528 conflicts to A/B `tsm.ld.swzl` is inconsistent with the earlier ablation. A/B can explain the residual ~26k, not naturally the whole count.

What the swz invariance does establish is narrower: l98’s static bank model failed to predict the emitted/hardware behavior. It does not establish which stream owns the counter. The pre-registered dichotomy was itself incomplete: l98 models distinct addresses per bank in C++ layout space [l98_scale_swizzle.cu:58](/root/marlin_ppu/quactlize/dev/fold_derivation/l98_scale_swizzle.cu:58); it does not prove the PPU instruction lowering, broadcast behavior, bank-index function, or profiler event semantics.

Could 278,528 still be the scale reads? Yes—indeed, that remains the best-supported attribution. The likely correction is “the scale reads remain conflicted despite the logical swizzle,” not “the conflicts were never scale reads.”

The “permutation within the same conflict class” explanation contradicts l98 under its assumed bank function: it explicitly calculates 4-way to 1-way. It becomes possible only if the real instruction/access granularity or hardware bank mapping differs from that assumption.

**The swizzle is not inert for this configuration.**

For `TN=128`, the selected type is explicitly `Swizzle<2,3,5>` [collective:63](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:63). With `gs=32`, `TileK=256`, and Stages=2:

- `Scale_TileK = 8`
- `cosize = 128 × 8 × 2 = 2048`
- 128, 8, 2, and 2048 are powers of two
- the swz variant defines `PPU_SCALE_SWIZZLE=1` and no `PPU_SCALE_PAD`

Therefore every condition at [collective:477](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:477) is true, and the flattened consumer view also receives the swizzle at [collective:1561](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1561). This is not the Stages=3 vacuous case.

**(2) True numerically, but it is not a meaningful swizzle result.**

`swz` has no packed decoder. Its scale and zero publications are global-to-shared async copies [collective:1127](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1127), which ACU reports under “Shared Store From Global Load,” not ordinary “Shared Store.”

Pack’s extra 73,728 conflicts come from explicit 16-bit decoder stores to `sS` and `sZ`. Those instructions do not exist in either base or swz. Thus swz = base at 8,192 does not show the swizzle attempting and failing to fix store conflicts; it shows that both variants lack the conflicting decoder-store stream.

**(3) The arithmetic is conditionally correct; the attribution and “complete explanation” are not.**

If ACU’s `%Peak` metric is

\[
P \propto \frac{\text{instructions}}{\text{elapsed metric-domain cycles}},
\]

then your ratio algebra is correct:

- Total instructions: \(1.2264 \times 36576/38323 = 1.1705\), or +17.0%.
- SALU instructions: \(1.9747 \times 36576/38323 = 1.8847\), or +88.5%.

But those are not yet trustworthy raw counts. ACU’s `%Peak` is cycle-normalized in form, but the denominator need not be the headline kernel cycle count. Your own memory rows fail an exact reconstruction:

- Shared-load transaction ratio is 0.9811. Dividing by the kernel-cycle ratio 0.9544 predicts +2.79% throughput, not the reported +4.47%.
- G2S predicts +19.75%, versus reported +20.68%.

That suggests pipe-domain cycles, weighted transactions, or another internal denominator. So “about 1.9× SALU” is plausible—the delta is too large to disappear—but +88.5% should not be presented as an exact absolute counter result without ACU’s raw count or metric-domain cycle field.

More importantly, swz versus pack is not an XOR ablation. It simultaneously compares:

- two fp16 global-to-shared channels versus one packed channel;
- no decoder stores versus 16-bit decoder stores;
- no packed-unit reads versus 4,608 packed-unit reads;
- different vector/scalar arithmetic and register allocation.

The +61.54% G2S instruction count in swz is a concrete alternative source of scalar address and predicate work. Pack’s decoder arithmetic is also predominantly vector IALU/FALU, so “simpler source code” does not imply fewer SALU instructions.

You need swz versus base compute counters to price the XOR. The pre-registration also specifically asked for AND/shift/XOR opcode deltas and `s.wait`; neither is in the supplied capture [TODO.md:21](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:21).

Finally, 38.74% SALU pipe-active versus 14.04% tensor pipe-active does not establish that SALU is the bottleneck. They are different pipe domains and peak denominators; pipe activity is not a stall attribution. It is consistent with XOR/address cost, but not a complete explanation of the ABBA +7%.

Recommendation: abandon this swizzle implementation for now, yes. It is repeatedly slower and produces no measured memory-counter benefit. Just do not call its mechanism closed.

**(4) This consequence is wrong in both halves.**

The half2 merge absolutely can affect load conflicts because it changes the consumer layout and turns two plane reads into one 32-bit read. The current tree itself expects about 136,192 fewer shared loads and says the 32-bit probe remains 4-way but spreads over eight banks instead of four [TODO.md:31](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:31). Even if conflict degree per merged instruction remains four-way, halving the instruction stream can roughly halve recorded load-conflict events.

On the store side, 36,864 is the number of publications removed, not necessarily the number of conflicts removed. A correctly emitted same-column 32-bit store has 32 adjacent lanes writing 32 adjacent bank words, hence can eliminate essentially all of the packed path’s added 73,728 store conflicts. The source already identifies that ownership-safe design at [PLAN_task20_scale.md:1109](/root/marlin_ppu/quactlize/dev/fold_derivation/PLAN_task20_scale.md:1109). It must be verified that the compiler emits a real 32-bit store, but “about half the conflicts” is not the source-level prediction.

**(5) Fair consistency check, but not an outlier test.**

The arithmetic is right:

- ACU: \(21.52/22.54 = 0.9547\), or −4.53%.
- ABBA point estimates: \(1.070/1.131 = 0.9461\), or −5.39%.

A conservative endpoint quotient from the supplied CIs is about 0.916–0.978, so the ACU ratio is plainly compatible with them. But a real CI for swz/pack must be calculated directly from the paired block samples; dividing the two marginal point estimates or CI endpoints loses their correlation.

Also, ACU measures one cold device launch, whereas the benchmark timing includes repeated launch/synchronization overhead [TODO.md:1342](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:1342). Therefore this is good directional corroboration, not statistical evidence that the ACU observation is “not an outlier.”

The corrected overall reading is: the swizzle is active, slower, and measurably useless in aggregate—but the 278,528 conflicts are still most likely the scale/zero consumer reads, and the half2 merge remains capable of attacking both their instruction/conflict count and the decoder stores.
