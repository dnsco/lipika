---
name: curate
description: Decide, with the owner, which knowledge-base vault threads are finished, what in them still lives, and whether they are drawn along the right lines. Groups the threads by split lineage, then repo, then system, reads each group in its own curator in parallel, and opens with one table: what each thread asked, how it ended (answered, subsumed, superseded, abandoned, still live, re-partitioned) and why. Then it lists what archiving would lose and any proposed re-partition — N threads redrawn as M, duplicates collapsed — asks the owner to rule, and carries out what he rules. Invoke when asked to "curate", "which threads are finished", "clean up the vault", "archive old threads", "re-partition the threads", "these threads overlap", or "what can we close".
---

# curate — which threads are finished, and where the lines should be

**The owner does not remember these threads.** A thread name is not a reason, and neither is its
title. Every line you show him says what the thread was for, in words for someone who never read it.

**You move nothing until he rules.** Reading is free; a move is his call.

## Do

1. **Resolve the scope.** One workstream, a named set, or "finished candidates" — every thread that has
   not accrued in two weeks.

   ```bash
   cd "$(lipika vault-config path)"
   lipika threads        # live, newest first; `--all` includes parked/ and archive/
   ```

   The owner named no scope? Use finished candidates and say which threads that is, in one line.

2. **Partition the scope into groups**, first rule that applies:
   - threads of one split lineage are one group — `lipika lineage --json`, its `lineages`. A
     lineage may span repos, and it is what ties threads of one body of work together;
   - else threads working in the same repo, per their routing note;
   - else threads whose routing notes name the same system.

   Say the groups in one line each before dispatching.

   **Never one curator per thread.** Curation's goal is merging, and a curator that sees one thread
   cannot judge whether a sibling absorbed it, or whether the two are one body of work.

3. **Dispatch one `lipika:curator` per group, all in one message** so they run at once. Each reads and
   judges its group whole, in its own context — not a reader feeding a judge, a split the owner ruled
   out. Give each exactly this:

   > Curate these threads, as one group, for the owner: <workstreams/…, one per line>. For each: finished,
   > or still live — and which of them subsume, supersede or duplicate each other, and whether the group
   > should be re-partitioned along different lines. Move, write and commit nothing. Other groups in
   > scope: <names>. Return one curation block per thread, and a REPARTITION block per proposal.

4. **Assemble one report, in this order, and nothing before the table but one line of framing:**

   **The ledger** — one row per thread:

   | Thread | What it asked | Ended as | Why | Do |
   |---|---|---|---|---|

   - *What it asked*: one plain sentence. Never the title restated.
   - *Ended as*, from this list only: `answered` · `subsumed by <thread>` · `superseded by <thread>` ·
     `abandoned` · `still live` · `re-partition into <new thread>`.
   - *Why*: one clause, with its evidence — the check that was run, or the line that says so.
   - *Do*: `archive`, `keep`, `carry, then archive`, or `re-partition`.

   **Needs your ruling** — right after the table, one line each. List every unruled escalation and every
   item that archiving would lose, with the thread it lives in. Never let one appear only in the detail.

   **What carries where** — each live item in a thread you advise archiving, and where it goes: a
   named live thread, a new thread with its question, or `nowhere, because …`. Skip items already
   carried verbatim elsewhere; name that thread once instead.

   **Re-partitions** — per proposal: the threads in, and for each thread out its slug and its
   description in one or two plain sentences, with a count of the items it would carry and how many
   duplicates collapsed. The item-by-item map goes in the detail file.

   **Detail** — the curators' per-item tables and item maps. Write them to a scratch file outside the vault and
   link it, rather than printing them in the message.

5. **Ask for rulings.** Skip this step when told to report only. Use `AskUserQuestion`: one question per thread
   you advise archiving, and one per proposed re-partition, four to a call. Options come from the row —
   *Archive*, *Keep*, *Carry first* — and for a re-partition *Re-partition as proposed*, *Keep as is*.
   Describe each option in the thread's own plain words, never with a term the report did not define.

6. **Carry out the rulings.**
   - **Carry first**: hand the live items to the receiving thread's next handoff, by name.
     Never edit that thread's orientation: it is a view, written only by a handoff.
   - **Archive**: run `lipika archive-thread <thread>` once per thread, then commit the paths it
     prints with `lipika vault-commit`. It moves files through Obsidian so links follow.
   - **Re-partition**: write each new thread here, from the curator's `REPARTITION` block. Do not
     invoke `/lipika:spin-out` — a nested skill call ends this one's span — but write what it writes:
     - `workstreams/YYYY-MM-DD-<slug>/<same>.md`, `type: routing`: the problem space, and the threads
       it came from.
     - Its first orientation, at `lipika stamp --for <new-ws>/orientation`, with every parent in
       `from:` as a YAML list (`from:` then one `  - "[[<thread>]]"` per parent). It opens with
       `## What this is`, the description, then `## Where this is`, then `## Needs the owner` and
       `## Live items` holding exactly the `ITEM`s mapped to it — each once, verbatim, keeping its own
       `as-of`, naming the thread it came from. `## Prior art` names the parents.
     - `gotchas.md`: each parent's entries that bear on the new problem space, verbatim, under
       `## From [[<parent>]]`. Read those files yourself; they are short.
     - In each thread in, a dump (`lipika stamp --for workstreams/<thread>/dumps`) recording the
       re-partition and where each of its items went.

     Commit these with `lipika vault-commit`, then `lipika orientation-audit` each new thread — it
     compares against every parent, and names an item no new thread carried with the parent it came
     from. Then archive every thread in, as above.
   - Then run `lipika dangling-links .` from the vault root and report the count before and after.
   - Finally, dispatch a `lipika:curator` to regenerate the index.

## Don't

- **Don't read the threads yourself** beyond the `gotchas.md` a re-partition copies. Your context is
  the one the owner talks to; the curators' are discarded.
- **Don't archive a thread he has not ruled on**, and never `mv` or `git mv` one.
- **Don't repeat a document's claim about a repo or PR** — the curators check them; carry their result.
