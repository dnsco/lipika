---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-09-17
amended: 2026-09-17
case: external-references
---

# R3 — what was only cited is a separate, visible document

**Clauses 2, 3 and 4 were written and committed BEFORE the change.** Clause 1 was **amended 2026-09-17,
after the first scoring**, and is the weaker half for that reason. What it replaced required the two
lists to be adjacent **headings in one document**; that followed from the aggregate shape R2 now fails.
With one subject per file, *cited but not opened* has no subject to live under and needs its own home.
**The rule did not change — the adjacency of read and unread is still the load-bearing part. Only what
"adjacent" means changed, from two headings to two neighbouring documents.**

## The change under test

Step 2a requires what was **read** and what was **cited by something read but never opened** to be kept
visibly apart. The second is the backlog, and it is the part that goes missing silently. On the measured
thread, the Notion page that is the stated source of record for the entire programme had never been
opened, and that only became visible once the two lists sat side by side.

1. **PASS** — the backlog is its own dated document, `workstreams/<ws>/reference/YYYY-MM-DD-unopened.md`,
   sitting beside the subject traces in the same folder. **FAIL if** unopened references are scattered as
   a per-entry annotation inside the subject traces, where a reader has to visit every file to assemble
   what was skipped — that is the merged-list failure wearing a new shape.

2. **PASS** — an unopened reference appears with **what cites it** and **what it is claimed to settle**.
   *(Original clause; passed on `0.3.6`: the Notion Arya / Core Platform Proposal was named as the stated
   source of record, with its last-read state, and why it could not be opened.)*

3. **PASS** — the orientation's `## References` names the unopened ones, and `pickup` reads them out in
   its step-7 report without a second document read. *(Original clause. **Unexercised on `0.3.6`** — the
   agentomatic thread's current orientation has no `## References` section at all, but it was written at
   14:52 and the trace at 15:51, so no handoff had run since. Score at the next handoff.)*

4. **FAIL if** a reference the run knew about but did not open is absent entirely. The list costs a
   session an admission of what it skipped; an omission here is the failure wearing a tidy face.

5. **FAIL if** unopened references are given death conditions and routed into the live set as OPEN Q or
   ESCALATED. Considered and rejected 2026-09-17: references accumulate, live items are bounded by dying,
   and escalating every unread page at the owner is the ceremony this change is meant to avoid.

## What a suspicious result looks like

**An empty backlog is the suspicious outcome, not the clean one.** Anything read from a doc site or a
Slack thread cites something. A run reporting that it opened everything it encountered has either read
very little or is reporting what it wishes were true.

**And a new one:** the backlog document is the one place in this design that accretes rather than
splitting by subject, so it is the one most likely to drift back toward an inventory. It is still
corrected by a newer dated document, never edited — but a run that carries thirty entries forward
unchanged across three dates has stopped checking them and is copying. Check whether anything ever
*leaves* it by being opened.
