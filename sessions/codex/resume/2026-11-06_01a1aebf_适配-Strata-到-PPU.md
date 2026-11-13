# Resume brief: 适配 Strata 到 PPU

- **Thread ID:** `01a1aebf-6413-7471-b589-6b1ed751bc7c`
- **Started / last event:** 2026-11-06 02:46 UTC → 2026-11-11 07:35 UTC
- **Working dir:** `/root`
- **Model:** gpt-6-astra  ·  **Source:** vscode  ·  **Codex CLI:** 0.166.0
- **Original rollout:** `/root/.codex/sessions/2026/11/06/rollout-2026-11-06T10-45-41-01a1aebf-6413-7471-b589-6b1ed751bc7c.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-11-06_01a1aebf_适配-Strata-到-PPU.md](../transcripts/2026-11/2026-11-06_01a1aebf_适配-Strata-到-PPU.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

https://github.com/DrXuQian/Strata 参考本碟llamacpp的改动适配到ppu，修改strata以适配ppu。

## Follow-up requests (chronological)

2. (2026-11-06 02:49 UTC) 假设已经有ncp flash lib，接口你可以看到从llamacpp中
3. (2026-11-06 02:50 UTC) Qwen3.8-flash-next
4. (2026-11-06 03:15 UTC) strata的moe offload，是遇到了再去取？没有prefetch？
5. (2026-11-06 03:15 UTC) 预测是怎么预测的？
6. (2026-11-06 03:16 UTC) 了解，继续
7. (2026-11-06 03:41 UTC) 最终给我上box实测
8. (2026-11-06 03:44 UTC) 我们还是以共享ncp flash lib中的几个库为前提，参考llamacpp修改strata
9. (2026-11-06 03:44 UTC) 最后给我command就行，box你没有访问权限
10. (2026-11-06 03:59 UTC) 不要patch，直接推送到我的fork
11. (2026-11-06 04:04 UTC) setup.py if why: (warn if cuda_tk == 13 or str(a.cuda) == "12" else ok)(f"CUDA {cuda_tk}: {why}") min_driver = CUDA12_COMPAT_DRIVER if cuda_tk == 12 else MIN_DRIVER if driver_major(gpu) < min_driver: if driver_major(gpu) < min_driver and os.environ.get("STRATA_SKIP_DRIVER_CHECK") != "1": fail(f"the NVIDIA driver is too old ({gpu['driver']}; {min_driver} or newer is needed)" + ("" if cuda_tk == 12 else f" (the CUDA 12 engine package needs {cuda12_min_driver()[1]} or newer, {cuda12_min_driver()[2]})"), "update it with the NVIDIA App or from https://www.nvidia.com/drivers, restart, and run this again") exl3.cu src/dsv41/vendor/ constexpr int W = 8 * K; __shared__ __align__(16) unsigned char sm[ …
12. (2026-11-06 04:31 UTC) 现在提交了哪些修改了哪些列一个表格
13. (2026-11-06 04:33 UTC) quactlize的加载需要onlineshuffle，这部分逻辑没改吧
14. (2026-11-06 04:34 UTC) 接入quactlize
15. (2026-11-06 06:52 UTC) 为什么还要llamacpp的path
16. (2026-11-06 07:22 UTC) 确定需要吗？原始的strata也需要？
17. (2026-11-06 07:29 UTC) --pack /path/to/strata-pack \ 是什么
18. (2026-11-06 07:33 UTC) 那我们也离线pack好了啊
19. (2026-11-06 08:40 UTC) CMake Error at cmake/ppu_backend.cmake:29 (message): PPU requires an explicit CMAKE_CUDA_ARCHITECTURES supported by the selected SDK; no NVIDIA auto-detection Call Stack (most recent call first): CMakeLists.txt:12 (include)
20. (2026-11-06 09:47 UTC) /sim/eec/shared/AI_workspace/llm-models/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL ls /sim/eec/shared/AI_workspace/llm-models/MTP-GGUF-modelzoo/Qwen3.8-Flash-Next-MTP/ mtp-inventory.json mtp-inventory.md mtp-manifest.json mtp-q2_0.gguf mtp-q2_0.gguf.report.json rt tensors root@aiswu52:/sim/eec/shared/junfu.qx/llama.cpp.ncp#
21. (2026-11-06 13:25 UTC) 还是改成都用pip install的里面的so可以嘛？
22. (2026-11-06 13:25 UTC) strata能直接用嘛？
23. (2026-11-06 13:25 UTC) 比如flash attention安装之后的so
24. (2026-11-06 13:26 UTC) 需要怎么适配？这样能够让strata之后我们更新算子，直接pip install就行了
25. (2026-11-06 13:27 UTC) 不要把适配放到算子包里面，可以strata中包含一个ppu的适配层
26. (2026-11-06 13:27 UTC) 算子就是直接安装，不改任何东西
27. (2026-11-06 13:28 UTC) 可以嘛？入口除了原来是torch tensor之外，其他的没有什么区别吧
28. (2026-11-06 13:30 UTC) 源码就是flash-attention-for-sail
29. (2026-11-06 13:30 UTC) 你可以直接看到吧
30. (2026-11-06 13:31 UTC) deepgemm-for-sail同理，
31. (2026-11-06 13:31 UTC) actlizeLA和quactlize也一样
32. (2026-11-06 13:38 UTC) host包+jit就可以了啊
33. (2026-11-06 13:39 UTC) deepgemm也是一回事
34. (2026-11-06 13:42 UTC) 开始适配，去掉之前的C ABI的方法
35. (2026-11-06 13:43 UTC) 要完全适配完
36. (2026-11-08 03:16 UTC) rebsae
37. (2026-11-08 03:16 UTC) rebase到最新的remote
38. (2026-11-08 03:58 UTC) 给我本地的ai一个prompt，如何安装侧视，本地是一个610，48GB的显存
39. (2026-11-08 04:00 UTC) 610也是ppu10
40. (2026-11-09 06:59 UTC) Strata 已经在本机 PPU1（PPU-ZW610，按 ppu10 准入）上装好并跑通，包括 --prepare、全部 host 检查、15 项设备 parity 和 A/B/C 端到端对照，三组输出一致。剩下一个问题：serve 模式用默认参数时，开启 provider 的 B/C 第一个请求就报错，要加 --lookup-max-t 6 才能正常运行（见“未验证项与限制”第 1 条）。完整报告在 REPORT.md，可复制的命令在第 11 节。 代码与提交 分支 ppu/qwen38-ncp，HEAD c2be8594 = 基线 5af755f8 + 5 个本地提交，没有 push： 4b66e9c8：actlizeLA 0.2.2 只认 ZW810/ZW890。actlizeLA 拒绝后，只有真实设备名 PPU-ZW610、cc 8.0、target ppu10 三项都满足才放行。算子包没改，也没伪造设备信息。 af31655c：run_box.sh 判断 pack 是否完成用错了文件，导致每次都重新打包。 6996de6b：parity 通过时也打印误差，判定和容差不变。 adaa572f：修了 box run 的三个问题：调用了不存在的 generate 子命令；--gpu 0 写死，会让模型跑到另一张卡；trace 运行缺 profile。 c2be8594：C 组用离线 K-pack 时，在图捕获前预留 QUactlize 的 scratch。修复前 C 组会 double free 崩溃。 补丁在 reports/patches/，依次应用到 5af755f …
41. (2026-11-09 08:05 UTC) 拉一下
42. (2026-11-11 07:30 UTC) 告诉我新的机器上的command，来安装测试strata。810E
43. (2026-11-11 07:30 UTC) 直接给我promtp就行了

## Files edited via apply_patch (most frequent first)

- `/workspace/strata-ppu/Strata/docs/PPU.md` ×14
- `/workspace/strata-ppu/Strata/include/strata/ppu/kernels.hpp` ×7
- `/workspace/strata-ppu/Strata/CMakeLists.txt` ×7
- `/workspace/strata-ppu/Strata/src/ppu/quactlize.cu` ×7
- `/workspace/strata-ppu/Strata/src/ppu/kernels.cu` ×6
- `/workspace/strata-ppu/Strata/src/core/native_head.cpp` ×6
- `/workspace/strata-ppu/Strata/tests/ppu/ncp_parity.cu` ×5
- `/workspace/strata-ppu/Strata/tools/ppu/check.sh` ×5
- `/workspace/strata-ppu/Strata/include/strata/ppu/quactlize.hpp` ×4
- `/workspace/strata-ppu/Strata/src/core/native_dense.cpp` ×4
- `/workspace/strata-ppu/Strata/tests/ppu/quactlize_parity.cu` ×4
- `/workspace/strata-ppu/Strata/python/strata_ppu/adapter.py` ×4
- `/workspace/strata-ppu/Strata/tests/ppu/mock_ncp.cpp` ×3
- `/workspace/strata-ppu/Strata/tests/ppu/test_loader.py` ×3
- `/workspace/strata-ppu/Strata/src/kernels/cuda/verify_kernels.cu` ×3
- `/workspace/strata-ppu/Strata/src/prefill/prefill.cpp` ×3
- `/workspace/strata-ppu/Strata/python/strata_ppu/jit.py` ×3
- `/workspace/strata-ppu/Strata/include/strata/ppu/ncp.hpp` ×2
- `/workspace/strata-ppu/Strata/src/ppu/ncp.cpp` ×2
- `/workspace/strata-ppu/Strata/cmake/ppu_backend.cmake` ×2
- `/workspace/strata-ppu/Strata/src/kernels/cuda/gdn.cu` ×2
- `/workspace/strata-ppu/Strata/src/kernels/cuda/fused_gdn.cu` ×2
- `/workspace/strata-ppu/Strata/src/core/verify.cpp` ×2
- `/workspace/strata-ppu/Strata/src/dsv41/vendor/exl3.cu` ×2
- `/workspace/strata-ppu/Strata/src/ppu/quactlize.cpp` ×2
- `/workspace/strata-ppu/Strata/src/kernels/cuda/iq_kernels.cu` ×2
- `/workspace/strata-ppu/Strata/src/ppu/offline.cpp` ×2
- `/workspace/strata-ppu/Strata/include/strata/ppu/offline.hpp` ×2
- `/workspace/strata-ppu/Strata/tools/ppu/pack.cu` ×2
- `/workspace/strata-ppu/Strata/src/ppu/offline_experts.cpp` ×2
- `/workspace/strata-ppu/Strata/python/strata_ppu/native/quact.cu` ×2
- `/workspace/strata-ppu/Strata/tests/ppu/fetch_admission_test.cpp` ×2
- `/workspace/strata-ppu/Strata/tests/ppu/loader_test.cpp` ×1
- `/workspace/strata-ppu/Strata/src/kernels/cuda/native_gdn.cu` ×1
- `/workspace/strata-ppu/Strata/src/prefill/kernels.cu` ×1
- `/workspace/strata-ppu/Strata/src/kernels/cuda/native_mmvq.cu` ×1
- `/workspace/strata-ppu/Strata/docs/SOURCE_INSTALL.md` ×1
- `/workspace/strata-ppu/target_probe.cu` ×1
- `/workspace/strata-ppu/Strata/setup.py` ×1
- `/workspace/strata-ppu/Strata/src/prefill/gemm.cu` ×1
- `/workspace/strata-ppu/Strata/tests/ppu/test_quactlize_loader.py` ×1
- `/workspace/strata-ppu/Strata/tests/ppu/mock_quactlize.cpp` ×1
- `/workspace/strata-ppu/Strata/tests/ppu/quactlize_loader_test.cpp` ×1
- `/workspace/strata-ppu/Strata/include/strata/ppu/quactlize/README.md` ×1
- `/workspace/strata-ppu/Strata/include/strata/kernels/iq_kernels.hpp` ×1
- `/workspace/strata-ppu/Strata/include/strata/ppu/offline_experts.hpp` ×1
- `/workspace/strata-ppu/Strata/include/strata/ppu/python.hpp` ×1
- `/workspace/strata-ppu/Strata/src/ppu/python.cpp` ×1
- `/workspace/strata-ppu/Strata/python/strata_ppu/__init__.py` ×1
- `/workspace/strata-ppu/Strata/python/strata_ppu/native/adapter.hpp` ×1
- `/workspace/strata-ppu/Strata/python/strata_ppu/native/tensor_module.cpp` ×1
- `/workspace/strata-ppu/Strata/tests/ppu/bridge_test.cpp` ×1
- `/workspace/strata-ppu/Strata/tests/ppu/test_bridge.py` ×1
- `/workspace/strata-ppu/Strata/python/strata_ppu/__main__.py` ×1
- `/workspace/strata-ppu/Strata/tests/ppu/test_packages.py` ×1
- `/workspace/strata-ppu/Strata/src/core/expert_source.cpp` ×1
- `/workspace/strata-ppu/Strata/tests/ppu/test_fetch_admission.py` ×1

## Last assistant conclusions

### 2026-11-09 07:04 UTC

根据这份实测，**610 的功能路径已跑通，但默认 serve 仍是必须修复的正确性问题**。

我核对了 `5af755f8` 的源码：短窗口 GDN parity 主要测试 `T=3`，尚未覆盖 serve 的 12-token 分组回放与提交。下一步应补齐 **8/9/12/16-token、不同接受前缀及 graph replay**，定位非有限值，不能只放宽上限。

性能方面，当前 A 最好：cache 6144 下，B 比 A 慢约 **9%**，C 慢约 **77%**。C 的每轮 75 ms 换入耗时也需要单独拆分定位。

先让本地 AI 在 `c2be8594` 所在仓库执行：

```bash
git push origin HEAD:refs/heads/ppu/610-validation
```

我这里远端仍是 `5af755f8`，无法读取 box 上的 `REPORT.md` 和 bundle。拿到这 5 个原始提交后，才能在已实测版本上继续修复，保留你们的全部改动。

### 2026-11-09 08:08 UTC

已拉取最新 `ppu/qwen38-ncp`，HEAD 为 [`18d03b75`](https://github.com/DrXuQian/Strata/commit/18d03b75e5f58af48254b1d14bd2424103adeb85)。

5 项本机修复已全部包含，原工作目录已快进同步，工作区干净。serve 超过 8-token 的限制仍保留。

### 2026-11-11 07:35 UTC

```text
请在这台 PPU 810E 新机器上，实际完成 Strata 的安装、构建、算子验证和模型测试，并交付可复现的运行命令。常规安装和排障直接执行，保留已有环境和用户文件。

