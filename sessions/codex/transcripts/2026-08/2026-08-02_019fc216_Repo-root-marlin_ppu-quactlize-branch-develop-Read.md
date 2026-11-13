# Repo /root/marlin_ppu/quactlize (branch develop). Read files. DO NOT EDIT ANY FILE.

acu is in, and it changes the picture twice. Attack both readings.

MEASURED (base = fp16-plane path, pack = native packed scale; identical grid (8,16,1)x(256,1,1), 131,072 mma both):

  time            base 20.05 us    packnop 21.57    pack 22.54
  regs            base 102         pack 98
  Shared Load     441,344 inst / 1,908,736 trans / 278,528 BC      IDENTICAL in base and pack (+0.00%)
  Shared Store    base 12,288 inst /  50,176 trans /  8,192 BC
                  pack 83,992 inst / 181,272 trans / 81,920 BC     -> +71,704 inst, +73,728 BC
  g2s Store       base 24,192 inst   pack 14,976                   -> pack does 9,216 FEWER
  tsm.ld          base 272,384       pack 276,992                  -> +4,608
  tsm.ld.swzl     168,960 both
  vmem.ld.tsm     base 18,432        pack 9,216                    -> pack halves it
  s.wait          base 253,312       pack 270,208
  Speed of Light  compute ~39.5%, memory ~31.7%, DRAM ~31.7%       neither saturated

The packnop-vs-pack capture separately showed EVERY memory counter identical (tsm.ld, tsm.ld.swzl, tsm.st,
smem.ld, vmem.acp.commit.grp all 0%), so the NOP ablation is structurally sound and pack-packnop really is the
decoder arithmetic.

TWO THINGS I WANT ARGUED, and I have probably got at least one wrong:

1. THE STORE CONFLICTS. +71,704 store instructions produce +73,728 conflicts -- ratio 1.03, i.e. essentially every
   added store conflicts, and transactions per added store are 131,096/71,704 = 1.83. My reading: the decoder forms
   half2(d*sc, -dmin*mn) in ONE register (gguf_packed_scale.h:270) then SPLITS it with lo_h2/hi_h2 and stores the
   halves as two separate 16-bit values into two separate planes (ppu_mma...hpp:1503-1504). 32 lanes x 2 bytes land
   on 16 four-byte banks -> structural 2-way conflict on every store. Proposed fix: store y2 as ONE 32-bit value
   into a single interleaved half2 plane -- halves the store count and makes it conflict-free by construction, and
   removes the zero tile (elements_per_smem_zero() currently ignores kPackedScaleOn, so shared is 57,344 -> 61,440).
   Is that reading right? Is the fix right? What breaks on the READ side, and how big is that change really?

2. THE LOAD CONFLICTS ARE BIGGER AND I ALMOST MISSED THEM. Shared Load BC = 278,528, IDENTICAL in both variants, so
   it is not a native-format problem at all -- it is in the baseline. Shared Load = tsm.ld (272,384) + tsm.ld.swzl
   (168,960). swzl is hardware-interleaved and should be conflict-free, so if it is ~1 transaction/instruction the
   plain tsm.ld carries 1,739,776 transactions over 272,384 instructions = 6.39 transactions per instruction and
   1.02 conflicts per instruction. That is 3.8x LARGER than the store conflicts we were about to optimise, and it is
   in BOTH paths.
   - Is that decomposition sound, or am I mis-attributing swzl's transactions?
   - What are those plain tsm.ld actually reading? I believe it is the mainloop reading sS and sZ per (n, group).
   - There is recorded history: an l98 analysis found the scale read has 4-way bank conflicts, and the
     PPU_SCALE_SWIZZLE fix measured +7.0% WORSE (CI 1.053..1.087). Why would a swizzle that provably removes the
     conflicts make it slower? That is the part I cannot explain.
   - Does the same half2-interleaved-plane change fix the LOAD side too -- one 32-bit read instead of two 16-bit
     reads from two planes? If so the fix is worth ~4x more than I said.

3. And a reframing my user gave me that I think is right: comparing pack against base is comparing against a kernel
   whose input CANNOT LEGALLY EXIST -- the fp16 planes cost +11.1% stored bytes and the product constraint forbids
   that. The legal comparison is (dequant-scale prepass + base) vs pack alone. Prepass moves 6.29 MB (read 2.10
   native + write 4.19 fp16); base itself achieves 1046 GB/s effective. So prepass+base is 22.3 us at DRAM peak and
   26.1 us at base's own rate, against pack's 22.54. Is that accounting right, and does it hold at other M?

