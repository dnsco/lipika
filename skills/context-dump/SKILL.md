---
name: context-dump
description: Append-only capture of working context into the knowledge-base vault — the durable cross-session memory for engineering work (a separate git repo / Obsidian vault spanning every project I work on). Use whenever you have learned something worth persisting, and at the end of a session or before a handoff, when it also writes the next orientation document a fresh agent will read. Invoke when asked to "dump context", "write a handoff", "save findings to the vault", "checkpoint the workstream", or before ending a long session.
---

# context-dump — write a record, and on the way out write the next orientation

Two modes.

- **A dump**, any time you have learned something worth keeping. One dated document.
- **A handoff**, when the session is ending. The dump, **plus** a new orientation document for whoever
  picks this up next.

## The rule underneath everything here

**Every document in the vault is a record or a view.**

- **A record is never edited.** Dumps, `reference/` traces, `sources/`, `external/`, and every orientation
  already written. Correct one by writing a newer one.
- **A view is regenerated wholesale, never patched.** An orientation is a view written *as* a record: fresh
  each handoff, newest wins.
- **`architecture/` is the owner's.** Contradict it with a dated trace; never edit it.

**Your dump is the store; the orientation is a projection over it.** The dump carries the **delta** — what
this session discovered and what it killed — and an orientation is the previous one plus the deltas since.
Write the delta even when not handing off: it is what survives a session that ends without one.

## Shape

```
grand-plans/<name>.md            a standing want. No liveness. The owner's
epics/<name>.md                  a large effort happening. live · parked · finished. The owner's.
                                 CITES its threads; does not contain them
workstreams/YYYY-MM-DD-<thread>/ one question being answered. NO status field
  YYYY-MM-DD-<thread>.md         routing note — what this thread is. Dated to match the folder
  orientation/<stamp>.md         newest wins. Written at handoff
  dumps/<stamp>-<topic>.md       <- YOUR DUMP GOES HERE
  reference/YYYY-MM-DD-<topic>.md  dated traces from source
```

**Only the epic tier carries state.** An epic is parked by a decision; a workstream falls off by date, so
a second shelf concept there would only disagree with the date. Membership is the epic's prose — no
frontmatter field.

One workstream is **one thread of work** — one path prefix, one agent at a time. A second concurrent thread
is a **new dated workstream**, not a subfolder; see step 4a. Resolve the vault with
`lipika vault-config path`. Full conventions: the vault's `CLAUDE.md`, which a session rooted in a code
project does **not** load automatically — read it if you have not.

**A workstream with no `dumps/`**: create it and write there; leave every existing document where it is.

## Do

1. **Find the home, name your choice, let the owner redirect.** Usually the most recently touched workstream.
   **A workstream is one question being answered.** When the question has changed, the answer is a new
   dated workstream — that is the normal path, not the exception, and threads are meant to be short. More
   of the same one only when it is the same question.

   ```bash
   cd "$(lipika vault-config path)" && git log -12 --name-only --pretty=format:'%h %ad %s' --date=short -- workstreams/
   lipika pass-log active --scope workstreams/<ws>     # is anyone else in here?
   ```

   Say it in one breath: *"Dumping into `workstreams/2026-08-21-x/`."* If an open pass overlaps, say so
   before you write — a STALE record is an agent that died, not one still working.

   ```bash
   lipika pass-log start context-dump "<what you are dumping>" --scope workstreams/<ws> --kind dump
   ```

2. **Write the dump** — `workstreams/<ws>/dumps/<stamp>-<topic>.md`. Several a day is normal, so the
   time is in the name, and **the name comes from the tool, never from `date`**:

   ```bash
   lipika stamp --for workstreams/<ws>/dumps     # UTC to the second, checked against what is there
   ```

   `date` is local time, and a name that does not sort last is invisible to `pickup` — the file writes,
   the commit succeeds, the handoff reports done, and nothing is loud. **If it exits 1, an existing name
   is ahead of the clock; it tells you when that heals. Wait — never invent a later name.** Inventing is
   what put those names ahead in the first place.

   Frontmatter: `type` / `status` / `date` / `tags`. **No `up:`** — retired 2026-08-25; the folder
   already says which thread this is.

   - **What you did and what came of it** — PR numbers, commit shas, branch names, what is green and what
     is red.
   - **Answer the questions you inherited.** For each open question or warning you touched: resolved (with
     the evidence), still open, or now understood differently.
   - **A scannable `## Live items` block — YOUR DELTA, not the inherited set restated.** What this
     session *discovered*, plus what it *killed* with the evidence that killed it. An item you neither
     found nor changed belongs to the orientation, not here; repeating it several times a day is how two
     documents start disagreeing. Collected, not scattered through prose, one per line:

     `[TYPE] statement — trigger → consequence → dies when <condition> · as-of YYYY-MM-DD`

     - **GATE** — a blocking precondition or ordering. The outage-class risk.
     - **LANDMINE** — breaks silently or burns time, with a known avoidance.
     - **OPEN Q** — unresolved, and agents can work on it.
     - **ESCALATED** — unresolved, and **only the owner can decide it**. An item routed here reaches a
       human; an OPEN Q does not.
     - **DEAD END** — ruled out, with the reason. It has no death condition; it fires forever.

     **Every item carries a death condition** — what would make it stop being true. An item you cannot
     write one for is usually two.

     **`as-of` is when the item was last *confirmed*, not last copied.** Carrying an item forward does not
     refresh its date.
   - **State, with its basis.** What landed and how you know: `merged #4131`, `commit a1b2c3d`, `gate
     green`. A draft or open PR has not landed. Asserting judgement instead is fine — say so:
     *judgement: the remaining work no longer describes this thread*. **An unstated basis is the only
     unacceptable one.**
   - **Reusable commands** — the exact incantation. A real script goes in Lipika's `tools/`, not the vault.
   - `[[wikilinks]]` to vault docs; literal text for code-repo paths, with the repo named.

