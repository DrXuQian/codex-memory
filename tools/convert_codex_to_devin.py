#!/usr/bin/env python3
"""Convert Codex / Claude Code state into a Devin-readable knowledge pack."""
import collections, datetime as dt, glob, hashlib, json, os, re, shutil, sqlite3, sys

EXPORT = "/root/autodl-tmp/codex-export"
OUT = f"{EXPORT}/devin-pack"
DB = f"{EXPORT}/db"
HOME = "/root"

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "<REDACTED_PRIVATE_KEY>"),
    (re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_\-]{20,}"), "<REDACTED_API_KEY>"),
    (re.compile(r"\bhf_[A-Za-z0-9]{30,}"), "<REDACTED_HF_TOKEN>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<REDACTED_AWS_KEY>"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"), "<REDACTED_SLACK_TOKEN>"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}(?:\.[A-Za-z0-9_\-]{4,}){0,2}"), "<REDACTED_JWT>"),
    (re.compile(r"(密码|口令)\s*(?:是|为|:|：|=)?\s*[A-Za-z0-9!@#$%^&*_.\-]{4,}"), r"\1<REDACTED>"),
    (re.compile(r"\bLTAI[A-Za-z0-9]{12,}"), "<REDACTED_ALIYUN_KEY>"),
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]{20,}"), r"\1 <REDACTED>"),
    (re.compile(r"(?i)\b(password|passwd|密码|api[_-]?key|access[_-]?token|secret[_-]?key|auth[_-]?token)(\s*[:=：]\s*)([\"']?)[^\s\"'<>]{6,}\3"), r"\1\2<REDACTED>"),
    (re.compile(r"(ssh\s+(?:-p\s*\d+\s+)?[\w.\-]+@[\w.\-]+(?:\s+-p\s*\d+)?)\s+(?![-<])[A-Za-z0-9!@#$%^&*]{8,}\b"), r"\1 <REDACTED_PASSWORD>"),
]
REDACTIONS = collections.Counter()
KNOWN = set()
CAPTURE = [
    re.compile(r"sshpass\s+-p\s*['\"]?([^\s'\"]{4,})"),
    re.compile(r"(?:密码|口令)\s*(?:是|为|:|：|=)?\s*([A-Za-z0-9!@#$%^&*_.\-]{4,})"),
    re.compile(r"(?i)(?:password|passwd)\s*[:=]\s*['\"]?([^\s'\"<>,]{6,})"),
    re.compile(r"ssh\s+(?:-p\s*\d+\s+)?[\w.\-]+@[\w.\-]+(?:\s+-p\s*\d+)?\s+(?![-<])([A-Za-z0-9!@#$%^&*]{8,})"),
]
KNOWN = set()
CAPTURE = [
    re.compile(r"sshpass\s+-p\s*['\"]?([^\s'\"]{4,})"),
    re.compile(r"(?:密码|口令)\s*(?:是|为|:|：|=)?\s*([A-Za-z0-9!@#$%^&*_.\-]{4,})"),
    re.compile(r"(?i)(?:password|passwd)\s*[:=]\s*['\"]?([^\s'\"<>,]{6,})"),
    re.compile(r"ssh\s+(?:-p\s*\d+\s+)?[\w.\-]+@[\w.\-]+(?:\s+-p\s*\d+)?\s+(?![-<])([A-Za-z0-9!@#$%^&*]{8,})"),
]


def redact(s):
    if not s:
        return s
    for c in CAPTURE:
        for m in c.finditer(s):
            if not m.group(1).startswith(("<", "$")):
                KNOWN.add(m.group(1))
    for c in CAPTURE:
        for m in c.finditer(s):
            if not m.group(1).startswith(("<", "$")):
                KNOWN.add(m.group(1))
    for pat, rep in SECRET_PATTERNS:
        s, n = pat.subn(rep, s)
        if n:
            REDACTIONS[pat.pattern[:40]] += n
    return s


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(redact(text))


