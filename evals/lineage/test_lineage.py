#!/usr/bin/env python3
"""Tests for split lineage: `lipika lineage`, and the parent resolvers that read `from:`.

Run `python3 evals/lineage/test_lineage.py`. Exit 0 all pass, 1 any fail.

A project is the chain of threads its splits produced. Each child's orientation names its parent
in `from:`. The epic tier used to tie a project's threads together, and it was dropped
2026-09-25, so this chain is now the only link.

These tests drive `bin/lipika` in this tree against a fixture vault. They import nothing from
tools/, so they test the CLI a definition calls.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"

ROOT = "2026-01-01-root"            # archived: the owner ruled it finished
CHILD = "2026-02-01-child"          # live, split from ROOT
GRAND = "2026-03-01-grand"          # live, split from CHILD
PARKED = "2026-03-05-parked-kid"    # parked, split from CHILD
ALONE = "2026-03-02-alone"          # live, no parent, no children

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def lipika(vault, *args, env=None):
    return subprocess.run([sys.executable, str(LIPIKA), *args, "--vault", str(vault)],
                          capture_output=True, text=True,
                          env=dict(os.environ, LIPIKA_TELEMETRY="0", **(env or {})))


def orientation(frm=None, body="## Live items\n- [OPEN Q] **a thing** → dies when done · as-of 2026-03-01\n"):
    fm = "---\ntype: orientation\nstatus: current\ndate: 2026-03-01\n"
    if frm:
        fm += f'from: "[[{frm}]]"\n'
    return fm + "---\n\n## Where this is\nx\n\n" + body


def thread(vault, rel, question, orients):
    d = vault / "workstreams" / rel
    name = Path(rel).name
    (d / "orientation").mkdir(parents=True)
    (d / f"{name}.md").write_text(f"# {question}\n")
    for stamp, text in orients:
        (d / "orientation" / f"{stamp}.md").write_text(text)
    return d


def fixture(d):
    vault = Path(d)
    thread(vault, f"archive/{ROOT}", "What was the first question?",
           [("2026-01-01-100000", orientation())])
    # The child's LATER orientation names a different parent. The oldest one that declares a
    # parent is the answer, because a thread's parentage does not change.
    thread(vault, CHILD, "What did the split ask?",
           [("2026-02-01-100000", orientation(ROOT)),
            ("2026-02-02-100000", orientation(ALONE))])
    thread(vault, GRAND, "What did the second split ask?",
           [("2026-03-01-100000", orientation(CHILD))])
    thread(vault, f"parked/{PARKED}", "What was set aside?",
           [("2026-03-05-100000", orientation(CHILD))])
    thread(vault, ALONE, "What stands alone?", [("2026-03-02-100000", orientation())])
    return vault


def main():
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)

        # The whole project, as JSON: one root, and every descendant under it.
        r = lipika(vault, "lineage", "--json")
        check("`lineage --json` exits 0", r.returncode == 0, f"exit {r.returncode}\n{r.stderr}")
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            data = {}
        parents = data.get("parents", {})
        check("an archived parent resolves", parents.get(CHILD) == f"archive/{ROOT}", parents)
        check("a live thread's parent resolves", parents.get(GRAND) == CHILD, parents)
        check("a parked thread's parent resolves", parents.get(f"parked/{PARKED}") == CHILD, parents)
        check("the OLDEST orientation's `from:` wins over a later one", parents.get(CHILD) != ALONE,
              parents)
        check("a thread with no `from:` has no parent", ALONE not in parents and
              f"archive/{ROOT}" not in parents, parents)
        projects = data.get("projects", [])
        roots = [p.get("root") for p in projects]
        check("the chain is one project rooted at the archived thread", roots.count(f"archive/{ROOT}") == 1,
              projects)
        proj = next((p for p in projects if p.get("root") == f"archive/{ROOT}"), {})
        check("the project holds every descendant, parked included",
              set(proj.get("threads", [])) == {f"archive/{ROOT}", CHILD, GRAND, f"parked/{PARKED}"}, proj)
        check("a thread with no parent and no children is not a project", ALONE not in roots, roots)

        # One thread: the chain up to its root, and its descendants.
        r = lipika(vault, "lineage", GRAND)
        check("`lineage <thread>` exits 0", r.returncode == 0, f"exit {r.returncode}\n{r.stderr}")
        out = r.stdout
        check("it names the root, the parent and the thread, oldest first",
              0 <= out.find(ROOT) < out.find(CHILD) < out.find(GRAND), out)
        check("it prints each thread's question", "What was the first question?" in out, out)

        r = lipika(vault, "lineage", "2026-09-09-nope")
        check("an unknown thread is exit 5", r.returncode == 5, f"exit {r.returncode}\n{r.stderr}")

        # The tree view, human-readable.
        r = lipika(vault, "lineage")
        check("`lineage` with no thread prints the project tree",
              r.returncode == 0 and ROOT in r.stdout and GRAND in r.stdout and ALONE not in r.stdout,
              r.stdout)

        # orientation-audit follows `from:` into archive/ on a thread's first orientation.
        r = lipika(vault, "orientation-audit", f"workstreams/{GRAND}")
        check("orientation-audit compares a first orientation against its parent",
              r.returncode in (0, 1) and "NOT CHECKED" not in r.stdout, f"exit {r.returncode}\n{r.stdout}")

    # A split from an ARCHIVED parent is still checked.
    with tempfile.TemporaryDirectory() as d:
        vault = Path(d)
        thread(vault, f"archive/{ROOT}", "What was the first question?",
               [("2026-01-01-100000", orientation())])
        thread(vault, CHILD, "What did the split ask?", [("2026-02-01-100000", orientation(ROOT))])
        r = lipika(vault, "orientation-audit", f"workstreams/{CHILD}")
        check("orientation-audit resolves a parent in archive/",
              r.returncode in (0, 1) and "NOT CHECKED" not in r.stdout, f"exit {r.returncode}\n{r.stdout}")

    # A new vault has no epics/ tier.
    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "home"
        home.mkdir()
        target = Path(d) / "newvault"
        r = subprocess.run([sys.executable, str(LIPIKA), "init", str(target), "--no-git"],
                           capture_output=True, text=True,
                           env=dict(os.environ, HOME=str(home), LIPIKA_TELEMETRY="0"))
        check("`lipika init` exits 0", r.returncode == 0, f"exit {r.returncode}\n{r.stderr}")
        check("`lipika init` creates no epics/", not (target / "epics").exists(),
              sorted(p.name for p in target.iterdir()) if target.exists() else "no target")
        claude = (target / "CLAUDE.md").read_text() if (target / "CLAUDE.md").exists() else ""
        check("the seeded CLAUDE.md does not teach an epic tier", "epics/" not in claude)

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
