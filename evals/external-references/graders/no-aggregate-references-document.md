---
type: regex
target: trace
pattern: '"file_path":"[^"]*/reference/[^"/]*references[^"/]*\.md"'
match: not_contains
---

No `reference/` file named `*references*` — one document per subject, never an aggregate.
