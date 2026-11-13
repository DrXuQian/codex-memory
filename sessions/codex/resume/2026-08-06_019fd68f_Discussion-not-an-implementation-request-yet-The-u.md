# Resume brief: Discussion, not an implementation request yet. The user asked why the build is slow and whether we already parallelise; I measured, and I think the existing task description for this points the wrong way. Want your view before either of us writes anything.

MEASURED TODAY:

  build.sh:318                 `make -j"${JOBS:-$(nproc)}"` — parallel make is already on
  CMakeLists.txt.in:308,494,802  _GEMV_UNIT_SRCS, _SK_SRCS, _MOE_UNIT_SRCS — gemv, split-K and the MoE sweep
                               each generate ONE .cu PER CONFIG, which is what gemv_perf_unit.inc,
                               moe_splitk_unit.inc and moe_bench_unit.inc exist for
  CMakeLists.txt.in:192-193    test_lowbit_dense_bench is ONE translation unit
  lowbit_dense_configs.inc     632 rows, expanded by X-macro inside that single TU, times the group-size arms

So `-j` cannot help the dense bench at all: 632 instantiations in one file get one core while the rest idle. That also explains the local numbers — the dense syntax check is 50s+ where the MoE ones are ~7s.

Task #29 is currently worded "Parallelise build.sh: prepare the overlay once, run N cmake+make concurrently". I think that is aimed at the wrong object: we do not need N builds, we need THIS build split into many TUs, exactly the treatment gemv/splitk/moe already have.

THREE THINGS I WANT YOUR VIEW ON, because I can argue myself into and out of each:

1. THE CONFIG SOURCE. If CMake generates dense units, where does it get the rows? The MoE generator holds its own axis lists (_MOE_TM_LIST etc.) IN CMakeLists.txt.in, while dense's rows come from benchmarks/emit_tactic_configs.cpp into a generated .inc that stamps a hash of ppu_tactic_space.hpp. Copying MoE's pattern would give dense a second source of truth and the two would drift — we have paid for that shape twice this week. My instinct is CMake should PARSE lowbit_dense_configs.inc (it is an X-macro, trivially parseable) rather than restate the axes. Do you see a reason that is wrong, and is the MoE side's own axis-list-in-CMake something we should be fixing at the same time?

2. THE BINARY MUST STAY ONE. --search_configs times every compiled config in one process, and the sweep driver depends on that (one process per SHAPE, not per config, because a device assert costs only that shape). So the split has to be many TUs linked into one executable, splitk-style — one function per unit, main calls them all — not 632 executables. Confirm I am not missing something in how the dispatch macro would have to change: today LOWBIT_DENSE_DISPATCH expands the whole list into an if-chain inside one function, and that chain is what maps a runtime TileCfg to a compiled Cfg<>.

3. GRANULARITY, and this is the one I would rather measure than argue. Each TU re-parses the whole cutlass/actlize header chain, so 632 TUs pay that 632 times. The MoE side has already paid this cost at 15 units and at whatever the MoE sweep's count is — you have those numbers or can get them cheaply. Is per-config right for dense, or should it be batches of k configs per TU? If you have the MoE per-unit wall clock, that is the input that settles it.

Also: do you know why dense never got a unit generator when the other three did? If there is a reason in the dispatch structure rather than just history, that changes the answer.

No code yet — I want the answer to 1 and 3, and a confirmation or correction on 2.

- **Thread ID:** `019fd68f-6fca-7312-a39f-f94947a390ea`
- **Started / last event:** 2026-08-06 10:12 UTC → 2026-08-06 10:18 UTC
- **Working dir:** `/root`
- **Model:** gpt-5.6-sol  ·  **Source:** mcp  ·  **Codex CLI:** 0.146.0
- **Original rollout:** `/root/.codex/sessions/2026/08/06/rollout-2026-08-06T18-12-32-019fd68f-6fca-7312-a39f-f94947a390ea.jsonl`
- **Subagents spawned:** 0 (not exported)

Full transcript: [2026-08-06_019fd68f_Discussion-not-an-implementation-request-yet-The-u.md](../transcripts/2026-08/2026-08-06_019fd68f_Discussion-not-an-implementation-request-yet-The-u.md)

## How to continue this work in Devin

