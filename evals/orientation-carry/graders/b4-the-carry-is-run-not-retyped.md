---
type: tool_used
tool: Bash
---

# B4 — the carry is a tool call

The weakest check in this case, and it is here for one reason: B1 can pass by careful retyping, and
a run that passes B1 by being careful has not demonstrated the change — it has demonstrated that
this particular run was careful, which the profiled handoff also was until it was not.

`Bash` is the only route to `lipika orientation-carry`, and the run uses `Bash` for much else, so
this proves almost nothing on its own. It is free, and it fails a run that wrote the orientation
with no shell at all.

**Replace this with a `regex` grader over the transcript for `orientation-carry` once the grader
mechanism for matching a command line is pinned down.** Written 2026-09-24; this is a placeholder
that knows it is one, which is better than a check that reads as stronger than it is.
