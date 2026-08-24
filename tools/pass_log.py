#!/usr/bin/env python3
"""
Pass log — one shared, append-only record of what every role is doing to this vault.

WHY ONE FILE AND NOT ONE PER UNIT
  Git tags were the previous mechanism and they were the wrong shape: a tag is a single global
  name per scope, so it could say neither WHEN a pass ran nor that two agents are on the same
  ground right now. An append-only log with timestamps says both. The tag mechanism is DEAD as of
  2026-08-19 (owner) -- nothing reads one, nothing writes one, and none were imported.

  The first design of this log put one beside each unit -- one per workstream, one per task --
  on the argument that history belongs next to its subject. That was reversed by the owner
  (2026-08-19, Dennis) for a reason the per-unit shape cannot serve: AGENTS NEED TO SEE WHAT
  OTHER AGENTS ARE CURRENTLY DOING, and they cannot afford to read N logs to find out. Passes
  run in parallel, in worktrees, over overlapping scopes, and the failure they produce is
  stomping each other's edits. Coordination is a global question, so it gets a global file.

  So: ONE log, at the vault root, and every role emits a `start` record and a `stop` record
  around its pass. `active` is then one read that answers "who else is on this ground".

  The cost of the reversal is that the log is not partitioned the way everything else here is,
  and it grows without bound. Both are cheap: `--scope` filters, and a log of one line per pass
  boundary is small for years. Consolidating many logs into one is mechanical; splitting one is
  not, which is the other reason this direction is the safe one.

WHERE THE FILE LIVES, AND WHY IT IS NOT TRACKED
  It resolves to the MAIN checkout (`git rev-parse --git-common-dir`), never the worktree the
  caller happens to be in. A sub-agent in an isolated worktree must append to the same file the
  orchestrator reads, or the log answers the coordination question about a tree nobody shares.

  A record carries the HEAD sha at the moment it was written, which is the only thing the tags were
  ever good for: the baseline record's sha is what a later pass diffs from. Record a `stop` from the tree that holds the merged
  work, or the sha anchors a commit nobody else has. And never rewrite history afterwards -- a rebase or squash
  orphans every recorded sha, and then no delta can be computed.

  It is deliberately UNTRACKED (git-excluded). Two reasons, both mechanical: N worktrees
  appending to a tracked file conflict on every pass, and this is machinery state rather than
  vault content -- nothing in the corpus should cite it. A missing log is a valid state and
  means "no baseline", which the tool reports rather than guessing around.

WHAT THE RECORDS MUST KEEP CLAIMING
  The log carries the guarantee, and the tool enforces it rather than asking:
    - A FULL run's stop record with `--result consolidated` is what establishes a baseline. It
      is the only thing a later pass may skip work on the strength of.
    - DELTAS STACK. A delta may never record `consolidated` (exit 2 -- a defect, not a
      judgement call). Their accumulated weight IS the signal that a full run is due, which is
      what `baseline` reports.
    - A SKIPPED SCOPE IS NEVER RECORDED AS CONSOLIDATED. `--result skipped` exists so that
      "not looked at" cannot be spelled the same way as "already handled".

USAGE
  python3 tools/pass_log.py start librarian "converting the workstream" --scope workstreams/x --kind full
  python3 tools/pass_log.py stop  librarian "converted, 3 commits" --result consolidated
    Role first, then one line of description; the timestamp and the HEAD sha are the tool's job.
    `stop` resolves the id from the role (and --scope when you hold several open), because
    hand-carrying a 62-char id between two commands is a transcription hazard, and a stop naming
    the wrong id records the wrong pass as finished. --id still overrides.
  python3 tools/pass_log.py active [--scope S] [--stale-hours N]
  python3 tools/pass_log.py history --scope S [--limit N]
  python3 tools/pass_log.py baseline --scope S

EXIT CODES
  0  fine -- and for `start`, no other pass overlaps your scope
  1  something to read and judge: `start` found a concurrent overlapping pass; `baseline` found
     no consolidated baseline (so your pass is necessarily full)
  2  a defect, not a judgement call: a delta or a scout claiming `consolidated`, or a `stop`
     naming an id that never started
  5  bad invocation
"""

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

