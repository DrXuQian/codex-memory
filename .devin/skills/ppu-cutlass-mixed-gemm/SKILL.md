---
name: ppu-cutlass-mixed-gemm
description: >
  Debugging and perf method for the PPU (T-Head ZW810 / ppu001) cutlass3 "actlize" mixed-input
  W4A16/W2A16/W1A16 grouped GEMM and the TWO-PLANE bit-plane formats (Q3 = int2+int1, Q5 = int4+int1,
  Q6 = int4+int2): the swzl/AIU delivery bound, the power-of-two register billing that governs
  occupancy, the converter-amortisation ceiling, the w64x32 warp shape sweeps forget, APG = gs/16,
  and the layout traps in tCrB_mma / partition_B / make_fragment_like. Invoke when working on
  Kernels/general/w4a16_gemm/cutlass_w4a16 or third_party/actlize collectives
  (ppu_mma_aiu_fold.hpp, ppu_mma_aiu_multistage_mixed_input.hpp, ppu_mma_aiu_mixed_input_2plane.hpp,
  fast_numeric_conversion_for_mix_gemm.h), chasing a numeric MISMATCH in a fold/chunk path, or
  deciding whether a register/occupancy change is worth building. Read the METHOD section before
  any multi-round debugging -- it is where the time actually goes.
---

# PPU cutlass mixed-input GEMM: method and traps

Local container has **no PPU SDK** — edit locally, build/run on the box (`aiswu96`,
`/sim/eec/shared/junfu.qx/Kernels`). Local nvcc + RTX 5090 exist but **5090 cannot proxy PPU perf**.
`fold_derivation/` holds ~50 box-free harnesses (`l1`..`l68`, `ft_check`, `gen_guard_check.sh`,
`syntax_check.sh`, `legacy_pipeline.hpp`); run them before every box round. **`rm -f` each binary and
print the compiler's error count** — a stale `/tmp` binary will happily print PASS for a build that
failed. `syntax_check.sh` reads `EXTRA_DEFS`, and a flag-on run is diffed against the flag-OFF
baseline, so a macro-only breakage shows as NEW ERRORS.

## METHOD — this is where the rounds go

**A RELATION YOU WRITE DOWN BEATS NOTHING; READ IT OFF THE OBJECT.** This single shape produced NINE
wrong findings in one session, in five disguises, and every one of them made a harness declare that a
BOX-VALIDATED configuration was broken — the expensive direction, because it sends you to fix working
code:

* a **stride** hardcoded (`cvt_in`'s mode-1 stride written as 32 half2; it is 64 at Block_K=256) —
  three separate times
* a **structural relation** hardcoded ("plane 2 always folds twice as hard as plane 1" — false at the
  one Block_K where both factors are 1)
* a **coverage space** hardcoded (indexed by `k_block` when one `(k_block, ii)` reaches only two of
  four vregs, so the space was double-counted)
* a **launch parameter** hardcoded in the gate itself (`WM=WN=32` for every row, while int1 at TK=64
  cannot RUN at WN=32 — the very reason the bit-granular packer exists)
* an **arithmetic unit** hardcoded (`ptr + e*K*N` on a sub-byte pointer; `sizeof(uint2b_t) == 1`, so
  that advances BYTES and expert 1 read past the allocation)
* a **tool's output format** hardcoded (grepping `make.log` for `-D...`, when the device compiles are
  `add_custom_command` with a COMMENT and make.log never contains a compile line at all)
* a **compiler diagnostic's shape** hardcoded, twice in a row: the syntax gate grepped `': error'`, so a
  source that could not find its headers was reported CLEAN for several edits — a missing include is
  `path:line:col: fatal error:`. I then "fixed" it FROM MEMORY by adding `catastrophic error` (the EDG
  form) and it still passed, because the actual line was the third form. Match `: <kind>: ` and read the
  output.
* **CMake's list semantics** hardcoded (`"…|4|2|32;64"` as one table row — `;` IS the separator, so
  `foreach(IN LISTS)` splits the row and the stray fragment has one field). A python mirror of the same
  table cannot see this; its `split(';')` has no such semantics, so the mirror passed while the real
  configure died six times per row.
* an **overlay's extension whitelist** hardcoded, then hardcoded again in the check meant to guard it
  (`*.inc` missing → `fatal error: moe_bench_unit.inc` 100+ lines into a parallel hgcc build; the
  inverted check then failed on `*.acurep`, an untracked artifact absent from a clean checkout, because
  I enumerated the extensions I could SEE locally)
* the **legal half only** tested: I verified TileK=32's LEGAL configurations compile and never checked
  that illegal ones filter — one hour after doing exactly that test for TileK=64. The box found it.

The rule: **if the quantity exists on an object — a cute Layout, a Tensor, a generated build file, a
compiled binary — ask the object.** A harness that restates it is testing the restatement. And when a
harness contradicts a passing box run, suspect the harness first: it was right nine times out of nine.

**Put a row with a KNOWN answer in every new harness.** Eight of those nine cost a full box round each.
The ninth cost ONE READ, and the only difference was that the harness contained an int1 row whose
grouped result is independently validated elsewhere: it failed too, so "the harness is wrong, not the
kernel" was available before any debugging. A second free signal came from the same run — the subject
returned the same value under two different L while the REFERENCE returned two, for the same input row,
which points at the reference without a single line of reading. **A new test with no known-good row can
only tell you that something is broken, never which of the two things it is.**

**A whole-output mismatch whose residual does not depend on the quantised data is never the kernel.**
Q6/Q5 read `bad=32768/32768` at every configuration, with identical values across configurations and
`got - exp = -16 * sum_k A*dl` carrying no `q` dependence at all. That forces
`sum_k A*dl*(emitted - q) = -8*sum_k A*dl` for every `(m,n)`, hence `emitted == q - 8` exactly — so the
two-plane combination was already correct and the defect was a sign in the golden's zero point. A 100%
failure rate reads like a broken kernel; the residual's structure is what distinguishes the two.

**Count MACHINE operations, not source operations, and the tool is local.** A "6 ops per half2 down to
4" converter optimisation was written, committed with the number stated as fact, and turned out to be a
complete no-op: `nvcc -arch=sm_80 -O3 -cubin` plus `cuobjdump -sass` gives BYTE-IDENTICAL SASS for both
forms, because the compiler already composes compile-time shifts and already fuses `x | (y & m)` into a
`lop3`. Before trading readability for an instruction count, compile both and count.

**Two quantities sharing a name fail in a way that looks like a subtle regression.** `P2_DIV` meant both
the COPY-STEP ratio `DL1/DL2` and the VREG ratio `LowBits/HiBits`. They coincide exactly at the
configuration that was already working, so conflating them left THAT row passing while changing every
other row — which reads as "my generalisation broke something subtle" and is really a name collision.
If two derived quantities can ever differ, they must not share an identifier.

