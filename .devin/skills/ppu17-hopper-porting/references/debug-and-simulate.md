# Debugging and single-launch simulation

## Compile the thing that will run

1. Bind repository/backend revisions, dirty diff, compiler version, complete
   flags and include roots. Avoid unowned flat overlays or header copies.
2. Probe the compiler's real device target using the **same flags** as the
   kernel. Assert compiler-provided architecture/features; do not supply those
   macros yourself. Native provenance also needs a capable PPU toolchain,
   whereas CUDA source/simulator-input compilation is a distinct mode.
3. Instantiate all admitted entrypoints. Require live multiply and output
   paths per kernel; a single good body must not hide an empty sibling.
4. Assemble, not only preprocess or emit PTX. Legacy `ppu.bar.*` leakage in
   this port survived PTX emission and failed at assembly.
5. Compile the real host dispatcher and link its generated definitions.
   Unresolved Torch/runtime symbols in a relocatable host-link check are not
   a loadable extension certificate. State that boundary, and test package
   import separately when a matching Python/Torch ABI is available.

Useful negatives: wrong target/legacy macro, missing generated unit, one empty
causal body, removed output store, missing cross-TU definition, wrong extension
identity. Missing environment capability is SKIP; an actual planted defect
remains FAIL, never an environment skip.

## Debug a numerical mismatch

Stop interpreting timing for that specialization. Bind the failure to one input
fixture, binary and launch. Compare Q/K/V strides and base semantics, GQA head
mapping, causal alignment, tail masks, TMA offsets and GMMA accumulator/output
ownership before changing arithmetic. Use the actual CuTe objects and traits
when enumerating layouts, with an independent logical-coordinate anchor.

Audit async lifetimes explicitly: producer issue → TMA completion → GMMA read
and completion → stage reuse. A CTA barrier does not stand in for an async
completion wait. Verify barrier phase, expected bytes and arrival counts.
Do not add waits until a test passes and label that a root-cause proof.

Softmax attention is not generally RAW-BIT equal to an FP64 reference. Fix
atol/rtol and nonfinite/LSE checks before results; retain exact-constructed
subtests and raw-bit replay only for properties they can prove. A negative
fixture must exercise the same mapping or lifetime defect being checked.

## One simulated target, CPU reference only

The current user contract is **one target invocation per simulation process**:

- No warmup, repeats, event-timing loops, automatic tuning, GPU reference,
  fallback retry or profiler replay. One fresh process per candidate/case.
- PyTorch may allocate tensors and invoke the extension. Create random data,
  casts, masks, scalars and correctness reference on **CPU explicitly**;
  copy prepared tensors to the target. Do not rely on the global default device.
- Audit the public API, not just the harness. `zero_()`/fill, `.contiguous()`,
  padding, metadata preprocessing, split/combine, quantization and hidden
  autograd can add kernels. For the admitted fixed forward, initialize the
  scheduling counter on CPU and copy it; use already-contiguous inputs.
- Synchronization and H2D/D2H copies are allowed but must not be reported as
  attention compute time. Check the simulator trace for the actual kernel
  symbol and launch count. A source call-count test is necessary, not final
  proof of what the runtime launched.
- D2H then compare on CPU. A row-blocked CPU FP64 oracle can cover the full
  shape without materializing every head's S×S score matrix at once.
- Forward only: no backward in the simulated trace. State/O/LSE finite alone
  is not a numerical correctness verdict; keep NOT_CHECKED visible.

Record simulator executable/version and model config hash, source and binary
hash, selected entrypoint, input hash/seed, dtype/layout/strides, shape, causal
mask convention, grid/block/cluster, runtime SM count and model cache size.
Use the simulator's cycles/time and frequency. Python elapsed/event time is
not simulated kernel time. Do not invent a simulator CLI when it has not been
provided; hand off a single-call application command for the actual tool.

For the FA integration, `tools/run_ppu17_forward.py` is that application.
Default priority case: B1/S2048/Hq32/Hkv2/D256/BF16, causal. Start correctness
with small tails and distinct GQA heads, then verify the real input shape.
The build and run must reject stale FA2/legacy extensions, not fall back.
