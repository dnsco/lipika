#!/usr/bin/env python3
"""What threads are live in the vault, so a session can be ASKED which one rather than guess.

WHY THIS EXISTS. Both capture skills used to resolve their thread from `git log ... --
workstreams/` and take the most recent. Several threads accrue in one vault on the same day --
this machinery and a product migration in another repo are two questions with two checkouts --
and the log interleaves them commit by commit. Measured 2026-08-25: the newest three commits
alternated between a machinery thread and a service-migration thread, so "most recently touched"
would have handed a product session the machinery thread, and two hours earlier the reverse.
Nothing anywhere reported the mismatch, because nothing knew what the session meant to work on.

So this prints the candidates and makes no choice. It deliberately has NO "--pick" and no
default: the whole defect was a resolver that always had an answer.

The date shown is the newest dated document IN the thread, not the thread's last commit. A commit
touching ten threads says nothing about which one accrued.
"""

import argparse
import re
import sys
from pathlib import Path

import vault_config

STAMP = re.compile(r"(\d{4}-\d{2}-\d{2})")


def newest_dated(tdir):
    """The latest date appearing in any document name under this thread. None if undated."""
    best = None
    for p in tdir.rglob("*.md"):
        m = STAMP.match(p.name)
        if m and (best is None or m.group(1) > best):
            best = m.group(1)
    return best


def question(tdir):
    """The thread's own one-line description, from its routing note's first heading."""
    for cand in (tdir / f"{tdir.name}.md", *sorted(tdir.glob("*.md"))):
        if not cand.is_file():
            continue
        for line in cand.read_text(errors="replace").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        break
    return ""


def threads(vault):
    root = vault.path / "workstreams"
    if not root.is_dir():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name == "parked":
            for p in sorted(d.iterdir()):
                if p.is_dir():
                    out.append((f"parked/{p.name}", newest_dated(p), question(p)))
            continue
        out.append((d.name, newest_dated(d), question(d)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="list the vault's threads; makes no choice, on purpose"
    )
    ap.add_argument("--vault")
    ap.add_argument("--all", action="store_true", help="include parked threads")
    args = ap.parse_args(argv)

    try:
        vault = vault_config.resolve(args.vault)
    except Exception as exc:  # vault_config refuses rather than guessing; say so plainly
        print(f"cannot locate the vault: {exc}", file=sys.stderr)
        return 2

    rows = threads(vault)
    if not args.all:
        rows = [r for r in rows if not r[0].startswith("parked/")]
    if not rows:
        print("no threads in workstreams/", file=sys.stderr)
        return 1

    rows.sort(key=lambda r: (r[1] or "0000-00-00"), reverse=True)
    width = max(len(r[0]) for r in rows)
    for name, date, q in rows:
        print(f"  {name:<{width}}  {date or 'undated  '}  {q}")
    print()
    print(f"{len(rows)} thread(s). ASK which one -- newest is not an answer, it is a coincidence "
          "of whichever\nthread committed last, and two of these are usually different repos.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