Be specific, cite file:line, run things if useful. Say plainly where I am wrong.

- **Thread ID:** `019fc216-5f1a-7b62-852b-055234aaf6b1`
- **Started / last event:** 2026-08-02 10:47 UTC → 2026-08-02 11:05 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/02/rollout-2026-08-02T18-47-53-019fc216-5f1a-7b62-852b-055234aaf6b1.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "553bf119f1744ed07022f038828e206df07dd901", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

---

## User · 2026-08-02 10:47 UTC

Repo /root/marlin_ppu/quactlize (branch develop). Read files. DO NOT EDIT ANY FILE.

acu is in, and it changes the picture twice. Attack both readings.

MEASURED (base = fp16-plane path, pack = native packed scale; identical grid (8,16,1)x(256,1,1), 131,072 mma both):

  time            base 20.05 us    packnop 21.57    pack 22.54
  regs            base 102         pack 98
  Shared Load     441,344 inst / 1,908,736 trans / 278,528 BC      IDENTICAL in base and pack (+0.00%)
  Shared Store    base 12,288 inst /  50,176 trans /  8,192 BC
                  pack 83,992 inst / 181,272 trans / 81,920 BC     -> +71,704 inst, +73,728 BC
  g2s Store       base 24,192 inst   pack 14,976                   -> pack does 9,216 FEWER
  tsm.ld          base 272,384       pack 276,992                  -> +4,608
  tsm.ld.swzl     168,960 both
  vmem.ld.tsm     base 18,432        pack 9,216                    -> pack halves it
  s.wait          base 253,312       pack 270,208
  Speed of Light  compute ~39.5%, memory ~31.7%, DRAM ~31.7%       neither saturated

The packnop-vs-pack capture separately showed EVERY memory counter identical (tsm.ld, tsm.ld.swzl, tsm.st,
smem.ld, vmem.acp.commit.grp all 0%), so the NOP ablation is structurally sound and pack-packnop really is the
decoder arithmetic.

TWO THINGS I WANT ARGUED, and I have probably got at least one wrong:

1. THE STORE CONFLICTS. +71,704 store instructions produce +73,728 conflicts -- ratio 1.03, i.e. essentially every
   added store conflicts, and transactions per added store are 131,096/71,704 = 1.83. My reading: the decoder forms
   half2(d*sc, -dmin*mn) in ONE register (gguf_packed_scale.h:270) then SPLITS it with lo_h2/hi_h2 and stores the
   halves as two separate 16-bit values into two separate planes (ppu_mma...hpp:1503-1504). 32 lanes x 2 bytes land
   on 16 four-byte banks -> structural 2-way conflict on every store. Proposed fix: store y2 as ONE 32-bit value
   into a single interleaved half2 plane -- halves the store count and makes it conflict-free by construction, and
   removes the zero tile (elements_per_smem_zero() currently ignores kPackedScaleOn, so shared is 57,344 -> 61,440).
   Is that reading right? Is the fix right? What breaks on the READ side, and how big is that change really?

2. THE LOAD CONFLICTS ARE BIGGER AND I ALMOST MISSED THEM. Shared Load BC = 278,528, IDENTICAL in both variants, so
   it is not a native-format problem at all -- it is in the baseline. Shared Load = tsm.ld (272,384) + tsm.ld.swzl
   (168,960). swzl is hardware-interleaved and should be conflict-free, so if it is ~1 transaction/instruction the
   plain tsm.ld carries 1,739,776 transactions over 272,384 instructions = 6.39 transactions per instruction and
   1.02 conflicts per instruction. That is 3.8x LARGER than the store conflicts we were about to optimise, and it is
   in BOTH paths.
   - Is that decomposition sound, or am I mis-attributing swzl's transactions?
   - What are those plain tsm.ld actually reading? I believe it is the mainloop reading sS and sZ per (n, group).
   - There is recorded history: an l98 analysis found the scale read has 4-way bank conflicts, and the
     PPU_SCALE_SWIZZLE fix measured +7.0% WORSE (CI 1.053..1.087). Why would a swizzle that provably removes the
     conflicts make it slower? That is the part I cannot explain.
   - Does the same half2-interleaved-plane change fix the LOAD side too -- one 32-bit read instead of two 16-bit
     reads from two planes? If so the fix is worth ~4x more than I said.

