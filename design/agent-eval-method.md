---
type: reference
status: reference
date: 2026-08-18
tags: [vault, meta, agents, evals, forensics, method]
---

# How the vault's agents get developed, measured and changed

The method behind the operating machinery (the `pickup` and `context-dump` skills, and the `curator` and
`scout` roles) and the
development role that measures them (the profiler, which runs as an ad-hoc brief against this document rather than
as a definition): where a change to one is authored, how its cost is measured, where the measurement is kept, and
what may be concluded from it. Cross-workstream reference — the *record* of what each round found lives
in the vault's own maintenance record, and the normative rules live in [[CLAUDE]]. This carries neither; it carries the
procedure.

**Written 2026-08-18, before the round it describes**, deliberately: it is meant to be amended in place as it is
used, not written up afterwards from memory. Amendments are dated at the bottom.

## The loop, and why it is a loop

1. **Author it here**, in `github.com/dnsco/lipika`. There is one copy of every definition, skill and
   tool; the port loop that used to be steps 1–2 was retired 2026-08-20 with the duplication it managed.
2. **Prove no rule was dropped**, with `lipika recall-check <pre-change-ref> <path>`. Every flag judged in
   writing; never reword a file to satisfy one. `--into` needs **every** survivor when content moves,
   including the source file if it kept some.
3. **Try it on real work**, then **profile it** — the frozen, verbatim measurement goes in the vault's
   `sources/evals/`. **Probe first**, always: nothing reports which version of a definition is live, and
   a rewrite reached through a symlink may not have loaded at all.
4. **Write the round's summary** into the workstream's own `reference/`, and feed the findings back to
   step 1.

Step 5 is not a duplicate of step 4. **A frozen eval is written for whoever audits the measurement; the summary
is written for the next agent, which will not read the eval.** So it is short — what changed this round, what was
run, then the findings and the numbers an agent needs to size its own work: current definition bytes, the last
measured span per role against its budget, and the traps that cost a call. One per round, dated,
`workstreams/<ws>/reference/YYYY-MM-DD-<topic>.md`; the newest is the one to read. It carries **no live status
and no next-moves** — those belong to the task frontier, and a summary that grows them has become a second
frontier.

Step 5's return edge is what makes this a loop rather than a checklist. Every durable improvement to these roles
so far came from a profile, not from re-reading a definition.

**One condition on step 4 that is easy to miss, and it was stated wrongly here until 2026-08-24.** The old
text said a definition is served stale "possibly for the whole session" and that the exercise run wants a fresh
session. **The documentation says the opposite**: Claude Code watches `~/.claude/agents/` and `.claude/agents/`
and loads edits within seconds, and restart is required only for an `agents/` directory absent at session start,
`--add-dir` directories, and `--disable-slash-commands`. Skills have documented live change detection.

What was actually measured on 2026-08-20 is narrower: an in-place edit **at a symlink's target** had not loaded
at +15 minutes, against an earlier "a few minutes" on a file owned **directly** in `~/.claude/agents/`. That is
one observation of a lower bound, not a duration — and the two conditions differing points at the symlink, not
at a timer. Suspected cause: a watcher registered on the link that never fires when only the target changes,
which would make the staleness **unbounded**. **Prompt caching is not the mechanism** — it keys on the exact
token prefix, so changed text is a cache miss and the new text runs.

Consequence for this method: **probe before you profile, always**, because nothing reports which version is
live. Do not wait out an interval; there is no measured interval to wait out.

**Probe behaviourally. Never ask a role to quote its own definition.** Measured the same day: a `scout` asked to
quote the command it had been told to use returned a rule that has **never existed in any version of that
file, in any repo** — verified by `grep -rl` and `git log --all -S`, both empty. It produced a fluent paraphrase
of the rule it was operating under and presented it as a quotation, which reads as confirmation and is worthless
as evidence. So: give the new text **a command or a write path the old text does not have**, dispatch real work,
and read the transcript for the call. What an agent did is not confabulable; what it says about itself is.

## Where the artifacts live