**A stale binary makes a failed build print PASS.** Running a gate suite in a compound command after a
`cd` that did not persist: nvcc could not find the sources, and seven of nine gates still printed their
success line from binaries left in `/tmp`. `rm -f` the binary first and print the compiler's error count
next to the verdict.

**Print the candidate next to ground truth. Do not swap expressions and diff totals.** Four rounds
went to the latter on one layout composition and produced nothing; printing both for a handful of
`(t, f)` produced the answer in one step. Same technique cracked a ladder's unexplained 10 points and
an int2 pairing bug.

**Decode a numeric MISMATCH into the parameter that is wrong.** With a controlled probe
(`scale(g,n) = 1 + (1/16)*((5n+3g) mod 13)`), solve each printed `got` for `g` and `n`. "every line
gives g=2 where g=0 is right" pinpointed a pipeline-stage off-by-one that no amount of reading index
math would have found. Choose the probe's **period coprime to the displacements you're hunting** —
a period-8 pattern is blind to the 8/16/32 offsets a broken fragment map produces.

**A harness that confirms a wrong assumption is worse than no harness** — it reads as evidence. One
harness verified a chunk split correctly, of the wrong model, for three rounds. Fix: **print the
layout you are reasoning about**, do not restate it.

**"Correct" at one config is not evidence.** A config passed while six failed, purely because with
two warps the warp-order swap it depended on is the identity.

**A cute layout describes what the PROGRAM asks for; whether the hardware does it is a codegen
question.** For register-resident, fully-unrolled, provably-equal values the compiler usually wins
first — a "4x redundancy" in the scale fragment measured as a **complete no-op**. Check that a
cute-level redundancy survives to the ISA *before* trading idiom for it. On this toolchain that means
acu: actlize's cute will not compile for device under nvcc (`__HGGCCC__`-gated globals), so the PTX
cannot be read.

**Never assume `git submodule update` ran.** A stale actlize made an A/B compare two identical
binaries with no trace in any log. Defence: a version macro in the collective that the harness
`#error`s on (`PPU_SCALE_FRAGMENT_API`).

**Make the log describe its own run.** Three separate rounds were wasted on logs that did not:
a perf lambda timing a different tile than the correctness check; a probe whose varying-scale mode
left no trace; a sweep printing the unchunked register model in a chunked build. Print the dispatched
shape, the active flags, and which model produced the numbers.

**`#if` leaves the other branch un-type-checked.** An int1-only emitter reached the box instantiated
for `uint2b_t` (576 errors) because the guard was `#if`. Use `constexpr bool` + `if constexpr` so both
branches type-check for every instantiation.

**A `static_assert` makes a wrong assumption loud, not cheap.** Do not build dependent code on top of
one — measure or derive the quantity first. And do not add an assert to protect your own shortcut: it
makes an implementation limitation read as a property of the design.

**Never hand-rebuild an existing rule in order to compare against it — CALL it.** Three fake findings
in one session came from exactly this: a "plane 2's own map" reconstruction that skipped `MixGemmEmit`
and `pi` and "proved" two maps differed in 8160/8192 entries; a reference map in a composition check
that described nothing; and a validation that was circular because the map under test had been derived
from the very pairing it was being checked against. If the rule exists in code, instantiate it.

**Self-consistency cannot catch a premise that is wrong on BOTH sides.** A map was checked against a
target built from the same conflation (physical row identified with logical column) and passed
cleanly — the comparison said nothing. **Gate a derivation at both ends against something that already
runs.** Concretely: emit the buffer and diff it byte-for-byte against the shipped offline, at a
configuration the box measures as correct. That check caught three separate wrong derivations in a row,
each of which had looked internally consistent.

**Choose a gate configuration that ALREADY WORKS, and make failure of the gate fatal.** A composition
check reported the working config broken and the broken config fine — which immediately revealed the
model was wrong, not the kernel. Without the gate it would have "confirmed" the broken config.

**One change per measurement.** A round bundled a kernel index change with a batch of portability
fixes; the result (worse) was then read as evidence against the index change, and it took a full
re-derivation to notice the experiment had two variables.

**Retract in the file, not by deleting it.** A wrong explanation sitting next to working code has cost
this repo real time before. Leave the derivation, mark it RETRACTED, and say what actually settled it.

**When a config change moves several things at once, a one-variable-per-rung NUMERIC ladder beats any amount of
derivation** -- and it is the only instrument whose gate is the golden rather than your own model. Five rounds of
layout derivation failed on a 2-plane Block_K=64 mismatch because the attempt had moved TN, WN and TK-with-fold
together. A five-rung ladder (base / TN / WN / WM / TK) localised it to `WM 32->64` in ONE box round, and the cause was
not a layout at all.

**A tiled copy can ask for more thread slots than the CTA has, and a modulo will hide it.** The scale copy's thread
layout was `(Scale_TileN/8, Scale_TileK)` unconditionally, sliced with `thread_idx % (ThrH*ThrW)`. Every config had
`ThrH*ThrW <= NumThreads` until one with `WOM = TM/WM == 1` halved the CTA: 128 slots against 64 threads, layout (16,8)
mapping `t -> (t%16, t/16)`, so **four of eight scale groups were never loaded** -- 41% of elements wrong. Every layout
involved is individually well-formed, so no layout algebra can see it. Cap the thread extent at `NumThreads/ThrW`, give
each thread the remaining elements, and `static_assert` the slot count against the CTA size. **Whenever a copy is
sliced by `thread_idx % X`, X is a claim about the launch geometry -- assert it.**

**Derive the right subsystem.** The closed loop over the B path (offline, delivery, emission, destination,
mma-expectation, scale-group, plus coverage) was CLEAN at the failing config -- correctly. Before spending rounds on a
derivation, ask which subsystem the ladder implicates; a clean model of the wrong subsystem is indistinguishable from
progress.

## Three ways an `if constexpr` guard does not guard

A legality predicate in front of a config sweep looks airtight and is not. All three of these shipped a
broken build or a meaningless gate in one session.

**1. `if constexpr (false)` suppresses instantiation ONLY inside a templated entity.** In a plain
function the discarded branch is still instantiated, so `moe_ok<...>() == false` does not make an
illegal shape compile away: `(TileM=32, WarpM=64)` produced **99 errors** headed by
`gemm_operands.hpp: division by zero`, because `warpOnM = TM/WM = 0` and the collective builder degrades
to `int` (same failure as TM=16/WM=32). Fix: make the body `template <int Dummy>` and call it with `<0>`.
The illegal units then cost a 4 s empty compile.

**2. A template argument is instantiated regardless of a later gate — even INSIDE the gate.** Two
separate box failures from this, so the rule is: **make the template TOTAL, do not rely on the guard.**

* `constexpr int _F = fold::FoldTraits<Bits,…>::F;` sitting ABOVE `if constexpr (moe_ok<…>())` fired
  FoldTraits' own `delivery <= slots` static_assert for configurations `moe_ok` rejects — the whole
  TileK=32 build died on int2 at WarpN=32 (slots 32 < delivery 64), already excluded by the predicate.
