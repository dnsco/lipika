---
type: reference
status: reference
date: 2026-08-21
tags: [vault, meta, agents, ontology, design, roles, tools]
---

# The design — what shape this system has, why, and what each role runs

The single design document for the vault and the machinery that maintains it.

**It carries no measurements. It carries parameters.** A **measured figure** is record and lives in
`sources/evals/`, dated and frozen; a **chosen threshold** is a design decision and is revisable here.
Where a claim rests on a measurement, it points.

**Not normative.** `CLAUDE.md` and the skill and agent definitions win on any conflict of wording.

**Markers:** `✅` built and in force · `⏳` partly · `▢` designed, not built · plus
`[GATE]` / `[OPEN Q]` / `[DEAD END]` as elsewhere.

## 1. What this is for, and the choice that constrains everything

The vault is durable cross-session memory for engineering work: a **cohesive corpus** read by agents that
need continuity, deliberately not a stochastic index.

- **What it buys.** Facts arrive **whether or not the agent thought to ask for them** — the only reason a
  recorded dead end ever prevents anything.
- **What it costs.** Curation is slow, and it is work.
- **Why the trade holds.** The corpus's most valuable contents are *negative* results: ruled-out
  approaches, gates, landmines. A negative result's trigger is someone about to re-propose the thing, and
  that person by definition does not know to query for it. Pull retrieval cannot fire on the absence of a
  query. This is the argument for a **push** surface, and it is independent of retrieval technology.

**The first force: work evolves.** A push surface works only while what it pushes is about the work at
hand, and while it is short enough to be read at the moment of proposing. Pieces of work emerge, change
what they are about, and finish. Context must be partitioned as they do, or one surface accumulates
everything the effort ever contained.

**The second force: this is agents writing for agents.** The reader who arbitrates content is an
occasional scanner, checking orientation and correcting mistakes. So: **act, then report for correction**,
not ask then act.

## 2. The goals

Judge every change against these, in order.

1. **An agent is pushed what bears on its work, and little else.** Relevance first, volume second.
2. **A warning fires unprompted or it does not count.**
3. **Nothing that was written down becomes unfindable.**
4. **Any operation somebody waits on finishes inside two minutes.**
5. **Adoption is incremental.** No shape is worth a re-architecture.
6. **Every claim names its enforcement, or admits it has none.**

### Goal 4 is a north star, and twice it has been mistaken for a limit

**Span** is the quantity: wall clock from a pass's `start` to its `stop`, computed by `pass_log.py` as
`span_s`. Neither token cost nor reasoning time — **what a human waits.**

**Two minutes is aspirational, for any operation, and is a ceiling on no role.** Both times it hardened
into a limit it did damage: scoped as the `frontier-clerk`'s ceiling, which a fan-out pass at
`max(child) + overhead` can never meet, and which produced two sub-librarians' "confessions"; and as
*every required step is wall clock spent against the budget*, withdrawn for discouraging the tools §10
argues are the cheap end. **Eval, profiling and developer-facing work are exempt.**

`lipika span-report` prints the series and **always exits 0**. A check that fails is how this hardens a
third time. **An operation over the star is a fact, not a backlog item** — this document is not a frontier
(§12), and a table of misses is the most inviting way for it to become one.

Measured 2026-08-21, over 57 passes:

| operation | median | inside |
|---|---|---|
| `context-dump` — the only synchronous one | 114 s | 11/18 |
| `pickup` | 97 s | not in the log — read-only, opens no pass |
| `curator` | 1407 s | 1/4 |

The 264 / 368 / 420 s figures quoted for `context-dump` are pre-redesign; the recent series is 117, 181,
39, 97 s. **A figure repeated from memory outlives the thing it measured** — which is the argument for the
tool, not for the target.

## 3. Records and views — the rule everything else follows from

**Every document is a record or a view. Nothing is both.**

| | record | view |
|---|---|---|
| dated | yes | yes, except `architecture/` |
| edited | **never** | regenerated wholesale, never patched |
| corrected by | writing a newer document | regenerating |
| examples | dumps, `reference/` traces, `sources/`, `external/`, every orientation already written | the current orientation, the vault index, `architecture/` |

**Why this is the whole design.** The vault previously had a third class — mutable *and* authoritative:
the task frontier and the parent register. That class was the entire maintenance bill. It needed surgical
edits, so it needed a slice tool and line citations; it needed a licence check so an edit could not claim
more than its evidence; it needed a losslessness gate because an edit could drop a fact; it needed a byte
budget because it accumulated; it needed a closure primitive to bound the accumulation; and it needed a
role of its own to do the editing. Seven tools and one role, all serving one class of document.

