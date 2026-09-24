---
type: file_exists
path: "workstreams/*/orientation/*.md"
---

# B0 — the run actually wrote an orientation

A guard. Every judged check in this case is scored against a new orientation; with none written
they can vote PASS against the seeded one and report a score that means nothing. The scaffold seeds
`2026-09-21-140000.md`, so this passes on the seed alone — B1 is what proves a *new* one exists,
and this only stops the suite scoring an empty workspace.
