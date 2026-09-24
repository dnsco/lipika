#!/usr/bin/env python3
"""archive-thread -- move a finished thread into `workstreams/archive/`, through Obsidian, or refuse.

WHY THROUGH OBSIDIAN
  A bare wikilink resolves by file name and survives a move, but a path-qualified one --
  `[[workstreams/<thread>/dumps/x]]` -- does not, and `mv` or `git mv` would leave it dangling
  silently. `obsidian move` rewrites inbound links as part of the move. It moves one file per call
  and has no folder move, so this makes one call per file, then removes the emptied folders.

WHAT IT REFUSES, MOVING NOTHING
  exit 3  Obsidian is not on PATH, not running, or its CLI is disabled
  exit 4  Obsidian is serving a different vault than the one resolved -- it would rewrite links in
          the wrong tree and report success. The normal state inside a git worktree.
  exit 5  no such thread
  exit 6  the destination exists, the path is already under archive/, or the thread has
          uncommitted changes, which a move would carry off without a record
  exit 7  a move failed partway. What moved is listed and not rolled back: git shows the partial
          state, and a rollback through the failing tool might not.

  exit 0  moved. Prints both halves of the rename for `lipika vault-commit`. It commits nothing.

USAGE
  lipika archive-thread <thread>            # <thread> as `lipika threads --all` names it
  lipika archive-thread <thread> --dry-run  # the checks, and the moves it would make
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_config  # noqa: E402


def die(code, *lines):
    for line in lines:
        print(line, file=sys.stderr)
    sys.exit(code)


def obsidian(vault, *cmd):
    if shutil.which("obsidian") is None:
        die(3, "REFUSING: the `obsidian` binary is not on PATH, so links could not follow the move.",
               "  Install the Obsidian CLI and have Obsidian running on this vault. Nothing was moved.")
    try:
        p = subprocess.run(["obsidian", *cmd], capture_output=True, text=True, timeout=30, cwd=vault)
    except subprocess.TimeoutExpired:
        die(3, f"REFUSING: `obsidian {cmd[0]}` timed out after 30s -- treat it as unavailable.")
    blob = f"{p.stdout}\n{p.stderr}"
    if "not enabled" in blob:
        die(3, "REFUSING: the Obsidian CLI is DISABLED, which is its default.",
               "  Enable it: Obsidian > Settings > General > Advanced > command line interface.")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("thread", help="as `lipika threads --all` names it, e.g. 2026-08-21-x or parked/x")
    ap.add_argument("--dry-run", action="store_true", help="check and list the moves; move nothing")
    vault_config.add_argument(ap)
    args = ap.parse_args(argv)

    vault = Path(vault_config.resolve_or_exit(args.vault, tool="archive-thread").path).resolve()
    name = args.thread.strip("/")
    if name.startswith("workstreams/"):
        name = name[len("workstreams/"):]
    if name.split("/")[0] == "archive":
        die(6, f"REFUSING: {name} is already under archive/.")
    src = vault / "workstreams" / name
    if not src.is_dir():
        die(5, f"no such thread: workstreams/{name}")
    dest = vault / "workstreams" / "archive" / src.name
    if dest.exists():
        die(6, f"REFUSING: {dest.relative_to(vault)} already exists; nothing was moved.")

    dirty = subprocess.run(["git", "-C", str(vault), "status", "--porcelain", "--", str(src)],
                           capture_output=True, text=True)
    if dirty.returncode:
        die(6, f"REFUSING: cannot read git status for {name}: {dirty.stderr.strip()}")
    if dirty.stdout.strip():
        die(6, f"REFUSING: workstreams/{name} has uncommitted changes. Commit or remove them first,",
               "  or the move carries work off without a record. Nothing was moved.",
               *("  " + line for line in dirty.stdout.splitlines()))

    indexed = None
    for line in obsidian(vault, "vault").stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[0].strip() == "path":
            indexed = Path(parts[1].strip()).expanduser().resolve()
    if indexed is None:
        die(3, "REFUSING: `obsidian vault` returned no path; treat the CLI as unavailable.")
    if indexed != vault:
        die(4, "REFUSING: Obsidian is serving a different vault than the one resolved.",
               f"  Obsidian serves : {indexed}",
               f"  resolved vault  : {vault}",
               "  It would rewrite links in that tree and report success. Nothing was moved.")

    files = sorted(p for p in src.rglob("*") if p.is_file() and p.name != ".DS_Store")
    moves = [(p.relative_to(vault).as_posix(), (dest / p.relative_to(src)).relative_to(vault).as_posix())
             for p in files]
    if args.dry_run:
        for a, b in moves:
            print(f"would move  {a}  ->  {b}")
        return 0

    done = []
    for a, b in moves:
        (vault / b).parent.mkdir(parents=True, exist_ok=True)
        p = obsidian(vault, "move", f"path={a}", f"to={b}")
        if p.returncode or not (vault / b).is_file() or (vault / a).exists():
            die(7, f"FAILED moving {a}: {(p.stderr or p.stdout).strip()[:200]}",
                   f"  {len(done)} of {len(moves)} moved before it; nothing rolled back:",
                   *(f"  moved {x}" for x in done))
        done.append(a)

    for d in sorted((p for p in src.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    if src.is_dir() and not any(p for p in src.iterdir() if p.name != ".DS_Store"):
        shutil.rmtree(src)

    rel_src, rel_dest = src.relative_to(vault).as_posix(), dest.relative_to(vault).as_posix()
    print(f"moved {len(done)} file(s) through Obsidian: {rel_src} -> {rel_dest}")
    print(f"commit both halves:  lipika vault-commit -m \"archive {src.name}\" -- {rel_src} {rel_dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
