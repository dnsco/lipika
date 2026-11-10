---
type: reference
status: reference
date: 2026-08-18
tags: [vault, meta, agents, evals, forensics, method]
---

# How the machinery gets tested, measured and changed

How a change to a skill, agent definition or tool is tested before it ships, and how a run of the real
thing is measured afterwards. The loop that orders these steps — graders first, author, deploy, dump,
restart, gate, probe, eval — is in `CLAUDE.md` and is not restated here.

## Two layers of test

| layer | where | tests | run |
|---|---|---|---|
| CLI suite | `evals/<name>/test_*.py` | a tool's mechanics — exit codes, output, refusals, against fixtures it builds itself | `python3 evals/<name>/test_<name>.py`; exit 0 all pass, 1 any fail |
| graders | `evals/<case>/graders/*.md` | an agent's judgement, in a scaffolded vault | `claude plugin eval` |

**Mechanics go in the CLI suite.** A tool change gets a hand-audited red case and a green case there,
written red first. It is deterministic, costs nothing, and runs in seconds.

**Graders are only for what a model decides.** A definition change needs them, committed **before** the
change: a grader written afterwards agrees with whatever happened. **Graders falsify; they do not show
improvement** — never eval the version you are replacing.

**Run the whole grader suite after any definition change**, not only the case you meant to move. A trim
that keeps every rule's text can still regress another case's dispatch path, and `recall-check` will not
see it.

## Graders — the suite, and how it runs

### Anatomy of a case

`evals/<case>/` holds four things:

- **`case.yaml`** — `schema_version`, `name`, and `context.scaffold_script`. A comment carries the command
  that runs the case. It has no cost key.
- **`prompt.md`** — frontmatter, then the prompt the run receives, verbatim. The frontmatter holds
  `name`, `description`, `tags`, `allowed_tools`, `max_turns`, `timeout_seconds`, and
  `expected_outcome`: the prose the judges read as the target.
- **`scaffold.sh`** — seeds the workspace, which **is** the vault the run works in: threads, dumps,
  orientations with known dispositions. It runs as the operator, outside the sandbox, so it never calls
  `lipika init` and writes only under `$PWD`.
- **`graders/*.md`** — one prediction per file. Frontmatter is the grader's type and options; the body
  says what it checks, and for an `llm` judge the body is the criteria verbatim.

### Running it

```bash
ANTHROPIC_API_KEY=$(security find-generic-password -s anthropic-eval-key -w) \
  claude plugin eval . --scaffold --allow-tools Bash Write Edit --trust-plugin --judge-model sonnet \
  --ablation none --runs 1 --keep-temp --max-cost-usd 7.5          # add --case <name> for one
```

- **Every run carries `--max-cost-usd` and `--runs 1`.** `runs` defaults to 3 plus a baseline arm. The
  ceiling is checked before each run launches, so it overruns by the runs in flight. The Console limit on
  `anthropic-eval-key` is the backstop.
- **`--allow-tools` grants the gated tools, and only those: `Bash`, `Write`, `Edit`, `WebFetch`,
  `WebSearch`.** A case's `allowed_tools` asks; `Read`, `Glob`, `Grep`, `Skill`, `Agent` and `TodoWrite`
  are granted without the flag. A case asking for a gated tool it was not granted is listed on stderr as
  `not granted`. `Bash Write Edit` covers every case.
- **Pass the key per command, never `export` it.** The child gets a sealed `HOME`, so OAuth fails and
  only an env var reaches it; an ambient key displaces OAuth for every session in that shell. The judges
  run in your process and bill normally.
- **`--judge-model sonnet`, always.** The default judge is `haiku`, which voted FAIL 3/3 on curate
  reports that met every clause — 2026-09-25 and 2026-10-01 — where `sonnet` voted PASS 3/3 on the same
  case. A case cannot set its judge model; only the flag can. The runner records votes, not reasons.
