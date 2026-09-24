---
type: tool_order
before:
  tool: Agent
  input_match: "lipika:tracer"
after:
  tool: Bash
  input_match: "vault-commit"
---

# the vault commit comes after the dispatches return

A parent that commits while children are still writing commits a partial handoff, and the files
that land after it are untracked with nothing to say so. The skill already requires the parent to
commit with an explicit pathspec — `lipika vault-commit -m … -- <paths>` — and that pathspec names
files a child produced, so the commit cannot precede them.

Both ends carry an `input_match`: the first tracer dispatch, and the Bash call that runs
`vault-commit`. Written as bare `Task`/`Bash` it could not pass — the tool is named `Agent` — and
had it matched, any early shell call would have satisfied `after`. **Not yet confirmed:** whether
`tool_order` compares first or last occurrences. If first, this proves the commit follows the first
dispatch, not the last; the substance is judged in the trace-content checks either way.

A tracer never commits. One commit, by the session, after the last child returns.
