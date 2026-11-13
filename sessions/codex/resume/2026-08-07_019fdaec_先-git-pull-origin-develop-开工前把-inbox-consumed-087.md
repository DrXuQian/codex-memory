# Resume brief: 先 git pull origin develop。开工前把 `inbox-consumed: 087` 和 wall-clock 时间戳写进 .coord/STATUS.md。

先读 .coord/INBOX.md 的 085 和 086 —— 085 撤回了我给你的一个错误描述(split-K 方向说反了),086 是我用 `git add -- benchmarks` 扫走你之前工作的归属声明。两条都不需要你做事,但会解释 git 状态。

## 这一轮只有一件事:把 copy_A_packed_row0 推广到 R 行

### 为什么

昨晚删掉了 compact-A(四刀,commit cbfe394 / 9edd379 / 3fdc155)。它想解决 M=1 时 A 的 15/16 padding,做法是改 smem 布局(TileM 行 → C 行),而 SmemLayoutACompact 是手搓 make_layout、**从不 composite InternalSmemLayoutAtomA**,所以 A 掉出 AIU/tsm.ld.swzl 硬件通路:

    acu,同一个 tile,grid 两边都是 (1,512,1)
    tsm.ld +640%,v.shll.i 176x,v.cnvt 241x,v.or.i 0 → 327,680
    tsm.ld.swzl -80%,vmem.aiu.ld.tsm -80%,MMA 计数逐位相同(163,840)
    结果:-55%(26.31us / 28.9% 对 16.98 / 44.7%)

而 PPU_A_PACK 是同一个想法**从分配侧**做的:只重叠 cube 基址,swzl 读指令一字未动。实测(两边都有 `[A path]` 见证行,都 Disposition: Passed):

    ordinary AIU + swzl        16.97 us   44.7% HBM   1237 GB/s
    PPU_A_PACK (只写 row 0)     16.49 us   46.0% HBM   1273 GB/s     +2.9%

记在 docs/BACKTEST.md 的 D8/D9。

### 要做什么

现在它只写 row 0,所以有效界是 M ≤ 1。写 0..R-1 行 → 界变成 M ≤ R,它就成了通用的小-M A provider。

row 0 只占 4 段 ×16 halfs,是因为 row 0 意味着 `lane/4 == 0 && v/2 == 0`,把 `vreg_row_idx = (v/2)*8 + lane/4 + coord_h` 塌成了 `vreg_vec_idx = v%2`。**那是一般式的特例**,每一行 r 都有自己的 4 段。所以 R 行占 R*64 halfs,最小无碰撞 pitch 是 R 的函数。

改动点在 quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp:
  * `aPackRunOff(s)` 现在是 row-0 闭式(`ssv = 0,4,2,6`),要带行索引
  * `aPackDisjoint()` 现在只检查 row-0,要扩成 R×R(第 i 个 cube 的 0..R-1 行 vs 第 j 个的 0..R-1 行)
  * `kAPackPitch` 变成 R 的函数,`kAPackSpanRaw` 跟着
  * `copy_A_packed_row0` → `copy_A_packed_rows<R>`,`kAWrThreads = kACubes * kASlices * 2` 随 R 缩放
  * 两个 launcher 的 one-row static_assert(fpA_intB_ppu.cuh、moe_grouped_ppu.cuh)界从 1 改成 R

### 两条不许猜

**pitch 必须从模型算,不能从 R=1 外推。** `ppu_tsm_ld_swzl_sim`(cute/arch/copy_ppu0010_aiu.hpp)是那条读指令的软件模型,dev/fold_derivation/l82/l84/l85/l86 是它的逐字宿主复刻,而模型本身在 l2l3/l17/l7/l10/l12/l13/l16 上 0-mismatch 验过。l84 是 row-0 落点,l85 是碰撞检查 —— **两个都要推广到 R 行并重跑**,不是把 64 乘个数。

**对齐必须保持结构性。** 现在的 pitch 是 64 halfs 而不是更紧的 16,原因是紧密打包**在 box 上 B 的 AIU load 里 fault 了**:smem_b 紧跟 smem_a,cute::array_aligned 只保证 16 B,PPU0010 的 AIU 要 32,而"以前一直对"纯属 A 的字节数碰巧是 32 的倍数。64 让每个 cube 基址和整个 span 都是 128 B 的倍数。R 行算出 pitch 之后要向上圆到保持这个性质,别把踩过的雷埋回去。

### 你现在可以本地编译了

