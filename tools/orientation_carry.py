#!/usr/bin/env python3
"""orientation-carry — the current orientation's carried sections, VERBATIM, for the next one.

WHY THIS EXISTS
  A handoff writes a new orientation as `previous orientation + the deltas since`, and the
  previous half of that was being re-authored token by token. Measured 2026-09-17 on
  `workstreams/2026-09-16-can-agentomatic-host-workloads`: the orientation phase cost 4m37s and
  62,817 bytes, of which ~50 KB was the previous live set retyped; the session had introduced 17
  items. `orientation-audit` then reported "91 of 91 accounted for" -- verifying work a program
  could have done.

  The defect rate is the argument, not the clock. The audit flagged exactly three problems: one
  item matched on prose alone at 56% of content words, having been reworded while it was copied,
  and two arrived without the death condition they carried in the predecessor. **All three were in
  carried items. None were in the seventeen new ones.** Re-typing is where a live set decays, and
  it decays silently: a reworded item still reads fine, and an item that lost its `dies when`
  clause can now never leave.

  Emitting the section RAW is what fixes it. Each item's own `as-of` comes across because nothing
  re-writes it -- correct by construction rather than by care. `as-of` is when an item was last
  *confirmed*, not last copied, and an item stamped with today's date because today is when it was
  retyped reads fresh and is not.

THIS IS NOT A PATCHED VIEW
  A view is regenerated wholesale, never patched, and that rule is right. This does not patch one.
  The output is still a NEW dated document, still authored by the session, still newest-wins. The
  tool does the mechanical half; the judgement -- what still lives, what died, what the thread is
  now about -- stays with the agent, and it is the only part a tool could get wrong.

  It arguably strengthens the rule. "Wholesale" currently costs four and a half minutes, which is
  exactly the pressure that tempts a session into carrying a selected subset -- something the skill
  forbids and nothing can detect.

WHAT IT REFUSES TO BE SILENT ABOUT
  Making a carry cheap removes the last thing that would make anyone notice an orientation growing.
  So the tool also does the opposite job: it separates out the items that can NEVER leave and exits
  non-zero naming them.

  Measured 2026-09-18, two unrelated threads in one vault, counting `[DEAD END]` plus anything whose
  death condition reads `dies never`:

    2026-09-16-can-agentomatic-host-workloads            62,817 B   125 items   30 immortal (24%)
    2026-09-17-how-do-external-references-get-recorded   22,326 B    72 items   30 immortal (42%)

  Both carried **the same 19** `dies never` items -- the `Edit` tool needing its own `Read`, `grep
  --include` failing under zsh, a refusal read through `tail` looking like a success. Those are
  facts about the machine, true of every thread, duplicated into each and retyped at every handoff.
  They are the one class that can only accumulate.

  So: **an item whose death condition is `dies never` is a warning that stays true, not a live
  item.** It goes in the thread's own `gotchas.md`, appended and never rewritten (2026-09-24; before,
  a shared surface collected every thread's). **Two classes are exempt, and neither exemption is about whether
  the item can die.** `[DEAD END]` has no death condition by design but is thread-LOCAL -- *do not
  re-propose this, here* -- which no shared surface can say. `[ESCALATED]` is exempt because of who
  reads it: an escalation is what the owner opens the document for, and a standing rule from him is
  exactly the shape that reads `dies never`. Found 2026-09-24, on this tool's second real use,
  when it swept *do not merge a PR unless he says so in that turn* out of a live set and
  `orientation-audit` reported it dropped with no successor. Silence toward the owner is the worst
  failure this tool has.

  The tool NAMES them and does not drop them. `--append-gotchas` appends them to `gotchas.md`
  verbatim and exits 0.

  Hand-typing was never the bound, which is the objection this answers. That 62.8 KB orientation
  went 9,067 -> 17,095 -> 19,890 -> 28,160 -> 36,545 -> 45,470 -> 49,867 -> 62,817 B across eight
  handoffs in 48 hours, every byte typed by an agent. It never slowed once.

CONTRACT

  exit 0  the carry is on stdout, and every carried item can still die or --append-gotchas
          appended the ones that cannot
  exit 1  the carry is on stdout, AND items that can never leave are listed on stderr. Not an
          error -- a decision to make before pasting. Do not wrap this in `set -e`.
  exit 3  nothing to carry: this thread has no orientation yet, so its first handoff writes one
          from scratch. Reported rather than printed empty, because an empty carry and a thread
          with nothing live look identical on stdout.
  exit 5  bad invocation

USAGE
  lipika orientation-carry <ws>                  # paste stdout into the new orientation
  lipika orientation-carry <ws> --all            # do not separate the immortals; emit everything
  lipika orientation-carry <ws> --append-gotchas # append the immortals to <ws>/gotchas.md; exit 0
  lipika orientation-carry --self-test
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import markers          # noqa: E402
import vault_config     # noqa: E402

# The sections a new orientation carries. `## Settled since the last orientation` is NOT one of
# them: it is a record of the last round's dispositions and belongs to that document.
CARRIED = ("needs the owner", "live items", "prior art")

ORIENT_DOC = re.compile(r"^\d{4}-\d{2}-\d{2}(-\d{4,6})?.*\.md$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)")
ITEM = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+")
# "dies never", and the handful of spellings that mean it. `re.I` matters: orientations in the
# wild write `Dies never` mid-sentence as often as `· dies never ·`.
IMMORTAL = re.compile(r"\bdies\s+never\b|\bfires\s+forever\b|\bnever\s+dies\b", re.I)


def orientations(ws_dir):
    """Every orientation document in the thread, oldest first by name."""
    d = os.path.join(ws_dir, "orientation")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if ORIENT_DOC.match(f)]


def blocks(text):
    """The document as (heading_level, heading_text, body_lines) in order.

    Headings are kept because a subsection is part of the carry: `### Working here at all` under
    `## Live items` is how a long live set stays readable, and dropping the heading while keeping
    its items is how one thread's sections silently merge into another's.
    """
    out, cur = [], None
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            cur = [len(m.group(1)), m.group(2).strip(), []]
            out.append(cur)
            continue
        if cur is not None:
            cur[2].append(line)
    return out


def carried_blocks(text):
    """The blocks under a carried section, INCLUDING its subsections.

    A deeper heading nests inside the section rather than leaving it -- the same rule
    `markers.list_items` follows (markers.py:144). Treating `###` as an exit made every item
    beneath a subsection invisible, silently, as a short carried count.
    """
    out, inside, depth = [], False, 0
    for level, title, body in blocks(text):
        low = title.lower()
        if any(w in low for w in CARRIED):
            inside, depth = True, level
        elif inside and level > depth:
            pass
        else:
            inside = False
        if inside:
            out.append((level, title, body))
    return out


def split_items(body):
    """Body lines as [(is_item, [raw lines])], continuation lines folded into their item.

    Raw, deliberately: the whole value of this tool is that nothing between the old document and
    the new one rewrites a character. An item's `as-of` survives because nobody retyped it.
    """
    out, cur = [], None
    for line in body:
        if ITEM.match(line):
            if cur:
                out.append((True, cur))
            cur = [line]
        elif cur is not None and (line.strip() or False):
            cur.append(line)
        else:
            if cur:
                out.append((True, cur))
                cur = None
            out.append((False, [line]))
    if cur:
        out.append((True, cur))
    return out


def is_immortal(raw_lines):
    """An item that can never leave a live set, and is therefore not thread state.

    Two kinds are excluded on purpose, and neither exclusion is about whether the item can die.

    `[DEAD END]` has no death condition by design, but it is thread-LOCAL -- *do not re-propose
    this, on this thread* -- and no shared surface can hold that.

    `[ESCALATED]` is excluded because of who reads it. An escalation is the thing a human opens
    the document for, and a standing rule from the owner -- *do not merge a PR unless I say so in
    that turn* -- is precisely the kind that reads as `dies never`. Measured 2026-09-24, on the
    second real use of this tool: it swept exactly that item out of a thread's live set, and
    `orientation-audit` reported it as dropped with no successor. Moving it to a durable surface
    is not wrong in principle and is wrong in effect, because the surface is not what a handoff
    puts in front of the owner. **Silence toward the owner is the worst failure this tool has**,
    so the class is exempt whatever its death condition says.
    """
    text = " ".join(l.strip() for l in raw_lines)
    if markers.typed_kind(text) in ("DEAD END", "ESCALATED"):
        return False
    return bool(IMMORTAL.search(text))


def render(text, keep_immortals):
    """(stdout_lines, immortal_items). Verbatim on both sides."""
    out, immortal = [], []
    cblocks = carried_blocks(text)
    for i, (level, title, body) in enumerate(cblocks):
        # A heading followed by deeper subsections is kept even with no body of its own.
        # Dropping `## Live items` because only `###` sections follow it landed the whole live
        # set under `## Needs the owner` -- measured 2026-09-25, on a real carry.
        has_sub = i + 1 < len(cblocks) and cblocks[i + 1][0] > level
        kept = []
        for is_item, raw in split_items(body):
            if is_item and not keep_immortals and is_immortal(raw):
                immortal.append(raw)
                continue
            kept.append(raw)
        # A heading whose every item was immortal is dropped with them: an empty `### Working here
        # at all` in the new document says the section exists and is empty, which is a claim.
        if not any(is_item for is_item, _ in [(ITEM.match(r[0]) is not None, r) for r in kept]):
            if not any(l.strip() for r in kept for l in r) and not has_sub:
                continue
        out.append("#" * level + " " + title)
        for raw in kept:
            out.extend(raw)
    while out and not out[-1].strip():
        out.pop()
    return out, immortal


GOTCHAS_HEAD = """---
type: gotchas
status: record
---

