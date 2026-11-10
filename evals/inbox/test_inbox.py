#!/usr/bin/env python3
"""Tests for the inbox: `lipika inbox`, and the tools that read it.

Run `python3 evals/inbox/test_inbox.py`. Exit 0 all pass, 1 any fail.

A message is a dated record in the receiver's `inbox/`, written by `lipika inbox send`. It is
absorbed when a later dump or orientation of the receiving thread links it. `orientation-carry`
brings every unlinked message into the carry; `threads` counts pending mail; `archive-thread`
refuses while any is pending; liveness and architecture votes ignore `inbox/`.

Drives `bin/lipika`; imports nothing from tools/.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"

PARENT = "2026-05-01-parent"
CHILD = "2026-05-02-child"
OTHER = "2026-05-03-other"
OLD = "2026-04-01-old"           # archived
SHELVED = "2026-04-02-shelved"   # parked
NOW = "2026-05-10-120000"

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def lipika(vault, *args, stdin=None, env=None):
    return subprocess.run([sys.executable, str(LIPIKA), *args, "--vault", str(vault)],
                          capture_output=True, text=True, input=stdin,
                          env=dict(os.environ, LIPIKA_TELEMETRY="0", **(env or {})))


def send(vault, to, frm, slug, body, now=NOW):
    args = ["inbox", "send"] + ([to] if to else []) + ["--from", frm, "--slug", slug, "--now", now]
    return lipika(vault, *args, stdin=body)


ORIENT = """---
type: orientation
status: current
date: 2026-05-05
---

## What this is
A fixture.

## Where this is
x

## Needs the owner

- **[ESCALATED] Rule on it.** → accepted when ruled · as-of 2026-05-05

## Live items

### The path

- **[OPEN Q] `#1` is open.** → accepted when `#1` merges · as-of 2026-05-05

## Settled since the last orientation

- nothing

## Prior art

- [[2026-04-01-old]] — measured the same thing.
"""

BODY = """# Findings on `#1`

Two things the owner of `#1` should know.

- **[OPEN Q] `#1` loads a 600-character grant but cannot create its derived name.** → accepted when
  the derived-name length is checked at load · as-of 2026-05-09
- **[LANDMINE] The staging role trusts every dev session.** → accepted when the trust is narrowed · as-of 2026-05-09
"""

UNTYPED = """# The machinery was in the way