dev/fold_derivation/stub_inc/ppu_arch_shim.h 是昨晚加的。cute/config.hpp:63 的 CUTE_INLINE_CONSTANT 键在 __HGGC_ARCH__ 上,而 syntax_check.sh 只传 __HGGCCC__,所以本地一直是 5954 个 "cute::_ undefined in device code"。按 __CUDA_ARCH__ 定义它(box 上 device 是 hgcc、host 是 g++,nvcc 一个 TU 编两遍)之后降到 **164,单一类,全来自 actlize 的 mma_ppu0015.hpp asm 约束**——那是 floor。

    nvcc -std=c++17 -arch=sm_80 --expt-relaxed-constexpr -D__HGGCCC__ -DPPU_FORCE_INSTANTIATE=1 \
      -include dev/fold_derivation/stub_inc/ppu_arch_shim.h -Xcudafe --error_limit=100000 \
      -I dev/fold_derivation/stub_inc -I third_party/actlize/include -I third_party/actlize/tools/util/include \
      -Itests -Ibenchmarks -Iquactlize/include -Idev -cuda -o /tmp/o.cu.cpp -x cu \
      benchmarks/test_lowbit_dense_bench.cu -Wno-deprecated-gpu-targets

**非-asm 错误必须是 0。** 我昨晚五个 consumer 都是这样验的。C++ 那半不用等 box;pitch 是经验量,只有 box 能最终确认。

### 约束

