---
name: dispatched-traces
description: A handoff with four external subjects, two of which a child could re-open itself
tags: [context-dump, references, fan-out]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit, Agent, TodoWrite]
max_turns: 80
timeout_seconds: 2400
expected_outcome: >
  The session dumps into the seeded thread. The two subjects that are one addressable artifact each
  are traced by dispatched sub-agents that re-open the artifact themselves; the two that are
  synthesis across the session's own reading are traced by the session; the one that cannot be
  reached is reported as unreachable and lands in the unopened list, with no trace invented for it.
---

You are picking up work in the knowledge-base vault you are standing in. The live thread is
`workstreams/2026-09-20-can-the-runner-survive-a-restart`.

Five things bear on it, and I have not read them into this conversation:

- The argument in `#platform-eng`, exported to `research-notes/platform-eng-export.md`. It is the
  export that survives, not the permalinks — the workspace is going away.
- The incident review for the 2026-09-12 restart, at `research-notes/incident-2026-09-12.md`.
- What the two candidate runners actually cost, which is spread across
  `research-notes/runner-a-pricing.md`, `research-notes/runner-b-pricing.md` and the numbers in the
  incident review. Nobody has put it in one place.
- Whether the restart semantics changed between releases, which you can only work out by reading
  `research-notes/changelog-v3.md` against `research-notes/changelog-v4.md` and deciding what the
  difference means.
- The vendor's hosted-tier page at `https://runner-b.example.com/pricing/enterprise`, which I never
  opened.

Work out whether the runner survives a restart, and hand off.
