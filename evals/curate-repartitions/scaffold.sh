#!/usr/bin/env bash
# Seed a vault with three LIVE threads whose lines are wrong, so a re-partition can be scored:
#
#   CACHE    -- how-does-the-price-cache-invalidate. Invalidation of the price cache.
#   STALE    -- why-are-stale-prices-served. The same body of work as CACHE, split on a reworded
#               question. Carries the TTL item VERBATIM from CACHE, and one item -- the read
#               replica's lag after the Postgres cutover -- that belongs to the migration.
#   MIGRATE  -- migrate-the-price-service-to-postgres. A different body of work.
#
# The right proposal is 3 -> 2: {CACHE, STALE} -> one cache thread, and STALE's replica-lag item
# carried to MIGRATE, which is kept. None is finished, so nothing is `answered` or `abandoned`.
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

thread() {  # thread <name> <title> <paragraph>
  mkdir -p "workstreams/$1/dumps" "workstreams/$1/orientation"
  printf -- '---\ntype: routing\ndate: %s\n---\n\n# %s\n\n%s\n' "${1:0:10}" "$2" "$3" \
    > "workstreams/$1/$1.md"
}

TTL='- [OPEN Q] **The 300s TTL on price entries is unowned.** Nobody chose it; it was the client default · as-of 2026-09-18'

# --- CACHE ------------------------------------------------------------------------------------
A=2026-09-18-how-does-the-price-cache-invalidate
thread "$A" "How does the price cache invalidate?" \
  "How entries in the pricing service's Redis cache are invalidated when a price changes."

cat > "workstreams/$A/orientation/2026-09-19-120000.md" <<ORIENT
---
type: orientation
status: current
date: 2026-09-19
---

## Where this is
Price writes publish an invalidation event; the cache drops the key on receipt. Events are
fire-and-forget, so a lost event leaves the old price until the TTL expires.

## Live items
$TTL
- [OPEN Q] **Whether invalidation events can be lost.** The publisher does not retry → accepted when
  the broker's delivery guarantee for the topic is read · as-of 2026-09-19
ORIENT

# --- STALE ------------------------------------------------------------------------------------
B=2026-09-22-why-are-stale-prices-served
thread "$B" "Why are stale prices served?" \
  "Customers see an old price for up to five minutes after a change. Split from [[$A]] when the
question was reworded around the symptom."

cat > "workstreams/$B/orientation/2026-09-23-120000.md" <<ORIENT
---
type: orientation
status: current
date: 2026-09-23
from: "[[$A]]"
---

## Where this is
The five-minute window matches the TTL, which points at lost invalidation events. Also found: after
the Postgres cutover, the read replica lags the primary, so a fresh cache fill can read an old row.

## Live items
$TTL
- [OPEN Q] **A fresh cache fill can read an old row from the lagging read replica.** Only after the
  Postgres cutover → accepted when fills read from the primary or the lag is bounded · as-of 2026-09-23
- [OPEN Q] **Five-minute staleness reproduces on staging.** → accepted when reproduced with event
  loss ruled in or out · as-of 2026-09-23
ORIENT

# --- MIGRATE ----------------------------------------------------------------------------------
C=2026-09-15-migrate-the-price-service-to-postgres
thread "$C" "Migrate the price service to Postgres" \
  "Move the pricing service's store from MySQL to Postgres: schema, cutover, and read replicas."

cat > "workstreams/$C/orientation/2026-09-24-100000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-24
---

## Where this is
Cutover done on 2026-09-21. The read replica is in service; its lag is not yet monitored.

## Live items
- [OPEN Q] **Replica lag has no alert.** → accepted when an alert on replica lag exists · as-of 2026-09-24
- [OPEN Q] **The MySQL instance is still running.** → accepted when it is decommissioned · as-of 2026-09-24
ORIENT
