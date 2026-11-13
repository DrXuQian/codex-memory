# Resume brief: 检查 llama.cpp 中 PCCL 未纳入 CUDA Graph 原

- **Thread ID:** `01a185b4-58e3-72d0-a4dc-f7b52d5f2102`
- **Started / last event:** 2026-10-29 03:29 UTC → 2026-11-05 07:01 UTC
- **Working dir:** `/root`
- **Model:** gpt-6-astra  ·  **Source:** vscode  ·  **Codex CLI:** 0.165.0
- **Original rollout:** `/root/.codex/sessions/2026/10/29/rollout-2026-10-29T11-29-11-01a185b4-58e3-72d0-a4dc-f7b52d5f2102.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-10-29_01a185b4_检查-llama-cpp-中-PCCL-未纳入-CUDA-Graph-原.md](../transcripts/2026-10/2026-10-29_01a185b4_检查-llama-cpp-中-PCCL-未纳入-CUDA-Graph-原.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

看一下本地的llama cpp的代码，为什么pccl没有包含在cuda graph中

## Follow-up requests (chronological)

2. (2026-10-29 03:32 UTC) 最小改动的适配版本思考一下
3. (2026-10-29 03:38 UTC) 改动大概多少航
4. (2026-10-29 03:39 UTC) 你这个改法最终事decode是一张cuda graph吗？
5. (2026-10-29 03:39 UTC) 我需要单张
6. (2026-10-29 03:54 UTC) 推送到一个单独的branch，push
7. (2026-10-29 06:16 UTC) 给我command我们测试一下 /sim/eec/shared/AI_workspace/llm-models/bench_model_zoo/DeepSeek-V4-Flash-0731-UD-Q4_K_XL/ DeepSeek-V4-Flash-0731-UD-Q4_K_XL-00001-of-00005.gguf，4卡tp，然后抓asys
8. (2026-10-29 06:44 UTC) 我们从master branch out试试，我想要加一个ppu的backend，GGML_BACKEND_PATH，
9. (2026-10-29 06:45 UTC) 然后我们在这个backend指向的so内部实现ppu的功能，这样不touch原始的llamacpp的代码
10. (2026-10-29 06:45 UTC) 然后我们在这个中间实现一个简单的算子。但是中间加个打印证明调用到了
11. (2026-10-29 06:49 UTC) 不是加法算子，应该是原生的llamacpp中包含的算子。我们在so中替换了
12. (2026-10-29 06:56 UTC) 但是你本地可以编译这个so，最终也调用到，最后报个错可以的
13. (2026-10-29 07:02 UTC) 提交一个新的branch。
14. (2026-10-29 07:06 UTC) so怎么bian yi d？
15. (2026-10-29 07:07 UTC) 这些代码不需要到llama cpp里面，对吗？
16. (2026-10-29 07:08 UTC) 也就是ppu backend下面都可以不再？
17. (2026-10-29 07:12 UTC) 我的意思是如果我们跑一个模型，最终调用了rms norm，我们的代码会覆盖原生的实现？
18. (2026-10-29 07:13 UTC) 如果模型用原声cuda backend，rms norm数据在显存，就不会替换吗？那什么时候替换
19. (2026-10-29 07:14 UTC) 我们就是一种cuda的兼容的ppu
20. (2026-10-29 07:20 UTC) 怎么替换
21. (2026-10-29 07:36 UTC) 如果融合路径的算子我们也替换呢？
22. (2026-10-29 07:47 UTC) 如果要替换整段moe-gemm部分的实现呢？还有linear attention
23. (2026-10-29 07:55 UTC) 没太理解，moe的话我们需要实现什么？
24. (2026-10-29 08:02 UTC) 但是需要修改llamacpp
25. (2026-10-29 08:09 UTC) 如果我们对于权重进行了shuffle，这部分的逻辑怎么实现比较合理？可以不touch原始的代码吗？
26. (2026-10-29 08:11 UTC) 只保留一份
27. (2026-10-29 08:20 UTC) 为什么cuda grpah还是分开的没有生效，是不是有什么开关
28. (2026-10-29 08:37 UTC) 配置之后没看到decode？
29. (2026-10-29 08:38 UTC) 挂了，
30. (2026-10-29 08:39 UTC) #0 0x00007fe35d6d7813 in wait4 () from /lib/x86_64-linux-gnu/libc.so.6 #1 0x00007fe35c9b58f3 in ggml_print_backtrace () from /sim/llama.cpp.1029/build-ci/bin/libggml-base.so.0 #2 0x00007fe35c9b5a9b in ggml_abort () from /sim/llama.cpp.1029/build-ci/bin/libggml-base.so.0#3 0x00007fe34e4ae605 in ggml_quactlize_mul_mat(ggml_backend_cuda_context&, ggml_tensor*) () from /sim/llama.cpp.1029/build-ci/bin/libggml-cuda.so.0 #4 0x00007fe34e34c9cb in ggml_cuda_compute_forward(ggml_backend_cuda_context&, ggml_tensor*) () from /sim/llama.cpp.1029/build-ci/bin/libggml-cuda.so.0 tpgraph为0的时候可以
31. (2026-10-29 08:39 UTC) #5 0x00007fe34e34f08b in ggml_cuda_graph_evaluate_and_capture(ggml_backend_cuda_context*, ggml_cgraph*, bool, bool, void const*) [clone .constprop.0] () from /sim/llama.cpp.1029/build-ci/bin/libggml-cuda.so.0 #6 0x00007fe34e3509fe in ggml_backend_cuda_comm_graph_compute(void*, ggml_cgraph**, unsigned long, unsigned long) () from /sim/llama.cpp.1029/build-ci/bin/libggml-cuda.so.0
32. (2026-10-29 08:50 UTC) 提交到对应的branch
33. (2026-10-29 09:13 UTC) 不同卡的cudagraph launch时间差距很大，
34. (2026-10-29 09:13 UTC) 第一个的pccl灯了非常久，我需要同时launch
35. (2026-10-29 09:28 UTC) 上传了
36. (2026-10-29 09:33 UTC) 你该杀了
37. (2026-10-29 09:33 UTC) 改啥了
38. (2026-10-29 09:34 UTC) 继续
39. (2026-10-29 09:37 UTC) 需要重新编译什么？
40. (2026-10-30 03:20 UTC) 我想要知道如果我只想用GGML_BACKEND_PATH 替换某个kernel的实现到我们自己的优化实现，怎么做？
41. (2026-10-30 03:23 UTC) 其他算子复用原实现，有什么需要改的？需要把所有的代码拷贝过来吗
42. (2026-10-30 03:25 UTC) 那你不就是相当于维护了一套基本上完整的代码吗
43. (2026-11-02 00:59 UTC) 如果想要实现llamacpp的中间表示用bf16？好实现吗？
44. (2026-11-02 00:59 UTC) 我需要最小改动的版本。对于原始的代码侵入越小yue ha。
45. (2026-11-02 00:59 UTC) 因为后期还要rebase
46. (2026-11-02 09:41 UTC) prefill如果也要multithread launch kernel呢？
47. (2026-11-02 09:44 UTC) 添加这个支持
48. (2026-11-05 03:10 UTC) vLLM 与 llama.cpp 的 DeepGemm 并发问题分析（截图转写） 验证完毕，不需要再跑代码。答案清晰了——【vLLM 从两个层面规避了这个问题，而这两个层面恰恰是 llama.cpp 没有的。】 1. 为什么 vLLM 不崩：架构层 + 策略层双保险 层面一（架构层）：【TP 是"多进程"，不是"多线程共享进程内缓存"。】 我们复现崩溃的核心是：kernel_runtime_cache 是文件作用域 static 的进程全局 unordered_map，4 个 TP rank 在同一个进程里无锁并发改它。vLLM 里 TP/NCCL rank 是各自独立进程（每卡一进程，torchrun/NCCL），所以每个进程里的 kernel_runtime_cache 各有一份、互不共享——根本不存在"多线程同时写同一个全局 map"这个前提。这是结构性差异。 层面二（策略层）：【warmup 在 compile_mode=1 下、单线程、逐 shape 串行把所有 kernel 预编译掉。】 kernel_warmup.py:179：PPU 平台在 CUDA(PPU) Graph capture 之前，逐个模型遍历所有可能用到的分组/稠密 GEMM shape（fp8/int8/bf16/fp4/w4a16/masked 全量或 relax 抽点），一次性调用 DeepGemm 把这些 kernel 全部 JIT build 进 cache（见 ppu_deep_gemm_warmup.py:135 set_compile_mode(1)，这是 DeepGemm 延迟编 …
49. (2026-11-05 03:17 UTC) 有没有不touch 算子库本身的方法
50. (2026-11-05 03:28 UTC) 也就是第一次有时间差？还是每次都有
51. (2026-11-05 03:29 UTC) 如果runtime调用的get sm之类的呢
52. (2026-11-05 03:32 UTC) 为什么多线程调用这些会有问题？因为写同一块cpu内存？多进程为什么没有这个问题
53. (2026-11-05 03:34 UTC) 如果只是launch kernel的时候多线程，怎么操作呢
54. (2026-11-05 07:00 UTC) llama.cpp本身的cuda代码是什么开源协议？

## Files edited via apply_patch (most frequent first)

- `/root/llama.cpp/ggml/src/ggml-cuda/ggml-cuda.cu` ×5
- `/root/llama.cpp/tests/test-tp-graph.cpp` ×5
- `/root/llama.cpp-ppu-backend/ppu-backend/ggml-ppu.cpp` ×5
- `/root/llama.cpp/tests/CMakeLists.txt` ×4
- `/root/llama.cpp/docs/multi-gpu.md` ×4
- `/root/llama.cpp-ppu-backend/ppu-backend/runtime.cu` ×2
- `/root/llama.cpp-ppu-backend/ppu-backend/runtime.h` ×2
- `/root/llama.cpp-ppu-backend/ppu-backend/host-test-runtime.cpp` ×2
- `/root/llama.cpp-ppu-backend/ppu-backend/demo.cpp` ×2
- `/root/llama.cpp-ppu-backend/ppu-backend/CMakeLists.txt` ×2
- `/root/llama.cpp-ppu-backend/ppu-backend/README.md` ×2
- `/root/llama.cpp/ggml/src/ggml-cuda/tp-graph-launch.h` ×2
- `/root/llama.cpp/ggml/include/ggml-backend.h` ×1
- `/root/llama.cpp/ggml/src/ggml-backend-meta.cpp` ×1
- `/root/llama.cpp-ppu-backend/ppu-backend/.gitignore` ×1
- `/root/llama.cpp-tp-kpack-fix/ggml/src/ggml-cuda/ggml-cuda.cu` ×1
- `/root/llama.cpp/ggml/src/ggml-cuda/CMakeLists.txt` ×1
- `/root/llama.cpp/ggml/src/ggml-cuda/gated_delta_net.cu` ×1
- `/root/llama.cpp/ggml/src/ggml-cuda/ncp-route.cuh` ×1
- `/root/llama.cpp/ggml/src/ggml-cuda/fattn.cu` ×1

## Last assistant conclusions

### 2026-11-05 03:33 UTC

**对，核心就是多个线程共享同一份 CPU 内存，却在没有同步的情况下读写它。** 不仅“两个线程同时写”有问题，“一个读、一个写”也可能出错。

拿这份 `get_num_sms()` 来说，它的初始化顺序是：

```cpp
_num_sms = new int(0);       // 指针先变成非空
查询设备属性();
*_num_sms = 实际SM数量;      // 最后才填入正确值
```

可能出现：

1. 线程 A 刚分配完，准备查询设备。
2. 线程 B 看到指针非空，以为初始化完成。
3. 线程 B 读到 **0**，用错误的 SM 数量选择配置或计算 launch 参数。

`unordered_map` 的问题更严重：一个线程正在查找，另一个线程插入并触发扩容，内部桶和节点关系发生变化，查找线程就可能访问失效的内存。C++ 中这属于数据竞争，结果没有保证。

**多进程为什么能避开？因为普通全局变量按进程隔离。**

| 执行方式 | CPU 端缓存 |
|---|---|
| 一个进程、四个 TP 线程 | 四个线程访问同一份 `kernel_runtime_cache`、`_num_sms` |
| 四个进程、每个进程一个 TP rank | 每个进程分别拥有自己的缓存和变量 |

即使四个进程加载的是同一个 `.so`，其普通可写全局变量也各有一份；共享库的代码可以共享，变量状态并不会自动共享。

所以，**把线程绑定到不同 GPU，并不能隔离 CPU 端的全局变量。** 多进程隔离解决的是这类进程内缓存竞争；如果使用显式共享内存或共同写磁盘 JIT 缓存，仍然需要相应的同步机制。

### 2026-11-05 03:36 UTC

**可以，做成“串行准备、并行 launch”两阶段。各卡线程只拿准备好的句柄和参数，直接调用底层 launch API。**

流程是：

```cpp
// 主线程：串行完成所有可能修改共享缓存的工作
for (int rank = 0; rank < 4; ++rank) {
    jobs[rank] = prepare_for_rank(rank, ...);
}