* Then the same shape again with the argument INSIDE the gate: `report(…, fold::warps_per_cu_chunked<…>)`
  in the non-taken branch still instantiated, and `warps_per_cu_chunked<128,32,256,32,64,…>` died on
  `64 / warps` with `warps = (128/32)*(32/64) = 0`. Naming a constexpr **variable template** as an
  argument instantiates it in a discarded statement.

So: keep "compute a derived quantity" separate from "assert this config is sane" (use an assert-free
`constexpr` function for the value), and make every model in `fold_traits.hpp` total — `warps < 1`
returns 0 rather than dividing. A shape with no legal warp tiling has an answer; it is zero.

**3. A `static_assert` with a NON-dependent false condition fires from inside a discarded branch.** So a
probe placed in the `if constexpr` body counts CANDIDATES, not legal rows — mine reported 42 at both
TileK=64 and TileK=128 and looked perfectly consistent, because 7 (TileM,WarpM) x 2 TileN x 3 stages = 42
either way. Put the probe OUTSIDE the gate with the condition NEGATED
(`static_assert(!moe_ok<…>(), "PROBE")`) and it fires once per LEGAL row: then 42 / 38, matching an
independent mirror on a case that DISCRIMINATES.

That last point is the general one: **a counter that agrees with the right answer for the wrong reason is
worse than no counter.** The unit generator also printed "128 generated units" while thoroughly broken,
because 8 malformed iterations x 16 equals 5 correct formats x 16.

## A harness that can rank a failed launch has no bound on how wrong its verdict is

`launch()` in `moe_grouped_ppu.cuh` returns **void** and reports failure by `printf` — `can_implement`,
workspace, `initialize`. So a timing harness measures an empty call. The MoE sweep reported
`q5 128x128:256 w32x64 s3` at **3.17 us as its FASTEST config**: 21 MB in 3.17 us is 6.6 TB/s against a
2.77 TB/s peak. Four of five per-format winners were `init failed` rows.

The cause was another incomplete smem model — `moe_ok` had `(TM*TK*2 + TN*TK*bits/8)*Stages` with **no
scale or zero tile**, so 264 KB computed as 252 KB and the predicate passed a config the runtime refuses.
`fold_traits.hpp` already had the complete expression.

**Two nets, because the first only catches known causes:**
1. a **failure counter** in the launcher (`moeg_fail_count()`), incremented at each early return — no
   signature change, so the twenty-odd other callers are untouched;
2. **physical impossibility**: reject any row whose ACTIVE WEIGHT TRAFFIC ALONE would need more than HBM
   peak in the measured time. Cause-agnostic, and it would have caught this immediately.

Net 2 is the one worth copying into any new perf harness. It is three lines and it makes "the kernel did
not run" impossible to confuse with "the kernel was fast".

## Gates go stale, and negative controls need their own directory

* **A gate that holds a COPY of what it gates will disagree with it.** An extracted `.cmake` copy of the
  unit generator reported OK within the hour while the real generator had moved to per-format Best slots
  and main no longer compiled. Slice the source at RUN TIME (`awk` from `set(_MOE_FORMATS)` to
  `ppu_w4a16_executable(`) instead of copying it.
* **Run the negative control in a SEPARATE output directory.** The check starts with `REMOVE_RECURSE`, so
  running the broken variant into the shared tree wipes the good one and dies partway — and the wreckage
  reads exactly like a real failure. I diagnosed "q6 is missing WarpN=64" from the corpse of my own
  negative control.
* **Verify a gate in BOTH directions every time**: it must fail on the bug and pass on the fix. Every
  gate in this work that was checked in only one direction was later found blind.

## The local gate MUST instantiate the collective — otherwise "clean" means nothing

`nvcc -cuda` over the harness parses the collective but **does not instantiate it**, so every
template-DEPENDENT error in the mainloop is invisible: a deliberate undefined symbol there is caught
(non-dependent, parse time) while a wrong copy coordinate is not. Two static errors shipped to the box
behind that gap while the local check said "clean".

Three flags are load-bearing:

* `-arch=sm_80` — without a real arch `__hfma2` is undeclared, that is an error, and **any error at all
  stops EDG's template instantiation**
* `--expt-relaxed-constexpr` — an nvcc-only restriction on constexpr host functions in device code;
  clang/hgcc do not have it
* `-DPPU_FORCE_INSTANTIATE=1` → `(void const*) cutlass::device_kernel<GemmKernel>` in the launcher.
  Taking the address of the `__global__` odr-uses it and pulls in the whole mainloop.
  **`&GemmKernel::operator()` does NOT work** — naming a `CUTLASS_DEVICE` member from host code
  instantiates nothing.

Verify it, do not assume it: plant `static_assert(sizeof(TileShape) == 0)` in the mainloop and count
the hits. 0 → the gate is blind; 32 → it is live. Then reintroduce a bug you already fixed and confirm
it is caught.

**clang accepts, nvcc/EDG rejects — four real source bugs found this way**, each of which alone was
enough to blind the gate: a trailing comma in a template-argument-list (ill-formed in every standard;
four occurrences); a missing `template` disambiguator on a dependent member template
(`.desc_.init<` → `.desc_.template init<`); `dim3({0,0,0})` ambiguous between `dim3(uint3)` and
`dim3(dim3&&)`; and `CUTE_DEVICE cast_smem_ptr_to_uint` called from `CUTE_HOST_DEVICE copy` (upstream
CUTLASS declares it `CUTE_HOST_DEVICE`).

**`partition_S` / `partition_B` are pure layout algebra** — `make_tiled_copy(atom, thr, val)` uses the
atom only for its `ThrID` and element type, no PTX. So the real AIU copy atom IS modelable locally
(`cute/arch/copy_ppu0010_aiu.hpp` + its traits + `cute/ppu_tensor_mix.hpp` for `is_mix_iterator`).
Do not declare something unanswerable offline before trying.

## The delivery bound (the one hard constraint)

One swzl/AIU delivery is a **fixed 16 bytes per thread**, so it carries `16*8/Bits` codes = **`16/Bits`
mma atom-slots** (an atom's B operand is 8 fp16/thread). The fp16 fragment must absorb it:

```
delivery = 16*8/Bits  <=  slots = WN*TK/32          i.e.   WN*TK*Bits >= 4096
```

`slots` does **not** contain `TN` — B is split across the N warps, so widening `TN` never helps; only
`WN` or `TK`. Consequences:

* narrower codes are **harder** to place: int1 gets 128 codes per delivery where int4 gets 32
* `B_regs = 4*MMA_N*MMA_K >= 4*16/Bits`, so int1 is forced to **>= 64 registers** on B
* the same constant is int1's advantage: one read feeds 4x the mma of int4 (measured, at one shared
  config: int1 49.9% > int2 48.1% > int4 45.9%, monotone in bits)