3. And a reframing my user gave me that I think is right: comparing pack against base is comparing against a kernel
   whose input CANNOT LEGALLY EXIST -- the fp16 planes cost +11.1% stored bytes and the product constraint forbids
   that. The legal comparison is (dequant-scale prepass + base) vs pack alone. Prepass moves 6.29 MB (read 2.10
   native + write 4.19 fp16); base itself achieves 1046 GB/s effective. So prepass+base is 22.3 us at DRAM peak and
   26.1 us at base's own rate, against pack's 22.54. Is that accounting right, and does it hold at other M?

Be specific, cite file:line, run things if useful. Say plainly where I am wrong.

## Assistant · 2026-08-02 10:48 UTC

I’ll trace the packed-scale write path, the mainloop scale/zero reads, and the recorded swizzle experiment in the repo, then reconcile each claim against the profiler arithmetic. I’ll keep the worktree untouched and call out any inference the counters cannot actually support.

<details><summary>4 tool call(s)</summary>

- `exec: const p = await tools.update_plan({plan:[ {step:"Inspect repo state and locate packed-scale, scale/zero shared-memory, and swizzle-history code",status:"in_progress"}, {step:"Trace write/read layouts and quantify the half2 interleaving chan …`
- `exec: const r = await tools.exec_command({ cmd:"rg --files -g '!third_party/cutlass/docs/**' | rg '(ppu_mma_aiu_multistage_mixed_input|gguf_packed_scale|l8[9-9]_|l9[0-9]_|CHECKPOINT|TODO|HANDOFF|PLAN_task20|acu|profile|packnop)'", workdir:"/root/ …`
- `exec: const cmds = [ ["packed header", "nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '220,300p'"], ["main declarations", "nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n -g '!third_party/cutlass/docs/**' -g '!third_party/cutlass/media/**' \"441,344|278,528|181,272|83,992|21\\.57|22\\.54|20\\.05|73,728|1,908,736|1,739,776\" .", workdir:"/root/marlin_ppu/quactli …`

</details>

## Assistant · 2026-08-02 10:48 UTC

The repository already contains a counter model for these exact captures, including an important warning: the load-conflict decomposition depends on whether `Shared Load transactions` includes the `tsm.ld.swzl` channel, and the code’s swizzle experiment changed the load instruction shape as well as the address map. I’m checking those two points against the actual layouts before accepting the “4× more valuable” conclusion.

<details><summary>17 tool call(s)</summary>

