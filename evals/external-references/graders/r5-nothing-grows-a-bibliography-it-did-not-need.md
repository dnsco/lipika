---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-09-17
case: external-references
---

# R5 — the negative case: no dump grows a bibliography it did not need

**Written and committed BEFORE the change.** This is the grader that fails if the change becomes
ceremony, and it is the one most likely to be scored generously. Score it adversarially.

## The change under test

Every clause added for references is scoped to *a reference a later reader would need to re-open in
order to re-check a claim*. It is not scoped to everything glanced at. The orientation's `## References`
section is explicitly **bounded by attention** — a wikilink to the newest trace, the handful the thread
rests on, the unopened backlog — and explicitly not the inventory.

- **PASS** — a dump whose work was entirely in-repo (a refactor, a test run, a PR) writes no references
  bullet and creates no trace.
- **PASS** — the orientation's `## References` stays a handful of lines on a thread with thirty
  references, with the inventory reachable by one wikilink.
- **PASS** — a second dump in the same session, resting on references the first already traced, cites
  the existing trace instead of writing a new one.
- **FAIL if** the orientation reproduces the inventory. This was the owner's stated fear about putting
  references in the orientation at all, and the bounded form is the concession that answered it.
- **FAIL if** a dump lists pages it opened and abandoned, or lists a reference it did not use.
- **FAIL if** the run creates a references trace on a thread with no external references, to satisfy the
  step.
- **FAIL if** the added prose is long enough to displace step 2's existing content. A definition is a
  system prompt paid on every invocation; length is a cost, not a thoroughness signal.

## What a suspicious result looks like

**R1 through R4 all reward writing more, and this one is the only counterweight.** A round where R1–R4
pass and R5 is scored "fine" is the expected shape of a change that has become ceremony. Compare the
diff's line count against what it removes, and compare a no-external-references dump before and after —
if it grew at all, say so.