Removing the class removes all of it. A view needs no losslessness gate because its sources are intact and
a bad regeneration is fixed by regenerating again. It needs no surgical discipline because you rewrite the
file. It cannot go over budget because you regenerate under a target rather than trimming an accumulator.

**The three older append-only tiers keep their own reasons**, which is why they generalise differently:
`sources/` because an edited transcript is no longer a transcript and every document citing it now quotes
something that was never said; `external/` because rewriting a delivered artifact makes the record
disagree with what people received; a dump because it is evidence of a moment.

✅ **`architecture/` is the one long-lived edited view, and only the owner writes it.** One written by an agent
fails worse than a stale one: it becomes the most-linked document in the vault with no dated
evidence positioned to contradict it, and nothing in the system is placed to disagree with it. Agents
produce the dated `reference/` traces behind it and **contradict it with them** — which is an ESCALATED
item, and the loop that keeps it honest.

## 4. The document ontology

```
vault/
  README.md                        VIEW — the index of threads. Regenerated.
  architecture/<system>.md         VIEW — the owner's. Stable name, no date, as-of <sha>.
  reference/YYYY-MM-DD-<topic>.md  RECORD — a trace from source, cross-thread
  workstreams/
    YYYY-MM-DD-<thread>/
      YYYY-MM-DD-<thread>.md       the routing note. Dated to match the folder.
      orientation/YYYY-MM-DD-HHMM.md   VIEW-as-record. Newest wins.
      dumps/YYYY-MM-DD-HHMM-<topic>.md RECORD — several a day is normal, so it carries the time
      reference/YYYY-MM-DD-<topic>.md  RECORD — a trace, thread-local
  sources/  external/  values/  grand-plans/     RECORD
```

✅ **One workstream is one thread of work** — one path prefix, one agent at a time. That makes the pass
log's prefix partition exactly right rather than approximate.

✅ **Heaviness is concurrent threads, not bytes.** Two hundred dumps on one thread cost nothing: orientation
is still one document and dumps are read on demand. Forty dumps across three concurrent efforts is already
too heavy at a fifth the size. **A second concurrent thread is a new dated workstream** — which is why
there is no task tier, no closure ceremony and no `done/`.

⏳ **A thread is short-lived, and splitting is the metabolism rather than a release valve.** A workstream
is one question being answered; when the question changes, the answer is a new dated workstream, not more
of the old one. Carrying every item forward (§5) is safe only because of this — a thread that lives for
months accumulates a live set nothing bounds, and the retired byte budgets were the wrong fix for the
right problem. **Selection did not die with per-handoff dropping; it moved to the split**, which is the
moment with enough information to make the call.

Three things follow, and they are the cost of the bet:
- **A finished thread's last orientation is its citable summary**, and it is sound as one precisely because
  nothing will supersede it. This is what other threads reference.
- **The index carries the navigation**, because there will be many folders. It stops being housekeeping.
- **Liveness is "accrued a dump recently"** — so most threads are dead most of the time, and any tool that
  counts threads must exclude the dead ones or it counts mostly noise.

Falsified by threads that keep needing to be merged back, or by a corpus where finding the live thread
costs more than reading a long orientation would have.

✅ **Three tiers, and only the middle one carries state.** Built 2026-08-21: `epics/` exists, and the five
efforts that were shelved in `workstreams/parked/` are parked epics.

| tier | what it is | liveness | state | written by |
|---|---|---|---|---|
| grand plan | a standing want | none — not started is not dead | none | the owner |
| **epic** | a large effort actually happening | live · parked · finished | **parked is explicit** | the owner |
| workstream | one question being answered | accrues, or falls off by date | none | agents |

**An epic can be parked; a workstream simply falls off.** Parking is a decision about a commitment, so it
belongs where commitments live — a handful of documents a person owns, never the twenty-plus dated folders
a short-thread regime produces. This is why liveness at the workstream tier needs no status field: the date
a thread last accrued is the whole answer, and any shelf list at that tier is a second concept that will
disagree with the first.

**An epic is a document that cites its threads, not a folder containing them** — `epics/<name>.md`, a view,
regenerated. Threads stay where they are, so no link breaks. A **finished** epic is the citable summary of
a completed body of work, sound as one for the same reason a dead thread's last orientation is: nothing
will supersede it.