def ts(v):
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        if v > 1e12:
            v /= 1000
        return dt.datetime.utcfromtimestamp(v).strftime("%Y-%m-%d %H:%M UTC")
    return str(v).replace("T", " ")[:16] + " UTC"


def clip(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + f"\n… [truncated {len(s) - n} chars]"


def slug(s, n=50):
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s or "").strip("-")
    return (s[:n] or "untitled").rstrip("-")


def one_line(s, n=240):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n] + " …"


def fence(s):
    s = s or ""
    ticks = "```"
    while ticks in s:
        ticks += "`"
    return ticks, s


# --------------------------------------------------------------------------- Codex
def codex_db():
    titles, meta, spawns, goals = {}, {}, collections.Counter(), {}
    try:
        c = sqlite3.connect(f"{DB}/state_5.sqlite")
        c.row_factory = sqlite3.Row
        for r in c.execute("select * from threads"):
            r = dict(r)
            titles[r["id"]] = r.get("title") or ""
            meta[r["id"]] = r
        for (p,) in c.execute("select parent_thread_id from thread_spawn_edges"):
            spawns[p] += 1
    except Exception as e:
        print("state db:", e)
    try:
        c = sqlite3.connect(f"{DB}/goals_1.sqlite")
        c.row_factory = sqlite3.Row
        for r in c.execute("select * from thread_goals"):
            goals[r["thread_id"]] = dict(r)
    except Exception as e:
        print("goals db:", e)
    names = {}
    p = f"{HOME}/.codex/session_index.jsonl"
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            try:
                o = json.loads(line, strict=False)
                names[o["id"]] = o["thread_name"]
            except Exception:
                pass
    return titles, meta, spawns, goals, names


def tool_summary(p):
    name = p.get("name") or p.get("type")
    raw = p.get("arguments") if "arguments" in p else p.get("input")
    desc = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
    try:
        a = json.loads(desc)
        if isinstance(a, dict):
            cmd = a.get("cmd") or a.get("command") or a.get("path") or a.get("query")
            if isinstance(cmd, list):
                cmd = " ".join(map(str, cmd))
            if cmd:
                desc = str(cmd)
    except Exception:
        pass
    if name == "apply_patch" or (isinstance(desc, str) and desc.startswith("*** Begin Patch")):
        files = re.findall(r"\*\*\* (?:Add|Update|Delete) File: (.+)", desc or "")
        return f"apply_patch: {', '.join(files[:8])}" + (" …" if len(files) > 8 else "")
    return f"{name}: {one_line(desc)}"


