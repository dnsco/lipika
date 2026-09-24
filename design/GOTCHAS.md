---
type: reference
status: evergreen
tags: [vault, gotchas]
---

# Gotchas

What bites after setup. None of it is visible from inside a session, which is why it is written down.

The first two are about **discipline** and cost you the record itself. The rest are mechanical, and every claim
below was measured rather than assumed.

## 1. A project session may not read this knowledge base's CLAUDE.md — say so explicitly

Claude Code loads `CLAUDE.md` from the current directory, its parents, and `~/.claude/`. A session rooted in a
**code project** therefore loads the *project's* — this knowledge base's `CLAUDE.md` sits in a subdirectory, and
a symlinked one at that, so whether it gets read is a coin flip.

An agent that writes here without it produces exactly what the conventions exist to prevent: an undated
filename, a doc in the wrong tier, chat voice, agent-local codenames ("Option C"), or an edit to a record.

Three mitigations. Use all three, because each covers a different hole:

1. **`pickup` at the start of a session that will touch the vault.** It carries the conventions, reads the
   current orientation, and is the only mitigation that fires before any writing rather than at the moment of it.
2. The `~/.claude/CLAUDE.md` pointer — that one every session does load.
3. Say it out loud when the work is substantial: *"run `pickup` before you write anything."*

Default assumption: if a session invoked neither skill, it has not read the conventions.

## 2. Reads are free; writes go through the skills, and two agents each write one thing

A project session sees `<vault>/` in its tree and treats it like any other directory — it will edit a doc in
place, "tidy" a section that reads as stale, or delete what looks obsolete. Unlike a bad code change, nothing
fails: the record is just quietly worse, and the loss shows up weeks later as a re-derived dead end.

**Every document is a record or a view, and the two take opposite handling.**

- **A record is never edited.** Dumps, `reference/` traces, `sources/`, `external/`, and every orientation
  already written. Correct one by writing a newer one, never by changing it — the newer document supersedes it,
  and the older one stays true about the moment it describes.
- **A view is regenerated wholesale, never patched.** The orientation a handoff writes, and the vault index.
  A bad regeneration is fixed by regenerating again, because the records behind it are intact.
- **`architecture/` carries the owner's reviewed judgement.** This vault's own agents never write one; an agent that genuinely understands the system may draft, and the document names its drafter. Agents produce the dated traces behind it and contradict it with them.
  They do not edit it.

So, stated for an invocation:

- **Read freely.** Any session may read and grep it — as a strong prior, not ground truth, and weigh the age.
- **`pickup` on the way in, `context-dump` on the way out**, and a handoff writes the next orientation.
- **Two agents write, each one class of document and nothing else.** A `curator` regenerates the
  shared surfaces no thread owns — the index, the conventions file, the memory pointer — and repairs
  links that cross threads. A `tracer`, dispatched by `context-dump`, creates one `reference/` trace
  for one external source it re-opened itself, and refuses rather than writing when it could not
  reach it. Neither commits; neither touches `architecture/`.
- **Nothing else writes**, and a session rooted in a code project is the one most likely to forget
  it — the vault is just another directory in that tree.

## 3. It is a different git repo

Via the symlink, `cd <project>/<vault> && git …` operates on **this** repo, not the project's. Convenient, and
a trap: a turn that touches code and docs leaves commits owed in two repos, and the knowledge-base ones are the
easy ones to forget. Commit here in the same turn you write.

**Never change HEAD in the vault checkout.** Every session in that tree shares it, so `git checkout -b` moves
HEAD for all of them and the next agent's commits land on your branch. Commit to the branch you found.

## 4. Search tools do not find it by default

Two independent blocks stack: `.git/info/exclude` hides it from anything honoring git ignore rules, **and** it is
a symlinked directory, which most walkers won't follow. Measured from a project root with the knowledge base
symlinked in:

