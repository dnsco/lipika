#!/usr/bin/env python3
"""
Doctor -- is this install wired up, and can it find what it needs?

WHY THIS FILE EXISTS
  Two locations have to be right before anything works, and they are resolved by different things
  for a reason that is easy to forget:

    where LIPIKA is    -> PATH, resolved by the SHELL. It cannot come from the config, because
                          reading the config means running Lipika. Any config-based answer to
                          "where are the tools" is circular.
    where the VAULT is  -> the config, resolved by a TOOL. See vault_config.

  Measured 2026-08-20: an env var is the wrong answer for the first. `CLAUDE_PLUGIN_ROOT` -- the
  one the harness documents for exactly this -- is EMPTY in the Bash environment of a subagent
  spawned from a plugin, while plugin `bin/` directories are on PATH. So PATH is the mechanism
  with evidence behind it, and this tool checks it rather than assuming it.

  Without this, a definition calling a `lipika` that is not on PATH fails with `command not
  found` -- which says nothing about which of the two wirings is missing.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIN = HERE.parent / "bin" / "lipika"


def installed_vs_tree(tree_arg=None):
    """Is the installed plugin the checkout? Returns a problem count.

    THE ONE FAILURE THE LOOP CANNOT OTHERWISE CATCH. What runs is the installed snapshot, so
    editing the tree changes nothing until a deploy -- and at an UNCHANGED version `install`,
    `update` and `marketplace update` all report success and copy nothing (measured 2026-08-24,
    all three). So a forgotten deploy is silent, and the next round measures the previous one and
    reports clean. It cost three days once.

    Until now this comparison existed only as a shell loop pasted into a handoff prompt and run by
    hand at the top of a session. A rule with an exit code fails loudly where a rule a human must
    remember does not fail at all.

    AND IT SPENT 0.3.0 UNABLE TO FAIL. `tree` was `HERE.parent`, so run from the installed snapshot
    -- which is how the plugin runs -- this compared that snapshot against itself. Measured
    2026-08-26: `ok installed 0.3.0 IS the tree` printed while the checkout differed in six files
    and was missing tools/threads.py, one line after this same run printed `WARNING that is NOT
    this checkout`. It had already computed the fact and did not use it.

    The second operand now comes from `handoff_prompt.checkout_root()` -- PATH, then a `.git` test --
    and its path is PRINTED, because a comparison whose second operand is unstated cannot be
    audited by the reader it was printed for.
    """
    try:
        sys.path.insert(0, str(HERE))
        import handoff_prompt as hp
    except Exception as e:
        print(f"  note     cannot compare installed vs tree: {e}")
        return 0

    try:
        inst = hp.installed_dir(hp.DEFAULT_CACHE.expanduser())
    except Exception:
        print("  note     no installed plugin found; this is a dev checkout, nothing to compare")
        return 0

    tree = Path(tree_arg).resolve() if tree_arg else hp.checkout_root()
    if tree is None:
        print("  MISSING  no git checkout found to compare the installed plugin against")
        print(f"           installed: {inst}")
        print("           `lipika` on PATH is inside the snapshot, which cannot be stale against "
              "itself.")
        print("           pass --tree <checkout>, or run this from a shell where `lipika` is the "
              "checkout's.")
        return 1
    if tree.resolve() == inst.resolve():
        print(f"  MISSING  tree and installed are the same directory ({inst})")
        print("           a comparison of a copy against itself cannot fail; pass --tree <checkout>")
        return 1

    declared = hp.manifest_version(tree)
    stale = hp.differing(tree, inst)

    if declared != inst.name:
        print(f"  STALE    tree declares {declared}, installed is {inst.name} -- the tree has not "
              f"been deployed")
        print("           bump BOTH .claude-plugin manifests if they are equal, then deploy; at an "
              "unchanged")
        print("           version every deploy command is a silent no-op")
        return 1
    if stale:
        print(f"  STALE    installed {inst.name} differs from {tree} in: {', '.join(stale)}")
        # The verdict is the same either way -- the snapshot is behind, and other clients read it.
        # The ADVICE is not. Measured 2026-08-27: a `claude -p` subprocess reading a directory
        # source's installLocation was told "these edits are not live" about edits that were live
        # for it, on the same screen where its own base directory said otherwise. Same shape as the
        # 0.3.0 defect -- the run had already computed the fact the sentence needed.
        kind, loc, err = marketplace_entry()
        reads_tree = (
            not err
            and kind == "directory"
            and loc
            and Path(loc).resolve() == tree.resolve()
        )
        if reads_tree:
            print("           these edits ARE live for any process that reads that directory "
                  "source -- deploying")
            print("           is what makes the snapshot agree, not what makes the edits take "
                  "effect. Bump both")
            print("           manifests and deploy.")
        else:
            print("           what runs is the installed copy, so these edits are not live. Bump "
                  "both manifests and deploy.")
        return 1
    print(f"  ok       installed {inst.name} IS {tree} (skills, agents, tools, bin)")
    return 0


MARKETPLACES = Path.home() / ".claude" / "plugins" / "known_marketplaces.json"


def marketplace_entry():
    """(source kind, installLocation, error). Read, never inferred.

    Two callers need this and they need it for different reasons: the source line states it, and the
    STALE advice is only correct for one of the two answers. Inferring it from the tree's path or the
    repo's name would be the ruled-out class one level down.
    """
    import json
    try:
        entry = json.loads(MARKETPLACES.read_text()).get("lipika")
    except (OSError, ValueError) as exc:
        return None, None, f"cannot read the marketplace entry ({MARKETPLACES}): {exc}"
    if not entry:
        return None, None, f"no `lipika` marketplace entry in {MARKETPLACES}"
    return (entry.get("source") or {}).get("source", "?"), entry.get("installLocation", "?"), None


def definition_source(path=None):
    """Where a session would READ definitions from -- which is not what installed_vs_tree measures.

    THE GAP THIS CLOSES. `installed_vs_tree` compares two folders and proves they are equal. That is
    a fact about FILES. It says nothing about which copy a running process loads, and on 2026-08-27
    the two answers differed by client: a fresh `claude -p` subprocess reported its pickup skill's
    base directory as the CHECKOUT, measured twice from two cwds, while the app session that spawned
    it reported a cache snapshot -- one already marked .orphaned_at.

    The cause is the marketplace entry, so that is what this reads rather than assumes: a `directory`
    source's installLocation IS the working tree. CLAUDE.md's stated payoff for installing as a
    plugin -- "an unmerged branch is no longer silently live" -- does not hold for a client that
    reads it, and a gate that stays silent about that is true about what it measured and read as a
    claim about something else.

    It never claims which copy THIS session loaded; a separate process cannot know that, and the
    probe step is what answers it. And it never sets the exit code: a directory source is a
    deliberate setup, not a fault.
    """
    kind, loc, err = marketplace_entry()
    if err:
        print(f"  note     {err}")
        print("           so where a session reads definitions from is UNSTATED, which is the "
              "thing this checks")
        return
    print(f"  ok       definitions source -> {kind}: {loc}")
    if kind == "directory":
        print("           a directory source IS the working tree, so a process that reads it runs "
              "the tree as it")
        print("           stands -- uncommitted edits included. The version number describes the "
              "snapshot, not")
        print("           necessarily what a given client loaded; the probe step is what tells you "
              "which.")


def main(argv=None):
    # It parsed NOTHING until now, which made `lipika doctor --vault <path>` a hard error while
    # `vault-normalize` step 1 said to pass --vault on every command. Recorded as a live landmine
    # 2026-08-25; closed here because the same pass had to add --tree anyway.
    ap = argparse.ArgumentParser(description="is this install wired up, and can it find what it needs")
    ap.add_argument("--vault", help="vault to resolve instead of the configured one")
    ap.add_argument(
        "--tree",
        help="checkout to compare the installed plugin against; defaults to whatever `lipika` on "
             "PATH resolves to, and only if that is a git checkout",
    )
    args = ap.parse_args(argv)

    problems = 0

    found = shutil.which("lipika")
    if found:
        print(f"  ok       `lipika` on PATH -> {found}")
        if Path(found).resolve() != BIN.resolve():
            print(f"  WARNING  that is NOT this checkout ({BIN}) -- you may be running another "
                  f"install's definitions while editing these")
            problems += 1
    else:
        problems += 1
        print("  MISSING  `lipika` is not on PATH, so a definition calling it by name fails with "
              "`command not found`.")
        print("           A plugin install puts bin/ on PATH by itself. For a dev checkout:")
        print(f'             export PATH="{BIN.parent}:$PATH"')

    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        print("  note     CLAUDE_PLUGIN_ROOT is set here, but it is empty in a subagent's shell "
              "(measured) -- do not write it into a definition")

    try:
        sys.path.insert(0, str(HERE))
        import vault_config
        v = vault_config.resolve(args.vault)
        print(f"  ok       vault -> {v.path}  (via {v.source})")
        print(f"           frozen tiers: {', '.join(v.frozen_tiers)}")
        if not (v.path / ".git").exists():
            print("  WARNING  that vault is not a git repository, so nothing there is recoverable")
            problems += 1
    except Exception as e:
        problems += 1
        print(f"  MISSING  no vault resolved: {e}")
        print(f"           write ~/.config/lipika/config.json, or pass --vault, or set "
              f"$LIPIKA_VAULT")

    problems += installed_vs_tree(args.tree)
    definition_source()

    for name in ("git", "python3"):
        p = shutil.which(name)
        print(f"  {'ok      ' if p else 'MISSING '} {name}{'' if p else ' -- required'}")
        problems += 0 if p else 1
    gh = shutil.which("gh")
    print(f"  {'ok      ' if gh else 'note    '} gh"
          f"{'' if gh else ' -- absent; marker verification against GitHub will not run'}")

    print()
    if problems:
        print(f"{problems} problem(s). Nothing above is fatal to reading a vault, but a MISSING "
              "line means some role will fail at its first call.")
        return 1
    print("wired: tools reachable by name, vault resolved, git present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
