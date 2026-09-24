#!/usr/bin/env python3
"""Graders for `lipika perf`: the transcript parser, skill spans, and flagging.

Written before the code they grade, so they can be wrong. Run: `python3 evals/perf/test_perf.py`
(also what `lipika perf --self-test` runs). Exit 0 all pass, 1 any fail.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))

T0 = 1_790_000_000  # an arbitrary epoch second


def ts(s):
    import datetime
    return datetime.datetime.fromtimestamp(T0 + s, datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def rec(t, kind, content, **kw):
    r = {"type": kind, "timestamp": ts(t), "sessionId": "S1", "cwd": "/w/proj",
         "message": {"role": kind, "content": content}}
    r.update(kw)
    return r


def use(uid, name, inp):
    return [{"type": "tool_use", "id": uid, "name": name, "input": inp}]


def result(uid):
    return [{"type": "tool_result", "tool_use_id": uid, "content": "ok"}]


# A context-dump that runs to the end of its turn, then a pickup that ends by asking.
FIXTURE = [
    rec(0, "user", "dump context please", origin={"kind": "human"}),
    rec(2, "assistant", use("u1", "Skill", {"skill": "lipika:context-dump"})),
    rec(2.1, "user", result("u1")),
    rec(2.2, "user", [{"type": "text", "text": "skill body"}], isMeta=True),
    rec(5, "assistant", use("u2", "Bash", {"command": 'cd "$(lipika vault-config path)" && lipika pass-log start x'})),
    rec(6, "user", result("u2")),
    rec(8, "assistant", use("u3", "Bash", {"command": "git status"})),
    rec(9, "user", result("u3")),
    rec(10, "assistant", use("u4", "Agent", {"subagent_type": "lipika:tracer", "prompt": "p"})),
    rec(40, "user", result("u4")),
    rec(50, "assistant", [{"type": "text", "text": "done"}]),
    rec(300, "user", "thanks, now pick up", origin={"kind": "human"}),
    rec(301, "assistant", use("u5", "Skill", {"skill": "lipika:pickup"})),
    rec(301.1, "user", result("u5")),
    rec(320, "assistant", use("u6", "AskUserQuestion", {"questions": []})),
    rec(500, "user", result("u6")),
    rec(505, "assistant", [{"type": "text", "text": "planning"}]),
    # A skill typed as a slash command: no Skill call, a human prompt naming it, then its body.
    rec(600, "user", "<command-message>lipika:context-dump</command-message>\n"
        "<command-name>/lipika:context-dump</command-name>", origin={"kind": "human"}),
    rec(600, "user", [{"type": "text", "text": "Base directory for this skill: "
        "/Users/x/.claude/plugins/cache/lipika/lipika/0.3.5/skills/context-dump\n\n# body"}],
        isMeta=True),
    rec(660, "assistant", [{"type": "text", "text": "dumped"}]),
]

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def write_fixture(d):
    p = os.path.join(d, "S1.jsonl")
    with open(p, "w") as fh:
        for r in FIXTURE:
            fh.write(json.dumps(r) + "\n")
    return p


def main():
    import _perf_parse as pp
    import perf as pr

    with tempfile.TemporaryDirectory() as d:
        path = write_fixture(d)
        events, end = pp.transcript_events(path, 0)
        check("parser returns the file's end as its new offset", end == os.path.getsize(path))

        # The cache contract: resuming from any line boundary yields the same events.
        with open(path, "rb") as fh:
            data = fh.read()
        cut = data.index(b"\n", len(data) // 2) + 1
        a, mid = pp.transcript_events(path, 0, stop=cut)
        b, _ = pp.transcript_events(path, mid)
        check("resume from a stored offset equals a full parse", a + b == events,
              f"{len(a)}+{len(b)} vs {len(events)}")
        check("a stored offset past the end of a shrunk file re-parses from 0",
              pp.transcript_events(path, len(data) + 999)[0] == events)

        spans = pp.skill_spans(events)
        check("three skill spans found, one of them typed as a slash command", len(spans) == 3,
              repr([s.get("skill") for s in spans]))
        if len(spans) == 3:
            cd, pk, sl = spans
            check("a slash command starts a span at the prompt, named without the slash",
                  sl["skill"] == "lipika:context-dump" and abs(sl["start"] - (T0 + 600)) < 0.01
                  and abs(sl["active_s"] - 60) < 0.01, (sl["skill"], sl["active_s"]))
            check("the skill body's base directory gives the version that ran",
                  sl["version"] == "0.3.5", sl.get("version"))
            check("a span with no base directory has version unknown", cd["version"] == "unknown",
                  cd.get("version"))
            check("span starts at the Skill call", abs(cd["start"] - (T0 + 2)) < 0.01)
            check("a skill that finishes its turn ends at the last assistant record",
                  abs(cd["end"] - (T0 + 50)) < 0.01 and cd["ended_by"] == "turn_end",
                  f"end={cd['end'] - T0} by={cd['ended_by']}")
            check("project is the transcript's cwd", cd["project"] == "/w/proj")
            check("lipika time is the Bash call that ran lipika", abs(cd["lipika_s"] - 1) < 0.01,
                  cd["lipika_s"])
            check("other tool time excludes lipika and agents", abs(cd["other_tools_s"] - 1) < 0.01,
                  cd["other_tools_s"])
            check("sub-agent time is the Agent call", abs(cd["subagent_s"] - 30) < 0.01,
                  cd["subagent_s"])
            check("model time is the remainder", abs(cd["model_s"] - (48 - 32)) < 0.01, cd["model_s"])
            check("dispatches are counted", cd["dispatches"] == 1)
            check("a skill that hands to the owner ends at the question, not the answer",
                  abs(pk["end"] - (T0 + 320)) < 0.01 and pk["ended_by"] == "ask",
                  f"end={pk['end'] - T0} by={pk['ended_by']}")
            check("the owner's wait is reported apart, not as skill time",
                  abs(pk["wait_s"] - 180) < 0.01 and abs(pk["active_s"] - 19) < 0.01,
                  f"wait={pk['wait_s']} active={pk['active_s']}")

    # Flagging, after rue: trailing-window median, k x dispersion, both directions.
    steady = [100, 104, 97, 101, 99, 103, 98, 102, 100, 101]
    marks = pr.flag(steady + [400], window=8, k=3)
    check("red: a 4x outlier after a steady window is flagged", marks[-1] == "flag", marks[-1])
    marks = pr.flag(steady + [20], window=8, k=3)
    check("red: a speedup is flagged too", marks[-1] == "flag", marks[-1])
    marks = pr.flag(steady + [106], window=8, k=3)
    check("green: a point inside the noise is not flagged", marks[-1] == "ok", marks[-1])
    marks = pr.flag([100, 300], window=8, k=3)
    check("a short series says not enough history, never ok",
          marks == ["history", "history"], marks)

    # Projects are repos: two repos never share a series, and a worktree folds into its repo.
    wt = "/nonexistent/workspace/onlineDataAnalysis/.claude/worktrees/mxnet-removal-0c24e9"
    check("a worktree cwd resolves to its repo", pr.project_key(wt) == "onlineDataAnalysis",
          pr.project_key(wt))
    check("a plain cwd resolves to its directory name",
          pr.project_key("/nonexistent/workspace/agentomatic") == "agentomatic")
    here = pr.project_key(os.path.dirname(os.path.abspath(__file__)))
    check("a cwd inside a git checkout resolves to its remote's repo name", here == "lipika", here)
    a = {"skill": "lipika:pickup", "project": "/n/workspace/agentomatic", "start": 1}
    b = {"skill": "lipika:pickup", "project": "/n/workspace/onlineDataAnalysis", "start": 2}
    groups = pr.group_skills([a, b])
    check("one skill in two projects is two series", len(groups) == 2, sorted(groups))

    # The page: one project at a time, chosen from a dropdown, lipika selected by default.
    import re
    span = {"skill": "lipika:pickup", "session": "S", "project": "/n/workspace/agentomatic",
            "start": T0, "end": T0 + 30, "active_s": 30, "ended_by": "ask", "wait_s": 0,
            "version": "0.5.0", "model_s": 30, "subagent_s": 0, "other_tools_s": 0, "lipika_s": 0}
    ev = {"case": "c", "t": T0, "s": 100, "cost": 1, "turns": 3, "score": 1, "version": "0.5.0"}
    home = dict(span, project="/n/workspace/lipika")
    page = pr.render([span, home], [], [], [ev], {}, 30)
    opts = re.findall(r'<option value="([^"]+)"( selected)?>', page)
    check("the page has a project dropdown listing every project",
          sorted(o for o, _ in opts) == ["agentomatic", "lipika", "lipika-evals"], opts)
    check("eval runs are their own project, not lipika",
          re.search(r'data-project="lipika-evals"><h2>eval c<', page) is not None)
    check("lipika is selected by default", ("lipika", " selected") in opts, opts)
    sections = re.findall(r'<section class="panel"[^>]*>', page)
    check("every panel carries its project",
          sections and all('data-project="' in x for x in sections), sections[:3])

    check("a record without version renders as unknown", pr.version_of({}) == "unknown")
    check("a record without session has project unknown", pr.project_of({}, {}) == "unknown")

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
