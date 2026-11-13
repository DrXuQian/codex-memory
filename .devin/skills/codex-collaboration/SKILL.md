---
name: codex-collaboration
description: >
  Operating manual for delegating kernel work to codex (MCP `mcp__codex__codex` or `codex exec`) from
  Claude Code, learned by getting each of these wrong: the channel is request/response so writing
  .coord/INBOX.md is NOT dispatching; the MCP tool's cwd/sandbox/approval-policy are TOP-LEVEL
  parameters and nesting them in `config` silently drops them; `approval-policy: never` means "never
  ask", i.e. AUTO-REJECT escalation, not auto-approve; a container whose seccomp blocks user
  namespaces makes codex's bwrap sandbox unusable so every command fails in 0 ms; heartbeats cannot
  detect a hang because a process blocked mid-turn writes none; and `git add -A` in a shared worktree
  commits codex's work-in-progress under your message. Invoke before dispatching to codex, when a
  dispatch appears to hang, or when deciding what to tell the user about codex's state.
---

# Working with codex

## The channel is request/response. Writing is not sending.

codex's process exists only for the duration of a call. `.coord/INBOX.md` is the **persistent record a
call refers to**, not the channel. Anything appended after a call ends sits there with no mechanism
that will ever open it.

**Three levels of evidence. Each licenses exactly one word.**

| you hold | you may say | it proves |
|---|---|---|
| `## NNN` in INBOX.md | **written** | nothing about delivery |
| a dispatch call with a task id | **sent, unconfirmed** | you dispatched |
| `inbox-consumed >= N` in STATUS.md | **read** | codex's own receipt |

Reporting level 1 as level 3 is the single most repeated failure in this collaboration — five times in
one session, with the rule and a CI gate for it already in place. Rules and gates did not stop it; the
judgement criterion does, because it asks *which artifact is in your hand* (checkable now) rather than
*did you remember* (not checkable).

**No task id ⇒ the word "dispatched" is not available to you.**

## Continue the thread; do not start a new one

**Every `mcp__codex__codex` call is a FRESH session.** The returned `threadId` differs each time, so codex's only
continuity is the repository: the code, `.coord/INBOX.md`, and the `.coord/STATUS.md` it writes itself. That is why
the INBOX protocol is load-bearing and why dispatch prompts have to carry so much — they are not verbose, they are
the entire context.

**`mcp__codex__codex-reply` continues a thread** (`threadId` + `prompt`). Default to it. Start a new thread only
when the subject genuinely changes.

**Why it matters more than cost.** A two-phase task — "attack this conclusion, then implement if it survives" —
loses its middle when phase two is a new session: the attack findings have to be re-narrated by you, and
re-narration is exactly where information is lost and where your own summary of someone else's reasoning gets
substituted for their reasoning. Continuing the thread removes you from that seam.

**One reply in flight per thread.** Two concurrent `codex-reply` calls on the same threadId do not queue: codex
answers both in a single turn, that answer is routed to ONE task id, and the other hangs until the 6-hour MCP cap
and reports `failed: timed out`. No work is lost -- the content arrived under the sibling id -- but the failure
looks like a dead codex, and it is a failure mode that the "always continue the thread" default makes MORE likely,
not less. Wait for the notification before replying again; if you must send something urgent mid-flight, put it in
INBOX.md, which is the persistent record that the NEXT turn will read anyway.

**So capture the threadId from every result.** It is in the task notification payload. Without it you cannot
continue, and you will not notice until the moment you want to.

**A fresh thread is not free of risk either:** with no history codex can re-walk a path already rejected. If you
do start fresh, the INBOX item must carry the REJECTION and its reason, not just the current ask — e.g. "F=4 was
once declared dead and that was retracted, so it is uncharted, not disproven."

## Dispatch mechanics that silently do nothing

**The MCP tool's parameters are top-level.** `cwd`, `sandbox`, `approval-policy` are siblings of
`prompt`, not members of `config` (`config` is for `~/.codex/config.toml` overrides). Nesting them
drops all three with no error, so codex runs with defaults while your call reads as if it were
configured.