`spin-out` run once for two children left this session's thread ambiguous. One spin-out per child.
"""


def thread(vault, rel, orients=(), dumps=()):
    d = vault / "workstreams" / rel
    name = Path(rel).name
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(f"---\ntype: routing\ndate: {name[:10]}\n---\n\n# {name}\n")
    for stamp, text in orients:
        (d / "orientation").mkdir(exist_ok=True)
        (d / "orientation" / f"{stamp}.md").write_text(text)
    for stamp, text in dumps:
        (d / "dumps").mkdir(exist_ok=True)
        (d / "dumps" / f"{stamp}.md").write_text(text)
    return d


def fixture(d):
    vault = Path(d) / "vault"
    (vault / "workstreams").mkdir(parents=True)
    thread(vault, PARENT, orients=[("2026-05-05-100000", ORIENT)])
    thread(vault, CHILD, orients=[("2026-05-05-110000", ORIENT.replace("## What this is\nA fixture.",
                                                                       "## What this is\nA child."))])
    thread(vault, OTHER)
    thread(vault, f"archive/{OLD}")
    thread(vault, f"parked/{SHELVED}")
    return vault


def git(vault, *args):
    return subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True)


def main():
    # ---- send -------------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        r = send(vault, PARENT, CHILD, "findings-on-1", BODY)
        path = vault / "workstreams" / PARENT / "inbox" / f"{NOW}-findings-on-1.md"
        check("send writes inbox/<stamp>-<slug>.md and exits 0", r.returncode == 0 and path.is_file(),
              f"exit {r.returncode}\n{r.stderr}")
        text = path.read_text() if path.is_file() else ""
        check("the message is a record: type message, status record, date from the stamp",
              "type: message" in text and "status: record" in text and "date: 2026-05-10" in text, text)
        check("a thread sender is written as a wikilink", f'from: "[[{CHILD}]]"' in text, text)
        check("the body is verbatim", BODY.strip() in text, text)
        check("send prints the path, the link to cite, and the commit line",
              f"workstreams/{PARENT}/inbox/{NOW}-findings-on-1.md" in r.stdout
              and f"[[{NOW}-findings-on-1]]" in r.stdout and "lipika vault-commit" in r.stdout, r.stdout)

        r = send(vault, None, "a conductor session", "friction", UNTYPED)
        root = vault / "inbox" / f"{NOW}-friction.md"
        check("no thread sends to the vault inbox", r.returncode == 0 and root.is_file(),
              f"exit {r.returncode}\n{r.stderr}")
        check("a free-text sender is kept as text", 'from: "a conductor session"' in root.read_text()
              if root.is_file() else False)

        r = send(vault, PARENT, CHILD, "findings-on-1", "# again\n\nx\n")
        check("a second send with the same stamp and slug refuses with exit 6", r.returncode == 6, r.stderr)
        check("the first message is unchanged", path.is_file() and path.read_text() == text)
        r = send(vault, OTHER, CHILD, "findings-on-1", "# again\n\nx\n", now="2026-05-10-120001")
        check("a slug reused with a new stamp is a new message", r.returncode == 0, r.stderr)
        (vault / "workstreams" / PARENT / "dumps").mkdir()
        (vault / "workstreams" / PARENT / "dumps" / "2026-05-09-100000-dup.md").write_text("# a dump\n")
        r = send(vault, OTHER, CHILD, "dup", "# x\n\nx\n", now="2026-05-09-100000")
        check("a basename that exists anywhere in the vault is refused with exit 6",
              r.returncode == 6 and not (vault / "workstreams" / OTHER / "inbox" / "2026-05-09-100000-dup.md").exists(),
              r.stderr)

        check("a missing target is exit 5", send(vault, "2026-01-01-nope", CHILD, "s", "# x\n\nx\n").returncode == 5)
        check("an archived target is exit 6", send(vault, OLD, CHILD, "s", "# x\n\nx\n").returncode == 6)
        check("a parked target is exit 6", send(vault, SHELVED, CHILD, "s", "# x\n\nx\n").returncode == 6)
        check("an empty body is exit 2", send(vault, PARENT, CHILD, "s", "").returncode == 2)
        check("a body without a title is exit 2", send(vault, PARENT, CHILD, "s", "no heading\n").returncode == 2)
        check("a bad slug is exit 2", send(vault, PARENT, CHILD, "Bad Slug!", "# x\n\nx\n").returncode == 2)
        r = send(vault, PARENT, "2026-01-01-nope", "s", "# x\n\nx\n")
        check("a dated sender that is not a thread is exit 5", r.returncode == 5, r.stderr)
        r = send(vault, "child", CHILD, "s", "# x\n\nx\n")
        check("a unique suffix resolves the target", r.returncode == 0, r.stderr)
        thread(vault, "2026-05-04-child")
        r = send(vault, "child", CHILD, "s2", "# x\n\nx\n", now="2026-05-10-120002")
        check("an ambiguous target is exit 5 and names the candidates",
              r.returncode == 5 and CHILD in r.stderr and "2026-05-04-child" in r.stderr, r.stderr)

    # ---- list -------------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        send(vault, PARENT, CHILD, "pending-one", BODY)
        send(vault, PARENT, OTHER, "in-a-dump", BODY, now="2026-05-10-120001")
        send(vault, PARENT, OTHER, "aliased", BODY, now="2026-05-10-120002")
        send(vault, PARENT, OTHER, "anchored", BODY, now="2026-05-10-120003")
        send(vault, PARENT, OTHER, "pathed", BODY, now="2026-05-10-120004")
        send(vault, PARENT, OTHER, "fenced-only", BODY, now="2026-05-10-120005")
        ws = vault / "workstreams" / PARENT
        (ws / "dumps").mkdir()
        (ws / "dumps" / "2026-05-11-090000-read-mail.md").write_text(
            "---\ntype: dump\n---\n\n# Read the mail\n\nAbsorbed [[2026-05-10-120001-in-a-dump]].\n")
        (ws / "orientation" / "2026-05-11-100000.md").write_text(
            ORIENT + "\n## Recent narrative\n\n- [[2026-05-10-120002-aliased|the aliased one]] and "
            f"[[2026-05-10-120003-anchored#Findings]] and [[workstreams/{PARENT}/inbox/2026-05-10-120004-pathed]].\n"
            "\n```\n[[2026-05-10-120005-fenced-only]]\n```\n")
        r = lipika(vault, "inbox", PARENT)
        out = r.stdout
        check("list exits 1 while anything is pending", r.returncode == 1, f"exit {r.returncode}\n{r.stderr}")
        check("an unlinked message is PENDING", "PENDING" in out and "pending-one" in out, out)
        check("a message linked by a later dump is ABSORBED",
              any("ABSORBED" in l and "in-a-dump" in l for l in out.splitlines()), out)
        for slug in ("aliased", "anchored", "pathed"):
            check(f"a `[[…]]` with {slug.rstrip('ed')} form absorbs",
                  any("ABSORBED" in l and slug in l for l in out.splitlines()), out)
        check("a link only inside a fenced block does not absorb",
              any("PENDING" in l and "fenced-only" in l for l in out.splitlines()), out)
        check("each line names the sender and the title", f"[[{OTHER}]]" in out and "Findings on" in out, out)

        r = lipika(vault, "inbox", CHILD)
        check("a thread with no inbox/ exits 0 and says so", r.returncode == 0 and "no inbox" in r.stdout,
              f"exit {r.returncode}\n{r.stdout}{r.stderr}")
        (vault / "workstreams" / CHILD / "inbox").mkdir()
        r = lipika(vault, "inbox", CHILD)
        check("an empty inbox/ exits 0", r.returncode == 0, r.stderr)
        check("no such thread is exit 5", lipika(vault, "inbox", "2026-01-01-nope").returncode == 5)
        check("no thread and no --vault-inbox is exit 5", lipika(vault, "inbox").returncode == 5)

        send(vault, None, "the owner", "to-nobody", UNTYPED, now="2026-05-10-130000")
        r = lipika(vault, "inbox", "--vault-inbox")
        check("the vault inbox lists its pending messages", r.returncode == 1 and "to-nobody" in r.stdout,
              f"exit {r.returncode}\n{r.stdout}{r.stderr}")
        (ws / "dumps" / "2026-05-12-090000-routed.md").write_text("# routed\n\nSent on: [[2026-05-10-130000-to-nobody]].\n")
        r = lipika(vault, "inbox", "--vault-inbox")
        check("a vault-inbox message linked from any thread document is absorbed", r.returncode == 0, r.stdout)

    # ---- threads: mail, and liveness ignores the inbox ------------------------------------------
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        before = lipika(vault, "threads").stdout
        send(vault, OTHER, CHILD, "late-mail", BODY, now="2026-06-01-120000")
        send(vault, None, "the owner", "general", UNTYPED, now="2026-06-01-120001")
        after = lipika(vault, "threads")
        row_before = next((l for l in before.splitlines() if OTHER in l), "")
        row_after = next((l for l in after.stdout.splitlines() if OTHER in l), "")
        check("a message does not move the receiver's date", "2026-06-01" not in row_after, row_after)
        check("`threads` marks pending mail", "mail: 1" in row_after, row_after)
        check("`threads` counts the vault inbox first", after.stdout.lstrip().startswith("vault inbox: 1 pending"),
              after.stdout)
        check("threads without mail are unmarked", "mail" not in next((l for l in after.stdout.splitlines() if PARENT in l), ""))

    # ---- orientation-carry brings pending messages in ----------------------------------------
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        send(vault, PARENT, CHILD, "findings-on-1", BODY)
        send(vault, PARENT, "a conductor session", "friction", UNTYPED, now="2026-05-10-120001")
        r = lipika(vault, "orientation-carry", PARENT)
        out = r.stdout
        check("carry exits 0 with pending messages and no immortals", r.returncode == 0, f"exit {r.returncode}\n{r.stderr}")
        head = f"### From [[{NOW}-findings-on-1]]"
        check("each message gets a `### From [[…]]` block", head in out and "### From [[2026-05-10-120001-friction]]" in out, out)
        li, nx = out.find("## Live items"), out.find("## Settled")
        nx = nx if nx != -1 else out.find("## Prior art")
        check("the blocks sit inside `## Live items`, before the next section",
              li != -1 and li < out.find(head) < nx, out)
        check("typed items come across verbatim",
              "- **[OPEN Q] `#1` loads a 600-character grant" in out and "as-of 2026-05-09" in out, out)
        check("the block names the sender and date", f"[[{CHILD}]]" in out and "2026-05-10" in out, out)
        check("an untyped message becomes one bullet from its first paragraph",
              "left this session's thread ambiguous" in out and "[OPEN Q] The machinery" not in out, out)
        check("the carry reports how many messages it brought in", "2 message" in r.stderr, r.stderr)

        (vault / "workstreams" / PARENT / "orientation" / "2026-05-11-100000.md").write_text(
            ORIENT.replace("## Settled", f"### From [[{NOW}-findings-on-1]]\n\n- carried\n\n## Settled"))
        r = lipika(vault, "orientation-carry", PARENT)
        check("a message the newest orientation links is not carried again",
              r.stdout.count(head) == 1 and "600-character" not in r.stdout, r.stdout)
        check("a message the newest orientation does not link is still carried",
              "### From [[2026-05-10-120001-friction]]" in r.stdout, r.stdout)

        send(vault, PARENT, CHILD, "immortal", "# w\n\n- **[LANDMINE] `Edit` needs its own `Read`** → dies never · as-of 2026-05-09\n",
             now="2026-05-10-120002")
        r = lipika(vault, "orientation-carry", PARENT)
        check("a `dies never` item in a message goes to stderr, not the carry",
              r.returncode == 1 and "needs its own" not in r.stdout and "needs its own" in r.stderr,
              f"exit {r.returncode}\n{r.stderr}")

        bare = thread(vault, "2026-05-06-bare")
        send(vault, "2026-05-06-bare", CHILD, "first-mail", BODY, now="2026-05-10-120003")
        r = lipika(vault, "orientation-carry", "2026-05-06-bare")
        check("no orientation but pending messages: the blocks are the carry, exit 0",
              r.returncode == 0 and "## Live items" in r.stdout and "first-mail" in r.stdout,
              f"exit {r.returncode}\n{r.stdout}{r.stderr}")
        check("no orientation and no messages is still exit 3",
              lipika(vault, "orientation-carry", OTHER).returncode == 3)

    # ---- lineage and architecture-candidates ignore the inbox -------------------------------------
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        (vault / "workstreams" / CHILD / "orientation" / "2026-05-05-110000.md").write_text(
            ORIENT.replace("date: 2026-05-05\n", f'date: 2026-05-05\nfrom: "[[{PARENT}]]"\n'))
        send(vault, CHILD, OTHER, "from-other", BODY)
        r = lipika(vault, "lineage", "--json")
        try:
            parents = json.loads(r.stdout).get("parents", {})
        except json.JSONDecodeError:
            parents = {}
        check("a message's `from:` is not a lineage edge", parents.get(CHILD) == [PARENT], parents)

        # PARENT and CHILD accrue a dump on 06-19 and vote on 06-20; OTHER's only recent file is a message.
        (vault / "reference").mkdir()
        (vault / "reference" / "2026-05-01-a-trace.md").write_text("# a trace\n")
        for t in (PARENT, CHILD):
            (vault / "workstreams" / t / "dumps").mkdir(exist_ok=True)
            (vault / "workstreams" / t / "dumps" / "2026-06-19-090000-work.md").write_text("# work\n")
        send(vault, PARENT, OTHER, "cites-trace", "# c\n\nSee [[2026-05-01-a-trace]].\n", now="2026-06-19-120001")
        send(vault, CHILD, OTHER, "also-cites", "# c\n\nSee [[2026-05-01-a-trace]].\n", now="2026-06-19-120002")
        send(vault, OTHER, CHILD, "recent-mail", "# c\n\nx\n", now="2026-06-19-120003")
        r = lipika(vault, "architecture-candidates", "--today", "2026-06-20")
        check("a thread whose only recent file is a message is not voting",
              f"not voting · {OTHER}" in r.stdout, r.stdout)
        check("a trace cited only from messages is not a candidate", "a-trace" not in r.stdout, r.stdout)

    # ---- archive-thread refuses with pending mail -------------------------------------------
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        git(vault, "init", "-q")
        send(vault, OTHER, CHILD, "unread", BODY)
        git(vault, "add", "-A")
        git(vault, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture")
        b = Path(d) / "bin"
        b.mkdir()
        os.symlink(shutil.which("git"), b / "git")
        env = dict(os.environ, LIPIKA_TELEMETRY="0", PATH=f"{b}:/usr/bin:/bin")
        r = subprocess.run([sys.executable, str(LIPIKA), "archive-thread", OTHER, "--vault", str(vault)],
                           capture_output=True, text=True, env=env)
        check("archive-thread refuses a thread with pending mail, exit 6, before it needs Obsidian",
              r.returncode == 6 and "unabsorbed" in r.stderr and (vault / "workstreams" / OTHER).is_dir(),
              f"exit {r.returncode}\n{r.stderr}")

    # ---- the 2026-11-10 audit: confinement, the race's loser, [[from]], root mail, gotchas provenance ----
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        (Path(d) / "outside").mkdir()
        r = send(vault, "../../outside", CHILD, "escape", BODY)
        check("a target outside workstreams/ is exit 5 and writes nothing",
              r.returncode == 5 and not (Path(d) / "outside" / "inbox").exists(), f"exit {r.returncode}\n{r.stderr}")
        (vault / "workstreams" / "archive" / OLD / "dumps").mkdir(parents=True)
        r = send(vault, f"archive/{OLD}/dumps", CHILD, "deep", BODY)
        check("a subdirectory of an archived thread is not a thread: exit 5, nothing written",
              r.returncode == 5 and not (vault / "workstreams" / "archive" / OLD / "dumps" / "inbox").exists(), r.stderr)
        check("a live thread's subdirectory is not a thread", send(vault, f"{PARENT}/dumps", CHILD, "deep2", BODY).returncode == 5)
        check("a container is not a thread", send(vault, "archive", CHILD, "container", BODY).returncode == 5)
        inbox_dir = vault / "workstreams" / PARENT / "inbox"
        inbox_dir.mkdir()
        pre = inbox_dir / f"{NOW}-raced.md"
        pre.write_text("# first writer\n")
        r = send(vault, PARENT, CHILD, "raced", BODY)
        check("an existing file is never truncated: exit 6, bytes unchanged",
              r.returncode == 6 and pre.read_text() == "# first writer\n", r.stderr)
        r = send(vault, PARENT, f"[[{CHILD}]]", "bracketed", BODY, now="2026-05-10-120001")
        p = inbox_dir / "2026-05-10-120001-bracketed.md"
        check("a `[[thread]]` sender, as `from:` stores it, is accepted",
              r.returncode == 0 and p.is_file() and f'from: "[[{CHILD}]]"' in p.read_text(), r.stderr)

    with tempfile.TemporaryDirectory() as d:
        vault = Path(d) / "v"
        (vault / "workstreams").mkdir(parents=True)
        send(vault, None, "the owner", "waiting", UNTYPED)
        r = lipika(vault, "threads")
        check("root mail is reported when no thread is live", "vault inbox: 1 pending" in r.stdout, f"{r.stdout}{r.stderr}")

    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        send(vault, PARENT, CHILD, "warning-only", "# w\n\n- **[LANDMINE] Quote the glob** → dies never · as-of 2026-05-09\n")
        r = lipika(vault, "orientation-carry", PARENT, "--append-gotchas")
        g = (vault / "workstreams" / PARENT / "gotchas.md")
        gt = g.read_text() if g.is_file() else ""
        check("a message's standing warning lands in gotchas under the message's own heading",
              f"## From [[{NOW}-warning-only]]" in gt and "Quote the glob" in gt, gt)
        check("the carry still links a message whose every item went to gotchas",
              f"### From [[{NOW}-warning-only]]" in r.stdout, r.stdout)
        (vault / "workstreams" / PARENT / "orientation" / "2026-05-11-100000.md").write_text(r.stdout)
        check("after that handoff the message is absorbed", lipika(vault, "inbox", PARENT).returncode == 0)

    pattern = next(l for l in (REPO / "evals/inbox-absorb/graders/the-new-orientation-links-the-message.md")
                   .read_text().splitlines() if l.startswith("pattern:"))[len("pattern:"):].strip().strip("'")
    msg = "2026-09-23-091500-harness-measured-the-window"

    def trace(body):
        return json.dumps({"file_path": "/w/workstreams/t/orientation/2026-11-10-010000.md", "content": body},
                          separators=(",", ":"))
    check("the grader regex accepts a real wikilink", re.search(pattern, trace(f"## Live items\n\n### From [[{msg}]]\n")) is not None)
    check("the grader regex accepts a path-qualified wikilink", re.search(pattern, trace(f"[[workstreams/t/inbox/{msg}|m]]")) is not None)
    check("the grader regex rejects a plain mention", re.search(pattern, trace(f"Mentioned: {msg}")) is None)
    check("the grader regex rejects a code span", re.search(pattern, trace(f"`[[{msg}]]`")) is None)

    # ---- vault-commit takes a sent message by the printed path ----------------------------------
    with tempfile.TemporaryDirectory() as d:
        vault = fixture(d)
        git(vault, "init", "-q")
        git(vault, "add", "-A")
        git(vault, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture")
        r = send(vault, PARENT, CHILD, "committed", BODY)
        rel = f"workstreams/{PARENT}/inbox/{NOW}-committed.md"
        r2 = subprocess.run([sys.executable, str(LIPIKA), "vault-commit", "--dry-run", "-m", "x",
                             "--vault", str(vault), "--", rel], capture_output=True, text=True,
                            env=dict(os.environ, LIPIKA_TELEMETRY="0"))
        check("vault-commit --dry-run covers the sent message", r2.returncode == 0 and rel in r2.stdout,
              f"exit {r2.returncode}\n{r2.stdout}{r2.stderr}")

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
