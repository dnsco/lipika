---
type: tool_used
tool: Bash
input_match: "orientation-carry"
---

# the carry is a tool call

The weakest check in this case, and it is here for one reason: `carried-items-keep-their-as-of-and-death-condition` can pass by careful retyping, and
a run that passes `carried-items-keep-their-as-of-and-death-condition` by being careful has not demonstrated the change — it has demonstrated that
this particular run was careful, which the profiled handoff also was until it was not.

`input_match` is a regex over the call's input, so this matches a Bash call whose command runs
`lipika orientation-carry`, not any shell use. It was a bare `tool: Bash` placeholder until
2026-09-24, when the `claude` 2.1.274 bundle showed `tool_used` accepts `input_match`, `min` and
`max`.
