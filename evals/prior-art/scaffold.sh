#!/usr/bin/env bash
# Seed a vault for a split, with prior art only a search would find:
#
#   PARENT     -- how-does-the-cache-invalidate. Live. The prompt names it.
#   RELATED    -- why-is-the-cache-slow, ARCHIVED. Nothing cites it. Its gotchas.md carries a
#                 warning that bears on measuring eviction (MONITOR doubles latency) and one that
#                 does not (the old dashboard).
#   UNRELATED  -- what-carries-billing-traffic. Live, another system. Its warning must not travel.
#
# RUNS OUTSIDE THE SANDBOX, as the operator: never `lipika init`, and write only under $PWD.

set -euo pipefail

mkdir -p workstreams/archive grand-plans architecture reference values sources external

cat > CLAUDE.md <<'VAULT'
# This vault

Durable cross-session memory for engineering work. Every document here is a **record** -- dated and
never edited, corrected only by a newer document -- or a **view**, regenerated wholesale and never
patched.

Tiers: `workstreams/` one question being answered each, split into a new dated thread when the
question changes, with finished threads under `workstreams/archive/`; `grand-plans/`;
`architecture/`; `reference/`; `values/`; `sources/`; `external/`.
VAULT

printf 'workstreams/*/.obsidian\n' > .gitignore

thread() {  # thread <path under workstreams/> <title> <paragraph>
  local name; name=$(basename "$1")
  mkdir -p "workstreams/$1/dumps" "workstreams/$1/orientation"
  printf -- '---\ntype: routing\ndate: %s\n---\n\n# %s\n\n%s\n' "${name:0:10}" "$2" "$3" \
    > "workstreams/$1/$name.md"
}

gotchas() {  # gotchas <path under workstreams/> <source> <items...>
  local f="workstreams/$1/gotchas.md" src="$2"; shift 2
  printf -- '---\ntype: gotchas\nstatus: record\n---\n\n# Warnings that stay true in this thread\n\n## From %s\n\n' "$src" > "$f"
  for i in "$@"; do printf -- '- %s\n' "$i" >> "$f"; done
}

# --- PARENT -----------------------------------------------------------------------------------
P=2026-09-10-how-does-the-cache-invalidate
thread "$P" "How does the cache invalidate?" \
  "How the session cache in \`svc/cache\` drops an entry when its source row changes."
cat > "workstreams/$P/orientation/2026-09-18-120000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-18
---

## Where this is
Invalidation is write-through: `svc/cache/invalidate.py` deletes the key on every row update. The
remaining question is whether a delete can race a read-through fill.

## Live items
- **[OPEN Q] Can a delete race a read-through fill?** → dies when measured with two writers · as-of 2026-09-18
- **[LANDMINE] `CACHE_MAXMEMORY` is read once at boot.** Changing it needs a restart → dies when the
  service reloads config · as-of 2026-09-15
ORIENT
gotchas "$P" "dumps/2026-09-12-100000-write-through" \
  "**[LANDMINE] The staging cache is shared with QA.** Flushing it breaks their run → dies never · as-of 2026-09-12"

# --- RELATED, archived, cited by nothing ------------------------------------------------------
R=archive/2026-08-20-why-is-the-cache-slow
thread "$R" "Why is the cache slow?" \
  "Why p99 reads from the session cache in \`svc/cache\` rose to 40ms. Answered: the eviction policy was allkeys-lru on a full instance."
cat > "workstreams/$R/orientation/2026-08-28-090000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-08-28
---

## Where this is
Answered. p99 rose because the instance sat at maxmemory and every write triggered an eviction
sweep under allkeys-lru.
ORIENT
gotchas "$R" "dumps/2026-08-25-150000-eviction-sweeps" \
  "**[LANDMINE] Running \`MONITOR\` on the cache doubles its latency.** Measure with \`INFO stats\` evicted_keys instead → dies never · as-of 2026-08-25" \
  "**[LANDMINE] The old Grafana cache dashboard reads a renamed metric.** Use the v2 board → dies never · as-of 2026-08-22"

# --- UNRELATED --------------------------------------------------------------------------------
U=2026-09-05-what-carries-billing-traffic
thread "$U" "What carries billing traffic?" \
  "Which load balancer and port the billing API's traffic arrives on, in each environment."
cat > "workstreams/$U/orientation/2026-09-19-100000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-19
---

## Where this is
Billing traffic arrives on the internal ALB, port 8443, in every environment but dev.
ORIENT
gotchas "$U" "dumps/2026-09-06-110000-alb" \
  "**[LANDMINE] The billing ALB's access logs lag by fifteen minutes.** → dies never · as-of 2026-09-06"

git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture"