def parse_codex(path):
    s = dict(id=None, cwd=None, model=None, source=None, start=None, end=None, cli=None, git=None,
             forked_from=None, events=[], files=collections.Counter(), finals=[])
    seen, turn = set(), None

    def add(kind, when, text, turn_id):
        key = (turn_id, kind, text)
        if text and key not in seen:
            seen.add(key)
            s["events"].append((kind, when, text))

    with open(path, "rb") as f:
        for line in f:
            if b'"type":"compacted"' in line[:200] or b'"type":"token_count"' in line[:200]:
                continue
            try:
                o = json.loads(line, strict=False)
            except Exception:
                continue
            t, p, when = o.get("type"), o.get("payload") or {}, o.get("timestamp")
            if when:
                s["start"] = s["start"] or when
                s["end"] = when
            pt = p.get("type")
            if t == "session_meta" and not s["id"]:
                s.update(id=p.get("id"), cwd=p.get("cwd"), cli=p.get("cli_version"), git=p.get("git"),
                         source=p.get("source") if isinstance(p.get("source"), str) else json.dumps(p.get("source")),
                         forked_from=p.get("forked_from_id"))
            elif t == "turn_context":
                s["model"] = p.get("model") or s["model"]
                s["cwd"] = p.get("cwd") or s["cwd"]
            elif t == "event_msg" and pt in ("task_started", "turn_started"):
                turn = p.get("turn_id") or turn
            elif t == "event_msg" and pt in ("user_message", "agent_message"):
                add("user" if pt == "user_message" else "assistant", when, p.get("message") or "", turn)
            elif t == "event_msg" and pt == "item_completed":
                it = p.get("item") or {}
                kind = {"UserMessage": "user", "AgentMessage": "assistant"}.get(it.get("type"))
                if kind:
                    text = chr(10).join(c.get("text", "") for c in it.get("content") or [] if isinstance(c, dict))
                    add(kind, when, text, p.get("turn_id") or turn)
                elif it.get("type") == "FileChange" and isinstance(it.get("changes"), dict):
                    for k in it["changes"]:
                        s["files"][k] += 1
            elif t == "event_msg" and pt == "task_complete" and p.get("last_agent_message"):
                s["finals"].append((when, p["last_agent_message"]))
            elif t == "event_msg" and pt == "patch_apply_end":
                ch = p.get("changes") or {}
                for k in (ch.keys() if isinstance(ch, dict) else []):
                    s["files"][k] += 1
            elif t == "response_item" and pt in ("function_call", "custom_tool_call", "local_shell_call", "web_search_call"):
                s["events"].append(("tool", when, tool_summary(p)))
    return s


def render_transcript(s, title, extra):
    out = [f"# {title}", "", *extra, "", "---", ""]
    tools = []

    def flush():
        if tools:
            out.append("<details><summary>%d tool call(s)</summary>\n" % len(tools))
            out.extend(f"- `{t.replace('`', chr(39))}`" for t in tools)
            out.append("\n</details>\n")
            tools.clear()

    for kind, when, text in s["events"]:
        if kind == "tool":
            tools.append(text)
            continue
        flush()
        out.append(f"## {'User' if kind == 'user' else 'Assistant'} · {ts(when)}\n")
        out.append(text.strip() + "\n")
    flush()
    return "\n".join(out)


def render_resume(s, title, extra, rel_transcript, rel_resume):
    users = [e for e in s["events"] if e[0] == "user"]
    out = [f"# Resume brief: {title}", "", *extra, "",
           f"Full transcript: [{os.path.basename(rel_transcript)}]({os.path.relpath(rel_transcript, os.path.dirname(rel_resume))})", "",
           "## How to continue this work in Devin", "",
           "1. Open the original working directory (or its equivalent) shown above.",
           "2. Start Devin there and say: `Read <path to this file> and continue the task from where it stopped. "
           "Verify the current state of the repo before changing anything.`",
           "3. Devin cannot replay Codex's encrypted reasoning or compacted context; treat this brief + the transcript "
           "as the source of truth and re-check facts against the code.", ""]
    if users:
        out += ["## Original request", "", clip(users[0][2].strip(), 6000), ""]
    if len(users) > 1:
        out += ["## Follow-up requests (chronological)", ""]
        out += [f"{i}. ({ts(w)}) {one_line(t, 700)}" for i, (_, w, t) in enumerate(users[1:], 2)]
        out.append("")
    if s["files"]:
        out += ["## Files edited via apply_patch (most frequent first)", ""]
        out += [f"- `{k}` ×{v}" for k, v in s["files"].most_common(60)]
        out.append("")
    finals = s["finals"][-3:] or [(w, t) for k, w, t in s["events"] if k == "assistant"][-2:]
    if finals:
        out += ["## Last assistant conclusions", ""]
        for w, t in finals:
            out += [f"### {ts(w)}", "", clip(t.strip(), 8000), ""]
    return "\n".join(out)


