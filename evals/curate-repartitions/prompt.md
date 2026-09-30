---
name: curate-repartitions
description: Three live threads split along the wrong lines, reported for an owner who remembers none of them
tags: [curate, curator, repartition]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Agent]
max_turns: 60
timeout_seconds: 1200
expected_outcome: >
  The ledger proposes one re-partition: the two cache threads are one body of work and become one
  new thread, and the replica-lag item in the stale-prices thread is carried to the migration
  thread, which is kept. Each new thread gets a one- or two-sentence description of its problem space.
  The TTL item, carried in both cache threads, appears once in the proposal. Nothing is moved.
---

/lipika:curate — are the threads in this vault drawn along the right lines? I remember none of them.
Give me the report only; I will rule on it later, so do not ask me anything and move nothing.
