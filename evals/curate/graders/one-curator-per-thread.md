---
type: tool_used
tool: Agent
input_match: 'curator'
min: 3
---

The skill dispatches one curator per thread, three in all, rather than reading every thread in its
own context. This is the speed lever: run 2 read seven threads serially in 404 s.