一、代码与约束

仓库：https://github.com/DrXuQian/Strata.git
分支：ppu/qwen38-ncp
已知基线：18d03b75e5f58af48254b1d14bd2424103adeb85

使用该分支，记录实际 HEAD，确认包含基线中的设备识别、box 脚本修复和 QUactlize 图捕获前 scratch 预留。

先阅读 AGENTS.md、docs/PPU.md、tools/ppu/check.sh、tools/ppu/run_box.sh。

适配统一放在 Strata 中。算子包正常安装、保持上游源码和接口不变，使用 Tensor 接口及 host + JIT，不恢复 libncp_* C ABI 加载方案。

二、检查机器与安装环境

检查并记录：
- 810E 的实际设备名称、PCI bus ID、compute capability、总显存和空闲显存；
- 驱动、完整 PPU SDK、编译器、Python、平台 Torch；
- CPU、系统 RAM、模型盘和构建盘的可用空间。

显存容量和缓存上限以新机器实测为准。

现有后端使用：
STRATA_PPU_TARGET=ppu10
PPU_CUDA_ARCH=80
CMAKE_CUDA_ARCHITECTURES=80

核对实际设备及 SDK 与此目标匹配。使用 PPU SDK 内的编译器和运行库。
设备名称以真实查询结果为准；若存在名称识别问题，基于真实架构证据在 Strata 侧处理，不伪造设备信息。