* `K_BLOCK_MAX = slots/delivery` copy steps per k-tile: 1 for int1, 2 for int2, 4 for int4 at
  `WN=64/TK=64`. int4's conversion is therefore already atom-granular.

**N-fold** exists only to reach the AIU's 32B contiguous minimum: `F = 32/(TK*Bits/8)`, so the
contiguous run is `F*TK*Bits/8 = 32 B` for **every** width — bank patterns are identical across widths
by construction, which kills any bank-conflict explanation of a width difference.

## Occupancy: registers are billed to a POWER OF TWO

`blk = min(smem_limit, warp_limit, register_limit)` — a formula omitting the register term ordered
nothing. acu reports `Block Limit Registers` directly and says which limit binds.

**Billing is rounded up to a power of two.** Reverse it from acu's own warp count:
`131072/16 warps = 8192 reg/warp = 256 reg/thread` for a kernel reporting **186**. So **129 registers
cost as much as 256**, and an 8- or 16-aligned model is refuted by that point.

```
regs/thread ~= WM*WN/32 (accum, fp32) + WM*TK/64 (A) + WN*TK/64 (B) + WN*TK/256 (scale, x2 with zero)
measured    ~= estimate + 12          # two anchors: 176->186, 128->142; DOES NOT extrapolate
warps/CU     = blk * warps_per_block
```

`accum = WM*WN/32` is the output and lives across the whole K loop — immovable. Two anchor points
**cannot call a bucket boundary**; only acu on the specific config does.

## Two performance factors, and they are ORDERED not additive

```
cvt/mma = 128/WM        converter amortisation; each B element feeds WM/16 mma instructions
warps/CU                occupancy, computed WITH the register limit and power-of-two billing
```

Over 25 measured points, `cvt/mma = 8` is a **throughput ceiling** (~39%) that occupancy cannot cross:
4x the blocks moved it 1.4 points. `cvt/mma = 4` is latency-bound and occupancy is worth ~6 points.

**The ordering matters and it fooled me once.** `cvt/mma = 2` measured "+0.3 points" and I recorded it
as worthless — true only because that config was register-starved (512-billed, `warps/CU 8`). Once
chunking freed the registers, `cvt/mma = 2` was worth **eleven points** over the best `cvt/mma = 4`
config. Mirror image: the `cvt/mma = 8` rows free exactly the same registers as rows that gained +10
and gain **nothing**. **The second axis only pays once the first is not saturating.**

**In the MoE band the first axis is worth MORE than on dense** — measured at matched `(TileM, TileN)`
with only warpM moving, so `cvt/mma` is separated from the m-tile count:

```
TM=64 TN=128 TK=64, L=64 experts, skewed rows     w32x64 (cvt/mma 4)  ->  w64x64 (cvt/mma 2)
Q3                                                 539.57 us           ->  429.19 us   +20.5%
Q5                                                 476.30 us           ->  355.50 us   +25.3%
Q6                                                 473.69 us           ->  361.53 us   +23.7%
```

against eleven points on dense. It fits: MoE collapses the useful A work, so conversion is a larger
share of what is left. **`WN` is not on this axis** (`cvt/mma = 128/WM`), and lowering it does not pay —
`w64x32` measured 13% WORSE than `w64x64` for Q6, which is why relaxing the delivery bound to reach
`WN=32` was closed rather than built.

**And in the MoE band the tile is NOT the lever at all.** Sweeping TileM 32/64/128/256 at fixed
warpM=64, the winner (TM=64) has neither the smallest m-tile count (256 at TM=32) nor the least masking
(8.1% at TM=32) — the two candidate explanations point at opposite ends and the winner is in the
middle. The weight-bound "minimise the total m-tile count" rule does **not** hold: more m-tiles
measured faster, while `A` is roughly TileM-independent (`mt * TM ~= total_rows`) and `B` falls as
`1/TM`, so the configurations that move the FEWEST bytes are the slowest. What is left is occupancy —
A-smem is `TM*TK*2`, so 4/8/16/32 KB per stage across that sweep.

## Layout traps (each cost >= one round)

**`sizeof(cutlass::uint2b_t) == sizeof(uint1b_t) == sizeof(int4b_t) == 1`.** They are byte-sized
wrappers holding 2, 1 or 4 bits, so `ptr + n` on one advances **n BYTES, not n elements**. Offsetting a
per-expert weight base by `e*K*N` therefore over-advances 4x / 8x / 2x, and expert 1 already reads past
the allocation. Same trap in the other direction: `DeviceAllocation<uint2b_t>(K*N)` allocates `K*N`
BYTES, so `copy_from_host` reads `K*N` bytes out of a host buffer holding only `K*N/4` — an
out-of-bounds host read that several shipped single-expert tests still perform. Offset and size in
bytes: `K*N*Bits/8`.

**`tCrB_mma` is NOT compact.** Measured: `((2,2,2), MMA_N, MMA_K) : ((1,2,4), 32, 8)` — `MMA_N` stride
**32**, `MMA_K` stride **8**. So `e = val + 32*n + 8*k` and `e/32` is `n_atom`, **not** `k_atom`.
Assuming compact `(8, 32)` produced "MMA_N atom 0 correct, atoms 1-3 wrong".

**`thr.partition_B(sB)` puts the thread base in the ITERATOR, not the layout** — `part.layout()(0)` is
0 for *every* thread. For a thread-inclusive map use `thrfrg_B(sB).layout()` and compose:

```cpp
btile = make_tile(_, make_tile(make_layout(make_shape(size<1>(vmnk), size<2>(vmnk)),
                                          make_stride(_0{}, _1{})), _));
TV = Mma{}.thrfrg_B(sB).layout().compose(btile, _).compose(right_inverse(vmnk), _);
```

* `.layout()` **before** `.compose()` — composing the *tensor* yields a tensor over the smem nullptr and
  evaluating it dereferences (a silent segfault, silent because stdout was buffered)
* `thrfrg_B`'s first mode is `bthrid`, and its warp order is **opposite** to the linear thread index
  (`thr_layout_vmnk` has warpM at stride 32, warpN at 64; `thrfrg_B` is `(lane,(warpN,warpM))`).
  `right_inverse(thr_layout_vmnk)` fixes it but **must be composed as a LAYOUT** — evaluating it to an
  integer discards the tuple structure and cute re-decomposes it colex, restoring the wrong order
* `get_layoutB_TV()` cannot be used directly: its reference has **no stride** (so column-major,
  codomain `n + N*k`) and is sized by the **MMA tile** (`WON*16`), not the block `TN`

**`make_fragment_like` preserves stride-0s in MODE 0 ONLY** (its own comment says so). That is why a
scale fragment keeps its k-val zeros but materialises `MMA_K`. And `compact_order` follows the
*reference* strides, so zeroing a mode after the fact leaves a non-compact neighbour — `filter_zeros`
first, then restore the zero.