// 常驻线程：统一放行，每个线程只提交本卡任务
workers.run([&](int rank) {
    launch_prepared(jobs[rank]);
});
```

这里是接口示意，具体分工如下：

| 串行准备阶段 | 并行 launch 阶段 |
|---|---|
| 查询 SM、选择 kernel 配置 | 绑定对应设备/上下文 |
| JIT、缓存查询和插入 | 读取已准备好的 kernel 句柄 |
| 加载模块、取得函数句柄、设置函数属性 | 使用各自的参数包和 stream 提交 |
| 分配 workspace、构造参数 | 返回，不额外同步 GPU |

准备工作完成后再释放线程，可以减少冷初始化造成的卡间提交差距。参数包需要每卡独立，模块和设备缓冲区也要保持有效。

**当前接口的限制是：llama.cpp 调用的 DeepGemm 入口把准备和 launch 合在一次调用里，没有返回可直接执行的 plan。** 内部虽然有 `compiler->build()` 和 `Runtime::launch()`，但本地的 [launch 包装](/root/marlin_ppu/DeepGEMM-for-sail/csrc/jit/kernel_runtime.hpp:81) 还会构造配置，而且固定使用默认 stream，不能直接当成上述纯 launch 接口。

因此有两种落地方式：

- **保持算子库二进制不动：串行预热、串行 CUDA Graph capture，随后四线程并行 `cudaGraphLaunch`。** 图保存了执行所需的信息，replay 不再进入 DeepGemm 的主机准备路径。适用于能够 capture 的 prefill/decode 路径。
- **普通 kernel 直接并行提交：在我们自己的适配层提供 `prepare/launch` 接口。** 需要能取得 kernel 句柄并正确构造参数；现有黑盒算子接口无法仅靠换线程完成这个拆分。

按你“少改代码、方便 rebase”的要求，**能够 capture 的部分优先采用第一种方式。**

### 2026-11-05 07:01 UTC

**llama.cpp 自身的 CUDA backend 代码采用 MIT 协议**，包括 `ggml/src/ggml-cuda/` 中的原生实现。见[官方 LICENSE](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE)。

对你们的用途，MIT 允许：

- 复制、修改、移植到 PPU，以及商业使用。
- 编译成闭源 `.so`，无需公开修改，也无需提交上游。
- 分发时须保留原版权声明和 MIT 许可证文本，包括免责条款。[MIT 条款](https://opensource.org/license/mit)

CUDA Runtime、cuBLAS、DeepGemm 等第三方依赖，则分别遵循各自的许可证。
