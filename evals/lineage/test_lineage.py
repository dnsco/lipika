#!/usr/bin/env python3
"""Tests for split lineage: `lipika lineage`, and the parent resolvers that read `from:`.

Run `python3 evals/lineage/test_lineage.py`. Exit 0 all pass, 1 any fail.

A split lineage is the graph of threads that splits and re-partitions produced. Each thread's first
orientation names its parents in `from:` -- one after a split, several after curate re-partitions
threads along new lines. It is the only link between threads.

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
MERGED = "2026-04-01-merged"        # re-partitioned from GRAND and OTHER, block-list `from:`
OTHER = "2026-03-10-other"          # live, no parent; one of MERGED's two parents
INLINE = "2026-04-02-inline"        # re-partitioned from OTHER and ALONE2, inline-list `from:`
ALONE2 = "2026-03-11-alone2"

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def lipika(vault, *args, env=None):
    return subprocess.run([sys.executable, str(LIPIKA), *args, "--vault", str(vault)],
                          capture_output=True, text=True,
                          env=dict(os.environ, LIPIKA_TELEMETRY="0", **(env or {})))


def orientation(frm=None, body="## Live items\n- [OPEN Q] **a thing** → dies when done · as-of 2026-03-01\n",
                inline=False):
    fm = "---\ntype: orientation\nstatus: current\ndate: 2026-03-01\n"
    if isinstance(frm, list) and inline:
        fm += "from: [" + ", ".join(f'"[[{f}]]"' for f in frm) + "]\n"
    elif isinstance(frm, list):
        fm += "from:\n" + "".join(f'  - "[[{f}]]"\n' for f in frm)
    elif frm:
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
        check("an archived parent resolves", parents.get(CHILD) == [f"archive/{ROOT}"], parents)
        check("a live thread's parent resolves", parents.get(GRAND) == [CHILD], parents)
        check("a parked thread's parent resolves", parents.get(f"parked/{PARKED}") == [CHILD], parents)
        check("the OLDEST orientation's `from:` wins over a later one", ALONE not in parents.get(CHILD, []),
              parents)
        check("a thread with no `from:` has no parent", ALONE not in parents and
              f"archive/{ROOT}" not in parents, parents)
        check("the JSON says lineages, not projects", "projects" not in data and "lineages" in data,
              sorted(data))
        lineages = data.get("lineages", [])
        check("the chain is one lineage rooted at the archived thread",
              [l.get("roots") for l in lineages].count([f"archive/{ROOT}"]) == 1, lineages)
        lin = next((l for l in lineages if f"archive/{ROOT}" in l.get("roots", [])), {})
        check("the lineage holds every descendant, parked included",
              set(lin.get("threads", [])) == {f"archive/{ROOT}", CHILD, GRAND, f"parked/{PARKED}"}, lin)
        check("a thread with no parent and no children is in no lineage",
              not any(ALONE in l.get("threads", []) for l in lineages), lineages)

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
        check("`lineage` with no thread prints the lineage tree",
              r.returncode == 0 and ROOT in r.stdout and GRAND in r.stdout and ALONE not in r.stdout,
              r.stdout)

        # orientation-audit follows `from:` into archive/ on a thread's first orientation.
        r = lipika(vault, "orientation-audit", f"workstreams/{GRAND}")
        check("orientation-audit compares a first orientation against its parent",
              r.returncode in (0, 1) and "NOT CHECKED" not in r.stdout, f"exit {r.returncode}\n{r.stdout}")

    # A re-partition: one new thread from several parents, in both YAML list spellings.
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        thread(vault, OTHER, "What did the other thread do?",
               [("2026-03-10-100000", orientation(body="## Live items\n"
                 "- [OPEN Q] **the other thread's item** · as-of 2026-03-10\n"))])
        thread(vault, ALONE2, "What else stood alone?", [("2026-03-11-100000", orientation())])
        # GRAND carries `a thing`; OTHER carries its own item. MERGED carries both.
        thread(vault, MERGED, "What body of work do both become?",
               [("2026-04-01-100000", orientation([GRAND, OTHER], body="## Live items\n"
                 "- [OPEN Q] **a thing** → dies when done · as-of 2026-03-01\n"
                 "- [OPEN Q] **the other thread's item** · as-of 2026-03-10\n"))])
        # INLINE carries nothing of OTHER's, so the audit must name what it left behind.
        thread(vault, INLINE, "What does the inline one become?",
               [("2026-04-02-100000", orientation([OTHER, ALONE2], inline=True))])

        r = lipika(vault, "lineage", "--json")
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            data = {}
        parents = data.get("parents", {})
        check("a block-list `from:` names every parent", sorted(parents.get(MERGED, [])) == sorted([GRAND, OTHER]),
              parents)
        check("an inline-list `from:` names every parent", sorted(parents.get(INLINE, [])) == sorted([OTHER, ALONE2]),
              parents)
        lin = next((l for l in data.get("lineages", []) if MERGED in l.get("threads", [])), {})
        check("a merge joins both parents' lineages into one",
              {f"archive/{ROOT}", CHILD, GRAND, OTHER, MERGED, INLINE, ALONE2} <= set(lin.get("threads", [])), lin)
        check("a joined lineage lists every root", {f"archive/{ROOT}", OTHER, ALONE2} <= set(lin.get("roots", [])),
              lin)
        check("a joined lineage lists each thread once", len(lin.get("threads", [])) == len(set(lin.get("threads", []))),
              lin)

        r = lipika(vault, "lineage", MERGED)
        out = r.stdout
        check("`lineage <merged>` exits 0", r.returncode == 0, f"exit {r.returncode}\n{r.stderr}")
        check("`lineage <merged>` names both parents and the root above them",
              all(n in out for n in (ROOT, CHILD, GRAND, OTHER, MERGED)), out)

        r = lipika(vault, "orientation-audit", f"workstreams/{MERGED}")
        out = r.stdout
        check("orientation-audit compares a re-partitioned thread against every parent",
              "NOT CHECKED" not in out and GRAND in out and OTHER in out, f"exit {r.returncode}\n{out}")
        check("an item carried from either parent is accounted for", "NOT CARRIED" not in out, out)

        r = lipika(vault, "orientation-audit", f"workstreams/{INLINE}")
        out = r.stdout
        check("an item no parent's successor carries is named, with the parent it came from",
              "the other thread's item" in out and OTHER in out.split("NOT CARRIED", 1)[-1],
              f"exit {r.returncode}\n{out}")

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