# Warnings that stay true in this thread

Append-only. Nothing here is rewritten or removed: a warning that stops being true is retired by a
later line saying so, and the bytes above it stay as they were.
"""


def append_gotchas(ws_dir, immortal, source):
    """Append each item not already present, verbatim, to the thread's `gotchas.md`.

    Never regenerated: an item that cannot die has nothing to drop, so a rewrite could only lose one.
    Returns (appended, already present).
    """
    path = os.path.join(ws_dir, "gotchas.md")
    existing = open(path, errors="replace").read() if os.path.exists(path) else ""
    new = [raw for raw in immortal if "\n".join(raw) not in existing]
    if new:
        head = GOTCHAS_HEAD if not existing else ("" if existing.endswith("\n") else "\n")
        body = "\n".join("\n".join(r) for r in new)
        with open(path, "a") as fh:
            fh.write(f"{head}\n## From orientation/{source}\n\n{body}\n")
    return len(new), len(immortal) - len(new)


def run(ws_dir, out=sys.stdout, err=sys.stderr, keep_immortals=False, to_gotchas=False):
    docs = orientations(ws_dir)
    if not docs:
        print(f"NOTHING TO CARRY: {os.path.basename(ws_dir)} has no orientation/ yet.", file=err)
        print("  A thread's first handoff writes one from scratch -- and if this thread was split\n"
              "  from another, that first orientation COPIES what still bears on it from the\n"
              "  parent and names the parent in `from:`. See context-dump step 4a.", file=err)
        return 3

    current = docs[-1]
    text = open(current, errors="replace").read()
    lines, immortal = render(text, keep_immortals)

    print(f"# carried verbatim from {os.path.basename(current)} "
          f"-- every `as-of` below is the date that item was last CONFIRMED", file=err)
    print("\n".join(lines), file=out)

    if not immortal:
        print(f"\n{len(docs)} orientation(s) in this thread; carried from the newest.", file=err)
        return 0

    if to_gotchas:
        added, had = append_gotchas(ws_dir, immortal, os.path.basename(current))
        print(f"\nNOT CARRIED -- {len(immortal)} item(s) whose death condition is `dies never`: "
              f"{added} appended to gotchas.md, {had} already there.", file=err)
        return 0

    print(f"\nNOT CARRIED -- {len(immortal)} item(s) whose death condition is `dies never`:",
          file=err)
    for raw in immortal:
        one = " ".join(l.strip() for l in raw)
        print("  · " + markers.one_line(ITEM.sub("", one, count=1)), file=err)
    print("\n  These can never leave a live set, so carrying them is the one thing that only ever\n"
          "  accumulates. An item that cannot die is a warning that stays true, not thread state:\n"
          "  it goes in this thread's `gotchas.md`. Run again with --append-gotchas to put it there.\n"
          "\n  Measured 2026-09-18: two unrelated threads carried the SAME 19 of these, 24% and 42%\n"
          "  of their live sets. Nothing had ever retired one.\n"
          "\n  If you judge one genuinely thread state, paste it back -- `--all` emits everything\n"
          "  and says nothing.", file=err)
    return 1


def self_test():
    """A green thread, a red one, and a thread with no orientation. Hand-audited, all three."""
    import io
    import tempfile
    failures = []

    green = """---
