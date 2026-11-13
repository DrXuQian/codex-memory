# Codex thread goals

- `019fe961-f686-7681-a873-0d58287ce0f0` **paused** — kpack在5070和5090上，在多个shape上达到xplane的最佳水准。
- `01a06bdd-3452-70e0-bb08-0e21921c79d5` **paused** — 在类似的config下，达到类似fp8的指令数量，如果不行，有明确证据证明。不能为了减少指令牺牲速度。
- `01a1a3f9-10d4-78d0-bbd1-cf8aded7645a` **blocked** — 完成 Flare 衍生框架对 Qwen3.8-Flash-Next UD-Q4_K_XL GGUF 主模型及 mtp-Qwen3.8-Flash-Next-shared-Q8_0.gguf 的端到端接入，在 RTX PRO 6000 上通过导出包与 Rust 原生运行验证；decode 与 MTP 使用同一轮 CUDA Graph，保持压缩权重驻留及 PLE 主机存储，排除热路径临时权重加载、JIT、逐 token CPU 同步并通过 GPU 时间线检查可消除的 bubble，完成去 PPU 前的框架准备；用户要求中间持续推进，不能在局部组件通过后结束。
