---
name: prior-art
description: Opening a new thread split from a parent, with one related thread nothing cites and one unrelated thread
tags: [context-dump, split, prior-art, scout]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit, Agent, TodoWrite]
max_turns: 80
timeout_seconds: 2400
expected_outcome: >
  The session opens a new dated thread split from the cache-invalidation thread. It dispatches a
  scout to find prior art. The new orientation's `## Prior art` points at the parent and at the
  archived cache-latency thread, which nothing cites but which bears on eviction, and not at the
  billing thread. The latency thread's warning about MONITOR is appended verbatim to the new
  thread's gotchas.md under a heading naming that thread. Nothing is copied from the billing thread.
---

/lipika:context-dump — the question has moved. We started on how the cache invalidates
(`workstreams/2026-09-10-how-does-the-cache-invalidate`), and what I actually need answered now is
whether the cache evicts under memory pressure, and what it evicts first. Open a new thread for that,
split from the invalidation thread, and hand off. Nothing has been measured yet.
