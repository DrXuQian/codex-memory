# Resume brief: REVIEW ONLY — 不要编辑任何文件,不要 git add/commit。你手上还拿着 INBOX 088 的四个文件,这是一个旁路只读任务,做完直接把结论写在回答里。

请攻击 quactlize 里 MoE grouped GEMM 的 MFU 和带宽利用率计算方法。代码在 `benchmarks/lowbit_moe_bench.hpp` 的 `report()`(约 280-355 行)。当前公式:

    mt      = Σ_e ceil(me[e] / TM)          # m-tile 总数,me[e] = 第 e 个 expert 的真实行数
    masked  = 1 - total / (TM * mt)         # total = Σ_e me[e]
    wb      = N * K * bits_total / 8        # 一个 expert 的权重字节
    sb      = N * (K / gs) * 2 * 2          # scale + zero,fp16
    a_dram  = total * K * 2                 # A:每个真实行一次
    dfl     = a_dram + active * (wb + sb) + total * N * 2
    gbs     = dfl / (us*1e-6) / 1e9         ;  HBM% = gbs / 2766.0
    tf      = 2 * total * N * K / (us*1e-6) / 1e12  ;  MFU = tf / 500e12

今天刚改了两处,请重点审这两个决定:
1. HBM 的分子原来是 `mt*TM*K*2`(**padding 后的 A 行数**),我换成了 `total*K*2`。理由:padding 行要么越界从不发出、要么是同样的 cache line,总线不搬它们。这个理由站得住吗?反例是什么?具体地:cutlass 的 predicated tile iterator 在 M 方向越界时到底是不发 load 还是发了再丢弃?如果是后者,DRAM 是否仍然要交付那些 line(取决于它们是否落在已经被真实行触及的 128B line 内)?
2. MFU 的分子是 `2*total*N*K`(**真实行**),我拒绝了"按机器实际算的行数 `TM*mt` 折算"的第二个数字。理由:padding 是 kernel 自己选的开销,必须记在它头上,否则这个指标对"decode 用了过大的 TileM"这个缺陷保持沉默。

还要审这些:
- `sb` 假设每个 gs 组都带 scale **和** zero 各一个 fp16。ScaleOnly 路径没有 zero,这个式子会高估 scale 通道。它在 `dfl` 里占比多大?值不值得按实际 KernelScale 类型分开?
- `active`(活跃 expert 数)乘 `(wb+sb)`,即"每个活跃 expert 的权重恰好读一次"。在非持久化调度、同一 expert 的多个 m-tile 分布在不同 CU 上时,这是下界还是等式?L2 能不能保证?
- `bits_total` 对双平面格式(Q3=int2+int1, Q5=int4+int1, Q6=int4+int2)是两个平面之和吗?如果 scale 平面对两个 B 平面共享,`sb` 是不是被算了两次?
- C 的 `total*N*2`:输出是 fp16 且每行写一次,对吗?有没有 split-K 的中间写回没算进去?
- HBM 峰值常数 2766 GB/s 和 PEAK 500 TF/s 是否是 ppu001 的正确值。
- 分母是墙钟 `us`。如果 kernel 是 launch-bound(bench 里有 `bench_floor::launch_bound()`),把 launch 开销算进带宽分母会把利用率压低多少?该不该扣?

要具体:指出哪一条是**错的**(不是"可以更精确"),给出反例或推导。你认为我上面两个改动哪个是错的,直接说。

