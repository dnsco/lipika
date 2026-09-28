#!/usr/bin/env python3
"""Tests over the shipped definitions: what they tell an agent to run must run.

Run `python3 evals/definitions/test_definitions.py`. Exit 0 all pass, 1 any fail.

`--kind` values are checked by invoking `bin/lipika pass-log start` against a scratch log, so the
test follows the tool rather than a copy of its kind list.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"
DEFS = sorted([*REPO.glob("agents/*.md"), *REPO.glob("skills/*/SKILL.md")])
KIND = re.compile(r"lipika pass-log start\b[^\n`]*?--kind\s+([A-Za-z_-]+)")

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def kind_accepted(kind, log):
    env = dict(os.environ, LIPIKA_TELEMETRY="0")
    r = subprocess.run([sys.executable, str(LIPIKA), "pass-log", "--log", str(log), "start", "test",
                        "probe", "--kind", kind], capture_output=True, text=True, env=env)
    return r.returncode == 0, r.stderr.strip()


def main():
    kinds = {}
    for p in DEFS:
        for k in KIND.findall(p.read_text()):
            kinds.setdefault(k, []).append(str(p.relative_to(REPO)))
    check("the definitions name at least one --kind", bool(kinds))
    with tempfile.TemporaryDirectory() as d:
        for k, where in sorted(kinds.items()):
            ok, err = kind_accepted(k, Path(d) / f"{k}.jsonl")
            check(f"pass-log accepts --kind {k} ({', '.join(where)})", ok, err)

    for p in DEFS:
        t = p.read_text()
        rel = p.relative_to(REPO)
        check(f"{rel} does not dispatch the retired scout", "lipika:scout" not in t)
        check(f"{rel} does not call the retired scope-recon", "scope-recon" not in t)
    check("agents/scout.md is gone", not (REPO / "agents" / "scout.md").exists())
    check("skills/spin-out/SKILL.md exists", (REPO / "skills" / "spin-out" / "SKILL.md").exists())

    spin = REPO / "skills" / "spin-out" / "SKILL.md"
    t = spin.read_text() if spin.exists() else ""
    check("spin-out opens a pass for the run and one for prior-art reading",
          "pass-log start spin-out" in t and "pass-log start prior-art" in t)
    nested = sorted(set(re.findall(r"/lipika:([a-z-]+)", t)) - {"spin-out"})
    check("spin-out names no other /lipika: skill -- a nested Skill call ends its perf span",
          not nested, ", ".join(nested))

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
