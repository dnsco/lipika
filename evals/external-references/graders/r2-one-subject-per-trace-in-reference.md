---
type: llm
focus: files
---

# R2 — a reference trace covers one subject

You are shown the list of file paths created during the run, one per line.

A **reference** is something outside the repos the session could read, which a later reader would
have to re-open to re-check a claim. A **trace** is a document recording what one reference supplied.
The session's evidence included a Slack argument, a stakeholder deck, an incident review, gists and
public vendor pages.

The unit of a trace is a **subject** — an argument, a decision, a document that settled something —
not a link. Forty URLs that all belong to one Slack argument are one subject, and therefore one
trace.

PASS when all of these hold:

- Each subject the session read has its **own dated document** under
  `workstreams/<thread>/reference/`, named for what it is about. A Slack channel's argument, a
  stakeholder deck, an incident review and a vendor page are four subjects and therefore four files.
- Filenames are dated, in the form `YYYY-MM-DD-<topic>.md`.

FAIL if any of these hold:

- Heterogeneous references are collected into **one document** with a heading per subject. A file
  that is correctly placed and correctly named is still this failure if it holds unrelated subjects.
- The run writes **one file per URL**, splitting a single subject across many documents. That is a
  different mechanical rule, not the rule.
- A trace lands in `dumps/`, in vault-root `sources/`, in vault-root `external/`, or in a
  `sources.md` beside the thread's routing note.
- An existing trace is **edited** rather than corrected by a newer dated document — including to fix
  a dead or moved link. A reference moving is an event, and a new dated document is how it becomes
  one.

## How to judge an empty or near-empty result

An empty `reference/` with a clean-looking dump is the **expected appearance of the defect this case
exists to catch**, not evidence that the session had nothing to file. Do not credit a run for filing
nothing unless the paths show it genuinely read nothing external.
