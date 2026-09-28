---
type: reference
status: reference
date: 2026-08-21
tags: [vault, meta, agents, ontology, design, roles, tools]
---

# The design — what shape this system has, and why

The design of the vault and the machinery that maintains it: the shape, the forces behind it, and
what would falsify each part. **Not normative** — `CLAUDE.md` and the skill and agent definitions win
on any conflict of wording. It carries **parameters, not measurements**: a measured figure is a record
and lives in the vault, dated; a chosen threshold is a design decision and is revisable here.

## 1. Purpose, and the forces that shape it

The vault is durable cross-session memory for engineering work: a **cohesive corpus** read by agents
that need continuity, deliberately not a stochastic index.

- **What it buys.** Facts arrive **whether or not the agent thought to ask for them.**
- **What it costs.** Curation is slow, and it is work.
- **Why the trade holds.** The corpus's most valuable contents are *negative* results — ruled-out
  approaches, gates, landmines. A negative result's trigger is someone about to re-propose the thing,
  who by definition does not know to query for it. Pull retrieval cannot fire on the absence of a
  query, so the corpus is a **push** surface, whatever the retrieval technology.

**Work evolves.** A push surface works only while what it pushes is about the work at hand and short
enough to read at the moment of proposing. Pieces of work emerge, change what they are about, and
finish; context is partitioned as they do, or one surface accumulates everything.

**Agents write for agents.** The human reader is an occasional scanner, checking orientation and
correcting mistakes. So agents **act, then report for correction**, rather than ask, then act.

## 2. Goals

Judge every change against these, in order.

1. **An agent is pushed what bears on its work, and little else.** Relevance first, volume second.
2. **A warning fires unprompted or it does not count.**
3. **Nothing that was written down becomes unfindable.**
4. **Any operation somebody waits on finishes inside two minutes.**
5. **Adoption is incremental.** No shape is worth a re-architecture.
6. **Every claim names its enforcement, or admits it has none.**

**Goal 4 is a north star, not a limit on any role.** Its quantity is **span** — wall clock from a
pass's `start` to its `stop`, what a human waits — computed by `pass_log.py` as `span_s`. As a limit
it does damage: a fan-out pass at `max(child) + overhead` can never meet it, and it discourages the
tools §10 argues are the cheap end. Eval, profiling and developer-facing work are exempt.
`lipika span-report` prints the series and **always exits 0**; an operation over the star is a fact,
not a backlog item.

## 3. Records and views

**Every document is a record or a view. Nothing is both.**

| | record | view |
|---|---|---|
| dated | yes | yes, except `architecture/` |
| edited | **never** | regenerated wholesale, never patched |
| corrected by | writing a newer document | regenerating |
| examples | dumps, `reference/` traces, `sources/`, `external/`, `gotchas.md`, every orientation already written | the current orientation, the vault index, `architecture/` |

**This is the whole design.** A document that is mutable *and* authoritative needs surgical edits, a
slice tool, a licence check on each edit, a losslessness gate, a byte budget, a closure primitive and a
role to do the editing. A view needs none of them: its sources are intact, so a bad regeneration is
fixed by regenerating, and it is written under a target rather than trimmed.

**The older append-only tiers have their own reasons.** An edited transcript in `sources/` is no longer
a transcript, and every document citing it quotes something never said. A rewritten artifact in
`external/` disagrees with what people received. A dump is evidence of a moment.

**A wikilink is an address, not a claim.** Repointing one when its target is renamed preserves what a
record says, so a record's links may be repaired — through `lipika obsidian rename`, which moves the
links with the file.

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

- **A workstream is one question being answered**, and one thread of work: one path prefix, one agent
  at a time. That makes the pass log's prefix partition exact.
- **Weight is concurrent threads, not bytes.** Two hundred dumps on one thread cost nothing — orientation
  is one document and dumps are read on demand. Forty dumps across three concurrent efforts is heavy at
  a fifth the size. A second concurrent effort is a new dated workstream, so there is no task tier and
  no closure ceremony.
- **When the question changes, the thread splits** into a new dated workstream, opened by `spin-out`.
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
- **A project is a split lineage.** The chain of `from:` links is one project, and may span repos.
  `lipika lineage` walks it, archived threads included. No document lists a project's threads.
- **A thread ends by not being listed as live.** Liveness is "accrued a dated document recently", so
  most threads are dead most of the time and a tool that counts threads excludes the dead ones. When
  the owner rules a thread finished, `lipika archive-thread` moves it to `archive/` through
  `obsidian move`, which rewrites path-qualified links. A path written as plain text inside a record
  goes stale and stays so.
- **A finished thread's last orientation is its citable summary**, sound because nothing will
  supersede it. The index carries the navigation between threads.
