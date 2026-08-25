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

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIN = HERE.parent / "bin" / "lipika"


def installed_vs_tree():
    """Is the installed plugin the checkout? Returns a problem count.

    THE ONE FAILURE THE LOOP CANNOT OTHERWISE CATCH. What runs is the installed snapshot, so
    editing the tree changes nothing until a deploy -- and at an UNCHANGED version `install`,
    `update` and `marketplace update` all report success and copy nothing (measured 2026-08-24,
    all three). So a forgotten deploy is silent, and the next round measures the previous one and
    reports clean. It cost three days once.

    Until now this comparison existed only as a shell loop pasted into a handoff prompt and run by
    hand at the top of a session. A rule with an exit code fails loudly where a rule a human must
    remember does not fail at all.
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

    tree = HERE.parent
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
        print(f"  STALE    installed {inst.name} differs from the tree in: {', '.join(stale)}")
        print("           what runs is the installed copy, so these edits are not live. Bump both "
              "manifests and deploy.")
        return 1
    print(f"  ok       installed {inst.name} IS the tree (skills, agents, tools, bin)")
    return 0


def main():
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
        v = vault_config.resolve()
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

    problems += installed_vs_tree()

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
