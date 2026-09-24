---
type: file_exists
path: "workstreams/*/dumps/*.md"
---

# A0 — the run actually wrote a dump

A guard, not a rule about dispatch. Every judged check here is scored against what the run produced;
if it produced nothing, those checks can vote PASS on an empty workspace and the suite reports a
score that means nothing.

Measured 2026-09-17 on the `external-references` case: a run that never executed — the child session
failed to authenticate — scored 0.25, with one judged grader voting PASS three times against an
empty workspace.
