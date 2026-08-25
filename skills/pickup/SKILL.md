---
name: pickup
description: Orient at the start of a session that will touch the knowledge-base vault — the durable cross-session memory for engineering work (a separate git repo / Obsidian vault spanning every project I work on). Reads the current orientation document for the thread being picked up, audits it against the one before it to catch anything that vanished without a disposition, judges how fresh each live item actually is, and opens with what needs the owner's decision. Read-only; it asks what the owner wants explored first, then ends in plan mode. Invoke at the start of a session, when resuming work someone else handed off, or when asked to "pick up where we left off", "get oriented", "what's the state of X", or "read the handoff".
---

# pickup — orient before you write

The counterpart to `context-dump`. A handoff wrote an orientation; you read it, check it, and say what the
owner needs to decide. **You write nothing.**

**The vocabulary an orientation assumes.** Every vault document is a **record** — dated and never edited,
corrected only by a newer document: dumps, `reference/` traces, `sources/`, `external/`, and every
orientation already written — or a **view**, regenerated wholesale and never patched: the current
orientation and the index. `architecture/` is a long-lived edited view and the owner's alone.

**And three tiers, of which only the middle one carries state.** A **grand plan** (`grand-plans/`) is a
standing want with no liveness — not started is not dead. An **epic** (`epics/`) is a large effort actually
happening: live, parked or finished, and parked is a decision someone made. A **workstream**
(`workstreams/`) is one question being answered, and it has **no status field** — the date it last accrued
is the whole answer, so a thread that stopped is simply not listed as live. An epic *cites* its threads
rather than containing them, so membership is prose in the epic and there is no frontmatter field to
check. Grand plans and epics are the owner's; agents write workstreams.

## Do

1. **Resolve where you are.**

   ```bash
   cd "$(lipika vault-config path)"
   git log -12 --name-only --pretty=format:'%h %ad %s' --date=short -- workstreams/
   ```

   Name the thread and let the owner redirect you. If the task described matches no live workstream, say
   so — that is usually a new thread rather than a wrong guess.

2. **Read the newest orientation, and only that one.**
   `workstreams/<ws>/orientation/` sorts by name; the last is current. Read one.

3. **Audit it against its predecessor.**

   ```bash
   lipika orientation-audit workstreams/<ws>
   # 0 checked and clean · 1 something to look at · 3 NOTHING WAS CHECKED
   ```

   **This is a recall aid, not a gate, and there is no failure exit.** It hands you the items the last
   orientation carried that this one does not. Every live item should have been carried, so anything
   listed here either had its death condition fire — check `## Settled since the last orientation` — or
   the last handoff lost it. Report which.

   **Exit 3 is not a pass.** A thread's first orientation has no predecessor, so nothing was verified —
   including whatever it claims to have carried across from a parent. Say so plainly rather than reporting
   a clean audit, and treat its "Settled since the last orientation" section as the author's self-report,
   which is what it is.

4. **Find the items worth one command, and run those commands.** Not "read every `as-of`" — on a thread
   that moved today every item is stamped today, and scanning forty dates returns nothing. Two cold runs
   both skipped the scan and did this instead.

   Ask of each item: **is its death condition checkable right now, in one call?** `is PR #N merged`,
   `does that file still exist`, `is the branch gone`. Run those; a confirmed item is worth more than a
   fresh-looking date, and a fired one you catch here is a drop the next handoff will not have to make.

   Then weigh `as-of` for the rest — **each item's own, not the document's date**. An item carried
   unchanged through six handoffs inherits today's filename and reads as fresh. More recent supersedes
   older, as **a prior, not a rule**: reach back into dumps when the newest document is thin or wrong.

5. **Ask whether the question has changed.** You have just read the whole live set, which no other agent
   does — a handoff is nearly out of budget and a `scout` is barred from the call. A workstream is one
   question being answered; if the items are now answering a different one, say so. That is a new dated
   workstream, and a split is where items stop being carried. Threads are meant to be short, so expect
   this to be yes more often than it feels like it should be.

6. **Ask whether an architecture document is missing.** You read cold, so you are the one who feels it: is there a
   system here you must work on that nothing describes?

   ```bash
   lipika architecture-candidates    # 0 nothing to recommend · 1 CANDIDATES FOUND, not an error
   ```

   Do not wrap this in `set -e`.

   The check is mechanical and your own experience is not; report both. **Recommend, never write** —
   `architecture/` is the owner's. Carry pointers: which system, which traces back it, which dumps
   disagree, and the question an architecture document would answer.

7. **Open with what the owner needs.** Your first message is, in this order:

   - **Needs a decision** — every ESCALATED item. This is the most useful thing you will say; put it first.
   - **Where this is** — two or three sentences, from the orientation. Not a summary of the whole thread.
   - **What the audit found** — drops caught, or that it was clean, with the exit code.
   - **Stale live items** — anything whose `as-of` argues it should be re-checked before being relied on.
   - **A missing architecture document**, if you found one.
   - **That this has become two threads**, if it has.

8. **Summarise in plain language before you ask anything.** Laconic, terse, salient: what you now
   know, in the words you would use to someone who has not read the thread. This is not the step-7
   report again — that is for orienting; this is for someone about to answer a question.

   **The live set is written in vocabulary the owner never agreed to.** Grader keys, agent-local
   codenames, design terms sealed in sessions he was not in. They read as shared and are not.

9. **Ask what the owner wants explored first, using only words your summary introduced.** Ask before a
   plan has formed, not after. This asks for an agenda, not for permission.

   **No question or option may name a term that summary did not define.** If an option needs one, the
   summary earns it first, or the option is rewritten without it. Measured 2026-08-25: a run put
   *"Key 2's own falsifier"*, *"span on the one operation inside the north star"* and *"the weaker
   moment"* to the owner as though the frames were shared. He could not answer what he could not
   parse, and said so.

   **Carry your findings into their answer rather than dropping them.** When the answer redirects the
   work, say which findings still bear on it.

   Then call `EnterPlanMode`.

## Don't

- **Don't read every dump.** Reach into one for evidence behind a specific item, not to reconstruct the
  story.
- **Don't read two orientations as two accounts of now.** The older one is a record of a past moment.
- **Don't fix what the audit found.** You are read-only. It goes in your report, and into your dump later.
- **Don't write, move or edit anything** — no records, no views, and not `architecture/`.
- **Don't skip the escalations** because they look like context. They are the reason a human is reading.

## When there is no orientation

A thread nobody has handed off yet has no `orientation/`. Say so plainly, read the routing note and the
newest two or three dumps instead, and report that the first handoff out of this session will create one.
Do not build one yourself: it would be a view written by someone who has not done the work.