| command | finds it? | why |
|---|---|---|
| `rg <pat>` | **no** | git exclude |
| `rg --no-ignore <pat>` | **no** | still a symlink |
| `rg --no-ignore --follow <pat>` | yes | both defeated |
| `rg <pat> <vault>/` | yes | explicit path arg overrides both |
| `grep -r` | **no** | `-r` doesn't follow symlinks |
| `grep -R` | yes | `-R` does |
| `find .` | **no** | needs `-L` |
| `find -L .` | yes | |

So an agent told to "search the codebase" will not see the knowledge base, and will not know it missed it.
**Name the path** — `rg 'encabulator' <vault>/` — rather than flipping `--follow` on globally. The default
exclusion is a feature: your notebook should not pollute code searches or land in a PR diff.

## 5. Project worktrees do not have the symlink

`git worktree add` produces a checkout with no untracked files, and the symlink is untracked by design. Measured:
**0 of 7** existing worktrees in a real project had it. A session in a worktree cannot see the knowledge base at
all — including the agent-created worktrees Claude Code uses.

Fix per worktree, with an absolute target since a worktree sits at a different depth and is disposable anyway:

```bash
ln -s ~/workspace/<vault> <vault>
```

If `git status` in that worktree then shows it untracked, add `/<vault>` to its exclude too.

## 6. Traps that are true on every thread, so they belong here and not in a live set

**Why this section exists, and it is a rule about orientations rather than about any one trap
below.** An item whose death condition reads `dies never` can never leave a thread's live set, so
it is the one class that only accumulates. Measured 2026-09-18: two unrelated threads in one vault
carried the **same 19** of these, at 24% and 42% of their live sets, retyped at every handoff.
**An item that cannot die is a convention, not thread state.** It goes here once and orientations
cite it. `lipika orientation-carry` separates them out at the handoff and exits 1 naming them.

`[DEAD END]` is the exception and stays in the thread: *do not re-propose this, **here***.

### The shell on this machine is zsh

- **`grep --include=*.md` fails** — zsh globs the pattern before grep sees it. Quote it.
- **`"$var:path"` silently applies a history modifier.** Write `"${var}:path"`.
- **Reading a tool's output through `tail` turns a refusal into an apparent success**, and `$?`
  after a pipeline reports the pipe's last command. `cmd > file; echo $?`.
- **Two `claude` binaries are on `PATH`** — `/opt/homebrew/bin/claude` and
  `~/.local/bin/claude`. Homebrew's wins by order. Print `claude --version` before believing
  anything about a CLI feature.

### Tools lie about themselves in specific, repeatable ways

- **`--help` can document a whole interface that invocation refuses.** Never conclude a CLI
  feature's availability from `--help`; invoke it. (And the inverse: `claude plugin eval`'s binary
  contains the string `count:`, which its grader loader rejects.)
- **A CLI measurement is about one host's installed binary, not about a feature.** `2.1.252`
  refused what `2.1.274` ran.
- **A failed setup command leaves a probe printing a clean-looking verdict.** Assert the setup
  landed before believing any measurement over it.
- **A proof can be corrupted into one that cannot fail, and it reads as a pass.** When a proof
  comes back green, confirm it *could* have failed.
- **A tool's verdict can be right while the sentence under it is wrong.** When a check prints
  advice, ask which client will read it.

### Writing and committing

- **The `Edit` tool needs its own `Read`.** A slice read through `Bash` does not satisfy the guard.
- **A new dump or orientation must sort last by name**, or `pickup` never reads it.
  `lipika stamp --for <dir>`; if it refuses, wait. Never invent a later name.
- **`lipika vault-commit` requires `-m` and refuses a subject over 72 characters** — and it
  refuses *after* the whole message is written. Count first.
- **Never change HEAD in the vault checkout.** It is shared, so a branch moves it for every
  session in the tree. This does **not** extend to the Lipika checkout, where local `main` was
  ruled correct 2026-08-27.
