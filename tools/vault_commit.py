#!/usr/bin/env python3
"""
Vault commit helper — refuses a bare commit and a half-rename.

WHY
  Three commit rules exist here, all learned the hard way, and all of them are prose today:

  1. NEVER a bare `git commit`. It takes the whole index, so it captures whatever another
     session in the same repo has staged -- and if you later switch branches, their work
     vanishes from their working tree. Always `git commit -m "..." -- <paths>`.
  2. BOTH HALVES of a rename in one pathspec list. Commit only the new half and the old file
     stays on the branch; commit only the old and the doc disappears.
  3. RE-CHECK CLEANLINESS AT COMMIT TIME. A check from before you started writing proves
     nothing about now.

  Measured 2026-08-18: an orchestrator that had bundled a doc-body edit into the same write as
  a shared-surface edit could not then split them, because `git commit -- <path>` cannot split
  hunks within a file. It un-applied the sentence, committed, and re-applied it -- two extra
  writes to a live doc to work around its own packaging. This refuses the shapes that lead
  there, and says which rule fired.

WHAT IT REFUSES
  - no pathspecs at all (the bare commit)
  - a pathspec naming one half of a detected rename without the other
  - a message that is empty, or a subject line over --subject-max (default 72)
  - staged changes outside the pathspecs you named, unless --allow-foreign-index
  - an orientation that repeats a section or an item (`orientation_audit.shape_faults`)

USAGE
  python3 tools/vault_commit.py -m "message" -- <paths...>
  python3 tools/vault_commit.py -m "message" --vault ~/vault --dry-run -- <paths...>
  python3 tools/vault_commit.py -m "msg" --trailer "Co-Authored-By: X <y@z>" -- <paths...>

    exit 0   committed (or --dry-run printed the plan)
    exit 2   a rule refused it -- the message says which
    exit 3   nothing to commit under those pathspecs
    exit 5   bad invocation
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orientation_audit                          # noqa: E402


def git(vault, *args, check=False):
    r = subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True)
    if check and r.returncode != 0:
        print((r.stderr or r.stdout).strip(), file=sys.stderr)
        sys.exit(2)
    return r.returncode, r.stdout


def git_full(vault, *args):
    """Like git(), but returns stderr too — printing only stdout hid a failure's reason."""
    r = subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def die(code, *lines):
    for l in lines:
        print(l, file=sys.stderr)
    sys.exit(code)


def vault_spec(spec, vault, cwd=None):
    """A pathspec as the vault-relative path `git status` reports, or None if it is outside.

    Git's own rule: a relative path is relative to the current directory when that is inside
    the repo, and to the repo root otherwise. Absolute paths are relativised. Existence is
    never consulted, because the old half of a move no longer exists.

    THE DEFECT THIS FIXES: specs were compared to `git status` verbatim, so an absolute path,
    or one relative to a subdirectory of the vault, matched nothing and this reported
    "nothing to commit". Reproduced 2026-09-30 with 8 archive-move pathspecs.
    """
    cwd = Path(cwd or os.getcwd()).resolve()
    p = Path(spec)
    if not p.is_absolute():
        p = (cwd if cwd == vault or vault in cwd.parents else vault) / p
    try:
        rel = p.resolve().relative_to(vault).as_posix()
    except ValueError:
        return None
    return "" if rel == "." else rel