- `exec: const cmds = [ ["layouts1","nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '180,260p'"], ["layouts2","nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multist …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n -g '!third_party/cutlass/docs/**' \"57,344|61,440|57344|61440|zero tile|zero_elements|smem_scale_raw\" docs dev benchmarks tests third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu …`
- `exec: const cmds = [ ["read_setup","nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1540,1705p'"], ["read_use1","nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mu …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n -g '!third_party/cutlass/docs/**' \"TSM_LD_SWZL|tsm\\.ld\\.swzl|PPU_TSM|SMEM_LD|smem\\.ld|Swzl|swzl\" third_party/actlize/include dev/fold_derivation | head -n 300", workdir:"/root/marlin_ppu/ …`
- `exec: const cmds=[ ["swzlasm","nl -ba third_party/actlize/include/cute/arch/copy_ppu0010_aiu.hpp | sed -n '420,560p'"], ["swzltraits","nl -ba third_party/actlize/include/cute/atom/copy_traits_ppu0010_aiu.hpp | sed -n '85,140p'"], ["operand","nl - …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n -g '!third_party/cutlass/docs/**' \"PPU_SCALE_SWIZZLE|swizzle|swz\" dev/fold_derivation/PLAN_task20_scale.md dev/fold_derivation/TODO.md docs/CHECKPOINT.md benchmarks/run_batch.sh | tail -n 22 …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba dev/fold_derivation/PLAN_task20_scale.md | sed -n '1140,1210p' && nl -ba benchmarks/run_batch.sh | sed -n '85,105p;187,245p;310,345p'", workdir:"/root/marlin_ppu/quactlize",yield_time_ms:1000 …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '120,180p' && git log --oneline --decorate -20 && find dev benchmarks docs -maxdepth 4 -typ …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n \"ScaleSwizzleFor|MaybeScaleSwizzle\" third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp && nl -ba third_party/actlize/include/cutlass/gemm/collective/p …`
- `exec: const r = await tools.exec_command({ cmd:"command -v nvcc || true; command -v hgcc || true; command -v acu || true; find . -type f \\( -name '*.acurep' -o -name '*.report' -o -name '*samples*' \\) -print | sort | head -n 200", workdir:"/roo …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba dev/fold_derivation/l96_packed_pair.cu | sed -n '150,220p' && nl -ba dev/fold_derivation/l94_native_scale_path.cu | sed -n '1,140p' && nl -ba dev/fold_derivation/l90_scale_tv.cu | sed -n '1,1 …`
- `exec: const r = await tools.exec_command({ cmd:"nvcc -std=c++17 -x cu -arch=sm_80 -w -I dev/fold_derivation/stub_inc -I third_party/actlize/include -o /tmp/quactlize_l98 dev/fold_derivation/l98_scale_swizzle.cu && /tmp/quactlize_l98 | tail -n 30" …`
- `wait: {"cell_id":"16","yield_time_ms":30000,"max_tokens":10000}`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba dev/fold_derivation/TODO.md | sed -n '1325,1450p' && rg -n \"interleav|half2|widen|one 32-bit read|32-bit\" dev/fold_derivation/TODO.md dev/fold_derivation/PLAN_task20_scale.md dev/fold_deriv …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba dev/fold_derivation/PLAN_task20_scale.md | sed -n '280,470p'", workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:30000 }); text(r.output);`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1180,1315p;1888,1920p'", workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_outp …`
- `exec: const r = await tools.exec_command({ cmd:"find . -type f -perm -111 -printf '%p\\n' | rg 'test_moe_splitk|test_q4k|l9[068]' | head -n 100 && find . -type f | rg '(\\.s$|\\.sass$|\\.asm$|disasm|objdump)' | head -n 100", workdir:"/root/marlin …`

</details>

## Assistant · 2026-08-02 10:53 UTC

One concrete correction is emerging: a conflict-free `tsm.ld.swzl` is not a one-transaction instruction. The ISA form writes four 32-bit registers per lane, so one warp instruction moves 512 bytes and has a four-transaction minimum on 32×4-byte banks. I’m also testing the existing lane map with 32-bit `(scale,zero)` slots; that determines whether interleaving removes the baseline load conflict or only halves the number of logical channels.

<details><summary>18 tool call(s)</summary>

