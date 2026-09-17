---
type: llm
focus: files
---

# R3 — what was only cited is a separate, visible document

You are shown the list of file paths created during the run, one per line.

A **reference** is something outside the repos the session could read. Some references the session
**opened and read**; others were **cited by something it read but never opened** — the second group
is the backlog, and it is the part that goes missing silently. The two must be kept visibly apart.

PASS when:

- The backlog is its **own dated document** under `workstreams/<thread>/reference/`, named so a
  reader can tell what it is — for example `YYYY-MM-DD-unopened.md` — sitting beside the subject
  traces in the same folder.

FAIL if any of these hold:

- There is no separate backlog document, and unopened references are instead scattered as per-entry
  annotations inside the subject traces, so a reader must visit every file to assemble what was
  skipped.
- The backlog is merged into a single document that also carries the references that were read.
- No backlog document exists at all.

## How to judge an empty or absent backlog

**An empty backlog is the suspicious outcome, not the clean one.** Anything read from a
documentation site or a Slack thread cites something further. A run that produced no backlog has
either read very little or is reporting what it wishes were true. Do not credit its absence as
"nothing to report".
