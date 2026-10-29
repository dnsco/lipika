#!/usr/bin/env bash
# One thread, described as billing's retry backoff. Its newest orientation carries:
#   IN SCOPE   -- the retry cap and jitter, under a question reworded from "how do retries back off"
#                 to "what retry policy should billing adopt". Same problem space: no split.
#   OUT        -- two items about the billing ledger's schema migration, which arrived because the
#                 same engineer was working both. A different problem space: split.
#
# RUNS OUTSIDE THE SANDBOX, as the operator: never `lipika init`, and write only under $PWD.

set -euo pipefail

mkdir -p workstreams grand-plans architecture reference values sources external

cat > CLAUDE.md <<'VAULT'
# This vault

Durable cross-session memory for engineering work. Every document here is a **record** -- dated and
never edited, corrected only by a newer document -- or a **view**, regenerated wholesale and never
patched.

Tiers: `workstreams/` one body of work each; `grand-plans/`; `architecture/`; `reference/`;
`values/`; `sources/`; `external/`.
VAULT

printf 'workstreams/*/.obsidian\n' > .gitignore

W=2026-09-20-how-do-billing-retries-back-off
mkdir -p "workstreams/$W/dumps" "workstreams/$W/orientation"
cat > "workstreams/$W/$W.md" <<'NOTE'
---
type: routing
date: 2026-09-20
---

# How do billing retries back off?

How the billing consumer spaces and caps its retries after a failed commit.
NOTE

cat > "workstreams/$W/orientation/2026-09-21-100000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-21
---

## What this is
How the billing consumer spaces and caps its retries after a failed commit: the backoff curve, the
jitter, the cap, and what happens after the last attempt.

## Where this is
Backoff is exponential from 200ms with a cap of 5.

## Live items
- [OPEN Q] **Whether jitter is full or equal.** → accepted when read from the pinned source · as-of 2026-09-21
ORIENT

cat > "workstreams/$W/orientation/2026-09-29-100000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-29
---

## What this is
How the billing consumer spaces and caps its retries after a failed commit: the backoff curve, the
jitter, the cap, and what happens after the last attempt.

## Where this is
The question is now framed as "what retry policy should billing adopt": the curve is known, and the
cap is a choice. Separately, the ledger table's schema migration started this week.

## Live items
- [OPEN Q] **Whether jitter is full or equal.** → accepted when read from the pinned source · as-of 2026-09-21
- [OPEN Q] **Raise the cap from 5 to 6 to ride out the nightly failover?** → accepted when billing
  agrees a number · as-of 2026-09-29
- [OPEN Q] **The ledger table's `amount` column moves from FLOAT to DECIMAL(18,4).** Backfill plan
  unwritten → accepted when the backfill runs on staging · as-of 2026-09-29
- [LANDMINE] **The ledger migration locks the table for ~40 minutes on production size.** Needs an
  online schema-change tool · as-of 2026-09-29
ORIENT
