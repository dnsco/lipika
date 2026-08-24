#!/usr/bin/env python3
"""
Marker vocabulary — the one home for what a state marker looks like.

WHY THIS IS A MODULE AND NOT A REGEX IN EACH TOOL
  Measured on this codebase: four tools each re-deriving one rule produced four different
  bugs. Marker spelling is the most re-derived rule here — bracketed `[LANDMINE]` and
  bold `**LANDMINE**` are both live, `✅ done` and `✅ settled` license different actions,
  and anything that counts items has to read both spellings. So the vocabulary lives once.

  Deliberately NOT a policy module. It answers "what state does this line assert" and
  "what identifies it"; whether a state licenses an action belongs to the tool asking.

STATES
  DONE    ✅ / done / settled / merged / mitigated / discharged / resolved / fixed
  WEAK    ▢ / ⏳ / not started / in-flight / unresolved / unmitigated / blocked
  NONE    prose

  DONE outranks WEAK on the same line, which is what makes a `✅ done … ▢ not started`
  line detectable as self-contradicting rather than silently one or the other.
"""

import re

# Both spellings are live in the corpus: bracketed in some notes, bold-prefix in others.
# Enforcing one everywhere was considered and declined -- the convention emerged rather
# than being designed. So anything counting markers reads both.
TYPED = re.compile(r"\[(LANDMINE|GATE|DEAD END|OPEN Q|ESCALATED)\]|\*\*\[?(LANDMINE|GATE|DEAD END|OPEN Q|ESCALATED)\b")

DONE = re.compile(r"✅|\bdone\b|\bMitigated\b|\bFixed\b|\bsettled\b|\bdischarged\b|\bresolved\b",
                  re.I)
WEAK = re.compile(r"▢|⏳|\bnot started\b|\bin-flight\b|\bunfixed\b|\bunmitigated\b|"
                  r"\bUnresolved\b|\bblocked\b|\bLive\b", re.I)
STRONG_WORD = re.compile(r"\b(Mitigated|Fixed|discharged|settled|closed|done)\b", re.I)

# A done-marker CARRIES evidence; a sentence that merely talks about one does not. The
# distinction is that a real marker leads its line -- optionally behind a list bullet and
# bold -- while a mention sits inside prose. Measured: without this, every "settled as
# direction" heading and every sentence describing the convention tripped the check.
LEADING_DONE = re.compile(r"^\s*(?:[-*+]\s*|\d+\.\s*)?(?:\*\*)?\s*(?:✅|▢|⏳)")
MENTION = re.compile(r"\b(a|an|the|any|every|no)\s+(done-?|✅\s*)?marker|"
                     r"\bmarkers?\b(?=[^.]*\b(is|are|mean|means|licen|read|spell|count))", re.I)

# Identifying material, in two strengths. HARD tokens name ONE thing -- a PR, a commit, a file --
# so a shared hard token is evidence that two lines are about the same item. A backticked word is
# NOT: measured, two unrelated frontiers in one workstream matched 12 of 12 residue items on
# shared spans like `CLAUDE.md` and `librarian`, so soft tokens count as vocabulary and feed the
# content-word score instead.
HARD_IDENT = re.compile(r"#\d{2,6}|\b[0-9a-f]{7,40}\b|\b[\w./-]+\.(?:py|md|json|yaml|yml|sh)\b")
SOFT_IDENT = re.compile(r"`[^`]+`")
IDENT = re.compile(HARD_IDENT.pattern + r"|" + SOFT_IDENT.pattern)
WIKILINK = re.compile(r"\[\[([^\]\n|#]+)")

DONE_STATE, WEAK_STATE, NO_STATE = 2, 1, 0

_STOP = set("""a an the and or but of to in on at for with from by is are was were be been
being it its this that these those as if then than so not no any every all some one two
which what when where how why we you i our your their there here now still only also just
same both each other more most less least over under into out up down about again very
much many few new old first last next same own such nor can will would should could may
might must do does did done doing have has had having""".split())


def state(line):
    """DONE_STATE / WEAK_STATE / NO_STATE for one line. DONE outranks WEAK."""
    if DONE.search(line):
        return DONE_STATE
    if WEAK.search(line):
        return WEAK_STATE
    return NO_STATE


