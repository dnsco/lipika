#!/usr/bin/env python3
"""Tests for `lipika handoff-prompt`: a deployed handoff carries the gate and picks no graders.

Run `python3 evals/handoff-prompt/test_handoff_prompt.py`. Exit 0 all pass, 1 any fail.

Graders are not tied to threads (owner, 2026-09-28), so an eval document naming the thread in
`about:` must not appear. Drives `bin/lipika` against a fixture vault, tree and plugin cache.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"
THREAD = "2026-01-01-thread"

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def main():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        vault = d / "vault"
        o = vault / "workstreams" / THREAD / "orientation"
        o.mkdir(parents=True)
        (o / "2026-01-01-000000.md").write_text("## Where this is\nx\n")
        (vault / "sources" / "evals").mkdir(parents=True)
        (vault / "sources" / "evals" / "2026-01-01-grader.md").write_text(
            f'---\nabout: "[[{THREAD}]]"\n---\n# a grader\n')

        tree = d / "tree"
        for name in ("skills", "agents", "tools", "bin"):
            (tree / name).mkdir(parents=True)
            (tree / name / "f").write_text(name)
        (tree / ".claude-plugin").mkdir()
        (tree / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": "9.9.9"}))
        cache = d / "cache"
        shutil.copytree(tree, cache / "9.9.9")

        r = subprocess.run([sys.executable, str(LIPIKA), "handoff-prompt", THREAD, "--deployed",
                            "--vault", str(vault), "--tree", str(tree), "--cache", str(cache)],
                           capture_output=True, text=True,
                           env=dict(os.environ, LIPIKA_TELEMETRY="0"))
        check("--deployed exits 0 when the tree is what is installed", r.returncode == 0, r.stderr)
        check("--deployed carries the gate command", "lipika doctor" in r.stdout, r.stdout)
        check("--deployed names the installed version", "installed 9.9.9" in r.stdout, r.stdout)
        check("no grader is chosen by thread", "2026-01-01-grader" not in r.stdout, r.stdout)

    print(f"\n{'FAIL' if failures else 'ok'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