1. Open the original working directory (or its equivalent) shown above.
2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. Verify the current state of the repo before changing anything.`
3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript as the source of truth and re-check facts against the code.

## Original request

Discussion, not an implementation request yet. The user asked why the build is slow and whether we already parallelise; I measured, and I think the existing task description for this points the wrong way. Want your view before either of us writes anything.

MEASURED TODAY:

  build.sh:318                 `make -j"${JOBS:-$(nproc)}"` — parallel make is already on
  CMakeLists.txt.in:308,494,802  _GEMV_UNIT_SRCS, _SK_SRCS, _MOE_UNIT_SRCS — gemv, split-K and the MoE sweep
                               each generate ONE .cu PER CONFIG, which is what gemv_perf_unit.inc,
                               moe_splitk_unit.inc and moe_bench_unit.inc exist for
  CMakeLists.txt.in:192-193    test_lowbit_dense_bench is ONE translation unit
  lowbit_dense_configs.inc     632 rows, expanded by X-macro inside that single TU, times the group-size arms

So `-j` cannot help the dense bench at all: 632 instantiations in one file get one core while the rest idle. That also explains the local numbers — the dense syntax check is 50s+ where the MoE ones are ~7s.

Task #29 is currently worded "Parallelise build.sh: prepare the overlay once, run N cmake+make concurrently". I think that is aimed at the wrong object: we do not need N builds, we need THIS build split into many TUs, exactly the treatment gemv/splitk/moe already have.

THREE THINGS I WANT YOUR VIEW ON, because I can argue myself into and out of each:

1. THE CONFIG SOURCE. If CMake generates dense units, where does it get the rows? The MoE generator holds its own axis lists (_MOE_TM_LIST etc.) IN CMakeLists.txt.in, while dense's rows come from benchmarks/emit_tactic_configs.cpp into a generated .inc that stamps a hash of ppu_tactic_space.hpp. Copying MoE's pattern would give dense a second source of truth and the two would drift — we have paid for that shape twice this week. My instinct is CMake should PARSE lowbit_dense_configs.inc (it is an X-macro, trivially parseable) rather than restate the axes. Do you see a reason that is wrong, and is the MoE side's own axis-list-in-CMake something we should be fixing at the same time?

2. THE BINARY MUST STAY ONE. --search_configs times every compiled config in one process, and the sweep driver depends on that (one process per SHAPE, not per config, because a device assert costs only that shape). So the split has to be many TUs linked into one executable, splitk-style — one function per unit, main calls them all — not 632 executables. Confirm I am not missing something in how the dispatch macro would have to change: today LOWBIT_DENSE_DISPATCH expands the whole list into an if-chain inside one function, and that chain is what maps a runtime TileCfg to a compiled Cfg<>.

3. GRANULARITY, and this is the one I would rather measure than argue. Each TU re-parses the whole cutlass/actlize header chain, so 632 TUs pay that 632 times. The MoE side has already paid this cost at 15 units and at whatever the MoE sweep's count is — you have those numbers or can get them cheaply. Is per-config right for dense, or should it be batches of k configs per TU? If you have the MoE per-unit wall clock, that is the input that settles it.

Also: do you know why dense never got a unit generator when the other three did? If there is a reason in the dispatch structure rather than just history, that changes the answer.

No code yet — I want the answer to 1 and 3, and a confirmation or correction on 2.

## Last assistant conclusions

### 2026-08-06 10:18 UTC

Your diagnosis is right: Task #29 targets the wrong layer. [`make -j`](</root/marlin_ppu/quactlize/build.sh:318>) is already active; the serialization is created by registering dense as one source at [CMakeLists.txt.in](</root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:191>). The task should be about sharding dense template instantiations inside the existing target, not running multiple builds.

### 1. Config source

CMake should consume `lowbit_dense_configs.inc`. I see no good reason to restate its axes.

Parsing the emitted X-macro is reasonable because its syntax is deliberately rigid: anchored `X(TM,TN,TK,WM,WN,ST,ACR,B)` rows. CMake would be a second consumer of the authoritative artifact, not a second authority.

The parser should fail closed:

- Register the `.inc` as a configure dependency, so changing it reruns CMake.
- Accept only the exact seven-integer row form.
- Validate parsed count against `LOWBIT_DENSE_CFG_ROWS`.
- Reject duplicates and malformed rows.
- Include all fields, including `ACR`, in generated symbol identities even though runtime names currently omit it.
- Generate files through `copy_if_different`, as the existing unit generators do.

I would not make the emitter produce a second committed CMake manifest unless both outputs are regenerated and checked atomically. That creates precisely the two-generated-artifacts-can-drift problem you are trying to remove.

The MoE axes are indeed the same structural defect. This is already called out explicitly in [BENCH_DESIGN.md](</root/marlin_ppu/quactlize/docs/BENCH_DESIGN.md:14>). However, I would not silently migrate MoE in the dense build-speed patch. The current emitter applies primary/guard pruning at [emit_tactic_configs.cpp](</root/marlin_ppu/quactlize/benchmarks/emit_tactic_configs.cpp:308>), while the MoE Cartesian product intentionally reaches configurations outside that policy. Pointing MoE at `--space=grouped` therefore may change experimental coverage, not merely its build mechanism.

My preferred scope:

- Build a table parser/batcher reusable by both.
- Use it for dense now.
- Migrate MoE separately once “pruned grouped table” versus “full legal grouped sweep” is explicit. If full coverage remains required, the emitter needs an unpruned/full mode first.

### 2. One binary

Confirmed: many TUs, one executable, one process per shape.

One correction to “one function per unit”: with batching, the compile unit and dispatch unit should be different things. I would use one exported wrapper per config, with several wrappers defined in each `.cu`. The runtime registry can hold the wrapper function pointer alongside `TileCfg`.

The current macro cannot remain in its present form. It names every `Cfg<GroupSize,...>::Gemm` inside the main TU at [test_lowbit_dense_bench.cu](</root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu:349>); retaining that expansion would instantiate everything serially again.

Instead:

- Each generated batch TU instantiates its assigned `Cfg<>` rows and exports ordinary non-template wrappers.
- Each wrapper handles the enabled group-size arms internally.
- `TileCfg` maps directly to its wrapper.
- `--config` calls one wrapper.
- `--search_configs` keeps looping over the same registry in the same process, as it does now at [test_lowbit_dense_bench.cu](</root/marlin_ppu/quactlize/benchmarks/test_lowbit_dense_bench.cu:1173>).

So the runtime `TileCfg → compiled Cfg<>` mapping still exists; it merely crosses an external function boundary instead of expanding a 632-case template chain in `main`.

### 3. Granularity

Per-config is not the right default for 632 rows. The repository already contains the measurement that settles the direction:

- Header parse: roughly 4.2–5 seconds.
- Each instantiated kernel: roughly 2.5–3 seconds.
- Three kernels in one unit: about 12 seconds.
- Forty-two kernels: about 109 seconds.
- For 642 kernels, the recorded model gives:
  - 128 units: 19.2 seconds
  - 192 units: 14.2 seconds
  - 360 units: 19.1 seconds

Those numbers are recorded at [CMakeLists.txt.in](</root/marlin_ppu/quactlize/quactlize/csrc/CMakeLists.txt.in:747>) and [moe_bench_unit.inc](</root/marlin_ppu/quactlize/benchmarks/moe_bench_unit.inc:4>). Their conclusion is exactly: target roughly one TU per effective compiler slot. Above that, extra compile waves mostly buy repeated header parsing.

For 632 rows and about 192 useful slots, the first serious candidate is therefore four configs per TU:

- `ceil(632 / 4) = 158` TUs
- one compile wave on a 192-slot box
- with all four group-size arms, up to 16 kernel instantiations per TU
- with `BENCH_GS`, four per TU

I would make batch size selectable and measure clean hgcc builds at `k = 1, 2, 4, 8`, holding `JOBS` fixed and recording wall time plus peak memory. The likely winner is `k=4`, but memory matters: [`build.sh`](</root/marlin_ppu/quactlize/build.sh:315>) records that concurrent front ends can consume gigabytes and OOM. In general the target is:

`number of TUs ≈ effective parallel compiler slots`

where effective slots are constrained by both `JOBS` and memory, not merely physical core count.

### Why dense never got this treatment

The history looks like inertia, not a dispatch constraint:

- The initial August 1 import already had the MoE unit generator because MoE began as a broad sweep.
- Dense began with only 17 hand-written configurations in one TU.
- On August 4 those became a generated X-macro table.
- On August 5 the table grew to 632 rows, but the original compilation topology remained unchanged.

The BODY-carrying dispatch macro makes the refactor less mechanical than split-K, because `Cfg<>`, `run<G>`, `Options`, and `Result` need a shared TU-facing interface. But it is not a fundamental obstacle.

I would rewrite Task #29 roughly as:

> Shard `test_lowbit_dense_bench` template instantiations into generated, batched translation units linked into the existing executable. Derive rows from `lowbit_dense_configs.inc`, preserve the single-process runtime registry and `--search_configs` behavior, and choose batch size from clean hgcc timing against the effective `JOBS`/memory limit.

No files were changed.