def carries_marker(line):
    """Does this line assert a state, as opposed to talking about markers?

    A marker leads its line; a mention sits in prose. This is the distinction that
    `marker-licence-check` was missing -- it read the sentence "a ✅ done marker is the only
    authority" as a done-marker and flagged the definition explaining itself.
    """
    # A heading is a section label, not a claim: `## Settled as direction` names a block of
    # decisions, and reading it as a completion marker flagged a correct document.
    if re.match(r"^\s*#{1,6}\s", line):
        return False
    if MENTION.search(line) and not LEADING_DONE.match(line):
        return False
    return bool(LEADING_DONE.match(line)) or state(line) != NO_STATE


def typed_kind(line):
    """`GATE` / `LANDMINE` / `OPEN Q` / `DEAD END`, or None."""
    m = TYPED.search(line)
    if not m:
        return None
    return (m.group(1) or m.group(2)).upper()


def idents(text, hard=False):
    """Identifying tokens, normalized. Backticks stripped; shas truncated to 7 so a short
    and a long spelling of the same commit compare equal. `hard=True` returns only tokens
    that name one thing (PR ref, commit, filename)."""
    out = set()
    for tok in (HARD_IDENT if hard else IDENT).findall(text):
        tok = tok.strip("`").strip()
        if re.fullmatch(r"[0-9a-f]{7,40}", tok):
            tok = tok[:7]
        if tok:
            out.add(tok.lower())
    return out


def significant(text):
    """The content words of a statement, for matching one against another when it carries no
    identifier. Lowercased, stopworded, marker glyphs and typed prefixes removed."""
    text = TYPED.sub(" ", text)
    text = re.sub(r"[✅▢⏳]", " ", text)
    text = re.sub(r"\[\[|\]\]|[`*_#\[\]()|]", " ", text)
    words = re.findall(r"[a-z][a-z0-9./-]{2,}", text.lower())
    # Trailing punctuation is INSIDE the token: the class carries `.` and `-` so `foo.py` and
    # `vault-config` survive as one word, which also swallows the period ending a sentence. So
    # `rewritten` and `rewritten.` were different words and never matched. Measured 2026-08-21 on
    # a correctly-recorded disposition: 3 shared words instead of 5, 11% instead of 19%, reported
    # as "no successor item resembles it". This affects every comparison in the system, not just
    # that one -- any word ending a sentence failed to match itself used mid-sentence.
    words = [w.rstrip("./-") for w in words]
    return {w for w in words if len(w) > 2 and w not in _STOP}


def overlap(a, b):
    """Jaccard-ish containment of a in b: what fraction of a's content words b also has."""
    if not a:
        return 0.0
    return len(a & b) / len(a)


def list_items(text, sections=None):
    """Every list item in the document, as (lineno, indent, text).

    Continuation lines are folded into their item, because a marker's evidence is routinely
    on the wrapped line -- reading line-at-a-time splits `✅ done 2026-08-20` from the sha
    that licenses it.
    """
    want = {s.lower() for s in sections} if sections else None
    cur, inside = None, want is None
    # A DEEPER heading nests inside the section; it does not leave it. `### Environment`
    # under `## Live items` is still live items, and treating it as an exit made every
    # item beneath a subsection invisible -- silently, as a short carried-count.
    depth = 0
    items, buf = [], None
    for n, raw in enumerate(text.splitlines(), 1):
        h = re.match(r"^(#{1,6})\s+(.*)", raw)
        if h:
            level = len(h.group(1))
            cur = h.group(2).strip().lower()
            if want is None:
                inside = True
            elif any(w in cur for w in want):
                inside, depth = True, level
            elif inside and level > depth:
                pass
            else:
                inside = False
            if buf:
                items.append(buf)
                buf = None
            continue
        if not inside:
            continue
        m = re.match(r"^(\s*)(?:[-*+]|\d+\.)\s+(.*)", raw)
        if m:
            if buf:
                items.append(buf)
            buf = [n, len(m.group(1)), m.group(2)]
        elif buf is not None:
            if raw.strip():
                buf[2] += " " + raw.strip()
            else:
                items.append(buf)
                buf = None
    if buf:
        items.append(buf)
    return [tuple(i) for i in items]


def one_line(text, width=132):
    """A list item collapsed to one printable line, for a report.

    Emphasis markers are stripped, not rendered: `**[LANDMINE]** **the thing**` spends ~25 characters
    of a truncated line on syntax. Measured 2026-08-21 -- a cold pickup reported several audit entries
    unidentifiable from the head alone and judged them by match percentage instead of content, which
    is weaker than the step asks for.
    """
    t = re.sub(r"\s+", " ", text).strip()
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", t)
    return t if len(t) <= width else t[:width - 1] + "\u2026"
