# PPU1.7 simulation performance

### Changing tail granularity changes a collective's lifetime contract

For FP16 B1/S1024/H56/D128 noncausal on40SM,448 Q128 tasks give a final
8-CTA wave. Splitting just the last8tasks into16Q64 halves is address-safe
and ideally12->11.5task-times, but it is not merely a scheduler-index edit:
the existing full/half collectives use two/one math WGs. `load_tail` drains
TMA/O but leaves256 QueryEmpty arrivals for the next Q. A final32producer
arrivals must close that named-barrier phase before switching its expected
count288->160. Also prove async retirement, explicit initialization cohort,
nonoverlapping old/new mbarrier storage and register handover.

The corrected mixed wrapper compiled on CUDA12.8 but grew spill12->32B in
each direction and stack8->16B; it was rejected before simulation and removed
from live source. UniformQ64 has255regs/thread versus168 but fewer threads
(256vs384), zero CUDA spills, and doubles KV task fills. Its break-even is
t64/t128<12/23, not an assured tail win. Actual CuTe coverage7340032cells and
compile negatives do not establish device numerics/performance. Keep this
axis separate from exp changes. Evidence: FA branch `ppu17-tail-qsplit`,
`dev/ppu17/experiments/tail-qsplit/`; native PPU1.7 unmeasured.

Optimize the already-correct mapped implementation. The original causal task
uses a **20-SM, 32-MiB LLC model**; the later S1024 FP16 simulation reports
**40 SM**. Bind each run separately, not to PPU1.0 or a full H100.
Peak math rates, clock, warp limits, register file, shared-memory capacity,
latencies, cache organization and cluster support must come from that model.
Leave unknown fields unknown; do not infer them from `SM90` compatibility.

### A near-tie after disabling pingpong is not a critical-path attribution

For FP16 B1/S1024/H56/D128 noncausal, Q128/KV128,40SM, W01 disables only
optional math-WG alternating issue. BOTH WGs then explicitly wait for K/V;
the old leader-only predicate is unsafe without the pingpong edge. The real
collective mutation fails its WG1 assertion. CUDA removes3optional named
barrier sites, preserves7data sites and4GMMA waits, with168regs/8stack/12B
spill each way unchanged and default encoded bodies2/2 identical.
The user reports240325cycles versus C07's240412:87cycles/-0.0361879%.
Raw report/model/binary identities and W01 numerics are not supplied. Retain
that tiny decrease, not a substantial win or claimed measurement noise; a
deterministic simulator may resolve it. A registered fewer-cycles condition
is numerically met: do not invent a minimum-speedup threshold afterward.
Similar total time does not prove those barriers cost nothing: waiting can
move to TMA/GMMA completion, and native PPU removal still needs confirmation.
Inspect the current report, not the older C03 spill report; no default
promotion from this scalar alone. Evidence: FA branch`ppu17-wg-scheduling`,
`dev/ppu17/experiments/wg-scheduling/README.md`.

### Source softmax overlap can disappear at native lowering

For FA FP16 B1/S1024/H56/D128 noncausal, the uploaded40-SM perfstatistics has
zero of90steady EX2 between wait1/wait0, although same-source PTX has90.
The CUDA12.8 native control has19 there. Old P physical registers are reused
by later softmax: never just delay/delete the completion wait. Empty CuTe
operand fences were inert. Two private volatile row-sum stores/readbacks
restored90/90 on CUDA but grew spill12->36B. An opt-in XOR-of-both-row-sum-bits
volatile store restored90/90 with unchanged168regs/8Bstack/12Bspill; it costs
1KiB shared plus one XOR/store per lane/steady step. This is an intentional
compiler-order anchor, not a free fence or a measured PPU win. Default encoded
bodies remain unchanged. The later PPU report **rejected C03**: overlap really
became90/90, steady PV wait0 sync stalls became0, yet complete kernel cycles
rose247267→266011(+7.58%). PPU lowering introduced23lane-private slots,
35,323,904B reads +18,964,480B writes, closed exactly from per-PC accesses to
memory counters. Even barrier IDs and epilogue addresses spilled. Same QK/PV,
EX2/FMA work and TMA bytes; the intended token added only2,293,760shared bytes.
Do not transfer NVIDIA's unchanged spill metadata to the PPU allocator.
Private traffic is not HBM traffic; aggregated stalls are not an additive
wall-time breakdown. Reduced wait stalls cannot admit a slower full kernel.
Retain the original default; shorten temporary lifetimes before retrying
overlap. Candidate application numerics/model hashes were not uploaded.
Evidence: FA branch `ppu17-softmax-overlap`,
`dev/ppu17/experiments/softmax-overlap/docs/simulation-verdict.md`.
One target call/CPU-only oracle. Archive each uploaded raw report by hash before
a replacement upload overwrites its name; extracted summaries cannot replay
the full original per-PC validation.