LOG_NAME = "pass-log.jsonl"

# Kinds that may establish a consolidated baseline. Everything else stacks.
BASELINE_KINDS = {"full"}
# `eval` is developer work — profiling or measuring another agent's run. It is exempt from
# the span budgets (its subject is a transcript, not the corpus) and it never consolidates.
# "curate" was missing while `agents/curator.md` prescribed it, so the curator's FIRST command
# failed on every run -- measured 2026-08-24. "clerk" and "convert" name retired roles and stay
# only because past log entries carry them.
KINDS = ["full", "delta", "scout", "dump", "curate", "clerk", "convert", "eval", "rollover"]
RESULTS = ["consolidated", "incremental", "skipped", "aborted"]


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def head_sha():
    """The commit a later pass diffs from. A record without one cannot answer 'what changed since'."""
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return out.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main_checkout():
    """The single shared tree, resolved from inside a worktree as well as from the main one."""
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not common:
        return None
    # <main>/.git -> <main>;  a bare repo has no working tree and is not a vault
    parent = os.path.dirname(common.rstrip("/"))
    return parent or None


def log_path(arg):
    """Where the shared log is. **The vault's root, never the caller's repository.**

    This used to derive from the current checkout, which was right while the tools lived inside the
    vault and wrong the moment they moved: running a tool from the machinery's own repo then wrote
    coordination records into the machinery's repo, where no other agent looks. Silently — an
    append always succeeds. One log per vault is the entire point of the file, so the vault
    resolves it.
    """
    if arg:
        return os.path.abspath(arg)
    env = os.environ.get("VAULT_PASS_LOG")
    if env:
        return os.path.abspath(env)
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import vault_config
        return str(vault_config.resolve().path / LOG_NAME)
    except Exception:
        pass  # fall back to the checkout, which is right when it IS the vault
    root = main_checkout()
    if not root:
        return None
    return os.path.join(root, LOG_NAME)


def read_records(path):
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # A torn or hand-edited line is reported, never silently dropped: this file is
                # the coordination surface, so a hole in it is a fact the caller needs.
                out.append({"event": "unparseable", "line_no": n, "raw": line[:200]})
    return out


