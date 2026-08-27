# Lipika — the machinery that operates a knowledge-base vault

**This repo is a tool, not a vault.** It holds the two capture skills, the agent definitions and the
tools that maintain an external Obsidian-vault-plus-git-repo of long-form engineering docs. The vault
lives somewhere else and is named in config; nothing here hardcodes a path to one.

*Lipika* — Blavatsky's celestial scribes, who inscribe the Akashic records. The vault is the record;
this is the scribe.

**You are almost certainly here to change the machinery, not to use it.** Using it is two skills —
`pickup` and `context-dump` — and they explain themselves. What follows is how to develop them.

**Start with `pickup` anyway.** The record of how this machinery got here lives in the vault, not in this
repo, and a session rooted here does not load the vault's conventions. `pickup` reads the one document
that says where the work is and what needs deciding, and it costs a single read.

**What runs on this machine is the INSTALLED PLUGIN VERSION, not the checked-out branch.** Lipika
installs as a plugin, and the installed copy is a versioned snapshot taken at deploy time. So editing
the tree — or switching branches — changes nothing until you run step 4 of the loop below. Two
consequences: "which definitions are in force" is a version number you can print rather than a fact
about your git state, and an unmerged branch is not silently live **in a client that reads the
snapshot**.

**That second one is narrower than it was written, measured 2026-08-27.** This marketplace is a
`directory` source whose `installLocation` is this checkout, and a fresh `claude -p` subprocess loads
its definitions from **there** — measured three times, from two working directories — while the app
session that spawned it read a cache snapshot. So for a CLI process the tree *is* live, uncommitted
edits included, which is the property the plugin install was adopted to remove. `lipika doctor` now
prints the source and its path rather than leaving it to be assumed.

This replaced hand-made symlinks from `~/.claude/` into the working tree, which had the opposite
properties: a `git checkout` changed the definitions everywhere including in open sessions, and an
edit through a link might never load at all.

## What the machinery believes

One rule, and everything else follows from it: **every document in the vault is a record or a view.**

- **A record is never edited.** Dumps, `reference/` traces, `sources/`, `external/`, and every
  orientation already written. A record is corrected by a newer document, never by a change to it.
  **A wikilink is an address, not a claim** — repointing one when its target is renamed preserves
  everything the document says, so a record's links may be repaired. Do it with
  `lipika obsidian rename`, which moves the links as part of the operation; the rule is "use the tool
  that cannot leave them stale", not "rename and then go check".
- **A view is regenerated wholesale, never patched.** Each thread's current orientation, and the vault
  index. Safe to rewrite from scratch precisely because the records behind it are intact.
- **`architecture/` is the owner's judgement, and that is a rule about provenance, not about agents.**
  **Lipika's own agents never write one** — they read documents, not systems, so what they would
  produce is a confident summary of the vault rather than of the thing it describes. **An agent with
  real accumulated understanding of the system being described may draft one**, and often is the best
  placed to; it becomes an `architecture/` document when the owner has reviewed it, and it **names who
  drafted it** so a later reader can weigh it. Either way, agents produce the dated traces behind it
  and contradict it with them. Narrowed 2026-08-24: the old wording said *no agent writes one*, which
  blocked distilling an agent that genuinely understood a codebase, and had to be overridden.
- **`epics/` and `grand-plans/` are the owner's prose, not the owner's files.** An epic *cites* its
  threads, and which threads exist is mechanical — an agent may maintain the citation list, and should.
  The framing, the judgement and whether an effort is parked stay the owner's.

The design, with the forces and the falsifiers: `design/vault-and-agent-ontology.md`. Its §8 is the list
of what this system used to do and why each piece is gone — **read it before re-proposing anything**,
because most obvious ideas here have already been built, measured and retired.

## Layout

```
agents/       role definitions — flat .md, because the registry reads *.md and a directory stops registering
skills/       pickup and context-dump; SKILL.md is read from disk at invocation, so edits take effect at once
tools/        runnable python; every one resolves the vault rather than assuming cwd
design/       this machinery's own design docs — the ontology, the eval method, the gotchas
templates/    what a new vault is seeded from, `.template` suffixed
ai_docs/      symlink to the vault this is developed against. Local, gitignored
```

## Reaching the vault from here

**Never write a path to it.** `vault_config` resolves it — flag, then `$LIPIKA_VAULT`, then
`~/.config/lipika/config.json`, then the checkout — and it **refuses rather than guessing**, because a
tool that guesses its target curates the wrong tree and reports success. It returns a `Vault`, whose
existence is the proof it is one; `.path` is the string.

