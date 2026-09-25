---
name: curate
description: Curation of three threads with known dispositions, reported for an owner who remembers none of them
tags: [curate, curator]
allowed_tools: [Read, Glob, Grep, Skill, Bash, Agent]
max_turns: 60
timeout_seconds: 1200
expected_outcome: >
  The report opens with one table, a row per thread, saying in plain words what each thread asked,
  its disposition from the fixed vocabulary, and why. The first thread is answered, the second is
  subsumed by the third, the third is still live. The retry-cap escalation, which no other thread
  carries, is listed as needing a ruling right after the table. The dead-letter alert item gets a
  destination. Nothing is moved.
---

/lipika:curate — which of the threads in this vault are finished? I remember none of them. Give me
the report only; I will rule on it later, so do not ask me anything and move nothing.