def append_record(path, rec):
    """One line, one atomic append. flock so parallel agents cannot interleave a line."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def norm_scope(scope):
    return scope.strip().strip("/") if scope else ""


def overlaps(a, b):
    """Path containment either way -- the same ground, not merely a similar name."""
    a, b = norm_scope(a), norm_scope(b)
    if not a or not b:
        return True  # an unscoped pass touches anything
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def open_passes(records):
    """start records with no matching stop, in log order."""
    stopped = {r.get("id") for r in records if r.get("event") == "stop"}
    return [r for r in records if r.get("event") == "start" and r.get("id") not in stopped]


def lineage(records, pass_id):
    """A pass's ancestor ids -- a sub-librarian nested inside its orchestrator's scope."""
    by_id = {r.get("id"): r for r in records if r.get("event") == "start"}
    out, cur, guard = set(), pass_id, 0
    while cur and guard < 32:
        rec = by_id.get(cur)
        cur = rec.get("parent") if rec else None
        if cur:
            out.add(cur)
        guard += 1
    return out


def make_id(role, scope, when):
    slug = re.sub(r"[^a-z0-9]+", "-", norm_scope(scope).lower()).strip("-") or "vault"
    return f"{role}-{slug}-{when.strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"


def age_str(delta):
    mins = int(delta.total_seconds() // 60)
    if mins < 60:
        return f"{mins}m"
    return f"{mins // 60}h{mins % 60:02d}m"


def fmt_open(rec, ref, stale_after):
    started = parse_ts(rec.get("ts"))
    age = "?" if not started else age_str(ref - started)
    stale = ""
    if started and stale_after and (ref - started) > stale_after:
        stale = "  STALE (no stop record -- assume the agent died, not that it is still working)"
    return (f"  {rec.get('id')}\n"
            f"    role={rec.get('role')} kind={rec.get('kind')} scope={rec.get('scope') or '(whole vault)'}"
            f" started={rec.get('ts')} age={age}{stale}"
            + (f"\n    note: {rec['note']}" if rec.get("note") else ""))


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def check_scope(scope, log_path):
    """A scope is a path, and a description in that slot silently mislabels the record.

    Measured on the first day of use: an agent passed its one-line description as --scope, and the
    log recorded a pass on a scope named after a sentence -- which no overlap check can match, so
    the record was invisible to exactly the coordination the log exists for. Whitespace is the
    unambiguous tell, so that is refused; a path that simply does not exist is warned about,
    because a pass may legitimately open on a scope it is about to create.
    """
    scope = norm_scope(scope)
    if not scope:
        return 0
    if any(c.isspace() for c in scope):
        print(f"refusing: --scope {scope!r} contains whitespace. A scope is a PATH, e.g. "
              f"workstreams/x.\nThe description is the second positional argument: "
              f"pass_log.py start <role> \"<description>\" --scope <path>", file=sys.stderr)
        return 5
    root = os.path.dirname(log_path)
    if root and not os.path.exists(os.path.join(root, scope)):
        print(f"note: {scope} does not exist under {root} -- fine if you are about to create it, "
              f"wrong if it is a typo, and an overlap check cannot match a scope nobody else names.")
    return 0


def cmd_start(args, path):
    bad = check_scope(args.scope, path)
    if bad:
        return bad
    records = read_records(path)
    when = now()
    pass_id = args.id or make_id(args.role, args.scope, when)
    rec = {
        "ts": iso(when), "event": "start", "id": pass_id, "role": args.role,
        "scope": norm_scope(args.scope), "kind": args.kind, "pid": os.getpid(),
        "sha": head_sha(),
    }
    if args.parent:
        rec["parent"] = args.parent
    if args.note:
        rec["note"] = args.note
    append_record(path, rec)

    mine = lineage(records + [rec], pass_id) | {pass_id}
    concurrent = [r for r in open_passes(records)
                  if r.get("id") not in mine
                  and pass_id not in lineage(records + [rec], r.get("id"))
                  and overlaps(args.scope, r.get("scope"))]
    print(pass_id)
    if not concurrent:
        print(f"no other pass is on {norm_scope(args.scope) or 'the vault'}  (log: {path})")
        return 0
    print(f"\nCONCURRENT PASS ON YOUR GROUND -- {len(concurrent)} open record(s) overlapping "
          f"{norm_scope(args.scope) or 'the whole vault'}:")
    for r in concurrent:
        print(fmt_open(r, now(), timedelta(hours=args.stale_hours)))
    print("\nJudge this before you write. A pass marked STALE is an agent that died without a stop\n"
          "record; a fresh one is someone editing the same files as you.")
    return 1


def resolve_id(records, role, scope):
    """The one open pass this caller means. Refuses rather than guesses between two.

    Hand-carrying a 62-char id from `start` to `stop` is a transcription hazard, and a stop that
    names the wrong id records the wrong pass as finished. So the id is derived: the newest open
    start for this role (and scope, if given).
    """
    open_for_role = [r for r in open_passes(records)
                     if r.get("role") == role and (not scope or overlaps(scope, r.get("scope")))]
    if not open_for_role:
        return None, "no open pass for that role"
    if len(open_for_role) > 1:
        ids = "\n  ".join(f"{r['id']}  scope={r.get('scope') or '(vault)'}" for r in open_for_role)
        return None, f"{len(open_for_role)} open passes for that role -- pass --scope or --id:\n  {ids}"
    return open_for_role[0]["id"], None


def cmd_stop(args, path):
    records = read_records(path)
    starts = {r.get("id"): r for r in records if r.get("event") == "start"}
    if not args.id:
        args.id, why = resolve_id(records, args.role, args.scope)
        if not args.id:
            print(f"cannot resolve which pass to close: {why}", file=sys.stderr)
            return 5
    start = starts.get(args.id)
    if start is None:
        print(f"no start record for id {args.id!r} in {path}", file=sys.stderr)
        print("A stop must close a start -- an unpaired stop records a pass nobody can date.",
              file=sys.stderr)
        return 2
    kind = start.get("kind")
    if args.result == "consolidated" and kind not in BASELINE_KINDS:
        print(f"refusing: a {kind} pass may not record 'consolidated'.", file=sys.stderr)
        print("Only a full run establishes a baseline. Deltas stack, and their accumulated weight\n"
              "is the signal the next full run is due. Use --result incremental.", file=sys.stderr)
        return 2
    if any(r.get("event") == "stop" and r.get("id") == args.id for r in records):
        print(f"refusing: {args.id} already has a stop record.", file=sys.stderr)
        return 2
    sha = head_sha()
    started = parse_ts(start.get("ts"))
    rec = {
        "ts": iso(now()), "event": "stop", "id": args.id, "role": start.get("role"),
        "scope": start.get("scope"), "kind": kind, "result": args.result,
        "sha": sha,
    }
    if started:
        rec["span_s"] = int((now() - started).total_seconds())
    # What the pass actually moved, measured rather than claimed -- and measured HERE, because an
    # agent composing figures by hand is the expensive way to get a worse number. Every field in a
    # record is either the tool's (ts, sha, span_s, commits, files_changed) or one short note. There
    # is deliberately no --metric flag: the first run with one had an agent retyping a span its own
    # child had already recorded (2026-08-19, owner: do not spend tokens emitting metrics). Anything
    # per-call -- tool counts, bytes returned -- comes from agent_transcript.py, which reads the
    # transcript and costs the agent nothing.
    rec.update(work_done(start.get("sha"), sha, start.get("scope")))
    if args.note:
        rec["note"] = args.note
    append_record(path, rec)
    started = parse_ts(start.get("ts"))
    span = age_str(now() - started) if started else "?"
    moved = " ".join(f"{k}={v}" for k, v in rec.items()
                     if k in ("commits", "files_changed"))
    print(f"stopped {args.id}  result={args.result}  span={span}  {moved}".rstrip())
    if args.result == "skipped":
        print("recorded as SKIPPED -- not consolidated. A later pass may not skip it on this record.")
    return 0


def work_done(base_sha, head, scope):
    """commits and files changed between a pass's start and stop, under its scope."""
    out = {}
    if not base_sha or not head or base_sha == head:
        return {"commits": 0, "files_changed": 0}
    rng = f"{base_sha}..{head}"
    args = ["--", scope] if norm_scope(scope) else []
    try:
        c = subprocess.run(["git", "rev-list", "--count", rng] + args,
                           capture_output=True, text=True, check=True).stdout.strip()
        out["commits"] = int(c or 0)
        f = subprocess.run(["git", "diff", "--name-only", rng] + args,
                           capture_output=True, text=True, check=True).stdout.split()
        out["files_changed"] = len(f)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return {}
    return out


