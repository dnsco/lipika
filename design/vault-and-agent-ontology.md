---
type: reference
status: reference
date: 2026-08-21
tags: [vault, meta, agents, ontology, design, roles, tools]
---

# The design — what shape this system has, and why

The design of the vault and the machinery that maintains it.

## 1. Purpose

The vault is durable cross-session memory for engineering work, read by agents that need continuity.
It is a **push** surface: what bears on the work arrives without being asked for. Negative results —
ruled-out approaches, gates, landmines — are among its most valuable contents, and the agent about to
re-propose one does not know to search for it. Curation is the cost.

**Context is partitioned as the work is.** Pieces of work start, change and finish, and each gets its
own thread, so what an agent is pushed stays about its work and short enough to read.

**Agents write for agents.** The owner scans to check orientation and correct mistakes, so agents act,
then report for correction.

## 2. Goals

Judge every change against these, in order.

1. **An agent is pushed what bears on its work, and little else.** Relevance first, volume second.
2. **A warning fires unprompted or it does not count.**
3. **Nothing that was written down becomes unfindable.**
4. **Operations are fast.** The target and how it is measured: `agent-eval-method.md`, *Speed*.
5. **Adoption is incremental.** No shape is worth a re-architecture.
6. **Every claim names its enforcement, or admits it has none.**

## 3. Records and views

**Vault documents are immutable by default.** A **record** is written once and never edited. The few
documents that change are **views**, regenerated wholesale rather than patched. Nothing is both.

| | record | view |
|---|---|---|
| dated | yes | yes, except `architecture/` |
| edited | **never** (`gotchas.md` is append-only) | regenerated wholesale, never patched |
| corrected by | writing a newer document | regenerating |
| examples | dumps, `reference/` traces, `sources/`, `external/`, `gotchas.md`, every orientation once superseded | the current orientation, the vault index, `architecture/` |

**Why.** A document that is mutable *and* authoritative needs a toolchain to edit it safely — slicing,
licence checks, losslessness gates, byte budgets, a role to do the editing. A record needs none. A view
needs none either: its sources are intact, so a bad regeneration is fixed by regenerating.

**The older append-only tiers have their own reasons.** An edited transcript in `sources/` is no longer
a transcript, and every document citing it quotes something never said. A rewritten artifact in
`external/` disagrees with what people received. A dump is evidence of a moment.

**Documents move, so the wikilinks inside a record may be updated to follow them.** A link is an
address, not a claim. Move with `lipika obsidian rename`, which updates the links with the file.

**`architecture/` is the one long-lived edited view, and it carries the owner's judgement.** It guards
against a document acquiring authority nobody granted: the most-linked thing in the vault, with no
dated evidence positioned to contradict it. The line is **provenance, not authorship**:

- **Lipika's own agents never write one.** They read documents, not systems, so their output would be
  a confident summary of the corpus rather than of the thing.
- **An agent that understands the system may draft one**, and is often the best placed to. It becomes
  an `architecture/` document when the owner has reviewed it, and **names its drafter**.
- Agents write the dated `reference/` traces behind it and **contradict it with them**, as an
  ESCALATED item.

## 4. The vault's shape

```
vault/
  README.md                          VIEW — the index of threads. Regenerated.
  CLAUDE.md                          the conventions, seeded from Lipika's template
  architecture/<system>.md           VIEW — the owner's. Stable name, no date, as-of <sha>
  reference/YYYY-MM-DD-<topic>.md    RECORD — a trace from source, cross-thread
  workstreams/
    YYYY-MM-DD-<thread>/
      YYYY-MM-DD-<thread>.md         the routing note, dated to match the folder
      orientation/YYYY-MM-DD-HHMMSS.md   VIEW when current, RECORD once superseded. Last sorts current
      dumps/YYYY-MM-DD-HHMMSS-<topic>.md RECORD — several a day is normal
      reference/YYYY-MM-DD-<topic>.md    RECORD — a trace, thread-local
      gotchas.md                     RECORD, append-only — warnings that stay true in this thread
    archive/<thread>/                a thread the owner ruled finished, moved whole
    parked/<effort>/                 shelved; hidden like archive/
  sources/  external/  values/  grand-plans/       RECORD, except grand-plans/, the owner's prose
  pass-log.jsonl                     untracked — who is working where, right now
```

