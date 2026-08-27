---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-08-26
case: self-comparison
---

# S1 — a check never reports agreement it did not measure

**Written and committed BEFORE the change.**

## The change under test

`tools/doctor.py:60` sets `tree = HERE.parent` — the folder the running script sits in. Run from the
installed snapshot, which is how the plugin normally runs, `installed_vs_tree()` compares that snapshot
against itself and cannot fail. It is being changed so the second operand is a **real checkout**,
found by measurement, and so the check **says it could not compare** when there is none.

**Precondition.** The machine must have both an installed plugin and a checkout, and they must
**differ** — an undeployed edit is enough. If they are identical, a green line is correct and this
grader is **UNEXERCISED**, not a pass.

- **PASS** — run from the installed snapshot against a differing checkout, `doctor` reports the
  disagreement. No line in the `ok` column claims they match.
- **PASS** — the checkout it compared against appears **as a path, in the output**. A comparison whose
  second operand is unstated cannot be audited by the reader it was printed for, which is the entire
  reason this check exists rather than being a rule someone remembers.
- **PASS** — with no checkout reachable at all, it says so and counts it as a problem. Silence and a
  green line are both wrong; the absence of a comparison is itself the finding.
- **FAIL if** an `ok ... IS the tree` line appears while the checkout differs. This is the observed
  defect and the sharpest clause here.
- **FAIL if** the checkout is found by a hardcoded path, `~/workspace`, the repo's directory name, or
  anything else not measured from the running environment. This thread ruled inference out on
  2026-08-25 in the identical shape: *it is an argument or it is absent*, because a value nothing
  declared acquires a meaning, gets read by one caller, and is explained by none.
- **FAIL if** the fix is only that `doctor` grew an option to pass the checkout in. An option a human
  must remember is the rule this check replaced. The option may exist; it must not be the only path.
- **FAIL if** `doctor` prints the disagreement and still exits 0. A check with no exit code is prose.

## What a suspicious result looks like

**On the machine this was written on, `lipika` on PATH resolves to the checkout** — so the discovery
path is the one that gets exercised and the refusal never runs. If every clause reads green, the
no-checkout case was almost certainly not exercised: check that it was run with `PATH` holding only the
installed `bin/`, and mark clause 3 UNEXERCISED rather than PASS if it was not.

The second weakness: clause 2 is satisfied by printing *any* path, and does not prove the path printed
is the one that was compared. Read the code, not only the output.
