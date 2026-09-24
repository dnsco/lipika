#!/usr/bin/env python3
"""architecture-candidates — which reference traces are load-bearing across threads and have no architecture document.

WHY THIS EXISTS
  `architecture/` holds the owner's description of a system: present tense, stable names, no dates. It
  is the only tier an agent may not write, because one written by an agent becomes the
  most-linked document in the vault with no dated evidence positioned to contradict it.

  So the question an agent CAN answer is when one is missing, and "useful across more than one
  thread" is the observable form of that. It is mechanical, and it fires without anyone
  remembering to ask -- which is the difference between this and a line in a skill telling an agent
  to notice.

  It is a heuristic and authority to RECOMMEND, never to write. A pickup's own experience of
  reading cold is the other half of the signal and this tool cannot see it.

CONTRACT
  exit 0  nothing to recommend
  exit 1  candidates, listed with who cites them
  exit 5  bad invocation
"""

import argparse
import datetime
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import markers          # noqa: E402
import vault_config     # noqa: E402


def md_files(root):
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in ("obsidian-skills", "node_modules")]
        for n in names:
            if n.endswith(".md"):
                yield os.path.join(dirpath, n)


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


# Directories under workstreams/ that GROUP threads rather than being one. A thread here is the
# child inside them. Kept as data because the set is a vault convention, not a rule of the model.
CONTAINERS = {"parked", "archive"}
# Of those, the ones whose threads have FINISHED. An archived thread moved there on the owner's
# ruling, so its citations say nothing about what is load-bearing now, however recent its dates.
FINISHED = {"archive"}


def thread_of(rel):
    """The workstream a vault-relative path belongs to, or None.

    ONLY a workstream counts. The vault index links every trace by construction, so counting it
    clears the bar for everything and the check answers yes to every question -- measured on the
    first run, 8 of 11 traces reported as candidates on the strength of a README line. A routing
    surface citing something is not a thread depending on it.

    CONTAINERS are not threads. `workstreams/parked/` holds five separate efforts and counted as one
    voting thread, which understates the corpus and lets one stale date silence five. Creating the
    epic tier did NOT fix this on its own -- an epic cites its threads rather than containing them,
    so the folders correctly stayed where they were and this function kept seeing one child.
    """
    parts = rel.split(os.sep)
    if len(parts) <= 2 or parts[0] != "workstreams":
        return None
    if parts[1] in CONTAINERS and len(parts) > 3:
        return os.path.join(parts[1], parts[2])
    return parts[1]


DATED = re.compile(r"(\d{4}-\d{2}-\d{2})")


def newest_dated_doc(root):
    """The newest YYYY-MM-DD found in a filename under root, or None.

    FILENAME dates, not git dates. A vault-wide restructure rewrites every file's commit
    date and makes every thread look equally fresh: measured 2026-08-21, all seven
    workstreams reported the same last-commit date while their filename dates spanned
    eighteen days. The filename is written by the author at the moment of writing and
    nothing later touches it.
    """
    best = None
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for n in names:
            m = DATED.match(n)
            if m and (best is None or m.group(1) > best):
                best = m.group(1)
    return best


def live_threads(vault, today, within_days):
    """Which workstreams still count as live, and why each one does not.

    A dead thread's citations are not evidence that anything is load-bearing NOW. Threads
    are short-lived by design, so most are dead most of the time and counting them counts
    mostly noise.

    There is no shelf list. A thread set aside stops accruing documents, so the date rule
    already covers it and a second concept would only disagree with the first.
    """
    ws_root = os.path.join(vault, "workstreams")
    live, excluded = set(), {}
    if not os.path.isdir(ws_root):
        return live, excluded

    # Must enumerate the same threads `thread_of` names, or a thread votes under a key nothing
    # here ever marked live. Expand containers one level; anything else is a thread.
    names = []
    for name in sorted(os.listdir(ws_root)):
        if name.startswith(".") or not os.path.isdir(os.path.join(ws_root, name)):
            continue
        if name in CONTAINERS:
            children = sorted(os.listdir(os.path.join(ws_root, name)))
            names += [os.path.join(name, c) for c in children
                      if os.path.isdir(os.path.join(ws_root, name, c)) and not c.startswith(".")]
            # Loose .md files sitting in a container belong to no thread, so they can never vote.
            # Say so: an unannounced gap reads as "everything was counted".
            loose = [c for c in children if c.endswith(".md")]
            if loose:
                excluded[f"{name}/ (loose)"] = (
                    f"{len(loose)} document(s) directly in the container, in no thread — cannot vote")
        else:
            names.append(name)

    for name in names:
        if name.split(os.sep)[0] in FINISHED:
            excluded[name] = "archived"
            continue
        d = os.path.join(ws_root, name)
        newest = newest_dated_doc(d)
        if newest is None:
            excluded[name] = "no dated document"
            continue
        age = (today - datetime.date(*(int(x) for x in newest.split("-")))).days
        if age > within_days:
            excluded[name] = f"last accrued {newest} ({age}d)"
        else:
            live.add(name)
    return live, excluded


