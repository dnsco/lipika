#!/usr/bin/env python3
"""
handoff-prompt -- the paste-ready prompt the next session needs, or a refusal.

WHY THIS EXISTS
  The loop ends at a restart the running agent cannot perform, cannot detect, and cannot proceed
  without. Step 5 used to say "your last message names what the next session must run" -- prose, at
  the end of a long session, which is exactly where a tired agent paraphrases. The next session then
  arrives without the one thing only the previous one knew.

  So the handoff is composed from state instead of memory: the thread, the version that is actually
  installed, the gate command for THAT version, and the graders to run, by path.

  It REFUSES rather than warns. A warning printed above a pasteable block is read past; the paste is
  what survives. The failure this exists to catch -- step 3 forgotten, version unbumped, every deploy
  command a silent no-op reporting success -- is silent by construction, so the check has to be loud
  or it is decoration.

  It reads the version from the INSTALLED plugin directory, never from the tree's manifest. Reading
  the tree and calling it "installed" is the precise confusion the loop's step-6 gate exists to
  catch, and it would be reintroduced one level down.
"""

import argparse
import filecmp
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_config  # noqa: E402

SHIPPED = ("skills", "agents", "tools", "bin")
DEFAULT_CACHE = Path.home() / ".claude" / "plugins" / "cache" / "lipika" / "lipika"


def tree_root():
    """The checkout this script lives in."""
    return Path(__file__).resolve().parent.parent


def installed_dir(cache):
    """The one live installed version directory.

    A version directory is retired by an `.orphaned_at` marker and claimed by `.in_use`. Anything
    else is ambiguous, and an ambiguous answer here would name the wrong round with confidence --
    so it refuses instead of picking.
    """
    if not cache.is_dir():
        raise Refusal(f"no installed plugin cache at {cache}\nis lipika installed as a plugin?")
    live = [
        d
        for d in sorted(cache.iterdir())
        if d.is_dir() and not (d / ".orphaned_at").exists()
    ]
    if not live:
        raise Refusal(f"every version under {cache} is orphaned; nothing is installed")
    if len(live) > 1:
        claimed = [d for d in live if (d / ".in_use").exists()]
        if len(claimed) != 1:
            names = ", ".join(d.name for d in live)
            raise Refusal(
                f"cannot tell which version is installed: {names}\n"
                "more than one is unorphaned and none is uniquely in use"
            )
        return claimed[0]
    return live[0]


class Refusal(Exception):
    pass


def manifest_version(root):
    p = root / ".claude-plugin" / "plugin.json"
    try:
        return json.loads(p.read_text())["version"]
    except (OSError, ValueError, KeyError) as exc:
        raise Refusal(f"cannot read a version from {p}: {exc}")


def differing(tree, installed):
    """Which shipped paths differ. The same comparison the loop's step 6 does by hand."""
    out = []
    for name in SHIPPED:
        a, b = tree / name, installed / name
        if not a.is_dir():
            continue
        if not b.is_dir():
            out.append(name)
            continue
        cmp = filecmp.dircmp(str(a), str(b))
        if _differs(cmp):
            out.append(name)
    return out


def _differs(cmp):
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return True
    return any(_differs(sub) for sub in cmp.subdirs.values())


def thread_dir(vault, thread):
    """Accept `workstreams/<slug>` or a bare slug; refuse anything that is not a thread."""
    cand = (vault.path / thread) if thread else None
    if cand is None or not cand.is_dir():
        cand = vault.path / "workstreams" / thread
    if not cand.is_dir():
        raise Refusal(f"no such workstream: {thread}")
    return cand


def newest_orientation(tdir):
    o = tdir / "orientation"
    if not o.is_dir():
        return None
    names = sorted(p for p in o.glob("*.md"))
    return names[-1] if names else None


ABOUT = re.compile(r'^about:\s*"?\[\[([^\]|]+)', re.M)


