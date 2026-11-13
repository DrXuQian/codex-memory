# Repo /root/marlin_ppu/quactlize (branch develop). You may read files. DO NOT EDIT ANY FILE.

The first valid like-for-like measurement of the Q4_K native-scale path is in. Protocol: 20 interleaved ABBA blocks,
paired per-block log ratios, 95% CI on the mean. All six intervals EXCLUDE 1.0:

    pack / base       +13.1%   1.111 .. 1.150     the native-format tax
    packnop / base     +9.2%   1.076 .. 1.109     transport + shared round trip + explicit stores + barrier slot
    pack / packnop     +3.5%   1.025 .. 1.045     the decode ARITHMETIC alone
    swz / base         +7.0%   1.053 .. 1.087     the scale-read bank swizzle
    bdqnop / base      -9.1%   0.894 .. 0.924     what the baseline int4 dequant costs
    (packsplit/pack)/(splitnop/packnop)  +3.4%   1.022 .. 1.045   placement, duplicated-read cost divided out

Context you should verify rather than take from me:
 - band is `64 8 2048 2048 32 3` (L=64, top-k 8, N=K=2048, gs=32, decode); the bench reports ~888.6 GB/s = 32.1% HBM
 - per 256 weights per column: base reads 128 B of int4 codes + 32 B of fp16 scale/zero planes; native reads 128 B +
   a 16 B packed unit. So the NATIVE path reads ~10% FEWER bytes and is 13.1% SLOWER.

MY EXPLANATION, which I want attacked:
   The kernel sits at 32% of HBM peak, so it is not bandwidth-bound and the 10% byte saving buys ~nothing. What the
   native path ADDS is all on the critical path: the 16 B lands in shared RAW, is read BACK from shared into
   registers, decoded, and the two fp16 planes are then STORED to shared by hand -- planes the fp16 path gets for
   free because its cp.async writes them directly. Shared footprint per unit per stage goes 32 B -> 48 B, and all of
   it sits between cp_async_wait and the publishing __syncthreads. So: give up HBM traffic nobody waits on, buy
   shared traffic and serial work everybody waits on.

ARGUE, do not summarise. Specifically:

1. Is that explanation right, and is it COMPLETE? What else could produce a 9.2% transport-side cost at this shape?
   Check the collective (third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp)
   rather than reasoning from my description. If you can compute the expected magnitude of any mechanism, do.

2. I want to capture acu counters NEXT, and NOT run a config sweep first. My argument: the 9.2/3.5 split is
   provisional because packnop consumes only u[0], so the loads of u[1..3] may be eliminated -- if packnop does not
   retain pack's raw shared-load and store counts, pack/packnop is a comparison of two different kernels and every
   number above that rests on it is meaningless. Agree or not, and say EXACTLY which counters to capture and what
   each outcome would mean. A recorded usage exists at dev/fold_derivation/HANDOFF_packed_scale.md:171.

3. The placement result is +3.4% WORSE with the interval excluding 1.0 -- splitting the eight groups across eight
   warps actively harms, after the duplicated 16-byte read is divided out. Is there a reading of that I am missing?
   What does it imply about where the cost actually sits?

4. My falsifiable prediction: the tax should SHRINK as the kernel becomes more bandwidth-bound (larger M, or a
   config with higher HBM%). Is that prediction actually implied by my explanation, or is it compatible with other
   explanations too -- i.e. is it a weak test?

Be specific, cite file:line, and say plainly where I am wrong.

- **Thread ID:** `019fc1ff-79e5-7e53-8e70-2eb74dbbd066`
- **Started / last event:** 2026-08-02 10:22 UTC → 2026-08-02 10:34 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T18-22-53-019fc1ff-79e5-7e53-8e70-2eb74dbbd066.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "553bf119f1744ed07022f038828e206df07dd901", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-02 10:22 UTC

Repo /root/marlin_ppu/quactlize (branch develop). You may read files. DO NOT EDIT ANY FILE.

