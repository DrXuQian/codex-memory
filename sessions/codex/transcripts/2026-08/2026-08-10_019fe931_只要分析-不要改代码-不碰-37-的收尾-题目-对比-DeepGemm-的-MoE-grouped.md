# 只要分析,不要改代码,不碰 #37 的收尾。

**题目:对比 DeepGemm 的 MoE grouped GEMM 写法和 quactlize 现在的写法,差别在哪 —— 把"我们要 convert 低比特格式"这一条排除掉。** 用户明确说:除了格式转换之外的区别。

先说仓库里已有的记录,别重新发现:

- 我们的**手写 AIU** grouped GEMM 曾经用 persistent scheduler 打平过 DeepGemm(memory `ppu-moe-aiu-persist-matches-deepgemm`):关键是 grid = #CU × blk/CU 的持久化调度 + grid-stride tile queue + expert cumsum,NST=4/BM=128。当时记了两个坑:要**填满 CU 槽而不是每 CU 一个**;**DeepGemm 的计时必须用 cuda-graph/asys,不能用墙钟**。
- 我们**现在**走的是 cutlass3 的 `quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp`,**非 persistent**。你自己在 `.coord/INBOX.md` 的 095 分析里写过:vendor 默认 grid 是 `P=min(CU,T)`(最多一 CTA/CU),`tile_scheduler_params.h:1662`;而那条路已有 `grid=72`、3.1% occupancy 的失败记录,就在 `ppu_aiu_gemm_mixed_input_group.hpp:195`。
- `docs/BACKTEST.md` C 段:ragged ~33% useful、uniform 49.2%,**同 shape 差 16 点,瓶颈是 masked rows**。

**要机制层面的差别,按对性能的影响排序,每条都要能点到代码或文档行:**

1. **调度** —— DeepGemm 怎么把 `(expert, m-tile, n-tile)` 映射到 CTA?我们怎么映射?persistent / grid-stride / tile queue 的具体形态差在哪。
2. **ragged 怎么处理** —— masked rows 是我们 33% 的主要损失。DeepGemm 对 token 数不整除 BM 的 expert 怎么办:也 pad?还是别的?(memory 记着我们当初手写 AIU 那条路的结论是 "mask-not-pad",但那不是现在这条路。)
3. **A 的搬运与复用** —— 同一个 expert 的多个 n-tile 之间,A 有没有被重复从 HBM 取。
4. **流水线深度与 smem 预算** —— stage 数、A/B/scale 各占多少、有没有 TMA / bulk-copy 等价物。
5. **epilogue 与输出** —— D 怎么写回、有没有 split-K、有没有 fuse 到下一个 op。
6. **计时口径** —— DeepGemm 报的数是 kernel-only 还是端到端。**这条重要**:我们今天刚发现自己的墙钟里含每次 `initialize` + blocking H2D(`moe_grouped_ppu.cuh:317`,那段注释自己说会串行化 host),如果两边口径不同,历史上"打平/落后"的比较全都要打折扣。

**每条给出:DeepGemm 怎么做 / 我们怎么做 / 差多少 / 是不是我们能搬。** 搬不动的要说清是**硬件差异**(PPU 无 TMA?无 cluster?)还是**没接线** —— 这两个的判据在 memory `blocker-mechanism-vs-wiring` 里。

**如果本地没有 DeepGemm 源码,直接说没有,不要凭印象比较。** memory 里提过我们有 `deepgemm_load_bin` 之类的工具,先找;找不到就说找不到,给我一个"要比较需要什么"的清单。我今天已经因为"凭没检查过的印象下结论"被纠正四次,这条上宁可空手也不要编。