`workstreams/parked/` was this rule violated — five separate efforts under one prefix, shelved at the
workstream tier because there was nowhere else to put them, which is also why `architecture-candidates`
counted them as one voting thread. Moved to `epics/` 2026-08-21.

**Membership is the epic's prose, and no frontmatter relation was added for it.** `up:` had exactly one
consumer — `scope_recon` reporting which documents *lacked* it — and nothing read the value; contrast
`from:`, which `orientation-audit` follows to find a parent thread's items. A second mostly-empty field
would have been a third thing to keep true, defended by a nag. The nag is retired.

✅ **A split COPIES what still bears on the new thread; it does not point at it.** The new thread's first
orientation carries the parent's still-live items across, reworded freely and each citing its source, and
names the parent in `from:`. Items that do not bear on the new thread stay behind — that is what splitting
is for. This is the one piece of the retired carry-across that survives, and it survives because the
*mechanism* was tied to task closure while the *duty* is tied to §1: a pointer is pull, and pull cannot
fire on an agent who does not know to look. Measured across this system's history, every mechanism that
relied on someone following a link to find a warning failed, and every one that put the warning in front
of the reader worked. `orientation-audit` follows `from:` and asks about every
parent item that did not come across — asks rather than fails, because only the author knows what bears on
the new thread.

✅ **A thread ends by not being listed as live.** Nothing is archived. A dated folder plus its last dump's
date already encodes the lifecycle, and leaving it in place is what keeps every inbound link true forever.

✅ **Folders and notes carry the date; `architecture/` does not.** The date is *opened*, never *current* —
last-touched stays derivable from git and is never written down. Wikilinks resolve by basename and dating
folders is exactly what invites a repeat topic, so the note carries the date too; otherwise a link to the
second effort on a subject quietly resolves to the first.

▢ **Conversion is lazy and additive.** A workstream in the old task shape gets a `dumps/` directory and is
written into; nothing already there moves. There is no migration project, and records never move.

## 5. The live set, and how an item dies

An orientation carries typed items: **GATE**, **LANDMINE**, **DEAD END**, **OPEN Q**, and **ESCALATED**.

✅ **ESCALATED is a distinct type, not a flavour of OPEN Q.** "Agents can work on this" and "only the owner
can decide this" route differently: escalations are what a fresh session opens with, so an item typed this
way reaches a human and an OPEN Q does not.

✅ **Every item carries a death condition** — what would make it stop being true. It costs the writing agent
nothing, with the context in hand, and without it a later agent cannot judge whether the item is live
without re-reading everything. It moves the cost to the agent best placed to pay it. A DEAD END is exempt:
it fires forever.

✅ **Every item carries its own `as-of`** — when last *confirmed*, not when last copied. An item carried
unchanged through six handoffs inherits the newest document's name and reads as fresh; its own `as-of` is
the only thing that says otherwise.

✅ **Recency is a prior, not a rule.** More recent information generally supersedes older and is trusted
more. The newest orientation can be thin or wrong and an agent may reach back into dumps; what it may not
do is treat an older orientation as a rival account of the present.

✅ **Three dispositions at a handoff: carried, resolved with evidence, escalated.** Every item live in
the previous orientation takes exactly one, and **carried is the default** — an item leaves only when its
death condition has fired. Selection asks the least-budgeted and least independent agent in the system to
predict what the next one needs, and a regenerated view costs the same to write at forty items as at ten.
On trial from 2026-08-21: if orientations stop being readable, selection comes back.

✅ **Every disposition states its basis: evidence or judgement.** This replaces *never infer completion; a
marker is the only authority*, which is retired — see §8.

✅ **A live item states itself; it never merely points.** "See `[[2026-08-19-the-thing]]`" is not an item.
Goal 2 is that a warning fires unprompted, and an agent reading one document does not follow a link it was
not told it needed — every mechanism in this system's history that relied on someone following a pointer
to find a warning failed. Link the detail *after* the statement, never instead of it. **Narrative is the
exception**, because going and reading it is exactly what it is for.

## 6. The two skills, and where the audit lives

| | when | synchronous | does |
|---|---|---|---|
| `pickup` | session start | **yes** | reads the current orientation, audits it, opens with what needs the owner, enters plan mode |
| `context-dump` | learned something | **yes** | one dated dump |
| `context-dump` (handoff) | session end | **yes** | the dump, plus a new dated orientation |

Both are skills rather than agents: they run in the main loop, where the context already is.

