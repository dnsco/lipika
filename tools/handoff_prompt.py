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


FROM = re.compile(r'^from:\s*"?\[\[([^\]|]+)', re.M)


def thread_lineage(tdir):
    """This thread's slug, then its parent's, following `from:` on the newest orientation.

    A SPLIT SEVERS GRADER SELECTION, and it does so silently -- measured 2026-08-25, on the split
    that this function was written during. Graders are sealed `about:` the thread they were written
    in; the work then moves to a successor thread, and the successor has none of its own. The tool
    printed "No graders are recorded against this thread; there is nothing to score" over six
    unscored clauses, exit 0, in a block meant to be pasted verbatim into the next session.

    Following `from:` is what `orientation-audit` already does to find a parent's items, so the
    edge exists and was simply not read here. One hop is deliberate: a chain of threads should not
    accumulate every grader ever written, and a grader more than one split old is almost certainly
    spent.
    """
    slugs = [tdir.name]
    o = tdir / "orientation"
    if o.is_dir():
        # ANY orientation, not just the newest. The 0.2.6 fix read only the newest, which carries
        # `from:` on a thread's FIRST orientation and never again -- so the very next handoff
        # dropped the parent's graders and the split-severance bug came back by another route.
        # Caught 2026-08-25 on the second handoff into this thread: five eval documents became one,
        # silently, at exit 0. A thread's parentage does not change, so the oldest orientation that
        # declares one is the answer.
        for name in sorted(o.glob("*.md")):
            m = FROM.search(name.read_text(errors="replace")[:1200])
            if m:
                slugs.append(m.group(1).strip())
                break
    return slugs


def graders_for(vault, tdir):
    """Every eval document whose `about:` names this thread or the one it split from.

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
    wanted = set(thread_lineage(tdir))
    hits = []
    for p in sorted(evals.glob("*.md"), reverse=True):
        m = ABOUT.search(p.read_text(errors="replace")[:1200])
        if m and m.group(1).strip() in wanted:
            hits.append(p)
    return hits


def compose(vault, tdir, version, graders, orientation, tree=None, cache=None):
    """The next session's prompt. Machinery framing ONLY when a deploy was declared.

    THE DEFECT THIS FIXES: this emitted the deploy sentence, the version and the four-directory
    gate for EVERY thread, unconditionally, at exit 0. Measured 2026-08-25 against
    `embedded-jetty-docker` -- a service migration that has never deployed this plugin -- it
    asserted "The plugin was redeployed to 0.2.6 and this session is the first to run after the
    restart" and told the reader that any output from the gate meant stop and deploy. Pasted into
    that thread's own checkout, three legs of the gate error and the fourth prints
    "Only in agents: .gitignore", because that repo has an `agents/` directory holding
    opentelemetry-javaagent.jar and postgresql.jar. A plausible staleness finding, not an obvious
    category error, inside a block the skill says to paste verbatim.

    `deployed` is an ARGUMENT and never an inference. The tool knows the installed version; it
    cannot know whether this session deployed, and it must not guess from the thread's name, path
    or tags. Inferring would rebuild `up:`: a value nothing declared, read by one caller, explained
    by none.
    """
    rel = tdir.relative_to(vault.path)
    lines = [f"Run /lipika:pickup on {rel}.", ""]
    if version:
        # Absolute paths on BOTH sides. The relative `$d` form silently compared whatever
        # directory the next session happened to open in -- correct only from this checkout,
        # which is the one place it proves nothing.
        gate_tree = tree if tree else Path.cwd()
        lines += [
            f"The plugin was redeployed to {version} and this session is the first to run after the",
            "restart, so start at step 6 of the loop -- prove the installed plugin is the tree before",
            "measuring anything:",
            "",
            f'  V={version}',
            f'  T="{gate_tree}"',
            f'  I="{cache}"',
            '  for d in skills agents tools bin; do',
            '    diff -rq "$T/$d" "$I/$V/$d" || echo "STALE: $d"',
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
    # No `else`. This used to state "No graders are recorded against this thread; there is nothing
    # to score" -- a confident negative, twice wrong. It fired over six unscored clauses at a split
    # (fixed 0.2.6 by following `from:`), and it answers a question a product thread never asked:
    # a service migration has no graders and needs no sentence saying so. Silence is the honest
    # output for "nothing found".
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
    ap.add_argument(
        "--deployed",
        action="store_true",
        help="this session redeployed the plugin, so the next one owes a restart and the step-6 "
             "gate. WITHOUT this, no version, no gate and no restart framing is emitted -- a "
             "thread that deployed nothing must not be told to deploy. Never inferred.",
    )
    args = ap.parse_args(argv)

    try:
        vault = vault_config.resolve(args.vault)
        tdir = thread_dir(vault, args.thread)
        tree = Path(args.tree).resolve() if args.tree else tree_root()
        cache = Path(args.cache).expanduser()

        if not args.deployed:
            # No deploy, no claim. The tree-vs-installed comparison exists so the next session does
            # not MEASURE a stale copy; a thread that is not measuring this machinery has nothing
            # to be stale about, and refusing there would block every product handoff on the state
            # of a repo it never touches.
            body = compose(
                vault, tdir, None, graders_for(vault, tdir), newest_orientation(tdir)
            )
            print("```")
            print(body)
            print("```")
            return 0

        inst = installed_dir(cache)
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

        body = compose(
            vault, tdir, version, graders_for(vault, tdir), newest_orientation(tdir),
            tree=tree, cache=cache,
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
