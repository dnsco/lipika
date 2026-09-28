#!/usr/bin/env python3
"""Tests for `lipika doctor`: it reports a tree holding commits origin/main does not.

Run `python3 evals/doctor/test_doctor.py`. Exit 0 all pass, 1 any fail.

A directory-source marketplace runs the checkout, so unmerged commits there are live. Drives
`bin/lipika doctor --tree` against a fixture git repo whose `origin/main` is set by `update-ref`.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def git(tree, *args):
    subprocess.run(["git", "-C", str(tree), *args], check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))


def doctor(tree):
    return subprocess.run([sys.executable, str(LIPIKA), "doctor", "--tree", str(tree)],
                          capture_output=True, text=True,
                          env=dict(os.environ, LIPIKA_TELEMETRY="0")).stdout


def main():
    with tempfile.TemporaryDirectory() as d:
        tree = Path(d) / "tree"
        tree.mkdir()
        git(tree, "init", "-q", "-b", "main")
        git(tree, "commit", "-q", "--allow-empty", "-m", "one")
        git(tree, "update-ref", "refs/remotes/origin/main", "HEAD")
        out = doctor(tree)
        check("a tree at origin/main reports no unmerged commits", "not on origin/main" not in out,
              out)

        git(tree, "commit", "-q", "--allow-empty", "-m", "two")
        out = doctor(tree)
        check("a tree ahead of origin/main says how many commits it holds",
              "1 commit(s) not on origin/main" in out, out)

    print(f"\n{'FAIL' if failures else 'ok'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
