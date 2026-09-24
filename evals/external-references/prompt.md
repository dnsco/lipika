---
name: external-references
description: A thread built on Slack threads and web pages, and no trace of either
tags: [context-dump, references]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Write, Edit, TodoWrite]
max_turns: 60
timeout_seconds: 1800
expected_outcome: >
  The session dumps into the seeded thread and records the external references it rested claims on
  as one dated trace per subject under the thread's reference/ folder, with a separate document for
  what it knew of but never opened.
---

You are picking up work in the knowledge-base vault you are standing in. The live thread is
`workstreams/2026-09-17-can-the-platform-host-the-workload`.

Everything I gathered is in `research-notes/` at the root of this vault: a copy of the programme's
documentation site, an export of the argument in `#platform-eng`, the proposal page, and two vendor
pages. Some of it names things I never opened.

Work out whether the platform can host the workload, and dump when you've got something.
