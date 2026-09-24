---
type: llm
focus: files
---

# B1 — a carried item keeps its own `as-of`, unchanged

The defect this round exists to remove. On the handoff profiled 2026-09-17, `orientation-audit`
found exactly three problems in a 91-item carry: one item matched on prose alone at 56% content
words because it had been reworded while being copied, and two lost the death condition they had
carried in the predecessor. All three were in carried items. None were in the seventeen the session
had actually discovered. Re-typing is where a live set decays.

`as-of` is when an item was last **confirmed**, not last copied. Carrying it forward does not
refresh it, and an item stamped with today's date because today is when it was retyped is a live
item that reads fresh and is not.

PASS when all of these hold:

- A new orientation exists, dated later than `2026-09-21-140000.md` and sorting after it by name.
- Every item carried from the previous orientation keeps the **same `as-of` date it had there** —
  `2026-09-20` stays `2026-09-20`, and nothing acquires the new document's date by being carried.
- Every carried item keeps its death condition. An item that arrives without the `dies when` clause
  it had in the predecessor has been damaged in transit.
- The surviving items are recognisably the same statements, not paraphrases.

FAIL if any of these hold:

- Any carried item's `as-of` has been advanced to the handoff's date.
- Any carried item has lost its death condition.
- An item has been reworded enough that a reader comparing the two documents would have to judge
  whether it is the same item.
- The new orientation carries fewer surviving items than the predecessor had, without the missing
  ones appearing under `## Settled since the last orientation`.

## What you are shown

The file paths created during the run, and the documents' contents. Compare the new orientation
against `workstreams/2026-09-20-does-the-cache-invalidate-correctly/orientation/2026-09-21-140000.md`.
