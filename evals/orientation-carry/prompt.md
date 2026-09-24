---
name: orientation-carry
description: A handoff on a thread whose live set is large, immortal in part, and partly dead
tags: [context-dump, orientation, carry]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit, TodoWrite]
max_turns: 60
timeout_seconds: 1800
expected_outcome: >
  The handoff writes a new orientation that carries the surviving live items with their own as-of
  dates unchanged, moves the two items whose death conditions have fired into the settled section
  with the evidence that fired them, and does not carry the environment facts whose death condition
  is "dies never" into the thread's live set.
---

You are picking up work in the knowledge-base vault you are standing in. The live thread is
`workstreams/2026-09-20-does-the-cache-invalidate-correctly`, and it has an orientation already.

This session did two things. `#4412` merged — that is the pull request the orientation is waiting
on. And the staging environment was torn down, so `staging-2.internal` no longer exists.

Nothing else changed. Hand off.
