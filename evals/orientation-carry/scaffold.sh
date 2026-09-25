#!/usr/bin/env bash
# Seed a vault with one live thread that already has an orientation, built so the carry has all
# three cases in it:
#
#   SURVIVING  -- items with a death condition that has not fired. Must be carried, and each one's
#                 own `as-of` must come across unchanged. Hand-transcription is what loses these:
#                 measured 2026-09-17, 3 defects across 91 carried items, 0 across 17 new ones.
#   FIRED      -- two items whose death conditions the prompt fires. Must leave the live set and
#                 appear under `## Settled since the last orientation` with the evidence.
#   IMMORTAL   -- items whose death condition is "dies never". These are facts about the machine,
#                 not about the thread. Measured 2026-09-18: two unrelated threads carried the same
#                 19 of them, 24% and 42% of their live sets, growing and never shrinking.
#
# RUNS OUTSIDE THE SANDBOX, as the operator: never `lipika init`, and write only under $PWD.

set -euo pipefail

mkdir -p workstreams grand-plans architecture reference values sources external

cat > CLAUDE.md <<'VAULT'
# This vault

Durable cross-session memory for engineering work. Every document here is a **record** -- dated and
never edited, corrected only by a newer document -- or a **view**, regenerated wholesale and never
patched.

Tiers: `workstreams/` one question being answered each; `grand-plans/`; `architecture/`;
`reference/`; `values/`; `sources/`; `external/`.
VAULT

printf 'workstreams/*/.obsidian\n' > .gitignore

WS=workstreams/2026-09-20-does-the-cache-invalidate-correctly
mkdir -p "$WS/dumps" "$WS/orientation" "$WS/reference"

cat > "$WS/2026-09-20-does-the-cache-invalidate-correctly.md" <<'NOTE'
---
type: routing
date: 2026-09-20
---

# Does the cache invalidate correctly?

Whether a write invalidates every replica's copy, and what is left stale when it does not.
NOTE

cat > "$WS/orientation/2026-09-21-140000.md" <<'ORIENT'
---
type: orientation
status: current
date: 2026-09-21
tags: [cache, invalidation]
---

# Orientation — 2026-09-21-140000

## Where this is

A write invalidates the primary's copy synchronously and the replicas' copies on a 60s sweep, so a
read against a replica inside that window returns stale data. Whether that is a bug or the contract
is not yet answered.

## Needs the owner

- **[ESCALATED] The 60s replica sweep is either the contract or a bug, and no document says which.**
  The original design note is lost; two engineers remember it differently → someone who was there
  must rule → dies when the owner rules, or a design note turns up · as-of 2026-09-21

## Live items

### The invalidation path

- **[OPEN Q] `#4412` narrows the sweep to 5s and has not merged.** It is approved and its CI is
  green → do not measure the window until it lands, or you measure the old one → dies when `#4412`
  merges or closes · as-of 2026-09-21
- **[GATE] Nothing has measured the stale window against a replica under load.** Every figure so
  far is from a single-client harness → an unloaded measurement is not the contract → dies when a
  loaded measurement exists · as-of 2026-09-20
- **[LANDMINE] The sweep timer restarts on config reload, so a frequent reload starves it.**
  Measured on `staging-2.internal` — a reload every 45s meant the sweep never ran → pin the reload
  interval above the sweep interval when measuring → dies when the timer is made monotonic · as-of
  2026-09-20
- **[OPEN Q] `staging-2.internal` is the only environment with replicas.** Everything measured so
  far was measured there → dies when staging-2 is gone, or a second environment gets replicas ·
  as-of 2026-09-20
- **[LANDMINE] A cache hit and a cache miss return the same status code**, so the access log cannot
  separate them → read the `x-cache` header, not the status → dies when the status codes diverge ·
  as-of 2026-09-19

### Working here at all

- **[LANDMINE] The `Edit` tool needs its own `Read`** — a slice read through Bash does not satisfy
  the guard → dies never · as-of 2026-09-15
- **[LANDMINE] `grep --include=*.md` fails in this shell** — zsh globs the pattern before grep sees
  it → quote it → dies never · as-of 2026-09-15
- **[LANDMINE] Reading a tool's output through `tail` turns a refusal into an apparent success**,
  and `$?` after a pipeline reports the pipe's last command → `cmd > file; echo $?` → dies never ·
  as-of 2026-09-15
- **[DEAD END] Invalidating on read rather than on write.** Ruled 2026-09-19: it moves the cost onto
  every reader and does not close the window, it widens it to the read interval.

## Settled since the last orientation

- **[OPEN Q] Whether the sweep is per-key or per-shard** → per-shard, read from the source at
  `cache/sweep.go:88`.

## References

The sweep's behaviour rests on one subject: [[2026-09-19-the-sweep-source]].

## Recent narrative

- 2026-09-21 13:40 — [[2026-09-21-134000-the-sweep-is-per-shard]]. The sweep is per-shard, and the
  replica window is 60s rather than the 15s the team believed.
ORIENT

cat > "$WS/dumps/2026-09-21-134000-the-sweep-is-per-shard.md" <<'DUMP'
---
type: dump
status: record
date: 2026-09-21
tags: [cache, invalidation]
---

# The sweep is per-shard, and the window is 60s

Read from the source. `cache/sweep.go:88` iterates shards, not keys, and the interval is 60s rather
than the 15s the team believed. That is the whole of this round.
DUMP

cat > "$WS/reference/2026-09-19-the-sweep-source.md" <<'REF'
---
type: reference
date: 2026-09-19
---

# The sweep implementation — the interval is 60s and the unit is a shard

`https://git.internal/platform/cache/blob/main/cache/sweep.go` · opened 2026-09-19 · behind SSO;
the content is `platform/cache` at `cache/sweep.go`, read with `gh repo clone --depth=1`

Line 88 iterates shards. The interval is a constant, 60s, not configurable at runtime.
REF
