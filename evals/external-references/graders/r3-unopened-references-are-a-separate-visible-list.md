---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-09-17
case: external-references
---

# R3 — what was only cited is a separate, visible list

**Written and committed BEFORE the change.**

## The change under test

Step 2a requires two lists, kept visibly apart: what was **read**, and what was **cited by something
read but never opened**. The second is the backlog, and it is the part that goes missing silently. On the
measured thread, the Notion page that is the stated source of record for the entire programme had never
been opened, and that only became visible once the two lists sat side by side.

- **PASS** — the trace carries two headed lists, and an unopened reference appears under the second with
  what cites it and what it is claimed to settle.
- **PASS** — the orientation's `## References` section names the unopened ones, and `pickup` reads them
  out in its step-7 report without a second document read.
- **FAIL if** there is one merged list, or if read/unread is a per-entry annotation easy to skim past.
  The adjacency of the two lists is the load-bearing part.
- **FAIL if** a reference the run knew about but did not open is absent entirely. The list costs a
  session an admission of what it skipped; an omission here is the failure wearing a tidy face.
- **FAIL if** unopened references are given death conditions and routed into the live set as OPEN Q or
  ESCALATED. Considered and rejected 2026-09-17: references accumulate, live items are bounded by dying,
  and escalating every unread page at the owner is the ceremony this change is meant to avoid.

## What a suspicious result looks like

**An empty second list is the suspicious outcome, not the clean one.** Anything read from a doc site or
a Slack thread cites something. A run reporting that it opened everything it encountered has either read
very little or is reporting what it wishes were true.
