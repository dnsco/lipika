---
type: regex
target: trace
pattern: '/reference/[^"]*\.md","content":"(?:[^"\\]|\\.)*\b180 ?s(?:[^"\\]|\\.)*\b120 ?s'
---

# the conversation's trace carries the decision and the objection

The `#platform-eng` export is going away, so its trace must carry what was decided — lease TTL to
180s — and the objection accepted with it: above 120s breaks dead-worker detection. Passes when one
write to a `reference/` file names 180s and then 120s. A decision recorded without its dissent fails.