选择一张空闲卡，设置 CUDA_DEVICE_ORDER=PCI_BUS_ID。
核对 Python、设备 parity 和 Strata 引擎实际使用同一张物理卡。当前 run_box.sh 会将 CUDA_VISIBLE_DEVICES 的单个 PCI 顺序编号传给引擎 --gpu。

复用匹配 SDK 的平台 Torch，避免安装依赖时将其替换成普通 PyPI Torch。
使用同一个 Python 环境安装或复用：
- https://github.com/t-head/flash-attention-for-sail
- https://github.com/t-head/DeepGEMM-for-sail
- https://github.com/DrXuQian/actlizeLA
- https://github.com/DrXuQian/QUactlize，使用 develop 分支

按各项目文档安装，记录版本、commit 和实际导入路径。
host/source 安装必须保留 JIT 所需源码、头文件和固定版本的 submodules。
检查 FA Tensor 入口、DeepGEMM BF16 NoPad 入口、PreparedGDNCore 和 QUactlize packing/JIT 接口。

确保 CMake >= 3.24、Python >= 3.10，并具备 Python 开发头文件和可嵌入的 libpython。

三、存储与模型

模型、离线 pack、JIT 缓存、构建产物和日志优先放在容量足够的持久磁盘。
先估算源模型、两个 pack 和构建临时空间。/dev/shm 只作为明确标记的临时空间，重要日志和报告必须持久保存。

