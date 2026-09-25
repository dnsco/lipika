---
type: tool_used
tool: Agent
input_match: 'curator'
min: 1
max: 1
---

The three threads are one group: the same system, no epic splitting them. The skill dispatches one
curator for the group, not one per thread. A curator that sees only its own thread cannot judge
whether a sibling absorbed it, and the goal of curation is merging threads. Replaces
`one-curator-per-thread`, which encoded a drift from the ruling "one curator per partition".
