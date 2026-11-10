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
workstreams/YYYY-MM-DD-<thread>/ one body of work. NO status field
  YYYY-MM-DD-<thread>.md         routing note — what this thread is. Dated to match the folder
  orientation/<stamp>.md         newest wins. Written at handoff
  dumps/<stamp>-<topic>.md       <- YOUR DUMP GOES HERE
  reference/YYYY-MM-DD-<topic>.md  dated trace from source. ONE SUBJECT EACH
  reference/YYYY-MM-DD-unopened.md what was cited and never opened. Newest wins
  gotchas.md                     warnings that stay true. Append-only
```

**No tier carries state.** A workstream falls off by date. A thread's first orientation names the
threads it came from in `from:` — one after a split, several after a re-partition — across repos if the
work spans them. `lipika lineage` prints it.

One workstream is **one thread of work** — one path prefix, one agent at a time. A second concurrent thread
is a **new dated workstream**, not a subfolder, opened with `/lipika:spin-out`. Resolve the vault with
`lipika vault-config path`. Full conventions: the vault's `CLAUDE.md`, which a session rooted in a code
project does **not** load automatically — read it if you have not.

**A workstream with no `dumps/`**: create it and write there; leave every existing document where it is.

## Do

1. **The home is the thread this session worked on. If you cannot name it, ask — do not infer it.**
   **A workstream is one body of work, and its `## What this is` describes the problem space.** Work
   this session did outside that description is a different body of work: a new dated workstream, and
   that is the normal path, not the exception — short threads keep context small. A question reworded
   inside the description is the same thread.

   **Never resolve it by recency.** Several threads accrue in one vault on the same day — this machinery and a product migration in
   another repo are two questions with two checkouts, interleaved commit by commit. A dump filed against
   the wrong thread is not a small error: it puts a product finding into the machinery's live set, where
   the next machinery session carries it forward as its own. Nothing detects it.

   You did the work, so you know which thread it was — that is why this asks *you* and not the log.

   ```bash
   cd "$(lipika vault-config path)"
   lipika threads                                     # what is live, if you need to see the names
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

   Frontmatter: `type` / `status` / `date` / `tags`; the folder already says which thread this is.

   - **What you did and what came of it** — PR numbers, commit shas, branch names, what is green and what
     is red.
   - **Answer the questions you inherited.** For each open question or warning you touched: resolved (with
     the evidence), still open, or now understood differently.
   - **A scannable `## Live items` block — YOUR DELTA, not the inherited set restated.** What this
     session *discovered*, plus what it *killed* with the evidence that killed it. An item you neither
     found nor changed belongs to the orientation, not here; repeating it several times a day is how two
     documents start disagreeing. Collected, not scattered through prose, one per line:

     `[TYPE] statement — trigger → consequence → accepted when <condition> · as-of YYYY-MM-DD`

     - **GATE** — a blocking precondition or ordering. The outage-class risk.
     - **LANDMINE** — breaks silently or burns time, with a known avoidance.
     - **OPEN Q** — unresolved, and agents can work on it.
     - **ESCALATED** — unresolved, and **only the owner can decide it**. An item routed here reaches a
       human; an OPEN Q does not.
     - **DEAD END** — ruled out, with the reason. It takes no acceptance clause.

     **Acceptance is optional.** `→ accepted when <condition>` is the item's goal — what, checked, would
     finish it — and a pickup checks it in one call, so give one to work-shaped items. Leave it off facts
     and warnings rather than inventing one. Older records write `→ dies when …`; it means the same.

     **`as-of` is when the item was last *confirmed*, not last copied.** Carrying an item forward does not
     refresh its date.
   - **State, with its basis.** What landed and how you know: `merged #4131`, `commit a1b2c3d`, `gate
     green`. A draft or open PR has not landed. Asserting judgement instead is fine — say so:
     *judgement: the remaining work no longer describes this thread*. **An unstated basis is the only
     unacceptable one.**
   - **An external page is a basis** — a Slack permalink, a Notion page, a gist, a dashboard, a vendor
     page, a rendered doc site. Name the one that settled the claim and wikilink the trace holding its
     URL: *the M2 assignment page — [[2026-09-16-the-m2-mandate]]*.
   - **Reusable commands** — the exact incantation. A real script goes in Lipika's `tools/`, not the vault.
   - `[[wikilinks]]` to vault docs; literal text for code-repo paths, with the repo named.

