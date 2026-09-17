---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-09-17
case: external-references
---

# R4 — a Slack thread is traced, not linked

**Written and committed BEFORE the change.**

## The change under test

The medium split (`sources/web/`, `sources/slack/`) was rejected 2026-09-17 — the medium is derivable
from the URL, so it is a taxonomy nobody needs to choose. The distinction that survives is **citable vs.
must-be-traced**: a rendered doc page survives as a URL; a Slack thread is not one document, its
permalink dies with workspace access, and a message can be edited out from under it. So step 2a requires
an auth-walled or mutable reference to have its **substance** traced, with the access route that
actually works.

- **PASS** — thirteen Slack messages become a `reference/` trace carrying what was said and decided, with
  the permalink attached as provenance rather than standing in for the content.
- **PASS** — an auth-walled page names the route that works. The measured example is the right shape:
  *behind GitHub auth, a browser without a session gets a login page; the content is
  `vlognow/core-platform-proj-management` under `site/content/agentic_projects/arya/`, read with
  `gh repo clone … --depth=1`*.
- **PASS** — a stable public page may stand as a URL and one line on what it settled. Transcribing it
  would be waste.
- **FAIL if** a bare permalink is the whole record of a conversation.
- **FAIL if** the trace describes the document rather than stating the fact it settled — *"the M2 page
  covers the workflow engine"* instead of *"owners are charlie.thomas + dennis.collinson; `candidate` is
  empty"*.
- **FAIL if** the run proposes a directory or frontmatter field keyed on medium. That decision is
  already made and re-proposing it is the failure this clause exists to catch.

## What a suspicious result looks like

A trace that reads as a bibliography — titles, dates, no findings — passes a shallow read and fails the
purpose. The test is whether a cold agent could re-derive the claim from the trace with the original
source unavailable.