✅ **The audit runs at pickup, not at handoff.** The handing-off agent is the least-budgeted and least
independent reader in the system — nearly out of room, and auditing its own work. The fresh one has a full
window and no stake. A bad handoff is caught one session later instead of never, and nothing blocks on the
handoff path.

✅ **`orientation-audit` is a recall aid, not a gate**, and it has no failure exit. It hands the incoming
agent the items the last orientation carried that this one does not, so it can decide per item whether to
dig. Matching is deliberately fuzzy, because a carried item is *meant* to be reworded.

**Length is not the failure mode** (Dennis, 2026-08-21). Goal 1 fails on a surface full of *another
thread's* warnings, not on a long one about this thread — which is why the byte budgets are retired (§8)
and heaviness is thread count. So an uncarried item whose death condition has not fired is a loss, and
the audit reports it as one. It still does not fail: only the reader can tell a fired death condition
from a lost item.

✅ **The architecture recommendation is pickup's, not handoff's.** A handoff *infers* an architecture document would
help; pickup *feels it* — it is the agent reading cold and discovering the system it must work on is
described nowhere. `architecture-candidates` is the mechanical half of the same signal.

✅ **A pickup ends in plan mode.** Measured 2026-08-21: hooks receive `permission_mode` as a **read-only**
input field and no hook output can change it, so a hook cannot force plan mode — the skill calls
`EnterPlanMode` itself.

## 7. The roles that remain, and the machinery they share

| role | scope | does |
|---|---|---|
| `curator` | the vault | regenerates the index, repairs links that cross threads, owns the shared surfaces |
| `scout` | any | read-only recon in a context that is discarded |

**Why there are only two.** Everything inside one thread belongs to the session working in it. What is
left for a background role is the surfaces no thread can own, and reconnaissance whose cost is worth
paying in a context that gets thrown away.

**The pass log carries concurrency.** `pass-log.jsonl` at the vault root, untracked, one shared file
because the question it answers is *what is another agent doing right now* and N logs do not answer it.
Every role announces itself with `start` before it writes and `stop` when it finishes. The one failure
mode seen so far is an unclosed `start`, and it fails safe.

✅ **Worktree isolation is retired (2026-08-20).** It cost five defects of its own, every one a tool
answering about the wrong tree, against three clobbering incidents that were each a scoped `git add` plus a
**bare** commit — which a worktree does not prevent and a pathspec does. Two things survive it: **a tree at
an unexpected commit reports clean**, so any agent given a base ref checks `HEAD` against it first; and
**nobody changes HEAD in a shared checkout**, because creating a branch moves it for every session in the
tree.

✅ **`recall-check` survives as a machinery-development tool only.** Its subject is now a definition being
rewritten here, not a corpus document — nothing in the vault is edited, so nothing in the vault needs it.
It is **not** the way to check a deliberate deletion: a pass whose purpose is removing rules flags every
one of them, and judging a hundred intended retirements in writing is a large amount of work for no
signal. The deletions are the deliverable; `git diff` is the record.

## 8. What was retired, and why — so it is not re-proposed

These were correct answers to a problem this design removes. They are recorded rather than erased, because
the reasoning that produced them was sound and the next person to hit the same symptom should find the
history rather than rebuild it.

| retired | what it did | why it is gone |
|---|---|---|
| the `frontier-clerk` | reconciled a mutable register against dumps | there is no register |
| the `librarian` | consolidated, merged, archived, closed, converted | records are never consolidated, nothing is archived, nothing closes |
| `frontier_slice` | read a register without its prose | nothing edits a register surgically |
| `marker_licence_check` | caught an edit claiming more than its evidence | replaced by dispositions stating their basis |
| `frontier_lag_check` | had the register fallen behind its dumps | the newest document is the state |
| `budget_check` + the 8/12 KB pairs | bounded an accumulating document | heaviness is thread count; a regenerated view cannot accumulate |
| `orientation_check` | did a new task pull warnings forward | there is no task tier; `orientation-audit` replaces it at a different point |
| `closure_check` | is this task finished, and what must carry | nothing closes; its fuzzy matcher lives on in `orientation-audit` |
| the task tier, `done/`, `historical/`, carry-across | partitioned an accumulating register | splitting a thread replaces all of it |
| *never infer completion; a marker is the only authority* | stopped an agent upgrading an item it had no evidence for | it made closure impossible — every real unit carries a `▢`, so requiring a marker meant nothing ever closed, measured across the vault's entire history. It guarded a mutable register against a second agent acting mechanically at a distance, and neither exists. Replaced by **every disposition states its basis** |
| *one marker per separately-statused fact* | stopped a composite marker collapsing distinctions | a writing rule compensating for downstream mechanical action; with judgement restored it has no consumer |
| the clean-tree halt | protected a losslessness guarantee | the guarantee is gone; what protects a commit is the pathspec |
| the write-authority partition | kept parallel agents off each other's files | the pass log answers concurrency directly |

