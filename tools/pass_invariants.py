#!/usr/bin/env python3
"""
Pass invariants — every end-of-pass check, in one call, run once.

WHY THIS IS ONE TOOL AND NOT FOUR COMMANDS
  The orchestrator ran the invariants twice: once as a "pre-run over my cross-scope changes
  now, so the final verification has a shorter tail", and then again in full after the merge.
  Measured 2026-08-18: 2 calls and 19s whose information was entirely discarded, because the
  merge invalidated the pre-run. The pre-run was in fact the LAST thing it did before
  returning with a scope still going -- so the one block of work it chose to do early was the
  one block the return threw away.

  Bundling them removes the temptation. There is one moment these are meaningful -- after the
  merge -- and one command that runs all of them then.

WHAT IT RUNS
  1. dangling_links.py       the [[link]] graph has no holes
  2. obsidian.py unresolved  the same question asked of Obsidian's own index, which sees
                             frontmatter link fields that (1) never scans. Neither subsumes
                             the other; a vault measured 0 by (1) and 6 by (2), both correct.
                             SKIPPED, not failed, when the index refuses (exit 3/4) -- inside
                             a worktree that refusal is correct and expected.
  3. frozen_tier_check.py    nothing altered substance in done/, sources/ or external/
  4. anchor re-diff          every scope named with --anchor has a consolidated record in the
                             pass log whose sha resolves and leaves an empty delta, which is
                             what "consolidated" means. Git tags no longer anchor anything

  Whole-vault by design. These are greps over a few dozen files, and scoping them to the delta
  is how a pass misses the merge one scope got wrong.

USAGE
  python3 tools/pass_invariants.py <base-ref> [--vault PATH] [--memory-dir PATH]
                                   [--anchor <scope-path>]...

    exit 0   every invariant clean (skips reported, not hidden)
    exit 1   at least one invariant failed -- read the section, do not re-run hoping
    exit 5   bad invocation
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


class Result:
    def __init__(self, name):
        self.name = name
        self.status = "?"      # PASS | FAIL | SKIP
        self.detail = ""
        self.output = ""


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def check_dangling(vault, memdir):
    res = Result("dangling links")
    tool = TOOLS / "dangling_links.py"
    if not tool.exists():
        res.status, res.detail = "SKIP", "dangling_links.py not present"
        return res
    cmd = [sys.executable, str(tool), str(vault)]
    if memdir:
        cmd.append(str(memdir))
    code, out = run(cmd, vault)
    res.output = out
    if code == 0:
        res.status, res.detail = "PASS", "no dangling links"
    else:
        res.status = "FAIL"
        tail = [l for l in out.splitlines() if l.startswith("== DANGLING")]
        res.detail = tail[0] if tail else "dangling links found"
    return res


def check_unresolved(vault, strict=False):
    res = Result("obsidian unresolved")
    tool = TOOLS / "obsidian.py"
    if not tool.exists():
        res.status, res.detail = "SKIP", "obsidian.py not present"
        return res
    code, out = run([sys.executable, str(tool), "unresolved"], vault)
    if code in (3, 4):
        # 3 = CLI unavailable, 4 = it indexes a different tree than this one. Inside a
        # worktree, 4 is the correct answer and not a failure of the vault.
        res.status = "SKIP"
        res.output = out
        res.detail = "index unavailable or indexes another tree (expected in a worktree)"
        return res
    if code != 0:
        res.status, res.detail, res.output = "FAIL", f"obsidian.py exited {code}", out
        return res

    items = [l.strip() for l in out.splitlines() if l.strip()]
    # A vault wikilink resolves by basename and rarely carries a slash. A path-style target is
    # almost always a markdown relative link -- [text](dir/page) -- which Obsidian also reports
    # as unresolved, and which in vendored submodule content is not the vault's business at
    # all. Reported, never failed on, unless --strict-unresolved: a check that fails forever on
    # content nobody will fix is one readers learn to dismiss, and then a real finding goes
    # with it. Obsidian DOES support path-style wikilinks, so these are surfaced, not dropped.
    named = [i for i in items if "/" not in i]
    pathy = [i for i in items if "/" in i]

    parts = []
    if named:
        parts.append("\n".join(named))
    if pathy:
        parts.append("path-style targets (usually markdown relative links, often vendored):\n"
                     + "\n".join(f"  {p}" for p in pathy))
    res.output = "\n\n".join(parts)

    bad = items if strict else named
    if bad:
        res.status = "FAIL"
        res.detail = f"{len(bad)} unresolved link target(s)"
        if pathy and not strict:
            res.detail += f" (+{len(pathy)} path-style, reported not failed)"
    else:
        res.status = "PASS"
        res.detail = "index reports none"
        if pathy:
            res.detail = f"none by name (+{len(pathy)} path-style, reported not failed)"
    return res


def check_frozen(vault, base):
    res = Result("frozen-tier substance")
    tool = TOOLS / "frozen_tier_check.py"
    if not tool.exists():
        res.status, res.detail = "SKIP", "frozen_tier_check.py not present"
        return res
    # --vault explicitly, NOT just cwd: frozen_tier_check resolves through vault_config,
    # whose order is flag -> $LIPIKA_VAULT -> config default -> checkout, and never cwd.
    # Without the flag this reported SUBSTANCE violations from the CONFIGURED vault while
    # its own header named the one under test -- accurate data about the wrong quantity,
    # which is the failure class this repo exists to prevent. Measured 2026-08-21.
    code, out = run([sys.executable, str(tool), base, "--vault", str(vault)], vault)
    res.output = out
    res.status = "PASS" if code == 0 else "FAIL"
    res.detail = "no substance altered" if code == 0 else "rule F violation, or a deleted frozen file"
    return res


def check_anchors(vault, anchors):
    """Every scope named here must have a recorded baseline whose sha leaves an empty delta.

    Git tags used to be the anchor; the pass log replaced them (see pass_log.py), so this reads
    the log. The claim being checked is unchanged: a scope recorded as consolidated must actually
    match the tree, or the next pass skips work on a promise nobody kept.
    """
    res = Result("anchors")
    if not anchors:
        res.status, res.detail = "SKIP", "no scope named (pass --anchor <scope> to check one)"
        return res
    log = Path(vault) / "pass-log.jsonl"
    if not log.is_file():
        res.status, res.detail = "FAIL", f"no pass log at {log}, so no scope can be consolidated"
        return res
    recs = []
    for line in log.read_text(errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    problems, lines = [], []
    for spec in anchors:
        scope = spec.partition("=")[0].strip("/")
        cons = [r for r in recs if r.get("event") == "stop" and r.get("result") == "consolidated"
                and (r.get("scope") or "").strip("/") == scope]
        if not cons:
            problems.append(f"{scope}: no consolidated record")
            continue
        sha = cons[-1].get("sha")
        if not sha:
            problems.append(f"{scope}: consolidated record carries no sha, so no delta is computable")
            continue
        code, out = run(["git", "cat-file", "-t", sha], vault)
        if code != 0 or out.strip() != "commit":
            problems.append(f"{scope}: recorded sha {sha[:12]} does not resolve to a commit "
                            f"(history rewritten?)")
            continue
        code, out = run(["git", "diff", "--name-only", f"{sha}..HEAD", "--", scope], vault)
        changed = [l for l in out.splitlines() if l.strip()]
        if changed:
            problems.append(f"{scope}: {len(changed)} file(s) changed since its consolidated record")
            lines.extend(f"    {c}" for c in changed[:5])
        else:
            lines.append(f"  {scope}  consolidated at {sha[:12]}, empty delta")
    res.output = "\n".join(lines)
    res.status = "FAIL" if problems else "PASS"
    res.detail = "; ".join(problems) if problems else f"{len(anchors)} scope(s) verified"
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="the pass's base ref")
    ap.add_argument("--vault", default=None,
                    help="vault path or a name from ~/.config/lipika/config.json; "
                         "default: $LIPIKA_VAULT, the config, then this checkout")
    ap.add_argument("--memory-dir", default=None)
    ap.add_argument("--anchor", action="append", default=[],
                    metavar="TAG[=SCOPE-PATH]",
                    help="a scope whose consolidated record must still hold; repeatable")
    ap.add_argument("--strict-unresolved", action="store_true",
                    help="also fail on path-style unresolved targets (markdown relative links)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="print each check's full output, not just failures")
    args = ap.parse_args()
    import vault_config
    args.vault = str(vault_config.resolve_or_exit(args.vault, "pass_invariants"))

    vault = Path(args.vault).expanduser().resolve()
    if not (vault / ".git").exists():
        print(f"not a git repository: {vault}", file=sys.stderr)
        return 5
    memdir = Path(args.memory_dir).expanduser() if args.memory_dir else None

    results = [
        check_dangling(vault, memdir),
        check_unresolved(vault, args.strict_unresolved),
        check_frozen(vault, args.base),
        check_anchors(vault, args.anchor),
    ]

    width = max(len(r.name) for r in results)
    print(f"pass invariants — vault {vault}, base {args.base}\n")
    for r in results:
        print(f"  {r.status:4}  {r.name:{width}}  {r.detail}")

    failed = [r for r in results if r.status == "FAIL"]
    skipped = [r for r in results if r.status == "SKIP"]

    for r in results:
        if r.output and (args.verbose or r.status == "FAIL"):
            print(f"\n--- {r.name} ---\n{r.output.rstrip()}")

    print()
    if skipped:
        # A skip announced costs the caller one command; a skip left silent reads as a clean
        # result, which is the failure every check here is shaped against.
        print(f"SKIPPED ({len(skipped)}): " + ", ".join(r.name for r in skipped))
    if failed:
        print(f"FAILED ({len(failed)}): " + ", ".join(r.name for r in failed))
        return 1
    print("all invariants clean" + (" (see skips above)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