- **`gotchas.md` holds what cannot die.** A `dies never` item is a warning that stays true, not live
  state; `orientation-carry --append-gotchas` appends it, and a later line retires one that stops being
  true. It is per-thread because a shared surface collects every thread's warnings.
- **Folders and notes carry the date they were opened; `architecture/` does not.** Last-touched is
  derivable from git and never written down. Wikilinks resolve by basename, so a dated note name keeps a
  link to the second effort on a subject from resolving to the first.

Falsified by threads that keep needing to be merged back, or a corpus where finding the live thread
costs more than reading a long orientation would.

## 5. The live set, and how an item dies

An orientation carries typed items: **GATE**, **LANDMINE**, **DEAD END**, **OPEN Q** and **ESCALATED**.

- **ESCALATED is a distinct type.** "Agents can work on this" and "only the owner can decide this"
  route differently: escalations are what a fresh session opens with.
- **Every item carries a death condition** — what would make it stop being true. The writer has the
  context in hand; without it, a later agent cannot judge liveness without re-reading everything. A DEAD
  END is exempt: it fires forever.
- **Every item carries its own `as-of`** — when last *confirmed*, not last copied. An item carried
  unchanged through six handoffs inherits the newest document's name; its own `as-of` is the only thing
  that says otherwise.
- **Recency is a prior, not a rule.** The newest orientation can be thin or wrong, and an agent may reach
  back into dumps. It may not treat an older orientation as a rival account of the present.
- **Three dispositions at a handoff: carried, resolved with evidence, escalated.** **Carried is the
  default**; an item leaves only when its death condition has fired. Selecting what to drop would ask the
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
  and exits non-zero naming the immortal fraction — the part that is actually unbounded. Hand-typing was
  never the bound.

## 6. The skills

| skill | when | does |
|---|---|---|
| `pickup` | session start | reads the current orientation, audits it against its predecessor, opens with what needs the owner, ends in plan mode. Read-only |
| `context-dump` | learned something; session end | one dated dump; at a handoff, also the next orientation and the handoff prompt |
| `spin-out` | the question changed | the parent's handoff, the new thread's routing note and first orientation, its prior art |
| `curate` | the owner asks what is finished | groups threads by lineage, one `curator` per group; one table of dispositions; archives what the owner rules finished |
| `vault-normalize` | a vault is in an old shape | creates, moves and deletes files to the current shape; never edits inside one |

They are skills rather than agents because they run in the main loop, where the context already is.

- **The audit runs at pickup, not at handoff.** The handing-off agent is nearly out of room and auditing
  its own work; the fresh one has a full window and no stake. A bad handoff is caught one session later
  instead of never, and nothing blocks the handoff path.
- **`orientation-audit` is a recall aid, not a gate**, with no failure exit. It lists items the last
  orientation carried that this one does not. Matching is fuzzy because a carried item is meant to be
  reworded. **Length is not the failure mode** — goal 1 fails on a surface full of *another thread's*
  warnings — so an uncarried item whose death condition has not fired is reported as a loss. Only the
  reader can tell a fired condition from a lost item, so it still does not fail.
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

## 8. Retired — do not re-propose

Each was a correct answer to a problem this design removes, or a mechanism measured and dropped.

| retired | what it did | why it is gone |
|---|---|---|
| the task frontier and parent register | mutable, authoritative state per thread | the third document class; §3 |
| the `frontier-clerk` | reconciled a register against dumps | there is no register |
| the `librarian` | consolidated, merged, archived and closed on its own judgement | records are never consolidated; archiving needs the owner's ruling |
| `frontier_slice` | read a register without its prose | nothing edits a register surgically |
| `marker_licence_check` | caught an edit claiming more than its evidence | dispositions state their basis |
| `frontier_lag_check` | had the register fallen behind its dumps | the newest document is the state |
| `budget_check` and byte budgets | bounded an accumulating document | weight is thread count; a regenerated view cannot accumulate |
| `orientation_check`, `closure_check` | pulled warnings into a new task; decided a task was finished | no task tier; `orientation-audit` replaces both at pickup |
| the task tier, `done/`, `historical/`, carry-across | partitioned an accumulating register | splitting a thread |
| *never infer completion; a marker is the only authority* | stopped an agent upgrading an item without evidence | it made closure impossible; replaced by stating the basis |
| *one marker per separately-statused fact* | stopped a composite marker collapsing distinctions | compensated for downstream mechanical action that no longer exists |
| the clean-tree halt | protected a losslessness guarantee | the guarantee is gone; the pathspec protects a commit |
| the write-authority partition | kept parallel agents off each other's files | the pass log answers concurrency |
| worktree isolation | a tree per agent | its defects were tools answering about the wrong tree; the clobbers it targeted were bare commits, which a pathspec prevents |
| the epic tier, `epics/` | grouped a project's threads | `from:` already records which threads are one project; a hand-kept list went stale |
| `up:` frontmatter | named a document's parent | nothing read it, and most values restated the folder path |
| `about:` frontmatter | named the thread a document concerns | nothing read it once `handoff-prompt` stopped; graders are not tied to threads |
| the `scout` | found related threads in the background | `spin-out` reads them inline, with the parent's context |
| warning recall by search at read time | found other threads' warnings when someone looked | pull cannot fire when nobody asks; prior art is pushed at the split |
| machinery copied into each vault, and port tooling | kept N copies in step | one copy, installed as a plugin |
| blocked parent time as a cost | ranked the largest problem | it cost nothing: no tokens, children working throughout |
| a "turns that thought and called nothing" signal | flagged idle deliberation | the harness emits reasoning in its own message, so it counted every deliberation |
| loop detectors and scoring over reasoning | classified thrashing | the need was a read, not a classifier |
| banning mutable measurements | kept figures out of documents | dating them is the fix |
| a `.locked` suffix while working | marked a file in use | breaks links, Obsidian and git paths; a crash leaves it locked |
| a status or lock file beside the pass log | a second concurrency store | one store with a derived projection |
| git tags as pass baselines | one global name per scope | could say neither when a pass ran nor that two agents overlapped |

