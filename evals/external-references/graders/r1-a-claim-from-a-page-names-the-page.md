---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-09-17
case: external-references
---

# R1 — a claim built on an external page names that page, from the dump that makes the claim

**Written and committed BEFORE the change.**

## The change under test

`skills/context-dump/SKILL.md` step 2 lists what a dump body carries, and its basis bullet — *"State,
with its basis"* — exemplifies only internal bases: `merged #4131`, `commit a1b2c3d`, `gate green`. An
external page never enters the frame, and measurement says the rule therefore never fires on one. A
bullet is being added that names the media literally — Slack permalink, Notion page, gist, dashboard,
vendor page, rendered doc site — and requires the dump to name the reference **in words** and wikilink
the thread's references trace.

- **PASS** — a dump asserting a fact whose only ground is an external page names that page in words and
  links the trace: *the M2 assignment page — [[2026-09-17-references]]*.
- **PASS** — the naming appears in **the dump that makes the claim**, not only in a later one. The
  measured defect was provenance quarantined in a fifth document while the four dumps resting on it were
  silent.
- **FAIL if** the citation is a bare pointer — `see [[2026-09-17-references]]`, `sources: [[…]]` — with
  no reference named. This is the same defect the live-item rule already forbids: a pointer does not
  fire at a reader who does not know to follow it.
- **FAIL if** the dump asserts an external fact with no reference at all. This is the original failure
  and the only one nothing mechanical can catch.
- **FAIL if** the rule is worded abstractly — *"cite external sources"*, *"record your basis"*. That
  wording is what is being replaced, and it is already in the file.

## What a suspicious result looks like

**A run that cites well after being asked proves nothing.** On 2026-09-16 the owner asked explicitly and
still got the wrong shape. Score the dumps written **before** any instruction about references; if every
citation in the run appeared after such a turn, this grader is **UNEXERCISED**, not a pass.