The bounded C04–C06 follow-up rejected source-order fixes before simulation.
Making a token depend only on row0 still gave75/15 native EX2; separate row
functions gave PTX45/45 but CUDA76/14. A real shared dependency on row1's old
maximum finally gave45/45 in both, but increased spills12->40B. Thus neither
source scheduling nor a successful native schedule alone meets the gate.
An actual CuTe layout sweep and independent lane/warp anchor proved row/token
ownership; they did not prove allocation efficiency. All live experimental
edits were removed, retaining a replay patch and the original default. Evidence:
`dev/ppu17/experiments/softmax-overlap/docs/partial-verdict.md`. These are
CUDA12.8 compile rejections, not PPU timing results. A following KV176->128
candidate is a separate axis using the original pipeline: fewer padded matrix
operations but more KV/softmax iterations6->8. Do not label that trade a win
before its same-model full-cycle result.

For that report, executed MMA work/compute cycles reconstruct the report's
294912FLOP/cycle denominator. The user's55.556% ceiling (~40/72) corrects
tensor utilization42.517%->76.53%; removing1056/1024KV padding gives74.21%
useful MFU. Do not apply this correction to other counters automatically:
some resource percentages exceed100%, and sampling_info is empty. Per-PC
stall sums are not an execution timeline or additive kernel-time savings.

## Fix the workload and denominator

For equal-length attention, counting QK and PV with two FLOPs per MAC:

```
noncausal useful FLOPs = 4 B Hq D S²
causal useful FLOPs    = 4 B Hq D S(S+1)/2
MFU                   = useful FLOPs / (simulated seconds × model peak FLOP/s)
```

For B1/S2048/Hq32/Hkv2/D256 this is 68,753,031,168 causal FLOPs.
BF16 K+V is 4 MiB; GQA reduces KV storage, not the Hq arithmetic. Model traffic
can exceed distinct bytes because of reloads. Fitting KV in LLC is not proof
that the workload has no delivery cost or is served entirely from LLC.

Keep useful causal FLOPs separate from executed padded/masked tile work. A
profiler/model's hardware compute-utilization counter need not equal MFU.
Never halve a causal denominator twice. A reported 39% alone does not locate
a bottleneck or prove it unreasonable.

## Explain before sweeping

Use source + generated target code + simulator trace to distinguish:

- **Work imbalance:** causal tile K-loop lengths, tail-wave size, number of
  query tiles per head, GQA mapping, dynamic/LPT versus static scheduling.
- **Resource/parallelism:** actual CTA threads/warpgroups, grid vs 20 SM,
  registers/spills/shared bytes, producer-consumer resource split and admitted
  resident CTAs. More grid is not automatically more resident work.
- **Operand delivery:** TMA issue/completion, descriptor setup, shared banks,
  reuse and GMMA operand retirement. More stages trade overlap for occupancy.
- **Non-matmul dependency:** softmax/reduction/SFU, barrier arrival imbalance,
  producer/consumer overlap, prologue/epilogue amortization and instruction
  footprint. Static instruction count is not dynamic executed work.

Ratios such as stalls per issued instruction are not disjoint fractions of
wall time. Do not sum them into a timing decomposition without the metric
definition. A lower bank-conflict count or higher occupancy is an explanation
candidate, not the performance acceptance criterion.

## Bounded 20-SM tuning order

1. Preserve a source/model-bound baseline. Complete same-math correctness
   before comparing speed. One invocation per candidate per simulation process.
2. Inspect the existing causal scheduler before inventing one. The integrated
   Hopper LPT scheduler already has a 32-MiB KV section budget and runtime SM
   count. That coincidence with this model's LLC is not a measured optimality
   claim; all heads/other live tensors still share cache capacity.
