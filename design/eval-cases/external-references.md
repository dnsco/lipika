# The `external-references` case — what it measures, and how much to trust each clause

**This document is not read at run time.** It holds what `claude plugin eval` must not hand a judge
model: which clauses predate the change they score, what each one replaced, what a suspicious result
looks like to the owner, and the measurements the case was built from. The runnable half —
`evals/external-references/prompt.md` and `graders/*.md` — carries only what a judge can act on.

The split exists because for a `type: llm` grader **the file body is the criteria, verbatim**. Before
this split, R2's body opened with *"Clauses 3 and 4 were written and committed BEFORE the change […]
score 1, 2 and 5 knowing they were authored against a known outcome"* — an instruction addressed to a
human scorer, which a judge model would have tried to act on.

Every grader below is keyed by its filename without `.md`, which is the name the runner reports.

## What the case measures

A session works a question whose evidence is **outside every repo it can read**: a rendered
documentation site behind SSO, a Slack thread of a dozen messages, a gist, a Notion page named as a
programme's source of record, two vendor pages. It reaches conclusions from them and then dumps.

### The original defect, measured 2026-09-16

On `workstreams/2026-09-16-can-agentomatic-host-workloads/` in the vault at `~/workspace/ai_docs`;
the vault-wide counts were taken 2026-09-17.

- Five dumps and three orientations were written from a GitHub Pages site, a gist, thirteen Slack
  messages, a repo branch and two vendor pages. **Not one link appeared in any of them** until the
  owner asked — and he asked only after scanning the dumps and finding the references he had assumed
  would be there were absent.
- Asked directly, the session wrote `dumps/2026-09-16-222023-primary-sources.md`. Its content was
  right — read / cited-but-not-opened split, what each reference supplied, and the access route that
  actually works (*behind GitHub auth; clone `vlognow/core-platform-proj-management` instead*). Its
  **frontmatter types itself `type: reference`** while the file sits in `dumps/`.
- The four dumps that *rest on* those references still name none of them. The provenance is
  quarantined in one late document rather than being reachable from the claims it settles.
- Hours later the project was renamed and every URL moved. That break was only visible because by
  then the links existed to break.
- Vault-wide, `reference/` had fired in **2 of 14 threads**, 6 documents total. In
  `skills/context-dump/SKILL.md` the word `reference` appeared exactly twice: once in the list of
  things that are immutable, once as a line in the shape diagram. **No step pointed at it.**

**The failure is not that the agent was careless. It is that "write down the sources" has a default
destination, and the default is `dumps/`.** An instruction with no named destination gets obeyed into
the wrong folder, and the one artefact produced is then superseded by the next dump.

### The second defect, measured on the fix, 2026-09-17

`0.3.6` fixed the destination and produced a new fault on the same thread. Step 2a named one
aggregate document per thread, so forty references — a Slack DM, a stakeholder deck, an incident
review, gists, public pages — became `###` headings inside a single 401-line file.

- **Correcting one reference means rewriting forty.** *Newest wins* over an aggregate, so the next
  document copies thirty-nine entries forward on faith or drops them silently. The shape the vault
  already used — one subject per dated file, still on line 38 of the skill's own diagram — has no
  such problem: a correction is one new file.
- **121 of those 401 lines are a `## Verbatim index`**, restating URLs already in the prose, written
  only so `lipika reference-check`'s literal-string matching would reach exit 0. A check drove the
  document's shape away from what a reader needs.

**This is the same class as the first defect, one level in.** The first was a destination nobody
named; the second is a *unit* nobody named.

### The second prompt turn is not a hint

The case's prompt has two turns, the second being *"Dump the sources too."* That is the instruction
the owner actually gave on 2026-09-16, and the run **still** put the artefact in the wrong place. A
version that only behaves when told the destination has not fixed anything. Do not remove the second
turn to make the case harder — removing it measures a different and easier thing.

### Vocabulary

**Reference**, never *source*. `sources/` at vault root means frozen eval measurements, never edited.
A grader that says "source" is testing a word the change deliberately retired. The one place *source*
survives in the runnable half is the prompt's second turn, quoted above, because it is a verbatim
record of what the owner typed.

## Per-grader provenance

### `r1-a-claim-from-a-page-names-the-page`

**Written and committed before the change.** No clause was amended.

*The change under test.* `skills/context-dump/SKILL.md` step 2 lists what a dump body carries, and
its basis bullet — *"State, with its basis"* — exemplifies only internal bases: `merged #4131`,
`commit a1b2c3d`, `gate green`. An external page never enters the frame, and measurement says the
rule therefore never fires on one. A bullet was added naming the media literally — Slack permalink,
Notion page, gist, dashboard, vendor page — requiring the dump to name the reference **in words** and
wikilink the thread's trace.

