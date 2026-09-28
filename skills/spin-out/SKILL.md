---
name: spin-out
description: Open a new knowledge-base vault thread split from a parent, because the question has changed. Writes the parent's handoff recording what moved, the new thread's routing note and first orientation, reads prior art across every thread itself, and ends as the new thread's first pickup. Invoke when asked to "spin out", "split this thread", "open a new thread for X", or when pickup or context-dump finds the question has changed.
---

# spin-out — open a thread, carry what bears on it, find its prior art

A workstream is one question. When the question changes, the answer is a new dated thread, and this
skill opens it: the parent's side, the new thread's side, and the prior art nothing links to yet.
It ends as the new thread's first pickup, so the session carries on in the new thread.

**Everything context-dump says about records, views, stamps, typed live items and commits holds
here.** Read the vault's `CLAUDE.md` if you have not. This skill does not invoke context-dump: a
nested skill call ends this one's timing in `lipika perf`, and the run is measured as one span.

## Do

1. **Name the parent and the new question, and open the pass.**

   ```bash
   cd "$(lipika vault-config path)"
   lipika pass-log active --scope workstreams/<parent>
   lipika pass-log start spin-out "<new question>" --scope workstreams/<parent> --kind dump
   ```

   The new thread is `workstreams/YYYY-MM-DD-<question-slug>/`, today's date, the slug phrased as
   the question. Read the parent's newest orientation and its `gotchas.md`, and decide which live
   items **move** (bear only on the new question), which are **copied** (bear on both) and which
   stay.

2. **The parent's side: a dump and a new orientation.** The dump
   (`lipika stamp --for workstreams/<parent>/dumps`) says the thread split, why, and what moved. The
   orientation (`lipika stamp --for workstreams/<parent>/orientation`) is
   `lipika orientation-carry <parent>` with the moved items deleted and written under
   `## Settled since the last orientation` as moved to `[[<new-ws>]]`. Copied items stay.

3. **The new thread's side.**
   - Routing note, `<new-ws>/<new-ws>.md`, `type: routing`: the question, the parent it split from,
     and what the parent keeps.
   - First orientation, `lipika stamp --for <new-ws>/orientation`, with `from: "[[<parent>]]"`.
     Copy every moved and copied item, reworded freely, each citing the parent orientation it came
     from, with its own `as-of`. Carry the references still bearing on the question, citing the
     parent's traces; never copy a trace.
   - `gotchas.md`: the parent's entries that bear on the question, **verbatim**, under
     `## From [[<parent>]]`, with the header `orientation-carry --append-gotchas` writes.

4. **Prior art — read it yourself.** You hold the parent's context, so the relevance call is yours.

   ```bash
   lipika pass-log start prior-art "<new-ws>" --scope workstreams --kind scout
   lipika threads --all          # every thread, archived and parked included
   lipika lineage <parent>       # the split chain
   ```

   Skip the parent and its lineage (already named). For every other thread whose question or system
   could bear on the new one, read its routing note, newest orientation and `gotchas.md` — one
   workstream at a time, never a grep of the vault root. Then write, in the new orientation:

   ```markdown
   ## Prior art
   - Lineage: [[<root>]] → … → [[<parent>]].
   - [[<thread>]] — what it found that bears on this question, in one or two sentences.
   ```

   **A bullet, not a paragraph.** Caveats, dates and detail stay in that thread, one link away; an
   orientation that restates its prior art grows with every split.

   `none found` when nothing bears. Do not list threads you read and rejected. Append each warning
   that bears on the question **verbatim** to the new `gotchas.md` under `## From [[<thread>]]`.

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

   Do not touch `README.md`; the curator owns the index, and a new thread is absent from it until
   one runs.

6. **Open as the new thread's pickup.** Your message, in order:
   - **needs a decision** — every ESCALATED item carried;
   - **where this is** — two or three sentences;
   - **prior art** — each related thread and what it found, and the warnings merged;
   - **what the owner wants explored first**, in words this message defined.

   Then call `EnterPlanMode`. The session now works the new thread.

## Don't

- **Don't dispatch an agent to read prior art.** The judgement needs the parent's context.
- **Don't invoke another lipika skill.** It ends this skill's `perf` span.
- **Don't move an item that also bears on the parent.** Copy it.
- **Don't change HEAD in the vault checkout, and don't push.**