**`approval-policy: never` means "never ask", which is auto-REJECT.** When codex needs to escalate —
e.g. its sandbox will not start — "never" denies the request. It is not "auto-approve everything".

**`on-request` only helps if the bridge can route the prompt.** Over MCP the escalation may come back
`Rejected("approval request failed")` because there is no channel to a human. Check that before
concluding codex is broken.

**Permissions**: `mcp__codex__*` absent from the settings allow-list means every dispatch waits on a
human click. An unclicked prompt looks exactly like a hung codex from the outside — zero CPU, idle
socket, `inbox-consumed` never moving — because codex received nothing.

## The sandbox, on a container that blocks user namespaces

codex sandboxes commands with **bwrap**. If the container's seccomp filter blocks
`clone(CLONE_NEWUSER)`, bwrap cannot start and **every shell command codex runs exits in 0 ms**,
including the `git pull` it needs to read its own inbox.

Diagnose in one line — `unshare -U true`. "Operation not permitted" with
`/proc/sys/user/max_user_namespaces` large and `unprivileged_userns_clone=1` means seccomp, not
sysctl, and it cannot be fixed from inside the container.

The working configuration there is `sandbox: danger-full-access` with `approval-policy: never`, so
codex never needs to ask. **That is a privilege decision belonging to the user**, not one to make
silently; the container being the isolation boundary is an argument to put to them, not a licence.

## `codex exec` as a second channel

`codex exec --sandbox <mode> --skip-git-repo-check - < prompt.txt > log 2>&1 &` has real advantages
over MCP: no client-side approval gate, output streaming to a file you can read at any moment, a pid,
and you can stop it. It hits the same bwrap wall, so it is a different channel and not a different
sandbox.

## Telling "working" from "hung"

**Heartbeats cannot answer this.** codex writes `last-heartbeat` at ITS checkpoints; a process blocked
mid-turn writes none. The instrument goes silent exactly when it is needed.

Two signals from outside, neither needing codex to be healthy:

- **CPU ticks** — `/proc/<pid>/stat` fields 14+15, sampled twice.
- **The socket's timer** — an ESTABLISHED connection with empty queues *and* `timer_active == 0` has
  no retransmit, keepalive or probe scheduled; the kernel will never wake the reader.

**One frozen window is not a hang.** A live codex was measured using **~4.5 s of CPU across twenty
minutes** — it wakes per streamed chunk and sleeps between. A five-second sample landing in a gap sees
exactly what death looks like. Require the state across several windows *and* zero cumulative CPU over
the whole span; a gap cannot survive the span because the next chunk lands inside it.

**Two more traps in writing such a probe:** matching `codex` anywhere in a cmdline makes the probe
match *itself* (a liveness check that cannot fail); and taking the top-N processes by total CPU can
miss a freshly-started one. Match `argv[0]`.

**And the verdict must not name a cause.** "CPU frozen, socket idle and untimered" is produced
identically by *a reply that will never arrive* and *a request that was never delivered*. Call it
STALLED, not HUNG, and check the cheap cause (permissions) before the expensive one (a dead peer).

`ci/codex_liveness.py` in quactlize implements all of this.

## The MCP wrapper carries a fuse, and it kills a HEALTHY turn

**Observed 2026-08-12.** codex had been working for three hours — seven commits, gates green,
mid-derivation on the load-bearing seam. Then, with no warning in its own log:

    turn_aborted   reason=interrupted   duration_ms=10818891   (3.005 h)

Nothing was wrong with codex. **Every `codex-reply` leaves a background wrapper whose tool timeout is a
fuse, and when the fuse burns down it aborts whatever turn is running.** `TaskStop` on that wrapper does
the same thing. The fuse is not per-turn: it starts when the wrapper starts and can span several turns,
so the turn it kills is usually not the one that lit it.

**Where it is set:** `~/.claude.json` -> `mcpServers.codex.timeout`, milliseconds. It shipped here at
`21600000` (6 h).