def graders_for(vault, tdir):
    """Every eval document whose `about:` names this thread, read from frontmatter.

    Sorted newest-first by filename, which is how the vault's stamps sort.

    This parsed a wikilink out of the whole head until 2026-08-25 -- any `[[slug]]` in the first
    1200 characters, frontmatter or body -- while its docstring claimed it read a key. Nobody
    could see the drift, because a substring match agrees with the key most of the time. That gap
    is how `up:` acquired purposes it never had: the docstring was the only description of the
    behaviour, and it was wrong. Match the key, so the claim and the code fail together.
    """
    evals = vault.path / "sources" / "evals"
    if not evals.is_dir():
        return []
    slug = tdir.name
    hits = []
    for p in sorted(evals.glob("*.md"), reverse=True):
        m = ABOUT.search(p.read_text(errors="replace")[:1200])
        if m and m.group(1).strip() == slug:
            hits.append(p)
    return hits


def compose(vault, tdir, version, graders, orientation):
    rel = tdir.relative_to(vault.path)
    lines = [
        f"Run /lipika:pickup on {rel}.",
        "",
        f"The plugin was redeployed to {version} and this session is the first to run after the",
        "restart, so start at step 6 of the loop -- prove the installed plugin is the tree before",
        "measuring anything:",
        "",
        f'  V={version}',
        '  for d in skills agents tools bin; do',
        '    diff -rq $d "$HOME/.claude/plugins/cache/lipika/lipika/$V/$d" || echo "STALE: $d"',
        "  done",
        "",
        "Any output means stop and deploy before measuring.",
        "",
    ]
    if graders:
        # Deliberately "eval documents", not "graders". `about:` cannot tell a sealed grader from the
        # record that scored it -- measured on this tool's own first run, which told a session to
        # "run" a scoring record. Naming a distinction the frontmatter does not carry would be a
        # confident wrong answer; naming what was actually found is not.
        lines.append(
            "Eval documents recorded against this thread, newest first. The graders among them "
            "are the ones written before a change; score against their text verbatim, and treat "
            "anything already scored as a record rather than work:"
        )
        for g in graders:
            lines.append(f"  {g.relative_to(vault.path)}")
        lines.append("")
    else:
        lines.append("No graders are recorded against this thread; there is nothing to score.")
        lines.append("")
    if orientation:
        lines.append(
            f"The orientation pickup will read is {orientation.relative_to(vault.path)} -- "
            "it carries the state, so this prompt does not repeat it."
        )
    else:
        lines.append(
            "This thread has no orientation yet, so pickup will fall back to the routing note "
            "and the newest dumps."
        )
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="the paste-ready prompt for the session after a restart, or a refusal"
    )
    ap.add_argument("thread", help="workstream the next session picks up (path or slug)")
    ap.add_argument("--vault")
    ap.add_argument(
        "--cache",
        default=str(DEFAULT_CACHE),
        help="installed plugin cache dir (for testing a red case)",
    )
    ap.add_argument(
        "--tree",
        default=None,
        help="checkout to compare against the installed copy (defaults to this script's own)",
    )
    args = ap.parse_args(argv)

    try:
        vault = vault_config.resolve(args.vault)
        tree = Path(args.tree).resolve() if args.tree else tree_root()
        inst = installed_dir(Path(args.cache).expanduser())
        version = inst.name

        stale = differing(tree, inst)
        if stale:
            raise Refusal(
                "the tree is not what is installed, so the next session would measure the "
                "previous round.\n"
                f"  installed: {inst}\n"
                f"  tree:      {tree}\n"
                f"  differs:   {', '.join(stale)}\n"
                "bump the version in BOTH .claude-plugin manifests, deploy, then run this again."
            )

        declared = manifest_version(tree)
        if declared != version:
            raise Refusal(
                f"the tree declares {declared} but {version} is installed.\n"
                "at an unchanged version every deploy command is a silent no-op -- deploy, "
                "then run this again."
            )

        tdir = thread_dir(vault, args.thread)
        body = compose(
            vault, tdir, version, graders_for(vault, tdir), newest_orientation(tdir)
        )
        # The fence is emitted here, not by the caller: a definition that has to wrap this in
        # prose is a definition that can wrap it wrongly, and the paste is what survives.
        print("```")
        print(body)
        print("```")
        return 0
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
