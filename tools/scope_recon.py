#!/usr/bin/env python3
"""
Scope recon — every mechanical fact about a set of scopes, in one call.

WHY
  Measured 2026-08-18: an orchestrator's pre-spawn phase was 16 calls and 328.7s. Eight of them
  were hand-written shell pipelines computing exactly what is below -- inventories, anchor
  resolution, delta diffs, a vault-wide marker harvest. Two of the eight returned NOTHING and
  were not diagnosed: a `for` loop calling git inside `$( )` failed with "command not found:
  git" twice in a row. A third blew up with "ugrep: exceeds complexity limits" inside a call
  that ran 105 SECONDS and returned two rows.

  Both failure classes are properties of writing shell at an agent's prompt, and both disappear
  by moving the loop into Python. And the phase's real cost was never the commands: strip that
  one outlier and commands were 9% of it while model generation between calls was 59%. Eleven
  calls collapsing to one is the whole saving.

  It is also what makes a `scout` worth dispatching. The Obsidian index answers link and
  frontmatter questions in ~0.01s, and it is only valid in the tree it indexes -- which is the
  main checkout, before any worktree exists. That is exactly where a scout runs.

WHAT IT EMITS PER SCOPE
  doc count, top-level docs, folder-note bytes, the anchors (BASELINE and LAST, from the pass log)
  type, the delta against each, the frontmatter table, and -- with --markers -- every PR/commit
  ref cited in the corpus, ready to hand to verify_pr_markers.py in one batch.

  Screening is reported as inputs, never as a verdict: no-delta-since-BASELINE, folder-note size,
  and whether anything sits at the scope's top level. The caller decides; a SKIP recommendation
  that hides its inputs cannot be overruled without re-deriving them.

USAGE
  python3 tools/scope_recon.py <scope-path>... [--vault PATH] [--markers] [--json]
  python3 tools/scope_recon.py workstreams/ --each          # one row per child directory

    exit 0   reported
    exit 5   bad invocation
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Two alternatives on purpose, because the digit floor can only safely differ between them.
#
#   QUALIFIED (owner/repo#N) accepts ONE digit. It used to demand two, and that silently lost
#   every single-digit ref in the vault -- measured: `dnsco/knowledge-base-template#4` was cited
#   in a doc the pass was mandated to fix, and the harvest returned {} for that scope. A young
#   repo's PRs are #1-#9, so the floor lost most of its refs, and it lost them without a word.
#   `owner/repo#4` cannot be prose or a heading, so there is nothing for the floor to protect.
#
#   BARE (#N) keeps the two-digit floor. There it earns its keep: `#1` appears in English
#   ("the #1 cause") and a one-digit bare ref is not worth the noise.
#
# Do not merge these back into one alternation -- that is what coupled the two floors.
REF = re.compile(
    r"(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(?P<num>\d{1,6})"
    r"|(?:(?P<bare>[A-Za-z0-9_.-]+))?#(?P<num2>\d{2,6})"
)
FM_KEYS = ("type", "status", "date", "about", "tier")   # `up` was retired 2026-08-25: it
# restated the folder path in 139 of 170 documents, drifted stale in 15 more, and nothing read
# it. `about:` replaces it ONLY on documents that live outside what they describe -- evals,
# epics, external, reference -- where the path genuinely cannot say which thread they concern.


def git(vault, *args):
    r = subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def frontmatter(path):
    out = {}
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return out
    if not lines or lines[0].strip() != "---":
        return out
    for l in lines[1:]:
        if l.strip() == "---":
            break
        if ":" in l:
            k, _, v = l.partition(":")
            k = k.strip()
            if k in FM_KEYS:
                out[k] = v.strip().strip('"').strip("'")
    return out


def anchors_for(vault, scope):
    """The scope's anchors, read from the pass log. Git tags are gone -- see pass_log.py.

    BASELINE is the newest stop record with result=consolidated: the only thing a later pass may
    skip work on the strength of. LAST is the newest stop record of any result. Both carry the sha
    recorded at that moment, which is what a delta is computed against.
    """
    scope = scope.strip("/")
    log = Path(vault) / "pass-log.jsonl"
    res = {"BASELINE": None, "LAST": None, "open": []}
    if not log.is_file():
        return res
    recs = []
    for line in log.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        rs = (r.get("scope") or "").strip("/")
        if rs and scope and not (rs == scope or rs.startswith(scope + "/") or scope.startswith(rs + "/")):
            continue
        recs.append(r)
    stops = [r for r in recs if r.get("event") == "stop"]
    stopped = {r.get("id") for r in stops}
    res["open"] = [r for r in recs if r.get("event") == "start" and r.get("id") not in stopped]
    if stops:
        res["LAST"] = {"sha": stops[-1].get("sha"), "ts": stops[-1].get("ts"),
                       "role": stops[-1].get("role"), "result": stops[-1].get("result")}
    cons = [r for r in stops if r.get("result") == "consolidated"]
    if cons:
        res["BASELINE"] = {"sha": cons[-1].get("sha"), "ts": cons[-1].get("ts"),
                           "role": cons[-1].get("role"), "result": "consolidated"}
    return res


def delta(vault, base, scope):
    if not base:
        return None
    code, out = git(vault, "diff", "--name-status", f"{base}..HEAD", "--", scope)
    if code != 0:
        return None
    return [l for l in out.splitlines() if l.strip()]


def canonicalise(refs):
    """Fold the spellings of one PR into one ref.

    Docs cite the same PR three ways -- `#168`, `repo#168`, `owner/repo#168` -- and handing all
    three to the verifier resolves the same PR three times. Fold toward the most qualified form,
    but only when the shorter one is a genuine tail of the longer: two different repos really can
    both have a #168, and collapsing those would report one PR's state for the other.
    """
    by_num = {}
    for r in refs:
        repo, _, num = r.rpartition("#")
        by_num.setdefault(num, []).append(repo)
    out, unqualified = [], set()
    for num, repos in by_num.items():
        full = sorted({r for r in repos if "/" in r})
        short = {r for r in repos if r and "/" not in r}
        bare = any(r == "" for r in repos)
        covered = {f.split("/")[-1] for f in full}
        out += [f"{f}#{num}" for f in full]
        # A single-segment repo (`repo#N`) is a form verify_pr_markers.py REFUSES -- and it
        # aborts the whole batch on one bad ref, so emitting these silently cost a scout its
        # entire marker resolution. They are returned separately for a human to qualify.
        unqualified.update(f"{sh}#{num}" for sh in sorted(short - covered))
        # a bare #num is only safe to drop if something qualified exists to stand for it
        if bare and not full and not short:
            out.append(f"#{num}")
    return sorted(out), sorted(unqualified)


def harvest_refs(root, scope):
    refs = {}
    for p in (root / scope).rglob("*.md"):
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        for m in REF.finditer(text):
            repo = m.group("repo") or m.group("bare") or ""
            num = m.group("num") or m.group("num2")
            # Prose hyphenates before a ref -- "post-#11605", "pre-#1885",
            # "rebase-that-drops-#11806" -- and the repo character class swallows the English.
            # A repo name never ends in a hyphen or a dot, so that alone separates them. Left
            # unfixed this put ~10 invented repos into the batch, and a verifier carrying
            # obvious noise is one whose real findings get dismissed with it.
            if repo.endswith(("-", ".")):
                repo = ""
            key = f"{repo}#{num}" if repo else f"#{num}"
            refs.setdefault(key, []).append(str(p.relative_to(root)))
    return refs


def recon_scope(vault, scope, want_markers):
    root = Path(vault)
    sdir = root / scope
    info = {"scope": scope, "exists": sdir.exists()}
    if not sdir.exists():
        return info

    docs = sorted(p for p in sdir.rglob("*.md"))
    info["doc_count"] = len(docs)
    info["top_level_docs"] = sorted(p.name for p in sdir.glob("*.md"))
    note = sdir / f"{sdir.name}.md"
    info["folder_note"] = str(note.relative_to(root)) if note.is_file() else None
    info["folder_note_bytes"] = note.stat().st_size if note.is_file() else 0

    a = anchors_for(vault, scope)
    info["anchors"] = a
    for label in ("LAST", "BASELINE"):
        base = a[label]["sha"] if a[label] else None
        d = delta(vault, base, scope)
        info[f"delta_vs_{label}"] = None if d is None else len(d)
        info[f"delta_vs_{label}_files"] = d or []

    fm = []
    for p in docs:
        row = frontmatter(p)
        row["path"] = str(p.relative_to(root))
        row["bytes"] = p.stat().st_size
        fm.append(row)
    info["frontmatter"] = fm
    # a status reading as live inside a settled tier is a defect a delta cannot see
    info["live_status_in_design"] = [
        r["path"] for r in fm
        if "/design/" in r["path"] and r.get("status") in ("active", "in-progress", "wip")
    ]
    # `missing_up` was retired 2026-08-21. It nagged for a field with no reader: `up:` had exactly
    # one consumer in the system, this report, and nothing anywhere read the VALUE. Contrast `from:`,
    # which orientation-audit follows to find a parent thread's items. A check defending a field
    # nobody consumes manufactures work at every scope it runs on.

    if want_markers:
        info["refs"] = harvest_refs(root, scope)

    # screening INPUTS, not a verdict
    info["screen_inputs"] = {
        "no_delta_since_BASELINE": info["delta_vs_BASELINE"] == 0,
        "folder_note_bytes": info["folder_note_bytes"],
        "top_level_docs_beside_note": [d for d in info["top_level_docs"]
                                       if note.is_file() and d != note.name],
    }
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scopes", nargs="+")
    ap.add_argument("--vault", default=None,
                    help="vault path or a name from ~/.config/lipika/config.json; "
                         "default: $LIPIKA_VAULT, the config, then this checkout")
    ap.add_argument("--each", action="store_true",
                    help="treat each argument as a parent and report one row per child directory")
    ap.add_argument("--markers", action="store_true", help="harvest cited PR/commit refs")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    import vault_config
    args.vault = str(vault_config.resolve_or_exit(args.vault, "scope_recon"))

    vault = Path(args.vault).expanduser().resolve()
    if not (vault / ".git").exists():
        print(f"not a git repository: {vault}", file=sys.stderr)
        return 5

    scopes = []
    for s in args.scopes:
        s = s.rstrip("/") + "/"
        if args.each:
            parent = vault / s
            if parent.is_dir():
                scopes += [str((vault / s / c.name).relative_to(vault)) + "/"
                           for c in sorted(parent.iterdir()) if c.is_dir()]
        else:
            scopes.append(s)

    results = [recon_scope(vault, s, args.markers) for s in scopes]

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    for r in results:
        print(f"\n=== {r['scope']}")
        if not r["exists"]:
            print("  DOES NOT EXIST")
            continue
        print(f"  docs {r['doc_count']}   folder-note {r['folder_note_bytes']:,}B   "
              f"top-level {len(r['top_level_docs'])}")
        for label in ("BASELINE", "LAST"):
            a = r["anchors"][label]
            if a:
                sha = (a["sha"] or "no sha recorded")[:12]
                print(f"  {label:<8} {sha}  {a['ts']}  {a['role']} ({a['result']})"
                      f"   delta {r[f'delta_vs_{label}']}")
            else:
                print(f"  {label:<8} (none — nothing has recorded one, so a pass here is full)")
        for o in r["anchors"].get("open", []):
            print(f"  OPEN PASS {o.get('role')} since {o.get('ts')} — someone may be in here now")
        if r["live_status_in_design"]:
            print(f"  live status inside design/: {', '.join(r['live_status_in_design'])}")
        si = r["screen_inputs"]
        print(f"  screen inputs: no_delta_since_BASELINE={si['no_delta_since_BASELINE']}  "
              f"note={si['folder_note_bytes']:,}B  "
              f"top_level_beside_note={len(si['top_level_docs_beside_note'])}")
        if r.get("refs"):
            print(f"  cited refs ({len(r['refs'])}): {' '.join(sorted(r['refs'])[:12])}"
                  + (" …" if len(r["refs"]) > 12 else ""))

    if args.markers:
        allrefs = sorted({k for r in results for k in (r.get("refs") or {})})
        canon, unqualified = canonicalise(allrefs)
        if canon:
            dropped = len(allrefs) - len(canon) - len(unqualified)
            print(f"\nbatch these in one call ({len(canon)} refs"
                  + (f", {dropped} duplicate spellings folded" if dropped else "") + "):")
            print(f"  python3 tools/verify_pr_markers.py {' '.join(canon)}")
        if unqualified:
            print(f"\nNOT batched — cited with a single-segment repo, which the verifier refuses"
                  f" (and it aborts the whole batch on one). Qualify as owner/repo#N by hand:")
            for u in unqualified:
                print(f"  {u}")
    print("\nScreening inputs are reported, not decided. A SKIP needs all three: no delta since the")
    print("consolidated BASELINE, a folder-note under your bound, and nothing at the scope's top level")
    print("beside it. No baseline means no licence to skip.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