- `exec: const r = await tools.exec_command({ cmd:"sed 's@(int(lay(n, g, 0)) \\* 2) / 4@int(lay(n, g, 0))@' dev/fold_derivation/l98_scale_swizzle.cu | nvcc -std=c++17 -x cu -arch=sm_80 -w -I dev/fold_derivation/stub_inc -I third_party/actlize/includ …`
- `wait: {"cell_id":"21","yield_time_ms":30000,"max_tokens":10000}`
- `exec: const r = await tools.exec_command({ cmd:"sed -e 's@using SmemCopyAtomS = Copy_Atom<DefaultCopy, half_t>;@using SmemCopyAtomS = Copy_Atom<DefaultCopy, uint32_t>;@' -e 's@make_smem_ptr(static_cast<half_t\\*>(nullptr))@make_smem_ptr(static_ca …`
- `wait: {"cell_id":"22","yield_time_ms":30000,"max_tokens":20000}`
- `exec: const r = await tools.exec_command({ cmd:"rg -n \"bdq_transform\" third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp third_party/actlize/include | head -n 80 && nl -ba third_party/actlize/include/cutl …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n \"kPacked(ZMul|HasMin|ScaleBias|PairFast)|ZMul\" third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp third_party/actlize/include/cutlass/gguf_packed_scal …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba third_party/actlize/include/cutlass/gguf_packed_scale.h | sed -n '70,115p' && nl -ba third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp | sed -n '1310, …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba quactlize/schemes.py | sed -n '1,220p' && rg -n \"6\\.29|4\\.19|2\\.10|1046|prepass|pre-pass|11\\.1|native.*bytes|stored bytes|like-for-like|legal\" . -g '!third_party/cutlass/docs/**' -g '!t …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n \"GB/s|gbs|bytes|bandwidth|1046|scale_bytes|packed_scale|L_active|topk|active\" benchmarks/test_moe_splitk_bench.cu benchmarks/moe_splitk_bench_common.hpp | head -n 260 && nl -ba benchmarks/te …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba benchmarks/moe_splitk_bench_common.hpp | sed -n '190,232p' && nl -ba benchmarks/test_moe_splitk_bench.cu | sed -n '1,115p'", workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_outpu …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n \"Q4_K|stored|bytes|144|160|11\\.1|scale.*plane|bits_per\" quactlize/formats.py README.md docs dev/fold_derivation/PLAN_task20_scale.md | head -n 240 && nl -ba quactlize/formats.py | sed -n '1 …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba quactlize/formats.py | sed -n '165,225p'", workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:10000 }); text(r.output);`
- `exec: const r = await tools.exec_command({ cmd:"rg -n \"HBM_GBS\" benchmarks quactlize | head -n 30 && python -m quactlize.formats | rg 'Q4_K|growth' | head -n 20", workdir:"/root/marlin_ppu/quactlize",yield_time_ms:10000,max_output_tokens:10000  …`
- `exec: const r = await tools.exec_command({ cmd:"awk 'BEGIN{native=8*2048*64*2; fp16=8*2048*64*4; move=native+fp16; base=20.05; peak=2766; rate=1046; printf(\"native=%d fp16=%d move=%d peak_us=%.6f sum_peak=%.6f own_us=%.6f sum_own=%.6f\\n\",nativ …`
- `exec: const r = await tools.exec_command({ cmd:"rg -n \"struct Swizzle|operator\\(.*Swizzle|swizzle_code|apply_swizzle|shiftr|shiftl\" third_party/actlize/include/cute | head -n 100 && rg -n \"struct Swizzle\" third_party/actlize/include/cute -g  …`
- `exec: const r = await tools.exec_command({ cmd:"nl -ba third_party/actlize/include/cute/swizzle.hpp | sed -n '50,90p' && nl -ba third_party/actlize/include/cute/pointer_swizzle.hpp | sed -n '68,112p' && nl -ba third_party/actlize/include/cute/lay …`
- `exec: const p = await tools.update_plan({explanation:"Traced the exact decode/store and scale-read layouts, ran the existing l98 probe plus a temporary 32-bit-slot variant, and checked the byte model against the benchmark’s traffic accounting. No …`
- `exec: const p=await tools.update_plan({plan:[ {step:"Inspect repo state and locate packed-scale, scale/zero shared-memory, and swizzle-history code",status:"completed"}, {step:"Trace write/read layouts and quantify the half2 interleaving change", …`

</details>

## Assistant · 2026-08-02 11:05 UTC

Plainly:

- Your store-conflict diagnosis is mostly right, but storing raw `y2` would be numerically wrong, and interleaving does not save shared-memory capacity.
- Your load-transaction decomposition is wrong because `tsm.ld.swzl` is intrinsically wide. The plain loads are indeed scale/zero loads, but a half2 plane does not remove their bank conflicts.
- The prepass byte accounting is right. The two timing estimates are scenarios, not reliable bounds, and they do not extrapolate directly across M.

## 1. Store conflicts

The structural diagnosis is correct. The packed decoder currently emits separate stores here:

- scale: [ppu_mma_aiu_multistage_mixed_input.hpp:1503](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1503)
- zero: [ppu_mma_aiu_multistage_mixed_input.hpp:1504](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1504)

For each decoder warp, 32 adjacent 16-bit stores occupy 16 four-byte banks. Stores cannot broadcast, so that is structurally conflicted. The exact expected decoder count is:

```text
4 decoder warps × 8 groups × 2 planes × 9 publications × 128 CTAs
= 73,728 conflicted store instructions
```

That exactly matching the +73,728 conflict counter is stronger evidence than the `73,728 / 71,704` ratio. The instruction delta is a net aggregate: the packed path also removes/skips other stores, notably the zero-plane clear at [line 1254](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1254). Therefore dividing conflict delta by net store-instruction delta is not a valid per-store ratio.

One correction: you cannot store raw `y2`. It initially holds `(d·sc, -dmin·mn)` at [gguf_packed_scale.h:266](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:266), but after splitting it the decoder changes zero to:

```text
zero = -dmin·mn + 8·scale
```

at [line 272](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gguf_packed_scale.h:272), with `kPackedZMul = 8` at [mainloop line 1329](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1329). Storing raw `y2` would omit the converter-bias cancellation and produce wrong results. You must repack the final `sz.scale, sz.zero`, or reform the arithmetic so the final pair stays packed.

