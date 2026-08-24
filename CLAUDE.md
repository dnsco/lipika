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

**Which branch is checked out here decides what every session on this machine runs.** `~/.claude/agents/`
and `~/.claude/skills/` symlink into this working tree, not into a commit — so a `git checkout` changes
the definitions in force everywhere, including for sessions already open, and an unmerged branch is fully
live. Know which branch you are on before you conclude anything about a role's behaviour.

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
- **`architecture/` is the owner's** — the one long-lived edited view. Agents produce the traces behind
  it and contradict it with them; they do not write it.
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

**Every change here lands through a pull request.** Nothing commits to `main` directly. A definition
is a system prompt paid on every invocation and re-read by nobody, so the PR body is the only durable
record of *why* it changed — and a change whose reasoning lives only in a session transcript is a
change the next author will undo. **A PR here is a record, not a gate**: `~/.claude/` symlinks into
the working tree, so an open PR's branch is already in force on this machine the moment it is
checked out. Land it or close it; never leave one open and checked out.

**The loop, and it is a loop:**

1. **Seal the key first.** Write what the new version must do, as statements that can be *wrong*,
   and **commit them before the change**. This is the TDD edge: the key is the test. A key written
   afterwards silently agrees with whatever happened — measured, twice.
2. **Author here**, once.
3. **Dump**, before anything measures. It is what a cold agent reads, so measuring against a tree the
   handoff has not been written into measures the wrong thing.
4. **PROBE BEFORE YOU MEASURE.** Ask a question the two versions answer *differently* and read what
   the role **did**, not what it says about itself — one asked to quote its own definition returned a
   rule that has never existed in any version of the file, in any repo. **Nothing reports which
   version of a definition is live**, so the probe is the only way to know, and it costs one question.
5. **Then curator, then eval**, scored against the sealed keys verbatim.
6. **Summarise the round where the next agent will read it**, and feed the findings back. That return
   edge is the difference between a design that stays true and one that becomes aspirational.

**On definitions going stale, corrected 2026-08-24.** Claude Code **watches** `~/.claude/agents/` and
`.claude/agents/` and loads edits within seconds; restart is documented as necessary only for an
`agents/` directory that did not exist at session start, `--add-dir` directories, and
`--disable-slash-commands`. Skills have documented live change detection. So the earlier rule here —
*wait 15 minutes, or start a fresh session* — was wrong, and it cost three days of a round not being
measured.

**What we actually measured is narrower and worse.** These definitions are reached through
**symlinks** into this working tree. Once, a symlink-target edit had not loaded at +15 minutes. The
plausible cause is a file watcher registered on the link that never fires when only the target
changes — which makes the staleness **unbounded rather than timed**. Prompt caching is not the
culprit: it keys on the exact prefix, so changed text is a cache miss and the *new* text runs.

Until the symlinks are gone, treat step 4 as mandatory rather than advisory.

**Never eval the version you are replacing.** It measures a system being deleted — retired as an idea
2026-08-21, and it is the shape a "let us get a baseline first" instinct takes.

`design/agent-eval-method.md` is the procedure in full. Read it before you touch a definition.

**`lipika recall-check <pre-change-ref> <path>` proves a rewrite dropped no rule.** Its subject is a
definition here, not a vault document — nothing in the vault is edited, so nothing there needs it. **It
is not the way to check a deliberate deletion**: a pass whose purpose is removing rules flags every one
of them, and judging a hundred intended retirements in writing is a great deal of work for no signal.
There, the deletions are the deliverable and `git diff` is the record.

**Prefer a tool that refuses to prose that asks.** A rule in a definition gets read past; the same rule
with an exit code fails loudly. A definition is also a system prompt paid on every invocation, so the
tool is the cheaper end too. **Give every new check a hand-audited red case and a green case** — a check
that stays red on correct content gets dismissed, and one that stays green on a real fault is worse.

## Landmines

- **A definition change reached through a SYMLINK may never load.** Claude Code watches
  `~/.claude/agents/` and loads edits within seconds — but ours are symlinks into this tree, and once a
  symlink-target edit had not loaded at +15 minutes. Suspected: a watcher on the link that never fires
  when only the target changes, which makes this unbounded rather than timed. **Probe before you
  profile**, because nothing reports which version is live. Corrected 2026-08-24; the old "stale for a
  few minutes" wording described a timer that does not exist.
- **A new skill needs a symlink.** `~/.claude/skills/<name> -> <repo>/skills/<name>`, or it never
  registers. Same for `~/.claude/agents/<name>.md`. Deleting a definition means deleting its symlink too.
- **A sub-agent in an unexpected tree reports clean.** A tree at a different commit still computes a
  delta that still looks clean. Every sub-agent given a base ref checks `git rev-parse HEAD` against it
  first, and **no agent in a shared checkout ever changes HEAD** — creating a branch moves it for every
  session in that tree.
- **A sub-agent inherits your cwd while every tool resolves the *configured* vault.** Dispatching from a
  worktree makes a pass read one tree and index another.
- **The `Edit` tool needs its own `Read`.** A slice read through Bash does not satisfy the guard.
- **`git push` over SSH fails here while `gh` is authenticated.** Push with
  `git -c credential.helper='!gh auth git-credential' push https://github.com/dnsco/lipika.git <branch>`.
- Everything else that bites, measured: `design/GOTCHAS.md`.

## Voice

Terse and factual, for a first-time reader. No agent-local codenames — say what a thing *is*, not the
label it got mid-session. **Harder for anything that leaves the conversation** — PR bodies, commit
messages and review replies carry the salient facts and none of the conversational frame. Commit subjects
under 72 characters, and end messages with:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```