*Owner-facing scoring rule, deliberately kept out of the rubric.* **A run that cites well after being
asked proves nothing.** On 2026-09-16 the owner asked explicitly and still got the wrong shape. Score
the dumps written **before** any instruction about references; if every citation in the run appeared
after such a turn, this grader is **UNEXERCISED**, not a pass. A judge model cannot make that call —
it sees a file, not the turn order — so it is scored here, by hand, against the transcript.

**Still not fully scorable.** R1 needs an *unprompted* dump on a thread with external references.
Every citation measured so far came after someone asked.

### `r2-one-subject-per-trace-in-reference`

**Clauses 3 and 4 were written and committed before the change. Clauses 1, 2 and 5 were amended
2026-09-17, after the first scoring**, and they are the weaker half of this grader for exactly that
reason — a clause written after a result can only agree with it. What they replaced required a single
`reference/<stamp>-references.md` **inventory**, which the `0.3.6` run satisfied; the shape it
produced is the aggregate defect above, and no clause of the original could see it.

**Score clauses 3 and 4 as evidence; score 1, 2 and 5 knowing they were authored against a known
outcome.**

*What passed on `0.3.6`.* Clause 3 (placement in `reference/`) passed. Clause 4 passed — the misfiled
`dumps/2026-09-16-222023-primary-sources.md` was corrected by a newer document, not edited.

*Why one subject per file, so a later run does not re-propose the aggregate.* Both reasons are in
"The second defect" above: the aggregate fights immutability, and it forced a machine-readable
duplicate. Kept here rather than in the rubric because it is an argument for the rule, not a test of
it.

*What a suspicious result looks like.* A thread with an empty `reference/` and a clean-looking dump
is the **expected** appearance of the original defect, not evidence of a thread with no external
references. Check what the run read before crediting it with having nothing to file. **And a newer
one:** a run that writes many small files, one per URL, has substituted a different mechanical rule
for the old one. The unit is a **subject** — an argument, a decision, a document that settled
something — not a link. This half is judge-usable and was kept in the rubric.

*Clause 3 has moved.* Placement is now `r2b-a-trace-lands-in-reference`, a free `file_exists` check.
See below.

### `r2b-a-trace-lands-in-reference`

**New 2026-09-17, and it is a mechanism change, not a new rule.** It is R2 clause 3 — *the trace is
written to `workstreams/<ws>/reference/`* — moved from a judge to `file_exists`, which costs nothing.

**What it cannot see.** The documented limit is *"Only files created during the run count"*, so a
file the scaffold created, or one Claude only edited, is invisible to it. That makes it a proof of
**creation**, which is exactly what clause 3 claimed, and no evidence at all about editing. R2 clause
4 — *corrections are a newer dated document, never an edit* — stays with the judge and gains a
`tool_used: Edit` with `min: 0, max: 0` as a cheap cross-check.

### `r3-unopened-references-are-a-separate-visible-list`

**Clauses 2, 3 and 4 were written and committed before the change. Clause 1 was amended 2026-09-17,
after the first scoring**, and is the weaker half for that reason. What it replaced required the two
lists to be adjacent **headings in one document**; that followed from the aggregate shape R2 now
fails. With one subject per file, *cited but not opened* has no subject to live under and needs its
own home.

**The rule did not change — the adjacency of read and unread is still the load-bearing part. Only
what "adjacent" means changed, from two headings to two neighbouring documents.**

*The change under test.* Step 2a requires what was **read** and what was **cited by something read
but never opened** to be kept visibly apart. The second is the backlog, and it is the part that goes
missing silently. On the measured thread, the Notion page that is the stated source of record for the
entire programme had never been opened, and that only became visible once the two lists sat side by
side.

*What passed on `0.3.6`.* Clause 2 passed: the Notion Arya / Core Platform Proposal was named as the
stated source of record, with its last-read state and why it could not be opened.

*Clause 3 is unexercised and cannot be scored by a judge.* It requires that the orientation's
`## References` names the unopened ones and that `pickup` reads them out in its step-7 report without
a second document read. On `0.3.6` the agentomatic thread's orientation had no `## References`
section at all — but it was written at 14:52 and the trace at 15:51, so no handoff had run since.
**Score at the next handoff, by hand.** It is not in the runnable rubric because a single-case run
does not produce a subsequent `pickup`.

### `r4-a-mutable-reference-is-traced-not-linked`

**Written and committed before the change.** No clause was amended.

*The change under test.* The medium split (`sources/web/`, `sources/slack/`) was rejected 2026-09-17
— the medium is derivable from the URL, so it is a taxonomy nobody needs to choose. The distinction
that survives is **citable vs. must-be-traced**: a rendered doc page survives as a URL; a Slack
thread is not one document, its permalink dies with workspace access, and a message can be edited out
from under it.

*The measured good example*, kept here because it names a real repo: an auth-walled page names the
route that works — *behind GitHub auth, a browser without a session gets a login page; the content is
`vlognow/core-platform-proj-management` under `site/content/agentic_projects/arya/`, read with
`gh repo clone … --depth=1`*.

