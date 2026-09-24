#!/usr/bin/env python3
"""Tests for a thread's `gotchas.md`: where an always-true warning goes instead of the orientation.

Run `python3 evals/gotchas/test_gotchas.py`. Exit 0 all pass, 1 any fail.

These drive the CLI, `bin/lipika` in this tree, against a fixture vault, and import nothing from
`tools/`, so they survive a rewrite of the tools in another language.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"

ORIENTATION = """---
type: orientation
---

## Needs the owner

- **[ESCALATED] Do not merge a PR unless he says so in that turn.** → dies never · as-of 2026-09-17

## Live items

### Tools

- **[LANDMINE] The `Edit` tool needs its own `Read`.** → dies never · as-of 2026-09-15
- **[OPEN Q] `#4412` has not merged.** → dies when `#4412` merges or closes · as-of 2026-09-21
- **[DEAD END] Invalidating on read.** Ruled 2026-09-19: it widens the window.
"""

EXISTING = "---\ntype: gotchas\n---\n\n# Warnings that stay true\n\n- **[LANDMINE] Written by hand.** → dies never\n"

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def lipika(vault, *args):
    env = dict(os.environ, LIPIKA_TELEMETRY="0")
    return subprocess.run([sys.executable, str(LIPIKA), *args, "--vault", str(vault)],
                          capture_output=True, text=True, env=env)


def read(p):
    return p.read_text() if p.exists() else ""


def fixture(d, gotchas=None):
    vault = Path(d)
    ws = vault / "workstreams" / "2026-09-20-t"
    (ws / "orientation").mkdir(parents=True)
    (ws / "orientation" / "2026-09-21-140000.md").write_text(ORIENTATION)
    if gotchas is not None:
        (ws / "gotchas.md").write_text(gotchas)
    return vault, ws


def main():
    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d)
        r = lipika(vault, "orientation-carry", "2026-09-20-t")
        check("without the flag, the message names the thread's gotchas.md",
              "gotchas.md" in r.stderr, r.stderr)
        check("the message no longer sends warnings to GOTCHAS.md or CLAUDE.md",
              "GOTCHAS.md" not in r.stderr and "CLAUDE.md" not in r.stderr, r.stderr)
        check("without the flag, nothing is written", not (ws / "gotchas.md").exists())

        r = lipika(vault, "orientation-carry", "2026-09-20-t", "--append-gotchas")
        g = read(ws / "gotchas.md")
        check("--append-gotchas exits 0: the always-true items are handled", r.returncode == 0,
              f"exit {r.returncode}\n{r.stderr}")
        check("the always-true item is appended verbatim",
              "- **[LANDMINE] The `Edit` tool needs its own `Read`.** → dies never · as-of 2026-09-15" in g, g)
        check("the appended item cites the orientation it came from", "2026-09-21-140000" in g, g)
        check("the always-true item stays out of the carry", "needs its own `Read`" not in r.stdout)
        check("an ESCALATED item is carried, not moved to gotchas",
              "Do not merge a PR" in r.stdout and "Do not merge a PR" not in g)
        check("a DEAD END is carried, not moved to gotchas",
              "[DEAD END]" in r.stdout and "[DEAD END]" not in g)
        check("an item that can die is carried, not moved", "#4412" in r.stdout and "#4412" not in g)

        before = g
        lipika(vault, "orientation-carry", "2026-09-20-t", "--append-gotchas")
        after = read(ws / "gotchas.md")
        check("a second run appends nothing already there", bool(before) and after == before, after)

    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d, gotchas=EXISTING)
        lipika(vault, "orientation-carry", "2026-09-20-t", "--append-gotchas")
        g = read(ws / "gotchas.md")
        check("the bytes already in gotchas.md are unchanged, and the new item follows them",
              g.startswith(EXISTING) and "needs its own `Read`" in g[len(EXISTING):], g)

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