The first valid like-for-like measurement of the Q4_K native-scale path is in. Protocol: 20 interleaved ABBA blocks,
paired per-block log ratios, 95% CI on the mean. All six intervals EXCLUDE 1.0:

    pack / base       +13.1%   1.111 .. 1.150     the native-format tax
    packnop / base     +9.2%   1.076 .. 1.109     transport + shared round trip + explicit stores + barrier slot
    pack / packnop     +3.5%   1.025 .. 1.045     the decode ARITHMETIC alone
    swz / base         +7.0%   1.053 .. 1.087     the scale-read bank swizzle
    bdqnop / base      -9.1%   0.894 .. 0.924     what the baseline int4 dequant costs
    (packsplit/pack)/(splitnop/packnop)  +3.4%   1.022 .. 1.045   placement, duplicated-read cost divided out

Context you should verify rather than take from me:
 - band is `64 8 2048 2048 32 3` (L=64, top-k 8, N=K=2048, gs=32, decode); the bench reports ~888.6 GB/s = 32.1% HBM
 - per 256 weights per column: base reads 128 B of int4 codes + 32 B of fp16 scale/zero planes; native reads 128 B +
   a 16 B packed unit. So the NATIVE path reads ~10% FEWER bytes and is 13.1% SLOWER.

MY EXPLANATION, which I want attacked:
   The kernel sits at 32% of HBM peak, so it is not bandwidth-bound and the 10% byte saving buys ~nothing. What the
   native path ADDS is all on the critical path: the 16 B lands in shared RAW, is read BACK from shared into
   registers, decoded, and the two fp16 planes are then STORED to shared by hand -- planes the fp16 path gets for
   free because its cp.async writes them directly. Shared footprint per unit per stage goes 32 B -> 48 B, and all of
   it sits between cp_async_wait and the publishing __syncthreads. So: give up HBM traffic nobody waits on, buy
   shared traffic and serial work everybody waits on.

ARGUE, do not summarise. Specifically:

1. Is that explanation right, and is it COMPLETE? What else could produce a 9.2% transport-side cost at this shape?
   Check the collective (third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp)
   rather than reasoning from my description. If you can compute the expected magnitude of any mechanism, do.

2. I want to capture acu counters NEXT, and NOT run a config sweep first. My argument: the 9.2/3.5 split is
   provisional because packnop consumes only u[0], so the loads of u[1..3] may be eliminated -- if packnop does not
   retain pack's raw shared-load and store counts, pack/packnop is a comparison of two different kernels and every
   number above that rests on it is meaningless. Agree or not, and say EXACTLY which counters to capture and what
   each outcome would mean. A recorded usage exists at dev/fold_derivation/HANDOFF_packed_scale.md:171.

3. The placement result is +3.4% WORSE with the interval excluding 1.0 -- splitting the eight groups across eight
   warps actively harms, after the duplicated 16-byte read is divided out. Is there a reading of that I am missing?
   What does it imply about where the cost actually sits?

4. My falsifiable prediction: the tax should SHRINK as the kernel becomes more bandwidth-bound (larger M, or a
   config with higher HBM%). Is that prediction actually implied by my explanation, or is it compatible with other
   explanations too -- i.e. is it a weak test?

Be specific, cite file:line, and say plainly where I am wrong.

## Assistant · 2026-08-02 10:23 UTC

I’ll inspect the collective and the recorded counter workflow, then trace the relevant template branches and byte/operation counts. I’ll keep this strictly read-only and cite exact lines.

<details><summary>1 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"sed -n '1,260p' third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp && sed -n '140,230p' dev/fold_derivation/HANDOFF_packed_scale.md && git status --short --b …`

</details>

## Assistant · 2026-08-02 10:23 UTC

The handoff confirms the capture must be pinned to `(8,16,1)x(256,1,1)`, but its “expected values” omit the scale-channel instruction counters that decide your concern. I’m now locating every packed/nop/split branch and reconstructing work per CTA, including synchronization and bank behavior.

