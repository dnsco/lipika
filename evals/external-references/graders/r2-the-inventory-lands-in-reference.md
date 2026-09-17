---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-09-17
case: external-references
---

# R2 — the references trace lands in `reference/`, and a newer one corrects it

**Written and committed BEFORE the change.**

## The change under test

`reference/` has fired in 2 of 14 threads, and in `skills/context-dump/SKILL.md` the word appears
exactly twice — in the immutability list, and as a line in the shape diagram. **No step points at it.** A
numbered step 2a is being added: when the session read external references, write
`workstreams/<ws>/reference/YYYY-MM-DD-references.md` — the URLs, what each settled, the access route,
first-opened dates.

- **PASS** — the inventory is written to `workstreams/<ws>/reference/`, dated, with the thread's
  own folder as its home.
- **PASS** — asked to correct or extend it later, the run writes a **newer dated** trace and leaves the
  existing one untouched. A moved or renamed URL is a new document with a date, which is the whole
  mechanism by which a reference moving becomes an event.
- **FAIL if** it lands in `dumps/`. The measured defect is precise: the file
  `dumps/2026-09-16-222023-primary-sources.md` declares `type: reference` in its own frontmatter while
  sitting in `dumps/`. **A document that types itself correctly and files itself wrongly is this failure,
  not a near miss.**
- **FAIL if** it lands in vault-root `sources/` or `external/`, or invents `sources.md` beside the
  routing note. Root `sources/` is frozen eval measurements; a thread-local accreting sidecar was
  considered and rejected.
- **FAIL if** an existing trace is edited in place — including to fix a dead link. That is the
  records-and-views violation the dated-trace mechanism exists to prevent.

## What a suspicious result looks like

A thread with an empty `reference/` and a clean-looking dump is the **expected** appearance of the
defect, not evidence of a thread with no external references. Check what the run read before crediting
it with having nothing to file.
