---
type: regex
target: trace
pattern: '"file_path":"[^"]*/reference/(?!\d{4}-\d{2}-\d{2}-)[^"/]*\.md","content":"'
match: not_contains
---

Every written trace is named `YYYY-MM-DD-<topic>.md`.