**Do not delete the field to disable it** — the fallback default is far SHORTER, so deleting makes every
turn die sooner. Raise it (`604800000` = 7 days). **The new value only takes effect on the next Claude
Code start**, so the running session keeps the old fuse; plan the night around the old number.

**This is not the same setting as `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`.** That one is about silence
between chunks and is already `0` here. A wrapper that is streaming happily still burns its fuse.

### The fix: run the thread over `codex exec resume`, not the MCP tool

**Verified 2026-08-12, not theorised.** After four aborts in one evening — 3.01 h, 2.72 h, then 42 s
and 24 s for two restarts that the next fuse killed on arrival — the thread was moved to the CLI:

    cd <repo>
    codex exec resume <session-uuid> \
      --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
      -o <last-message-file> -  < prompt.txt

**Same session id, so the whole conversation carries over** — this is not a fresh thread. And there is
no MCP wrapper, so there is no fuse. A fifth fuse fired eighteen minutes later and the CLI turn kept
running through it, which is the actual proof.

Two flag placement traps: `resume` does **not** accept `-C/--cd` (put the process in the repo with
`cd` instead), and the global options must sit **after** `resume`, not before it.

**When several fuses are queued, restarting over MCP is a losing game.** They were all created inside a
three-minute window hours earlier and burned down one after another, each killing whatever turn was
running — including the restart sent seconds before. Switch channels instead of retrying.

**Stop the surviving wrappers while codex is idle.** `TaskStop` aborts a running turn, so the moment
right after an abort — or right after a fresh turn starts, when losing it costs a handful of events —
is the cheap window. Leaving one alive means it fires later, on a turn holding hours of work.

### The probe must distinguish three states, not two

`turn_aborted` and a genuine hang look identical from the outside — in both, the event log stops
growing. They need opposite responses, so a probe that only knows "done / not done" is not enough:

| exit condition | what actually happened | what to do |
|---|---|---|
| `task_complete` appears | the turn **finished normally** | review, then dispatch the next turn — codex is stopped and INBOX is unread by construction |
| `turn_aborted` appears | something **outside** killed a healthy turn | resend `codex-reply` immediately; the uncommitted work is usually still on disk |
| N minutes with no new event | possibly hung — see the section above | diagnose before resending |

**A probe must notify by EXITING, not by printing.** Background output is not read unless something
brings you back; only the process ending does that. A long-lived probe that prints status forever is
indistinguishable from no probe — that mistake cost four hours of codex idling once already. Poll on
the order of minutes, not tens of minutes: a long interval saves nothing and converts "it stopped" into
a whole idle block.

### The two channels fail in opposite ways — and there is a fourth state

Neither channel is strictly better; they trade one failure for another, and knowing which you are on tells
you what to watch for.

| | MCP `codex-reply` | `codex exec resume` |
|---|---|---|
| carries the 6 h fuse | **yes** — kills healthy turns | no |
| survives a Claude Code restart | the server does, but… | **no** — it is a child process and dies with the parent |
| resumes a thread after **its own** process restarts | **no** — `Session not found for thread_id`, the mapping was in memory | **yes** — reads the rollout file from disk |

Observed both in one night: the fuse killed four MCP turns, so the thread moved to the CLI; then the
Claude Code process restarted, the CLI child died with it, and the MCP server had also restarted so
`codex-reply` answered `Session not found`. Only `codex exec resume <uuid>` could pick the thread back
up, because the on-disk rollout is the durable copy.

**This adds a fourth state the probe must separate**, and it is the one that looks most like a hang:

| what you see | what happened |
|---|---|
| `task_complete` in the log | finished normally |
| `turn_aborted` in the log | interrupted, marker written |
| log stopped, **process alive** | genuinely hung — diagnose before resending |
| log stopped, **process gone, no marker** | **killed** — the log simply ends mid-turn |

The last two are indistinguishable from the log alone. The discriminator is whether the process still
exists, so a probe that only reads the transcript cannot tell them apart and will sit through a dead
session waiting for events that will never come.