def cmd_active(args, path):
    records = read_records(path)
    ref = now()
    stale_after = timedelta(hours=args.stale_hours)
    rows = [r for r in open_passes(records) if overlaps(args.scope, r.get("scope"))]
    torn = [r for r in records if r.get("event") == "unparseable"]
    if not os.path.exists(path or ""):
        print(f"no pass log at {path} -- nothing has recorded a pass yet")
        return 0
    if not rows:
        print(f"no open pass on {norm_scope(args.scope) or 'the vault'}  (log: {path})")
    else:
        print(f"{len(rows)} open pass(es) on {norm_scope(args.scope) or 'the vault'}:")
        for r in rows:
            print(fmt_open(r, ref, stale_after))
    for r in torn:
        print(f"  UNPARSEABLE line {r['line_no']}: {r['raw']}")
    return 0


def cmd_history(args, path):
    records = [r for r in read_records(path)
               if r.get("event") in ("start", "stop") and overlaps(args.scope, r.get("scope"))]
    if not records:
        print(f"no records for {norm_scope(args.scope) or 'the vault'}  (log: {path})")
        return 0
    for r in records[-args.limit:]:
        extra = f" result={r['result']}" if r.get("result") else ""
        for k in ("span_s", "commits", "files_changed"):
            if r.get(k) is not None:
                extra += f" {k}={r[k]}"
        note = f"  -- {r['note']}" if r.get("note") else ""
        print(f"{r['ts']}  {r['event']:5}  {r.get('role','?'):15} {r.get('kind','?'):6} "
              f"{r.get('scope') or '(vault)'}{extra}{note}")
    return 0