def covered(path, specs):
    p = Path(path)
    for s in specs:
        if path == s or str(p).startswith(s.rstrip("/") + "/"):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    if "--self-test" in sys.argv[1:]:
        return self_test()
    ap.add_argument("-m", "--message", required=True)
    ap.add_argument("--vault", default=None,
                    help="vault path or a name from ~/.config/lipika/config.json; "
                         "default: $LIPIKA_VAULT, the config, then this checkout")
    ap.add_argument("--trailer", action="append", default=[])
    ap.add_argument("--subject-max", type=int, default=72)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-foreign-index", action="store_true",
                    help="proceed even if changes are staged outside your pathspecs")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()
    import vault_config
    args.vault = str(vault_config.resolve_or_exit(args.vault, "vault_commit"))

    vault = Path(args.vault).expanduser().resolve()
    raw = [p for p in args.paths if p != "--"]
    specs = [vault_spec(p, vault) for p in raw]
    outside = [r for r, s in zip(raw, specs) if s is None]
    if outside:
        die(2, "REFUSED: pathspec(s) outside the vault:", *[f"  {p}" for p in outside],
            f"  vault: {vault}")
    if "" in specs:
        die(2, "REFUSED: a pathspec names the whole vault, which is a bare commit by another name.")

    if not specs:
        die(2,
            "REFUSED: no pathspecs.",
            "A bare commit takes the whole index, including anything another session in this",
            "repo has staged. Name the paths:  vault_commit.py -m \"...\" -- <paths>")

    subject = args.message.splitlines()[0]
    if not subject.strip():
        die(2, "REFUSED: empty subject line.")
    if len(subject) > args.subject_max:
        die(2, f"REFUSED: subject is {len(subject)} chars, over --subject-max {args.subject_max}.",
               f"  {subject}")

    # -uall, because plain --porcelain collapses a wholly-new directory to ONE entry naming the
    # directory. A pathspec for a file inside it then matches nothing and this tool reports
    # "nothing to commit under those pathspecs" -- a silent no-op on a real write. Measured
    # 2026-08-21 writing the first document into a workstream's new reference/.
    code, status = git(vault, "status", "--porcelain", "-uall")
    if code != 0:
        die(5, f"not a git repository: {vault}")

    entries = []
    for line in status.splitlines():
        if not line.strip():
            continue
        x, y, rest = line[0], line[1], line[3:]
        if " -> " in rest:
            old, new = rest.split(" -> ", 1)
            entries.append((x + y, old.strip('"'), new.strip('"')))
        else:
            entries.append((x + y, rest.strip('"'), None))

    # Rename detection against the index, so a staged R shows both halves.
    code, staged = git(vault, "diff", "--cached", "--name-status", "-M")
    renames = []
    for line in staged.splitlines():
        parts = line.split("\t")
        if parts and parts[0].startswith("R") and len(parts) >= 3:
            renames.append((parts[1], parts[2]))
    # Also pair an unstaged delete with an untracked add of the same name -- the shape a move
    # leaves when git has not been told. Only a name that appears ONCE on each side pairs:
    # every thread has a gotchas.md, so moving several threads made every delete pair with every
    # thread's addition, and committing one thread was refused as half a rename.
    from collections import Counter
    dels = [p for st, p, _ in entries if "D" in st]
    adds = [p for st, p, _ in entries if st.strip() in ("??", "A")]
    dn, an = Counter(Path(d).name for d in dels), Counter(Path(a).name for a in adds)
    for d in dels:
        for a in adds:
            name = Path(d).name
            if Path(a).name == name and d != a and dn[name] == 1 and an[name] == 1:
                renames.append((d, a))

    for old, new in renames:
        has_old, has_new = covered(old, specs), covered(new, specs)
        if has_old != has_new:
            missing = old if has_new else new
            die(2,
                "REFUSED: half a rename.",
                f"  {old}  ->  {new}",
                f"  your pathspecs cover {'the new half' if has_new else 'the old half'} only.",
                f"  add:  {missing}",
                "",
                "Committing one half leaves the other behind: the old file survives on the",
                "branch, or the doc disappears. Both halves go in one pathspec list.")

    changed_in_specs = [p for st, p, new in entries
                        if covered(new or p, specs) or covered(p, specs)]
    if not changed_in_specs:
        die(3, "nothing to commit under those pathspecs:", *[f"  {s}" for s in specs])

    for p in changed_in_specs:
        f = vault / p
        if p.endswith(".md") and f.parent.name == "orientation" and f.is_file():
            faults = orientation_audit.shape_faults(f.read_text(errors="replace"))
            if faults:
                die(2, f"REFUSED: {p} repeats itself.", *[f"  {m}" for _, m in faults], "",
                    "Rebuild it from `lipika orientation-carry`, not by slicing the old one.")

    if not args.allow_foreign_index:
        foreign = [p for st, p, new in entries
                   if st[0] not in (" ", "?") and not (covered(new or p, specs) or covered(p, specs))]
        if foreign:
            die(2,
                f"REFUSED: {len(foreign)} path(s) are STAGED outside your pathspecs.",
                *[f"  {p}" for p in foreign[:10]],
                "",
                "They may belong to another session in this repo. `git commit -- <paths>` will",
                "not take them, but their presence means the index is not yours alone —",
                "re-check before writing. Pass --allow-foreign-index if you know they are yours.")

    message = args.message
    for t in args.trailer:
        if t not in message:
            message = message.rstrip() + "\n\n" + t if "\n\n" not in message[-200:] else message.rstrip() + "\n" + t

    cmd = ["commit", "-m", message, "--", *specs]
    if args.dry_run:
        print("would run:  git " + " ".join(
            f'"{c}"' if " " in c or "\n" in c else c for c in cmd))
        print("\ncovered changes:")
        for p in changed_in_specs:
            print(f"  {p}")
        if renames:
            print("\nrenames, both halves present:")
            for o, n in renames:
                print(f"  {o} -> {n}")
        return 0

    # `git commit -- <paths>` only takes TRACKED modifications; an untracked path makes it fail
    # with "did not match any file(s) known to git". Staging exactly the paths you named is safe
    # in a way `git add -A` is not -- it cannot pick up another session's work, which is the
    # whole reason pathspecs are mandatory here.
    untracked = [p for st, p, new in entries
                 if st.strip() == "??" and (covered(new or p, specs) or covered(p, specs))]
    if untracked:
        acode, aout, aerr = git_full(vault, "add", "--", *untracked)
        if acode != 0:
            die(2, "could not stage the new files:", aerr.strip() or aout.strip())

    code, out, err = git_full(vault, *cmd)
    if out.strip():
        print(out.strip())
    if code != 0:
        # Printing only stdout hid the reason entirely on the first failure of this tool.
        print((err or "git commit failed with no message").strip(), file=sys.stderr)
        return 2
    _, head = git(vault, "log", "-1", "--format=%h %s")
    print(f"\ncommitted {head.strip()}")
    _, after = git(vault, "status", "--porcelain")
    if after.strip():
        print(f"tree still has {len(after.strip().splitlines())} uncommitted path(s) — expected if "
              f"you are committing one scope at a time.")
    return 0