3. Test one measured bottleneck at a time: query/KV tile geometry, warpgroup
   work assignment, stage count, legal registers/shared reuse, or scheduling
   order. Keep every rejected candidate and change only a bounded inventory.
4. For a larger change, first prove coverage, GQA/mask ownership, exact barrier
   counts and async lifetimes locally. Never delete required waits to win a
   simulation. Treat new cluster/packed-GQA/split features as new scope.
5. Select by complete admitted kernel modeled cycles, including setup and
   epilogue, not only GMMA utilization. If helper kernels are required, report
   total cost separately and get agreement to extend the one-kernel contract.

For each candidate record parent, changed axis, expected mechanism, exact
config, static code/resources, CPU correctness, simulated cycles, trace path
and accept/reject/UNRESOLVED. State the model's timing resolution; do not
manufacture sample variance or confidence intervals from a single invocation.
No latency or utilization target is a result until the model has run it.

## Hopper is a control, not a replacement model

MIG has fixed supported profiles; it does not generally provide an arbitrary
20-SM partition with the desired 32-MiB LLC. Green Contexts may constrain SM
resources on supported CUDA/device versions, but actual SM allocation and
cluster guarantees must be queried. Never change device partitions as an
implicit tuning step. A matching SM count still does not match cache, clocks,
latencies or memory bandwidth. A launch grid of 20 changes work supply only.

## Official Hopper control lessons

For a same-input upstream comparison, preserve the admitted binary and pin the
official source plus its own CUTLASS revision. Run the two extensions in fresh
processes if they register the same Torch operator namespace. Use identical
operator kwargs and CPU input hashes; validate both against the CPU oracle,
not only against each other. Report within-arm repeatability separately from
observed cross-arm raw equality.

Audit API initialization: upstream FA3 may launch an integer counter-fill
kernel, while the simulator-oriented port uses CPU zero plus H2D. Keep these
in complete-call timing, list them separately in the trace, and isolate the
attention kernel for a second explicitly instrumented comparison. The PPU1.7
single-target simulation rule must not be silently imposed by modifying the
official physical-device reference. Static code size or matched resources do
not prove equal speed; overlapping repeated sample ranges remain UNRESOLVED.

Evidence: flash-attn PPU1.7 branch, dev/ppu17/docs/h800-official-ab.md
(2026-09-26, B1/S2048/Hq32/Hkv2/D256 BF16 causal, H800 PCIe). This control
did not establish a port slowdown or a70% result; it is not a universal device
upper bound. Do not infer a short-sequence GQA target from long-sequence MHA
headline utilization, or use post-phase clock snapshots as in-kernel averages.

When a long-sequence curve plateaus, inspect the operating envelope before
attributing the full nominal-MFU gap to code. Join passive clock/power-limit
samples to the actual attention trace's wall-clock window; account for the
remote host timezone. A sampling hit on `SW Power Cap` during that window is
evidence of power limiting, not a cycle-weighted average or a measured fraction
of time throttled. Keep the registered peak denominator unchanged and obtain
authorization before changing clock/power settings. Do not use snapshots
during CPU references, idle gaps or another job as attention evidence.

Evidence: dev/ppu17/docs/h800-sequence-scaling.md (2026-09-26, same immutable
port/official H800 binaries, B1/Hq32/Hkv2/D256 causal). Median useful MFU rose
through8K, fell at16K, and both code paths hit the default350W power cap in
time-aligned snapshots. This is not a native PPU1.7 limit or proof that all
remaining performance loss is power rather than implementation.

## Causal geometry and scheduler counterexample

Do not infer that a reference's smaller KV tile or lack of an atomic task
counter will improve this port. Bind both axes separately and keep host
metadata allocation consistent with the selected scheduler. A single-tile
variant also changes CTA initialization count and execution order/LPT, so its
delta is not an isolated measurement of the atomic counter's cost.

Evidence: flash-attn branch `ppu17-causal-tuning`,
`dev/ppu17/experiments/causal-tuning/docs/results.md` (2026-09-26).
On H800, B1/H32/Hkv2/D256 BF16 causal, 128x80/64 crossed with dynamic LPT /
single-tile: all24 primary runs pass the same full CPU FP64 O/LSE oracle.
At S2048 single-tile is clearly slower; N64+LPT has no established benefit
at S2048 or S8192. Keep the default; this does not predict a20-SM PPU model.
N64 reduces shared allocation but still does not admit a second such CTA.
At S2048 it removes only2.86% of padded matrix work while adding21.43% KV
iterations/softmax updates (at8K:0.78% less work,24.03% more iterations).
This tradeoff is more informative than treating narrower tiles as free wins.

