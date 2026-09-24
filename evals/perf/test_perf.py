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
    import perf_report as pr

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
        check("two skill spans found", len(spans) == 2, repr([s.get("skill") for s in spans]))
        if len(spans) == 2:
            cd, pk = spans
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

    check("a record without version renders as unknown", pr.version_of({}) == "unknown")
    check("a record without session has project unknown", pr.project_of({}, {}) == "unknown")

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
