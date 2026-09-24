---
type: file_exists
path: "workstreams/*/dumps/*.md"
---

# the run actually wrote a dump

A guard, not a rule about references. Every other check in this case is scored against what the run
produced; if the run produced nothing, the judged checks can vote PASS on an empty workspace and the
suite reports a score that means nothing.

Measured 2026-09-17: a run that never executed — the child session failed to authenticate — scored
0.25, with `reference-writes-stay-proportionate` voting PASS three times against an empty workspace.

Provenance: `design/eval-cases/external-references.md`.