Explicit FlashInfer Hopper and cuDNN comparisons must bind actual device
symbols, not Python/host dispatcher names. FlashInfer's dispatcher is named
SinglePrefillWithKVCache..., but its generated Hopper kernel is
PrefillWithKVCacheKernel with TMA traits and SingleTileScheduler. Its returned
LSE is base2 on this API: normalize on CPU for the natural-log oracle, not via
an extra GPU kernel hidden in the reference timing. CUPTI's grid-averaged
"blocks per SM" is not resident occupancy.

## Scalar GDN control: inspect roles as well as opcodes

When adapting a vector-gated KDA collective to scalar GDN, scalar gates can
factor outside QK/KK and QH/KH products. This changes the floating-point
schedule even when the real-arithmetic identity is exact; use the independent
numeric contract, not an invented raw-equivalence claim against the old TF32
schedule. After that algorithm change, delivery-only candidates should again
require parent raw equality.

For an actual C++/DSL SASS comparison, extract the loaded JIT ELF completely
(including its program headers), select the exact dtype/initial-state symbol,
and compare equivalent recurring PC intervals. Do not add four C++ variants
against one DSL variant, count lowercase `x` in HGMMA shape suffixes correctly,
or treat an outlined wait backedge as a full straight-line loop traversal.
Line annotations alone can misattribute a register-pressure spill to a nearby
barrier call: trace the spilled value and its consumers.

Non-obvious findings on H800/CUDA12.8, scalar GDN C64/D128:

- A two-entry runtime-indexed named-barrier ID array lowered to local memory.
  A stateless selection removed the array, but its full-call timing remained
  UNRESOLVED. It did not eliminate all compiler spills.
- `-O3` did not disable CUTLASS pipeline DEBUG checks. An explicit, hash-bound
  NDEBUG build removed120 trap sites and improved this candidate modestly;
  retain public ABI/oracle checks and reject reuse across the flag change.
- Caching repeated gate coefficients reduced the state body's MUFU sites49
  to16 but slowed the complete call. Account for work transferred onto a TMA
  producer; do not optimize only the consuming warpgroup's instruction count.
  A later controlled composition is important: caching alone after the
  aux-load improvement had no established gain, nor had producer separation
  on the earlier pre-improvement parent. Publishing the cached channels on
  the existing separate alpha warp then won
  3–4% versus that incumbent, with parent fingerprints and unchanged math.
  Preserve channel-publication-before-commit and the producer's own consumer
  arrival/release. An isolated losing axis is not proof that its interaction
  with critical-path ownership can never win. This does not establish a win
  over FlashInfer's fastest path or native PPU1.7 performance.
- Pairing the wrong conversion seam left the targeted32 scalar F2F sites
  intact. The native postcondition rejected it before device timing; trace
  the producing accumulator and actual operand retile before editing.
- A live/causal predicate around initialized, in-range metadata reads kept
  repeated shared loads in the auxiliary body. Reading the metadata without
  that predicate, while masking the exponent input and preserving the final
  output mask, reduced LDS sites99 to21 and won a paired full-forward test
  (~180 to148us), with parent raw equality. This is legal only when the
  unmasked address and initialization lifetime are proved, including tails.
- Moving inverse ownership left obsolete metadata consumers in the state
  protocol. Compile the actual arrival-count expressions and plant a dead
  consumer as a negative; never remove a wait without updating the matching
  lifetime/participant contract. Here fewer native SYNCS sites still produced
  overlapping timing envelopes, so the protocol cleanup was not a speed win.

Evidence: GDN-QSA-sm80 `docs/SM90_FLASHINFER_SASS_20260926.md` and its
hash-bound campaign records. These are physical Hopper control observations,
not native PPU1.7 performance/ISA guarantees. Recheck lowering and lifetimes
with the actual PPU1.7 compiler/model before carrying the changes over.
Follow-up: `docs/SM90_SASS_FOLLOWUP_20260926.md`. After proving disjoint state
and physical output owners, removing only the two-WG alternating issue policy
retained all data barriers and passed numerics, but timing still overlapped.
Do not conflate a legal removal, fewer spill/barrier sites, and a speed win.
Separating the auxiliary full-chunk and final-chunk specializations then won
another4–5% versus the cached/separate-producer incumbent: full-aux static
sites1244->1140 with identical matrix work. It also changed whole-kernel
allocation (stack88/80->24/32B), despite unchanged state source; full-aux
local-load sites actually rose0->3. Do not attribute the gain solely to masks
or infer allocation changes only affect the edited warp's source. Actual
visitor/fragment coverage, tail/initial/GVA cases and parent fingerprints
were retained. This still did not beat fastest FlashInfer on that H800 cohort.

