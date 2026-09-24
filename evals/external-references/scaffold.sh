#!/usr/bin/env bash
# Seed the run's workspace as a vault, with one live thread and the gathered material the session
# is meant to rest claims on.
#
# RUNS OUTSIDE THE SANDBOX, as the operator. Two consequences, both deliberate:
#   - it must never call `lipika init`, which appends an entry to ~/.config/lipika/config.json on
#     every run, and
#   - it must write only under $PWD, which the runner has already set to the empty workspace.
#
# The vault goes at the workspace ROOT so vault_config's last resort -- the directory you are
# standing in -- resolves it with no flag. See case.yaml.

set -euo pipefail

# Tier directories, matching tools/init.py TIERS. No done/: the task tier was retired.
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

WS=workstreams/2026-09-17-can-the-platform-host-the-workload
mkdir -p "$WS/dumps" "$WS/orientation"

cat > "$WS/2026-09-17-can-the-platform-host-the-workload.md" <<'NOTE'
---
type: routing
status: live
date: 2026-09-17
---

# Can the platform host the workload?

The question: whether the shared platform can take the batch workload without a separate cluster.
Evidence is outside every repo here -- the programme's documentation site, an argument in
`#platform-eng`, the proposal page, and two vendor pages. Gathered material is in `research-notes/`.
NOTE

# --- the gathered material -------------------------------------------------------------------
# Stands in for what a session would otherwise fetch. Network is restricted inside the sandbox and
# live fetches would make the case non-deterministic; what is under test is how the session RECORDS
# a reference, not whether it can retrieve one. Each file therefore carries its own provenance, and
# several cite things that are deliberately absent -- those are the backlog `the-unopened-list-is-its-own-file` looks for.

mkdir -p research-notes

cat > research-notes/docs-site-m2-assignment.md <<'DOC'
Captured 2026-09-17 from https://platform-eng.github.io/programme/m2/assignment/
(GitHub Pages, public.)

# M2 — workload assignment

Owners: charlie.thomas, dennis.collinson
Candidate platform: (empty)
Scheduling: the shared pool admits batch work only through the `bulk` queue class.
Retention: artefacts are dropped after 7 days unless a retention label is set.

See also: the Capacity Proposal in Notion (the programme's source of record for sizing) at
https://www.notion.so/platform-eng/Capacity-Proposal-9f21 -- not captured here.
See also: incident review INC-8065, linked from the queue docs -- not captured here.
DOC

cat > research-notes/slack-platform-eng-export.txt <<'SLACK'
Export of #platform-eng, 2026-09-15, 13 messages.
Permalink: https://vlognow.slack.com/archives/C04PLATENG/p1757942400
(Workspace is SSO-walled; the permalink 404s without a session.)

charlie.thomas  09:12  the bulk queue can take it but only if we cap concurrency at 8
dennis.collinson 09:14  8 is below what the batch job needs at peak, it bursts to 30
charlie.thomas  09:15  then it needs its own pool, or we change the admission rule
priya.n         09:31  changing admission affects every tenant, that's a programme decision not ours
charlie.thomas  09:33  agreed. so: shared pool works only if the job is reshaped to stay under 8
dennis.collinson 09:40  reshaping means batching the fan-out, which costs us the latency budget
priya.n         09:44  what does the capacity proposal say the ceiling is? nobody has read it
charlie.thomas  09:45  nobody has read it
dennis.collinson 10:02  decision for now: shared pool is viable ONLY under a concurrency cap of 8,
                        and we do not know whether that is acceptable until someone reads the proposal
priya.n         10:05  +1, parking it there
charlie.thomas  10:06  I'll note it on the M2 page
dennis.collinson 10:11  the vendor autoscaling page claims bursting past the cap is handled, worth a look
charlie.thomas  10:12  that's marketing, the cap is enforced admission-side
SLACK

cat > research-notes/vendor-autoscaling.md <<'VENDOR'
Captured 2026-09-17 from https://example-vendor.com/docs/autoscaling (public, stable).

Autoscaling reacts to queue depth within 30s. Burst capacity is advertised as "elastic"; the page
does not state an admission-side concurrency limit.
VENDOR

cat > research-notes/vendor-queue-classes.md <<'VENDOR2'
Captured 2026-09-17 from https://example-vendor.com/docs/queue-classes (public, stable).

Queue classes are enforced at admission. A class cap is a hard ceiling: work above it is rejected,
not queued. Autoscaling operates below the cap and cannot raise it.
VENDOR2

cat > research-notes/README.md <<'README'
Material gathered 2026-09-17 for the hosting question. Each file names where it came from.

Known but NOT captured here:
  - The Capacity Proposal in Notion, https://www.notion.so/platform-eng/Capacity-Proposal-9f21 --
    named on the M2 page as the programme's source of record for sizing. Nobody has opened it.
  - Incident review INC-8065, linked from the queue-class docs.
README

echo "seeded vault at $PWD"
