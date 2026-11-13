# Resume brief: 只要分析,不要改代码,不碰 #37 的收尾。

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

Full transcript: [2026-08-10_019fe931_只要分析-不要改代码-不碰-37-的收尾-题目-对比-DeepGemm-的-MoE-grouped.md](../transcripts/2026-08/2026-08-10_019fe931_只要分析-不要改代码-不碰-37-的收尾-题目-对比-DeepGemm-的-MoE-grouped.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

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

## Last assistant conclusions

### 2026-08-10 01:24 UTC

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

**DeepGem
… [truncated 2776 chars]
