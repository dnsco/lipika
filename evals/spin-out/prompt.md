---
name: spin-out
description: Spinning a new thread out of a parent, with one related thread nothing cites and one unrelated thread
tags: [spin-out, split, prior-art]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit, Agent, TodoWrite]
max_turns: 80
timeout_seconds: 2400
expected_outcome: >
  The session opens a new dated thread split from the cache-invalidation thread and writes the
  parent a new orientation recording the move. It reads prior art itself, dispatching no agent. The
  new orientation's `## Prior art` names the parent and the archived cache-latency thread, which
  nothing cites but which bears on eviction, with a line on what that thread found; it does not name
  the billing thread. The latency thread's MONITOR warning is appended verbatim to the new thread's
  gotchas.md under a heading naming that thread. Nothing is copied from the billing thread.
---

/lipika:spin-out — the question has moved. We started on how the cache invalidates
(`workstreams/2026-09-10-how-does-the-cache-invalidate`), and what I actually need answered now is
whether the cache evicts under memory pressure, and what it evicts first. Spin that out of the
invalidation thread. Nothing has been measured yet.
