#!/usr/bin/env bash
# Seed the run's workspace as a vault with one live thread and five things that bear on it, chosen
# so the dispatch rule has something to be wrong about:
#
#   two ADDRESSABLE subjects  -- one artifact each, re-openable by a child that was not in the
#                                conversation. These are what a tracer is for.
#   two SYNTHESIS subjects    -- a claim that exists only across several artifacts and the session's
#                                own judgement about them. Dispatching these is the failure `synthesis-is-not-dispatched` catches.
#   one UNREACHABLE subject   -- a URL, and the sandbox has no network. A tracer must refuse; the
#                                session must file it as unopened rather than invent a trace.
#
# RUNS OUTSIDE THE SANDBOX, as the operator: never `lipika init` (it appends to the operator's real
# ~/.config/lipika/config.json), and write only under $PWD, which the runner has set to the empty
# workspace. The vault goes at the workspace ROOT so vault_config resolves it with no flag.

set -euo pipefail

mkdir -p workstreams grand-plans architecture reference values sources external research-notes

cat > CLAUDE.md <<'VAULT'
# This vault

Durable cross-session memory for engineering work. Every document here is a **record** -- dated and
never edited, corrected only by a newer document -- or a **view**, regenerated wholesale and never
patched.

Tiers: `workstreams/` one question being answered each; `grand-plans/`; `architecture/`;
`reference/`; `values/`; `sources/`; `external/`.
VAULT

printf 'workstreams/*/.obsidian\n' > .gitignore

WS=workstreams/2026-09-20-can-the-runner-survive-a-restart
mkdir -p "$WS/dumps" "$WS/orientation" "$WS/reference"

cat > "$WS/2026-09-20-can-the-runner-survive-a-restart.md" <<'NOTE'
---
type: routing
date: 2026-09-20
---

# Can the runner survive a restart?

Whether a job in flight survives the runner process being restarted, and what that costs.
NOTE

# --- ADDRESSABLE 1: a conversation, mutable and going away. One artifact.
cat > research-notes/platform-eng-export.md <<'SLACK'
# #platform-eng — export, 2026-09-19

**Priya Raghunathan** 09:12
Restart kills the lease. We saw it on the 12th. Anything mid-flight is redelivered, and we have no
idempotency on three of the job types.

**Tomas Lindqvist** 09:14
Redelivery is the contract though. The runner is allowed to restart. The question is whether *we*
are allowed to be non-idempotent, and the answer is no.

**Priya Raghunathan** 09:15
Agreed, but that is a six-week change across three teams. Meanwhile the lease TTL is 30s and a
rolling restart takes 90s, so every rolling restart redelivers the whole in-flight set.

**Tomas Lindqvist** 09:21
Then the decision is: raise the lease TTL above the restart window as a stopgap, and do idempotency
properly after. Not either/or.

**Priya Raghunathan** 09:22
That is the decision. TTL to 180s this week. Idempotency triage starts next sprint.

**Dilnoza Karimova** 09:40
Note that TTL above 120s breaks the dead-worker detection we built in June — it was tuned to the 30s
lease. Raising it means a dead worker holds its jobs for three minutes.

**Tomas Lindqvist** 09:44
Accepted, and it is worse than doing nothing only if workers die more often than we restart. They
do not. Going with 180.
SLACK

# --- ADDRESSABLE 2: a document, one artifact, states its own findings.
cat > research-notes/incident-2026-09-12.md <<'INC'
# Incident review — 2026-09-12, runner restart redelivered 1,840 jobs

**Impact.** A rolling restart of the runner fleet at 14:02 UTC redelivered 1,840 in-flight jobs. Of
those, 1,203 were idempotent and completed twice with no effect. 637 were not: 412 sent a duplicate
notification, 225 double-charged and were reversed by hand over the following two days.

**Cause.** The lease TTL is 30 seconds. A rolling restart of the fleet takes 90 seconds. Every job
held by a draining worker loses its lease before the replacement worker is ready, and the queue
redelivers it.

**Not the cause.** The queue behaved correctly. No message was lost. This was not a durability
failure and the runner's own persistence was never in question.

**Cost of the manual reversal.** 31 engineer-hours, two people, over two days.

**Actions.** (1) Raise the lease TTL above the restart window. (2) Idempotency triage per job type,
starting with the 637. (3) Nothing about the runner choice: both candidates behave this way.
INC

# --- SYNTHESIS 1: cost, which exists in no single document.
cat > research-notes/runner-a-pricing.md <<'A'
# Runner A — pricing

Self-hosted, open source, no licence fee. Priced by what you run it on.

- Control plane: 3 nodes minimum for quorum.
- Storage: its own Postgres, sized to job retention.
- No per-job or per-checkpoint charge.
A

cat > research-notes/runner-b-pricing.md <<'B'
# Runner B — pricing

Hosted tiers, and a self-hosted option under a source-available licence.

- Hosted: metered per **checkpoint**, not per job. A long job with frequent checkpoints costs more
  than a short one that never checkpoints.
- Self-hosted: licence is free under 50 workers; commercial above that.
- The enterprise tier's numbers are not on this page.
B

# --- SYNTHESIS 2: a difference between two documents, and what it means.
cat > research-notes/changelog-v3.md <<'V3'
# Runner, v3.x changelog

## 3.4.0
- Leases are renewed by the worker on a fixed 10s timer.
- A worker that misses two renewals loses its lease.

## 3.2.0
- `--drain-timeout` added; a draining worker stops accepting new jobs.
V3

cat > research-notes/changelog-v4.md <<'V4'
# Runner, v4.x changelog

## 4.1.0
- Leases are renewed on a timer derived from the TTL (TTL/3), not a fixed 10s.
- A draining worker now **hands back** its leases rather than holding them to expiry.

## 4.0.0
- `--drain-timeout` renamed `--drain-deadline`; the old flag is removed, not deprecated.
V4

# No file exists for the vendor enterprise page. It is a URL in the prompt and the sandbox has no
# network, which is the point of `no-trace-is-written-for-the-unreachable-page`.