def convert_codex():
    titles, meta, spawns, goals, names = codex_db()
    files = [os.path.join("/", l.strip()) for l in open(f"{EXPORT}/main_sessions.list") if l.strip()]
    rows = []
    for i, path in enumerate(files, 1):
        s = parse_codex(path)
        tid = s["id"] or os.path.basename(path)[-41:-6]
        title = names.get(tid) or titles.get(tid) or next((one_line(t, 80) for k, _, t in s["events"] if k == "user"), "untitled")
        day = (s["start"] or "0000-00-00")[:10]
        base = f"{day}_{tid[:8]}_{slug(title)}"
        rel_t = f"sessions/codex/transcripts/{day[:7]}/{base}.md"
        rel_r = f"sessions/codex/resume/{base}.md"
        g = goals.get(tid)
        extra = [f"- **Thread ID:** `{tid}`", f"- **Started / last event:** {ts(s['start'])} → {ts(s['end'])}",
                 f"- **Working dir:** `{s['cwd']}`", f"- **Model:** {s['model']}  ·  **Source:** {s['source']}  ·  **Codex CLI:** {s['cli']}",
                 f"- **Original rollout:** `{path}`", f"- **Subagents spawned:** {spawns.get(tid, 0)} (not exported)"]
        if s["git"]:
            extra.append(f"- **Git:** `{json.dumps(s['git'], ensure_ascii=False)}`")
        if s["forked_from"]:
            extra.append(f"- **Forked from:** `{s['forked_from']}`")
        if g:
            extra.append(f"- **Goal ({g.get('status')}):** {one_line(g.get('objective'), 500)}")
        write(f"{OUT}/{rel_t}", render_transcript(s, title, extra))
        write(f"{OUT}/{rel_r}", render_resume(s, title, extra, rel_t, rel_r))
        nuser = sum(1 for e in s["events"] if e[0] == "user")
        rows.append(dict(id=tid, title=title, start=s["start"], end=s["end"], cwd=s["cwd"], model=s["model"],
                         source=s["source"], user_turns=nuser, subagents=spawns.get(tid, 0),
                         files_edited=len(s["files"]), transcript=rel_t, resume=rel_r,
                         rollout_bytes=os.path.getsize(path)))
        print(f"[codex {i}/{len(files)}] {base}", flush=True)
    rows.sort(key=lambda r: r["end"] or "", reverse=True)
    with open(f"{OUT}/sessions/codex/index.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    md = ["# Codex threads (main threads only, newest first)", "",
          f"{len(rows)} threads. Subagent threads were intentionally excluded.", "",
          "| Last activity | Title | Working dir | User turns | Resume | Transcript |", "|---|---|---|---|---|---|"]
    for r in rows:
        t = r["title"].replace("|", "\\|")
        md.append(f"| {ts(r['end'])} | {t} | `{r['cwd']}` | {r['user_turns']} | [brief]({r['resume'][len('sessions/codex/'):]}) "
                  f"| [full]({r['transcript'][len('sessions/codex/'):]}) |")
    write(f"{OUT}/sessions/codex/INDEX.md", "\n".join(md) + "\n")
    if goals:
        write(f"{OUT}/sessions/codex/goals.md", "# Codex thread goals\n\n" + "\n".join(
            f"- `{k}` **{g.get('status')}** — {g.get('objective')}" for k, g in goals.items()) + "\n")
    hist = f"{HOME}/.codex/history.jsonl"
    if os.path.exists(hist):
        by = collections.OrderedDict()
        for line in open(hist, encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line, strict=False)
            except Exception:
                continue
            by.setdefault(o.get("session_id"), []).append((o.get("ts"), o.get("text", "")))
        md = ["# Codex prompt history (every prompt typed, grouped by session)", ""]
        for sid, items in by.items():
            md += [f"## `{sid}` — {names.get(sid) or titles.get(sid) or ''}", ""]
            md += [f"- ({ts(t)}) {one_line(x, 1500)}" for t, x in items]
            md.append("")
        write(f"{OUT}/history/codex-prompt-history.md", "\n".join(md))
    return rows


