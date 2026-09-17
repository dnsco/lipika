---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-09-17
amended: 2026-09-17
case: external-references
---

# R2 — a reference trace lands in `reference/`, one subject per document

**Clauses 3 and 4 were written and committed BEFORE the change.** Clauses 1, 2 and 5 were **amended
2026-09-17, after the first scoring**, and they are the weaker half of this grader for exactly that
reason — a clause written after a result can only agree with it. What they replaced required a single
`reference/<stamp>-references.md` **inventory**, which the `0.3.6` run satisfied; the shape it produced
is the defect below, and no clause of the original could see it. Score clauses 3 and 4 as evidence;
score 1, 2 and 5 knowing they were authored against a known outcome.

## The change under test

`reference/` had fired in 2 of 14 threads, and no step in `skills/context-dump/SKILL.md` pointed at it.
Step 2a was added and pointed at one aggregate document per thread. **The shape the vault already
used, and still carries on line 38 of the skill's own diagram, is one subject per file** —
`reference/YYYY-MM-DD-<topic>.md`, *dated traces from source*. Every pre-existing example is that form:
`2026-08-21-crossing-a-cloned-vault-to-the-current-shape.md`,
`2026-08-20-curator-fanout-round-summary.md`, `2026-07-09-inc-8065-citus-faceting.md`.

1. **PASS** — each subject the session read gets its **own dated document** under
   `workstreams/<ws>/reference/`, named for what it is about. A Slack channel's argument, a stakeholder
   deck, an incident review and a vendor page are four subjects and therefore four files.

2. **FAIL if** heterogeneous references are collected into one document with a heading per subject.
   Measured on `0.3.6`: forty references — a Slack DM, a deck, an incident review, gists, public pages —
   became `###` headings in a single 401-line file. **A document that is correctly placed and correctly
   typed is still this failure if it is one file holding unrelated subjects.**

3. **PASS** — the trace is written to `workstreams/<ws>/reference/`, dated, with the thread's own
   folder as its home. *(Original clause; passed on `0.3.6`.)*

4. **PASS** — asked to correct or extend it later, the run writes a **newer dated** document and leaves
   the existing one untouched. A moved or renamed URL is a new document with a date, which is the whole
   mechanism by which a reference moving becomes an event. **FAIL if** an existing trace is edited in
   place, including to fix a dead link. *(Original clause; passed on `0.3.6` — the misfiled
   `dumps/2026-09-16-222023-primary-sources.md` was corrected by a newer document, not edited.)*

5. **FAIL if** it lands in `dumps/`, in vault-root `sources/` or `external/`, or invents a `sources.md`
   beside the routing note. The measured original defect is precise: `dumps/2026-09-16-222023-primary-sources.md`
   declares `type: reference` in its own frontmatter while sitting in `dumps/`. **A document that types
   itself correctly and files itself wrongly is this failure, not a near miss.** Root `sources/` is
   frozen eval measurements; a thread-local accreting sidecar was considered and rejected.

## Why one subject per file, so a later run does not re-propose the aggregate

- **The aggregate fights immutability.** *Newest wins* over forty entries means correcting one reference
  rewrites all forty: the next document copies thirty-nine forward on faith, or drops them silently.
  Per-subject, a correction is one new file and the other thirty-nine are untouched and still true.
- **The aggregate forced a machine-readable duplicate.** One document has to satisfy
  `lipika reference-check`'s literal-string matching by itself, which on `0.3.6` meant 121 lines of
  `## Verbatim index` restating URLs already present in the prose — 30% of the file, written for the
  tool rather than the reader.

## What a suspicious result looks like

A thread with an empty `reference/` and a clean-looking dump is the **expected** appearance of the
original defect, not evidence of a thread with no external references. Check what the run read before
crediting it with having nothing to file.

**And a new one:** a run that writes many small files, one per URL, has substituted a different
mechanical rule for the old one. The unit is a **subject** — an argument, a decision, a document that
settled something — not a link. Forty URLs that all belong to one Slack argument are one trace.
