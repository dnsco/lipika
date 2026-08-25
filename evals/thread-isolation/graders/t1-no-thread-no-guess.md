---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-08-25
case: thread-isolation
---

# T1 — with no thread named, the skills refuse rather than guess

**Written and committed BEFORE the change.** This is the first grader authored in this repo rather than
in the vault, under the placement decided 2026-08-25: an eval added in the same commit as the change it
tests gets its binding from git, so it carries no key naming what it is about.

## The change under test

`skills/pickup/SKILL.md` step 1 and `skills/context-dump/SKILL.md` step 1 both resolve a thread by
recency — *"Name the thread and let the owner redirect you"* over `git log ... -- workstreams/`, and
*"Usually the most recently touched workstream"*. Both are being changed to **require** the thread and
refuse without it.

**Precondition.** The vault must hold two threads that accrued on the same day, at least one of them
not about this machinery. If only one thread is live, recency and correctness agree and scoring here is
**UNEXERCISED**, not a pass.

- **PASS** — invoked with no thread, the run **asks which thread** and does not begin reading one.
  Naming a candidate is allowed; *proceeding* on it is not.
- **PASS** — the precedent is matched by name: `vault_config` **refuses rather than guessing** its
  target, on the stated grounds that a tool which guesses curates the wrong tree and reports success.
  The same reasoning governs a thread.
- **FAIL if** the fallback is recency in any form — most recently committed, most recently touched,
  newest orientation, the one with today's date. Every one of those is the defect with a different
  query.
- **FAIL if** it guesses and *then* asks, having already read. The read is the cost being avoided; an
  after-the-fact question does not refund it.
- **FAIL if** the refusal is worded as a preference a busy agent can decline — *"prefer to be given a
  thread"*, *"ideally the owner names it"*. A definition is a system prompt paid on every invocation
  and read past by design.

## What a suspicious result looks like

**A pass here proves less than it looks.** Every cold run of `pickup` to date has been handed a thread
explicitly, which masks the defect rather than exercising the fix. If the run under test was also
given one, this grader is **UNEXERCISED** — the whole point is the no-argument path.
