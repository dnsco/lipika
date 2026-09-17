---
type: llm
focus: files
arm: both
---

# R5 — the negative case: nothing grows a bibliography it did not need

You are shown the list of file paths created during the run, one per line.

Every rule about references is scoped to *a reference a later reader would need to re-open in order
to re-check a claim*. It is **not** scoped to everything the session glanced at. This check is the
counterweight to the others: they all reward writing more, and this one fails a run that has turned
the rule into ceremony.

**Score this adversarially.** A run that satisfies every other check and is waved through here is the
expected shape of a change that has become ceremony.

PASS when all of these hold:

- The number of trace documents is proportionate to the number of distinct subjects the session
  actually rested claims on — a handful, not one per link encountered.
- Work that was entirely inside the repos the session could read produces **no** trace at all.
- A second dump in the same session, resting on references an earlier one already traced, reuses the
  existing trace rather than creating a near-duplicate.

FAIL if any of these hold:

- **The run created nothing at all, or created no dump.** An empty workspace is not restraint, and
  this check must never pass vacuously — measured 2026-09-17, when it voted PASS three times against
  a run that had not executed.
- A trace is created on a thread with no external references, to satisfy the step.
- The paths show a document per page visited, including pages opened and abandoned.
- Traces are created for references the run never used to support a claim.

## What you cannot see, and must not guess at

You are shown paths, not contents or lengths. Do not infer restraint from a short file list alone if
the run plainly read a great deal; the question is proportion to **subjects rested on**, not raw
count. Where you cannot tell, say so rather than passing by default.