**`raw_pointer_cast(t.data())` before `reinterpret_cast`** — a subbyte tensor's `.data()` is a
`cute::subbyte_iterator` and casting the class type to `uint32_t*` is ill-formed. `convert_tensor`
already had the idiom.

**Prefer cute's algebra over index arithmetic that happens to work.** `right_inverse(Layout)` exists
(don't hand-roll the inverse permutation). A per-bit-weight closed form **is** a Layout: the converter
emission map is `shape ((2,..,2),(2,2))` over (code bits, vreg bits) with strides
`(2, 8, 16, .., 1)` and `(2*CodesPerVreg, 4)`. Expressed that way it *composes* with the rest of the
chain instead of being a function every consumer calls specially — and it follows the fragment layout
instead of restating it.

## Chunked conversion (`PPU_B_CHUNK`) — the mechanism worth knowing

The delivery bound forces the fp16 fragment to hold a whole delivery. Chunking **decouples how many
atom-slots the delivery covers from how many are fp16 at once**: convert one k-atom into a
`(val, MMA_N)` buffer and reuse it. Every delivered code still converts and is used; mma count and
total converter work are unchanged — only the emission **order** changes. Verified zero duplicated
work: the per-chunk emission is an exact partition (a pair's two halves never straddle a chunk edge,
because the low-lane index is always even).

Measured: `B` 64 -> 16 registers, acu 186 -> 142; int1 **50.2% -> 63.7%**, biggest at larger `TK`
because the saving is `4*MMA_N*(MMA_K-1)`.

The chunk gate is a **compile-time** predicate over the fragment's own layout:

```
keep : ((e/8) % MMA_K) == Chunk            e/8 == MMA_K*n_atom + k_atom
at   : ((e%8) + 8*(e/(8*MMA_K))) / 2       val + 8*n_atom
```

and both are better written as `composition(L_dst, right_inverse(FragLayout))`.

Pipeline hazard: at `K_BLOCK_MAX == 1` the `++smem_pipe_read` block fires **every** iteration and sits
**before** the mma loop, so a per-atom transform placed in that loop reads an already-advanced stage.
Capture the stage before the advance.

## Where int1 actually ships

**Never standalone.** int1 is the sparse plane of the GGUF bit-plane decomposition — Q3 = int2+int1,
Q5 = int4+int1 (Q6 = int4+int2, no int1). `TK` is set by the **sparsest** plane, so a combination
containing int1 obeys int1's delivery bound: Q3/Q5 at `WN=32` need `TK >= 128`. A standalone-int1
ScaleZero number measures nothing that ships; the affine applies to the combined dequantisation in
the 2-plane converter.

## Per-plane N-fold (2-plane / B-concat), and why it is a load-layer change only

The fold factor is per plane: `F_p = contig_p >= 32 ? 1 : 32/contig_p`, `contig_p = Block_K*bits_p/8`.
One shared factor is what pins a 2-plane path to `Block_K >= 256` — the only K where int2 and int1 both
reach the AIU's 32 B minimum unfolded. TK=256 costs A-smem 32 KB/stage (blk=2, 12.5% occupancy) and 128
fp16 registers each for A and B; it measures 16.7% MFU against int4's 53.2%.

Q6 (int4+int2) needs **no** fold at `Block_K=128` (both F=1). Q3 and Q5 carry an int1 plane and need
per-plane fold below 256.

The fold lives only in the load layer — the collective's own words: the swzl READ partitions the
PHYSICAL `(Ng, FoldF*TKe)` shape while the MMA fragment partitions a LOGICAL `(TileShape.N,
TileShape.K)` view of the same bytes. A 2-plane collective already has separate load machinery for
plane 2, so per-plane fold is a stride/shape change to an already-independent path. What it touches:
plane 2's `SmemLayoutB2` (physical), its own `dB2`, **its own `FoldTilerB2` for `local_tile`** (cutting
a folded tensor with `TileShape` fires copy.hpp's `size<1>(src) == size<1>(dst)`), and **its own
k-iteration coordinate** — `local_tile` divides the interleaved counting tensor's NESTED K mode, so at
`Block_K=128` plane 1's k mode is `(_2,1)` (a tuple) while plane 2's folded tiler consumes `kCon`
exactly and leaves a scalar. Feeding plane 1's coordinate to plane 2 is a coordinate-SHAPE mismatch,
not the rank mismatch it first looks like.

**The one that is not obvious: `hi_vreg0` must carry the N index.** With the shipped
`hi_vreg0 = k_block % P2_DIV`, a folded plane 2 has `P2_DIV == 1`, so every `ii` reads vregs `{0,2}`
and `{1,3}` are never touched — half the tile's high bits cannot arrive, whatever the placement.
Correct: `&cvt_hi(_, ii % MMA_N2) + (k_block % P2_DIV) + P2_DIV * (ii / MMA_N2)`, which degenerates to
the shipped expression when `P2_DIV == 1 && MMA_N2 == MMA_N1`. The OFFLINE needs no change — the
existing fold already produces exactly what that indexing demands (verified byte-for-byte).

Result: Q3 at `Block_K=128` (int2 F=1, int1 F=2) `bad=0/32768` against the native Q3_K golden, with the
`Block_K=256` control unchanged at `bad=0`.

**`MmaPermK = FoldF > 0 ? TileShape.K : 32*8/bits`** (`ppu_mma_builder.inl`). The fold path permutes K
by the tile; everything else by the 32 B run span. That single constant is why a fold-path layout
derivation does not transfer to a non-fold path — and at `Block_K=128` for int2 the two rules coincide
(`32*8/2 == 128`), which is why that step needed no builder change.

**The offline generator's frame has a precondition:** `8*CPW == TK`, i.e. exactly one 32 B delivery per
physical row per k-tile (int1→256, int2→128, int4→64, and any folded plane by construction). It is NOT
satisfied by int2 at `TK=256` (two deliveries per row) — generalise with `DL = (F*TK*bits/8)/32` and
index the map `[((row*DL + dl)*8 + wd)*CPW + j]`. The chunk ordering (N-instance outer vs delivery
outer) is a single bit: resolve it against the gate, do not guess.

## Two-plane formats (Q3 / Q5 / Q6): ONE closed form, and where the cost actually is

`MixGemm2Plane<LowBits, HiBits, Chunk, NChunk, Rebase, FragLayout>` covers Q3 = int2+int1,
Q6 = int4+int2, Q5 = int4+int1. There is no per-format index algebra, and there must not be — writing
the second and third pairing by hand is what the METHOD section above is about.

```
kPairs     = 16/LowBits                                      half2 pairs per low vreg
kVregRatio = LowBits/HiBits                                  high/low vreg ratio INSIDE one delivery
hshift(T,V)= HiBits * (T + kPairs * (V % kVregRatio))         where the high plane's bits sit
hi vreg    = kVregRatio * (V / kVregRatio)
at_plain   = MixGemmEmit<LowBits>::index(T,V) / 2             the LOW plane's own emission
```

Derivation: a delivery is 16 B/thread either way, so the low plane brings `128/LowBits` codes in 4 vregs
while the high plane's 16 B covers `128/HiBits` of them. Inside one high vreg the two half2 lanes sit 16
bits apart, so a pair is `(a, a + 16/HiBits)`, and
`idx(v_local, c) = (c % kPairs) + kPairs*v_local + (16/HiBits)*(c / kPairs)` is a bijection because
`kPairs * kVregRatio == 16/HiBits`. **At (2,1) it reproduces Q3's shipped `8*(V&1)+T` and `2*(V>>1)`
exactly** — which is the only reason to trust it, and `at_plain` turns out to be what Q3's hand-written
`AtLayout` always was.

**int4 was never "a different scheme" — only a bias.** `MixGemmChunkEmit`'s mask and mul already matched
the general rule; only `add` needed `-(2^(10-bpos) + Bias)`, i.e.
`0x8000 | ((25-bpos)<<10) | (Bias ? 1<<(bpos+3) : 0)`, which emits exactly the 0xE408 (-1032) and
0xD480 (-72) the shipped int4 converter hardcodes.

**int4's -8 is a uniform offset the ZERO POINT absorbs.** With `low = q & 15` and `high = q >> 4` the
converter emits `q - 8` for EVERY q, no wrapping, so `zero = +8*dl` (PLUS — `apply_scale_atom` is
`multiplies` then `plus`). Q3 needs none of this because int2 carries no bias. And the offline must write
`q & 15` through `place_derived` DIRECTLY: the `preprocess_weights_for_mixed_gemm` shim adds int4's +8 to
reproduce the legacy pipeline.

**Q6 and Q5 are structurally SIMPLER than Q3.** int4's contiguous run is already >= 32 B at every
Block_K >= 64, so their LOW plane never folds (F1 = 1, interleave-256 walk) and only the high plane does.
Delivery bounds for picking configs: low int4 `WN >= 1024/TK`, Q6's int2 high `WN >= 2048/TK` (32 at
TK=64, so the whole w*x32 family is legal), Q5's int1 high `WN >= 4096/TK` (64 at TK=64).

