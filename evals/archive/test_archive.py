#!/usr/bin/env python3
"""Tests for `workstreams/archive/`: where a finished thread goes, and how the tools read it.

Run `python3 evals/archive/test_archive.py`. Exit 0 all pass, 1 any fail.

These drive the CLI, `bin/lipika` in this tree, against a fixture vault, and import nothing from
`tools/`, so they survive a rewrite of the tools in another language.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"
TODAY = "2026-09-24"

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def lipika(vault, *args):
    env = dict(os.environ, LIPIKA_TELEMETRY="0")
    return subprocess.run([sys.executable, str(LIPIKA), *args, "--vault", str(vault)],
                          capture_output=True, text=True, env=env)


def thread(vault, rel, cites=None):
    """A thread with a routing note and one dump dated today, optionally citing a trace."""
    d = vault / "workstreams" / rel
    name = rel.split("/")[-1]
    (d / "dumps").mkdir(parents=True)
    (d / f"{name}.md").write_text(f"# The question {name} answers\n")
    body = f"# dump\n\n[[{cites}]]\n" if cites else "# dump\n"
    (d / "dumps" / f"{TODAY}-120000-{name}.md").write_text(body)


def names(stdout):
    return [line.split()[0] for line in stdout.splitlines() if line.startswith("  ")]


def main():
    with tempfile.TemporaryDirectory() as d:
        vault = Path(d)
        (vault / "reference").mkdir()
        (vault / "reference" / f"{TODAY}-shared-trace.md").write_text("# a trace\n")
        thread(vault, "2026-09-24-live", cites=f"{TODAY}-shared-trace")
        thread(vault, "archive/2026-08-21-old", cites=f"{TODAY}-shared-trace")
        thread(vault, "archive/2026-08-22-older", cites=f"{TODAY}-shared-trace")
        thread(vault, "parked/h2db")

        shown = names(lipika(vault, "threads").stdout)
        check("archived and parked threads are hidden by default", shown == ["2026-09-24-live"], shown)
        every = sorted(names(lipika(vault, "threads", "--all").stdout))
        check("--all lists each archived thread as archive/<name>, never one called `archive`",
              every == ["2026-09-24-live", "archive/2026-08-21-old", "archive/2026-08-22-older",
                        "parked/h2db"], every)

        r = lipika(vault, "architecture-candidates", "--today", TODAY)
        out = r.stdout + r.stderr
        check("an archived thread does not vote, however recent its documents",
              "archive/2026-08-21-old" not in out.split("live thread(s) voting:")[-1].split("\n")[0]
              and "CANDIDATES" not in out, out)
        check("architecture-candidates says an archived thread is not voting, and why",
              re.search(r"not voting · archive/2026-08-21-old\s+— archived", out) is not None, out)
        r = lipika(vault, "architecture-candidates", "--today", TODAY, "--all-threads")
        out = r.stdout + r.stderr
        check("with --all-threads, archived threads vote as themselves, not as `archive`",
              "cited from 3 threads" in out and "archive/2026-08-21-old" in out, out)

    old_rule = re.compile(r"nothing is archived|nothing is moved|don't move documents|records never move",
                          re.I)
    stale = []
    for rel in ("skills", "agents", "templates", "tools", "design", "CLAUDE.md", "README.md"):
        p = REPO / rel
        for f in ([p] if p.is_file() else sorted(p.rglob("*"))):
            if not f.is_file() or f.suffix not in (".md", ".py", ".template"):
                continue
            for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                # §8's retired-roles table records what the librarian did and why it went. History.
                if line.startswith("| the `librarian` |"):
                    continue
                if old_rule.search(line):
                    stale.append(f"{f.relative_to(REPO)}:{n}")
    check("no definition, template, tool or design doc still states the no-archive rule", not stale, stale)

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
