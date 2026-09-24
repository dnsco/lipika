---
type: llm
focus: trace
---

# A3 — a trace that is the session's own synthesis is written by the session

The line this round adds to the skill, and the one that stops "dispatch the traces" becoming "fan
everything out". A tracer is for a subject that is **one addressable artifact a child can re-open**.
It is not for a claim that exists only across several artifacts plus the session's judgement about
them, because a child sent to write one of those has neither the artifacts in view nor the
judgement, and will produce a confident summary of the wrong thing.

Two of the five subjects in the prompt are synthesis: what the two runners **cost**, which is spread
across three documents and stated in full by none of them, and whether **restart semantics changed
between v3 and v4**, which is a difference between two changelogs plus a reading of what the
difference means.

PASS when all of these hold:

- The cost comparison and the v3/v4 semantics question are traced — or dumped — by the session
  itself, not handed to a sub-agent as a subject to go and write.
- `reference/<date>-unopened.md` is written by the **session**. Only the session knows what it did
  not open; a child cannot be sent to report an absence.
- The dispatch decision is legible: the run says, in one line somewhere, why a given subject was
  delegated or kept.

FAIL if any of these hold:

- Every subject is dispatched, including the two that are synthesis. A run that delegates
  everything has not learned the rule, it has learned the mechanism.
- A sub-agent is sent to compare the two pricing documents, or to read the two changelogs against
  each other.
- The unopened list is produced by a sub-agent.
- Nothing is dispatched at all. That is A1's failure, and it is this grader's failure too only if
  the run also gives no reason.

## What you are shown

The session transcript as JSON, one message per line — the first twelve messages and the last
twelve. Sub-agent dispatches appear as tool calls with their prompts; judge what each child was
**asked to do**, not what it returned.