2a. **If this session read anything outside the repos, trace it — one document per subject** —
   `workstreams/<ws>/reference/YYYY-MM-DD-<topic>.md`, named for what it is about:

   ```bash
   lipika stamp --for workstreams/<ws>/reference     # a DATE. You supply the topic
   ```

   **The unit is a subject, not a link.** A Slack argument, a deck, an incident review and a vendor page
   are four subjects and four files; forty permalinks from one channel argument are one. **Never one
   document holding unrelated subjects** — correcting one reference in an aggregate rewrites all of
   them, and the rest get copied forward on faith.

   ```markdown
   # <the subject> — <the fact it settled, never a description of the document>
   `<url>` · opened YYYY-MM-DD · <the access route that actually works>
   ```

   **What you never opened goes in one place of its own** — `reference/YYYY-MM-DD-unopened.md`, beside
   the traces. **It is the half that goes missing**, because it costs you an admission of what you
   skipped. Write it: what it is, **what cites it**, and what it is claimed to settle.

   - **A stable public page may stand as a URL** with one line on what it settled. Transcribing it is
     waste, and several such pages may share one trace if they settle one subject.
   - **An auth-walled or mutable reference gets its substance traced.** A Slack thread is not one
     document, its permalink dies with workspace access, and a message can be edited out from under it —
     same for a DM, a dashboard view, anything behind SSO. Carry what was said and decided; the
     permalink is provenance, not content. Name the route that works: *behind GitHub auth; the content
     is `<org>/<repo>` under `<path>`, read with `gh repo clone … --depth=1`*.
   - **Correct it with a newer trace, never an edit.** A moved, renamed or dead URL is an event, and a
     dated document is what keeps it one. The old trace stays true about its own moment.
   - **It fires on a reference a later reader would need to re-open**, not on everything glanced at. A
     session whose work was entirely in-repo writes no trace and no references bullet.

2b. **Dispatch a `tracer` for every subject that is one addressable artifact. Write the rest
   yourself.**

   Send one `tracer` per subject, all in one message so they run at once. **Open each prompt with
   the absolute path to write** — `workstreams/<ws>/reference/YYYY-MM-DD-<topic>.md`, the date from
   `lipika stamp --for workstreams/<ws>/reference`. A tracer given no path writes nothing. Then the
   address, the subject and the claim it settles — *nothing else*. **Not the substance**: the handoff's cost is text generated, so pasting the source into the prompt
   spends what the dispatch exists to save. The child re-opens the artifact in a context that is
   then discarded.

   - **Dispatch** one artifact a child can re-open on its own: a Slack thread, a deck, an incident
     review, a vendor page, a doc site.
   - **Write it yourself** when the trace is **synthesis** — a claim across several artifacts plus
     your judgement. A child has neither, and returns a confident summary of the wrong thing.
   - **Never dispatch `unopened.md`.** An absence cannot be delegated.
   - **A tracer that refuses has done its job** — it writes nothing and returns the address and the
     error. Route that to the unopened list.
   - **Read what comes back.** A source that settles less than the claim you sent is a correction,
     and it belongs in your dump.

   You commit once, after every tracer has returned (step 5). Tracers neither commit nor open a pass.

   ```bash
   lipika reference-check <ws>    # URLs in dumps no reference/ trace carries. 0 clean · 1 findings
   lipika trace-check <ws>        # can a later reader get back to the source. 0 clean · 1 findings
   ```

   **A clean exit is not a clean bill** — nothing can see what you read and did not write down. **If
   `reference-check` reports untraced URLs that your traces plainly carry, say so and stop** — it
   matches literal strings, so a grouped or abbreviated citation reads as untraced, and the fix is
   the tool rather than a machine-readable index bolted onto a document a human has to read. It
   skips fenced code: a URL in a `bash` block is a command to re-run, not a source to re-open.

   **`trace-check` names a fact about a document, never an instruction to edit one.** A trace is a
   record. An older trace it flags stays exactly as it is.

3. **Second pass — what did not make it in?** Before you commit: what would a cold-start you need in a
   month? Sweep for implicit decisions made without the *why*, dead ends ruled out without the reason,
   environment traps, external references nothing names, and concrete current state. Route anything new into `## Live items` in the typed
   shape rather than into loose prose.