Further scoped evidence: `docs/SM90_AUXILIARY_SASS_20260926.md`:

- Once all metadata reads are proved initialized and in range, a final output
  select may suffice even if inactive exponent intermediates overflow. In this
  CUDA kernel, removing only the redundant exponent-input mask preserved live
  arithmetic and won another3–5%. Require direct parent-byte comparisons on
  overflow/underflow stress as well as ordinary tails; do not silently admit
  wider inputs or replace standard `exp2f` with fastmath. This is not blanket
  permission to unmask memory accesses or remove final causal selects.
- An explicit in-place diagonal FFMA removed35 row copies with unchanged21
  FFMA/21SHFL, yet both it and its composition with the mask improvement lost
  complete-forward timing. Whole-kernel allocation changed. Keep shuffles
  unconditional when only some lanes update, and do not promote a native
  instruction-count win without its parent-paired device result.
- Distinguish cached prefix factors from relative decay: `exp(last-prefix[t])`
  can remain duplicated across state WGs after `exp(prefix[t])` is cached.
  Proving the actual operand map exposed4096 thread/token evaluations for64
  coefficients. Publishing the extra channel under the existing independent
  gate producer's lifetime won4–6%, with explicit rounded subtraction,
  parent fingerprints and unchanged matrix/barrier counts. The extra512B and
  producer SFU work are real costs; neither the arithmetic identity nor the
  native state EX2 reduction alone establishes a win on another backend.
  H800 still lost fastest FI by about8%; native PPU1.7 remains unmeasured.

### A proved fast domain is not necessarily a generated fast path

For CUDA12.8/SM90, this scalar GDN's standard `exp2f` lowers to an
underflow test, optional RN half-input, MUFU.EX2 and optional RN square.
An existing producer can prove that all finite prefix differences exceed
-126 by reducing their rounded span. That arithmetic proof does **not**
prove the compiler removes per-element work:

- Branching around two templated whole epilogues was if-converted into
  duplicate native paths (64->124 static EX2 sites, stack24/32->112B).
  Numerics passed, but complete forward153.776us lost to120.048us control.
- A flat inline-PTX sequence restored64 sites and the old stack sizes.
  However, conditional `setp` became `FSETP.LT.AND ... !P2`: the comparison
  still executes.122.3995vs120.560us had overlapping envelopes. Do not label
  it a compare-elimination win or promote it because the C++ says fast path.

Before carrying a compiler-specific math lowering between backends, inspect
the separate standard-library native path and test the exact exponent seam,
including subnormals, specials and exhaustive boundary intervals. Here an
unconditional direct EX2 negative mismatched262560inputs; an actual device
producer with one omitted prefix incorrectly admitted160lane flags. A second
host formula alone would not test that producer. These are exact observed
tests, not a universal proof for all float inputs/compiler versions.

Evidence: GDN-QSA-sm80 `docs/SM90_EX2_GUARD_20260926.md` and its3capture/
216forward manifest. Keep the previous incumbent; do not weaken its contract
or infer native PPU1.7 instruction semantics from this Hopper result.

### Role budgets can serialize WGMMA without changing CTA occupancy

On CUDA12.8/H800, redistributing the same65536-register CTA pool from
loader/aux/state/state24/104/192/192 to24/120/184/184 triggered ptxas C7512
in every real specialization. Native no-initial-state HGMMA count stayed112,
but WARPGROUP.DEPBAR sites grew18->112: the compiler serialized each matrix
operation. Preserve that warning and reject the intended asynchronous-path
experiment before timing. A fixed aggregate budget is not proof of adequate
per-role accumulator capacity;192 is this kernel/compiler's observed safe
point, not a universal hardware threshold. Native PPU1.7 must be checked
separately.