| artifact | location |
|---|---|
| agent definitions (live) | `~/.claude/agents/<role>.md` |
| agent definitions (both repos) | `agents/<role>.md` in this vault and in the template |
| the dump skill | `~/.claude/skills/context-dump/SKILL.md`, `skills/context-dump/SKILL.md` in both repos |
| subagent transcripts | `~/.claude/projects/<project-slug>/<session-id>/subagents/agent-<agentId>.jsonl` |
| task-output symlinks to the same files | `/private/tmp/claude-502/<slug>/<session-id>/tasks/<id>.output` |
| frozen profiling reports | `sources/evals/YYYY-MM-DD-HHMM-<subject>-profile.md`, **`HHMM` from `date -u` when you write it** — not the run's start, not its completion |
| the findings drawn from them | `workstreams/vault-maintenance/` |
| the round summary an agent actually reads | `workstreams/<ws>/reference/YYYY-MM-DD-<topic>.md`, newest first |

Timestamp an eval filename **to the minute**, from the profiled agent's completion time, so several evals in one
day cannot collide:

```bash
D=~/.claude/projects/<project-slug>/<session-id>/subagents
stat -f '%Sm' -t '%Y-%m-%d-%H%M' "$D/agent-<agentId>.jsonl"
```

Frontmatter on an eval: `type: source`, `kind: eval`, `date`, `time`, `subject`, `tags: [..., verbatim]`, plus a
provenance paragraph naming the transcript it was read from.

## What a profile is FOR — read for what is obviously wrong, first

**The point is catching the traps we keep falling into, not producing comparable numbers.** Every
improvement that has held came from someone reading a transcript and noticing something glaring: a loop that
called `git` inside `$( )` and failed twice without being diagnosed, a regex that blew up and burned 105
seconds to return two rows, an agent that read a 29KB file every sub-agent already had as its system prompt, a
spawn that never passed the key its own instructions demanded.

None of those needed a controlled comparison. They needed someone to look.

So do the sanity pass first, and do not let it wait on measurement hygiene:

- **Scan the call list end to end.** Anything that returned nothing, errored, or ran absurdly long against its
  neighbours is the finding. Two identical failures in a row means nobody read the first one.
- **Ask what was re-derived.** A fact supplied in the prompt and then recomputed is pure waste, and it recurs.
- **Ask what landed in the wrong context.** Recon in the one context that must survive to the end is the
  most expensive place to put it.
- **Ask which instruction did not fire.** If a definition said to do something and the transcript shows it
  did not happen, that is not a lapse to note — it is a rule that needs to become a tool.
- **Name the footguns.** A trap hit twice across rounds is worth more than any number in this document.

**Numbers are the second pass, and they do not have to be uniform.** Do not hold back a change to keep a
measurement comparable, do not re-run a pass for a clean number, and do not present a confound as though it
disqualified the round. Say what changed, say what you measured, move on. This is a craft as much as a
measurement — the transcripts are evidence, not an experiment, and the goal is a faster, less trap-prone
system, not a tidy series.

## Reading a transcript

**Never `cat` or `Read` one whole.** It overflows context and exceeds the 30KB Bash cap. Slice it with `jq`:

```bash
# what it did, one row per call
jq -r 'select(.message.content) | .message.content[]? | select(.type=="tool_use")
       | "\(.name)\t\((.input.command // .input.file_path // "") | tostring | gsub("\n";" ⏎ "))"' "$F" | cut -c1-170 | nl -ba

# when it did it
jq -r 'select(.message.content) | select(.message.content[]?|select(.type=="tool_use")) | .timestamp' "$F" | nl -ba

# what it cost
jq -r 'select(.message.usage) | "\(.message.usage.cache_read_input_tokens // 0)\t\(.message.usage.output_tokens // 0)"' "$F" | nl -ba
```