4. **If this is a handoff, write the next orientation** — `lipika stamp --for
   workstreams/<ws>/orientation`. This is the name `pickup` reads, so sorting last is the whole document.

   **An orientation is a projection over the records: previous orientation + every dump delta since.**
   Read them and write a **new** document. Do not diff-and-patch the old one in your head, and do not
   write from session memory — the dumps are the evidence trail the next agent gets.

   **Do not retype the previous live set. Carry it.**

   ```bash
   lipika orientation-carry <ws>   # `## Needs the owner` + `## Live items`, verbatim
   ```

   Paste that in, then do the judgement it cannot: **delete the items that are finished**, writing
   each into `## Settled since the last orientation` with the evidence, and author the rest —
   `## Where this is`, your new items, the escalation ordering, `## References`, `## Recent narrative`.
   Retyping is where a live set decays: rewording and lost clauses happen in carried items, not new
   ones. A carried item keeps its own `as-of`. `## What this is` comes across verbatim; if the thread
   has none yet, write it — one or two sentences on the problem space, from the routing note and the
   work — and change it only when the body of work itself is redrawn, which is curate's call.

   **It exits 1 and names the standing warnings — act on those.** An older item closing
   `→ dies never` is a **warning that stays true, not a live item**; write a new one straight into
   `gotchas.md`. Run
   `lipika orientation-carry <ws> --append-gotchas` to append them verbatim to this thread's
   `gotchas.md`. **It is appended to, never rewritten**: retire a warning that stops being true with a
   later line. Not the vault's `CLAUDE.md` or Lipika's `design/GOTCHAS.md` — a shared surface collects
   every thread's warnings. `[DEAD END]` and `[ESCALATED]` stay in the orientation: one is
   thread-local, the other is what the owner opens it for. An item you judge thread state after all,
   paste back.

   ```markdown
   ---
   type: orientation
   status: current
   date: YYYY-MM-DD
   from: "[[YYYY-MM-DD-<parent-thread>]]"   # only on a thread's FIRST orientation; a YAML list if several
   ---

   ## What this is
   One or two sentences: the problem space this body of work covers. The scope a split is judged against.

   ## Where this is
   Two or three sentences. What state the work is in.

   ## Needs the owner
   Every ESCALATED item. If there are none, say so.

   ## Live items
   Every carried GATE / LANDMINE / DEAD END / OPEN Q, in the typed shape, each with its own `as-of`.

   ## Settled since the last orientation
   One line per item finished, with the evidence.

   ## References
   The handful this thread actually rests on, one line each on what it settled, each linking its own
   trace — and [[YYYY-MM-DD-unopened]], named, for what was cited and never opened.

   ## Prior art
   Threads that bear on this one, written by `spin-out` when the thread was opened. Carried
   verbatim by `orientation-carry`, so write it once.

   ## Recent narrative
   The last handful of dumps, newest first, one or two sentences each, linked.
   ```

   **`## References` is bounded by attention, not by thread age.** A wikilink, a handful, the unopened
   backlog. **Never the inventory** — that is the trace, and reproducing it here is how an orientation
   grows without bound. Which handful matters is your judgement: nothing can rank it, and you did the
   work.

   **Carry every live item forward.** An item leaves the live set for exactly two reasons: it is
   **finished** — its acceptance met, or judged no longer live, either way with the evidence — or it is
   **a warning that stays true**, which goes to `gotchas.md`, said out loud. Do not select on anything
   else: a long set about this thread is not the failure mode, and choosing for
   the next agent is a call you are the worst placed to make.

   **A live item states itself.** "See [[2026-08-19-the-thing]]" is a pointer, and a warning has to fire
   at an agent who does not know to look. Link the detail *after* the statement, never instead of it.
   `## Recent narrative` and `## Prior art` are the two places a pointer is the content.

4a. **A new thread is opened by `/lipika:spin-out`, not here.** It writes the parent's side and the
   new thread's, and finds the new thread's prior art. If this session worked in a different problem
   space, end this dump and run it.

5. **Commit** in the vault, which is its own repo. Stage **specific paths** — never `git add -A`, never a
   bare `commit`, because other sessions write here.

   ```bash
   cd "$(lipika vault-config path)" && lipika vault-commit -m "…" -- <your paths>
   ```

   **The subject must be 72 characters or fewer** — `vault-commit` refuses a longer one, and it
   refuses after you have written the whole message. Count it before you write the body.

   **Commit once, after every `tracer` has returned**, with their paths in the pathspec. A commit
   that races a child leaves that file untracked with nothing to say so.

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
   lipika handoff-prompt <workstream> --deployed
   ```

   **Print its output verbatim as the last thing in your message.** It arrives already fenced; do not
   unwrap it, do not add a sentence inside the fence, and do not follow it with anything the reader
   would have to scroll past. The paste is what survives — commentary above it is read past.

   **It refuses rather than warns**, exit 3, when the tree is not what is installed or the two
   manifests disagree with the installed version. A refusal is not something to work around or
   paraphrase: it means the deploy did not happen, so there is no valid handoff to write yet. Deploy,
   then run it again.

   It composes the prompt from the machine — the installed version and that version's gate command,
   both only under `--deployed`. **It does not restate the live set**, and neither should you: the
   orientation you just wrote is what the next session reads.

## Don't

- **Don't move a thread.** Archiving needs the owner's ruling, and a handoff is not where it happens.
- **Don't write a second live orientation for one thread.** If the work has become two threads, that is a
  second dated workstream, and say so.

## Voice

Terse and factual, written for a first-time reader who was not in the room. **No agent-local codenames** —
"Option C", "Track B", "Phase 2", workflow IDs — say what a thing *is*. Filenames carry their stamp:
`YYYY-MM-DD-HHMMSS-topic.md` for dumps and orientations, from `lipika stamp`; `YYYY-MM-DD-topic.md`
elsewhere. **`stamp --for <dir>` returns the resolution that directory wants** — seconds for
`dumps/` and `orientation/`, which are read by being newest; a date for `reference/`, which is
addressed by subject. You always supply the topic.
**Timestamp every metric**: "9 KB at 2026-08-21", never "9 KB". Better still, cite the reference and let a
tool answer the number.