def cmd_baseline(args, path):
    records = read_records(path)
    scoped = [r for r in records if overlaps(args.scope, r.get("scope"))]
    baselines = [r for r in scoped
                 if r.get("event") == "stop" and r.get("result") == "consolidated"]
    if not baselines:
        print(f"NO BASELINE for {norm_scope(args.scope) or 'the vault'} -- no full run has recorded "
              f"'consolidated'.")
        print("Your pass is necessarily full: nothing here has been read, so nothing may be skipped.")
        return 1
    last = baselines[-1]
    since = [r for r in scoped
             if r.get("event") == "stop" and parse_ts(r.get("ts")) and parse_ts(last["ts"])
             and parse_ts(r["ts"]) > parse_ts(last["ts"])]
    print(f"baseline: {last['ts']}  {last.get('role')} full on {last.get('scope') or '(vault)'}")
    if last.get("sha"):
        print(f"anchor:   {last['sha']}   -> your delta is `git diff --stat {last['sha'][:12]}..HEAD -- <scope>`")
    else:
        print("anchor:   none recorded -- the delta cannot be computed from this record; treat the pass as full")
    print(f"deltas since: {len(since)}")
    if since:
        print("Those are incremental and unconsolidated. Their accumulated weight is the signal "
              "the next full run is due.")
    skipped = [r for r in scoped if r.get("event") == "stop" and r.get("result") == "skipped"]
    if skipped:
        print(f"skipped records: {len(skipped)} -- these claim no coverage; read them before "
              f"treating the scope as handled.")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(
        description="One shared append-only log of vault passes: who is working where, and what "
                    "has actually been consolidated.")
    ap.add_argument("--log", help="override the log path (default: <main checkout>/" + LOG_NAME + ")")
    ap.add_argument("--stale-hours", type=float, default=4.0,
                    help="an open pass older than this is reported STALE (default 4)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start", help="open a pass; prints its id and any concurrent overlapping pass")
    s.add_argument("role", help="who you are: librarian, frontier-clerk, context-dump, scout, …")
    s.add_argument("note", nargs="?", default="", help="one line on what you are about to do")
    s.add_argument("--scope", default="", help="path the pass may write, e.g. workstreams/x")
    s.add_argument("--kind", default="delta", choices=KINDS)
    s.add_argument("--parent", help="the id of the pass that dispatched you, if any")
    s.add_argument("--id", help="use this id instead of a generated one")

    t = sub.add_parser("stop", help="close a pass and record what it established")
    t.add_argument("role", help="the same role you opened with; the id is resolved from it")
    t.add_argument("note", nargs="?", default="", help="one line on what you did")
    t.add_argument("--result", default="incremental", choices=RESULTS)
    t.add_argument("--scope", default="", help="narrow the match when you have several open")
    t.add_argument("--id", help="close this exact id, skipping resolution")

    a = sub.add_parser("active", help="open passes -- who is on this ground right now")
    a.add_argument("--scope", default="")

    h = sub.add_parser("history", help="recent records for a scope")
    h.add_argument("--scope", default="")
    h.add_argument("--limit", type=int, default=20)

    b = sub.add_parser("baseline", help="the last consolidated full run, and the deltas since")
    b.add_argument("--scope", default="")
    return ap


def main(argv):
    ap = build_parser()
    args = ap.parse_args(argv)
    path = log_path(args.log)
    if not path:
        print("cannot locate the vault: not a git repository, and no --log or VAULT_PASS_LOG given",
              file=sys.stderr)
        return 5
    return {
        "start": cmd_start, "stop": cmd_stop, "active": cmd_active,
        "history": cmd_history, "baseline": cmd_baseline,
    }[args.cmd](args, path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
