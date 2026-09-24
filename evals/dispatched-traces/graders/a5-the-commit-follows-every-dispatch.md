---
type: tool_order
before: Task
after: Bash
---

# A5 — the vault commit comes after the dispatches return

A parent that commits while children are still writing commits a partial handoff, and the files
that land after it are untracked with nothing to say so. The skill already requires the parent to
commit with an explicit pathspec — `lipika vault-commit -m … -- <paths>` — and that pathspec names
files a child produced, so the commit cannot precede them.

This is a weak mechanical check by construction: `Bash` is the only tool a vault commit can run
through, and the run uses `Bash` for much else, so it proves ordering and not that the ordering was
a commit. It is here because the failure it guards is silent and the check is free. The substance
is judged in A2 — a trace that never landed is not visible there either.

A tracer never commits. One commit, by the session, after the last child returns.