**Do not hand-roll the mechanical half.** `tools/agent_transcript.py` finds a transcript (including under a
worktree's own project slug), lists a session's subagents, and prints one row per tool call with the bytes that
call returned into context, a per-tool aggregate, and the cost figures with every trap below already applied:

```bash
lipika agent-transcript --list                      # sessions and subagents, newest first
lipika agent-transcript <agent-id>                  # calls, per-tool totals, cost
lipika agent-transcript <agent-id> --calls --min-bytes 2000   # just the expensive reads
lipika agent-transcript <agent-id> --grep orientation-audit   # did the check actually run
```

Bytes-returned is the denominator of a relevant-fraction measurement; classifying each row as load-bearing,
duplicated or never-used is the judgement, and that stays yours. The `jq` recipes below remain the reference for
anything the tool does not answer.

Four traps, each of which has produced a wrong number here:

- **Number by CALL, not by line.** Heredocs span many lines and inflate every count. The `gsub` collapse above is
  what makes the numbering trustworthy.
- **A resume is not a unit of work.** Resuming an agent re-pays its whole prior transcript as input before it does
  anything new, so **never sum a resumed agent's token figures**. Measured: one clerk's three runs sum to 213,957
  while a single well-specified call is 65,545, and run 2 made three calls yet cost more than run 1's eighteen.
  One head-librarian's naive sum of 237,630 overstates an uninterrupted run by ~44%. **Re-spawn with a tight
  brief rather than resume.**
- **Cache-creation is not context paid for.** Summing `cache_creation_input_tokens` against a peak read counts
  churn *within* one run as cost, and the number it produces looks like a context problem that is not there. Read
  `cache_read_input_tokens` for what a turn actually loaded, and report the peak rather than the sum.
- **A backgrounded child's report is not in its parent's transcript.** It arrives out of band, so the delegate's
  context cost cannot be attributed from the parent alone — measured 2026-08-19, a 28,436 B scout report was
  absent from the dispatcher's file entirely. Profile the child's own transcript, or say the number is a floor.
- **A worktree session gets its own project slug.** The artifact table above assumes one slug per repo; a session
  rooted in `<repo>/.claude/worktrees/<name>` writes under a slug derived from that path, so transcripts are not
  where the table says. Resolve the slug from the session, not from the repo.
- **Never collapse newlines in a command preview.** The `gsub` in the recipe above uses ` ⏎ ` for exactly this
  reason: collapsing to `|` fabricates pipelines, and five multi-line commands read as broken `x | echo` before
  the raw input was checked. A trap that invents a defect is worse than one that hides a number.
- **A live transcript grows while you read it.** Say where you stopped, and say the file was still being appended
  to. One profile here did exactly that and was right to.

## Reporting a profile

**Every profile opens with a qualitative read of how the run went, before any figure.** Not optional, not a
closing paragraph — a profile that is only numbers reliably misses the thing worth fixing, and the numbers are
the evidence for the read rather than a substitute for it. Its material is the agent's own reasoning:

```bash
lipika agent-transcript <agent-id> --thinking      # the largest blocks, in full
```

Answer these in your own words, each pointing at a call number or a quoted line:

- **Where did it thrash?** Repeated attempts at one thing, a range guessed three times, an approach abandoned
  and resumed. Note what it was trying to satisfy — thrashing is usually a rule it could not meet, not
  incompetence, and the fix is then the rule.
- **What did it re-derive that it already had?** Its own earlier result, its dispatcher's brief, another
  agent's report. This is the cheapest large saving available and it never shows up as a defect.
- **Where did it sound confused, or confidently wrong?** A conclusion stated without the read that would
  support it. A fabricated citation. A rule it restated in a form the definition does not contain.
- **What did it do that nobody asked for**, and what did it decline that it should have raised?
- **Where did it hesitate for the right reason?** Refusals and self-corrections are the most valuable thing in a
  transcript and the easiest to optimise away by accident. Name them so a later round does not delete them.
- **If you could tell this agent one thing before it started, what would it be?** That sentence is usually the
  next definition change, and it is often not what the numbers point at.

**A size is not a finding.** Reasoning bytes and block counts locate where to read; they say nothing about
whether the thinking was good. Measured: one profile reported a 13,451 B thinking block belonging to a role
whose largest was 6,539 B — the big block was the profiler's own. Quote the line, or say you did not read it.

**And do not invent a defect out of transcript shape.** The harness emits reasoning in its own assistant
message, separate from the one carrying the tool call, so *"turns that thought and called nothing"* counts every
deliberation. That signal was built here, measured against a real run, and deleted rather than shipped.

- **Lead with the glaring problems**, per the section above. A profile whose findings are all deltas has
  probably missed the thing worth fixing.
- **Report tool calls, tokens and wall clock separately.** They are separate axes and they move independently —
  dead waiting shows up in none of the token figures.
- **Classify every avoidable call** as one of four: *defect* / *should be a tool* / *retry-or-refinement loop* /
  *duplicated with another role*. Useful because it is per-call: it keeps working when a round changed many
  things at once, which most rounds do and should.
- **Separate what an agent did from what it was told to do.** A call ordered by the definition is not the agent's
  waste; it is the definition's.
- **Check the boundary from the artifacts, not from the report** — `git status --porcelain`, the actual writes in
  the transcript — because an agent's account of staying inside its contract is not evidence that it did.
- **Reproduce the agent's report as returned** when freezing it. `sources/` is frozen by rule, correctable only by
  appending, and that is the point: a measurement a later consolidation paraphrases stops being a measurement.

## What the profiles have established

Standing conclusions. Each was measured, and each is the reason some rule now takes the shape it does.

- **Prose in a definition does not fire; a tool with an exit code does.** Four instances in one session: a scope
  screen shipped unsatisfiable and went unnoticed until used; "dispatch a scout if recon runs past a handful of
  commands" did not fire across fourteen recon commands; an agent told to prefer the Obsidian CLI never checked
  which tree it was answering about; and a checker reported "no frozen-tier files changed" nine times having read
  no diff. Every fix that held was a script. **Prefer a tool that refuses to prose that asks** — and it is the
  cheaper end, since a definition is a system prompt paid on every invocation.
- **A pass has a floor, and the floor is the cost.** The marginal work — reading three overlapping docs and
  emitting the survivor — was ~19k of a 185.9k pass, 10%. The rest is paid regardless of backlog, and input
  context is re-paid every turn, so the floor is multiplied by turn count. **Batching docs into one scope is
  nearly free; adding a scope costs a whole floor.**
- **The bottleneck is round trips, not command runtime.** Strip one outlier and commands were 9% of a phase while
  model generation between calls was 59%. Halving the call count halves the phase; making commands faster buys
  almost nothing.
- **Wall clock hides where tokens do not.** One run's 915s idle gap was 55% of its span and appears in no token
  figure.
- **The porting placeholders are the most-repeated trap in this record**, broken a different way almost every
  time they are touched: a live placeholder shipped into a file agents load as a system prompt; a substitution
  that rewrote a tool's own docstring and then its comparison code, making the checker a silent no-op; a private
  vault path leaked upward into the public template; and a port tool that skipped inline code spans as
  "discussion" and so left every real usage unsubstituted, because paths here are always written in backticks.
  Four rounds, four variants, one cause: each tool re-deriving which tokens exist and where one may appear. Both
  answers lived in one imported module rather than in each tool, and the whole mechanism was **retired
  2026-08-20** along with the duplication that needed it. The transferable finding is not about
  placeholders: **four tools each re-deriving one rule produced four different bugs**, so a rule with
  more than one caller belongs in a module they import, not in prose each of them interprets.
- **Complete markers are the cheapest speed-up found.** Same role, same workstream: 65,545 tokens / 18 calls /
  365s with incomplete markers against 48,811 / 13 / 117s with complete ones, on a *larger* entry.

## Naming what must not be optimised away

Before any efficiency work touches a definition, **name the judgement acts it must preserve**, from the profiles.
Each is a read of specific prose against a claim followed by a decision *not* to act, and none of them can be
batched:

- rejecting a sub-agent's finding as a false positive after reading the cited lines, where acting would have
  damaged a correct doc;
- recording a scope that did no work as `skipped` rather than consolidated, so it still reads "not looked at";
- refusing to invent a convention when a supplied decision's premise turned out to be wrong;
- verifying a load-bearing manifest claim rather than trusting it, and verifying that deleted content survived in
  its named survivor;
- reporting an uncorroborated claim *as* uncorroborated, and classifying a pre-existing flag as history rather
  than one's own;
- refusing to credit a check that had become self-confirming;
- and the clerk refusing to strike an item on source-code evidence when the entry carried no marker, then naming
  the distinction once the marker arrived: *"the fact did not change; the licence did."*

A cheaper agent that no longer does these is not cheaper; it is a different agent.

## Choosing a model for the work

Mid-tier for forensic and mechanical work — transcript profiling, manifest validation, port checks, factual state
manifests. That is where the wall clock goes, and it was measured doing it well. Keep the strongest model for
judgement-bearing prose, because every failure that has mattered here was **distinction-collapse**: *failed* vs
*never requested*, *identical* vs *flattened*, *settled* vs *settled-but-unexecuted*, *fixed* vs *unfixed*.

**`model:` is per-agent; `effortLevel` is not.** A role's model is set in its own frontmatter, so the split
above is encodable and should be encoded — prose telling an invoker to choose has measurably not fired. Effort
is session-wide, subagents inherit it, and the `Agent` tool exposes no per-agent override, so it can only be
stated. Say when it changed rather than hiding it, and then keep going: a confound is a caveat on one number,
not a reason to hold back a change or re-run a pass.

## Amendments

*Dated notes added as this method gets used. Append; do not rewrite the sections above from memory.*

- **2026-08-18 — written**, before the round it describes, from three frozen profiles in `sources/evals/` and the
  findings in the eval round that produced them.

- **2026-08-18 — a definition's BODY refreshes live; its `model:` frontmatter does not.** Measured in one
  session: `agents/scout.md` was edited to `model: sonnet` and dispatched without a restart. It used
  `scope_recon.py`, `frontier_lag_check.py` and `obsidian unresolved` — all instructions that exist only in the
  edited body and were absent from its prompt — and ran as `claude-opus-5` throughout. So a body edit takes
  effect immediately and a model pin does not: it binds at session start. **Restart before profiling a role
  whose model you just changed**, or you measure a different quantity than the one you set. Read the model back
  from the transcript rather than assuming either way:

  ```bash
  jq -r 'select(.message.model)|.message.model' "$F" | sort -u
  ```

- **2026-08-18 — do not restate a definition's contents in the prompt you profile it with.** The clerk was
  dispatched with a prompt that named `frontier_slice.py` and described the archivist drain, both of which its
  edited definition also carried. When it used the drain and did *not* use the slice, neither result was
  attributable: prompt and definition said the same thing. **Give a bare prompt when the question is whether a
  definition fired.** The scout run was designed that way afterwards and settled the question in one dispatch.

- **2026-08-18 — a tool that hands another tool an input it refuses is a defect in the first tool.**
  `scope_recon.py --markers` emitted single-segment `repo#N` refs; `verify_pr_markers.py` refuses that form and
  aborts the entire batch on one bad ref, so a scout lost its whole marker resolution and re-spelled by hand.
  Neither tool was wrong in isolation. **Check the contract between tools you chain, not just each one's
  output** — and prefer a tool that reports the unusable input separately to one that poisons a batch with it.

- **2026-08-19 — naming a tool in a definition does not make an agent reach for it. Requiring its OUTPUT does.**
  Measured cleanly on the `scout`'s first run, dispatched with a bare prompt so only the definition was in play:
  its headline instruction is to start with `scope_recon.py`, and it instead ran six hand-written shell calls
  first, then ran the tool eighth — where it reproduced what those calls had already computed, to the same doc
  counts, the same folder-note byte figure and the same delta. The `frontier-clerk` did the same thing with
  `frontier_slice.py`, paging back 92% of a 44KB frontier through six round trips, though that run cannot
  attribute the failure because the prompt named the tool too.

  The fix that does not need a new script: **make the report schema demand the tool's output.** The scout must
  now open its report with `scope_recon.py`'s raw output under a named heading; the clerk must cite the slice
  line number for every line it changes. An agent can still hand-roll, but it cannot produce a conforming report
  without having run the tool. Prefer this to removing the agent's ability to hand-roll — the scout used `Bash`
  legitimately for git facts the tool does not emit.

- **2026-08-19 — a tool-based read does not satisfy the `Edit` guard.** `Edit` refuses a file the session has
  not opened with `Read`, and reading through `Bash` — `sed`, or a slicing tool — does not count. So "stop
  paging with `sed`, use the slice tool" and "write with `Edit`" are in direct tension, and the first `Edit`
  after a tool-based read will fail. The cheap answer, which the clerk found unaided and which now sits in its
  definition: `Read` ten lines at the first anchor's offset, using the slice's own line numbers. One small read,
  once — not a re-read of the file the slice existed to avoid.

- **2026-08-18 — running one link check is running half of one.** `dangling_links.py` scans bodies and knows
  the false-positive classes; `obsidian unresolved` reads the index and sees `links:` frontmatter fields no body
  scan reaches. Measured on the same vault at the same commit: **0 and 6, both correct.** The assumption going
  in was that the Python tool duplicated the CLI; it does not.