- **Thread ID:** `019fdb3a-cbd7-7163-bbde-71886d2860fc`
- **Started / last event:** 2026-08-07 07:58 UTC → 2026-08-07 08:22 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/07/rollout-2026-08-07T15-58-11-019fdb3a-cbd7-7163-bbde-71886d2860fc.jsonl`
- **Subagents spawned:** 3 (not exported)
- **Git:** `{"commit_hash": "e3ec14de8d9cbd49108fb8805050cfdc12d4c634", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-07_019fdb3a_REVIEW-ONLY-不要编辑任何文件-不要-git-add-commit-你手上还拿着-INBO.md](../transcripts/2026-08/2026-08-07_019fdb3a_REVIEW-ONLY-不要编辑任何文件-不要-git-add-commit-你手上还拿着-INBO.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

REVIEW ONLY — 不要编辑任何文件,不要 git add/commit。你手上还拿着 INBOX 088 的四个文件,这是一个旁路只读任务,做完直接把结论写在回答里。

请攻击 quactlize 里 MoE grouped GEMM 的 MFU 和带宽利用率计算方法。代码在 `benchmarks/lowbit_moe_bench.hpp` 的 `report()`(约 280-355 行)。当前公式:

    mt      = Σ_e ceil(me[e] / TM)          # m-tile 总数,me[e] = 第 e 个 expert 的真实行数
    masked  = 1 - total / (TM * mt)         # total = Σ_e me[e]
    wb      = N * K * bits_total / 8        # 一个 expert 的权重字节
    sb      = N * (K / gs) * 2 * 2          # scale + zero,fp16
    a_dram  = total * K * 2                 # A:每个真实行一次
    dfl     = a_dram + active * (wb + sb) + total * N * 2
    gbs     = dfl / (us*1e-6) / 1e9         ;  HBM% = gbs / 2766.0
    tf      = 2 * total * N * K / (us*1e-6) / 1e12  ;  MFU = tf / 500e12

今天刚改了两处,请重点审这两个决定:
1. HBM 的分子原来是 `mt*TM*K*2`(**padding 后的 A 行数**),我换成了 `total*K*2`。理由:padding 行要么越界从不发出、要么是同样的 cache line,总线不搬它们。这个理由站得住吗?反例是什么?具体地:cutlass 的 predicated tile iterator 在 M 方向越界时到底是不发 load 还是发了再丢弃?如果是后者,DRAM 是否仍然要交付那些 line(取决于它们是否落在已经被真实行触及的 128B line 内)?
2. MFU 的分子是 `2*total*N*K`(**真实行**),我拒绝了"按机器实际算的行数 `TM*mt` 折算"的第二个数字。理由:padding 是 kernel 自己选的开销,必须记在它头上,否则这个指标对"decode 用了过大的 TileM"这个缺陷保持沉默。

还要审这些:
- `sb` 假设每个 gs 组都带 scale **和** zero 各一个 fp16。ScaleOnly 路径没有 zero,这个式子会高估 scale 通道。它在 `dfl` 里占比多大?值不值得按实际 KernelScale 类型分开?
- `active`(活跃 expert 数)乘 `(wb+sb)`,即"每个活跃 expert 的权重恰好读一次"。在非持久化调度、同一 expert 的多个 m-tile 分布在不同 CU 上时,这是下界还是等式?L2 能不能保证?
- `bits_total` 对双平面格式(Q3=int2+int1, Q5=int4+int1, Q6=int4+int2)是两个平面之和吗?如果 scale 平面对两个 B 平面共享,`sb` 是不是被算了两次?
- C 的 `total*N*2`:输出是 fp16 且每行写一次,对吗?有没有 split-K 的中间写回没算进去?
- HBM 峰值常数 2766 GB/s 和 PEAK 500 TF/s 是否是 ppu001 的正确值。
- 分母是墙钟 `us`。如果 kernel 是 launch-bound(bench 里有 `bench_floor::launch_bound()`),把 launch 开销算进带宽分母会把利用率压低多少?该不该扣?

要具体:指出哪一条是**错的**(不是"可以更精确"),给出反例或推导。你认为我上面两个改动哪个是错的,直接说。

## Last assistant conclusions

### 2026-08-07 08:22 UTC

直说：两个“换分子”的决定都不该回滚。

- 改动 2 正确：MFU 应只算真实模型工作 `2*total*N*K`。padding 是实现开销，必须通过时间反映为 MFU 下降。
- 改动 1 中，`mt*TM` 换成 `total` 也正确——但它算的是 A 的“有效/唯一字节”，不是实际 HBM 字节。错的是继续把 `dfl/us` 称为物理 `HBM%`，以及“traffic locked/exact”的结论。旧的 padded-A 分子更错。

## A 的 predication

当前 MoE A 路径其实不是传统 CUTLASS `PredicatedTileIterator`，而是 AIU bulk tensor copy：

- descriptor 的 `dim_h=M_e`、`cube_h=TileM`：[copy_aiu_base.hpp](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/arch/copy_aiu_base.hpp:65)
- grouped `load_init()` 把真实 expert M 传进去：[ppu_mma_aiu_mixed_input_2plane.hpp](/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp:631)
- 实际指令是 `.padz...2d.b16`：[copy_ppu0010_aiu.hpp](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/arch/copy_ppu0010_aiu.hpp:58)
- collective 自己明确写了 M=1 时“fetches exactly one row and zero-fills the rest”：[quactlize_mma_mixed_input.hpp](/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp:436)

所以它不是“先发 TileM 行 load，再把越界结果丢掉”；越界元素由 `.padz` 产生零。硬件内部是否会对有效边界做 cache-line overfetch，C++ 源码不能证明，需要计数器，但这不等于读取完整 padding 行。

传统 CUTLASS iterator 更直接：`valid()` 被传给 `global_load`：[predicated_tile_iterator.h](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/transform/threadblock/predicated_tile_iterator.h:346)，汇编是 `@p ppu.ld.global...`：[memory.h](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/arch/memory.h:153)。predicate=false 时 load 指令不执行，不是 load 后 discard。

“padding 行反正是同一个 128B line”这个理由则是错的。反例：`K=2048, fp16` 时一行是 4096B，即 32 条 128B line；第二行完全是另外 32 条 line。若真发出 padding load，L2 miss 就必须让 DRAM 交付这些 line。只有地址确实落在真实访问已带入的同一 line 且仍在 cache 时，才不增加 HBM。

因此：

- `total*K*2`：正确的有效/唯一 A payload。
- `mt*TM*K*2`：对当前 `.padz` 路径不是 compulsory DRAM bytes。
- 实际 HBM A 流量：仍可能因跨 N-tile 重读、L2 命中、128B line amplification 而高于或低于该值。

## `active*(wb+sb)` 不是实际 HBM 等式

令 `t_e=ceil(me[e]/TM)`。三个不同口径必须分开：

- 唯一逻辑 footprint：`active*(wb+sb)`。
- 不依赖跨 M-tile cache reuse 的 global-request payload：`Σ_e t_e*(wb+sb) = mt*(wb+sb)`。
- 实际 DRAM：由 L2 初始状态、容量、冲突、并发 miss 合并和 transaction 大小决定。

在 decode 时 `t_e=1`，所以 B/S 在单次 kernel 的逻辑 load 域确实只覆盖一次；但不能推导“每个 expert 从 HBM 恰好读一次”：

- 计时前有同一 buffer 的 warmup：[lowbit_moe_bench.hpp](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:208)，整套权重若部分驻留 L2，本次 HBM 可能少于一次。
- 多个 M-tile 分布到不同 CU 时，L2 只保证共享/一致性，不保证保留到下一 CTA，也不保证一次 DRAM miss。
- 反过来，冷 cache、容量/冲突 miss 会使同一 expert 的权重多次到 HBM。

所以 [moe_row_ran()](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:359) 把 `active*wb` 称为“least it can possibly have moved”，并据此把有效 GB/s 超过 2766 的行判为 DID NOT RUN，是确定性错误。cache-hot 合法 kernel 完全可以超过“HBM-equivalent 100%”。

同样，[`dce`](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:315) 里的 A 应至多按 `ntile*total*K*2` 的有效请求算，不应再用 `ntile*a_pad`。而 32B 有效请求导致 128B line fill 时，bus 可以饱和但有效带宽只有 25%；因此 `gbs_c < 0.9*peak => NOT-BW` 也不是可靠判据。

## MFU

真实行 MFU 是正确口径。它回答的是模型完成了多少有用 FLOP：

\[
\mathrm{MFU}_{useful} =
\frac{2\,total\,N\,K/t}{500\text{ TF/s}}
\]

padding 行如果拖慢 kernel，就自然降低这个数；不能把 `TM*mt` 填回去“原谅”它。

可以另报诊断性的 issued tensor-op utilization，但不能替代 MFU。若 N/K 也可能有尾块，完整 issued FLOP 应是：

\[
2\,(TM\cdot mt)\,
(TN\lceil N/TN\rceil)\,
(TK\lceil K/TK\rceil)
\]

只有 N、K 整除时才退化成 `2*TM*mt*N*K`。当前 `masked` 已经是更清楚的 M-padding 诊断。

另外，代码的单位是对的：`tf` 已是 TF/s，所以 MFU 是 `tf/500`。问题中若按字面写成 `tf/500e12`，会错 1e12；源码实际通过 `tf*1e12/PEAK` 抵消了。

## Scale、双平面和 C

`sb` 在 ScaleOnly 下是确定性错误，值得按实际模式分开，不只是“更精确”。

令 `G=ceil(K/gs)`：

- ScaleZero：`N*G*4` bytes/expert。
- ScaleOnly：`N*G*2` bytes/expert。

完整 ScaleOnly 正确分母应为：

\[
2\,total\,K +
active\,(NK\,bits/8 + 2NG) +
2\,total\,N
\]

当前多算了 `active*2NG`。在 decode、权重项占主导时：

- 默认 `gs=32`：Q3/Q5/Q6 的当前 S+Z 项约占 25.0% / 16.7% / 14.3%；ScaleOnly 总 `dfl` 分别被高估约 14.3% / 9.1% / 7.7%。
- 若采用 Q3/Q5/Q6 常见的 `gs=16/32/16`，高估约 25.0% / 9.1% / 14.3%。

模式在编译期已经明确区分：[ppu_mixed_policy.hpp](/root/marlin_ppu/quactlize/quactlize/include/ppu_mixed_policy.hpp:22)，ScaleOnly tuple 确实没有 zero，因此应当分开。另有一个条件问题：kernel 用 `ceil(K/gs)`，报告用 `K/gs`；默认整除时无影响，任意 CLI K 时会少算，测试分配也可能不足。

`bits_total` 对双平面取和是正确的：

- Q3 = 2+1
- Q5 = 4+1
- Q6 = 4+2

scale/zero 是两个 B plane 共享的一套，当前 `sb` 只在 `dfl` 中出现一次，没有重复计算。2-plane collective 也只建立一个 gS、可选一个 gZ：[ppu_mma_aiu_mixed_input_2plane.hpp](/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp:669)。

不过 `report()` 的 `run=` 诊断用 `bits_total` 把双平面当成一个连续 b-bit plane，是错的。以 Q3/TK64 为例，实际是 int2 plane 的 32B run 加 int1 plane 的 32B run；当前会打印不存在的 24B combined run。

`total*N*2` 对当前路径是正确的逻辑输出字节：D 是 fp16、beta=0、真实元素各写一次，而且 benchmark 明确传 `splitk=1`：[lowbit_moe_bench.hpp](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:483)。若把同一公式用于 S>1 split-K，则会少算：

- S 份 partial 写：`S*D`
- merge 读：`S*D`
- final 写：`D`

总计 `(2S+1)*D`，即当前公式之外还差 `2S*D`。

## 峰值和墙钟分母

`500 TF/s` 和 `2766 GB/s` 在仓库内是一致的 ppu001 名义峰值：[BACKTEST.md](/root/marlin_ppu/quactlize/docs/BACKTEST.md:11)、[CHECKPOINT.md](/root/marlin_ppu/quactlize/docs/CHECKPOINT.md:15)。所以：

- 500 作为 FP16 nameplate MFU 分母合理。
- 2766 作为 nameplate HBM% 分母合理。
- 它们不是可持续实测 roof。仓库另有 bw_probe 约 2200 GB/s；若实际可持续峰是 2200，饱和时按 2766 只显示 79.5%。最好明确称 nameplate%，不能称“总线实际利用率”。

launch/setup 对结果的压低比例只能写成：

\[
\frac{U_{wall}}{U_{kernel}}=\frac{t_{kernel}}{t_{wall}}
\]

没有 device timing 就不能给固定百分比，也不能用 empty-launch floor 相减。纯异步 uniform 路径下，稳态近似 `t_wall≈max(t_kernel,t_issue)`；若 kernel 只需 launch interval 的一半，墙钟利用率就是 device-only 的约一半。

当前 ragged/decode 更严重：每个 timed call 都重做 initialize、构造 prefix，并执行 blocking H2D copy：[moe_grouped_ppu.cuh](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:317)。源码明确说该 copy 会 serialise host：[moe_grouped_ppu.cuh](/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh:91)。而 `bench_floor` 只排队 raw nop kernels：[bench_floor.cuh](/root/marlin_ppu/quactlize/benchmarks/bench_floor.cuh:57)，两者并非同一 loop shape。

所以：

- 若要端到端 operator 指标：保留 wall `us`，但名称应是 end-to-end useful MFU / effective GB/s。
- 若要 grouped GEMM kernel 的 MFU/HBM：不能扣一个 launch floor；应把 prefix/setup 移出计时，或用 device event/ACU DRAM counters 单独测 kernel。
- `launch_bound(row<3f)` 只能作警告，不能量化修正，而且对当前 ragged 路径会漏报。

最后还有明确的陈旧矛盾：[`report()` 前半注释](/root/marlin_ppu/quactlize/benchmarks/lowbit_moe_bench.hpp:293) 仍说 padded A compulsory，而最终 banner 仍打印 padded A、traffic LOCKED：[test_lowbit_moe_bench.cu](/root/marlin_ppu/quactlize/benchmarks/test_lowbit_moe_bench.cu:265)。这些文字现在都是错的。

按要求，本次只读审查，未修改、暂存或提交任何文件。
