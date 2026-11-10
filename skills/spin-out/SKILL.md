---
name: spin-out
description: Open a new knowledge-base vault thread split from a parent, because the work has moved into a different problem space. Writes the parent's handoff recording what moved, the new thread's routing note and first orientation, reads prior art across every thread itself, and ends as the new thread's first pickup. Invoke when asked to "spin out", "split this thread", "open a new thread for X", or when pickup or context-dump finds work outside the thread's problem space.
---

# spin-out — open a thread, carry what bears on it, find its prior art

A workstream is one body of work, and its `## What this is` describes the problem space. When work
falls outside that description, this opens a thread for it: the parent's side, the new thread's side,
and the prior art nothing links to yet. A question reworded inside the description is not a split.

**context-dump's rules on records, views, stamps, typed items and commits hold here.** Read the
vault's `CLAUDE.md` if you have not. Do not invoke context-dump, or any skill: a nested skill call
ends this one's span in `lipika perf`.

## Do

1. **Name the parent and the new problem space, and open the pass.**

   ```bash
   cd "$(lipika vault-config path)"
   lipika pass-log active --scope workstreams/<parent>
   lipika pass-log start spin-out "<new problem space>" --scope workstreams/<parent> --kind dump
   ```

   **If `active` lists an open pass on the parent, stop and ask the owner before `start`.** Two
   sessions once opened the same thread 4 minutes apart, and nothing refuses the second.

   The new thread is `workstreams/YYYY-MM-DD-<slug>/`, dated today. Read the parent's newest
   orientation and its `gotchas.md`, and decide which live items **move** (bear only on the new problem
   space), which are **copied** (bear on both) and which stay.

2. **The parent's side: a dump and a new orientation.** The dump
   (`lipika stamp --for workstreams/<parent>/dumps`) says the thread split, why, and what moved. The
   orientation (`lipika stamp --for workstreams/<parent>/orientation`) is
   `lipika orientation-carry <parent>` with the moved items deleted and written under
   `## Settled since the last orientation` as moved to `[[<new-ws>]]`. Copied items stay.

3. **The new thread's side.**
   - Routing note, `<new-ws>/<new-ws>.md`, `type: routing`: the problem space, the parent it split
     from, and what the parent keeps.
   - First orientation, `lipika stamp --for <new-ws>/orientation`, with `from: "[[<parent>]]"`. It
     opens with `## What this is`: one or two sentences describing the new problem space — the scope
     every later split of this thread is judged against.
     Copy every moved and copied item, reworded freely, each citing the parent orientation it came
     from, with its own `as-of`. Carry the references still bearing on the work, citing the
     parent's traces; never copy a trace.
   - `gotchas.md`: the parent's entries that bear on the work, **verbatim**, under
     `## From [[<parent>]]`, with the header `orientation-carry --append-gotchas` writes.

4. **Prior art — read it yourself; never dispatch an agent.** Relatedness is judged against the
   parent's context, which only you hold.

   ```bash
   lipika pass-log start prior-art "<new-ws>" --scope workstreams --kind scout
   lipika threads --all          # every thread, archived and parked included
   lipika lineage <parent>       # the split chain
   ```

   Skip the parent and its lineage (already named). For every other thread whose work or system
   could bear on the new one, read its routing note, newest orientation and `gotchas.md`. Then write, in the new orientation:

   ```markdown
   ## Prior art
   - Lineage: [[<root>]] → … → [[<parent>]].
   - [[<thread>]] — what it found that bears on this work, in one or two sentences.
   ```

   **A bullet, not a paragraph.** Caveats, dates and detail stay in that thread, one link away; an
   orientation that restates its prior art grows with every split. `none found` when nothing bears. Do not list threads you rejected. Append each warning
   that bears on the work **verbatim** to the new `gotchas.md` under `## From [[<thread>]]`.

   ```bash
   lipika pass-log stop prior-art "<n> related of <m> read" --result incremental
   ```

5. **Check, commit once, close the pass.**

   ```bash
   lipika orientation-audit workstreams/<new-ws>     # follows from: and checks what was carried
   lipika orientation-audit workstreams/<parent>     # moved items must show under Settled
   lipika vault-commit -m "<≤72 chars>" -- <every path written>
   lipika pass-log stop spin-out "<new-ws>" --result incremental
   ```

   Do not touch `README.md`; the curator owns the index.

6. **Open as the new thread's pickup.** Your message, in order:
   - **needs a decision** — every ESCALATED item carried;
   - **where this is** — two or three sentences;
   - **prior art** — each related thread and what it found, and the warnings merged;
   - **what the owner wants explored first**, in words this message defined.

   Then call `EnterPlanMode`. The session now works the new thread.

## Don't

- **Don't change HEAD in the vault checkout, and don't push.**
