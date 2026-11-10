#!/usr/bin/env python3
"""inbox -- a dated record one thread leaves for another, and whether the receiver has absorbed it.

A message is `workstreams/<thread>/inbox/<stamp>-<slug>.md`, or `inbox/<stamp>-<slug>.md` at the
vault root when no live thread owns it. It is a record: written once, never edited, corrected by a
later message. It is ABSORBED when a later dump or orientation of the receiving thread links it;
a vault-inbox message, when any document under `workstreams/` does. Derived, never written down.

CONTRACT
  send   exit 0  written; the path, the `[[link]]` to cite and the commit line are on stdout
         exit 2  body empty, body without a `# title`, or a slug outside [A-Za-z0-9-]
         exit 5  target not found or ambiguous; a dated `--from` that names no thread
         exit 6  target under archive/ or parked/; the basename exists anywhere in the vault
  list   exit 0  nothing pending (a thread with no inbox/ says so)
         exit 1  pending messages, each listed
         exit 5  no such thread, or neither a thread nor --vault-inbox

USAGE
  lipika inbox send [<thread>] --from <thread|text> --slug <slug> [--now YYYY-MM-DD-HHMMSS] < body.md
  lipika inbox <thread>
  lipika inbox --vault-inbox
  lipika inbox --self-test
"""

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lineage       # noqa: E402
import markers       # noqa: E402
import stamp         # noqa: E402
import vault_config  # noqa: E402

CONTAINERS = ("parked", "archive")
SKIP_DIRS = {"obsidian-skills", "node_modules"}
SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")
NOW = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}$")
DATED = re.compile(r"^\d{4}-\d{2}-\d{2}-")
FENCED = re.compile(r"```.*?```|`[^`\n]*`", re.S)
TITLE = re.compile(r"^#\s+(.*)$", re.M)


def die(code, *lines):
    for line in lines:
        print(line, file=sys.stderr)
    sys.exit(code)


def md_files(root):
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS]
        for n in names:
            if n.endswith(".md"):
                yield Path(dirpath) / n


def links(text):
    """Basenames every wikilink in `text` resolves to, lower-cased. Code spans do not link."""
    out = set()
    for t in markers.WIKILINK.findall(FENCED.sub("", text)):
        out.add(t.strip().split("/")[-1].lower())
    return out


def messages(inbox_dir):
    inbox_dir = Path(inbox_dir)
    if not inbox_dir.is_dir():
        return []
    return sorted(p for p in inbox_dir.glob("*.md") if not p.name.startswith("."))


def thread_docs(tdir):
    tdir = Path(tdir)
    return [p for sub in ("dumps", "orientation") for p in sorted((tdir / sub).glob("*.md"))]


def vault_docs(vault_path):
    return list(md_files(Path(vault_path) / "workstreams"))


def pending(inbox_dir, citing_docs):
    """[(message, absorbed_by or None)] for every message in `inbox_dir`."""
    msgs = messages(inbox_dir)
    if not msgs:
        return []
    linked = {}
    for doc in citing_docs:
        for name in links(Path(doc).read_text(errors="replace")):
            linked.setdefault(name, Path(doc))
    return [(m, linked.get(m.stem.lower())) for m in msgs]


def meta(msg):
    text = Path(msg).read_text(errors="replace")
    fm = text[:3000]
    if fm.startswith("---"):
        close = fm.find("\n---", 3)
        fm = fm[:close] if close != -1 else fm
    m = lineage.FROM_LINE.search(fm)
    frm = m.group(1).strip().strip('"') if m else ""
    t = TITLE.search(text[len(fm):] if text.startswith("---") else text)
    return frm, (t.group(1).strip() if t else ""), Path(msg).stem[:10]


def thread_dirs(vault_path):
    """Every thread root as (rel, dir): `name`, or `container/name` under parked/ and archive/."""
    root = Path(vault_path) / "workstreams"
    out = []
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name in CONTAINERS:
            out += [(f"{d.name}/{p.name}", p) for p in sorted(d.iterdir())
                    if p.is_dir() and not p.name.startswith(".")]
        else:
            out.append((d.name, d))
    return out