- **A workstream is one discrete body of work** — sometimes a question, sometimes a task like
  "migrate this test suite". One path prefix, one agent at a time. That makes the pass log's prefix partition exact.
- **A workstream says what it is.** Every orientation opens with `## What this is`: one or two sentences
  describing the problem space, carried verbatim and redrawn only by curate. It is the scope a split is
  judged against — the cue is work outside the description, not a reworded question. "The question
  changed" was the earlier cue; it fired on rewording, and the resulting threads carried each other's
  items.
- **Keep threads small.** A thread that runs long gathers cruft, absorbs adjacent work until its
  orientation carries more than an agent can use, and takes longer to audit. Several concurrent efforts
  in one thread is worse: each is pushed the others' warnings. So a second concurrent effort is a new
  dated workstream, and a thread that has grown past its work splits.
- **When the work moves into a different problem space, the thread splits** into a new dated
  workstream, opened by `spin-out`.
  Threads are short-lived, and the split is where selection happens: it is the moment with enough
  information to decide what still bears. Carrying every item at a handoff (§5) is safe only because
  of this.
- **A split copies what still bears on the new thread; it does not point at it.** The new thread's
  first orientation carries those items across, reworded freely and citing their source, and names the
  parent in `from:`. A pointer is pull, and pull cannot fire on an agent who does not know to look.
  `orientation-audit` follows `from:` and asks about every parent item that did not come across — asks,
  because only the author knows what bears.
- **A new thread is pushed its prior art.** `spin-out` reads the other threads when it opens one,
  inline, because relatedness is judged against the parent's context. `## Prior art` names each related
  thread with what it found; bearing warnings are copied verbatim into the new `gotchas.md`.
- **Lines get redrawn.** A split drawn wrong shows as duplicated items. `curate` can propose a
  **re-partition** — N live threads become M new ones along different lines, each with its own
  description, every live item assigned once, the old threads archived. The new threads name every
  parent in `from:`.
- **A lineage is the `from:` graph.** One parent after a split, several after a re-partition; it may
  span repos. `lipika lineage` walks it, archived threads included. No tier or name groups threads.
- **A thread ends by not being listed as live.** Liveness is "accrued a dated document recently", so
  most threads are dead most of the time and a tool that counts threads excludes the dead ones. When
  the owner rules a thread finished, `lipika archive-thread` moves it to `archive/` through
  `obsidian move`, which rewrites path-qualified links. A path written as plain text inside a record
  goes stale and stays so.
- **A finished thread's last orientation is its citable summary**, sound because nothing will
  supersede it. The index carries the navigation between threads.
- **`gotchas.md` holds warnings that stay true.** They are not live state; the writer puts one there
  directly, `orientation-carry --append-gotchas` moves an older item closing `→ dies never`, and a later
  line retires one that stops being true. It is per-thread because a shared surface collects every thread's warnings.
- **Folders and notes carry the date they were opened; `architecture/` does not.** Last-touched is
  derivable from git and never written down. Wikilinks resolve by basename, so a dated note name keeps a
  link to the second effort on a subject from resolving to the first.

Falsified by threads that keep needing to be merged back, or a corpus where finding the live thread
costs more than reading a long orientation would.

## 5. The live set, and how an item is finished

An orientation carries typed items: **GATE**, **LANDMINE**, **DEAD END**, **OPEN Q** and **ESCALATED**.

- **ESCALATED is a distinct type.** "Agents can work on this" and "only the owner can decide this"
  route differently: escalations are what a fresh session opens with.
- **An item may carry acceptance** — `→ accepted when <condition>`, what, checked, would finish it.
  It is a goal, and a pickup checks it in one call; give one to work-shaped items and leave it off facts
  and warnings. It is optional, and the agent carrying items judges liveness either way. Older records
  write `→ dies when …`, which the tools read as the same. It replaced the required death condition
  2026-09-30: a required clause got invented for items that had none, and `dies never` became a category
  that only accumulated.
- **Every item carries its own `as-of`** — when last *confirmed*, not last copied. An item carried
  unchanged through six handoffs inherits the newest document's name; its own `as-of` is the only thing
  that says otherwise.
