# PPU Kernel Design Agents

Follow `docs/agent-flow.md` and `prompts/basic-flow.md`. Keep the reusable
workflow small. PPU knowledge and tool guidance belong here; task kernels,
datasets, private paths, reports and binaries belong in task workspaces.
Repository-facing prose, code and comments use English.

For a PPU task, start with `docs/ppu.md` and `prompts/ppu.md`. Identify the
actual device/generation, then resolve the task's native build, oracle and benchmark. Run
the KDA loop on the requested device; general hardware-documentation gaps are
not prerequisites when the task's required primitives can be built and tested.

Read `docs/ppu-adaptation.md` before changing the workflow. Preserve KDA's
contract / draft / plan / candidate / evidence structure. Select ACU or Asys
by the analysis question. MCP is optional and does not change measurement
semantics or grant device access.

Knowledge is distilled from multiple operator repositories, local memory and
skills. Source anchors are in `skills/ppu-kernel-knowledge/references/sources.md`.
Keep required PPU guidance in tracked Markdown with relative links. Use official
public repositories for dependencies and algorithm baselines, not personal forks.
Bring needed historical documentation into the relevant local reference instead
of linking an author's operator repositories. Do not require another machine
to have private memory or globally installed skills. Distinguish task-owned
extensions from capabilities verified in the official dependency revision.
Update the relevant synthesis and provenance together. Resolve later corrections
before promoting a remembered observation into guidance. Never transfer a
PPU1.0 layout, NVIDIA timing, or simulator result to another target silently.

For documentation changes, check local links, provenance and `git diff --check`.
For skill changes, also validate frontmatter and exercise the documented tools
where available. Add executable tests when code or behavior warrants them.
Preserve upstream licenses and third-party attribution. Use explicit paths
when committing, follow DCO, and do not publish or run device jobs unless the
active task authorizes them.