```bash
cd "$(lipika vault-config path)"     # every tool takes --vault as an override
lipika vault-config show
lipika doctor                        # is everything wired
```

**Call every tool by name — `lipika <command>`.** A plugin's `bin/` is on `PATH`;
`${CLAUDE_PLUGIN_ROOT}` is **empty** in a subagent's shell, measured, so a definition that interpolates
a path fails at its first call in the role least able to explain why.

**The vault is this project's own memory too**, and the machinery's own record lives in it. Read it as a
strong prior, not ground truth, and **weigh the age** — a figure from today has not had time to drift.

**Write into it only through the skills.** `pickup` on the way in, `context-dump` on the way out. Editing
vault documents by hand from a session rooted here is easy, because the vault looks like just another
directory in this tree, and it is how a record stops being evidence of a moment.

## Developing the machinery

**There is exactly one copy of every file here.** This repo used to be a template that a vault copied,
and every change ran a four-step port loop. That loop is gone. If you find yourself substituting a
placeholder or diffing two copies of a definition, something has regressed.

**The one-copy rule is about identity, not directories.** A vault must not hold a *copy of this
repo's* machinery — that is the whole of it. A vault may hold **its own** `tools/` and **its own**
`skills/`, written by its agents in the course of the work, and they are corpus rather than
machinery. The test when deciding whether something in a vault should be deleted is *"is this a copy
of something in Lipika?"*, never *"is it in a directory called `skills/`?"* Ruled 2026-08-21, after
the directory-shaped version of the rule nearly deleted a vault's own `pr-description` skill.

**Every change here lands through a pull request, and it is SQUASHED by the owner** — `main` is
protected, so nothing else can land one. A squash leaves the checkout *diverged*, not behind, and the
deploy reads the checkout, so realign before the next one:

```bash
git diff --stat main origin/main    # must be EMPTY
git reset --hard origin/main
```

A definition
is a system prompt paid on every invocation and re-read by nobody, so the PR body is the only durable
record of *why* it changed — and a change whose reasoning lives only in a session transcript is a
change the next author will undo. **A PR here is a record more than a gate** — you are usually the
only reviewer — but it is no longer *also* live: since what runs is the installed version, an open
branch affects nothing until it is deployed. Land it or close it anyway; three stacked PRs sat open
for three days and made `main` a fiction.

**The loop, and it is a loop:**

1. **Write the graders first.** State what the new version must do, as statements that can be
   *wrong*, and **commit them before the change**. This is the TDD edge: the grader is the test. One
   written afterwards silently agrees with whatever happened — measured, twice.

   *Grader* is `claude plugin eval`'s word for exactly this, so it is ours. Until that tool is
   ungated — it prints *"currently in early access"* on `2.1.241`, checked 2026-08-24 — graders are
   prose in the vault's `sources/evals/` and a human scores them. When it opens they become
   `evals/<case>/graders/*.md` and score themselves. **The name changed to match the tooling we are
   heading for; the rule did not.**