- **`--scaffold` is off by default**; without it the seeded vault never exists.
- **`--keep-temp`, always.** Without it the trace is deleted. The kept directory's `home/` is sealed mode
  000; `chmod 700` it and the `sealed/` inside to read it, and never run git in there.
- **Reports** go to `evals/results/<timestamp>/{report.html,aggregate-result.json}`, gitignored. End every
  run by linking the owner to its `report.html` — the last line the run prints. A summary of the
  per-grader lines is not the record he reads.

### Reading it

- **Read the per-grader lines, never the headline.** A grader skipped for the cost ceiling scores as a
  failure, and the summary can contradict the lines.
- **Exit 1 is "below threshold" or "a case failed to load".** Read stderr.
- **A score is only as good as what the grader can see.** Before blaming a definition, read the kept
  trace: a grader counting the wrong tool name, or a judge failing on evidence outside its focus, looks
  exactly like a regression.

### Writing one

- **Prefer mechanical.** `regex` with `target: trace` sees the **whole** run: match inside the write it
  judges — `/reference/[^"]*\.md","content":"…<fact>` — and use lookaheads for several facts.
  `tool_used` with `input_match` counts calls.
- **An `llm` judge sees less than it seems.** `focus: trace` is the first and last 12 messages; `files` is
  paths only; `{source: file, path}` is one literal path. Use a judge only when its focus holds the
  evidence.
- **Keys.** A grader takes `type`, `weight`, `arm` and its type's options; an unknown key rejects the
  whole case. `tool_used`: `tool`, `input_match`, `min` (**default 1** — an absence check needs `min: 0`),
  `max`. `tool_order`: `before`/`after`, a name or `{tool, input_match}`, first occurrences. `regex`:
  `target`, `pattern`, `match: contains | not_contains | count:N`. `file_exists`: `path`, `exists`. The
  mechanics, read from the harness bundle, are the vault trace
  `workstreams/2026-09-24-what-does-a-handoff-cost/reference/2026-09-24-plugin-eval-grader-mechanics.md`.
- **The subagent tool is `Agent`**; `Task` is an alias the trace never records.
- **Every case needs a free guard** — a `file_exists` on its main output — or a judge can pass an empty
  workspace.
- **Test a new grader on a kept trace, green and red**, before paying for a run.

## Speed

**Any operation somebody waits on should finish inside two minutes** — a north star, not a limit on any
role. As a limit it does damage: a fan-out pass at `max(child) + overhead` can never meet it, and it
discourages the tools that are the cheap end. Eval, profiling and developer-facing work are exempt.

The quantity is **span**: wall clock from a pass's `start` to its `stop`, what a human waits, computed by
`pass_log.py` as `span_s`. `lipika span-report` prints the series and **always exits 0**; an operation
over the star is a fact, not a backlog item.

## Where the artifacts live

| artifact | location |
|---|---|
| definitions, as authored | `agents/<role>.md` and `skills/<name>/SKILL.md` in Lipika |
| definitions, as installed | `~/.claude/plugins/cache/lipika/lipika/<version>/`, a snapshot taken at deploy; `lipika doctor` compares it with the tree and names where definitions are read from |
| subagent transcripts | `~/.claude/projects/<project-slug>/<session-id>/subagents/agent-<agentId>.jsonl` |
| task-output symlinks to the same files | `/private/tmp/claude-502/<slug>/<session-id>/tasks/<id>.output` |
| cases, graders and CLI suites | `evals/` in Lipika |
| scored runs | `evals/results/<timestamp>/`; the trace survives only under `--keep-temp` |
| frozen profiles | the vault's `sources/evals/YYYY-MM-DD-HHMM-<subject>-profile.md` |
| what a round found | a dump in the thread doing the work |

**Name a profile to the minute, from the profiled agent's completion time**, so several in one day cannot
collide:

```bash
stat -f '%Sm' -t '%Y-%m-%d-%H%M' "$D/agent-<agentId>.jsonl"
```

