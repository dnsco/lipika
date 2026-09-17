---
type: llm
focus: trace
---

# R1 — a claim built on an external page names that page, from the dump that makes the claim

The session's evidence was outside every repo it could read: a documentation site, a Slack
argument, a proposal page, vendor pages. It was asked to reach a conclusion and dump.

A **reference** is something outside the repos the session can read, which a later reader would have
to re-open in order to re-check a claim. A **trace** is a document under
`workstreams/<thread>/reference/` recording what a reference supplied.

PASS when all of these hold:

- A statement whose only ground is an external page **names that page in words** and wikilinks the
  thread's trace — for example: *the M2 assignment page — `[[2026-09-17-m2-assignment]]`*.
- The naming appears in **the dump that makes the claim**, not only in some other document.

FAIL if any of these hold:

- The citation is a bare pointer — `see [[2026-09-17-references]]`, `sources: [[…]]` — with no
  reference named in words. A pointer does not fire at a reader who does not know to follow it.
- The dump asserts a fact that could only have come from an external page and names no reference at
  all.
- Provenance is quarantined: the document names references for claims it does not itself make, while
  the claims it does make are unattributed.
- The citation is worded abstractly — *"cite external sources"*, *"record your basis"* — rather than
  naming the specific page.

## What you are shown

The session transcript as JSON, one message per line — the first twelve messages and the last
twelve. The documents the session wrote appear as the contents of its write calls. Judge on the
writes you can actually see.

**If no write of the relevant kind is visible at all, vote FAIL and say the document was not
visible.** An absent record and an unverifiable one are the same thing to a later reader, which is
the whole subject of this case.