### `r5-nothing-grows-a-bibliography-it-did-not-need`

**Written and committed before the change.** This is the grader that fails if the change becomes
ceremony, and it is the one most likely to be scored generously.

*Owner-facing scoring rule.* **R1 through R4 all reward writing more, and this one is the only
counterweight.** A round where R1–R4 pass and R5 is scored "fine" is the expected shape of a change
that has become ceremony. Compare the diff's line count against what it removes, and compare a
no-external-references dump before and after — if it grew at all, say so. A judge scoring one run
cannot do either comparison; both are done by hand against the diff.

**The `## References` bound has no instrument.** *Bounded by attention, not by thread age. Never the
inventory.* R5 fails a run that reproduces the inventory, but nothing measures the section's length.
`file_exists` can instrument *placement* and not this. It dies when R5 is scored against a thread
with thirty references, which none has yet.

## Measured constraints of the runner, 2026-09-17 on `2.1.274`

Each of these was found by running the suite, not by reading the documentation.

- **A grader takes only `type`, `weight`, `arm` and its own type options.** Lipika's document
  frontmatter — `kind`, `life`, `status`, `date`, `case`, `amended` — is rejected at load with
  `Unrecognized key(s) in object`, and one bad key fails the whole case file. That vocabulary lives
  in this document instead. The graders were sealed 2026-09-17; R2 and R3 were amended the same day.
- **`focus: { source: file, path: … }` does not accept a glob.** The grader *throws* —
  `path "workstreams/*/reference/*.md" does not exist` — rather than failing. Since a dump's filename
  is a timestamp chosen at run time, no concrete path is knowable in advance, so the three
  content-judging graders use `focus: trace` and judge the session's write calls. The cost is the
  documented truncation to the first twelve and last twelve messages; each rubric says so and says
  what to do about it.
- **`file_exists` does accept a glob**, and reports a clean miss rather than throwing. That is why
  placement is checked there and not by a judge.
- **A judged grader will pass vacuously on an empty workspace.** R5 voted `PASS PASS PASS` against a
  run that never executed. Two fixes, both kept: R5 now fails explicitly when nothing was created,
  and `r0-the-run-produced-a-dump` guards the suite mechanically for free. The same run scored 0.25
  before and 0.11 after, which is the correct score for a run that did nothing.
- **The suite tests the checkout, not the deployed snapshot.** `plugins:` defaults to the nearest
  enclosing plugin, so a path target loads this working tree — uncommitted edits included. Good for
  iterating, and **not** a substitute for the loop's deploy gate, for exactly the reason a
  `claude -p` subprocess is not.

### The case is one turn, where the measured scenario was two

A case sends one user message. `context.history_file` is the only multi-turn route and needs a
`.jsonl` transcript. The prompt here is the **first** turn only, so the run is unprompted about
references — which is what R1 has always required and never had.

**The second turn is not lost, it is a second case still to write.** *"Dump the sources too"* is the
instruction the owner actually gave on 2026-09-16, after which the run still put the artefact in the
wrong place; a version that only behaves when told the destination has not fixed anything. That
needs its own case with a `history_file`, and until it exists this suite does not cover it.

### Open: the run could not authenticate

Every run so far ended `exit 1: Not logged in · Please run /login`, so **the session under test has
never executed** and no score from this suite means anything yet.

**The mechanism, measured from a `--keep-temp` directory.** The run gives the child session a
synthetic `HOME` — `<temp>/home`, with its own `<temp>/config` holding a fresh `settings.json` and
`.claude.json`. The credential on this machine is in the macOS Keychain, reachable only through the
real Claude Code configuration, which that child cannot see. So it starts logged out, and re-running
reproduces it exactly. It is not a broken credential and no amount of re-running fixes it.

**The route that survives a synthetic HOME is an API key in the environment**, since the
provider-selecting and authenticating variables are on the documented inherit allowlist. Export
`ANTHROPIC_API_KEY` in the shell the eval runs from. Operator action, by design — nothing in this
repo should hold it.

**This also leaves the sandbox question unmeasured.** The orientation carries a landmine saying an
eval run inherits `HOME` and so resolves the operator's real vault; the documentation says writes are
confined to the workspace and `$HOME` is unreadable. Nothing here settles it, because nothing ran.
The record is unchanged.

## What still cannot be scored by machine

Carried forward so a later round does not mistake a green suite for full cover.

- **R1's unprompted-citation rule** — needs transcript turn order, scored by hand.
- **R3 clause 3** — needs a subsequent `pickup`, which a single-case run does not produce.
- **R5's two comparisons** — need the diff and a before/after dump, not one run.
- **Nothing can see what a session read and did not write down.** Step 2a says it: *a clean exit is
  not a clean bill.* R1 is the only cover and it is scored by hand.