<details><summary>6 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"rg -n \"PACKNOP|PACK_NOP|packnop|PACKED.*NOP|BDQ|SWZ|SPLIT|packed_decode|code_from_words|group_of_words|ScaleRaw|ScalePacked|cp_async_wait|syncthreads|tSrS|tSsS|tSgS|partition_extra|vmem|barrier\"  …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '180,340p;430,660p;760,1090p;1100,1280p;1300,1525p;1530,1815p'","workdir":"/root/marlin_pp …`
- `exec: const ranges = ["340,660","760,1090","1100,1280","1300,1520","1800,1930"]; for (const range of ranges) { const r = await tools.exec_command({cmd:'nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input. …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '618,760p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_token …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '756,1090p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_toke …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1100,1280p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_output_tok …`

</details>

## Assistant · 2026-08-02 10:24 UTC

One important correction is already visible in the code: native transport is not merely “one 16-byte copy per column.” All 256 CTA threads are wrapped onto a 128-thread copy, so every packed unit is copied twice; the baseline scale and zero copies are also duplicated by the same outer modulo. That preserves the nominal 2× channel-byte reduction, but it creates duplicate async instructions and changes the global transaction/coalescing pattern—both are plausible parts of the 9.2%, separate from raw HBM bytes.

<details><summary>7 tool call(s)</summary>

- `exec: const r = await tools.exec_command({"cmd":"nl -ba dev/fold_derivation/HANDOFF_packed_scale.md | sed -n '1,140p;155,210p;250,320p'\nrg --files | rg '\\.(report|csv|json)$|acu|profile|counter' | head -200\nrg -n \"smem\\.ld|tsm\\.st|bank conf …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba dev/fold_derivation/TODO.md | sed -n '1240,1495p'\nnl -ba dev/fold_derivation/PLAN_task20_scale.md | sed -n '1000,1215p'","workdir":"/root/marlin_ppu/quactlize","yield_time_ms":10000,"max_ou …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"888|2766|GB/s|HBM|bandwidth|bytes|traffic|32\\.1|SK_QUANT|16x128:256\" dev third_party/actlize/Kernels/general/w4a16_gemm/cutlass_w4a16 -g '*.hpp' -g '*.cuh' -g '*.cu' -g '*.md' | head -300 …`
- `exec: const r = await tools.exec_command({"cmd":"find . -path '*moe_splitk_bench_common.hpp' -o -path '*lowbit_moe_bench.hpp' | sort\nnl -ba dev/fold_derivation/TODO.md | sed -n '115,140p'\nnl -ba dev/fold_derivation/PLAN_task20_scale.md | sed -n …`
- `exec: const r = await tools.exec_command({"cmd":"rg -n \"GB/s|HBM|2766|wbytes|floor|bytes\" benchmarks/lowbit_moe_bench.hpp benchmarks/moe_splitk_bench_common.hpp\nnl -ba benchmarks/lowbit_moe_bench.hpp | sed -n '175,275p'\nnl -ba benchmarks/moe_ …`
- `exec: const r = await tools.exec_command({"cmd":"sed -n '1,240p' dev/fold_derivation/acu_capture.sh\nnl -ba dev/test_width_acu.cu | sed -n '130,210p'\nrg -n \"DRAM Throughput|Shared Load|Shared Store From Global Load|Bank Conflicts|transactions|A …`
- `exec: const r = await tools.exec_command({"cmd":"nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '1,260p'\nnl -ba benchmarks/moe_splitk_bench_common.hpp | sed -n '200,230p'","workdir":"/root/marlin_ppu/quactlize","yield_ti …`

</details>

## Assistant · 2026-08-02 10:34 UTC

## 1. The explanation is directionally right, but not complete

The code does exactly the expensive round trip you describe:

