---
name: inbox-absorb
description: A handoff on a thread whose inbox holds one unabsorbed message
tags: [context-dump, inbox, orientation]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit, TodoWrite]
max_turns: 60
timeout_seconds: 1800
expected_outcome: >
  The handoff reads the thread's inbox, writes a new orientation that links the message and carries
  its item into the live set or settles it with a stated basis, and `lipika inbox <thread>` exits 0
  afterwards.
---

You are picking up work in the knowledge-base vault you are standing in. The live thread is
`workstreams/2026-09-20-does-the-cache-invalidate-correctly`, and it has an orientation already.

This session did one thing: confirmed that `#4412` is still open. Nothing else changed. Hand off.
