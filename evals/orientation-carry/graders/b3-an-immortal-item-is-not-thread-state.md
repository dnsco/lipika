---
type: llm
focus: files
---

# B3 — an item whose death condition is `dies never` does not stay in the live set

The rule this round adds, and the reason making carry cheap does not simply make orientations grow
faster.

Measured 2026-09-18, across two unrelated threads in one vault:

| orientation | bytes | items | `[DEAD END]` + `dies never` |
|---|---|---|---|
| `2026-09-16-can-agentomatic-host-workloads` | 62,817 | 125 | 30 (24%) |
| `2026-09-17-how-do-external-references-get-recorded` | 22,326 | 72 | 30 (42%) |

Both carried **the same 19** `dies never` items — the `Edit` tool needing its own `Read`, `grep
--include` failing under zsh, a refusal read through `tail` looking like a success. Those are facts
about the machine, true of every thread, duplicated into each one and re-typed at every handoff.
They are the one class of item that can only accumulate, because nothing can ever retire them.

So: **an item whose death condition is `dies never` is a convention, not a live item.** It belongs
written once on a durable surface — the vault's `CLAUDE.md`, this repo's `design/GOTCHAS.md` — with
the orientation citing the surface rather than carrying the text.

`[DEAD END]` is the exception and stays. It has no death condition by design and fires forever, but
it is genuinely thread-local: *do not re-propose **this**, on **this** thread*, which no shared
surface can say.

PASS when all of these hold:

- The three `dies never` landmines in the seeded orientation — `Edit` needing its own `Read`, `grep
  --include` under zsh, `tail` swallowing a refusal — are **not** carried into the new
  orientation's `## Live items`.
- The run says where they went or where they belong: named as conventions for a durable surface,
  rather than deleted in silence. A disposition states its basis, and "this is not thread state" is
  a basis.
- The `[DEAD END]` about invalidating on read **is** carried. It has no death condition and is
  thread-local.

FAIL if any of these hold:

- The three environment landmines are carried into the live set unchanged. That is the status quo
  and the thing being measured against.
- They are dropped with no mention at all — a reader of the new orientation alone cannot tell
  whether they were retired, promoted, or lost.
- The `[DEAD END]` is dropped along with them, on the reasoning that it also has no death
  condition. The two classes are distinguished by whether a shared surface could hold the item, not
  by whether it can die.
- A **mortal** item is dropped as though it were a convention. `dies when the timer is made
  monotonic` is a death condition; that item stays.

## What you are shown

The file paths created during the run, and the documents' contents.