**The two-plane converter costs 4 machine ops per half2 against a single plane's 2, and it does not come
down.** `lop3 + shift + lop3 + fma` vs `lop3 + fma`. The first lop3's three operands are already src,
mask and the 0x6400 base, and the high plane's bits live in a different register, so they must be shifted
and OR'd. Removing the shift would mean storing the high plane pre-shifted to its destination bit
position, which wastes field width in a 1-2 bit plane and buys the ALU back as traffic.

**Measured, tuned, gs=16, chunked, M=2048 N=K=4096.** All three land within 1.15-1.24x of a single 4-bit
GEMM while carrying 3, 5 and 6 bits, and **all three peak at the SAME geometry `(64,128,64) w64x64 s2`**:

| | us | MFU | vs int4 |
|---|---|---|---|
| int4 (1 plane) | 228 | 60% | 1.00x |
| Q3 = int2+int1 | 261 | 52% | 1.15x |
| Q5 = int4+int1 | 268 | 51% | 1.18x |
| Q6 = int4+int2 | 282 | 49% | 1.24x |

Ordered by total bit width, and NOT bandwidth-bound: Q6 at `(64,128,64)` moves ~940 MB against the int4
winner's ~1342 MB, because that one's TN=64 re-reads A twice as often. A-concat is retired for good —
`B-concat / A-concat = 0.55x`.

## `w64x32` is a real warp shape and sweeps forget it

Worth +7 to +9 points on int2 AND int4, and it was missing from every sweep. `MMA_N = warpN/16`, which
depends ONLY on warpN — TN and TM are free. Chunking needs `8*MMA_N*MMA_K == kOut`, i.e. `MMA_N == 2` at
TK=64, i.e. `warpN == 32`; and `cvt/mma = 128/WM` wants `WM = 64`. Only `w64x32` satisfies both. Sweeps
that carry w32x32 (chunked but cvt/mma = 4) and w64x64 (cvt/mma = 2 but MMA_N = 4, so the predicate turns
chunking OFF) miss it entirely — and the w64x64 row then looks like evidence that big warps are bad.

**Corollary about references: a reference you have not tuned on the same grid is not a ceiling.** int2 at
w64x32 briefly appeared to beat int4, which "retired int4 as the ceiling". int4 simply had no w64x32 row;
with one it goes 243 -> 211 us and is fastest again.

## Scale granularity: APG = gs/16, independent of the tile

`APG = MMA_KA_/Scale_TileK = (Block_K/16)/(Block_K/gs)`, so **Block_K cancels**. `gs=16` therefore forces
`APG = 1` — a scale reload from smem at EVERY mma atom — and no tile choice avoids it. Q3_K's native
granularity IS 16, so that is the shipping operating point.

**And it costs almost nothing: 2.6% on Q3** (262 vs 255 us against gs=32). int4 pays the most, 10.8%,
which fits — most mma-dense, least conversion, so the reload is relatively most visible. Consequence:
prefetching the next group's scale, and folding the dequant constants into one `hfma2`, are each worth at
most that on the shipping path. Measure the gs difference before queueing either.

**That is the scale's LATENCY. Its TRAFFIC is a different and much larger budget, and I conflated the
two once.** The weights are kept sub-byte at great cost — fold, chunk, two-plane — and then the scales
are stored as dense fp16 without question. Relative to the weight channel, and independent of shape
since both scale with `N*K`:

```
S/B = 32 / (gs * bits)     Q2_K gs16 b2 -> 1.00   scale+zero EQUALS the weight channel
                           Q3_K gs16 b3 -> 0.67
                           Q6_K gs16 b6 -> 0.33
                           Q4_K gs32 b4 -> 0.25
                           Q5_K gs32 b5 -> 0.20
```

**Small batch is where it dominates**: at decode the useful A work collapses (a few rows per active
expert) while every active expert's full weight slab is still streamed, so the kernel is purely
weight+scale bandwidth and a 67% overhead is a large share of TOTAL time. **And a third of it is
provably redundant** — `ggml-common.h` states Q3_K and Q6_K as `x = a * q` with no `dmin`, so their zero
is `-4*dl` / `-32*dl`, a fixed multiple of the scale carrying no information. Fold the centre into the
converter's `add`, which already carries int4's `-8`: `add = 0x8000 | ((25-bpos)<<10) | (B << bpos)`
needs only `B*2^bpos < 1024`, and `B=4` is exact at every int2 `bpos`. Q2_K/Q4_K/Q5_K have a real `dmin`
and must keep theirs.