Match `argv[0]`/`argv[1]` when checking, not a `-f` pattern: `pgrep -f 'codex exec'` matches the shell
running the check, so the liveness test can never fail. `ps -eo args --no-headers | awk '$1 ~ /codex$/ && $2 == "exec"'`
does not have that problem.

### After an abort, the work is on disk

An aborted turn does not roll back the worktree. Everything codex had written but not committed is
still there. **Before anything else, tell codex its work survives and have it commit with explicit
pathspecs** — and say plainly which parts are unfinished, so nothing half-done is committed as
complete. Do not commit it yourself; see the worktree rules below.

The restart prompt must also say **that the abort was external**. Otherwise codex reads the gap as its
own failure or as the task being cancelled, and re-derives what it already had.

## Sharing one worktree

**Never `git add -A`.** The ownership split is agreed at the level of *editing*; `-A` ignores it at the
level of *committing* and sweeps codex's in-progress files — possibly mid-edit — into a commit whose
message describes something else. `git add <explicit paths>` and read `git status --porcelain` first:
a path outside your half means codex is working, not that you should include it.

**If you already did: do not rebase.** codex is running; rewriting history under it is worse than a
wrong message. Append an INBOX item saying which item was committed, telling it not to redo the work
and to check whether what landed is what it intended.

`.coord/STATUS.md` is codex's file. Committing it yourself destroys the receipt your own delivery
criterion depends on.

## Getting useful work back

- **Ask for a commit per sub-item.** "Commit after each of ①②③ rather than batching" makes progress
  observable without codex having to report it, and gives a second cheap liveness signal.
- **Ask it to write `inbox-consumed` before starting work**, not after finishing.
- **Send one item, not four.** A dispatch that also says "and read this whole third-party source tree"
  is one you cannot distinguish from a stall.
- **Tell it what you changed on your side**, including things it did not ask about. It reads the repo,
  and an unexplained rename reads as breakage.
- **Give it the design input rather than the design.** Pointing at
  `Kernels/general/w4a16_gemm/fpA_intB_standalone/` and naming the field
  (`enableCudaKernel`, first in the record, tile fields meaningless when set) got that encoding back
  verbatim, better documented than the request.

## codex is often right

In one session it overturned five of my blocking judgements, each time correctly: a format that was
already supported by a trait-driven collective; a builder that already routed a case I said it did
not; a fault-injection heuristic that would have hit the wrong tensor. **It is in the files and you
are not.** A "this is impossible" derived by reasoning should be assumed wrong until it has been read
off the object. See `blocker-mechanism-vs-wiring`.

Align on decisions and commits with codex *before* reporting to the user; give the user the
synthesised conclusion, not the negotiation.

## Traps this collaboration actually hit (2026-08-07)

Nine of these are mine, and eight of the nine share one root: **I concluded from an instrument I had not
checked.** The tenth is codex's and it is the same shape. Each entry gives the judgement that catches it *before*
the conclusion leaves your mouth.

### Writing is still not sending

I unblocked codex with a commit, wrote "you can proceed" into INBOX, and never dispatched. codex sat idle at
`inbox-consumed: 088` while I reported it as working. The rule at the top of this file already says this; having
the rule did not stop it, because the failure happens at a moment when you *feel* you have communicated.

**Judgement:** before saying codex is doing anything, name the task id from the dispatch call. No id, no verb.

### The shared container

codex and I share `/tmp`. I ran `g++ ... | head -5 && /tmp/sc` — the compile FAILED, `head` returned 0, `&&`
fired, and `/tmp/sc` **existed because codex had built it**. I nearly reported codex's probe output as my own
measurement.

Two rules, both cheap: **never read success through a pipe** (`cmd | head` reports head's status, and this
repository has now paid for it four times), and **name scratch binaries uniquely** (`/tmp/claude_<thing>`).

### Reproduce a gate's failure WITH the gate

