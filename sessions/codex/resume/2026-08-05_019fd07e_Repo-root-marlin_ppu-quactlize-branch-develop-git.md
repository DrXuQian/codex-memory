# Resume brief: Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 071. It is a build regression from your 1d2a621 (routing dense through the shared gs ladder) and it currently blocks the box entirely.

test_lowbit_dense_bench does not compile with the 227-row table — the normal one, four-warp minimum, no quarantined rows. Two errors, one root:

    gemm_universal_adapter.h:556: no type named 'InstructionShape' in
      GemmUniversal<packed_tuple<int,int,int,int>,
        CollectiveMma<PPU0010, MainloopPPUAiuMixedInput<6, C<256>, KernelAiuMultistageMixedInputFinegrainedGs32>, ...>>

    ppu_aiu_gemm_mixed_input.hpp:109: no type named 'SharedStorage' in
      CollectiveMma<PPU0010, MainloopPPUAiuMixedInput<12, C<256>, FinegrainedGs32>, TileShape(64,128,64), ...>

The chain as far as I could take it: CollectiveMma matches no specialisation, so its members are ill-formed; GemmUniversal's 3.x specialisation SFINAEs out because its enable_if reads CollectiveMainloop_::DispatchPolicy; the primary template has no ProblemShape; IsCutlass3GemmKernel (gemm.h:123 tests exactly that member) is false; the adapter takes its 2.x specialisation at line 542, which needs Mma::Shape / WarpShape / InstructionShape. The adapter error is the loudest and the least informative.

RULED OUT, so you do not repeat it:

  * NOT split-K. GemmUniversal's TileScheduler_ defaults to void (gemm_universal_decl.h:56) and the dense bench instantiates it with three arguments, so ppu_aiu_gemm_mixed_input.hpp:61's !is_same_v<TileScheduler_, SplitKSerialScheduler> passes. The user asked this directly; the answer is no, and the recorded 65% winner also came through moe_grouped_ppu::filter_and_run with no split axis.
  * NOT a missing policy specialisation. MainloopPPUAiuMixedInput<Stages_, kContinous_, FinegrainedGs32> exists at dispatch_policy.hpp:292 and sets Schedule = KernelAiuMultistageMixedInput, so line 60's is_base_of_v check passes too. Both conditions on that specialisation look satisfied, which is where I stopped being able to progress.
  * NOT my quarantined table — INBOX 069 was that, and 070 retracts it.

What I could not determine is why CollectiveMma fails to match. Its specialisation head (ppu_mma_aiu_multistage_mixed_input.hpp:108-123) looks generic over the schedule. Candidates I cannot rank: the TileShapePair_ the dense bench passes (cute::tuple<TileShape, ScaleTileShape> with ScaleTileShape = Shape<Int<TN>, Int<scale_groups_v<TileShapeK, GroupSize>>>), a competing more-specialised CollectiveMma, or an argument whose type differs between the dense and grouped instantiation paths.

THE COMPARISON THAT SHOULD SETTLE IT, and it needs no hardware: grouped instantiates the same tag and the same tile through moe_grouped_ppu and it builds. Diff the two CollectiveMma argument lists — both type strings are available.

Priority: this blocks everything. 066 ① (does a two-warp dense row still abort now the COARSE assert is gone) cannot be tested, the dense sweep cannot run, and the box has been idle on failed builds for several rounds. Two of those rounds were my fault — an unpushed rename and a leftover config table — and this one is not.

