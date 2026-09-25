#!/usr/bin/env bash
# Seed a vault with three threads whose dispositions are known, so a curation report can be scored:
#
#   ANSWERED   -- does-the-queue-drop-messages. Its question is answered, and its one gate fired: the
#                 load measurement it waited on exists as a dump.
#   SUBSUMED   -- how-do-retries-back-off. The third thread's routing note says it took this one
#                 over and carries its jitter question verbatim. Two items are carried NOWHERE:
#                 an unruled escalation (the retry cap), which archiving would lose, and an open
#                 question (the dead-letter alert), which needs a destination.
#   LIVE       -- what-does-the-queue-guarantee. Open items, nothing fired.
#
# RUNS OUTSIDE THE SANDBOX, as the operator: never `lipika init`, and write only under $PWD.

set -euo pipefail

mkdir -p workstreams epics grand-plans architecture reference values sources external

cat > CLAUDE.md <<'VAULT'
# This vault

Durable cross-session memory for engineering work. Every document here is a **record** -- dated and
never edited, corrected only by a newer document -- or a **view**, regenerated wholesale and never
patched.

Tiers: `workstreams/` one question being answered each; `epics/`; `grand-plans/`; `architecture/`;
`reference/`; `values/`; `sources/`; `external/`.
VAULT

printf 'workstreams/*/.obsidian\n' > .gitignore

thread() {  # thread <name> <title> <paragraph>
  mkdir -p "workstreams/$1/dumps" "workstreams/$1/orientation"
  printf -- '---\ntype: routing\ndate: %s\n---\n\n# %s\n\n%s\n' "${1:0:10}" "$2" "$3" \
    > "workstreams/$1/$1.md"
}

# --- ANSWERED ---------------------------------------------------------------------------------
A=2026-08-03-does-the-queue-drop-messages
thread "$A" "Does the queue drop messages?" \
  "Whether the order queue loses messages between the broker and the billing consumer."

cat > "workstreams/$A/orientation/2026-08-09-160000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-08-09
---

## Where this is
Answered: the queue drops nothing. The loss was the billing consumer acking before its database
commit, so a crash between the two lost the message. Fixed in `consumer/ack.py`, which now acks
after commit.

## Live items
- **[GATE] The fix is unverified under load.** Every check so far is one client → dies when a load
  measurement exists in this thread's dumps · as-of 2026-08-09
- **[LANDMINE] The broker console's acked count lags by up to a minute.** Do not read loss from it →
  dies never · as-of 2026-08-05
- **[DEAD END] Adding broker replicas.** Loss was consumer-side; replicas changed nothing. Ruled 2026-08-06.
ORIENT

cat > "workstreams/$A/dumps/2026-08-10-110000-load-test-zero-loss.md" <<'DUMP'
---
type: dump
status: record
date: 2026-08-10
---

# Load test: zero loss

2M messages at 4k/s through the fixed consumer, with a kill every 30s. Produced 2,000,000,
committed 2,000,000. The fix holds under load.
DUMP

# --- SUBSUMED ---------------------------------------------------------------------------------
B=2026-08-12-how-do-retries-back-off
thread "$B" "How do retries back off?" \
  "How the billing consumer spaces its retries after a failed commit."

cat > "workstreams/$B/orientation/2026-08-14-120000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-08-14
---

## Where this is
Retries back off exponentially from 200ms, capped at 5 attempts, then go to the dead-letter queue.

## Needs the owner
- [ESCALATED] **The retry cap of 5 is unowned.** Nobody decided it; it was the library default, and
  billing says a sixth attempt would catch the nightly failover → dies when the owner rules on the
  cap · as-of 2026-08-14

## Live items
- **[OPEN Q] Whether the jitter is full or equal.** The library docs contradict its source → dies
  when read from the pinned version's source · as-of 2026-08-13
- **[OPEN Q] The dead-letter queue has no alert.** A message there is invisible until someone looks →
  dies when an alert exists · as-of 2026-08-14
ORIENT

# --- LIVE -------------------------------------------------------------------------------------
C=2026-09-20-what-does-the-queue-guarantee
thread "$C" "What does the queue guarantee?" \
  "What delivery the order queue promises its consumers, end to end. Continues [[$B]]: the retry
work moved here on 2026-09-20, and that thread stopped accruing."

cat > "workstreams/$C/orientation/2026-09-22-100000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-22
from: "[[2026-08-12-how-do-retries-back-off]]"
---

## Where this is
Mapping the queue's delivery promise: at-least-once to the broker, and whether consumers may rely on
ordering within a partition.

## Live items
- **[OPEN Q] Whether ordering holds within a partition across a rebalance.** → dies when measured
  across a forced rebalance · as-of 2026-09-22
- **[OPEN Q] Whether the jitter is full or equal.** The library docs contradict its source → dies
  when read from the pinned version's source · as-of 2026-08-13 · from [[2026-08-12-how-do-retries-back-off]]
ORIENT