def self_test():
    """Four thread moves, committed with their 8 pathspecs in each form a caller reaches for.

    Every form must cover all 32 status entries: 16 deletes, 16 additions. Before `vault_spec`, the absolute and the
    subdirectory-relative forms reported "nothing to commit" (exit 3).
    """
    import tempfile
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        def sh(*a, cwd=root):
            return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True)
        sh("init", "-q")
        names = [f"2026-09-0{i}-t{i}" for i in range(1, 5)]
        for n in names:
            for f in (f"{n}.md", "gotchas.md", "dumps/x.md", "orientation/o.md"):
                (root / "workstreams" / n / f).parent.mkdir(parents=True, exist_ok=True)
                (root / "workstreams" / n / f).write_text(f"# {n} {f}\n")
        sh("add", "-A")
        sh("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
        (root / "workstreams" / "archive").mkdir()
        for n in names:
            (root / "workstreams" / n).rename(root / "workstreams" / "archive" / n)

        pairs = [(f"workstreams/{n}", f"workstreams/archive/{n}") for n in names]
        forms = {
            "vault-relative": (root, [x for pr in pairs for x in pr]),
            "absolute": (Path("/"), [str(root / x) for pr in pairs for x in pr]),
            "relative to workstreams/": (root / "workstreams",
                                         [x.removeprefix("workstreams/") for pr in pairs for x in pr]),
        }
        for label, (cwd, specs) in forms.items():
            r = subprocess.run([sys.executable, os.path.abspath(__file__), "--vault", str(root),
                                "--dry-run", "-m", "archive", "--", *specs],
                               cwd=cwd, capture_output=True, text=True)
            got = r.stdout.split("covered changes:")[-1].split("renames")[0].split()
            if r.returncode != 0 or len(got) != 32:
                failures.append(f"{label}: exit {r.returncode}, {len(got)} of 32 covered\n"
                                f"{r.stdout}{r.stderr}")
        # One thread of the four, alone. Every thread has a gotchas.md, so pairing by name
        # alone matched this thread's deletes to the other threads' additions and refused it
        # as half a rename.
        one = [f"workstreams/{names[0]}", f"workstreams/archive/{names[0]}"]
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--vault", str(root),
                            "--dry-run", "-m", "one", "--", *one], capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"one thread of four moved: exit {r.returncode}, expected 0\n{r.stderr}")

        # Its red partner: a single real move, one half named, must still be refused.
        (root / "lone.md").write_text("lone\n")
        sh("add", "lone.md")
        sh("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "lone")
        (root / "grand-plans").mkdir()
        (root / "lone.md").rename(root / "grand-plans" / "lone.md")
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--vault", str(root),
                            "--dry-run", "-m", "half", "--", "grand-plans/lone.md"],
                           capture_output=True, text=True)
        if r.returncode != 2 or "half a rename" not in r.stderr:
            failures.append(f"a lone move with one half named must be refused, got {r.returncode}")

        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--vault", str(root),
                            "--dry-run", "-m", "x", "--", "/etc/hosts"],
                           capture_output=True, text=True)
        if r.returncode != 2:
            failures.append(f"a path outside the vault must be refused (exit 2), got {r.returncode}")
    for f in failures:
        print("FAIL", f, file=sys.stderr)
    print("self-test: " + ("FAILED" if failures else
                           "every pathspec form covers 32 of 32; one thread of four commits; a lone half-move is refused"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