- 每个子项一个 commit,别攒。push 你 land 的。
- `git add` **只用显式路径**。benchmarks/ ci/ docs/ tests/ quactlize/*.py 是我的半边 —— 我昨晚就是用 `git add -- benchmarks` 扫走了别人的在途改动(见 086),别重复。
- 不要 `git add -A`。
- 额度是滚动窗口,可能中途再撞限。**先报增量结果再继续,别一口气跑到死。**
- 别碰 third_party/actlize(ci/check_actlize_pristine.py 会拦)。

- **Thread ID:** `019fdaec-594b-74d2-b781-9f246696eb33`
- **Started / last event:** 2026-08-07 06:32 UTC → 2026-08-07 06:50 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** exec  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/07/rollout-2026-08-07T14-32-30-019fdaec-594b-74d2-b781-9f246696eb33.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "fbaff57bfc56ab7766a8bb5c1b400b07d30cb59c", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-07_019fdaec_先-git-pull-origin-develop-开工前把-inbox-consumed-087.md](../transcripts/2026-08/2026-08-07_019fdaec_先-git-pull-origin-develop-开工前把-inbox-consumed-087.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

先 git pull origin develop。开工前把 `inbox-consumed: 087` 和 wall-clock 时间戳写进 .coord/STATUS.md。

先读 .coord/INBOX.md 的 085 和 086 —— 085 撤回了我给你的一个错误描述(split-K 方向说反了),086 是我用 `git add -- benchmarks` 扫走你之前工作的归属声明。两条都不需要你做事,但会解释 git 状态。

## 这一轮只有一件事:把 copy_A_packed_row0 推广到 R 行

### 为什么

昨晚删掉了 compact-A(四刀,commit cbfe394 / 9edd379 / 3fdc155)。它想解决 M=1 时 A 的 15/16 padding,做法是改 smem 布局(TileM 行 → C 行),而 SmemLayoutACompact 是手搓 make_layout、**从不 composite InternalSmemLayoutAtomA**,所以 A 掉出 AIU/tsm.ld.swzl 硬件通路:

    acu,同一个 tile,grid 两边都是 (1,512,1)
    tsm.ld +640%,v.shll.i 176x,v.cnvt 241x,v.or.i 0 → 327,680
    tsm.ld.swzl -80%,vmem.aiu.ld.tsm -80%,MMA 计数逐位相同(163,840)
    结果:-55%(26.31us / 28.9% 对 16.98 / 44.7%)

而 PPU_A_PACK 是同一个想法**从分配侧**做的:只重叠 cube 基址,swzl 读指令一字未动。实测(两边都有 `[A path]` 见证行,都 Disposition: Passed):

    ordinary AIU + swzl        16.97 us   44.7% HBM   1237 GB/s
    PPU_A_PACK (只写 row 0)     16.49 us   46.0% HBM   1273 GB/s     +2.9%

记在 docs/BACKTEST.md 的 D8/D9。

### 要做什么

现在它只写 row 0,所以有效界是 M ≤ 1。写 0..R-1 行 → 界变成 M ≤ R,它就成了通用的小-M A provider。

row 0 只占 4 段 ×16 halfs,是因为 row 0 意味着 `lane/4 == 0 && v/2 == 0`,把 `vreg_row_idx = (v/2)*8 + lane/4 + coord_h` 塌成了 `vreg_vec_idx = v%2`。**那是一般式的特例**,每一行 r 都有自己的 4 段。所以 R 行占 R*64 halfs,最小无碰撞 pitch 是 R 的函数。

改动点在 quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp:
  * `aPackRunOff(s)` 现在是 row-0 闭式(`ssv = 0,4,2,6`),要带行索引
  * `aPackDisjoint()` 现在只检查 row-0,要扩成 R×R(第 i 个 cube 的 0..R-1 行 vs 第 j 个的 0..R-1 行)
  * `kAPackPitch` 变成 R 的函数,`kAPackSpanRaw` 跟着
  * `copy_A_packed_row0` → `copy_A_packed_rows<R>`,`kAWrThreads = kACubes * kASlices * 2` 随 R 缩放
  * 两个 launcher 的 one-row static_assert(fpA_intB_ppu.cuh、moe_grouped_ppu.cuh)界从 1 改成 R

### 两条不许猜

**pitch 必须从模型算,不能从 R=1 外推。** `ppu_tsm_ld_swzl_sim`(cute/arch/copy_ppu0010_aiu.hpp)是那条读指令的软件模型,dev/fold_derivation/l82/l84/l85/l86 是它的逐字宿主复刻,而模型本身在 l2l3/l17/l7/l10/l12/l13/l16 上 0-mismatch 验过。l84 是 row-0 落点,l85 是碰撞检查 —— **两个都要推广到 R 行并重跑**,不是把 64 乘个数。

**对齐必须保持结构性。** 现在的 pitch 是 64 halfs 而不是更紧的 16,原因是紧密打包**在 box 上 B 的 AIU load 里 fault 了**:smem_b 紧跟 smem_a,cute::array_aligned 只保证 16 B,PPU0010 的 AIU 要 32,而"以前一直对"纯属 A 的字节数碰巧是 32 的倍数。64 让每个 cube 基址和整个 span 都是 128 B 的倍数。R 行算出 pitch 之后要向上圆到保持这个性质,别把踩过的雷埋回去。

### 你现在可以本地编译了

dev/fold_derivation/stub_inc/ppu_arch_shim.h 是昨晚加的。cute/config.hpp:63 的 CUTE_INLINE_CONSTANT 键在 __HGGC_ARCH__ 上,而 syntax_check.sh 只传 __HGGCCC__,所以本地一直是 5954 个 "cute::_ undefined in device code"。按 __CUDA_ARCH__ 定义它(box 上 device 是 hgcc、host 是 g++,nvcc 一个 TU 编两遍)之后降到 **164,单一类,全来自 actlize 的 mma_ppu0015.hpp asm 约束**——那是 floor。

    nvcc -std=c++17 -arch=sm_80 --expt-relaxed-constexpr -D__HGGCCC__ -DPPU_FORCE_INSTANTIATE=1 \
      -include dev/fold_derivation/stub_inc/ppu_arch_shim.h -Xcudafe --error_limit=100000 \
      -I dev/fold_derivation/stub_inc -I third_party/actlize/include -I third_party/actlize/tools/util/include \
      -Itests -Ibenchmarks -Iquactlize/include -Idev -cuda -o /tmp/o.cu.cpp -x cu \
      benchmarks/test_lowbit_dense_bench.cu -Wno-deprecated-gpu-targets

**非-asm 错误必须是 0。** 我昨晚五个 consumer 都是这样验的。C++ 那半不用等 box;pitch 是经验量,只有 box 能最终确认。

### 约束

- 每个子项一个 commit,别攒。push 你 land 的。
- `git add` **只用显式路径**。benchmarks/ ci/ docs/ tests/ quactlize/*.py 是我的半边 —— 我昨晚就是用 `git add -- benchmarks` 扫走了别人的在途改动(见 086),别重复。
- 不要 `git add -A`。
- 额度是滚动窗口,可能中途再撞限。**先报增量结果再继续,别一口气跑到死。**
- 别碰 third_party/actlize(ci/check_actlize_pristine.py 会拦)。

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×4
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l85_cube_overlap.cpp` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/quactlize_mma_mixed_input.hpp` ×2
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l86_row0_perm.cpp` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l84_row0_placement.cpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/detail/ppu_a_pack.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_extensions/cutlass/gemm/collective/builders/quactlize_mma_builder.inl` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh` ×1

## Last assistant conclusions

### 2026-08-07 06:50 UTC

已完成并推送到 `origin/develop`，工作树干净。

- `7736833`：推广 l84/l85/l86 模型并重跑，全 PASS。模型所得 pitch：
  - R=1：64 halfs
  - R=2..4：320
  - R=5..8：640
  - R=9..12：960
  - R=13..16：1024
- `a6a6cbe`：实现 `copy_A_packed_rows<R>`、R×R 碰撞检查、随 R 扩展的 copy 数量、奇数 cache-line 半段交换，以及 M<R 时 zfill。
- `cd7390e`：dense/grouped launcher 都限制为 `M/Mmax <= PPU_A_PACK`。
- `f678f4a`：更新 `.coord/STATUS.md`，记录 `inbox-consumed: 087`。

验证结果：

- l84/l85/l86：全部 PASS。
- 五个有效 consumer 在 `PPU_A_PACK=4` 下均为 164/164 asm floor，非-asm 错误 0。
- `R=1/4/8` dense 全实例化检查均为非-asm 0。
- actlize pristine 检查通过，未改 `third_party/actlize`。
- 未触碰 benchmarks/tests/ci/docs 用户半边。

剩余仅需 ppu001 上确认所选 R 的边界正确性与性能。