- **Editing one hard-wrapped paragraph pushes the overflow down it one line at a time.** Rewrap
  the whole paragraph in one edit, and count **characters**, not bytes.

### Agents and trees

- **A sub-agent inherits your cwd while every tool resolves the *configured* vault.** Dispatching
  from a worktree makes a pass read one tree and index another.
- **A tree at an unexpected commit computes a delta that still looks clean.** Check
  `git rev-parse HEAD` against the base ref before trusting a diff.
- **A loop step only a human can perform stalls the loop silently.** That is why the restart ends
  the session rather than sitting inside it.

## 7. Running the eval suite

Also true on every thread, so also not live items. `claude plugin eval` shipped in `v2.1.269`;
everything below was measured on `2.1.274`.

### The run is not you

- **The child agent gets a sealed `HOME`**, so the OAuth credential in your keychain is
  unreachable and the run exits `Not logged in`. The **judge** calls run in the parent process, in
  your environment, so they authenticate and bill normally — a run can cost real money and score
  0.00 with every judge voting FAIL against a workspace no agent ever wrote to.
- **An environment variable survives the `HOME` swap**, so a key reaches the child where OAuth
  cannot. Pass it **per command**, never `export` it: the CLI selects one *active credential*, so
  an ambient `ANTHROPIC_API_KEY` can displace OAuth for every interactive session in that shell and
  move subscription usage to API billing with nothing announcing it.

  ```bash
  ANTHROPIC_API_KEY=$(security find-generic-password -s anthropic-eval-key -w) \
    claude plugin eval . --case <name> --scaffold \
    --allow-tools Bash Write Edit Task --trust-plugin --ablation none --runs 1 --keep-temp
  ```

- **`--scaffold` is off by default.** Without it the workspace is empty, the seeded vault never
  exists, and every `file_exists` grader fails for a reason that has nothing to do with the change.
- **The tool grants are separate from the case's `allowed_tools`.** The case declares what a run
  *may* use; `--allow-tools` is you saying yes. A grader needing an ungranted tool is reported at
  load, above the score, where it reads as a warning.

### Reading the result

- **A grader skipped for the cost ceiling is scored as a FAILURE**, so the headline understates a
  change that was never measured. Read the per-grader lines; never the score alone.
- **The runner can contradict itself**: three graders printing `skipped: cost ceiling` under a
  summary printing `nothing was skipped`. The per-grader lines are the truthful ones.
- **`--max-cost-usd` is checked before a run launches, not during one**, so a single run overruns
  by its whole cost. $2 capped, $2.13 spent.
- **Exit 1 means "below threshold" OR "a case file failed to load".** Read stderr, not `$?`.
- **Without `--keep-temp` the trace is deleted**, including on a run whose score you then have to
  explain. `tracePath` in `aggregate-result.json` will point at a path that no longer exists.
- **A judged grader passes vacuously on an empty workspace.** Every case needs a free
  `file_exists` guard proving the run produced anything at all.

### Writing a grader

- **A grader takes `type`, `weight`, `arm` and its own type's options, and nothing else.** An
  unknown key rejects the **whole case file**, not the one grader. Vault document frontmatter is
  rejected outright, and `type:` means the grader *mechanism* here — `regex | tool_order |
  tool_used | file_exists | llm | baseline` — not the vault's document class.
- `tool_used` takes `tool:`. `tool_order` takes `before:` and `after:`. `file_exists` takes
  `path:`. `llm` takes `focus:`. **`count:` is in the binary's strings and is rejected by the
  loader.**
- **For a `type: llm` grader the file body IS the criteria**, handed to a judge verbatim — so a
  rubric may contain nothing addressed to a human that a judge would read as an instruction.
- **Cost, for sizing.** One 39-turn run of a handoff-shaped case: **$2.13**. The default is 3 runs
  per case plus a no-plugin baseline arm, so a two-case suite at defaults is ~$13 plus judges. A
  failing change does not need three samples: `--runs 1 --ablation none` until it passes once.