A profile's frontmatter is `type: eval`, `date`, `tags` and `subject`, plus a provenance paragraph naming
the transcript it was read from. It reproduces the agent's report as returned: `sources/` is frozen, and a
paraphrased measurement stops being one.

## What a profile is for — the obvious thing, first

**A profile exists to catch the traps we keep falling into, not to produce comparable numbers.** The
improvements that hold come from someone reading a transcript and noticing something glaring: a command
failing twice undiagnosed, a regex burning minutes to return two rows, an agent reading a file it already
had as its system prompt, a spawn missing the key its instructions demanded.

Do the sanity pass first:

- **Scan the call list end to end.** Anything that returned nothing, errored, or ran absurdly long against
  its neighbours is the finding. Two identical failures in a row means nobody read the first one.
- **Ask what was re-derived.** A fact supplied in the prompt and then recomputed is pure waste.
- **Ask what landed in the wrong context.** Recon in the one context that must survive to the end is the
  most expensive place for it.
- **Ask which instruction did not fire.** That is not a lapse to note; it is a rule that needs to become
  a tool.
- **Name the footguns.** A trap hit twice across rounds is worth more than any number.

**Give a bare prompt when the question is whether a definition fired.** A prompt that restates the
definition makes every result unattributable.

**A role's `model:` takes effect only in a new session.** After changing one, restart before profiling
it, and read the model back from the transcript:

```bash
jq -r 'select(.message.model)|.message.model' "$F" | sort -u
```

**Numbers are the second pass, and they need not be uniform.** Do not hold back a change to keep a
measurement comparable, and do not re-run for a clean number. Say what changed, say what you measured,
move on.

## Reading a transcript

**Never `cat` or `Read` one whole** — it overflows context and the Bash output cap. Use the tool:

```bash
lipika agent-transcript --list                                # sessions and subagents, newest first
lipika agent-transcript <agent-id>                            # calls, per-tool totals, cost
lipika agent-transcript <agent-id> --calls --min-bytes 2000   # just the expensive reads
lipika agent-transcript <agent-id> --grep orientation-audit   # did the check actually run
lipika agent-transcript <agent-id> --thinking                 # the largest reasoning blocks, in full
```

It prints one row per call with the bytes it returned, a per-tool aggregate, and cost with the traps below
applied. Classifying each row as load-bearing, duplicated or unused is the judgement, and stays yours. For
anything it does not answer, slice with `jq`:

```bash
jq -r 'select(.message.content) | .message.content[]? | select(.type=="tool_use")
       | "\(.name)\t\((.input.command // .input.file_path // "") | tostring | gsub("\n";" ⏎ "))"' "$F" | cut -c1-170 | nl -ba
jq -r 'select(.message.usage) | "\(.message.usage.cache_read_input_tokens // 0)\t\(.message.usage.output_tokens // 0)"' "$F" | nl -ba
```

The traps, each of which has produced a wrong number:

- **Number by call, not by line.** Heredocs span many lines; the `gsub` collapse is what makes numbering
  trustworthy.
- **Never collapse newlines to `|`.** It fabricates pipelines; ` ⏎ ` does not.
- **A resume is not a unit of work.** A resumed agent re-pays its whole prior transcript as input, so never
  sum its token figures. Re-spawn with a tight brief rather than resume.
- **Cache creation is not context paid for.** Read `cache_read_input_tokens` for what a turn loaded, and
  report the peak rather than the sum.
- **A backgrounded child's report is not in its parent's transcript.** Profile the child's own transcript,
  or say the number is a floor.
- **A worktree session has its own project slug.** Resolve the slug from the session, not the repo.
- **A live transcript grows while you read it.** Say where you stopped.

## Reporting a profile

**Open with a qualitative read of how the run went, before any figure**, from the agent's own reasoning.
Answer these, each pointing at a call number or a quoted line:

