---
type: regex
target: trace
pattern: '## From[^"\\]*what-carries-billing-traffic'
match: not_contains
---

# the unrelated thread's warning does not travel

A `gotchas.md` full of another system's warnings fails the same way a long one does: the warning
that matters is buried.