- Packed bytes are asynchronously staged as one 16-byte unit per column ([ppu_mma...hpp:240](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:240)).
- After `cp_async_wait`, the unit is loaded into four `uint32_t` registers ([ppu_mma...hpp:1441](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1441)).
- Eight scale/zero pairs are decoded and scalar-stored into the ordinary fp16 planes ([ppu_mma...hpp:1503](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1503)).
- This is between the wait and the publishing barrier ([ppu_mma...hpp:1018](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1018)).

So yes: the native path replaces two overlappable gmem→smem copies with one copy plus an explicit smem→register→smem producer. That is a bad exchange when the global-byte saving is not the active limiter.

But three parts of your argument are too strong.

First, 32.1% does not prove “HBM traffic nobody waits on.” The benchmark’s GB/s is not a hardware counter. It always charges two fp16 planes:

- `sb = ... * 2.0 * 2.0` ([moe_splitk_bench_common.hpp:206](/root/marlin_ppu/quactlize/benchmarks/moe_splitk_bench_common.hpp:206)).
- GB/s is then simply those modeled bytes divided by wall time ([moe_splitk_bench_common.hpp:210](/root/marlin_ppu/quactlize/benchmarks/moe_splitk_bench_common.hpp:210)).

For this band:

- Codes: 16,777,216 B
- Baseline scale/zero: 4,194,304 B
- A + D: 65,536 B
- Baseline total: 21,037,056 B
- Native total: 18,939,904 B

That is exactly a 9.97% logical-byte reduction. At 888.6 GB/s, the modeled baseline time is about 23.67 µs. If those bytes scaled linearly at that effective rate, the saving would be 2.36 µs—not negligible relative to the measured 3.10 µs native penalty. Low peak utilization can mean latency, poor transaction efficiency, insufficient concurrency, or pipe serialization; it does not mean memory is irrelevant. Existing ACU evidence actually has `Memory Dependency` as the leading stall at this shape ([TODO.md:1261](/root/marlin_ppu/quactlize/dev/fold_derivation/TODO.md:1261)).

Second, there are nine packed decode passes for eight K tiles. The initial decode is at [ppu_mma...hpp:989](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:989), and the drain loop invokes another at [ppu_mma...hpp:1019](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1019). The recorded counter derivation confirms nine passes for eight tiles ([HANDOFF_packed_scale.md:62](/root/marlin_ppu/quactlize/dev/fold_derivation/HANDOFF_packed_scale.md:62)).

That creates 12.5% redundant packed-producer work:

- 1,179,648 decoded `(column,group)` pairs for 1,048,576 required.
- About 2.36 MB of raw shared reads across the kernel.
- About 4.72 MB of explicit shared writes.
- Source-level expectation: 73,728 warp store instructions/conflict events.

If the 9.2% transport-side cost scaled proportionally, eliminating the drain pass is worth at most about one percentage point. Not the answer, but not zero.

Third, the shared-memory footprint can affect residency in general, although not at this pinned shape. Despite comments saying the zero tile disappears, the implementation does not size `smem_zero` to zero under `kPackedScaleOn`; `elements_per_smem_zero()` still returns the full layout size ([ppu_mma...hpp:534](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:534)). The raw staging allocation is then appended ([ppu_mma...hpp:582](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:582)).

Thus:

- Base: 57,344 B/CTA
- Packed: 61,440 B/CTA

Both allow four CTAs in 256 KiB, so there is no shared-memory block-limit transition here. With only 128 CTAs on 72 CUs, this cannot plausibly explain 9.2%. Still capture the resource counters to verify that the compiler/runtime agrees.

Other plausible contributors to 9.2% are:

- The halfword stores are bank-inefficient: 32 lanes occupy 16 four-byte banks. The prior capture reported about 73,728 added conflicts ([HANDOFF_packed_scale.md:55](/root/marlin_ppu/quactlize/dev/fold_derivation/HANDOFF_packed_scale.md:55)).
- Decode delays the next B/A register load and the next global-copy issue, not just the barrier. It can shorten effective multistage overlap for the entire mainloop ([ppu_mma...hpp:1023](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1023)).
- Every 256-thread CTA is wrapped onto a 128-thread scale-copy partition ([ppu_mma...hpp:801](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:801)). Both baseline and packed copies are duplicated, so this is not directly a native penalty, but requested bytes, DRAM bytes, and wait behavior can differ because baseline has two strided streams while packed has one contiguous stream.
- Compiler scheduling, instruction-fetch behavior, and register allocation can differ materially between full and NOP even without spills.

