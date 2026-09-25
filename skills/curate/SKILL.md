---
name: curate
description: Decide, with the owner, which knowledge-base vault threads are finished and what in them still lives. Reads each thread in its own curator, in parallel, and opens with one table — what each thread asked, how it ended (answered, subsumed, superseded, abandoned, still live) and why — then what archiving would lose, then asks the owner to rule, and archives what he rules finished. Invoke when asked to "curate", "which threads are finished", "clean up the vault", "archive old threads", or "what can we close".
---

# curate — which threads are finished, and why

**The owner does not remember these threads.** A thread name is not a reason, and neither is its
title. Every line you show him says what the thread was for, in words for someone who never read it.
Run 1 of the curator gave a list of names and was unusable for exactly that reason.

**You move nothing until he rules.** Reading is free; a move is his call.

## Do

1. **Resolve the scope.** One workstream, a named set, or "finished candidates" — every thread that has
   not accrued in two weeks.

   ```bash
   cd "$(lipika vault-config path)"
   lipika threads        # live, newest first; `--all` includes parked/ and archive/
   ```

   The owner named no scope? Use finished candidates and say which threads that is, in one line.

2. **Dispatch one `lipika:curator` per thread, all in one message** so they run at once. Each reads
   and judges its own thread whole. That is one context per thread, not a reader feeding a judge —
   a split the owner ruled out. Give each exactly this:

   > Curate `workstreams/<thread>` for the owner. Which is it: finished, or still live? Move, write and commit
   > nothing. The other threads in scope are: <names>. Return the curation block.

   Naming the rest of the scope lets a curator see "subsumed by" and "duplicate".

3. **Assemble one report, in this order, and nothing before the table but one line of framing:**

   **The ledger** — one row per thread:

   | Thread | What it asked | Ended as | Why | Do |
   |---|---|---|---|---|

   - *What it asked*: one plain sentence. Never the title restated.
   - *Ended as*, from this list only: `answered` · `subsumed by <thread>` · `superseded by <thread>` ·
     `abandoned` · `still live`.
   - *Why*: one clause, with its evidence — the check that was run, or the line that says so.
   - *Do*: `archive`, `keep`, or `carry, then archive`.

   **Needs your ruling** — right after the table, one line each. List every unruled escalation and every
   item that archiving would lose, with the thread it lives in. Never let one appear only in the detail.

   **What carries where** — each live item in a thread you advise archiving, and where it goes: a
   named live thread, a new thread with its question, or `nowhere, because …`. Skip items already
   carried verbatim elsewhere; name that thread once instead.

   **Detail** — the curators' per-item tables. Write them to a scratch file outside the vault and
   link it, rather than printing them in the message.

4. **Ask for rulings.** Skip this step when told to report only. Use `AskUserQuestion`: one question per thread
   you advise archiving, four to a call, and options from its row — *Archive*, *Keep*, *Carry first*.
   Describe each option in the thread's own plain words, never with a term the report did not define.

5. **Carry out the rulings.**
   - **Carry first**: hand the live items to the receiving thread's next handoff, by name.
     Never edit that thread's orientation: it is a view, written only by a handoff.
   - **Archive**: run `lipika archive-thread <thread>` once per thread, then commit the paths it
     prints with `lipika vault-commit`. It moves files through Obsidian so links follow.
   - Then run `lipika dangling-links .` from the vault root and report the count before and after.
   - Finally, dispatch a `lipika:curator` to regenerate the index.

## Don't

- **Don't read the threads yourself.** Your context is the one the owner talks to; the curators' are
  discarded.
- **Don't archive a thread he has not ruled on**, and never `mv` or `git mv` one.
- **Don't repeat a document's claim about a repo or PR** — the curators check them; carry their result.
