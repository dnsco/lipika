#!/usr/bin/env python3
"""Tests for `lipika dangling-links`: a subdirectory is scanned, links resolve against the vault.

Run `python3 evals/dangling-links/test_dangling_links.py`. Exit 0 all pass, 1 any fail.

Drives `bin/lipika` against a fixture vault that is a git repository.
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


def run(*args, env=None):
    return subprocess.run([sys.executable, str(LIPIKA), "dangling-links", *args],
                          capture_output=True, text=True,
                          env=dict(os.environ, LIPIKA_TELEMETRY="0", **(env or {})))


def main():
    with tempfile.TemporaryDirectory() as d:
        vault = Path(d) / "vault"
        (vault / "workstreams" / "a").mkdir(parents=True)
        (vault / "workstreams" / "b").mkdir(parents=True)
        (vault / "workstreams" / "b" / "target.md").write_text("# target\n")
        (vault / "workstreams" / "a" / "doc.md").write_text("See [[target]].\n")
        subprocess.run(["git", "init", "-q", str(vault)], check=True)

        r = run(str(vault / "workstreams" / "a"))
        check("a link out of the scanned subdirectory resolves", r.returncode == 0,
              r.stdout[-300:])

        (vault / "workstreams" / "a" / "doc.md").write_text("See [[target]] and [[nowhere]].\n")
        r = run(str(vault / "workstreams" / "a"))
        check("a genuinely missing link from a subdirectory still exits 1",
              r.returncode == 1 and "nowhere" in r.stdout, r.stdout[-300:])
        check("findings are named relative to the vault root",
              "workstreams/a/doc.md" in r.stdout, r.stdout[-300:])

        r = run(env={"LIPIKA_VAULT": str(vault)})
        check("a bare call scans the configured vault", r.returncode == 1 and "nowhere" in r.stdout,
              (r.stdout + r.stderr)[-300:])

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