So: your core mechanism is right; “32% means nobody waits on HBM” is wrong; and the ninth pass plus pipeline/code-generation effects make it incomplete.

## 2. Capture counters now; do not sweep first

I agree with your sequencing. The 9.2/3.5 attribution is provisional.

The code gives the compiler explicit permission to eliminate `u[1..3]`: the NOP consumes only `u[0]` ([ppu_mma...hpp:1483](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1483)), while the real decoder indexes the register array with compile-time constants ([gguf_packed_scale.h:62](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:62)). The optimizer can turn the full 16-byte vector read into one 32-bit read in NOP.

Where you are wrong is “every number above is meaningless.” These remain valid direct intervention measurements:

- `pack/base`: valid native-format tax.
- `packnop/base`: valid cost of the compiled NOP kernel, but not necessarily “transport.”
- `swz/base` and `bdqnop/base`: independent results.
- `pack/packnop`: not “decode arithmetic alone” until structural equality is proven.
- The normalized split result is also not a clean placement isolate yet.

Capture these five pinned variants: `base`, `packnop`, `pack`, `splitnop`, `packsplit`. Capturing `swz` and `bdqnop` in the same pinned manner is worthwhile, but not required to settle the NOP issue. Use the recorded one-row command at [HANDOFF_packed_scale.md:171](/root/marlin_ppu/quactlize/dev/fold_derivation/HANDOFF_packed_scale.md:171).

For every capture, retain these counters:

| Counter | Required outcome and interpretation |
|---|---|
| Grid/block, `v.mma.f32.f16.m16n16k16`, `vmem.st`, output bytes | Must be `(8,16,1)x(256,1,1)`, 131,072 MMA, 512 output stores, 32,768 output bytes. Otherwise discard the capture. |
| Registers/thread, scratch/local bytes, `vmem.ld`, local `vmem.st` | Pack and NOP must not introduce different spills. A difference means `pack/packnop` includes register-allocation effects. |
| Shared memory/CTA, Block Limit Shared Mem, Block Limit Registers, achieved warps/CU | Expect 57,344 B base and 61,440 B packed-family, but the same four-block SMEM limit. A residency change would be an alternate explanation. |
| `Shared Load Instructions`, `Shared Load Transactions`, shared-load bank conflicts, and opcode-width breakdown for `smem.ld` | Full packed previously implied +4,608 instructions and +36,864 transactions: one 16-byte read by four decoder warps × nine passes × 128 CTAs. If NOP has the same instructions but about one-eighth the transactions, `u[1..3]` were eliminated. Then 3.5% includes raw-read transport, not just arithmetic. |
| `tsm.st`/Shared Store instructions, transactions, bank conflicts | Pack, packnop, splitnop, and packsplit must match. Source-level work is 73,728 warp halfword stores/conflicts. Any NOP reduction means the explicit-store control failed. |
| `Shared Store From Global Load` instructions, transactions and bytes; `vmem.acp.commit.grp` and wait counts | Pack, NOP, and split variants must match. Base should do more scale-channel async-store work. A difference between pack and packnop means their g2s transport is not equivalent. |
| DRAM read bytes/transactions/throughput; L2 read sectors/hit rate | Base→packed should reduce unique logical scale bytes by about 2,097,152 B. If DRAM bytes do not fall, duplicate/replayed requests or transaction inefficiency destroyed the supposed saving. Pack and packnop must match. |
| Decoder opcode counts: shifts, masks, inserts, `ppu.sub.f16x2`, `ppu.fma.rtte.f16x2`, plus total IALU/FALU instructions | Pack−NOP should contain the decoder arithmetic; pack and packsplit should have the same group-arithmetic totals. Extra split counts identify duplicated setup/codegen, not placement. |
| `Memory Dependency`, `Barrier`, `Execution Dependency`, `Instruction Fetch`; LSU/IALU/FALU busy | Barrier rising in packnop points to the critical interval. LSU/issue rising without Barrier points to aggregate shared-pipe or instruction pressure. Memory Dependency rising despite fewer DRAM bytes points to disturbed mainloop overlap. Instruction Fetch rising in split points to its duplicated unrolled code. |

