#!/usr/bin/env bash
# One live thread with an orientation and one pending inbox message from a sibling thread. The
# message carries a typed item the handoff must carry or settle, and links nothing else.
# RUNS OUTSIDE THE SANDBOX, as the operator: never `lipika init`, write only under $PWD.

set -euo pipefail

mkdir -p workstreams grand-plans architecture reference values sources external

cat > CLAUDE.md <<'VAULT'
# This vault

Durable cross-session memory for engineering work. Every document here is a **record** -- dated and
never edited, corrected only by a newer document -- or a **view**, regenerated wholesale and never
patched. A thread's `inbox/` holds messages from other threads; the next handoff absorbs them.
VAULT

printf 'workstreams/*/.obsidian\n' > .gitignore

WS=workstreams/2026-09-20-does-the-cache-invalidate-correctly
SIB=workstreams/2026-09-22-replica-load-harness
mkdir -p "$WS/dumps" "$WS/orientation" "$WS/inbox" "$SIB"

cat > "$WS/2026-09-20-does-the-cache-invalidate-correctly.md" <<'NOTE'
---
type: routing
date: 2026-09-20
---

# Does the cache invalidate correctly?

Whether a write invalidates every replica's copy, and what is left stale when it does not.
NOTE

cat > "$SIB/2026-09-22-replica-load-harness.md" <<'NOTE'
---
type: routing
date: 2026-09-22
---

# A load harness for replica reads

Building the harness that drives replica reads under load.
NOTE

cat > "$WS/orientation/2026-09-21-140000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-21
---

## What this is
Whether a write invalidates every replica's copy, and what is left stale when it does not.

## Where this is

A write invalidates the primary synchronously and the replicas on a 60s sweep. Whether that is the
contract or a bug is not answered.

## Needs the owner

- **[ESCALATED] The 60s replica sweep is either the contract or a bug.** → accepted when the owner
  rules · as-of 2026-09-21

## Live items

- **[OPEN Q] `#4412` narrows the sweep to 5s and has not merged.** → accepted when `#4412` merges
  · as-of 2026-09-21
- **[GATE] Nothing has measured the stale window against a replica under load.** → accepted when a
  loaded measurement exists · as-of 2026-09-20

## Settled since the last orientation

- none

## References

- none

## Recent narrative

- 2026-09-21: opened.
ORIENT

cat > "$WS/inbox/2026-09-23-091500-harness-measured-the-window.md" <<'MSG'
---
type: message
status: record
date: 2026-09-23
from: "[[2026-09-22-replica-load-harness]]"
---
# The harness measured the window under load

The replica load harness ran against `staging-2.internal` on 2026-09-23 with 40 clients.

- **[OPEN Q] Under load the stale window is 61–64s, not 60s.** The sweep slips by up to 4s at 40
  clients → accepted when the sweep is measured at 100 clients · as-of 2026-09-23
MSG
