#!/usr/bin/env python3
"""Tests for `lipika archive-thread`: moving a finished thread through Obsidian, so links follow.

Run `python3 evals/archive/test_archive_thread.py`. Exit 0 all pass, 1 any fail.

Obsidian cannot run in a fixture, so a fake `obsidian` on PATH stands in: it answers `vault` with a
path and performs `move path=... to=...`, logging each call. What this proves is that the tool moves
EVERY file through Obsidian -- which is what keeps links true -- and refuses, moving nothing, when
Obsidian is absent, serving another vault, or the move would clobber or carry uncommitted work.
That Obsidian repairs the links is Obsidian's behaviour, not tested here.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"
T = "2026-08-21-old"

FAKE = r'''#!/usr/bin/env python3
import os, shutil, sys
log = os.environ["FAKE_OBSIDIAN_LOG"]
args = sys.argv[1:]
with open(log, "a") as fh:
    fh.write(" ".join(args) + "\n")
if args == ["vault"]:
    print("name\tfixture")
    print("path\t" + os.environ["FAKE_OBSIDIAN_VAULT"])
    sys.exit(0)
if args and args[0] == "move":
    kv = dict(a.split("=", 1) for a in args[1:])
    root = os.environ["FAKE_OBSIDIAN_VAULT"]
    src, dst = os.path.join(root, kv["path"]), os.path.join(root, kv["to"])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    print("Moved: " + kv["path"] + " -> " + kv["to"])
    sys.exit(0)
print("unknown command", file=sys.stderr)
sys.exit(1)
'''

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def git(vault, *args):
    return subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True)


FILES = {
    f"{T}.md": "# The question the old thread answered\n",
    "dumps/2026-08-21-120000-first.md": "# first\n",
    "orientation/2026-08-21-130000.md": "## Live items\n",
    "gotchas.md": "# Warnings\n",
}


def fixture(d):
    vault = Path(d) / "vault"
    ws = vault / "workstreams" / T
    for rel, body in FILES.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(body)
    (vault / "README.md").write_text(f"- [[{T}]]\n")
    git(vault, "init", "-q")
    git(vault, "add", "-A")
    git(vault, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture")
    return vault, ws


def bindir(d, with_obsidian=True):
    b = Path(d) / ("bin" if with_obsidian else "bin-bare")
    b.mkdir()
    os.symlink(shutil.which("git"), b / "git")
    if with_obsidian:
        (b / "obsidian").write_text(FAKE)
        (b / "obsidian").chmod(0o755)
    return b


def run(vault, b, served, *args):
    log = Path(vault).parent / "obsidian.log"
    env = dict(os.environ, LIPIKA_TELEMETRY="0", PATH=f"{b}:/usr/bin:/bin",
               FAKE_OBSIDIAN_LOG=str(log), FAKE_OBSIDIAN_VAULT=str(served))
    r = subprocess.run([sys.executable, str(LIPIKA), "archive-thread", *args, "--vault", str(vault)],
                       capture_output=True, text=True, env=env)
    calls = log.read_text().splitlines() if log.exists() else []
    return r, [c for c in calls if c.startswith("move ")]


def unmoved(ws):
    return all((ws / rel).is_file() for rel in FILES)


def main():
    # Green: every file moves through Obsidian, bytes unchanged, git sees pure renames.
    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d)
        r, moves = run(vault, bindir(d), vault, T)
        dest = vault / "workstreams" / "archive" / T
        check("archiving a thread exits 0", r.returncode == 0, f"exit {r.returncode}\n{r.stderr}")
        check("every file moves through `obsidian move`, one call each", len(moves) == len(FILES), moves)
        check("every file arrives with its bytes unchanged",
              all((dest / rel).is_file() and (dest / rel).read_text() == body
                  for rel, body in FILES.items()))
        check("the thread's old folder is gone", not ws.exists())
        git(vault, "add", "-A")
        status = git(vault, "diff", "--cached", "-M", "--name-status").stdout.split("\n")
        status = [s for s in status if s]
        check("git sees only 100% renames", status and all(s.startswith("R100") for s in status), status)
        check("the output names both halves for vault-commit",
              f"workstreams/{T}" in r.stdout and f"workstreams/archive/{T}" in r.stdout, r.stdout)

    # Red: no Obsidian on PATH.
    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d)
        r, moves = run(vault, bindir(d, with_obsidian=False), vault, T)
        check("without Obsidian it refuses with exit 3 and moves nothing",
              r.returncode == 3 and unmoved(ws), f"exit {r.returncode}\n{r.stderr}")

    # Red: Obsidian serving a different vault.
    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d)
        r, moves = run(vault, bindir(d), Path(d) / "elsewhere", T)
        check("when Obsidian serves another vault it refuses with exit 4 and moves nothing",
              r.returncode == 4 and not moves and unmoved(ws), f"exit {r.returncode}\n{r.stderr}")

    # Red: the destination already exists.
    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d)
        (vault / "workstreams" / "archive" / T).mkdir(parents=True)
        r, moves = run(vault, bindir(d), vault, T)
        check("when the destination exists it refuses and moves nothing",
              r.returncode != 0 and not moves and unmoved(ws), f"exit {r.returncode}\n{r.stderr}")

    # Red: uncommitted work inside the thread.
    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d)
        (ws / "dumps" / "2026-08-22-090000-uncommitted.md").write_text("# not yet committed\n")
        r, moves = run(vault, bindir(d), vault, T)
        check("with uncommitted work in the thread it refuses and moves nothing",
              r.returncode != 0 and not moves and unmoved(ws), f"exit {r.returncode}\n{r.stderr}")

    # Red: a thread that does not exist, and one already archived.
    with tempfile.TemporaryDirectory() as d:
        vault, ws = fixture(d)
        r, _ = run(vault, bindir(d), vault, "2026-01-01-nope")
        check("a thread that does not exist is refused", r.returncode != 0, r.stderr)
        r, _ = run(vault, bindir(d), vault, f"archive/{T}")
        check("a path already under archive/ is refused", r.returncode != 0 and unmoved(ws), r.stderr)

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