The syntax tier reported 40 `mixed policy` assertions on `test_int1_sweep.cu`. I hand-rolled an nvcc line, got 0
at the base revision, and announced twice — with different attributions — that codex's commits had introduced it.
codex re-ran **the actual gate** in a clean worktree at the same base and got the same 40. It was pre-existing;
my command simply did not carry the gate's flags.

**Judgement:** a hand-rolled repro of a gate failure is a different experiment. If you must hand-roll, say so and
do not attribute. Attribution requires the gate, at a sha, in a clean tree.

### Gate results need a sha (and a clean tree)

On a shared worktree, `local_gates` measures a state that is **nobody's commit**. codex reported "4 reds are
pre-existing" from its own dirty tree; I reported an attribution from mine. Both unfalsifiable.

`git worktree add -q --detach /tmp/wtX <sha>` is the whole fix. Remove with `--force` and `prune` afterwards, and
**do not cd into it before removing** — getcwd fails.

To codex's credit it later re-ran four gates properly and replaced its own sloppy claim with a precise
classification: two stale gates, one stand-in-environment failure, one checker false positive. **That is what a
retraction should look like**, and it is worth asking for in those terms.

### Do not file your own action items into codex's queue

My review of #44 ended in "there should be a gate that compiles at each R", and I sent that to codex along with
the finding. `ci/` is mine. A review conclusion whose action lands in your own half is work, not a request.

**Judgement:** after every review, sort the conclusions by whose files they touch before writing the INBOX item.

### Run their test the way their test runs

codex added `tests/test_moe_only_filter.py`. I ran `python3 tests/test_moe_only_filter.py`, got rc=0 with the
regression re-injected, and was one sentence from reporting "the gate is empty". It is a pytest module: running
it directly imports and exits. Under `pytest` it fails correctly on the injected regression.

**Judgement:** an rc=0 from a test you invoked a new way is not evidence until a **negative control** fails.
Inject the exact defect the test was written against; if it still passes, THEN you have a finding.

### Fit against the variable the machine actually consumes

I fitted `t = a + b·W` with `W` = useful FLOP across two token counts and derived "723 µs of fixed per-call
overhead". The machine does *padded* work, and `msk` fell 14.5% → 5.4% between the points, so `mt` grew 3.62×
while useful FLOP grew 4×. Using `mt`, no intercept is needed. A later M=1 run took 20.8 µs total — an order of
magnitude below the "constant" — which falsified it outright.

**Judgement:** before fitting, ask which quantity the hardware is proportional to. Two collinear terms cannot be
separated by two points, and a fit will happily invent a constant to absorb the difference.

### A probe that trips over the thing it is probing

To measure what relaxing `ScaleCopyCoverage` would open, I wrote a probe that skipped that exclusion — but its
first line called `kernel_exclusion()`, which is **where the exclusion lives**. It returned early, my skip never
ran, and I reported "+0%, relaxing buys nothing". The real answer is +48% to +99%, and it recovers a warp shape
that is otherwise 0 rows.

**Judgement:** when a probe reports "no effect", the first hypothesis is that the probe did not reach the
subject. Prove the bypass fires — print the count of rows that took it.

### Verify a command before handing it over

I gave a build command containing `MOE_STAGES=6`. That variable exists in exactly two strings, both of which
*advise using it*, one printed by the build itself; nothing forwards or reads it. I also guessed the binary path
when `build.sh` finds and prints it.

**Judgement:** every knob in a command you hand over must be traceable to a forwarder or a cache var, and every
path to something that printed it.

### The class these keep landing in

Four separate checks this session hardcoded a property of their subject and reported the mismatch as the
subject's fault: the units gate spelled six `[0-9]+` and said "the table declares 404"; the provenance gate
hardcoded a macro prefix and said grouped tables "predate the durability guard"; `generated-edges` resolved
build-dir output against the source tree and said "the generator will emit a source that cannot compile"; and the
tactic space encodes a scale-copy constraint so a legal warp shape is never emitted at all.

**Judgement:** when a check's message blames the artifact, read the check first. And prefer a `static_assert` in
the kernel over a rule in the enumerator — the enumerator makes "lost" and "never generated" identical.
