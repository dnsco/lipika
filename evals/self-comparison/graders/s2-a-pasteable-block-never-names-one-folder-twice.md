---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-08-26
case: self-comparison
---

# S2 — a pasteable block never names one folder twice

**Written and committed BEFORE the change.**

## The change under test

`tools/handoff_prompt.py:38` defines `tree_root()` as the folder the running script sits in, and the
`--deployed` path compares that against the installed snapshot before composing the gate block. Run
from the installed snapshot the two are the same directory, so `differing()` is empty by construction,
the exit-3 refusal cannot fire, and the emitted block asks the next human to diff a folder against
itself. It is being changed so the checkout is found by measurement and the tool **refuses** when there
is none.

**Precondition.** A thread that has actually deployed the plugin, invoked with `--deployed`. Without
that flag no gate is emitted at all and there is nothing here to score — that path is T2's subject, not
this one.

- **PASS** — the emitted `T` and `I` resolve to **different** directories, or the tool refuses at exit
  3 and emits no block. Either is correct; a block is not.
- **PASS** — the version named in the block agrees with the version declared by the folder `T` points
  at. **This is what reached a human on 2026-08-26** — `V=0.3.0` over a checkout declaring `0.2.4` —
  and it is the clause most worth trusting, because the failure is arithmetic rather than judgement.
- **PASS** — run with no checkout reachable, it refuses. Exit 3, and the message names how to supply
  the checkout.
- **FAIL if** `T` and `I` resolve to the same directory, however absolute each one is. `0.3.0`'s own
  grader required only that both be absolute paths, and passed this defect; absolute is necessary and
  proves nothing on its own.
- **FAIL if** the refusal is a warning printed above the fence rather than an exit. A caveat outside a
  pasteable block is read past — that is the measured reasoning that made this a tool instead of prose,
  and it does not stop being true for this refusal.
- **FAIL if** a block is emitted whose gate the tool has not itself run. The tool composes the
  comparison; nothing downstream is better placed to check it, and the next reader is the one with the
  least context.

## What a suspicious result looks like

**Three green is plausible here and still incomplete.** The refusal (clause 3) is the clause that will
go unexercised, because on a developer's machine a checkout is always reachable. If it was not run with
`PATH` holding only the installed `bin/`, mark it UNEXERCISED.

Clause 2 is the one to lean on. Clause 1 can be satisfied by a tool that emits two different-looking
paths for the wrong reason — for instance, one absolute and one relative — so confirm both resolve, and
that the one named `T` is a git checkout.