Leader-only role timestamps can locate producer versus consumer waiting,
but even unsynchronized probes changed spills and added~8% to full-forward
time here. Bind actual native stamp positions to completion barriers, verify
all CTA/chunk/role slots, measure perturbation, and never add overlapping role
intervals or rank the instrumented image. The observed~58us inverse interval
included probes/synchronization, not58us of proven excess over FlashInfer.
Simplifying one inverse coordinate removed a shuffle but increased spills;
paired timing remained unresolved. Evidence:
GDN-QSA-sm80 `docs/SM90_ROLE_CRITICAL_PATH_20260926.md`.

### Independent value tiles trade duplicated work for grid fill

For scalar GDN, disjoint V-column state/output owners can form separate CTAs
without a reduction or a changed recurrence. On CUDA12.8/H800114SM, splitting
V128 into two V64 CTAs removed one state WG per CTA, allowing aux104→232
registers while retaining state192 and asynchronous WGMMA. The primary
B1/T2048/Hv32 case won~101vs113us fastest FlashInfer. This does **not** make
the duplicated QK/KK/inverse and Q/K loads free: the first B2/Hv32 expansion
produced128 CTAs, still one resident CTA per SM, and lost~194vs114us. The old
unsplit parent was~125us there. Numerics and parent raw equality passed.

Before promoting a grid-fill change, test both sides of its actual occupancy
wave boundary with the same immutable images. Preserve the unsplit path and
report the duplicated auxiliary work. In particular, the current PPU1.7
20SM model has a different wave boundary; these H800 wins are not a PPU
selector or a native-lowering guarantee. Evidence:
GDN-QSA-sm80 `docs/SM90_VALUE_SPLIT_20260926.md` and
`docs/SM90_MULTI_WORKLOAD_20260926.md`: the completed14-workload inventory
also exposes a different T8192 gap to FlashInfer's CP path and a low-head
gap to FlashQLA's V32 path. They need different mechanisms, not one global
grid rule. One reference fails the fixed numerical gate; retain that failure
instead of turning missing performance evidence into a win.

When trying to keep V128 in one state WG, storing only the rounded BF16 H
operand in shared does not remove the live FP32 H/O1/SK accumulators. Here
128+64+64 values/thread already exceed248 registers before control. The
actual CUDA12.8 S42 image emitted C7512 and920/1016B stack despite a correct
16384-cell STSM-to-SS descriptor map. Two-WG variants passed the same map,
but did not meet their declared native/resource gate either. A tensor
placement proof is not a register-liveness or asynchronous-lowering proof.
Keep these as rejected compile experiments, not measured slowdowns or a
universal rejection of shared operands. Evidence:
`docs/SM90_MULTI_WORKLOAD_FOLLOWUPS_20260926.md`; native PPU1.7 unmeasured.

### Price the live interval of an asynchronous overlap

Two scalar-GDN experiments on CUDA12.8/H800 distinguished legal overlap from
useful overlap. Issuing O2 then KV with **separate unscaled/scaled operands**
kept both operands valid until wait0 and improved high-head full-forward nsys
time about125→122us. Reusing the unscaled operand in place would race O2.
By contrast, issuing next-chunk KK before the current inverse kept32extra
FP32 registers live across14inverse HMMA sites. Native code genuinely retained
the overlap with no premature wait or register alias, and parent RAW tests
passed, but stack grew16/104→88/152B and six graph screens all lost (~30–37%).
The earlier next-K wait is also a possible cost; spills alone are not a causal
decomposition. Keep the second change rejected, rather than treating async
opcodes as performance admission. This overlap mechanism is not transferable
to PPU1.0, which lacks Hopper WGMMA groups. Evidence:
GDN-QSA-sm80 `docs/SM90_PAIRED_STATE_20260927.md` and
`docs/SM90_LOSING_CELLS_20260927.md` (S50/S62); native PPU1.7 still unmeasured.

When exposing formerly equal ring-depth axes, use asymmetric actual-type
tests. The same scalar collective hardcoded QK=KK=2 but sized KK storage with
the QK depth. Equal-default numerics and separate integer models could not
detect the coupling. Compiling QK1/KK2 with the old binding fails the actual
storage-capacity assertion; QK2/KK1 tests the opposite direction. Bind each
producer, storage extent and reader pipeline to its own axis before timing.
This is a verification method for PPU as well, not evidence that shallower
rings or extra saved shared bytes improve another target.