The decisive NOP outcomes are simple:

- Same raw-load width/transactions, stores, async copies, resources, and spills: the 9.2/3.5 split is structurally credible.
- Same `smem.ld` count but much lower NOP transactions/bytes: your concern is confirmed.
- Different store counts: the NOP is unusable as presently written.
- Same memory counts but different registers/stalls: it remains a compiler-schedule ablation, not “arithmetic alone.”

## 3. The placement result does not yet prove placement itself is harmful

There is a reading you are missing.

The full split duplicates more than the raw read. It duplicates per-column header setup: `mul2_of_words()` and `head_of_words()` are computed before the group bodies ([ppu_mma...hpp:1445](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1445)). NOP makes both dead because its stores depend only on `u[0]`. Therefore `(packsplit/pack)/(splitnop/packnop)` does not divide out the full decoder’s duplicated header work.

More importantly, if NOP reads only four bytes:

- `packsplit/pack` duplicates a 16-byte raw read.
- `splitnop/packnop` duplicates a four-byte raw read.

Your normalization then leaves twelve bytes per participating lane, plus their shared transactions, in the alleged “placement” term.

The split also emits two separate unrolled group branches—groups 0–3 and 4–7 ([ppu_mma...hpp:1506](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1506)). Dynamic group arithmetic may be equal while static code size and instruction-fetch behavior worsen.

Thus the current defensible statement is:

> The implemented full-decode split has a 3.4% negative interaction that NOP does not reproduce.

It is not yet:

> Spreading identical work across eight warps is intrinsically 3.4% worse.

If counters establish identical raw-load width, stores, dynamic arithmetic, setup, and no resource change, then the result really does kill your slowest-warp theory. It would imply the tax is not the four-warps × eight-groups serial chain. It would place it in aggregate issue/shared service, pipeline disruption, or front-end/code-layout effects. But you need the counters before making that inference.

## 4. The shrinking-tax prediction is weak, and “larger M” is probably the wrong axis

Conditionally, yes: if the current regime hides the byte saving but exposes the producer work, then a genuinely DRAM-throughput-dominated regime could expose the 10% saving and hide some ALU/shared work.

But that is not uniquely implied by your explanation. The native producer cost is not fixed per launch; it is per `(M-tile, column, superblock)`. More M tiles repeat the packed decode and stores. Meanwhile weights may be reused from cache across M tiles. That can make the native tax stay constant or grow.

Also:

- Increasing M normally raises weight reuse and arithmetic intensity, making GEMM less bandwidth-bound.
- For `M<=16`, this kernel already computes the padded 16-row MMA tile; changing real M may barely change mainloop work.
- For `M>16`, both packed producer work and CTA count grow, while unique HBM weight traffic may not grow proportionally.
- A higher benchmark “HBM%” is endogenous: it is modeled bytes divided by a shorter time, not evidence that DRAM is the limiting resource.

Many unrelated mechanisms predict a shrinking percentage too: fixed launch overhead, longer common-path duration, better occupancy, different drain amortization, or a compiler schedule that happens to hide packed work.

So it is a weak correlation test. A convincing version requires actual DRAM bytes/throughput plus unchanged per-tile packed instruction counts and stall evidence showing a transition from IALU/LSU/barrier exposure to DRAM saturation. Without that, “tax shrank at higher reported HBM%” does not identify your mechanism.