- **Thread ID:** `019fd07e-78b3-7f20-8fd3-a849ebf4ad73`
- **Started / last event:** 2026-08-05 05:56 UTC → 2026-08-05 15:01 UTC
- **Working dir:** `/root/marlin_ppu/quactlize`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/05/rollout-2026-08-05T13-56-17-019fd07e-78b3-7f20-8fd3-a849ebf4ad73.jsonl`
- **Subagents spawned:** 0 (not exported)
- **Git:** `{"commit_hash": "43614c81f6cdaeaf64437b793490835f861c5514", "branch": "develop", "repository_url": "git@github.com:DrXuQian/quactlize.git"}`

Full transcript: [2026-08-05_019fd07e_Repo-root-marlin_ppu-quactlize-branch-develop-git.md](../transcripts/2026-08/2026-08-05_019fd07e_Repo-root-marlin_ppu-quactlize-branch-develop-git.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Repo /root/marlin_ppu/quactlize, branch develop — git pull first. Read INBOX 071. It is a build regression from your 1d2a621 (routing dense through the shared gs ladder) and it currently blocks the box entirely.

test_lowbit_dense_bench does not compile with the 227-row table — the normal one, four-warp minimum, no quarantined rows. Two errors, one root:

    gemm_universal_adapter.h:556: no type named 'InstructionShape' in
      GemmUniversal<packed_tuple<int,int,int,int>,
        CollectiveMma<PPU0010, MainloopPPUAiuMixedInput<6, C<256>, KernelAiuMultistageMixedInputFinegrainedGs32>, ...>>

    ppu_aiu_gemm_mixed_input.hpp:109: no type named 'SharedStorage' in
      CollectiveMma<PPU0010, MainloopPPUAiuMixedInput<12, C<256>, FinegrainedGs32>, TileShape(64,128,64), ...>

The chain as far as I could take it: CollectiveMma matches no specialisation, so its members are ill-formed; GemmUniversal's 3.x specialisation SFINAEs out because its enable_if reads CollectiveMainloop_::DispatchPolicy; the primary template has no ProblemShape; IsCutlass3GemmKernel (gemm.h:123 tests exactly that member) is false; the adapter takes its 2.x specialisation at line 542, which needs Mma::Shape / WarpShape / InstructionShape. The adapter error is the loudest and the least informative.

RULED OUT, so you do not repeat it:

  * NOT split-K. GemmUniversal's TileScheduler_ defaults to void (gemm_universal_decl.h:56) and the dense bench instantiates it with three arguments, so ppu_aiu_gemm_mixed_input.hpp:61's !is_same_v<TileScheduler_, SplitKSerialScheduler> passes. The user asked this directly; the answer is no, and the recorded 65% winner also came through moe_grouped_ppu::filter_and_run with no split axis.
  * NOT a missing policy specialisation. MainloopPPUAiuMixedInput<Stages_, kContinous_, FinegrainedGs32> exists at dispatch_policy.hpp:292 and sets Schedule = KernelAiuMultistageMixedInput, so line 60's is_base_of_v check passes too. Both conditions on that specialisation look satisfied, which is where I stopped being able to progress.
  * NOT my quarantined table — INBOX 069 was that, and 070 retracts it.

What I could not determine is why CollectiveMma fails to match. Its specialisation head (ppu_mma_aiu_multistage_mixed_input.hpp:108-123) looks generic over the schedule. Candidates I cannot rank: the TileShapePair_ the dense bench passes (cute::tuple<TileShape, ScaleTileShape> with ScaleTileShape = Shape<Int<TN>, Int<scale_groups_v<TileShapeK, GroupSize>>>), a competing more-specialised CollectiveMma, or an argument whose type differs between the dense and grouped instantiation paths.

THE COMPARISON THAT SHOULD SETTLE IT, and it needs no hardware: grouped instantiates the same tag and the same tile through moe_grouped_ppu and it builds. Diff the two CollectiveMma argument lists — both type strings are available.

Priority: this blocks everything. 066 ① (does a two-warp dense row still abort now the COARSE assert is gone) cannot be tested, the dense sweep cannot run, and the box has been idle on failed builds for several rounds. Two of those rounds were my fault — an unpushed rename and a leftover config table — and this one is not.

## Follow-up requests (chronological)

2. (2026-08-05 06:23 UTC) STOP work on 071 immediately. Its premise is false and I have retracted it. Read .coord/INBOX.md item 073 (pushed as 48b0817 on develop). The short version: The user ran the tree-state check on the box. Every source file matches HEAD and the actlize submodule matches (46a2b851), BUT `git status --porcelain` showed `M benchmarks/lowbit_dense_configs.inc` -- the box was carrying an uncommitted, STALE regeneration of that table: box working tree md5 9f2ab3dcc7411017a2c51bdd298af1ff 150 rows, 25 geometries, TM<=128, TK in {16,32,64} HEAD md5 1e588988cedd22caaec6df1035e1f21b 227 rows, 43 geometries, TM<=256, TK in {32,64} intersection of the two on (TileM,TileN,TileK,WarpM): ZERO Byte-identical h …
3. (2026-08-05 07:50 UTC) FINISH 061 FIRST. Nothing below is blocking and nothing below needs an answer today. Two new items are on develop. Neither asks you to stop what you are doing. 075 -- you already answered this in your last reply, and I agree with your recommendation: one controlled two-warp device run before admitting all 293 rows, quarantine untouched until then. Nothing further from you. 076 (a2d194f) -- the inventory of what can reach main. One mechanical finding and two rows that are yours: * 63 tracked files are compiled ELF probe binaries (l6..l70, leg1/3/5, sweep, ft_check, ftchk, l2l3, l5s, dev/low_bit/w2a16_swzl_probe) totalling 166.0 MB, which is essentially the whole 161 MB .git. Each appears once …
4. (2026-08-05 08:26 UTC) A DESIGN QUESTION FROM THE USER, and I think they are right and we are both wrong. I want your objection before anything changes. Congratulations on 061 -- I have read your summary and have no notes on the refactor itself. The user's words: "这些肯定要加回到dense的表啊。缺了什么导致不能加进去" then "现在这种做法太奇怪了" then, decisively, "如果是因为编译限制，应该这个不记录不就行了吗？trtllm是怎么做的". THE CATEGORY ERROR. ppu_tactic_space.hpp's Exclusion::DenseSubFourWarpDeviceAbort does not state a constraint. It states a MEMORY OF AN OBSERVATION -- "on 2026-08-04 these aborted" -- and it lives in the file that defines what is LEGAL. A space definition should say what the kernel can build; it should not carry a list of things that once failed on har …
5. (2026-08-05 09:53 UTC) THE DEVICE RUN YOU ASKED FOR HAPPENED. The two-warp dense row does not abort, and it beats grouped. [CUTLASS w4 gs=32 cfg=64x64:64x32:s3] M=2048 209.27 us | 328.4 TFLOP/s | cmp 65.7% tile 6494 GB/s (32.4x min, L2-served) | min 200 GB/s (7.2% HBM) against the grouped L=1 record of 211.33 us / 65.0% (BACKTEST A1, 2026-07-28), same shape, same geometry. Recorded as A0 in docs/BACKTEST.md (7445b87). WHAT IT SETTLES: * The sub-four-warp exclusion is refuted on hardware, not only in the compiler. You and I both concluded from source that there was no basis for it; this is the confirmation, and it arrived after the deletion rather than before -- which was the user's call, and it was the right one.  …
6. (2026-08-05 10:30 UTC) NEW TASK, ASSIGNED BY THE USER: you write the llama.cpp-side tune logic, I review it. This is a departure from the usual split (you kernels, me scaffolding) and it is deliberate -- the user asked for it this way. llama.cpp is at /root/llama.cpp on this machine. THE DESIGN TO COPY, AND IT IS NOT GemmPluginProfiler. I read TensorRT-LLM main earlier this week; that class no longer exists. Selection lives in tensorrt_llm/_torch/autotuner.py and its shape is: * Tuning is an EXPLICIT MODE: `with autotune(cache_path=...)`. Inference is pure lookup. The source comment is "Expect no cache miss in inference." * A cache MISS IS NOT AN ERROR. It takes fallback_entry() = (runner 0, tactic -1) plus warnin …
7. (2026-08-05 10:41 UTC) REVIEW: APPROVED. Build that boundary. Then a second task from the user below. Your design satisfies every constraint I set and two of them better than I asked: * Cold cache serves every request -- warn once, null config -> compiled default, outside the admitted domain -> llama's stock kernel. That is the path I wanted shown and you showed it. * Nothing remembers a failure. "Do not mutate the cache or remember the failure" is the exact property, and making the test prove "lookup never writes negative state" is stronger than my constraint, which only said not to have such a list. * Provenance: hashing the ACTUAL LOADED ELF resolved from a loaded symbol is better than what I asked for. A path  …
8. (2026-08-05 12:11 UTC) REVIEW OF BOTH. The llama.cpp cache is accepted. The GEMV work is accepted as far as it goes, and I measured what "as far as it goes" means -- it is narrower than the summary implies and I think you will want to know before anyone builds on it. ACCEPTED, and two details are better than what I asked for: * Unconditional checks in the CTest despite -DNDEBUG. assert() compiling out in Release is exactly how a test passes while checking nothing, and you pre-empted it. * "Any profiling-cost prune belongs to the tuner" with M>=16 kept legal. That is the TRT-LLM separation precisely -- enableCudaKernel's `m >= 16` prune is a tuning-time saving, never a legality claim -- and it is the distinction we …
9. (2026-08-05 12:17 UTC) GO AHEAD ON THE K-TAIL, on the plan you just wrote, with your own correctness bar as the gate. Your analysis is accepted in full and I have nothing to add to the mechanism. Three things I want on the record because they are the reasoning, not the result: * "Its utilization may be poor -- especially the half-warp Q3/Q5 case -- but that is a performance question for tuning, not a legality barrier." That is the exact line we spent today re-drawing. A slow shape is a tuning input; only an incorrect one is a legality claim. If Q3/Q5 at K=512 turns out to be terrible, it belongs in the tactic cache losing to a tensor-core row, not in a validity query refusing to exist. * The TRT-LLM check is what  …
10. (2026-08-05 13:06 UTC) NEXT TASK FROM THE USER: give MoE a scale_first entry in the .so. It is wiring, not a kernel, and I checked before asking. THE KERNEL ALREADY EXISTS AND IS THE VALIDATED ONE. moe_grouped_ppu::filter_and_run<QuantMode::FinegrainedScaleOnly, ...> is what benchmarks/test_scalefirst_bench.cu calls, and it is what produced BACKTEST A1 (211.33 us / 65.0%, int4 gs=32, M=2048 N=K=4096) -- the same collective A0 measured at 209.27 through the dense route at L=1. So nothing here needs a new mainloop; the path is measured and correct. What is missing is only that the shared library does not expose it. THE EXPORT SURFACE TODAY: dense: quactlize_ppu_dense_lowbit (scale_first) 3 entries quactlize_ppu_dens …
11. (2026-08-05 13:14 UTC) GO AHEAD ON grouped_lowbit. Your route reasoning is accepted and I am adopting your framing over mine. "`route` is the resident artifact/ABI contract -- not the logical operation or kernel family" is a sharper statement than the one I asked the question with, and the three guarantees follow from it rather than being bolted on: * a grouped_fully_quantized winner cannot hit a grouped_lowbit lookup * a cold grouped_lowbit key falls back through the grouped scale-first default, never through fully_quantized * provider competition belongs to the offline-format planner, and only becomes a winner property if both artifacts are simultaneously resident and deliberately compete The last one is the par …
12. (2026-08-05 13:44 UTC) A DESIGN QUESTION THE USER WANTS YOU IN ON. Explicit division first: I WRITE THE CODE for this one, you argue. You are mid-grouped_lowbit and the probe is a dev/ harness in my half; the user said only one of us writes. Please do not touch dev/ or scratchpad for this. THE USER'S PROPOSAL: make the SMALL-TileK folded layout canonical, and let LARGER TileK read the same bytes through a different cute layout, because the AIU copy is a strided shape anyway. His argument: small TileK is unavoidable (the run must reach the AIU's 32-byte minimum, so sub-byte widths must fold adjacent N columns), while large TileK is already legal unfolded -- so the weak constraint should bend to the strong one rathe …
13. (2026-08-05 13:52 UTC) THE FRAGMENT MAP IS READ, NOT REASONED, AND IT SAYS YES. Then one naming decision I want settled before either of us writes, because getting it wrong produces exactly the class of misreading that cost today. MEASURED (dev/fold_derivation/tilek_fragment_map.cu, committed 7ee1da2, stub-MMA harness, no box): (64,64) w64x32 [A0/A1 winner, 2 warps] TK64->TK128 YES TK64->TK256 YES thread 33 YES (64,64) w32x32 [4 warps] YES YES YES (16,32) w16x16 [D4 decode band] YES YES YES (64,128) w64x64 [int1 winner] YES YES YES Every row: the TileK=64 slots repeat, k advancing by EXACTLY 64. Two negative controls fire -- claiming k advances by 32 fails naming rep 1 slot 0, and a different warp shape fails on s …
14. (2026-08-05 14:03 UTC) YOUR CATCH WAS RIGHT AND THE CORRECTED PROBE STILL SAYS YES. Go ahead with the predicate change and the ABI -- the user is asleep, told us to finish tonight and to decide things ourselves rather than ask. So this is a decision, not a question. WHAT I FIXED, all three of them errors of mine: 1. Your catch: the probe used get_tiled_mma's PermutionK_=void branch. Now it builds Tile<WOM*16, WON*16, MmaPermK> with MmaPermK from the SHARED rule (cutlass::MixGemmMmaPermK<Bits, TK, F>), exactly as xplane_offline.hpp:92 does. 2. The user's catch: it compared two SEPARATE (TN,TK) tensors -- different shape, different N-stride -- so agreement between them said nothing about sharing one artifact. Now ON …
15. (2026-08-05 14:54 UTC) THE ALL-CONFIG COMPILE FOUND A MISSING CONSTRAINT, which is exactly what you said it was for. Your two handoffs are closed; this is a new one for you, precisely characterised. BOTH HANDOFFS DONE (a277ec3): * Cfg::Policy passes the artifact TileK, as kArtifactTileK -- a named alias of the binary constant, because the .inc is included AFTER Cfg so the macro is not visible there, and because TileShapeK now reads like the tactic quantity. * l110_unit_pack_abi links ppu_dense_layout.cu via a new GATE_SRCS map. It reports "unit-pack-abi formats=5 grouped=5 bad=0". * 18/18 lint. Three checks broke on the 7-field row and each break was the check being honest -- the table gate refused to parse `artif …

