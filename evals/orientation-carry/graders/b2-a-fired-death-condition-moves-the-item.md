---
type: llm
focus: files
---

# B2 — an item whose death condition fired leaves the live set, with its evidence

Carrying cheaply must not become carrying indiscriminately. The judgement the tool does **not** do
is which items are still alive; that stays with the session, and this is the check on it.

The prompt fires exactly two death conditions:

- `#4412` merged. The `[OPEN Q]` about it says *dies when `#4412` merges or closes*.
- `staging-2.internal` was torn down. The `[OPEN Q]` about it says *dies when staging-2 is gone, or
  a second environment gets replicas*.

PASS when all of these hold:

- Neither of those two items appears in the new orientation's `## Live items`.
- Both appear under `## Settled since the last orientation`, each naming **what fired it** — that
  `#4412` merged, that staging-2 was torn down — rather than only that it is now settled.
- The `[LANDMINE]` about the sweep timer restarting on config reload is **still carried**. It was
  measured on staging-2, but its death condition is *dies when the timer is made monotonic*, which
  has not fired. Losing a still-true item because the environment it was measured on is gone is the
  error this clause exists to catch.
- The `[GATE]` about nothing having measured the stale window under load is still carried. Nothing
  in the prompt fires it.

FAIL if any of these hold:

- Either fired item is still in the live set.
- Either is dropped silently — gone from the live set and absent from the settled section. An item
  that vanishes without a disposition is indistinguishable from one lost in transit.
- The settled entry states the disposition without its basis: *"no longer relevant"* rather than
  *"`#4412` merged"*.
- The sweep-timer landmine or the under-load gate is dropped.

## What you are shown

The file paths created during the run, and the documents' contents.