- **Recency is a signal, not a rule.** The newest document is the likeliest to be true, and every
  document is a partial projection. An older orientation or dump is a historical view: possibly
  outdated, and possibly holding context the newest one dropped. The aim is the context the task needs,
  not a complete model of the world.
- **Three dispositions at a handoff: carried, resolved with evidence, escalated.** **Carried is the
  default**; an item leaves only when it is finished — acceptance met, or judged no longer live. Selecting what to drop would ask the
  least-budgeted agent in the system to predict what the next one needs, and a regenerated view costs the
  same to write at forty items as at ten.
- **Every disposition states its basis: evidence or judgement.** Silent inference is the failure;
  inference is not.
- **A live item states itself; it never merely points.** "See `[[the-thing]]`" is not an item. Link the
  detail *after* the statement. Narrative is the exception: reading it is what it is for.
- **A dump carries its delta** — what it discovered or killed. The whole live set would be duplicated
  several times a day into documents that can disagree; a report alone would lose the reconciliation when
  a session ends without a handoff. Records are the store, and the orientation is the projection over them.
- **The carry is a tool, and the tool bounds the document.** `orientation-carry` makes carrying cheap,
  and exits non-zero naming the standing warnings — the part that is actually unbounded. Hand-typing was
  never the bound.

## 6. The skills

| skill | when | does |
|---|---|---|
| `pickup` | session start | reads the current orientation, audits it against its predecessor, opens with what needs the owner, ends in plan mode. Read-only |
| `context-dump` | learned something; session end | one dated dump; at a handoff, also the next orientation and the handoff prompt |
| `spin-out` | work outside the thread's problem space | the parent's handoff, the new thread's routing note and first orientation, its prior art |
| `curate` | the owner asks what is finished, or whether the lines are right | groups threads by lineage, one `curator` per group; one table of dispositions and proposed re-partitions; archives and re-partitions what the owner rules |
| `vault-normalize` | a vault is in an old shape | creates, moves and deletes files to the current shape; never edits inside one |

They are skills rather than agents because they run in the main loop, where the context already is.

- **The audit runs at pickup, not at handoff.** The handing-off agent is nearly out of room and auditing
  its own work; the fresh one has a full window and no stake. A bad handoff is caught one session later
  instead of never, and nothing blocks the handoff path.
- **`orientation-audit` is a recall aid, not a gate**, with no failure exit. It lists items the last
  orientation carried that this one does not. Matching is fuzzy because a carried item is meant to be
  reworded. **Length is not the failure mode** — goal 1 fails on a surface full of *another thread's*
  warnings — so an uncarried item not recorded as finished is reported as a loss. Only the reader can
  tell a finished item from a lost one, so it still does not fail. After a re-partition it compares
  against every parent.
- **The architecture recommendation is pickup's.** A handoff infers one would help; pickup, reading cold,
  finds the system it must work on described nowhere. `architecture-candidates` is the mechanical half.
- **A pickup calls `EnterPlanMode` itself.** Hooks receive `permission_mode` read-only, so no hook can set it.

## 7. The roles, and the machinery they share

| role | scope | does |
|---|---|---|
| `curator` | the vault's shared surfaces | regenerates the index, the conventions file and the memory pointer; repairs links that cross threads; for `curate`, judges one group of threads and moves nothing |
| `tracer` | one external source | re-opens it in a context that is discarded and writes one `reference/` trace |

**Why only two.** Everything inside one thread belongs to the session working in it. What is left is the
surfaces no thread owns, and an external source worth re-reading in a context that gets thrown away.

**Why a tracer may write.** A handoff's cost is text the session generates, at a flat rate. A child *told*
what a source says costs the same bytes; a child that **re-opens** the source costs its address. So a
tracer writes that one file — no dump, no orientation, no index, no commit, never `architecture/` — and
**refuses rather than writes** when it cannot reach the source, because a fabricated trace is the risk it
buys. `evals/dispatched-traces` scores that refusal. Falsified by a dispatched trace measurably thinner
than a session-written one on the same subject, or a fabrication reaching the record.

**The pass log carries concurrency.** `pass-log.jsonl` at the vault root, untracked, one shared file
because the question is *what is another agent doing right now*. Every role writes `start` before it
writes and `stop` when it finishes. An unclosed `start` fails safe.

