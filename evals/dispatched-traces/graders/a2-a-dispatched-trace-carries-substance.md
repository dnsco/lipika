---
type: llm
focus: files
---

# A2 — a dispatched trace carries the substance, not a pointer

The run should have written reference traces under `workstreams/<thread>/reference/`, some of them
through a dispatched sub-agent. Judge their contents. It does not matter to this check which of them
were dispatched — a trace written by a child is held to exactly the standard a trace written by the
session is.

The `#platform-eng` export is a conversation that is going away, and the incident review is a
document behind an internal system. Neither survives as a pointer.

PASS when all of these hold:

- The conversation is recorded as **what was said and decided** — that the lease TTL goes to 180s as
  a stopgap, that idempotency triage follows, and that a named person objected because a TTL above
  120s breaks dead-worker detection. The objection is part of the decision, not colour.
- The incident review's trace states the **numbers that settle the claim** — 1,840 redelivered, 637
  non-idempotent, 30s lease against a 90s restart window — rather than that an incident review
  exists.
- Each trace names the route that actually works, and carries its own date.

FAIL if any of these hold:

- A trace **describes the document** instead of stating the fact it settled: *"the export covers the
  restart argument"* rather than *"TTL to 180s, accepted over a known regression in dead-worker
  detection"*.
- A trace is a bare path or permalink with a one-line label.
- A dispatched trace is **thinner** than the ones the session wrote itself. That is the specific way
  this change fails: the work gets cheaper by getting worse, and a trace nobody re-reads until the
  source is gone is exactly where that goes unnoticed.
- A trace records a decision without the dissent or the cost attached to it, where the source
  carried one.

## The test to apply

Could a cold reader re-derive the claim from this trace with the original artifact deleted? That is
the only thing a trace is for.

## What you are shown

The files the run wrote, not the transcript. Changed from `focus: trace` on 2026-09-24: that focus
shows the first twelve messages and the last twelve and elides the rest, and in a 39-turn handoff
every dispatch and every write sits in the elided middle. The first scored run's judges were shown
none of the three traces and voted on their absence.
Which trace a child wrote is not visible here, which is fine — the standard does not depend on it.
**If no trace exists at all, vote FAIL and say so** — an absent record and an unverifiable one are
the same thing to a later reader.