**THE fp16 SCALE PATH IS NOT A FALLBACK — IT IS THE NATIVE FORM FOR GPTQ AND AWQ, so it must never be
deleted in the name of shrinking the scale channel.** The distinction is sharper than "keep a backup":
for GGUF K-quants the fp16 scale is something WE synthesised from an already-quantised 6- or 8-bit
field, so compressing it back is LOSSLESS — it recovers the checkpoint's own representation. For GPTQ
and AWQ the fp16 scale IS the checkpoint, so quantising it would be a NEW lossy step nobody asked for.
**Never trade accuracy the source format already paid for.**

```
format      scale native  zero native     fp16 scale?  zero removable?
GGUF Q2_K   4-bit x d     4-bit x dmin    no (ours)    no, real dmin
GGUF Q3_K   6-bit x d     none, x = a*q   no (ours)    YES, it is -4*dl
GGUF Q4_K   6-bit x d     6-bit x dmin    no (ours)    no, real dmin
GGUF Q5_K   6-bit x d     6-bit x dmin    no (ours)    no, real dmin
GGUF Q6_K   8-bit x d     none, x = a*q   no (ours)    YES, it is -32*dl
GPTQ sym    fp16          0               YES          yes, already 0 -> ScaleOnly
GPTQ asym   fp16          4-bit packed    YES          no
AWQ         fp16          4-bit packed    YES          no
```

A compressed scale is therefore an ADDITIONAL specialisation selected per source format, with
`ElementScale` staying a template parameter defaulting to `half_t`; the GPTQ regression is what proves
nothing was traded away.

**Widening GGUF's packed 6-bit scales to 8-bit buys nothing at runtime** (+3.6% Q3_K, +2.8% Q4_K, +2.3%
Q5_K, 0% for Q2_K and Q6_K whose scales are already 4+4 and int8). The offline already unpacks to dense
fp16, so the widened bytes are discarded before the kernel sees them. Defensible as offline
simplification — no cross-byte 6-bit shuffle, cf. `get_scale_min_k4` — not as a bandwidth change.

## A hand-written config list confounds axes, and one of them was stages

The MoE sweep was 30 hand-written rows for a long time. TileK appeared only as 64; TileN as one value per
family; WarpN as each format's minimum; and **stages was not an axis at all** — it was baked into each
row. That silently decided a published verdict: int4's row ran s3 while int2's IDENTICAL shape ran s2, so
`i4 382.76 vs i2 420.83` was a stages comparison. With stages as a real axis over `{2,3,4}`:

* **the single-plane winner flips: i2 `64x128:64 w64x32 s3` = 300.26 us (55.5% MFU) against i4's best
  362.14** — int2 beats int4 by 17% in the MoE band, the reverse of dense
* **the optimal stage count is format AND shape dependent** — q3/q5 want s2, i2/q6 want s3, **i4 wants
  s4**, which was in no row of the old table. `q3 64x128:64 w64x64` spans 349.38 / 407.38 / 536.83 across
  s2/s3/s4: a **1.54x** spread on one shape.

**RETRACTED because of this: "Q3 is 20.7% slower than Q5 in MoE and 27% on dense, and it is the only
format whose LOW plane also folds (F1=2) — a correlation across two regimes worth an acu investigation."**
It was the GRID. On the full product q3's best is 349.38 against q5's 340.75: a **2.5%** gap. A
"correlation across two regimes" built on two hand-picked grids is one grid's artifact seen twice.

Also: `mt` (m-tile count) and `msk` (masked fraction) are both NON-predictive at 336 rows exactly as at
30 — the winner has neither the smallest `mt` (TileM=256 does) nor the least masking (TileM=32 does) — and
the compulsory traffic floor is 5-29% of HBM on **every** row, so nothing in the band is bandwidth-bound.
The lever is occupancy.

**Compare only WITHIN a run.** The identical config `q3 64x128:64 w64x64 s2` measured 429.19 us in the
30-row run and 349.38 in the 336-row one, same data and shape. Testable hypothesis: the old sweep packed
64 experts per row (~1.2-1.5 s of host time) where the new one packs once and memcpys (~30 ms), so the old
run idled the GPU before every timing loop. Until that is checked, no cross-run number is usable.

## Compile parallelism is capped by the SOURCE COUNT, not by `-j`

`cutlass_build_dev_kernels` emits one `add_custom_command` per `.cu`, so a sweep in a single file compiles
strictly serially however large `-j` is — 8 sources use 8 of 192 cores. Pick the granularity by
measurement (nvcc front end, local):

| unit | wall |
|---|---|
| 0 kernels (header only) | **5 s** — the fixed cost |
| 3 kernels (one shape, two-plane) | **25 s** |
| 21 kernels | 57 s |
| 42 kernels | 109 s |

Marginal cost is NOT linear: a 3-kernel unit spends ~20 s on its first kernel because the whole collective
instantiates once. So the useful floor is **one shape per unit** — 128 generated units finish in less wall
clock than the ORIGINAL 30-row single file while instantiating 11x as many configurations.

**Split on axes that are part of the SHAPE, not on stages.** Stages is a runtime cost, not a compile one:
the offline pack is per shape, so all three stage counts share one pack (31 ms per two-plane shape, 24 ms
single-plane, ~3 s over the sweep — already the same order as the GPU time). Splitting stages triples it
for nothing. And pack ONE expert then `memcpy` the rest: the pattern does not depend on `e`, and packing
64 identical experts is 268 M positions per row to produce one row's worth of information.

Two things the split then needs: **every unit must report its own `-D` state** (one unit missing
`PPU_B_CHUNK` runs the unchunked collective under a banner compiled in a different TU saying chunked — so
each votes at static-init and main prints the tally), and the **unit count must be compiled in from the
generator** so a silently shrunk enumeration shows up in the log.

## Debug checklist: eight ways a change looked fine and was not

Every entry below cost at least one box round trip in one session. Read this list *before* concluding
anything from a run.

**1. Two places must agree and I changed one.** Four times in one session, on the same feature:
`PPU_A_CUBE_H` changed the swzl **read**'s cube while the **write** kept `Block_MN` (→ NaN); the row-0 run
offsets were hardcoded for `CUBE_H=16` and a `64x64x128` config walked off (→ compiler caught it); the pack
pitch existed as **two literals**, builder 16 and collective 64 (→ `invalid VA`); `gA` was made a plain
tensor under one macro but not the other, so `&gA(...)` on a mix tensor produced a nonsense address
(→ fault at `s.wait commit_group(1)`).
**The fix is never a `static_assert` comparing them — it is one definition used by both** (a shared macro, a
constant computed from the other). Before touching a coupled quantity, *list every derived site*: for the AIU
this is `bits_per_aiu`, `GmemTiledCopy`'s value layout → `Tiler_MN` → `desc_.cube_h`, the swzl atom's
`CUBE_H`/`CubePitch`, `SmemLayoutA`, and the writer's own arithmetic.

**2. A comparison-based checker reports MATCH on NaN.** `NaN > threshold` is false, `std::max(x, NaN)`
returns `x`, and `NaN != 0` is *true*. So an all-NaN buffer scores `bad = 0`, `max_rel = 0`, and passes a
liveness test. **Count non-finite values; never compare them.** Print both absmaxes and the first few raw
values unconditionally — a verdict built from comparisons cannot distinguish *equal* from *both zero* from
*both NaN*.