# --------------------------------------------------------------------------- Claude Code
def claude_text(content):
    if isinstance(content, str):
        return content, []
    texts, tools = [], []
    for c in content or []:
        if not isinstance(c, dict):
            continue
        if c.get("type") == "text":
            texts.append(c.get("text", ""))
        elif c.get("type") == "tool_use":
            inp = c.get("input") or {}
            d = inp.get("command") or inp.get("file_path") or inp.get("pattern") or inp.get("prompt") or json.dumps(inp, ensure_ascii=False)
            tools.append(f"{c.get('name')}: {one_line(str(d))}")
    return "\n".join(texts), tools


def convert_claude():
    rows = []
    for path in sorted(glob.glob(f"{HOME}/.claude/projects/*/*.jsonl")):
        proj = os.path.basename(os.path.dirname(path))
        sid = os.path.basename(path)[:-6]
        s = dict(events=[], files=collections.Counter(), finals=[], start=None, end=None, cwd=None, model=None)
        for line in open(path, "rb"):
            try:
                o = json.loads(line, strict=False)
            except Exception:
                continue
            if o.get("isSidechain") or o.get("type") not in ("user", "assistant"):
                continue
            when = o.get("timestamp")
            s["start"] = s["start"] or when
            s["end"] = when or s["end"]
            s["cwd"] = o.get("cwd") or s["cwd"]
            m = o.get("message") or {}
            s["model"] = m.get("model") or s["model"]
            text, tools = claude_text(m.get("content"))
            if o["type"] == "user" and isinstance(m.get("content"), list) and not text:
                continue
            if text.strip():
                s["events"].append((o["type"], when, text))
            s["events"] += [("tool", when, t) for t in tools]
            for t in tools:
                if t.startswith(("Edit:", "Write:", "MultiEdit:")):
                    s["files"][t.split(": ", 1)[1]] += 1
        if not s["events"]:
            continue
        title = next((one_line(t, 80) for k, _, t in s["events"] if k == "user"), "untitled")
        day = (s["start"] or "0000-00-00")[:10]
        base = f"{day}_{sid[:8]}_{slug(title)}"
        rel_t = f"sessions/claude/transcripts/{base}.md"
        rel_r = f"sessions/claude/resume/{base}.md"
        extra = [f"- **Claude Code session:** `{sid}` (project `{proj}`)", f"- **Started / last event:** {ts(s['start'])} → {ts(s['end'])}",
                 f"- **Working dir:** `{s['cwd']}`", f"- **Model:** {s['model']}", f"- **Original file:** `{path}`"]
        write(f"{OUT}/{rel_t}", render_transcript(s, title, extra))
        write(f"{OUT}/{rel_r}", render_resume(s, title, extra, rel_t, rel_r))
        rows.append(dict(id=sid, title=title, end=s["end"], cwd=s["cwd"], transcript=rel_t, resume=rel_r))
        print("[claude]", base, flush=True)
    md = ["# Claude Code sessions", "", "| Last activity | Title | Working dir | Resume | Transcript |", "|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: r["end"] or "", reverse=True):
        md.append(f"| {ts(r['end'])} | {r['title'].replace('|', '/')} | `{r['cwd']}` | [brief]({r['resume'][len('sessions/claude/'):]}) "
                  f"| [full]({r['transcript'][len('sessions/claude/'):]}) |")
    write(f"{OUT}/sessions/claude/INDEX.md", "\n".join(md) + "\n")
    hist = f"{HOME}/.claude/history.jsonl"
    if os.path.exists(hist):
        md = ["# Claude Code prompt history", ""]
        for line in open(hist, encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line, strict=False)
                md.append(f"- ({ts(o.get('timestamp'))}) `{o.get('project')}` — {one_line(o.get('display'), 1500)}")
            except Exception:
                pass
        write(f"{OUT}/history/claude-prompt-history.md", "\n".join(md) + "\n")
    return rows


# --------------------------------------------------------------------------- skills + rules
def copy_tree(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, symlinks=False, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".staging"))
    else:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)


