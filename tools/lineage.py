#!/usr/bin/env python3
"""Split lineage: which threads descend from which, read from each thread's `from:`.

WHY THIS EXISTS. A thread's first orientation names the threads it came from in `from:` -- one
parent after a split, several after curate re-partitions threads along new lines. That graph is the
only link between threads: no tier groups them. The epic tier was dropped 2026-09-25 and the word
"project" 2026-09-30, so a lineage is just this graph.

Before this, nothing walked a lineage from parent to child. The two readers of `from:` went one
hop up and never looked in `archive/` or `parked/`, so a split from a thread the owner had
archived lost its parent silently. Three live threads were in that state on the day this was
written.

`resolve_thread` is the one resolver for a thread named in `from:`, and `declared_parents` the one
reader of it. `orientation-audit` and `handoff-prompt` use them, so a parent in `archive/` or
`parked/` resolves everywhere, and a list of parents reads the same everywhere.

`from:` takes three spellings: `from: "[[a]]"`, `from: ["[[a]]", "[[b]]"]`, and a YAML block list.

Exit codes: 0 printed · 2 cannot locate the vault · 5 no such thread.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import threads as threads_mod
import vault_config

FROM_LINE = re.compile(r"^from:[ \t]*(.*)$", re.M)
WIKI = re.compile(r"\[\[([^\]|#\n]+)")
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


def parents_in(text):
    """Every thread `from:` names in one document's frontmatter, in order.

    Reads the inline value and, when it is empty, the YAML block list under it.
    """
    fm = text[:3000]
    if fm.startswith("---"):
        close = fm.find("\n---", 3)
        fm = fm[:close] if close != -1 else fm
    m = FROM_LINE.search(fm)
    if not m:
        return []
    value = m.group(1)
    if not value.strip():
        block = []
        for line in fm[m.end():].splitlines()[1:]:
            if not re.match(r"^\s+-\s", line):
                break
            block.append(line)
        value = "\n".join(block)
    return [s.strip() for s in WIKI.findall(value)]


def declared_parents(tdir):
    """The threads the OLDEST orientation's `from:` names, or [].

    Oldest, because a thread's parentage does not change. A later orientation that repeats or
    changes `from:` is a copying error, not a new parent.
    """
    o = Path(tdir) / "orientation"
    if not o.is_dir():
        return []
    for p in sorted(o.glob("*.md")):
        names = parents_in(p.read_text(errors="replace"))
        if names:
            return names
    return []


def rel(vault_path, d):
    return str(Path(d).relative_to(Path(vault_path) / "workstreams"))


def build(vault):
    """{thread: [parents]}, {thread: [unresolved names]}, and row info for every thread."""
    rows = {name: (date, q) for name, date, q in threads_mod.threads(vault)}
    parents, unresolved = {}, {}
    for name in rows:
        for declared in declared_parents(Path(vault.path) / "workstreams" / name):
            d = resolve_thread(vault.path, declared)
            if d is None:
                unresolved.setdefault(name, []).append(declared)
            elif rel(vault.path, d) != name and rel(vault.path, d) not in parents.get(name, []):
                parents.setdefault(name, []).append(rel(vault.path, d))
    return rows, parents, unresolved


def children_of(parents):
    out = {}
    for child, ps in parents.items():
        for parent in ps:
            out.setdefault(parent, []).append(child)
    for v in out.values():
        v.sort()
    return out


def ancestors(name, parents):
    """Every thread above `name`, nearest first, each once."""
    out, frontier, seen = [], [name], {name}
    while frontier:
        nxt = []
        for n in frontier:
            for p in parents.get(n, []):
                if p not in seen:
                    seen.add(p)
                    out.append(p)
                    nxt.append(p)
        frontier = nxt
    return out


def descendants(name, kids):
    """`name` and every thread below it, depth first, each once."""
    out, stack, seen = [], [name], set()
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
        stack.extend(reversed(kids.get(n, [])))
    return out


def lineages(parents):
    """Connected groups of threads, joined by any `from:` edge. A merge joins two lineages."""
    adj = {}
    for child, ps in parents.items():
        for p in ps:
            adj.setdefault(child, set()).add(p)
            adj.setdefault(p, set()).add(child)
    seen, out = set(), []
    for start in sorted(adj):
        if start in seen:
            continue
        group, stack = [], [start]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            group.append(n)
            stack.extend(adj[n] - seen)
        roots = sorted(n for n in group if not parents.get(n))
        kids = children_of(parents)
        ordered = []
        for r in roots:
            for n in descendants(r, kids):
                if n not in ordered:
                    ordered.append(n)
        ordered += sorted(set(group) - set(ordered))
        out.append({"roots": roots, "threads": ordered})
    return out


def line(name, rows, depth):
    date, q = rows.get(name, (None, ""))
    return f"{'  ' * depth}{name}  {date or 'undated'}  {q}"


def print_tree(name, rows, kids, depth=0, parents=None, seen=None):
    """A thread and everything below it. A thread with several parents prints in full once; later
    appearances name it and its other parents instead of repeating the subtree."""
    seen = set() if seen is None else seen
    extra = ""
    if parents and len(parents.get(name, [])) > 1:
        extra = "  (from " + ", ".join(parents[name]) + ")"
    if name in seen:
        print(f"{'  ' * depth}{name}  — shown above{extra}")
        return
    seen.add(name)
    print(line(name, rows, depth) + extra)
    for k in kids.get(name, []):
        print_tree(k, rows, kids, depth + 1, parents, seen)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lipika lineage",
                                 description="which threads descend from which, by `from:`")
    ap.add_argument("thread", nargs="?", help="one thread: every thread above it, and below it")
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
        above = ancestors(name, parents)
        if args.json:
            print(json.dumps({"thread": name, "parents": parents.get(name, []),
                              "ancestors": above,
                              "descendants": descendants(name, kids)[1:],
                              "unresolved": unresolved.get(name, [])}, indent=2))
            return 0
        # Oldest first: thread names are dated, so a sort is the order they were opened in.
        for n in sorted(above, key=lambda n: Path(n).name):
            print(line(n, rows, 0))
        print_tree(name, rows, kids, 1 if above else 0, parents)
        for u in unresolved.get(name, []):
            print(f"\n`from:` names {u}, which is not a thread here", file=sys.stderr)
        return 0

    lins = lineages(parents)
    if args.json:
        print(json.dumps({"parents": parents, "lineages": lins, "unresolved": unresolved},
                         indent=2))
        return 0
    for lin in lins:
        seen = set()
        for r in lin["roots"]:
            print_tree(r, rows, kids, 0, parents, seen)
        print()
    for child, names in sorted(unresolved.items()):
        for n in names:
            print(f"UNRESOLVED  {child}: `from:` names {n}, which is not a thread here")
    print(f"{len(lins)} lineage(s) of more than one thread; "
          f"{len(rows) - sum(len(l['threads']) for l in lins)} thread(s) stand alone.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