目标模型：
Qwen3.8-Flash-Next，UD-Q4_K_XL GGUF。

优先检查以下已有共享路径，找不到时搜索本机实际位置：
MODEL_DIR=/sim/eec/shared/AI_workspace/llm-models/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL
MTP_RT=/sim/eec/shared/AI_workspace/llm-models/MTP-GGUF-modelzoo/Qwen3.8-Flash-Next-MTP/rt

复用完整、兼容的现有模型和 pack，避免重复下载、重复打包。
区分：
- Strata pack：tools/iq_pack.py，UD-Q4_K_XL 使用 --compat-bf16；
- QUactlize K-pack：strata-ppu-pack 离线生成。

Strata pack 的完成标记是 native_experts.txt 和 index.txt。
运行时保留原始 GGUF，--native 指向第一分片。
MTP 使用包含 dense.txt、dense.bin、experts.bin 的 rt 目录。

四、构建和算子测试

设置实际 PPU_SDK、PYTHON、BUILD_DIR、OUT_DIR 和 JIT 缓存目录。
按资源情况选择 JOBS，显式指定 CUDA architecture 80。

运行 python -m strata_ppu --prepare，并通过 tools/ppu/check.sh 完成：
- host bridge、包接口、离线容器、fetch admission；
- FA、FA-Q8、DeepGEMM MoE；
- GDN verify、commit、graph、prefix、partial、chunked；
- QUactlize dense、grouped、graph、fallback、budget、offline。