type: orientation
---

## Needs the owner

- **[ESCALATED] Somebody must rule.** → dies when they rule · as-of 2026-09-20

## Live items

### The path

- **[OPEN Q] `#4412` has not merged.** → dies when `#4412` merges or closes · as-of 2026-09-21
- **[DEAD END] Invalidating on read.** Ruled 2026-09-19: it widens the window.

## Settled since the last orientation

- **[OPEN Q] Per-key or per-shard** → per-shard.

## Prior art

- [[2026-09-01-older-cache-thread]] — measured the same invalidation window on the read path.
"""
    red = green.replace("### The path\n", "### The path\n\n"
                        "- **[LANDMINE] The `Edit` tool needs its own `Read`** → dies never · "
                        "as-of 2026-09-15\n")
    # A standing owner rule, typed ESCALATED and reading `dies never`. It must be CARRIED.
    # Real item, real regression: this shape was swept out of a live set on 2026-09-24.
    esc = green.replace("- **[ESCALATED] Somebody must rule.**",
                        "- **[ESCALATED] Do not merge a PR unless he says so in that turn.** → "
                        "dies never · as-of 2026-09-17\n"
                        "- **[ESCALATED] Somebody must rule.**")

    with tempfile.TemporaryDirectory() as tmp:
        for name, body, want in (("green", green, 0), ("red", red, 1)):
            ws = os.path.join(tmp, name)
            os.makedirs(os.path.join(ws, "orientation"))
            with open(os.path.join(ws, "orientation", "2026-09-21-140000.md"), "w") as fh:
                fh.write(body)
            so, se = io.StringIO(), io.StringIO()
            code = run(ws, out=so, err=se)
            if code != want:
                failures.append(f"{name}: exit {code}, expected {want}\n{se.getvalue()}")
            got = so.getvalue()
            # The carry is verbatim: each line it emits must appear in the source unchanged.
            for line in got.splitlines():
                if line.strip() and line not in body:
                    failures.append(f"{name}: emitted a line that is not in the source: {line!r}")
            if "as-of 2026-09-21" not in got:
                failures.append(f"{name}: a carried item lost its own as-of")
            if "[DEAD END]" not in got:
                failures.append(f"{name}: a DEAD END was treated as immortal; it is thread-local")
            if "Settled since" in got:
                failures.append(f"{name}: the settled section belongs to the OLD document")
            if "## Needs the owner" not in got or "### The path" not in got:
                failures.append(f"{name}: a heading was dropped, so subsections would merge")
            # `## Live items` has no items of its own, only subsections. Dropping it lands the
            # live set under `## Needs the owner` -- measured 2026-09-25, on a real carry.
            if "## Live items" not in got:
                failures.append(f"{name}: `## Live items` was dropped because only subsections follow it")
            # Prior art is pointers by design, and carried whole, so the pointers survive handoffs.
            if "## Prior art" not in got or "older-cache-thread" not in got:
                failures.append(f"{name}: `## Prior art` was not carried")
        # red's immortal must be OFF stdout and ON stderr, which is the whole separation.
        ws = os.path.join(tmp, "red")
        so, se = io.StringIO(), io.StringIO()
        run(ws, out=so, err=se)
        if "needs its own `Read`" in so.getvalue():
            failures.append("red: the immortal item was carried into the pasteable output")
        if "needs its own" not in se.getvalue():
            failures.append("red: the immortal item was dropped silently instead of named")
        so2 = io.StringIO()
        if run(ws, out=so2, err=io.StringIO(), keep_immortals=True) != 0:
            failures.append("--all must not refuse; it is the escape hatch")
        if "needs its own `Read`" not in so2.getvalue():
            failures.append("--all must emit the immortal items")

        # An ESCALATED item reading `dies never` is a standing rule from the owner, and a
        # handoff is how it reaches him. It is carried, and the tool stays quiet about it.
        ws = os.path.join(tmp, "esc")
        os.makedirs(os.path.join(ws, "orientation"))
        with open(os.path.join(ws, "orientation", "2026-09-21-140000.md"), "w") as fh:
            fh.write(esc)
        so, se = io.StringIO(), io.StringIO()
        if run(ws, out=so, err=se) != 0:
            failures.append("esc: an ESCALATED item must not make the tool refuse\n" + se.getvalue())
        if "Do not merge a PR" not in so.getvalue():
            failures.append("esc: an ESCALATED item was swept out of the carry")

        bare = os.path.join(tmp, "bare")
        os.makedirs(bare)
        if run(bare, out=io.StringIO(), err=io.StringIO()) != 3:
            failures.append("a thread with no orientation/ must be exit 3, not an empty carry")

    for f in failures:
        print("FAIL", f, file=sys.stderr)
    print("self-test: " + ("FAILED" if failures
                           else "green, red, escalated, --all and no-orientation all as specified"))
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scope", nargs="?",
                    help="workstream: a thread name, vault-relative path, or absolute path")
    ap.add_argument("--all", action="store_true",
                    help="emit every item, including ones that can never die, and exit 0")
    ap.add_argument("--append-gotchas", action="store_true",
                    help="append the items that can never die to the thread's gotchas.md, and exit 0")
    ap.add_argument("--self-test", action="store_true", help="run the hand-audited cases and exit")
    vault_config.add_argument(ap)
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.scope:
        ap.print_usage(sys.stderr)
        print("orientation-carry: name a workstream, or pass --self-test", file=sys.stderr)
        return 5

    vault = str(vault_config.resolve_or_exit(args.vault, tool="orientation-carry").path)
    scope = args.scope.rstrip("/")
    for cand in (scope, os.path.join(vault, scope), os.path.join(vault, "workstreams", scope)):
        if os.path.isdir(cand):
            ws = os.path.abspath(cand)
            break
    else:
        print(f"orientation-carry: no such workstream: {args.scope}", file=sys.stderr)
        return 5
    return run(ws, keep_immortals=args.all, to_gotchas=args.append_gotchas)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
