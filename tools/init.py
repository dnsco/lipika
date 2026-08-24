#!/usr/bin/env python3
"""
Init — seed a new vault and register it, in one command.

WHY IT EXISTS
  Seeding a vault was three README steps run once per vault ever: make the directories, copy two
  templates, write a config entry. Run-once sequences are exactly the ones that get a step wrong,
  and this one has: a vault whose `.gitignore` was never copied tracked its pass log, which turns
  every pair of parallel passes into a merge conflict. A command cannot skip a step.

WHAT IT DOES NOT DO
  It does not write conventions of its own. `CLAUDE.md` comes from the template verbatim, because
  a second author of the same rules is a second thing to keep true. The seeded README is six lines
  and says so -- a thin map is what the conventions ask for, and an annotated one becomes a second
  frontier that silently drifts.

IDEMPOTENT, AND IT WILL NOT CLOBBER
  Existing files are left alone and reported as `kept`. That makes it safe to re-run after the
  templates change, and safe on a vault that predates it -- which is the only way an existing
  vault gets a missing entry.

USAGE
  lipika init <path> [--name NAME] [--default] [--no-git]

    <path>        where the vault lives; created if missing
    --name NAME   the key it gets in ~/.config/lipika/config.json (default: the directory name)
    --default     make it the default vault
    --no-git      skip `git init` (for a directory already inside a repo)

EXIT CODES
  0  seeded, or already complete
  1  the path exists and is a file, or a config entry names a different path
  5  bad invocation
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import vault_config

TIERS = {
    "workstreams": "one question being answered each; a thread gets a folder, a folder-note, dumps/ and orientation/",
    "epics": "a large effort actually happening. live / parked / finished. Cites its threads",
    "grand-plans": "long-horizon direction the workstreams serve. A standing want, with no liveness",
    "architecture": "how a system is put together. The owner's; agents write the traces behind it",
    "reference": "subsystem maps traced from source, cross-workstream. No status, no next-moves",
    "values": "evergreen principles the docs lean on by name",
    "sources": "raw verbatim inputs — transcripts, clipped articles. Append-only",
    "external": "artifacts written for an outside audience. Append-only",
}
# No `done/`. The task tier and its closure ceremony were retired at dnsco/lipika#8 --
# splitting a thread replaces all of it, and a thread that stopped is simply not listed
# as live. Seeding `done/` into a NEW vault taught the retired shape on the first command
# anyone runs. An EXISTING `done/` stays where it is: records never move.

README = """---
type: moc
status: active
tags: [vault, index]
---

# {name} — vault map

What lives here and where. **[[CLAUDE]]** is the operating manual: conventions, and who may write.

**This map carries no state.** A thread's state lives in its newest `orientation/` document — go
there for "where are we". An annotated table of contents becomes a second frontier and silently
drifts; one line per document is the whole design.

**Nothing here closes.** A workstream has no status field: the date it last accrued is the whole
answer, and a thread that stopped is simply not listed as live. Only an epic carries state.

## Workstreams

_(nothing yet — the first `context-dump` will create one)_
"""


def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def main(argv):
    ap = argparse.ArgumentParser(
        description="Seed a new knowledge-base vault and register it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Re-running is safe: existing files are kept, never overwritten.")
    ap.add_argument("path")
    ap.add_argument("--name", default=None, help="config key (default: the directory name)")
    ap.add_argument("--default", action="store_true", help="make it the default vault")
    ap.add_argument("--no-git", action="store_true")
    a = ap.parse_args(argv)

    root = Path(a.path).expanduser().absolute()
    if root.exists() and not root.is_dir():
        print(f"{root} exists and is not a directory", file=sys.stderr)
        return 1
    name = a.name or root.name

    templates = Path(__file__).resolve().parent.parent / "templates"
    for t in ("vault-CLAUDE.md.template", "vault-gitignore.template"):
        if not (templates / t).is_file():
            print(f"missing template {templates / t}", file=sys.stderr)
            return 1

    made, kept = [], []
    root.mkdir(parents=True, exist_ok=True)
    for tier, why in TIERS.items():
        d = root / tier
        (made if not d.exists() else kept).append(f"{tier}/")
        d.mkdir(exist_ok=True)
        keep = d / ".gitkeep"
        if not any(p for p in d.iterdir()) and not keep.exists():
            keep.write_text("")

    for src, dst in (("vault-CLAUDE.md.template", "CLAUDE.md"),
                     ("vault-gitignore.template", ".gitignore")):
        target = root / dst
        if target.exists():
            kept.append(dst)
            continue
        target.write_text((templates / src).read_text())
        made.append(dst)

    readme = root / "README.md"
    if readme.exists():
        kept.append("README.md")
    else:
        readme.write_text(README.format(name=name))
        made.append("README.md")

    if not a.no_git and not (root / ".git").exists():
        inside = run(["git", "rev-parse", "--show-toplevel"], cwd=str(root))
        if inside.returncode:
            r = run(["git", "init", "-q"], cwd=str(root))
            made.append("git repo" if not r.returncode else f"git init FAILED: {r.stderr.strip()}")
        else:
            kept.append(f"git repo ({inside.stdout.strip()})")

    cfg_path = vault_config.CONFIG_PATH
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
        except json.JSONDecodeError as e:
            print(f"{cfg_path} is not valid JSON ({e}); fix it before seeding", file=sys.stderr)
            return 1
    vaults = cfg.setdefault("vaults", {})
    existing = vaults.get(name)
    if existing and Path(existing).expanduser().absolute() != root:
        print(f"config already maps {name!r} to {existing}, which is not {root}.\n"
              f"pass --name to register this one under a different key", file=sys.stderr)
        return 1
    if existing:
        kept.append(f"config entry {name}")
    else:
        vaults[name] = str(root)
        made.append(f"config entry {name}")
    if a.default or "default" not in cfg:
        cfg["default"] = name
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")

    print(f"vault  {root}\nname   {name}" + ("  (default)" if cfg["default"] == name else ""))
    if made:
        print("created  " + ", ".join(made))
    if kept:
        print("kept     " + ", ".join(kept))
    print("\nCLAUDE.md is the template verbatim. Edit it in place — a vault's copy is SUPPOSED to\n"
          "diverge, naming your real repos and your dated evidence, and it is never ported back.")
    print()
    d = run([sys.executable, str(Path(__file__).resolve().parent / "doctor.py")])
    sys.stdout.write(d.stdout)
    sys.stderr.write(d.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