**A shared checkout has two rules.** Nobody changes HEAD in it, because a branch moves it for every
session in the tree. And a tree at an unexpected commit reports clean, so an agent given a base ref checks
`HEAD` against it first. A commit is protected by its pathspec, not by isolation.

**`recall-check` is a machinery-development tool.** It proves a rewritten definition dropped no rule. Its
subject is a definition, never a vault document, since nothing in the vault is edited. It is not how to
check a deliberate deletion — there, the deletions are the deliverable and `git diff` is the record.

## 8. Invariants, with what would falsify each

| invariant | why | falsified by |
|---|---|---|
| An agent is pushed what bears on its work | A surface full of another thread's warnings fails as a long one does | Recall flat in the irrelevant fraction |
| Every document is a record or a view | The maintenance bill was entirely the third class | A document that must be both, and stays correct |
| A record is never edited | It is evidence of a moment; a later moment gets a later document | An edited record nobody had to reconcile |
| Documents move, and the wikilinks inside them follow | A link is an address, not a claim; a dangling link loses one | A link update that changed what a document asserted |
| A lineage is the `from:` graph | Which threads came from which is recorded once, in `from:` | Two threads of one body of work with no `from:` link, that curation needed grouped |
| A workstream is scoped by its described problem space | A split cue that fires on rewording duplicates items | Threads split on the description that still carried each other's items |
| A vault needs no tools or skills of its own for standard maintenance, and may hold them for its own purposes | Maintenance is the installed plugin's job | A vault that needed a local tool to be maintained |
| A view is regenerated, never patched | Patching reintroduces surgical discipline and its toolchain | A patched view that stayed true over months |
| A warning that stays true is not a live item | It can never leave, so it only accumulates | A standing warning `gotchas.md` could not hold without losing what made it useful |
| An item left out of an orientation stays recoverable | Records are immutable and complete | A dropped item that could not be found again |
| A disposition states its basis | Silent inference is the failure | An unstated basis nobody later needed |
| One thread per workstream | Two threads under one prefix put two agents on one path | Two concurrent threads sharing an orientation, each pushed the other's warnings |
| Every metric carries the date it was taken | Undated figures invite every later agent to correct them | Agents agreeing on an undated figure across a month |
| `architecture/` is the owner's reviewed judgement, and names its drafter | An unreviewed model becomes confident, most-linked and uncontradicted | A reviewed architecture document surviving a trace that disagreed with it |
| Prose in a definition does not fire; a tool with an exit code does | Rules that silently failed to fire were fixed by moving them into tools | A rule holding across several passes on prose alone |

## 9. Tool-design rules

- **Prefer a tool that refuses to prose that asks.** A rule in a definition gets read past; the same
  rule with an exit code fails loudly. A definition is a system prompt paid on every invocation, so the
  tool is the cheaper end too.
- **Give every check a hand-audited red case and a green case.** A check that stays red on correct
  content gets dismissed; one that stays green on a real fault is worse. Fixtures find matcher faults
  that reading does not.
- **When two cases cannot be separated by a threshold, ask whether the distinction matters.** If both
  outcomes lead the reader to the same cheap action, make the check advisory rather than adding
  ceremony to defend it. A check that cannot separate its cases may be measuring the wrong thing.
- **A check reports what it did not check.** Skips and empty filters get their own exit code or label;
  an unannounced gap reads as a clean result.
- **A rule about where a fact belongs can change who reads it.** When a rule moves content, ask who was
  reading it where it was. *An item that cannot die is a convention* places machine traps correctly and
  would move an ESCALATED item off the one surface a handoff puts in front of the owner.

## 10. Maintaining this document

It describes the system as it is. When the system changes, rewrite the section, in the present tense;
the pull request is the record of what changed and why. A rule its owner cannot parse has failed —
rewrite it rather than re-explain it.

| document | carries |
|---|---|
| `CLAUDE.md` | the normative rules, terse and operative |
| `agent-eval-method.md` | how a change to a role or tool is tested and measured |
| `future-work.md` | changes ruled but not built, and the open questions |
| `retired.md` | what was tried and dropped, and why — for a major change to the vault's shape |
| `GOTCHAS.md` | what bites, measured |
| the vault's dumps and `sources/evals/` | the record — what each round found, with figures |
| this document | the design — the shape, the forces, the falsifiers |