A final 32-bit `(scale,zero)` store is otherwise the right store-side design:

```text
73,728 decoder stores → 36,864
73,728 decoder conflict events → 0
```

Thirty-two consecutive 4-byte stores cover all 32 banks once. Use an explicitly 32-bit store and verify hgcc does not split it back into two half stores.

But it does not reduce shared-memory bytes. For this configuration:

```text
decoded scale + zero today: 4 KiB + 4 KiB = 8 KiB
combined half2 tile:                           8 KiB
raw packed staging:                           4 KiB
```

So the packed allocation remains 61,440 bytes. You can remove the member named `smem_zero`, but the combined tile must grow to 8 KiB. The current code indeed ignores `kPackedScaleOn` when sizing zero at [lines 535–542](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:535), while also allocating the raw staging buffer at [line 582](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:582). The comments claiming zero elements are stale relative to the implementation.

## 2. Load conflicts

Your attribution of `tsm.ld` to scale/zero is right. On this FINE ScaleZero configuration the hot path executes the two reloads at [lines 1905–1908](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1905). The count also reconciles:

```text
272,384 / 131,072 logical copy calls = 2.08 tsm.ld per copy call
```

The transaction decomposition is not right, however. A `tsm.ld.swzl` instruction writes four 32-bit registers per lane, as shown by the ISA wrapper at [copy_ppu0010_aiu.hpp:445](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/arch/copy_ppu0010_aiu.hpp:445). Its CUTE source layout is 128 bits per lane at [copy_traits_ppu0010_aiu.hpp:113](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/atom/copy_traits_ppu0010_aiu.hpp:113).

Thus one warp instruction moves:

```text
32 lanes × 16 bytes = 512 bytes
```

A conflict-free wide instruction is therefore not a one-transaction operation. In the profiler’s apparent 128-byte bank-service units, four transactions is the natural minimum.

Consequently:

```text
swzl minimum ≈ 168,960 × 4 = 675,840 transactions
plain maximum = 1,908,736 − 675,840 = 1,232,896
plain maximum / 272,384 = 4.53 transactions/instruction
```

So 6.39 cannot be obtained by assigning only one transaction to each swizzled load. A consistent decomposition is approximately:

```text
plain tsm.ld:       272,384 × 4    = 1,089,536
tsm.ld.swzl:        remaining        819,200
swzl transactions/instruction         4.85
```

The aggregate counters do not uniquely prove that split, but they rule out your split.

Likewise, `278,528 / 272,384 = 1.02` should not be interpreted as “one excess bank transaction per instruction” or necessarily as 2-way. The existing static probe shows the plain layout is 4-way on four banks. The conflict counter appears closer to “this instruction conflicted/replayed” than to a count of every excess bank word.

### Does half2 interleaving fix the reads?

No, not the bank conflict itself.

I ran the existing [l98 probe](/root/marlin_ppu/quactlize/dev/fold_derivation/l98_scale_swizzle.cu:58) unchanged, then ran an in-memory variant using a 32-bit slot and `Copy_Atom<DefaultCopy,uint32_t>`; no repository file was changed. At TN=128:

```text
current half plane:  plain 4-way on 4 banks
half2 word plane:    plain 4-way on 8 banks
```

The word layout uses twice as many banks, but still places four distinct words on each participating bank. The decoder store is conflict-free because decoder lanes own consecutive `n`. The MMA consumer has a different lane→`n` map with the concentrating 256-element thread stride, so the read remains 4-way.

Interleaving may nevertheless halve the logical load channel:

```text
two copies per group: scale + zero
one copy per group:   packed (scale,zero)
```

Best-case ISA effect:

```text
tsm.ld saved: about 272,384 / 2 = 136,192
tsm.st saved:                         36,864
ratio:                                  3.69×
```

So your “roughly 4× larger” intuition is reasonable as an instruction-count upper bound—but because two channels become one, not because the read becomes conflict-free. Conflict events would roughly halve, not fall to zero.

It is also not a two-line read-side change. Currently the collective constructs separate half fragments and copy views at [lines 1556–1601](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp:1556). Downstream arithmetic expects SoA registers:

```text
(scale_n, scale_n+...)
(zero_n,  zero_n+...)
```

A shared half2 tile delivers AoS registers:

```text
(scale_n, zero_n)
```

You either:

