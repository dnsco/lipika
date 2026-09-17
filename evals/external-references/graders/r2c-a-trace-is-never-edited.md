---
type: tool_used
tool: Edit
input_match: "reference/"
min: 0
max: 0
---

# R2c — a trace under `reference/` is never edited

Cross-check on R2's immutability clause. A record is corrected by a newer dated document, never by a
change to it, so no `Edit` call should touch a path under `reference/`.

**Scoped deliberately.** An unscoped "never called `Edit`" would fail a run that correctly edits the
thread's routing note, which is not a record — a check that stays red on correct content gets
dismissed. The `input_match` confines it to the files the rule is actually about.

This is a cheap proxy, not the rule: R2's judged clause is what scores the behaviour.
Provenance: `design/eval-cases/external-references.md`.
