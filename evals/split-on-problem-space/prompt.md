---
name: split-on-problem-space
description: Pickup of a thread carrying work outside its problem space, and a question merely reworded
tags: [pickup, split]
allowed_tools: [Read, Glob, Grep, Skill, Bash]
max_turns: 40
timeout_seconds: 900
expected_outcome: >
  Pickup reads the thread's `## What this is` and says the ledger-schema items are a different
  problem space, recommending `/lipika:spin-out` for them. It does not recommend a split because the
  retry question was reworded: that work is still inside the description.
---

/lipika:pickup workstreams/2026-09-20-how-do-billing-retries-back-off
