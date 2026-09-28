#!/usr/bin/env python3
"""Split lineage: which threads are one project, read from each thread's `from:`.

WHY THIS EXISTS. A thread splits into a new dated thread when its question changes, and the new
thread's first orientation names its parent in `from:`. The split lineage is a project. On
2026-09-25 the owner ruled that a workstream is a project, a goal that may span repos, and dropped
the epic tier. Epics had been the only thing tying a project's threads together, so this chain
is now the only link.

Before this, nothing walked a lineage from parent to child. The two readers of `from:` went one
hop up and never looked in `archive/` or `parked/`, so a split from a thread the owner had
archived lost its parent silently. Three live threads were in that state on the day this was
written.

`resolve_thread` is the one resolver for a thread named in `from:`. `orientation-audit` and
`handoff-prompt` use it, so a parent in `archive/` or `parked/` resolves everywhere.

Exit codes: 0 printed · 2 cannot locate the vault · 5 no such thread.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import threads as threads_mod
import vault_config

FROM = re.compile(r'^from:\s*"?\[\[([^\]|#\n]+)', re.M)
CONTAINERS = threads_mod.CONTAINERS


def resolve_thread(vault_path, name):
    """The directory of the thread `name` names, or None.

    `name` may be a bare slug, `archive/<slug>`, `workstreams/...`, or a wikilink path. It
    looks in workstreams/, then parked/ and archive/, then for a unique suffix match.
    """
    root = Path(vault_path) / "workstreams"
    name = name.strip().strip("/")
    if name.startswith("workstreams/"):
        name = name[len("workstreams/"):]
    for cand in (root / name, *(root / c / name for c in CONTAINERS)):
        if cand.is_dir():
            return cand
    slug = Path(name).name
    for base in (root, *(root / c for c in CONTAINERS)):
        if base.is_dir():
            for d in sorted(base.iterdir()):
                if d.is_dir() and (d.name == slug or d.name.endswith(slug)):
                    return d
    return None


def declared_parent(tdir):
    """The slug the OLDEST orientation's `from:` names, or None.

    Oldest, because a thread's parentage does not change. A later orientation that repeats or
    changes `from:` is a copying error, not a new parent.
    """
    o = Path(tdir) / "orientation"
    if not o.is_dir():
        return None
    for p in sorted(o.glob("*.md")):
        m = FROM.search(p.read_text(errors="replace")[:1500])
        if m:
            return m.group(1).strip()
    return None


def rel(vault_path, d):
    return str(Path(d).relative_to(Path(vault_path) / "workstreams"))


def build(vault):
    """{thread: parent}, {thread: unresolved name}, and row info for every thread."""
    rows = {name: (date, q) for name, date, q in threads_mod.threads(vault)}
    parents, unresolved = {}, {}
    for name in rows:
        declared = declared_parent(Path(vault.path) / "workstreams" / name)
        if not declared:
            continue
        d = resolve_thread(vault.path, declared)
        if d is None:
            unresolved[name] = declared
        elif rel(vault.path, d) != name:
            parents[name] = rel(vault.path, d)
    return rows, parents, unresolved


def children_of(parents):
    out = {}
    for child, parent in parents.items():
        out.setdefault(parent, []).append(child)
    for v in out.values():
        v.sort()
    return out


def root_of(name, parents):
    seen = {name}
    while name in parents and parents[name] not in seen:
        name = parents[name]
        seen.add(name)
    return name


def descendants(name, kids):
    out, stack = [], [name]
    while stack:
        n = stack.pop()
        out.append(n)
        stack.extend(reversed(kids.get(n, [])))
    return out


def projects(parents):
    kids = children_of(parents)
    roots = sorted({root_of(c, parents) for c in parents})
    return [{"root": r, "threads": descendants(r, kids)} for r in roots]


def line(name, rows, depth):
    date, q = rows.get(name, (None, ""))
    return f"{'  ' * depth}{name}  {date or 'undated'}  {q}"


def print_tree(name, rows, kids, depth=0):
    print(line(name, rows, depth))
    for k in kids.get(name, []):
        print_tree(k, rows, kids, depth + 1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lipika lineage",
                                 description="which threads are one project, by split lineage")
    ap.add_argument("thread", nargs="?", help="one thread: its chain up to its root, and below it")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--vault")
    args = ap.parse_args(argv)

    try:
        vault = vault_config.resolve(args.vault)
    except Exception as exc:                                  # noqa: BLE001
        print(f"cannot locate the vault: {exc}", file=sys.stderr)
        return 2

    rows, parents, unresolved = build(vault)
    kids = children_of(parents)

    if args.thread:
        d = resolve_thread(vault.path, args.thread)
        if d is None:
            print(f"no thread named {args.thread}", file=sys.stderr)
            return 5
        name = rel(vault.path, d)
        chain = [name]
        while chain[-1] in parents and parents[chain[-1]] not in chain:
            chain.append(parents[chain[-1]])
        chain.reverse()
        if args.json:
            print(json.dumps({"thread": name, "chain": chain,
                              "descendants": descendants(name, kids)[1:],
                              "unresolved": unresolved.get(name)}, indent=2))
            return 0
        for depth, n in enumerate(chain[:-1]):
            print(line(n, rows, depth))
        print_tree(name, rows, kids, len(chain) - 1)
        if name in unresolved:
            print(f"\n`from:` names {unresolved[name]}, which is not a thread here", file=sys.stderr)
        return 0

    projs = projects(parents)
    if args.json:
        print(json.dumps({"parents": parents, "projects": projs, "unresolved": unresolved},
                         indent=2))
        return 0
    for p in projs:
        print_tree(p["root"], rows, kids)
        print()
    for child, name in sorted(unresolved.items()):
        print(f"UNRESOLVED  {child}: `from:` names {name}, which is not a thread here")
    print(f"{len(projs)} project(s) of more than one thread; "
          f"{len(rows) - sum(len(p['threads']) for p in projs)} thread(s) stand alone.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
