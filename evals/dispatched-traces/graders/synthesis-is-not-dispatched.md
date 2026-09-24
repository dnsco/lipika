---
type: tool_used
tool: Agent
input_match: "changelog-v[34]|runner-[ab]-pricing\\.md"
min: 0
max: 0
---

# a trace that is the session's own synthesis is written by the session

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
- Nothing is dispatched at all. That is `an-addressable-subject-is-dispatched`'s failure, and it is this grader's failure too only if
  the run also gives no reason.

## How it is checked

Mechanically, since 2026-09-24. It was a judge over `focus: trace`, which shows the first twelve
messages and the last twelve; every dispatch in the first scored run sat in the elided middle, so
the judge voted on nothing. What the rule forbids is visible in the dispatch itself: a child sent a
synthesis subject has to be told which documents to compare. Zero `Agent` calls may name a
changelog or a pricing file. The Runner B enterprise **URL** does not match — that one is
addressable, and `no-trace-is-written-for-the-unreachable-page` owns it.

Nothing dispatched at all also passes here, and fails `an-addressable-subject-is-dispatched`. The unopened list's author is `the-unopened-list-is-not-dispatched`. The
"legible decision" clause above is no longer graded; it was the soft end of a judged check.