## 9. Invariants, with what would falsify each

| invariant | why | falsified by |
|---|---|---|
| An agent is pushed what bears on its work | A surface full of another thread's warnings fails as a long one does | Recall flat in the irrelevant fraction |
| Every document is a record or a view | The maintenance bill was entirely the third class | A document that must be both, and stays correct |
| A record is never edited | It is evidence of a moment; a later moment gets a later document | An edited record nobody had to reconcile |
| A record's links may be repaired | Repointing a moved target preserves every claim; a dangling link loses one | A link repair that changed what a document asserted |
| A project is its split lineage; no document lists its threads | Which threads are one effort is recorded once, in `from:` | Two threads of one effort with no `from:` chain, that curation needed grouped |
| A vault must not hold a copy of Lipika's machinery, but may hold its own tools and skills | The cost was N copies of one file, not a directory named `skills/`. The test is identity | A vault-local tool that cost what the port loop cost |
| A view is regenerated, never patched | Patching reintroduces surgical discipline and its toolchain | A patched view that stayed true over months |
| A dispatched agent may create a `reference/` trace, and no other thread document | It costs the caller only an address; judgement about what a thread is stays with the session | A dispatched trace thinner than a session's; a fabrication in the record |
| A `dies never` item is a convention, not a live item | It can never leave, so it only accumulates | A `dies never` item a shared surface could not hold without losing what made it useful |
| An item left out of an orientation stays recoverable | Records are immutable and complete | A dropped item that could not be found again |
| A disposition states its basis | Silent inference is the failure | An unstated basis nobody later needed |
| One thread per workstream | Two threads under one prefix put two agents on one path | Two concurrent threads sharing an orientation, each pushed the other's warnings |
| Every metric carries the date it was taken | Undated figures invite every later agent to correct them | Agents agreeing on an undated figure across a month |
| `architecture/` is the owner's reviewed judgement, and names its drafter | An unreviewed model becomes confident, most-linked and uncontradicted | A reviewed architecture document surviving a trace that disagreed with it |
| Prose in a definition does not fire; a tool with an exit code does | Rules that silently failed to fire were fixed by moving them into tools | A rule holding across several passes on prose alone |

## 10. Tool-design rules

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

## 11. Open questions

- **May a pickup write a dump?** A pickup confirms things nobody records until the next handoff, and a
  session that ends without one loses them. Appending to the orientation is ruled out — it is a view.
  The open shape is a pickup emitting a *record*. Against: it costs span, and read-only is that skill's
  strongest property. Dies when a pickup's findings are measurably lost, or read-only is judged worth it.
- **Does the routing note earn its place** beside the orientation, or does the index carry its one line?
- **What is the relevant fraction of a pickup** — of what it loads, how much bore on the work? It is the
  quantity this design claims to move, and it is unmeasured.
- **How stale is too stale?** Liveness and staleness use a 14-day window
  (`architecture-candidates --live-within-days`); it is a chosen parameter, not a measured one.
- **Does regenerating from the previous orientation plus new dumps lose items** that regenerating from
  all records would not? The loss is recoverable; its rate is unknown.

## 12. Maintaining this document

It describes the system as it is. When the system changes, rewrite the section, in the present tense;
the pull request is the record of what changed and why. A rule its owner cannot parse has failed —
rewrite it rather than re-explain it.

| document | carries |
|---|---|
| `CLAUDE.md` | the normative rules, terse and operative |
| `agent-eval-method.md` | how a change to a role or tool is tested and measured |
| `GOTCHAS.md` | what bites, measured |
| the vault's dumps and `sources/evals/` | the record — what each round found, with figures |
| this document | the design — the shape, the forces, the falsifiers |