def main(argv):
    ap = argparse.ArgumentParser(prog="lipika architecture-candidates", add_help=True)
    ap.add_argument("--vault", default=None)
    ap.add_argument("--min-threads", type=int, default=2,
                    help="how many distinct workstreams must cite a trace before it is a candidate")
    ap.add_argument("--live-within-days", type=int, default=14,
                    help="a thread votes only if it accrued a dated document this recently "
                         "(a chosen threshold, revisable; see design/vault-and-agent-ontology.md)")
    ap.add_argument("--all-threads", action="store_true",
                    help="let threads that have stopped accruing vote too")
    ap.add_argument("--today", default=None, help="YYYY-MM-DD, for tests")
    args = ap.parse_args(argv)

    try:
        # resolve() returns a Vault, whose existence is the proof it is one; .path is the str.
        vault = args.vault or str(vault_config.resolve().path)
    except Exception as e:                                # noqa: BLE001
        print(f"cannot resolve the vault: {e}", file=sys.stderr)
        return 5

    arch_dir = os.path.join(vault, "architecture")
    portrayed = set()      # everything the architecture documents already link to
    nodes = []
    if os.path.isdir(arch_dir):
        for p in md_files(arch_dir):
            nodes.append(stem(p))
            body = open(p, encoding="utf-8", errors="replace").read()
            portrayed |= {t.strip() for t in markers.WIKILINK.findall(body)}

    # Traces: dated documents in any reference/ directory, at the root or under a workstream.
    traces = {}
    for p in md_files(vault):
        rel = os.path.relpath(p, vault)
        if os.sep + "reference" + os.sep in os.sep + rel or rel.startswith("reference" + os.sep):
            traces[stem(p)] = rel

    if not traces:
        print("no reference/ traces in the vault — nothing to recommend an architecture document for.")
        return 0

    today = (datetime.date(*(int(x) for x in args.today.split("-")))
             if args.today else datetime.date.today())
    live, excluded = ((None, {}) if args.all_threads
                      else live_threads(vault, today, args.live_within_days))

    # Who cites each trace, by thread. A thread that has stopped accruing does not vote.
    cited = defaultdict(set)
    for p in md_files(vault):
        rel = os.path.relpath(p, vault)
        if rel.startswith("architecture" + os.sep):
            continue
        body = open(p, encoding="utf-8", errors="replace").read()
        here = thread_of(rel)
        if not here:
            continue                       # routing surfaces and raw inputs do not vote
        if live is not None and here not in live:
            continue                       # a thread that has stopped accruing does not vote
        for target in markers.WIKILINK.findall(body):
            t = target.strip()
            if t in traces and stem(p) != t:
                cited[t].add(here)

    cands = sorted(((t, srcs) for t, srcs in cited.items()
                    if len(srcs) >= args.min_threads and t not in portrayed),
                   key=lambda kv: (-len(kv[1]), kv[0]))

    print(f"{len(traces)} trace(s) · {len(nodes)} architecture node(s) · "
          f"threshold {args.min_threads} thread(s)")
    if live is not None:
        print(f"live thread(s) voting: {', '.join(sorted(live)) or 'none'}")
        # Announce every exclusion. A silent one reads as "everything was counted".
        for name in sorted(excluded):
            print(f"  not voting · {name} — {excluded[name]}")

    if not cands:
        # With no architecture documents at all, "already reachable from one" is vacuously true and
        # reads as coverage. Found by a cold pickup 2026-08-21 -- the same defect class as
        # orientation-audit's exit 0 answering both "checked and clean" and "nothing was checked",
        # in the sibling tool, unfixed because the fix was applied where it was found.
        if not nodes:
            print("\nnothing to recommend — and there are NO architecture documents, so this is not "
                  "coverage.\nNo trace was cited by "
                  f"{args.min_threads}+ live threads. That is the whole finding.")
        else:
            print("\nnothing to recommend: every cross-thread trace is already reachable from an "
                  "architecture document.")
        return 0

    print("\nCANDIDATES — cited across threads, with no architecture node linking them:")
    for t, srcs in cands:
        print(f"  · {t}")
        print(f"      {traces[t]}")
        print(f"      cited from {len(srcs)} threads: {', '.join(sorted(srcs))}")
    print("\nRecommend these to the owner with pointers, and do not write one yourself.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