def resolve_target(vault_path, name):
    """(thread dir, candidates), chosen from the listing of thread roots. A path is never joined,
    so `../x` and `<thread>/dumps` name nothing. One candidate matches; several are ambiguous."""
    name = name.strip().strip("/")
    if name.startswith("workstreams/"):
        name = name[len("workstreams/"):]
    dirs = thread_dirs(vault_path)
    cands = [d for r, d in dirs if r == name or d.name == name]
    if not cands:
        cands = [d for r, d in dirs if d.name.endswith(Path(name).name)]
    return (cands[0] if len(cands) == 1 else None), cands


def rel(vault_path, p):
    return Path(p).relative_to(vault_path).as_posix()


def cmd_send(argv):
    ap = argparse.ArgumentParser(prog="lipika inbox send")
    ap.add_argument("thread", nargs="?", help="the receiving thread; omit for the vault inbox")
    ap.add_argument("--from", dest="sender", required=True, help="the sending thread, or who you are")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--now", help="YYYY-MM-DD-HHMMSS, for tests")
    vault_config.add_argument(ap)
    args = ap.parse_args(argv)
    vault = Path(vault_config.resolve_or_exit(args.vault, tool="inbox").path).resolve()

    if not SLUG.match(args.slug):
        die(2, f"REFUSING: slug {args.slug!r} is not [A-Za-z0-9-]. Nothing was written.")
    if args.now and not NOW.match(args.now):
        die(2, f"REFUSING: --now {args.now!r} is not YYYY-MM-DD-HHMMSS.")
    body = sys.stdin.read().strip()
    if not body:
        die(2, "REFUSING: empty body on stdin. Nothing was written.")
    if not body.startswith("# "):
        die(2, "REFUSING: the body must open with a `# title` line. Nothing was written.")

    if args.thread:
        target, cands = resolve_target(vault, args.thread)
        if target is None and len(cands) > 1:
            die(5, f"REFUSING: {args.thread!r} is ambiguous:", *(f"  {rel(vault, c)}" for c in cands))
        if target is None:
            die(5, f"no such thread: {args.thread}")
        if target.parent.name in CONTAINERS:
            die(6, f"REFUSING: {rel(vault, target)} is {target.parent.name}; it reads no mail. Nothing was written.")
        inbox_dir = target / "inbox"
        to = target.name
    else:
        inbox_dir = vault / "inbox"
        to = "the vault"

    sender = args.sender.strip()
    bracketed = sender.startswith("[[") and sender.endswith("]]")
    bare = sender[2:-2].strip() if bracketed else sender
    thread_shaped = bracketed or bool(DATED.match(bare))
    sdir, scands = resolve_target(vault, bare)
    if thread_shaped and sdir is None:
        if len(scands) > 1:
            die(5, f"REFUSING: --from {sender!r} is ambiguous:", *(f"  {rel(vault, c)}" for c in scands))
        die(5, f"REFUSING: --from {sender!r} looks like a thread and none is named so. "
               "Pass a thread name, or plain text for a sender that is not a thread.")
    if not thread_shaped and sdir is not None and sdir.name != bare:
        sdir = None
    frm = f"[[{sdir.name}]]" if sdir is not None else bare.replace('"', '\\"')

    st = args.now or stamp.stamp(stamp.utc_now())
    name = f"{st}-{args.slug}"
    clash = next((p for p in md_files(vault) if p.stem == name), None)
    if clash is not None:
        die(6, f"REFUSING: a note named {name} exists: {rel(vault, clash)}. Links resolve by basename. "
               "Nothing was written.")

    inbox_dir.mkdir(parents=True, exist_ok=True)
    path = inbox_dir / f"{name}.md"
    try:
        with open(path, "x") as fh:
            fh.write(f"---\ntype: message\nstatus: record\ndate: {st[:10]}\nfrom: \"{frm}\"\n---\n\n{body}\n")
    except FileExistsError:
        die(6, f"REFUSING: {rel(vault, path)} appeared before the write. Nothing was overwritten.")
    r = rel(vault, path)
    subject = f"inbox {to}: {args.slug}"[:72]
    print(f"wrote {r}")
    print(f"cite it as [[{name}]]")
    print(f"commit it:  lipika vault-commit -m \"{subject}\" -- {r}")
    return 0