def collect_skills_and_rules():
    report = []
    global_skills = {
        f"{HOME}/.codex/skills/ppu-cold-gemv-tuning": "codex",
        f"{HOME}/.codex/skills/ppu17-hopper-porting": "codex",
        f"{HOME}/.claude/skills/codex-collaboration": "claude",
        f"{HOME}/.claude/skills/ppu-cutlass-mixed-gemm": "claude",
        f"{HOME}/.claude/skills/ppu-ptx": "claude",
    }
    for src, origin in global_skills.items():
        if os.path.exists(src):
            name = os.path.basename(src)
            copy_tree(src, f"{OUT}/skills/{name}")
            fm = open(f"{OUT}/skills/{name}/SKILL.md", encoding="utf-8").read(600)
            report.append(f"- `skills/{name}` (from {origin}) frontmatter-ok={fm.startswith('---') and 'name:' in fm and 'description:' in fm}")
    seen = {}
    for p in [l.strip() for l in open(f"{EXPORT}/agent_docs.list") if l.strip()]:
        try:
            data = open(p, "rb").read()
        except Exception:
            continue
        h = hashlib.md5(data).hexdigest()
        if h in seen:
            seen[h][1].append(p)
            continue
        seen[h] = (p, [p])
    for h, (p, alls) in seen.items():
        if os.path.basename(p) == "SKILL.md" and "/skills/" in p:
            src = os.path.dirname(p)
            dst = f"{OUT}/project-rules{src}"
            copy_tree(src, dst)
        else:
            dst = f"{OUT}/project-rules{p}"
            copy_tree(p, dst)
    write(f"{OUT}/project-rules/INDEX.md", "# Project rule files and project skills (deduplicated)\n\n"
          "Each entry is stored at `project-rules/<original absolute path>`. Identical copies are listed under the kept one.\n\n" +
          "\n".join(f"- `{p}`" + ("".join(f"\n  - same as: `{x}`" for x in alls[1:])) for p, alls in seen.values()) + "\n")
    copy_tree(f"{HOME}/.codex/rules/default.rules", f"{OUT}/codex-config/default.rules")
    cfg = open(f"{HOME}/.codex/config.toml", encoding="utf-8").read()
    write(f"{OUT}/codex-config/config.toml", cfg)
    return report


if __name__ == "__main__":
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    sk = collect_skills_and_rules()
    codex = convert_codex()
    claude = convert_claude()
    known = sorted((k for k in KNOWN if len(k) >= 6), key=len, reverse=True)
    for root, _, fs in os.walk(OUT):
        for fn in fs:
            fp = os.path.join(root, fn)
            try:
                t = open(fp, encoding="utf-8").read()
            except Exception:
                continue
            t2 = t
            for k in known:
                t2 = t2.replace(k, "<REDACTED_KNOWN_SECRET>")
            if t2 != t:
                REDACTIONS["known-literal"] += 1
                open(fp, "w", encoding="utf-8").write(t2)
    known = sorted((k for k in KNOWN if len(k) >= 6), key=len, reverse=True)
    for root, _, fs in os.walk(OUT):
        for fn in fs:
            fp = os.path.join(root, fn)
            try:
                t = open(fp, encoding="utf-8").read()
            except Exception:
                continue
            t2 = t
            for k in known:
                t2 = t2.replace(k, "<REDACTED_KNOWN_SECRET>")
            if t2 != t:
                REDACTIONS["known-literal"] += 1
                open(fp, "w", encoding="utf-8").write(t2)
    summary = {"known_secret_count": len(known),"known_secret_count": len(known),"codex_threads": len(codex), "claude_sessions": len(claude), "skills": sk,
               "redactions": dict(REDACTIONS)}
    write(f"{OUT}/EXPORT_REPORT.json", json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