- **Thread ID:** `019fe931-b4b5-7363-858e-53817ddcf672`
- **Started / last event:** 2026-08-10 01:02 UTC → 2026-08-10 01:24 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/10/rollout-2026-08-10T09-02-56-019fe931-b4b5-7363-858e-53817ddcf672.jsonl`
- **Subagents spawned:** 3 (not exported)
- **Git:** `{"commit_hash": "96b0af8c717b7e48612e714ca80c661f134c9a3c", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-10 01:03 UTC

只要分析,不要改代码,不碰 #37 的收尾。

**题目:对比 DeepGemm 的 MoE grouped GEMM 写法和 quactlize 现在的写法,差别在哪 —— 把"我们要 convert 低比特格式"这一条排除掉。** 用户明确说:除了格式转换之外的区别。

先说仓库里已有的记录,别重新发现:

- 我们的**手写 AIU** grouped GEMM 曾经用 persistent scheduler 打平过 DeepGemm(memory `ppu-moe-aiu-persist-matches-deepgemm`):关键是 grid = #CU × blk/CU 的持久化调度 + grid-stride tile queue + expert cumsum,NST=4/BM=128。当时记了两个坑:要**填满 CU 槽而不是每 CU 一个**;**DeepGemm 的计时必须用 cuda-graph/asys,不能用墙钟**。
- 我们**现在**走的是 cutlass3 的 `quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp`,**非 persistent**。你自己在 `.coord/INBOX.md` 的 095 分析里写过:vendor 默认 grid 是 `P=min(CU,T)`(最多一 CTA/CU),`tile_scheduler_params.h:1662`;而那条路已有 `grid=72`、3.1% occupancy 的失败记录,就在 `ppu_aiu_gemm_mixed_input_group.hpp:195`。
- `docs/BACKTEST.md` C 段:ragged ~33% useful、uniform 49.2%,**同 shape 差 16 点,瓶颈是 masked rows**。

**要机制层面的差别,按对性能的影响排序,每条都要能点到代码或文档行:**

1. **调度** —— DeepGemm 怎么把 `(expert, m-tile, n-tile)` 映射到 CTA?我们怎么映射?persistent / grid-stride / tile queue 的具体形态差在哪。
2. **ragged 怎么处理** —— masked rows 是我们 33% 的主要损失。DeepGemm 对 token 数不整除 BM 的 expert 怎么办:也 pad?还是别的?(memory 记着我们当初手写 AIU 那条路的结论是 "mask-not-pad",但那不是现在这条路。)
3. **A 的搬运与复用** —— 同一个 expert 的多个 n-tile 之间,A 有没有被重复从 HBM 取。
4. **流水线深度与 smem 预算** —— stage 数、A/B/scale 各占多少、有没有 TMA / bulk-copy 等价物。
5. **epilogue 与输出** —— D 怎么写回、有没有 split-K、有没有 fuse 到下一个 op。
6. **计时口径** —— DeepGemm 报的数是 kernel-only 还是端到端。**这条重要**:我们今天刚发现自己的墙钟里含每次 `initialize` + blocking H2D(`moe_grouped_ppu.cuh:317`,那段注释自己说会串行化 host),如果两边口径不同,历史上"打平/落后"的比较全都要打折扣。

**每条给出:DeepGemm 怎么做 / 我们怎么做 / 差多少 / 是不是我们能搬。** 搬不动的要说清是**硬件差异**(PPU 无 TMA?无 cluster?)还是**没接线** —— 这两个的判据在 memory `blocker-mechanism-vs-wiring` 里。

**如果本地没有 DeepGemm 源码,直接说没有,不要凭印象比较。** memory 里提过我们有 `deepgemm_load_bin` 之类的工具,先找;找不到就说找不到,给我一个"要比较需要什么"的清单。我今天已经因为"凭没检查过的印象下结论"被纠正四次,这条上宁可空手也不要编。

## Assistant · 2026-08-10 01:03 UTC

收到：只做只读分析，不改代码，也不碰 #37 的收尾。我会先核对本地是否确有 DeepGemm 源码/生成产物；只有能落到本地代码行的机制才下结论，并把“格式转换”完全排除。并行核对调度、ragged/搬运/流水线，以及两边计时口径。

<details><summary>21 tool call(s)</summary>

- `spawn_agent: {"task_name":"deepgemm_source","fork_turns":"all","message":"gAAAAABqeSNSgcsJszvbNPmoWsx8195F29sIzHzzMqRgtbC4brebi3S6icWS8ppCvJ4AkUNUA49cqhQ1q1vCy0oiTeIa03Q8GItRyhQ9Dct90737ieTkNjJKPbnjOFgonJcwWOUbWvrR5vubfye8JADaHbAciM7e-ieDeSB-kgDK55uwDBt …`
- `spawn_agent: {"task_name":"pipeline_data","fork_turns":"all","message":"gAAAAABqeSNZjCTxfQ15WTRTsQlvHQmQiOTssENuvk_g6TIohd-svoeF8ia-kLIlPZIHH3lVc3M1bEdJcZ6w2kcR6dHCemqtwtsNw0ohqv7IR6gqcFSNaUl5axzM0v7NaNFQqLUVE7G45Dtc9X6P4Ove8iAg6EzJfgodY99G_acpVlu4uPELY …`
- `spawn_agent: {"task_name":"epilogue_timing","fork_turns":"all","message":"gAAAAABqeSNe8LqzHPipu9G2-1IGKvXH1pPk17RDmiD0ZvHJRSyfawJhaW0r0Ein6a_P9ohbtnB4W0Y-berqh766Cmwg3v8IIIN3dtvIHKjotr_0T8V3dPNk3m6k0sC1lqCSuFqUDACBwBnctdVi9DYO2ZFm-RFdCpAxqLrvioPQZG_H5iw …`
- `exec: const p = await tools.update_plan({plan:[ {step:"定位已有记录与本地 DeepGemm 证据",status:"in_progress"}, {step:"逐项核对当前 CUTLASS3 路线的机制与数值",status:"pending"}, {step:"校准计时口径并评估历史比较可信度",status:"pending"}, {step:"按性能影响排序形成可搬性结论",status:"pending"} ]}); tex …`
- `exec: const r = await tools.exec_command({ cmd: "pwd && rg --files -g 'AGENTS.md' -g '.coord/INBOX.md' -g 'docs/BACKTEST.md' -g '*deepgemm*' -g '*DeepGemm*' -g 'ppu_aiu_gemm_mixed_input_group.hpp' -g 'moe_grouped_ppu.cuh' -g 'tile_scheduler_param …`
- `exec: const r = await tools.exec_command({ cmd: "ls -la .coord 2>/dev/null; rg --files -uu /root/marlin_ppu | rg '(AGENTS\\.md$|INBOX\\.md$|BACKTEST\\.md$|deepgemm|DeepGemm|moe_grouped_ppu\\.cuh$|ppu_aiu_gemm_mixed_input_group\\.hpp$|tile_schedul …`
- `exec: const r = await tools.exec_command({ cmd: "rg --files -uu /root 2>/dev/null | rg -i 'deep.?gemm|deepgemm_load_bin|blocker-mechanism-vs-wiring' | head -n 1000", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 30000, max_output_tokens:  …`
- `exec: const r = await tools.exec_command({ cmd: "ls -la /root/llama.cpp/thirdparty/DeepGEMM 2>/dev/null; git -C /root/llama.cpp/thirdparty/DeepGEMM rev-parse --short HEAD 2>/dev/null; git -C /root/llama.cpp/thirdparty/DeepGEMM status --short 2>/d …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /root/marlin_ppu/memory/ppu-moe-aiu-persist-matches-deepgemm.md; nl -ba /root/marlin_ppu/memory/blocker-mechanism-vs-wiring.md", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000,  …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n -C 8 '(095|tile_scheduler_params|grid=72|3\\.1%|persistent|DeepGemm)' .coord/INBOX.md | head -n 500", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 40000 }); …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n '^(#|##|###).*C|ragged|33\\.?0?%|49\\.2%|masked|uniform|useful|issued|DeepGemm|padding' docs/BACKTEST.md | head -n 500", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_outpu …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba docs/BACKTEST.md | sed -n '132,168p'; nl -ba .coord/INBOX.md | sed -n '3800,3842p'; nl -ba .coord/INBOX.md | sed -n '1260,1302p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000 …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp | sed -n '1,280p'; nl -ba third_party/actlize/include/cutlass/gemm/kernel/tile_scheduler_params.h | sed -n '1600,1705p'", workdir: "/root …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp | sed -n '230,520p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 50000 }); text(r.output);`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba quactlize/include/moe_grouped_ppu.cuh | sed -n '1,430p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 60000 }); text(r.output);`
- `exec: const r = await tools.exec_command({ cmd: "rg -n -C 5 '(hggcEvent|cudaEvent|std::chrono|chrono|initialize|warmup|iterations|filter_and_run|moe_grouped_ppu::launch|moe.*group)' quactlize examples tests ppu_tests scripts . 2>/dev/null | head  …`
- `exec: const r = await tools.exec_command({ cmd: "rg --files tests dev | rg '(moe|grouped).*(bench|perf)|bench.*moe|test_lowbit_moe_bench' | sort", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 10000 }); text(r.ou …`
- `exec: const r = await tools.exec_command({ cmd: "rg --files -uu . | rg 'test_(lowbit_moe|moe_splitk)_bench\\.cu$|moe_bench.*\\.cu$' | sort", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 10000 }); text(r.output);`
- `exec: const r = await tools.exec_command({ cmd: "rg -n -C 10 '(PpuTimer|Event|chrono|warm|iter|once|filter_and_run|elapsed|prefix_ready)' benchmarks/test_lowbit_moe_bench.cu; nl -ba benchmarks/test_lowbit_moe_bench.cu | sed -n '1,360p'", workdir: …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n -C 10 '(elapsed|Event|chrono|warm|moe_time|time_|measure|launch\\(|once)' benchmarks/lowbit_moe_bench.hpp | head -n 1000; nl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '1,460p'", workdir: " …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '450,720p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 50000 }); text(r.output);`

</details>

## Assistant · 2026-08-10 01:05 UTC

已确认本机不是“没有 DeepGemm”：工作树本体没检出，但有 DeepGemm 生成后的完整 `kernel.cu` 缓存，另有一份 TRT-LLM 内嵌的 DeepGemm 源码。因此可以做源码级比较；我会区分“生成 kernel 的直接证据”和“仓库记录”，不拿版本不明的接口行为互相代替。初步还发现一个关键校准：当前 header 已经绕开 vendor 的 `min(CU,T)` persistent grid，实际是“每个真实 tile 一个 CTA”的扁平非 persistent grid。

<details><summary>37 tool call(s)</summary>

- `exec: const r = await tools.exec_command({ cmd: "for f in /root/.deep_gemm_cache/cache/kernel.sm90_m_grouped_bf16_gemm_contiguous.*/kernel.cu; do wc -l \"$f\"; sha256sum \"$f\"; done", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000,  …`
- `exec: const r = await tools.exec_command({ cmd: "for f in /root/.deep_gemm_cache/cache/kernel.sm90_m_grouped_bf16_gemm_contiguous.*/kernel.cu; do echo FILE:$f; nl -ba \"$f\"; done", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max …`
- `exec: const r = await tools.exec_command({ cmd: "rg --files -uu / 2>/dev/null | rg '/deep_gemm/(impls/sm90_bf16_gemm\\.cuh|scheduler\\.cuh|jit_kernels/|include/)' | head -n 500", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 30000, max_ou …`
- `exec: const r = await tools.exec_command({ cmd: "ls -la /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm | head -n 80; git -C /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_ …`
- `exec: const r = await tools.exec_command({ cmd: "git -C /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm rev-parse --show-toplevel; git -C /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/d …`
- `exec: const r = await tools.exec_command({ cmd: "stat -c '%y %n' /root/.deep_gemm_cache/cache/kernel.sm90_m_grouped_bf16_gemm_contiguous.*/kernel.cu | sort; git -C /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe statu …`
- `exec: const r = await tools.exec_command({ cmd: "find /root -type f \\( -name 'deepgemm_load_bin.py' -o -name 'scan_moe_layers.py' -o -name 'asys_report.py' \\) -print 2>/dev/null", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 30000, max …`
- `exec: const r = await tools.exec_command({ cmd: "git -C /root/llama.cpp branch -a --no-color; git -C /root/llama.cpp log --all --name-only --pretty=format: | rg '(deepgemm_load_bin|scan_moe_layers|asys_report|mmf-aiu|moe_gemm_aiu)' | sort -u", wo …`
- `exec: const r = await tools.exec_command({ cmd: "find /root -type d -name .git -prune -print 2>/dev/null | head -n 100; find /root -type f -path '*/.git' -print 2>/dev/null | head -n 100", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 300 …`
- `exec: const r = await tools.exec_command({ cmd: "for d in /root/marlin_ppu/Kernels /root/llama-validate /root/.claude/jobs/a7d83a5d/tmp/qutlass; do echo REPO:$d; git -C \"$d\" branch -a --no-color 2>/dev/null | rg -i 'moe|aiu|deep|ppu' | head -n  …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm/legacy/m_grouped_gemm.py | sed -n '1,360p'; nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6 …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm/legacy/m_grouped_gemm.py | sed -n '80,360p'; rg -n 'm_grouped|MGrouped|masked|contiguous|padding|pad' / …`
- `exec: const r = await tools.exec_command({ cmd: "find /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe -maxdepth 2 -type d -print | sort; rg --files -uu /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchp …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/csrc/apis/gemm.hpp | sed -n '430,590p'; nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpa …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n 'sm90_m_grouped_bf16|bf16_gemm_impl|MGroupedMasked|MGroupedContiguous' /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/csrc /tmp/claude-0/-root/b4d24e49-75af-4442 …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/csrc/jit_kernels/impls/sm90_bf16_gemm.hpp | sed -n '1,270p'; nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/csrc/jit_kernels/heuristics/sm90.hpp | sed -n '140,290p'; nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20d …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm/include/deep_gemm/impls/sm90_bf16_gemm.cuh | sed -n '1,430p'", workdir: "/root/marlin_ppu/quactlize", y …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n 'is_computation_valid' /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm/include /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_pr …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/tests/generators.py | sed -n '300,415p'; rg -n 'get_theoretical_mk_alignment|mk_alignment' /tmp/claude-0/-root/b4 …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/csrc/jit_kernels/heuristics/runtime.hpp | sed -n '1,100p'; rg -n 'kLegacyMKAlignment' /tmp/claude-0/-root/b4d24e4 …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n 'block_m_info|nopad|no_pad|masked_m|m_grouped.*masked' /root /tmp/claude-0 2>/dev/null | head -n 1000", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 30000, max_output_tokens: 50000 } …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /root/llama.cpp/ppu_so/moe/deepgemm_c.cpp | sed -n '1,420p'; rg -n 'block_m_info|nopad|get_best_configs|compile_and_tune|scheduler' /root/llama.cpp/ppu_so /root/llama.cpp -g '*.cpp' -g '*.cu …`
- `exec: const r = await tools.exec_command({ cmd: "ls -la /root/llama.cpp/ppu_so; find /root/llama.cpp/ppu_so -maxdepth 4 -type d -print | sort | head -n 200; rg --files -uu /root/llama.cpp/ppu_so | sort | head -n 300", workdir: "/root/marlin_ppu/q …`
- `exec: const r = await tools.exec_command({ cmd: "git -C /root/llama.cpp submodule status --recursive | head -n 100; find /root/llama.cpp/.git/modules -maxdepth 5 -type d -iname '*DeepGemm*' -print", workdir: "/root/marlin_ppu/quactlize", yield_ti …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n -C 2 'DeepGemm|deepgemm' /root/llama.cpp/.gitmodules /root/llama.cpp/ppu_so/README.md /root/llama.cpp/ppu_so/CMakeLists.txt; git -C /root/llama.cpp ls-files -s ppu_so/third_party/DeepGemm thi …`
- `exec: const r = await tools.exec_command({ cmd: "find /root/llama.cpp/.git/modules -maxdepth 6 -type d -print | sort | rg -i '(ppu|deep|gemm)'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 10000 }); text(r.outp …`
- `exec: const r = await tools.exec_command({ cmd: "git -C /root/llama.cpp ls-files -s | rg -i 'deepgemm'; git --git-dir=/root/llama.cpp/.git/modules/thirdparty/DeepGEMM log -1 --format='%H %ci %s'; git --git-dir=/root/llama.cpp/.git/modules/thirdpa …`
- `exec: const r = await tools.exec_command({ cmd: "git --git-dir=/root/llama.cpp/.git/modules/thirdparty/DeepGEMM --work-tree=/tmp log -1 --format='%H %ci %s'; git --git-dir=/root/llama.cpp/.git/modules/thirdparty/DeepGEMM --work-tree=/tmp branch - …`
- `exec: const r = await tools.exec_command({ cmd: "rg --files -uu /root /tmp 2>/dev/null | rg '(common_bf16\\.hpp$|m_grouped_bf16_gemm\\.hpp$|jit_kernels/impls/bf16_gemm\\.hpp$|scheduler\\.cuh$)' | head -n 500", workdir: "/root/marlin_ppu/quactlize …`
- `exec: const r = await tools.exec_command({ cmd: "git -C /root/marlin_ppu/Kernels log -1 --format='%H %ci %s'; wc -l /root/marlin_ppu/Kernels/moe_ffn/fp8/trtllm_cutlass_standalone/cpp/tensorrt_llm/deep_gemm/*; nl -ba /root/marlin_ppu/Kernels/moe_f …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /root/marlin_ppu/Kernels/moe_ffn/fp8/trtllm_cutlass_standalone/cpp/tensorrt_llm/deep_gemm/scheduler.cuh | sed -n '400,708p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max …`
- `exec: const r = await tools.exec_command({ cmd: "rg -l 'BF16GemmCutlass3Runtime' /root/marlin_ppu/*.jsonl /root/.claude/**/*.jsonl 2>/dev/null | head -n 100; rg -n 'BF16GemmCutlass3Runtime|m_grouped_bf16_gemm.hpp|GroupScheduleMode|MainloopSm90Tma …`
- `exec: const r = await tools.exec_command({ cmd: "nl -ba /root/llama.cpp/ppu_so/moe/deepgemm_c.cpp | sed -n '300,900p'", workdir: "/root/marlin_ppu/quactlize", yield_time_ms: 10000, max_output_tokens: 70000 }); text(r.output);`
- `exec: const r = await tools.exec_command({ cmd: "rg -n 'kIsNoPadPreprocessLayout|GroupedNoPad|NoPadScheduler|block_m_info' /root/marlin_ppu/0e9fac6a-53ba-4eda-a836-b73d4e69a6b9.jsonl | head -n 300", workdir: "/root/marlin_ppu/quactlize", yield_ti …`
- `exec: const r = await tools.exec_command({ cmd: "wc -l -c /root/marlin_ppu/0e9fac6a-53ba-4eda-a836-b73d4e69a6b9.jsonl; jq -r 'select(tostring | contains(\"kIsNoPadPreprocessLayout\")) | .message.content[]? | select(.type==\"tool_result\") | .cont …`
- `exec: const r = await tools.exec_command({ cmd: "rg -n -o '.{0,500}(GroupedNoPadScheduler|NoPadScheduler|kIsNoPadPreprocessLayout).{0,1500}' /root/marlin_ppu/0e9fac6a-53ba-4eda-a836-b73d4e69a6b9.jsonl | head -n 300", workdir: "/root/marlin_ppu/qu …`

</details>

## Assistant · 2026-08-10 01:12 UTC

已经确认一个关键边界：本机没有当时内部 PPU DeepGemm `GroupedNoPad` 的完整源码树，只有转写 shim、同源 scheduler，以及一份较新的公开版源码。我会把“历史 PPU 路径”和“公开 SM90 路径”严格分栏，不拿后者的 TMA/cluster 能力冒充当时的实现。另一个已经能落代码的结论是：`NoPad` 只是不物理补 A，尾块仍按 `ceil(M_e/BM)` 发整块计算，所以并没有消除 masked-row 税。

<details><summary>30 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"rg -n -uu \"MainloopPPUAiuMixedInput|struct SharedStorage|SmemLayoutA|SmemLayoutB|Stages|ppu\\.cp\\.async\\.aiu\\.bulk|ClusterShape\" quactlize/include third_party/actlize/include | head -n 260","w …`
- `exec: const cmds = [ ["scheduler", "nl -ba third_party/actlize/include/cutlass/gemm/kernel/ppu_tile_scheduler_group.hpp | sed -n '1,280p'"], ["mainloop-storage", "nl -ba quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma …`
- `exec: const cmds = [ ["storage", "nl -ba quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp | sed -n '690,745p'"], ["load-copy", "nl -ba quactlize/include/quactlize_extensions/cutlass/gemm/collective/quac …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp | sed -n '185,285p'; nl -ba third_party/actlize/include/cutlass/gemm/kernel/ppu_tile_scheduler_group.hpp | sed -n '395,435p'","workdir":" …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n -uu \"KernelAiuMultistagePersistent|PersistentTileSchedulerPPUGroup|fetch_next_work\\(|advance_to_next_work\\(\" third_party/actlize/include/cutlass/gemm quactlize/include | head -n 220","wor …`
- `exec: const cmds = [ ["selector", "nl -ba third_party/actlize/include/cutlass/gemm/kernel/tile_scheduler.hpp | sed -n '80,130p'"], ["persist-kernel", "nl -ba third_party/actlize/include/cutlass/gemm/kernel/ppu_aiu_gemm_persistent.hpp | sed -n '40 …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/include/quactlize_extensions/cutlass/gemm/quactlize_dispatch_policy.hpp | sed -n '65,130p'; rg -n \"struct ArtifactFoldedSchedule|ArtifactFoldedSchedule\" quactlize/include/ppu_mix …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba quactlize/include/ppu_mixed_policy.hpp | sed -n '35,85p'; nl -ba .coord/INBOX.md | sed -n '3800,3842p'; nl -ba /root/marlin_ppu/memory/blocker-mechanism-vs-wiring.md | sed -n '20,58p'","work …`
- `exec: const cmds = [ ["dg-shim-nopad", "nl -ba /root/llama.cpp/ppu_so/moe/deepgemm_c.cpp | sed -n '64,165p;300,410p;653,820p'"], ["dg-derived-sched", "nl -ba /root/marlin_ppu/Kernels/moe_ffn/fp8/trtllm_cutlass_standalone/cpp/tensorrt_llm/deep_gem …`
- `exec: const dg=/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe; const cmds = [ ["ours-time", "nl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '200,232p;245,272p;310,345p;510,610p'"], ["dg-time", 'nl -ba ${dg}/deep_gem …`
- `exec: const dg="/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe"; const cmds = [ ["ours-time", "nl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '200,232p;245,272p;310,345p;510,610p'"], ["dg-time", 'nl -ba ${dg}/deep_g …`
- `exec: const dg="/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe"; const r = await tools.exec_command({"cmd":'nl -ba ${dg}/deep_gemm/testing/bench.py | sed -n '79,150p'; nl -ba ${dg}/tests/test_bf16.py | sed -n '145,16 …`
- `exec: const dg="/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe"; const r=await tools.exec_command({"cmd":'nl -ba ${dg}/deep_gemm/csrc/jit_kernels/heuristics/sm90.hpp | sed -n '1,120p;135,205p'; nl -ba ${dg}/deep_gemm …`
- `exec: const r=await tools.exec_command({"cmd":"rg -n -uu \"423\\.96|162\\.1|i4 64x128:64\" . /root/marlin_ppu/memory /root/marlin_ppu/quactlize 2>/dev/null | head -n 100; nl -ba quactlize/include/fold_traits.hpp | sed -n '215,275p'; rg -n \"eleme …`
- `exec: const r=await tools.exec_command({"cmd":"nl -ba quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp | sed -n '570,670p'; nl -ba dev/fold_derivation/SWEEP_STATE.md | sed -n '85,130p'; nl -ba .coord/IN …`
- `exec: const r=await tools.exec_command({"cmd":"rg -n \"LOWBIT_QMODE_SEL|LOWBIT_QMODE\" benchmarks CMakeLists.txt dev scripts ci build.sh | head -n 160; rg -n \"enum class QuantMode|QuantMode::\" quactlize/include/ppu_mixed_policy.hpp quactlize/in …`
- `exec: const r=await tools.exec_command({"cmd":"nl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '30,52p;430,465p'; nl -ba ci/check_measured_paths_ship.py | sed -n '1,40p'; nl -ba dev/fold_derivation/SWEEP_STATE.md | sed -n '105,116p'","workdir":"/ …`
- `exec: const r=await tools.exec_command({"cmd":"rg -n \"ScaleOnly|LOWBIT_QMODE|PPU_DEFS\" dev/fold_derivation/SWEEP_STATE.md .coord/INBOX.md | head -n 120","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens":12000}); t …`
- `exec: const dg="/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe"; const r=await tools.exec_command({"cmd":'rg --files -uu ${dg} | rg 'heuristic|sm90.*hpp|common_bf16' | head -n 100',"workdir":"/root/marlin_ppu/quactli …`
- `exec: const dg="/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe"; const r=await tools.exec_command({"cmd":'nl -ba ${dg}/csrc/jit_kernels/heuristics/sm90.hpp | sed -n '1,120p;135,205p'',"workdir":"/root/marlin_ppu/quac …`
- `exec: const r=await tools.exec_command({"cmd":"nl -ba quactlize/include/moe_splitk_ppu.cuh | sed -n '1,115p'; rg -n \"splitk|reduce\" quactlize/include quactlize/csrc benchmarks | head -n 180","workdir":"/root/marlin_ppu/quactlize","yield_time_ms …`
- `exec: const r=await tools.exec_command({"cmd":"nl -ba quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp | sed -n '95,185p'; nl -ba quactlize/include/moe_grouped_ppu.cuh | sed -n '250,283p'; nl -ba quactlize/include/moe_splitk_reduce.cuh | sed  …`
- `wait_agent: {"timeout_ms":1000}`
- `wait_agent: {"timeout_ms":10000}`
- `send_message: {"target":"/root/pipeline_data","message":"gAAAAABqeSbLmyOs8h9xKK1WnRxQNxpuvykWCMAwBwkVLlZQDIDjWdn3ilLZjffrSCGd65DrfCNbjhei1WS5PScFJwqbOMiPdAGWiDHsmAmDU0XhJal255rWbWg8jJpOJc-a3OkMz0u78_9689qdGSwRFkSET4BB8ITZOSrkHKTpi2LBAIqsFUS5e4y6xr2-Q6iMj …`
- `exec: const r=await tools.exec_command({"cmd":"find /root/.deep_gemm_cache/cache -maxdepth 2 -type f -name 'kernel.cu' -path '*m_grouped_bf16_gemm*' -print 2>/dev/null | sort | head -n 20; rg -n \"kNumTMAMulticast|NUM_TMA_MULTICAST|num_tma_multic …`
- `exec: const r=await tools.exec_command({"cmd":"for f in /root/.deep_gemm_cache/cache/kernel.sm90_m_grouped_bf16_gemm_contiguous.*/kernel.cu; do echo \"$f\"; sed -n '1,35p' \"$f\" | tail -n 18; done","workdir":"/root/marlin_ppu/quactlize","yield_t …`
- `wait_agent: {"timeout_ms":10000}`
- `list_agents: {}`
- `wait_agent: {"timeout_ms":10000}`

</details>

## Assistant · 2026-08-10 01:19 UTC

计时口径也已经落定：当前 423.96 µs 是 launcher 墙钟，不是 kernel-only；每个 timed iteration 都重跑 `can_implement/get_workspace_size/initialize`，ragged 还重建 prefix 并做 blocking H2D。历史 DeepGemm 的 452 µs 则明确是 asys 的 GEMM kernel-only；同一记录里的 DeepGemm wrapper wall 是 1440 µs。因此现有数字不能直接排“谁快多少”，只能保留机制比较和各自同口径的内部差值。

<details><summary>6 tool call(s)</summary>

- `exec: const r=await tools.exec_command({"cmd":"nl -ba .coord/INBOX.md | sed -n '3688,3760p'; nl -ba /root/llama.cpp/ppu_so/moe/deepgemm_c.cpp | sed -n '1,55p;815,870p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_toke …`
- `exec: const r=await tools.exec_command({"cmd":"nl -ba benchmarks/moe_router_fixture.hpp | sed -n '1,95p'; nl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '285,310p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens" …`
- `exec: const r=await tools.exec_command({"cmd":"nl -ba quactlize/include/ppu_tactic_space.hpp | sed -n '1,30p;180,210p'; nl -ba third_party/actlize/include/cute/arch/copy_ppu0010_aiu.hpp | sed -n '45,90p'; nl -ba third_party/actlize/include/cute/a …`
- `exec: const r=await tools.exec_command({"cmd":"ls -ld /root/llama.cpp/ppu_so/third_party/DeepGemm; find /root/llama.cpp/ppu_so/third_party/DeepGemm -maxdepth 1 -mindepth 1 -print | head; p=/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/ …`
- `exec: const r=await tools.exec_command({"cmd":"git -C /tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe rev-parse HEAD; git status --short","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tokens …`
- `exec: const plan = [ {step:"核对仓库已有记录与当前 quactlize grouped GEMM 路径",status:"completed"}, {step:"定位并核验本地 DeepGemm 源码、缓存与历史 PPU 旁证",status:"completed"}, {step:"逐项比较调度、ragged、A 复用、流水线、epilogue 与计时口径",status:"completed"}, {step:"按性能影响和可搬性整理证据化结论",stat …`

</details>

## Assistant · 2026-08-10 01:24 UTC

结论先说：排除低比特格式转换后，DeepGemm 与当前 quactlize 唯一明确的一阶机制差别是调度。DeepGemm 的 `NoPad` 并没有消除 masked-row 计算；A 也没有因为 persistent 就跨 n-tile 留在 smem；epilogue 基本等价。流水线的历史精确比较做不了，因为当时 PPU DeepGemm 的 kernel 源码本地不存在。现有性能数字又混用了 kernel-only 和 launcher wall，不能再据此说“领先/落后 X%”。

源码边界必须先划清：历史 PPU DeepGemm submodule 只剩 gitlink `164e851...`，[标记在这里](/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/theirs/ppu_so/third_party/DeepGemm:1)，实际工作树为空。能核验的是按旧实现转写的 [deepgemm_c.cpp](/root/llama.cpp/ppu_so/moe/deepgemm_c.cpp:1)、DeepGemm-derived scheduler，以及公开版 commit `1f6f3f3`。公开版是 SM90 新实现，不能冒充历史 452 µs 的 PPU cubin。`deepgemm_load_bin.py`、`scan_moe_layers.py`、`asys_report.py` 本地也都没找到。

### 1. 调度——最大的真实差别

**DeepGemm：**固定 resident grid，加全局 grid-stride 队列。历史记录里的形态是：

```text
t = iter * gridDim.x + blockIdx.x
t -> expert -> local m_tile -> n_tile
```

队列按 expert-major、m-major、n-minor，并做 N-group swizzle 以保 L2 locality，[已有记录:15–21](/root/marlin_ppu/memory/ppu-moe-aiu-persist-matches-deepgemm.md:15)。PPU shim 先以 `#CU` 建 grid，再用 occupancy API 乘 `blocks_per_cu`，明确填满所有 resident 槽，[deepgemm_c.cpp:774–814](/root/llama.cpp/ppu_so/moe/deepgemm_c.cpp:774)。专家数 ≥128 时，先在设备上生成每个 m-block 的 `(expert, M_e, block-prefix, row-prefix)` 映射，[deepgemm_c.cpp:80–150](/root/llama.cpp/ppu_so/moe/deepgemm_c.cpp:80)。

**我们当前：**不是 vendor 默认的 `P=min(CU,T)`。那个默认确实存在于 [tile_scheduler_params.h:1662–1703](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/kernel/tile_scheduler_params.h:1662)，但当前 specialization 已经绕过它：

- ragged grid 是 `(Σ_e ceil(M_e/TM), ceil(N/TN), 1)`；
- 一个 block 只处理一个 `(expert,m_tile,n_tile)`；
- `blockIdx.x` 通过 prefix 二分映射到 expert，`blockIdx.y` 就是 n-tile；
- kernel 内没有工作队列循环。

证据在 [ppu_aiu_gemm_mixed_input_group.hpp:195–226](/root/marlin_ppu/quactlize/quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp:195) 和 [245–299](/root/marlin_ppu/quactlize/quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp:245)。文件里的 `fetch_next_work()` 目前是未被 operator 调用的死接头。

**差多少：**

- 已知的 persistent 槽位效应：旧手写 AIU 从只发 `#CU` 的 561 µs 降到 `#CU×2` 的 472 µs，快 **15.9%**，[记录:23–26](/root/marlin_ppu/memory/ppu-moe-aiu-persist-matches-deepgemm.md:23)。
- naïve 接 vendor persistent 的失败也是真实的：grid=72、3.1% occupancy、16% CU throughput，[当前 header:195–198](/root/marlin_ppu/quactlize/quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp:195)。
- 但当前 flat static grid 已经消除了“只发 72 CTA”和“小 expert 的 idle blocks”。因此“当前 CUTLASS static → 正确 persistent”的增量没有测过，不能把旧 15.9%直接搬过来。

**能不能搬：**能，归类为“没接线/接口适配”，不是硬件 blocker。actlize 已有 grouped persistent scheduler 的 grid-stride 实现，[ppu_tile_scheduler_group.hpp:46–62, 279](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/kernel/ppu_tile_scheduler_group.hpp:46)，也有 persistent kernel 的 work-loop，[ppu_aiu_gemm_persistent.hpp:314–383](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/kernel/ppu_aiu_gemm_persistent.hpp:314)。难点是它吃普通 `MainloopPPUAiu` 接口，而当前 mixed-input collective 接口不同，所以不是改一个 tag，仍需 mixed-input persistent kernel adapter；仓库 095 也已把这个边界写明，[INBOX:3805–3836](/root/marlin_ppu/quactlize/.coord/INBOX.md:3805)。

### 2. Ragged——最大损失，但不是两者的差别

**DeepGemm：**历史 `GroupedNoPad` 的 A 是紧凑 expert-order 存储，不做每专家物理 padding，[deepgemm_c.cpp:653–657](/root/llama.cpp/ppu_so/moe/deepgemm_c.cpp:653)。但 block-map 仍为每个专家生成 `ceil(M_e/BM)` 个 m-block，[94–150](/root/llama.cpp/ppu_so/moe/deepgemm_c.cpp:94)。也就是说：

- storage 是 no-pad；
- issued compute 仍是按 BM 向上取整；
- 尾块无效行仍被 mask，整块 MMA 税还在。

公开版 BF16 kernel 甚至直接留着 `TODO: remove some useless computation for unaligned Ms`，[sm90_bf16_gemm.cuh:222–244](/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm/include/deep_gemm/impls/sm90_bf16_gemm.cuh:222)。

**我们：**同样是 mask-not-physical-pad。flat grid 不发 idle expert blocks；A 的 `.padz` bulk copy只读取真实行，其余 smem 行由硬件补零，[moe_grouped_ppu.cuh:235–245](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:235)。但 MMA 仍按完整 TM tile 执行。

**差多少：**

- 仓库确认的同 shape 差距是约 **49.2% → 33%，约 16 个点**；同一个 ragged kernel 的 useful 33% 对 issued 46% 又直接隔了约 **13 个点**，[BACKTEST:145–163](/root/marlin_ppu/quactlize/docs/BACKTEST.md:145)。
- 因此 masked rows 确实是主损失，但 DeepGemm NoPad 不会把它拿掉。
- C1 固定分布下，当前 TM64 是 599 个 m-tile、38,336 issued rows，mask 14.5%。若 DeepGemm 配置取 BM128，则是 311 个 m-tile、39,808 issued rows，mask 17.7%。这是按固定 fixture 和 [公式](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:299) 推导，不是 452 µs cubin 的实测；当时 DG 的实际 BM 没留下，不能据此定案。

**能不能搬：**没有可搬的 DeepGemm“消除尾块”机制。若要真正砍掉 masked MMA，需要 tail/GEMV 专门路径、更小 BM 或可变 M mainloop；这不是 scheduler 接线，现有源码也不足以判成“PPU 硬件绝对做不到”。DeepGemm 的设备端 block-map/preprocess 倒可以搬，属于接线，可避免当前 host prefix + H2D。

### 3. A 的搬运与复用

**DeepGemm：**历史 kernel body缺失，不能确认其 PPU 版 A load 细节。能确认的公开版行为是：persistent CTA 每拿到新 `(m,n)` tile，仍重新跑完整 K-loop并重新 TMA-load A/B；不会把前一个 n-tile 的 A 留在 smem。scheduler 的收益是 n-minor 排序带来的 L2 temporal locality，而不是 A 只加载一次。

公开 SM90 版还可以通过 2-CTA TMA multicast 在两个相邻 n-tile 间共享 A，但这是公开 SM90 路径；本机八个实际 grouped BF16 cache kernel 全部实例化为 multicast=1，例如 [这个 kernel.cu](/root/.deep_gemm_cache/cache/kernel.sm90_m_grouped_bf16_gemm_contiguous.06c3482cf7e0f93f3d75d218a9a2e0d3/kernel.cu:8)。

**我们：**每个 `(expert,m,n)` CTA 都独立 `load_init`、独立 sA 和 stage ring，[当前 kernel:245–299](/root/marlin_ppu/quactlize/quactlize/include/ppu_aiu_gemm_mixed_input_group.hpp:245)。仓库 traffic model也明确写着：A 的 issued 上界是每 n-tile 一次，实际可能命中 L2，[lowbit_moe_bench.hpp:258–265](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:258)。

**差多少：**C1 的 N=512、TN=128 是 4 个 n-tile，所以每个真实 A 行最多发 4 次请求。真实 A footprint 为 128 MiB，issued 上界 512 MiB；实际 HBM 在两者之间，缺当前 cache counter，不能再报一个伪精确值。历史记录只有 static grid 的 L2 hit 约14%，没有 current-vs-DG 的同口径 counter。

**能不能搬：**

- n-minor swizzle、显式 locality queue：scheduler 接线，可搬。
- 真正同 CTA 跨 n 保留 A：需要重写 tile/mainloop 生命周期，不是换 scheduler。
- cross-CTA multicast：当前 mixed policy 是 1×1×1，但 vendor 层已有 cluster barrier 和 cluster launch 接口，[barrier.h:388–415](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/arch/barrier.h:388)。同时本地没找到 AIU bulk-load multicast 变体。因此按 `blocker-mechanism-vs-wiring` 的判据，只能写“当前未接、硬件能力未知”，不能写“PPU 无 cluster”。

### 4. 流水线深度与 smem

**DeepGemm：**历史 452 µs 对应的 `(BM,BN,BK,stages,SMSIZE,blocks/CU)` 没留下。shim 说明这些值由 `get_best_configs` 返回并会打印，[deepgemm_c.cpp:355–370, 748–750](/root/llama.cpp/ppu_so/moe/deepgemm_c.cpp:355)，但本地没有那次日志，所以精确 stage/smem 差值未知。

仅作为非历史参考，公开 SM90 版：

- A/stage=`BM×BK×2`，B/stage=`BN×BK×2`，另有 D smem和 barriers；
- 用独立 128-thread TMA producer group和 WGMMA consumer；
- heuristic 在 232,448 B 内尽量加深，至少3/4 stage、最多16，[sm90.hpp:105–108, 148–198](/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/csrc/jit_kernels/heuristics/sm90.hpp:105)。

本机公开版 cache 是5–12 stage、约202–220 KiB/CTA，但它不是历史 PPU kernel，不能拿这个比例解释452 µs。

**我们：**当前是普通 CTA-wide async stage ring，`wait → __syncthreads → prefetch/fence → MMA`，[ppu_mixed_pipeline.hpp:39–87](/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/detail/ppu_mixed_pipeline.hpp:39)。C1 winner 是 s6。按当前源码默认 ScaleZero：

- 每 stage：A 8 KiB、B 4 KiB、scale 0.5 KiB、zero 0.5 KiB；
- s6：A 48 KiB、B 24 KiB、scale 3 KiB、zero 3 KiB；
- mainloop payload 合计 **78 KiB**；ScaleOnly 则是 **75 KiB**。

布局和分配来自 [quactlize_mma_mixed_input.hpp:438–443, 633–739](/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp:438)。mainloop/epilogue是 union，不相加；最终 `SharedStorageSize` 仍以 `MOEG_SMEM` 类型打印为准，[moe_grouped_ppu.cuh:172–195](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:172)。仅按256 KiB smem上限可容3 CTA/CU，实际还要看寄存器。

**能不能搬：**

- “PPU 无 TMA 等价物”是错的。当前已经使用 `ppu.cp.async.aiu.bulk.tensor...padz...swzl.2d`，[copy_ppu0010_aiu.hpp:51–83](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/arch/copy_ppu0010_aiu.hpp:51)。异步 bulk、二维 tensor、zero-fill、swizzle都已接线。
- 当前缺的是公开 SM90 那种独立 producer/math 分工；vendor 已有 cp.async completion barrier，因此先归类为 collective 未接线，不能直接判硬件不可能。Hopper 的动态寄存器重分配则没有本地证据。
- scale/B 的字节差异本身与低比特格式绑定，按题意不计作 DeepGemm 机制优势。

### 5. Epilogue、输出、split-K、fusion

**DeepGemm：**历史 PPU 路径写连续 BF16 D，alpha=1、beta=0，[deepgemm_c.cpp:783–794](/root/llama.cpp/ppu_so/moe/deepgemm_c.cpp:783)。生成 kernel body缺失，所以不能声称历史版用了 TMA store。接口中没有 split-K、bias、activation或下一算子 fusion。

**我们：**当前用 `EpiloguePtrArraySimtVectorized`，按 expert 的 D pointer/stride写连续 FP16结果，仍是 alpha=1、beta=0、无 C，[moe_grouped_ppu.cuh:120–139, 258–264](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:120)。主 sweep固定 `splitk=1`，[lowbit_moe_bench.hpp:578–592](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:578)。仓库另有实验性 in-kernel split-K和 FP32 merge，但不在当前比较基线，[moe_splitk_ppu.cuh:50–83](/root/marlin_ppu/quactlize/quactlize/include/moe_splitk_ppu.cuh:50)。

**差多少：**两边最终写回都是 `rows×N×2 B`；BF16 vs FP16数值格式不同，但字节量相同。当前多一次 ptr-array 间接寻址，开销未单测。split-K和下一算子 fusion的基线差为0。

**能不能搬：**这里没有 DeepGemm 优势可搬。若把当前输出专门化为 flat base，是普通接线；真正 fuse SwiGLU或下一 GEMM不是 epilogue flag 能解决的。

### 6. 计时口径——现有“打平/落后”不能直接沿用

**DeepGemm：**

- 历史 452 µs 是明确的 `asys-kernel-only`，[memory:10–13](/root/marlin_ppu/memory/ppu-moe-aiu-persist-matches-deepgemm.md:10)。
- 同一 wrapper 的 wall 是1440 µs，含 config/compile lookup、block-info allocation等；比 named-kernel 多约988 µs、总计约3.2×。CUDA event loop还会计入GPU idle gap，只有 graph replay或asys kernel duration得到约452 µs，[memory:27–30](/root/marlin_ppu/memory/ppu-moe-aiu-persist-matches-deepgemm.md:27)。
- 公开版 benchmark同样通过 profiler按 kernel name 的 `cuda_time_total` 取 kernel-only，[bench.py:79–145](/tmp/claude-0/-root/b4d24e49-75af-4442-836b-b20da6e6712c/scratchpad/dg_probe/deep_gemm/testing/bench.py:79)。

**我们：**

- `time_it` 用 host `high_resolution_clock` 包住20次完整 launcher调用，最后才 sync，[lowbit_moe_bench.hpp:209–223](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:209)。
- timed lambda每次重新进入 `filter_and_run`，且传 `prefix_ready=false`。
- 每次都包含 `can_implement`、`get_workspace_size`、`initialize`；ragged 还重新建 host prefix并做 blocking H2D，然后才 `gemm.run`，[moe_grouped_ppu.cuh:317–335](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:317)。当前实际是 initialize 在322行、blocking copy在332行。

所以当前423.96 µs是“部分 API-call wall”：包含上述 launcher开销，但不含routing、weight pack等完整 MoE E2E。它只是当前 grouped kernel时间的上界，不能与DeepGemm 452 µs named-kernel直接排位。

历史472 vs452的“约慢20 µs/4.4%”只能叫近似 parity：它是手写 AIU cudaEvent 对 DG asys，而且当时输出类型也不同。今天的423.96则是另一条CUTLASS3路径和另一种计时口径，不能用来延续“打平/落后”的结论。

另外，33% useful对46% issued的约13点仍然直接证明masked MMA是主损失；但在今天这个 harness里，ragged相对uniform还额外承担prefix二分、initialize和blocking H2D，因此不能把未来测到的完整16点全部当作纯kernel masked税。

要把剩余未知项定量，需要：

- 取回历史 `164e851...` 源树，或至少452 µs对应的 generated `kernel.cu`/fatbin；
- 取回当时的 `(BM,BN,BK,warpM,warpN,stages,smem,blocks/CU)` 日志；
- 取回 `deepgemm_load_bin.py`/asys trace，分别报告 block-info、GEMM和wrapper；
- 同一router histogram、shape、输出dtype和cache状态，双方各报：GEMM kernel-only、调度prepass+GEMM、完整launcher wall。

全程只读，工作树无改动，#37 未触碰。