2. **Author here**, once.
3. **DEPLOY, if the change ships anything — before the dump, not after.** A change under `skills/`,
   `agents/`, `tools/` or `bin/` is carried by the plugin, and **editing the tree changes nothing
   about what runs** — the installed copy is frozen at its version. A change to `CLAUDE.md`,
   `design/` or `README.md` ships nothing and needs no deploy: those are read from the checkout. When
   in doubt, deploy; it is cheap and a missed one is silent. Bump the version in **both**
   `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, commit, then:

   ```bash
   claude plugin marketplace update lipika
   claude plugin update lipika@lipika        # prints the old -> new version
   claude plugin tag .                       # validates the two manifests agree; refuses if uncommitted
   ```

   **Same version is a silent no-op** from `update`, from `install`, and from `marketplace update` —
   measured 2026-08-24, all three. If the version did not change, nothing was deployed and you are
   about to measure the previous round.
4. **Dump.** It comes *after* the deploy so it can state the version that is actually installed, and
   *before* anything measures, because it is what a cold agent reads — measuring against a tree the
   handoff has not been written into measures the wrong thing.
5. **Ask for a restart, and END THE SESSION HERE.** `plugin update` says it itself: *"Restart to
   apply changes."* The deployed version is on disk and the running process has not read it —
   measured 2026-08-24, when a session that had just deployed `0.2.1` went on loading a skill from
   the `0.2.0` directory.

   **This is a handoff, not a pause.** The agent running the loop cannot restart, cannot detect a
   restart, and cannot proceed without one — so a round that treats it as an internal step stalls
   there silently. Your last message names what the next session must run: the graders, by path.

   **A `claude -p` subprocess is the one way to keep looping without a restart, and it measures a
   different thing.** It is a fresh process, so it loads current definitions — but from the
   *checkout*, per the directory source above, not from the deployed snapshot. That makes it good for
   iterating and **wrong as a substitute for the gate**: it would run an undeployed edit and report
   nothing amiss. Pass it the handoff prompt verbatim on **stdin**, and require the two things a
   caller cannot otherwise see:

   ```bash
   { cat handoff.txt; echo; echo "Report the pickup skill's Base directory first, then the verbatim output of the gate command."; } \
     | claude -p --allowedTools Bash Read Grep Glob Skill
   ```

   Ask for the **base directory** and the **verbatim gate output**, in that order, or the reply is a
   summary of a measurement rather than the measurement. Without `--allowedTools` it stops at the
   first permission prompt and reports the gate as "queued"; with the prompt passed as an argument
   after `--allowedTools` it is swallowed and `claude` exits saying no input was given. Both measured
   2026-08-27.

   **Do not compose that message by hand.** `context-dump`'s step 7 prints it, from
   `lipika handoff-prompt <workstream>` — the installed version, that version's gate command, and
   every grader whose `up:` names the thread, already fenced for pasting. It **refuses**, exit 3,
   when the tree is not what is installed: a warning above a pasteable block is read past, and the
   paste is what survives. A refusal means the deploy did not happen and there is no handoff to
   write yet.

   *— everything below happens in the NEW session —*

6. **GATE: prove the installed plugin IS the tree, or the eval is worthless.** This is the point of
   the loop — a measurement of a stale copy measures the previous round and reports clean.

   ```bash
   lipika doctor
   ```

   A `STALE` or `MISSING` line about the installed plugin means **stop and deploy** (step 3) before
   measuring anything. It compares all four shipped paths, not just `skills` — an agent definition
   drifts as silently as a skill — and it **names the checkout it compared against**, which is the
   part you have to read.

   It also names **where definitions are read from** — the marketplace source kind and its
   `installLocation`, read from `known_marketplaces.json` rather than assumed. A green comparison is
   exactly when that gets misread: two folders being equal is a fact about files, not about which
   copy the process in front of you loaded. That line never changes the exit code, because a
   directory source is a deliberate setup and not a fault.

   **This was a `diff -rq` loop pasted into the session, and the loop was the defect.** Its relative
   `$d` form compared whatever directory the session happened to open in, which in a foreign checkout
   produced a *plausible* staleness finding rather than an obvious error. Its absolute form then
   compared the installed snapshot against itself — the tool composing it worked out "the tree" as its
   own directory, so both paths named one folder and nothing could fail. Two shapes of the same
   mistake in two rounds; the comparison lives in one place now, with an exit code.

   `doctor` refuses rather than reporting green when it cannot find a checkout — in a shell where
   `lipika` is the installed snapshot and nothing else is reachable, pass `--tree <checkout>`.
7. **PROBE.** Ask a question the two versions answer *differently* and read what the role **did**, not
   what it says about itself — one asked to quote its own definition returned a rule that has never
   existed in any version of the file, in any repo. The gate above proves the *files* are current;
   the probe proves the *running session* has read them, which a restart is required for and
   `claude plugin list` does not tell you.
8. **Then curator, then eval**, scored against the graders verbatim.
9. **Summarise the round where the next agent will read it**, and feed the findings back. That return
   edge is the difference between a design that stays true and one that becomes aspirational.

**Why a deploy step at all — this replaced a superstition.** The rule here used to be *wait 15
minutes, or start a fresh session*, on the belief that a definition edit is "served stale". The
documentation says close to the opposite: Claude Code **watches** `~/.claude/agents/` and
`.claude/agents/` and loads edits within seconds, skills have documented live change detection, and
restart is documented as necessary only for an `agents/` directory absent at session start,
`--add-dir` directories, and `--disable-slash-commands`. That wrong rule cost three days of a round
going unmeasured, because it asked for a fresh session and nothing asked any human to open one.

What was actually measured was narrower: an edit reached through a **symlink** had not loaded at +15
minutes — one observation of a lower bound, not a duration, and consistent with a watcher registered
on the link that never fires when only the target changes. That would make the staleness **unbounded**.
Prompt caching is not the mechanism; it keys on the exact prefix, so changed text is a cache *miss*
and the new text runs.

**Installing as a plugin dissolves the question instead of managing it.** The installed copy is a
`view` in this repo's own sense — regenerated wholesale by step 4, never edited — and each round
leaves a distinct, inspectable, versioned directory. "Which version is live" stops being unknowable
and becomes a number you can print. It also makes this machine match what anyone else installing
Lipika runs, which the symlinks never did.

**The one way this fails is forgetting step 3**, which silently measures the previous round. Unlike the
symlink failure it is *detectable*, and `lipika doctor` now detects it rather than this paragraph
asking you to remember — that is what step 6 runs. It took two rounds to get right: the check shipped
in `0.3.0` comparing the installed copy against its own directory, which cannot fail, and `0.3.1`
made the second operand a checkout found by measurement and printed alongside the verdict.

**Why the restart ends the session rather than sitting inside the loop.** Measured 2026-08-24 by
running the loop on itself: the agent executing it cannot restart, cannot detect a restart, and
cannot proceed without one. A step only a human can perform, buried mid-loop, stalls there and
nothing says so — which is exactly how the rule this replaced cost three days. Putting it at the
boundary makes the stall impossible: the round *ends*, with an explicit ask, the way a handoff does.

**Never eval the version you are replacing.** It measures a system being deleted — retired as an idea
2026-08-21, and it is the shape a "let us get a baseline first" instinct takes.

`design/agent-eval-method.md` is the procedure in full. Read it before you touch a definition.

**`lipika recall-check <pre-change-ref> <path>` proves a rewrite dropped no rule — provisionally.**
It is a **bridge, not settled machinery**: it verifies *text* where a grader verifies *behaviour*, and
a dropped rule that changes nothing matters less than a kept rule nobody follows. Its record is thin —
9 flags and 1 real drop restored in one round, 6 runs and 1 real catch in another — and nothing
invokes it automatically, so it fires only when someone remembers. **Dies when behavioural graders run
against definitions.** Do not extend it in the meantime. Its subject is a
definition here, not a vault document — nothing in the vault is edited, so nothing there needs it. **It
is not the way to check a deliberate deletion**: a pass whose purpose is removing rules flags every one
of them, and judging a hundred intended retirements in writing is a great deal of work for no signal.
There, the deletions are the deliverable and `git diff` is the record.

**Prefer a tool that refuses to prose that asks.** A rule in a definition gets read past; the same rule
with an exit code fails loudly. A definition is also a system prompt paid on every invocation, so the
tool is the cheaper end too. **Give every new check a hand-audited red case and a green case** — a check
that stays red on correct content gets dismissed, and one that stays green on a real fault is worse.

## Landmines

- **Editing the tree deploys nothing, and at an unchanged version every command is a silent no-op.**
  `install`, `update` and `marketplace update` all report success and copy nothing when the version
  matches — measured 2026-08-24, all three. Bump both manifests or you will measure the previous
  round. This replaced the older hazard, which was worse: definitions reached through a symlink where
  an edit to the link's *target* might never load at all, unbounded rather than timed.
- **A new skill or agent needs a DEPLOY, not a symlink.** The plugin carries everything under
  `skills/` and `agents/`, so adding one is just adding the file and running step 4 of the loop. There
  is nothing to wire per definition and nothing to remember to delete. If you find yourself hand-making
  a link in `~/.claude/`, you have created a second wiring path that will disagree with the installed
  copy the first time the tree changes without a redeploy.
- **A sub-agent in an unexpected tree reports clean.** A tree at a different commit still computes a
  delta that still looks clean. Every sub-agent given a base ref checks `git rev-parse HEAD` against it
  first, and **no agent in a shared checkout ever changes HEAD** — creating a branch moves it for every
  session in that tree.
- **A sub-agent inherits your cwd while every tool resolves the *configured* vault.** Dispatching from a
  worktree makes a pass read one tree and index another.
- **The `Edit` tool needs its own `Read`.** A slice read through Bash does not satisfy the guard.

- Everything else that bites, measured: `design/GOTCHAS.md`.

## Voice

Terse and factual, for a first-time reader. No agent-local codenames — say what a thing *is*, not the
label it got mid-session. **Harder for anything that leaves the conversation** — PR bodies, commit
messages and review replies carry the salient facts and none of the conversational frame. Commit subjects
under 72 characters, and end messages with:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```