- expose even/odd halfword views and hope hgcc merges the adjacent loads, or
- issue an explicit 32-bit copy and deinterleave the registers yourself.

The second guarantees the shared-load reduction but may add register shuffles, interfere with existing half2 vectorization, and increase registers. It touches coarse reloads, FINE reloads, prefetch reloads, fragment setup, and both transform operands. This is a medium-sized collective-layout change, not merely replacing lines 1503–1504.

## Why the proven swizzle is slower

The l98 result proves a static address property: for its modeled instruction, the XOR layout changes 4-way-on-4-banks to 1-way-on-16-banks and preserves both views. It does not prove that the emitted machine code is cheaper overall.

CUTE’s swizzle is literally:

```cpp
offset ^ ((offset & mask) >> shift)
```

at [swizzle.hpp:75](/root/marlin_ppu/quactlize/third_party/actlize/include/cute/swizzle.hpp:75). Unless the compiler folds the donor bits completely, that adds mask/shift/XOR address generation and a longer dependency chain in every hot scale reload; it also affects gmem→smem destination addressing. With shared memory at roughly 28–32% of peak, fewer bank services need not repay those address instructions or any lost CSE/vectorization.

With your CI `1.053..1.087`, the slowdown is real. Its cause is not established by the data currently quoted. The decisive swizzle capture needs:

```text
tsm.ld instructions
Shared Load transactions
Shared Load bank conflicts
integer AND/shift/XOR deltas
s.wait and relevant stall reasons
```

If bank conflicts and transactions do not fall, l98 did not model the emitted access. If they do fall while time rises, address generation/codegen is the explanation. Timing alone cannot distinguish those cases.

## 3. Legal comparison and the prepass

Your reframing is right, with one wording correction: the fp16 representation cannot legally be resident, but the repo explicitly permits it as a transient prefill workspace at [formats.py:175](/root/marlin_ppu/quactlize/quactlize/formats.py:175). The legal alternatives are therefore:

```text
native packed GEMM
vs
native → transient fp16 scale/zero prepass → baseline GEMM
```

Q4_K is 144 bytes per 256 weights, while replacing its 16-byte native metadata with 32 bytes of fp16 planes makes 160 bytes, exactly +11.1%; the executable definition is at [formats.py:64](/root/marlin_ppu/quactlize/quactlize/formats.py:64) and [line 105](/root/marlin_ppu/quactlize/quactlize/formats.py:105).

For eight active 2048×2048 experts:

```text
native scale input = 8 × 2048 × (2048/256) × 16 = 2,097,152 B
fp16 plane output  = 8 × 2048 × (2048/32)  × 4 = 4,194,304 B
prepass traffic                                      6,291,456 B
```

Using the repo’s 2766 GB/s HBM figure:

```text
6.291456 MB / 2766 GB/s = 2.2746 us
20.05 + 2.2746          = 22.3246 us
```

At 1046 GB/s:

```text
6.291456 MB / 1046 GB/s = 6.0148 us
20.05 + 6.0148          = 26.0648 us
```

So your arithmetic is right.

Two caveats:

- At 20.05 µs, the benchmark’s 21,037,056-byte accounting implies 1049.2 GB/s, not 1046. The 1046 figure corresponds almost exactly to the older 20.11 µs base. This is only a 0.3% discrepancy.
- The 22.32 µs result ignores prepass launch, decode arithmetic, addressing, and synchronization. The 26.06 µs result is not an upper bound either: the base kernel’s effective rate mixes weights, shared-memory work, and computation and is not the bandwidth of a streaming prepass. Producer/consumer L2 residency could also alter the traffic.

At M=1, pack’s 22.54 µs is only 0.22 µs above the idealized 22.32 µs prepass+base figure. A real separate prepass is therefore very likely slower, but it should be measured rather than inferred from either bandwidth rate.

This does not extrapolate directly across M. For fixed active experts, N, and K, the prepass byte count is independent of rows:

```text
Tlegal(M) = Tprepass(Eactive,N,K) + Tbase(M)
```

But the packed decoder is repeated per M tile, approximately with `Σe ceil(Me / TileM)`. For `M_e ≤ 16`, the CTA count is unchanged; above 16, packed decode work repeats while the prepass remains once per active expert. Cache reuse, compute utilization, and eventually the separate dense path all change as well. Re-measure by M band; do not reuse the decode-band 1046 GB/s.

The worktree remained clean.