3. **Second pass — what did not make it in?** Before you commit: what would a cold-start you need in a
   month? Sweep for implicit decisions made without the *why*, dead ends ruled out without the reason,
   environment traps, and concrete current state. Route anything new into `## Live items` in the typed
   shape rather than into loose prose.

4. **If this is a handoff, write the next orientation** — `lipika stamp --for
   workstreams/<ws>/orientation`. This is the name `pickup` reads, so sorting last is the whole document.

   **An orientation is a projection over the records: previous orientation + every dump delta since.**
   Read them and write a **new** document. Do not diff-and-patch the old one in your head, and do not
   write from session memory — the dumps are the evidence trail the next agent gets.

   ```markdown
   ---
   type: orientation
   status: current
   date: YYYY-MM-DD
   from: "[[YYYY-MM-DD-<parent-thread>]]"   # only on a thread's FIRST orientation
   ---

   ## Where this is
   Two or three sentences. What this thread is for and what state it is in.

   ## Needs the owner
   Every ESCALATED item. If there are none, say so.

   ## Live items
   Every carried GATE / LANDMINE / DEAD END / OPEN Q, in the typed shape, each with its own `as-of`.

   ## Settled since the last orientation
   One line per item whose death condition fired, with the evidence.

   ## Recent narrative
   The last handful of dumps, newest first, one or two sentences each, linked.
   ```

   **Carry every live item forward.** An item leaves the live set only when its death condition has
   fired — name which, with the evidence. Do not select: a long set about this thread is not the failure
   mode, and choosing for the next agent is a call you are the worst placed to make.

   **A live item states itself.** "See [[2026-08-19-the-thing]]" is a pointer, and a warning has to fire
   at an agent who does not know to look. Link the detail *after* the statement, never instead of it.
   `## Recent narrative` is the one place a pointer is the content.

4a. **If you are opening a new thread, its first orientation COPIES what still bears on it.**

   A split is not a link. Read the parent thread's current orientation and copy across every live item
   that bears on the new thread — reworded freely, each citing the source it came from — then name the
   parent in `from:`. Items that do not bear on it stay behind; that is the whole point of splitting.

   ```bash
   lipika orientation-audit workstreams/<new-ws>    # follows `from:` and checks what you carried
   ```

   **Do not touch `README.md`. The index has exactly one author, and it is the `curator`.**

   **A new thread is invisible to a human browsing the index until a curator runs, and that is the
   accepted cost.** Say so if it matters to the owner; do not fix it here. This step used to append
   the thread's line — link, question, epic — while the curator regenerated the same list as *what
   the thread is, live or finished, with dates*. Two authors, two shapes: an appended line never
   looked curated, and the next curator run overwrote it. Removed 2026-08-25 on the ruling that
   keeping a view current buys churn and disagreement, and that a view regenerated rarely is worth
   more than one patched constantly.

   **Do not compensate by asking for a curator run** — no cadence, no trigger, no "run the curator
   after a split". That reintroduces exactly the churn this removed.

5. **Commit** in the vault, which is its own repo. Stage **specific paths** — never `git add -A`, never a
   bare `commit`, because other sessions write here.

   ```bash
   cd "$(lipika vault-config path)" && lipika vault-commit -m "…" -- <your paths>
   ```

   **Never change HEAD.** No `git checkout -b` — the checkout is shared, so a branch moves HEAD for every
   session in it. Don't push unless asked.

6. **Close the pass.**

   ```bash
   lipika pass-log stop context-dump "<the dump you wrote>" --result incremental
   ```

   `--result aborted` if you did not write. An unclosed `start` reads as someone still working in here.

7. **If a deploy happened this session, end by printing the next session's prompt — and nothing after it.**

   Only when the machinery was redeployed. An incremental dump is not a handoff to a restarted
   session, and a restart nobody needs trains the reader to skip the block.

   ```bash
   lipika handoff-prompt <workstream>
   ```

   **Print its output verbatim as the last thing in your message.** It arrives already fenced; do not
   unwrap it, do not add a sentence inside the fence, and do not follow it with anything the reader
   would have to scroll past. The paste is what survives — commentary above it is read past.

   **It refuses rather than warns**, exit 3, when the tree is not what is installed or the two
   manifests disagree with the installed version. A refusal is not something to work around or
   paraphrase: it means the deploy did not happen, so there is no valid handoff to write yet. Deploy,
   then run it again.

   It composes the prompt from the machine — the installed version, that version's gate command, and
   every grader whose `about:` names this thread. **It does not restate the live set**, and neither should
   you: the orientation you just wrote is what the next session reads.

## Don't

- **Don't move documents.** Nothing is archived.
- **Don't write a second live orientation for one thread.** If the work has become two threads, that is a
  second dated workstream, and say so.

## Voice

Terse and factual, written for a first-time reader who was not in the room. **No agent-local codenames** —
"Option C", "Track B", "Phase 2", workflow IDs — say what a thing *is*. Filenames carry their stamp:
`YYYY-MM-DD-HHMMSS-topic.md` for dumps and orientations, from `lipika stamp`; `YYYY-MM-DD-topic.md`
elsewhere.
**Timestamp every metric**: "9 KB at 2026-08-21", never "9 KB". Better still, cite the reference and let a
tool answer the number.