## 9. Invariants, with what would falsify each

| invariant | why | falsified by |
|---|---|---|
| An agent is pushed what bears on its work | A surface full of another thread's warnings fails as a long one does | Recall flat in the irrelevant fraction |
| Every document is a record or a view | The maintenance bill was entirely the third class | A document that must be both, and stays correct |
| A record is never edited | It is evidence of a moment; a later moment gets a later document | An edited record nobody had to reconcile |
| A wikilink is an address, not a claim, so a record's links may be repaired | Repointing a moved target preserves every claim; leaving it dangling loses one. Rename through `lipika obsidian rename`, which moves the links with the file | A link repair that changed what a document asserted |
| The owner writes an epic's PROSE; an agent keeps its citations true | Which threads exist is mechanical and goes stale fastest; the judgement is not and does not | An agent-maintained citation list that misrepresented the effort |
| A vault must not hold a COPY of Lipika's machinery — but may hold its own tools and skills | The bill was N copies of one file, not the existence of a `skills/` directory. The test is identity, not location | A vault-local tool or skill that cost what the port loop cost |
| A view is regenerated, never patched | Patching reintroduces surgical discipline and its whole toolchain | A patched view that stayed true over months |
| An item left out of an orientation stays recoverable from the dumps | Records are immutable and complete, so archaeology is always available | A dropped item that could not be found again |
| A disposition states its basis | Silent inference is the failure; inference itself is not | An unstated basis nobody later needed |
| One thread per workstream | Two threads under one prefix put two agents on one path with an advisory warning between them | Two concurrent threads sharing an orientation without either being pushed the other's warnings |
| Every metric carries the date it was taken | Undated figures invite every later agent to correct them | Agents agreeing on an undated figure across a month |
| The owner writes `architecture/` | One written by an agent is confident, most-linked, and uncontradicted | An agent-written architecture document surviving a trace that disagreed with it |
| Prose in a definition does not fire; a tool with an exit code does | Every measured instance of a rule silently not firing was fixed by moving it into a tool | A rule holding across several passes on prose alone |

## 10. Three tool-design rules the set was built on

- **Prefer a tool that refuses to prose that asks.** Measured repeatedly: a scope-screening condition
  shipped unsatisfiable and went unnoticed until used; a mandatory dispatch did not fire across fourteen
  recon commands; a verifier reported "nothing changed" nine times having read no diff. Every one was
  fixed by moving the rule into a tool with an exit code. A definition is also a system prompt paid on
  **every** invocation, so a tool is the cheaper end as well.
- **When two cases cannot be separated by a threshold, ask whether the distinction matters.** Measured
  2026-08-21: a genuinely deleted item scored 20% content-word overlap and one carried-but-rewritten
  scored 28%. Eight points is not a threshold. The first answer was a convention forcing the author to
  word dispositions so the matcher could find them — ceremony, to defend a distinction that turned out not
  to matter, since both outcomes lead the reader to the same cheap action. The check became advisory
  instead. **A check that cannot separate its cases may be measuring the wrong thing.**
- **A check that stays red on correct content gets dismissed.** Give every new check a hand-audited red
  case and a green case. Measured 2026-08-21 while building `orientation-audit`: its first matcher scored
  a deleted item at 43% against a successor that never mentioned it, because it compared each item to the
  *concatenation* of the successor's items and shared scaffolding vouched for everything. Its second
  reported a correctly-recorded resolution as needing judgement, because it demanded a hard identifier in
  a haystack one item long. Both were found by the fixtures, not by reading.
- **A check reports what it did not check, rather than swallowing it.** Skips and empty-filter cases get
  their own exit code or label; an unannounced gap reads as a clean result.

## 11. Standing tensions — open, deliberately

- ✅ **Settled 2026-08-21 (Dennis) — a dump carries its DELTA**, neither of the two options the question
  was posed as. Carrying the whole live set duplicates it several times a day into documents that can
  disagree; reporting only loses the reconciliation when a session dies without a handoff. The delta is
  what a dump *discovered* or *killed*. Records become the store and the orientation the projection over
  them — which §9 already claims, and which report-only violated by making a *view* the sole holder of
  authoritative state.