## Files edited via apply_patch (most frequent first)

- `/root/marlin_ppu/quactlize/ci/local_gates.py` ×14
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_multistage_mixed_input.hpp` ×14
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_mixed_input_2plane.hpp` ×13
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/ppu_mma_aiu_fold.hpp` ×13
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_backend.cu` ×11
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_mixed_policy.hpp` ×8
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/detail/ppu_mixed_metadata_policy.hpp` ×8
- `/root/llama.cpp/tests/test-ppu-tactic-cache.cpp` ×7
- `/root/marlin_ppu/quactlize/tools/tune.py` ×7
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_backend.cu` ×7
- `/root/marlin_ppu/quactlize/.coord/STATUS.md` ×6
- `/root/llama.cpp/ggml/src/ggml-cuda/ppu-so.cu` ×6
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_tactic_space.hpp` ×6
- `/root/marlin_ppu/quactlize/quactlize/include/moe_grouped_ppu.cuh` ×5
- `/root/marlin_ppu/quactlize/quactlize/include/fpA_intB_ppu.cuh` ×4
- `/root/marlin_ppu/quactlize/dev/fold_derivation/DENSE_GROUPED_PARITY_061.md` ×4
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/detail/ppu_mixed_pipeline.hpp` ×4
- `/root/llama.cpp/ggml/src/ggml-cuda/ppu-tactic-cache.cpp` ×4
- `/root/marlin_ppu/quactlize/quactlize/include/gemv_lowbit/gemv_launcher.hpp` ×4
- `/root/marlin_ppu/quactlize/tests/test_gguf_routes.py` ×4
- `/root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu` ×3
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l112_mixed_policy_parity.cu` ×3
- `/root/llama.cpp/ggml/src/ggml-cuda/ppu-tactic-cache.hpp` ×3
- `/tmp/artifact_tactic_policy_probe.cu` ×3
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l111_dense_gs32_match.cu` ×2
- `/root/marlin_ppu/quactlize/ci/check_dense_tactic_table.py` ×2
- `/root/marlin_ppu/quactlize/build.sh` ×2
- `/root/marlin_ppu/quactlize/dev/fold_derivation/l113_mixed_metadata_policy.cu` ×2
- `/root/llama.cpp/ggml/src/ggml-cuda/ppu-quactlize-so.h` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_ppu_config.h` ×2
- `/root/marlin_ppu/quactlize/tests/test_gemv_lowbit.cu` ×2
- `/root/marlin_ppu/quactlize/quactlize/include/quactlize_ppu_device.h` ×2
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/dispatch_policy.hpp` ×2
- `/root/marlin_ppu/quactlize/quactlize/csrc/device/ppu_dense_layout.cu` ×2
- `/root/marlin_ppu/quactlize/dev/fold_derivation/stub_inc/hggc_runtime.h` ×1
- `/root/marlin_ppu/quactlize/benchmarks/emit_tactic_configs.cpp` ×1
- `/root/marlin_ppu/quactlize/dev/fold_derivation/syntax_baseline/test_lowbit_dense_bench.cu.txt` ×1
- `/root/marlin_ppu/quactlize/benchmarks/lowbit_dense_configs.inc` ×1
- `/root/llama.cpp/tests/CMakeLists.txt` ×1
- `/root/llama.cpp/ggml/src/ggml-cuda/CMakeLists.txt` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/ppu_dense_configs.inc` ×1
- `/root/marlin_ppu/quactlize/benchmarks/gemv_perf_common.hpp` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/gemv_lowbit/gemv_kernel.hpp` ×1
- `/root/marlin_ppu/quactlize/tests/test_grouped_lowbit_exports.py` ×1
- `/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/builders/ppu_mma_builder.inl` ×1
- `/root/marlin_ppu/quactlize/quactlize/include/fold_traits.hpp` ×1
- `/root/marlin_ppu/quactlize/third_party/actlize/include/ppu_include.hpp` ×1

## Last assistant conclusions

### 2026-08-05 13:54 UTC

`ArtifactTileK` / `TacticTileK` is the right naming split. I’d use those names consistently, with `ArtifactLowFold` / `ArtifactHighFold` only as derived compile-time values.

I do not yet agree that `7ee1da2` closes the layout proof. Its `BuilderTiledMma` omits the `Tile<..., MmaPermK>` argument that the real builder supplies at [ppu_mma_builder.inl](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/builders/ppu_mma_builder.inl:647). The real offline map includes it at [xplane_offline.hpp](/root/marlin_ppu/quactlize/quactlize/include/xplane_offline.hpp:92). Thus the probe proves atom-fragment repetition, not yet the complete folded consumer mapping. I would correct that probe before changing the artifact ABI.

Answers to the four questions:

- Scale-first scale/zero planes are TileK-independent. They remain logical `[N,K/gs,L]`; `Scale_TileK` only controls how many consecutive groups a consumer stages. No second artifact TileK is needed for them.
- One combined artifact should carry one `ArtifactTileK`, from which both low/high folds are derived. Q3 at 64 therefore means `(F_low,F_high)=(2,4)`. The compiled provider must receive both; today the builder carries the low fold but re-derives the high fold from consumer TileK.
- The AIU run does not stay 32 bytes. With canonical F, it grows from 32 to 64/128 bytes as `TacticTileK` grows. It still physically carries all F adjacent N columns, but this requires the folded collective; the ordinary collective cannot reinterpret those bytes.
- Fully-quantized is more constrained. Packed metadata is enabled only when `Scale_TileK` covers exactly the packed unit’s group count—currently effectively one superblock per k-tile. Canonical code planes may eventually be shared, but packed-unit staging/indexing remains tied to its own TacticTileK domain.

Once the corrected full-map probe proves completeness/injectivity, my predicate change is:

1. Derive artifact folds exclusively from `ArtifactTileK`.
2. Use `TacticTileK` for fragment capacity, topology, smem, delivery size, and kernel geometry.
3. Require the compiled provider’s physical tilers/descriptors to use the artifact folds.
4. Reject rows where either artifact fold cannot divide or completely cover the tactic geometry.

Separately, grouped_lowbit is complete and pushed as `10ebf78`:

- All six grouped scale-first exports.
- `FinegrainedScaleOnly` provider and queryable validity.
- Distinct `grouped_lowbit` tactic-cache route and alias control.
- Shipping-route, ABI, syntax, registry, portability, and cache-writer gates pass.

`origin/develop` now points to `10ebf78`; the quactlize worktree is clean.

### 2026-08-05 14:37 UTC

Implemented and pushed:

- quactlize `c8246ad`
- actlize `5d40f7ca`

The predicate now separates `ArtifactTileK` from `TacticTileK`, validates complete tiling and exact 32-byte runs, and derives both artifact folds independently. The builder preserves those folds in its physical descriptors; Q3 TK64 correctly carries `(F_low,F_high)=(2,4)` even for a TK256 consumer. See [ppu_mixed_policy.hpp](/root/marlin_ppu/quactlize/quactlize/include/ppu_mixed_policy.hpp:148) and [ppu_mma_builder.inl](/root/marlin_ppu/quactlize/third_party/actlize/include/cutlass/gemm/collective/builders/ppu_mma_builder.inl:744).

Scale addressing needs no second artifact field: scales remain logical `(N,K/group_size)` data; only the consumer window changes with `TacticTileK`. Larger tactics use multiple integral 32-byte AIU deliveries rather than changing the delivery granule.

Validation passed:

- Full 293-row dense syntax gate: clean, zero new errors.
- Shipping `.so` backend syntax: clean.
- Dense/grouped policy parity.
- Four grouped syntax variants.
- Cross-TileK int2 and Q3 provider probe.
- Producer/unit-pack ABI when correctly linked: `bad=0`.

Two handoffs remain in the other ownership area:

- [test_lowbit_dense_bench.cu](/root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu:269) must pass `LOWBIT_DENSE_CFG_ARTIFACT_TILEK` to `Cfg::Policy`.
- The registered `l110_unit_pack_abi` gate needs to link `ppu_dense_layout.cu`; currently its implementation passes but the registered row fails at link.

### 2026-08-05 15:01 UTC

Landed and pushed `492edef` on `develop`.

- Added `ScaleCopyCoverage` to [ppu_tactic_space.hpp](/root/marlin_ppu/quactlize/quactlize/include/ppu_tactic_space.hpp).
- Conservatively checks gs16 using the collective’s exact formula.
- Added positive, boundary, and gs32-pass/gs16-fail compile-time controls.
- Multi-TileK regeneration produces **632 rows**, not 584: removing 111 illegal preferred rows exposes 48 legal fallback/guard rows.
- Distribution: `{64:293, 128:224, 256:115}`, with zero gs16 violations.
- TileK64 remains unchanged.
- Mixed-policy gates `l112` and `l113` pass.

The worktree is clean and synchronized with `origin/develop`.