**3. A refused launch, and a dead oracle, read as a pass.** `refuse vs refuse` compares two untouched
buffers and always matches. Snapshot the refusal counter and make growth a **failure**; key vacuity on the
golden's magnitude, not on whether a "worst index" was assigned (`worst = -1` is what a **bit-exact pass**
looks like, not a broken one — I asserted the opposite and built a check on it).

**4. `-D` on the compile line does not mean the code responds to it.** A stale checkout and a misspelled
macro both pass `build.sh`'s verification, which only greps the command. Twice: once the source predated the
macro (`grep -c` returned 0), once a *rebuilt binary was never rebuilt*. **Make the kernel self-report** —
if a macro claims to change `SharedStorageSize` and the value equals the unmodified arithmetic, that is a
failure, not a plausible timing.

**5. Never evaluate a binary you have not confirmed carries the change.** The mangled name in a fault dump
lists every template argument; read the ones you edited out of it before interpreting anything else. Two
runs in one session were judged before noticing the artifact was old.

**6. Instruction count is not time when no pipe is above ~20%.** With IALU 14%, FALU 14%, SALU 17%, TENSOR
12% and LSU 6%, removing 1.8 scalar instructions per mma bought exactly nothing. The instruction mix says
*what work exists*; **Pipe Utilization and Warp State say what costs time**. Here the top stall was
`Memory Dependency 0.919` with only 14.2 warps/CU available to hide it.

**7. Shrinking a shared-memory member is not a weaker form of removing it.** Everything after it moves.
`cute::array_aligned` guarantees 16 B while PPU0010's AIU load needs 32 — the alignment that worked held by
*arithmetic coincidence* (A's byte count happened to be a multiple of 32), not by declaration. A one-element
placeholder produced `AIU_ld TSM size out of range`; removing the member entirely was correct.

**8. The local nvcc gate is more permissive than hgcc.** A `static_assert` calling a member of the same,
still-incomplete class compiles under EDG and is rejected by clang, surfacing as
`no type named 'SharedStorage' in CollectiveMma<...>` — an error naming something unrelated. The gate proves
a TU *parses under nvcc*; permissiveness differences are exactly what it cannot see. Prefer body-level
asserts, and treat a box-only failure as a language question before a logic one.

### And the standing rule this session kept re-proving

Read the quantity off the object; do not re-derive it. `max_common_vector` is the layout's *permitted*
vector, not what the copy *emitted* (predicted 4 loads/mma, measured 16). `cosize_v<SmemLayoutA>` is the
layout's extent, not the allocation. `CUBE_H` is a runtime operand of the instruction, not a footprint knob —
and which row a lane reads is decided by the lane/vreg structure (`row = lane/4 + 8*(v/2)`), which no address
computation can reach. When a hardware simulator exists in the tree (`ppu_tsm_ld_swzl_sim`), replay it on the
host: it answered in minutes what three box round trips had not.

## A local model that only proves itself right cannot close a device bug

Learned by burning three box round trips on one defect, then closing it locally in 48 minutes once the
question changed.

**The symptom.** The grouped expert-identity probe (controlled input: `q=8` so the converter's `q-8`
term vanishes, the zero plane carries `e/256`, `A=1`, so the output IS the expert id the kernel read)
reported `read = e-64` for `e >= 128` on device. Two exhaustive host models of the address chain --
scheduler -> int64 GEP -> `gZ` -> `partition_S/D` -> scatter/recover, all 256 experts, independently
anchored, with planted negative controls that reproduced the symptom -- both came back **clean**.

**Why that loop does not converge.** Those models answer *"is this chain computed correctly?"*. The
question that settles a device disagreement is *"can the model reproduce the wrong value the device
produced?"* A model that cannot reproduce the error says nothing about the device, so each round ends
at the box, and the next model is another proof of self-consistency.

**The rule.**

> Point the local model at the OBSERVED WRONG VALUE, not at correctness. The root cause is whatever
> you had to assume in order to reproduce it.

Same technique as the `1512` diagnosis (simulate the wrong StrideB, get `222 + 2*645 = 1512` exactly,
then fix). Here the target list was `e=1 -> 2`, `e=3 -> 6`, `e=129 -> 85`, `e=190 -> 126`, and nothing
was allowed to be committed as a fix until the host printed those four.

**What it turned out to be** (and it was a shipping correctness bug, not a test artifact): the
non-interleaved B expert pitch was passed as a count of *logical codes* and advanced as *bytes* on a
raw `int4b_t*`. int4 is two codes per byte, so **expert `e` reads expert `2e`**; from `e = 128` the
read leaves the B allocation entirely, lands in the fp16 scale buffer (bytes `00 28` decoded as int4
contribute exactly `-44`, hence `129 -> 85`) and then in the zero fill (`-64`, hence `190 -> 126`).
Four seams carried it: ordinary, fold, 2-plane low and high. The interleaved path is byte-pitched by
design and was correct.

**Two corollaries worth keeping:**

*A clean multiplicative factor is not evidence against an addressing bug.* "An address error yields
garbage, not an exact 2x" is only true when the data is not encoded linearly in the index -- and a
controlled-input probe **deliberately** encodes it that way. On such a probe an exact ratio is the
signature of landing on a neighbouring index, not a refutation.

*Unit confusion in sub-byte types is a family, not an incident.* Same shape twice in one repo:
this pitch, and `DeviceAllocation` sizing by `sizeof(T)` while `copy_from_host` counts
`sizeof_bits<T>`. Audit rule: for every `int4b_t` / `uint2b_t` / 1-bit pointer arithmetic or size
expression, write down **what unit that quantity is in**, and flag any quantity used as two different
units in two places.

## A scheduler's numerics reduce to a combinatorial property you can check on the host

Under an **order-independent fixture** (every partial sum exactly representable, so any accumulation
order yields the identical value -- see the exact-fixture construction), the result of a GEMM is the
sum of the contributions of the assigned `(tile, k)` units and does **not** depend on which CTA does
which. Therefore:

> coverage-exactly-once  =>  numerically correct

and coverage is pure integer combinatorics: host-checkable exhaustively, no device.

For a Stream-K / Marlin style scheduler this leaves only two things that genuinely need silicon:

1. **does the emitted code actually follow the decomposition it computed** -- this is where the expert
   pitch bug lived, so it is not dismissible; and
2. **races / memory ordering in the peer-lock protocol**, covered by repeated launches plus a
   position+value fingerprint that must be stable.

Even (1) has local attacks that work: compile the real instantiation and read the address arithmetic
in the IR/asm, where the offending constant appears literally; or use a compile-time probe -- make a
`constexpr`/template compute the offset and `static_assert` it against a literal, and the compiler
prints the **actual** value in the error message when it fails.
