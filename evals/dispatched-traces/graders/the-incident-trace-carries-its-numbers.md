---
type: regex
target: trace
pattern: '/reference/[^"]*\.md","content":"(?:[^"\\]|\\.)*1,840(?:[^"\\]|\\.)*637'
---

# a reference trace states the incident's numbers

A trace that says an incident review *exists* has not recorded it. Passes when one write to a
`reference/` file carries both `1,840` (redelivered) and `637` (non-idempotent) in its content.
Matched inside the write, not anywhere in the trace, so reading the source does not satisfy it.

`target: trace` is the whole run for a regex grader. For an `llm` grader `focus: trace` is the
first and last twelve messages, and `focus: files` is paths only — the reason this was a judge
until 2026-09-24 and is not now. Green on both kept runs of that day; red with the numbers removed.

Not graded any more: whether a dispatched trace is thinner than a session-written one.