共 15 项设备 parity，保留完整日志和误差数据。
保持原有容差；SKIP/77 记为未验证。
导入、JIT 或编译成功不等于设备数值测试通过。

五、模型端到端对照

以 tools/ppu/run_box.sh 为入口，先使用：
EXPERT_CACHE=256
MAX_NEW=32
WITH_MTP=0

脚本的基础模型配置为：
prefill=128、spec=4、max-context=4096、KV int8、greedy。

先跑通无 MTP，再加入匹配的 MTP runtime 验证。
当前命令行调用形式为 strata <参数>，按该版本 --help 构造命令。
需要自定义引擎参数时使用 tools/ppu/check.sh --，只使用脚本实际支持的环境变量。

执行三组：
A：关闭 FA/MoE/GDN provider，关闭 QUactlize；
B：开启 FA/MoE/GDN provider，关闭 QUactlize；
C：开启 FA/MoE/GDN provider，开启 QUactlize 并使用离线 K-pack。

三组使用同一 prompt、profile、缓存、上下文、MTP 和生成参数。
检查输出及 dispatch，确认目标算子和 packed expert 确实被调用。
比较 EOS 前的有效回复，并记录 token 差异；必要时先检查 A 自身的重复性。

六、serve 的已知限制

基线版本开启 PPU GDN 后，serve 默认 lookup 窗口可能超过逐层提交的 8-token 上限。
本次正常 serve 验证明确使用：
--lookup-max-t 6

A/B/C 三组保持相同窗口设置。
使用仓库现有 serve 测试工具或请求协议，至少测试首个请求和后续稳态请求。

不要简单删除上限检查。此前在 610 上放宽上限后，C 组曾出现长时间停顿和非有限值。
超过 8 token 的窗口作为单独的未解决项记录；本次安装验收不要求冒险放宽它。

七、性能测量

正确性通过后，再依据新机实际可用显存逐步增加 expert cache，每次只改变一项参数。
记录请求的缓存槽数和实际驻留槽数，并为运行峰值保留至少约 4GiB 显存余量。
记录同卡其他进程的占用。

固定配置后生成 128 或 256 tokens，至少重复 3 次。
分别记录：
- 冷 JIT、首次 import Torch、模型加载；
- prefill 时间和 decode tok/s；
- serve 首次请求及稳态请求；
- 显存峰值、系统内存占用、输出一致性。

离线打包、profile 准备和冷 JIT 单独计时。
610 的历史结果仅作为参考，不作为 810E 的测试结论，也不预设 B/C 一定更快。

八、交付

在持久目录保存 REPORT.md、完整日志和可复制的脚本/命令，内容包括：
- 环境、设备身份、Strata commit、算子版本；
- 安装、构建、离线 pack、命令行运行和 serve 的准确命令；
- 每项测试的 PASS / FAIL / SKIP；
- A/B/C 输出、误差、性能和资源占用；
- 必要的 Strata 修复提交；
- 仍未解决的问题、真实报错和最小复现。

能够自主修复的继续处理。缺少关键资源或接口不支持时，明确记录阻塞条件，并完成其余独立检查。所有“通过”必须来自这台 810E 的实际执行。
```
