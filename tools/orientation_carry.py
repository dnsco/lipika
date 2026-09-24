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

  So: **an item whose death condition is `dies never` is a convention, not a live item.** It belongs
  on a durable surface once -- the vault's `CLAUDE.md`, Lipika's `design/GOTCHAS.md` -- with the
  orientation citing the surface. `[DEAD END]` is the exception and stays in the live set: it has no
  death condition by design, but it is thread-LOCAL -- *do not re-propose this, here* -- which no
  shared surface can say.

  The tool NAMES them and does not drop them. Promoting a landmine to a convention is a judgement
  with a destination, and the destination is a file the agent has to open.

  Hand-typing was never the bound, which is the objection this answers. That 62.8 KB orientation
  went 9,067 -> 17,095 -> 19,890 -> 28,160 -> 36,545 -> 45,470 -> 49,867 -> 62,817 B across eight
  handoffs in 48 hours, every byte typed by an agent. It never slowed once.

CONTRACT

  exit 0  the carry is on stdout and every carried item can still die
  exit 1  the carry is on stdout, AND items that can never leave are listed on stderr. Not an
          error -- a decision to make before pasting. Do not wrap this in `set -e`.
  exit 3  nothing to carry: this thread has no orientation yet, so its first handoff writes one
          from scratch. Reported rather than printed empty, because an empty carry and a thread
          with nothing live look identical on stdout.
  exit 5  bad invocation

USAGE
  lipika orientation-carry <ws>                  # paste stdout into the new orientation
  lipika orientation-carry <ws> --all            # do not separate the immortals; emit everything
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
CARRIED = ("needs the owner", "live items")

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

    `[DEAD END]` is excluded on purpose. It also has no death condition, but it is thread-local --
    *do not re-propose this, on this thread* -- and no shared surface can hold that.
    """
    text = " ".join(l.strip() for l in raw_lines)
    if markers.typed_kind(text) == "DEAD END":
        return False
    return bool(IMMORTAL.search(text))


def render(text, keep_immortals):
    """(stdout_lines, immortal_items). Verbatim on both sides."""
    out, immortal = [], []
    for level, title, body in carried_blocks(text):
        kept = []
        for is_item, raw in split_items(body):
            if is_item and not keep_immortals and is_immortal(raw):
                immortal.append(raw)
                continue
            kept.append(raw)
        # A heading whose every item was immortal is dropped with them: an empty `### Working here
        # at all` in the new document says the section exists and is empty, which is a claim.
        if not any(is_item for is_item, _ in [(ITEM.match(r[0]) is not None, r) for r in kept]):
            if not any(l.strip() for r in kept for l in r):
                continue
        out.append("#" * level + " " + title)
        for raw in kept:
            out.extend(raw)
    while out and not out[-1].strip():
        out.pop()
    return out, immortal


def run(ws_dir, out=sys.stdout, err=sys.stderr, keep_immortals=False):
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

    print(f"\nNOT CARRIED -- {len(immortal)} item(s) whose death condition is `dies never`:",
          file=err)
    for raw in immortal:
        one = " ".join(l.strip() for l in raw)
        print("  · " + markers.one_line(ITEM.sub("", one, count=1)), file=err)
    print("\n  These can never leave a live set, so carrying them is the one thing that only ever\n"
          "  accumulates. An item that cannot die is a CONVENTION, not thread state: write it once\n"
          "  on a durable surface -- the vault's `CLAUDE.md`, or `design/GOTCHAS.md` in Lipika if\n"
          "  it is about the machinery -- and let the orientation cite the surface.\n"
          "\n  Measured 2026-09-18: two unrelated threads carried the SAME 19 of these, 24% and 42%\n"
          "  of their live sets. Nothing had ever retired one.\n"
          "\n  Not dropped for you. Moving one is a judgement with a destination, and you have to\n"
          "  open the destination. If you decide one is genuinely thread-local, paste it back --\n"
          "  `--all` emits everything and says nothing.", file=err)
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
"""
    red = green.replace("### The path\n", "### The path\n\n"
                        "- **[LANDMINE] The `Edit` tool needs its own `Read`** → dies never · "
                        "as-of 2026-09-15\n")

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

        bare = os.path.join(tmp, "bare")
        os.makedirs(bare)
        if run(bare, out=io.StringIO(), err=io.StringIO()) != 3:
            failures.append("a thread with no orientation/ must be exit 3, not an empty carry")

    for f in failures:
        print("FAIL", f, file=sys.stderr)
    print("self-test: " + ("FAILED" if failures
                           else "green, red, --all and no-orientation all as specified"))
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scope", nargs="?",
                    help="workstream: a thread name, vault-relative path, or absolute path")
    ap.add_argument("--all", action="store_true",
                    help="emit every item, including ones that can never die, and exit 0")
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
    return run(ws, keep_immortals=args.all)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