- **Where did it thrash?** Thrashing is usually a rule it could not meet, and the fix is then the rule.
- **What did it re-derive that it already had?** The cheapest large saving, and it never shows as a defect.
- **Where did it sound confused, or confidently wrong?** A conclusion without the read to support it; a
  fabricated citation; a rule restated in a form the definition does not contain.
- **What did it do that nobody asked for**, and what did it decline that it should have raised?
- **Where did it hesitate for the right reason?** Refusals and self-corrections are the easiest thing to
  optimise away by accident. Name them.
- **If you could tell it one thing before it started, what would it be?** That is usually the next
  definition change.

Then:

- **A size is not a finding.** Byte counts locate where to read; quote the line, or say you did not read it.
- **Do not invent a defect from transcript shape.** The harness emits reasoning in its own message, so
  "turns that thought and called nothing" counts every deliberation.
- **Report tool calls, tokens and wall clock separately.** Dead waiting shows in no token figure.
- **Classify every avoidable call**: *defect*, *should be a tool*, *retry-or-refinement loop*, or
  *duplicated with another role*.
- **Separate what an agent did from what it was told to do.** A call the definition ordered is the
  definition's waste.
- **Check the boundary from the artifacts** — `git status --porcelain`, the writes in the transcript —
  not from the agent's account of itself.

## What profiles have established

- **Prose in a definition does not fire; a tool with an exit code does.** Prefer a tool that refuses to
  prose that asks.
- **Naming a tool does not make an agent reach for it; requiring its output does.** Make the report
  demand the tool's raw output under a named heading, and the agent cannot conform without running it.
- **A pass has a floor, and the floor is the cost.** The marginal work is a small fraction; input context
  is re-paid every turn. Batching work into one pass is nearly free; adding a pass costs a whole floor.
- **The bottleneck is round trips, not command runtime.** Halving the call count halves the phase; faster
  commands buy almost nothing.
- **Wall clock hides where tokens do not.** An idle gap can be most of a span.
- **A rule with more than one caller belongs in a module they import.** Several tools each re-deriving one
  rule produce several different bugs.
- **A tool that hands another tool an input it refuses is a defect in the first tool.** Check the contract
  between tools you chain, and prefer one that reports an unusable input separately to one that aborts the
  batch.
- **Complete markers are the cheapest speed-up.** An agent reading items with complete death conditions
  and `as-of` does less re-checking.
- **Running one link check is running half of one.** `lipika dangling-links` scans bodies;
  `obsidian unresolved` reads the index and sees frontmatter links no body scan reaches. Run both.
- **`Edit` needs its own `Read`.** A slice read through Bash does not satisfy the guard; `Read` a few lines
  at the anchor.

## What must not be optimised away

Before efficiency work touches a definition, **name the judgement acts it must preserve**. Each is a read
of specific prose against a claim, followed by a decision *not* to act:

- rejecting a sub-agent's finding as a false positive after reading the cited lines;
- recording a pass that did no work as `skipped`, so it still reads "not looked at";
- refusing to invent a convention when a supplied decision's premise is wrong;
- verifying a load-bearing claim rather than trusting it, and verifying that deleted content survived
  where it was said to;
- reporting an uncorroborated claim *as* uncorroborated;
- refusing to credit a check that has become self-confirming;
- declining to strike an item on evidence that does not license it: *"the fact did not change; the
  licence did."*

A cheaper agent that no longer does these is not cheaper; it is a different agent.

## Choosing a model

Mid-tier for forensic and mechanical work — transcript profiling, manifest validation, factual state.
The strongest model for judgement-bearing prose, because the failures that matter are
**distinction-collapse**: *failed* vs *never requested*, *identical* vs *flattened*, *settled* vs
*settled-but-unexecuted*.

**`model:` is per-agent; effort is not.** A role's model is set in its frontmatter, so encode the split
there — prose telling an invoker to choose does not fire. Effort is session-wide and subagents inherit it,
so it can only be stated. Say when it changed, and keep going: a confound is a caveat on one number.
