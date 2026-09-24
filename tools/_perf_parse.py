"""Resumable parsers behind `lipika perf`.

Cache contract: every parser is `(path, offset, stop=None) -> (rows, new_offset)`, reads whole
lines only, and restarts at 0 when the offset is past the end of the file. Rows are line-local, so
rows[0:k] + rows[k:end] == rows[0:end], and a store can keep `cursor(path, offset)` and parse only
new bytes. Spans are not line-local, so they are derived from events by `skill_spans`; a store
keeps the events.

A skill span, from `~/.claude/projects/<project>/<session>.jsonl`:
- starts at a `Skill` tool_use, or at a human prompt naming a slash command;
- ends at the first of: `ask` (AskUserQuestion / ExitPlanMode; the wait for the answer is
  `wait_s`, not skill time), `turn_end` (the last assistant record before the next human prompt),
  `next_skill`, `eof`;
- takes its version from the skill body's base directory, `.../plugins/cache/<m>/<p>/<version>/`.

`attributionSkill` is not a boundary: it stays set after the skill finishes (a pickup was still
attributed 14 minutes on, 2026-09-24).

Composition: `lipika_s` (Bash calls running `lipika`), `subagent_s` (Agent/Task),
`other_tools_s`, and `model_s`, the active time outside every tool interval. A background dispatch
returns at once, so its child's work is not in `subagent_s`.
"""

import datetime
import json
import os
import re

ASK = {"AskUserQuestion", "ExitPlanMode"}
AGENT = {"Agent", "Task"}
LIPIKA = re.compile(r"(?:^|[\s;&|(`$\"'])lipika\s")
COMMAND = re.compile(r"<command-name>/([^<\s]+)</command-name>")
BASE_DIR = re.compile(r"Base directory for this skill: (\S+)")
CACHED = re.compile(r"/plugins/cache/[^/]+/[^/]+/([^/]+)/skills/")


def epoch(ts):
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def read_lines(path, offset=0, stop=None):
    """(list of decoded JSON objects, new_offset). Whole lines only; a bad line is skipped."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return [], 0
    if offset > size:
        offset = 0
    end = size if stop is None else min(stop, size)
    with open(path, "rb") as fh:
        fh.seek(offset)
        data = fh.read(max(0, end - offset))
    cut = data.rfind(b"\n") + 1
    out = []
    for line in data[:cut].splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out, offset + cut


def jsonl_rows(path, offset=0, stop=None):
    """Telemetry and pass-log: each line already is a row."""
    return read_lines(path, offset, stop)


def is_human(r, content):
    if r.get("isMeta"):
        return False
    origin = r.get("origin")
    if isinstance(origin, dict):
        return origin.get("kind") == "human"
    return isinstance(content, str) and not content.lstrip().startswith("<")


def transcript_events(path, offset=0, stop=None):
    """Events from one Claude transcript: human, asst, use, result. Sidechains are skipped."""
    lines, new = read_lines(path, offset, stop)
    out = []
    for r in lines:
        if r.get("isSidechain") or r.get("type") not in ("user", "assistant"):
            continue
        t = epoch(r.get("timestamp"))
        if t is None:
            continue
        base = {"t": t, "s": r.get("sessionId"), "cwd": r.get("cwd")}
        content = (r.get("message") or {}).get("content")
        if r["type"] == "user":
            if is_human(r, content):
                out.append({**base, "k": "human"})
                m = COMMAND.search(content if isinstance(content, str) else json.dumps(content))
                if m:
                    out.append({**base, "k": "use", "id": None, "name": "Skill", "skill": m.group(1)})
            elif isinstance(content, list):
                if r.get("isMeta"):
                    m = BASE_DIR.search(json.dumps(content))
                    if m:
                        v = CACHED.search(m.group(1))
                        out.append({**base, "k": "base", "version": v.group(1) if v else "unversioned"})
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        out.append({**base, "k": "result", "id": b.get("tool_use_id")})
            continue
        out.append({**base, "k": "asst"})
        for b in content if isinstance(content, list) else []:
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            name, inp = b.get("name"), b.get("input") or {}
            ev = {**base, "k": "use", "id": b.get("id"), "name": name}
            if name == "Skill":
                ev["skill"] = inp.get("skill")
            elif name == "Bash" and LIPIKA.search(inp.get("command") or ""):
                ev["lipika"] = True
            out.append(ev)
    return out, new


def union(intervals):
    total, cur = 0.0, None
    for a, b in sorted(intervals):
        if cur is None or a > cur[1]:
            if cur:
                total += cur[1] - cur[0]
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    return total + (cur[1] - cur[0] if cur else 0.0)


def skill_spans(events):
    results = {e["id"]: e["t"] for e in events if e["k"] == "result"}
    spans, cur, last_asst = [], None, None

    def close(end, by, wait=0.0):
        end = max(end if end is not None else cur["start"], cur["start"])
        iv = {"lipika": [], "agent": [], "other": []}
        for u in cur["uses"]:
            done = min(results.get(u["id"], end), end)
            if done <= u["t"]:
                continue
            cls = "lipika" if u.get("lipika") else "agent" if u["name"] in AGENT else "other"
            iv[cls].append((u["t"], done))
        active = end - cur["start"]
        spans.append({
            "skill": cur["skill"], "session": cur["s"], "project": cur["cwd"],
            "start": cur["start"], "end": end, "active_s": round(active, 3),
            "ended_by": by, "wait_s": round(wait, 3),
            "lipika_s": round(union(iv["lipika"]), 3),
            "subagent_s": round(union(iv["agent"]), 3),
            "other_tools_s": round(union(iv["other"]), 3),
            "model_s": round(max(0.0, active - union(iv["lipika"] + iv["agent"] + iv["other"])), 3),
            "version": cur["version"],
            "tool_calls": len(cur["uses"]),
            "dispatches": sum(1 for u in cur["uses"] if u["name"] in AGENT),
        })

    for e in events:
        k = e["k"]
        if k == "asst":
            last_asst = e["t"]
        elif k == "human":
            if cur:
                close(last_asst, "turn_end")
                cur = None
        elif k == "use" and e["name"] == "Skill":
            if cur:
                close(last_asst, "next_skill")
            cur = {"skill": e.get("skill") or "?", "start": e["t"], "s": e["s"], "cwd": e["cwd"],
                   "uses": [], "version": "unknown"}
        elif k == "base" and cur and cur["version"] == "unknown":
            cur["version"] = e["version"]
        elif k == "use" and e["name"] in ASK:
            if cur:
                close(e["t"], "ask", max(0.0, results.get(e["id"], e["t"]) - e["t"]))
                cur = None
        elif k == "use" and cur:
            cur["uses"].append(e)
    if cur:
        close(last_asst, "eof")
    return spans