- `[OPEN Q]` **May a pickup write a dump?** A pickup confirms things nobody records until the next
  handoff — the one on 2026-08-21 re-checked four death conditions, corrected a figure and found two
  unrecorded items, all of which would have died with the session. **Appending to the orientation is not
  the question and is ruled out**: it is a view. The open shape is a pickup emitting a *record*, leaving
  the next handoff to regenerate the view over it. It would also close a hole §6 already has — a pickup is
  told a stale GATE is worth one command before trusting it, then given nowhere to put the answer.
  Against: writing costs span on the one operation inside the north star, and read-only is the strongest
  property that skill has. **Dies when** a pickup's findings are measurably lost to a session ending
  without a handoff, or when read-only is judged worth the loss.
- `[OPEN Q]` **Does the routing note earn its place beside orientation**, or does the index carry its one
  line?
- `[OPEN Q]` **What is the relevant fraction of a pickup** — of what it loads, how much bore on the work.
  Never measured, and it is the quantity this design claims to move.
- `[OPEN Q]` **How stale is too stale.** `orientation-audit` reports an item at 14 days on no evidence.
- `[OPEN Q]` **Does regenerating from `previous orientation + dumps since` lose things** that regenerating
  from all records would not? The loss is recoverable — the records are intact — but the rate is unknown.
- **[DEAD END] Attacking a parent agent's blocked time.** Ranked the largest problem across three passes
  and was never a cost: no tokens, children working throughout. **Do not re-propose.**
- **[DEAD END] A "turns that thought and called nothing" signal.** The harness emits reasoning in its own
  message, so the count was *every* deliberation — 37 of 37 on one run. **Inventing a defect is worse than
  missing one.**
- **[DEAD END] Loop detectors and scoring over reasoning.** Scaffolded, then dropped: the ask was a gut
  check, not a classifier.
- **[DEAD END] Banning mutable measurements from documents.** The correct fix is dating them.
- **[DEAD END] Renaming a file with a `.locked` suffix while working on it.** Breaks the link graph,
  Obsidian and git paths mid-operation, and a crashed agent leaves it locked forever.
- **[DEAD END] A second status or lock file alongside the pass log.** One store with a derived projection,
  not two things that can disagree.
- **[DEAD END] Importing the pre-log git tags as baselines.** A tag was one global name per scope, so it
  could say neither *when* a pass ran nor that two agents were on the same ground.
- **[DEAD END] Keeping the machinery duplicated into each vault and improving the port tooling.** Three
  tools existed for it and six files still needed hand-porting. There is one copy now.

## 12. How to read and maintain this document

**Living document, and the place to experiment.** Mechanisms marked `▢` are untested and their numbers are
hypotheses: run them, measure, and amend here with a dated amendment.

**Not a frontier.** A `▢` means *the system is not this shape yet*, not *someone should go do this*. A PR
number or a next-move appearing here means it has become a second frontier.

**Voice.** Terse and factual, for a first-time reader. A rule its own owner cannot parse has failed,
however well it encodes a real measurement — rewrite it rather than re-explaining it.

| document | carries |
|---|---|
| `CLAUDE.md` | the normative rules, terse and operative |
| `agent-eval-method.md` | the **procedure** for changing and measuring a role |
| the thread's own dumps | the **record** — what each round found, with figures |
| `sources/evals/` | the **verbatim measurements**, frozen and dated |
| this document | the **design** — the shape, the forces, the falsifiers |

## Amendments

**2026-08-21 — records and views.** The mutable-and-authoritative document class is removed, and with it
seven tools, two roles and the task tier; §8 is the retirement record. Orientation replaces the frontier
and is written fresh at each handoff rather than edited. `pickup` is added as the read-side counterpart to
`context-dump`, and the audit moves to it. `architecture/` is added as a new tier and is the owner's.
ESCALATED is added to the marker vocabulary. Heaviness becomes thread count rather than bytes.

**Earlier, compressed.** The document was reframed on 2026-08-19 around partitioning — *work evolves, so
context must be partitioned as pieces of it emerge and finish* — which is when the sub-unit became a dated
task, byte budgets arrived, and measurements became dated rather than banned. 2026-08-20 recorded the pass
log replacing one-log-per-unit, the machinery moving into its own repo, worktree isolation retiring, and
the closure primitive that let a task close for the first time. Most of that is superseded above; the
reasoning is preserved in §8 rather than deleted.