def report(label, rows, vault):
    pend = [m for m, by in rows if by is None]
    print(f"{label}  {len(rows)} message(s), {len(pend)} pending")
    for m, by in rows:
        frm, title, _ = meta(m)
        state = "PENDING " if by is None else "ABSORBED"
        tail = "" if by is None else f"  by {rel(vault, by)}"
        print(f"  {state}  {m.stem}  from {frm}  {title}{tail}")
    return 1 if pend else 0


def cmd_list(argv):
    ap = argparse.ArgumentParser(prog="lipika inbox", description=__doc__.splitlines()[0])
    ap.add_argument("thread", nargs="?")
    ap.add_argument("--vault-inbox", action="store_true", help="the inbox at the vault root")
    vault_config.add_argument(ap)
    args = ap.parse_args(argv)
    if not args.thread and not args.vault_inbox:
        ap.print_usage(sys.stderr)
        print("inbox: name a thread, or pass --vault-inbox, or `send`", file=sys.stderr)
        return 5
    vault = Path(vault_config.resolve_or_exit(args.vault, tool="inbox").path).resolve()

    if args.vault_inbox:
        d = vault / "inbox"
        if not d.is_dir():
            print("no inbox at the vault root")
            return 0
        return report("inbox/", pending(d, vault_docs(vault)), vault)

    target, cands = resolve_target(vault, args.thread)
    if target is None and len(cands) > 1:
        die(5, f"{args.thread!r} is ambiguous:", *(f"  {rel(vault, c)}" for c in cands))
    if target is None:
        die(5, f"no such thread: {args.thread}")
    d = target / "inbox"
    if not d.is_dir():
        print(f"no inbox in {rel(vault, target)}")
        return 0
    return report(rel(vault, d) + "/", pending(d, thread_docs(target)), vault)


def self_test():
    """The absorbed matcher: alias, anchor and path forms link; a code span does not. And the
    race's loser: a file that appears between the basename scan and the write is never truncated."""
    import io
    import tempfile
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "race"
        (vault / "workstreams" / "2026-01-01-t").mkdir(parents=True)
        target = vault / "workstreams" / "2026-01-01-t" / "inbox" / "2026-01-02-000000-same.md"
        real = md_files

        def scan_then_lose(root):
            for p in real(root):
                yield p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# first writer\n")

        globals()["md_files"] = scan_then_lose
        saved = sys.stdin, sys.stderr
        sys.stdin, sys.stderr = io.StringIO("# second writer\n\nx\n"), io.StringIO()
        try:
            cmd_send(["2026-01-01-t", "--from", "x", "--slug", "same", "--now", "2026-01-02-000000",
                      "--vault", str(vault)])
            code = 0
        except SystemExit as e:
            code = e.code
        finally:
            sys.stdin, sys.stderr = saved
            globals()["md_files"] = real
        if code != 6 or target.read_text() != "# first writer\n":
            failures.append(f"race: exit {code}, body {target.read_text()!r}; expected 6 and the first writer's bytes")

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp) / "t"
        (t / "inbox").mkdir(parents=True)
        (t / "dumps").mkdir()
        for s in ("alias", "anchor", "path", "fenced", "plain", "none"):
            (t / "inbox" / f"2026-01-01-000000-{s}.md").write_text(f"---\nfrom: x\n---\n# {s}\n")
        (t / "dumps" / "2026-01-02-000000-d.md").write_text(
            "[[2026-01-01-000000-alias|a]] [[2026-01-01-000000-anchor#h]] "
            "[[workstreams/t/inbox/2026-01-01-000000-path]] `[[2026-01-01-000000-fenced]]` "
            "[[2026-01-01-000000-plain]]\n")
        got = {m.stem.split("-")[-1]: by is not None for m, by in pending(t / "inbox", thread_docs(t))}
        want = {"alias": True, "anchor": True, "path": True, "fenced": False, "plain": True, "none": False}
        for k, v in want.items():
            if got.get(k) != v:
                failures.append(f"{k}: absorbed={got.get(k)}, expected {v}")
    for f in failures:
        print("FAIL", f, file=sys.stderr)
    print("self-test: " + ("FAILED" if failures
                           else "alias, anchor and path forms link; a code span does not; a race never truncates"))
    return 1 if failures else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return self_test()
    if argv and argv[0] == "send":
        return cmd_send(argv[1:])
    return cmd_list(argv)


if __name__ == "__main__":
    sys.exit(main())
