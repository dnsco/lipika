# Lipika

Agents and tools that maintain a **knowledge-base vault** — an Obsidian-vault-plus-git-repo of dated,
long-form engineering docs that Claude Code sessions write to and read back, so context outlives the
session that produced it. One vault spans every project you work in.

*Lipika* — the celestial scribes who inscribe the Akashic records. The vault is the record; this is the
scribe.

**This repo is not a vault.** It holds the machinery; the vault lives wherever you keep it and is named
in config. Nothing here hardcodes a path to one.

## Install

```bash
/plugin marketplace add dnsco/lipika
/plugin install lipika
```

Then tell it where your vault is:

```bash
mkdir -p ~/.config/lipika && cat > ~/.config/lipika/config.json <<'JSON'
{
  "default": "notes",
  "vaults": { "notes": "/absolute/path/to/your/vault" }
}
JSON
lipika vault-config show
```

The config also carries the thresholds the tools enforce — size budgets, per-role time budgets, which
directories are append-only — so a number has one home instead of being restated in prose that goes
stale. Every command resolves the vault the same way: `--vault`, then `$LIPIKA_VAULT`, then the config,
then the checkout you are standing in. **A command that cannot resolve a vault refuses rather than
guessing**, because a tool that guesses its target curates the wrong tree and reports success.

`lipika doctor` says whether the wiring is intact — the two halves resolve differently, so it checks them
separately.

## Set up a vault

A vault is a git repo of markdown, readable as an Obsidian vault. It needs one document at its root saying how
its documents are placed, named and maintained. One command seeds all of it and registers the vault:

```bash
lipika init /path/to/your/vault          # --name KEY, --default, --no-git
```

It creates the tier directories, copies both templates, writes the config entry and runs `doctor`. Re-running is
safe: anything already there is kept, never overwritten, which is also how an older vault picks up an entry it
is missing. What it copies:

```
templates/vault-CLAUDE.md.template  ->  <vault>/CLAUDE.md
templates/vault-gitignore.template  ->  <vault>/.gitignore
```

That template carries the **corpus half** — placement, filenames, frontmatter, voice, and what the byte budgets
are for. It points here for the machinery half and for every threshold's value, because a rule restated in two
places diverges and a number restated in prose goes stale while a tool enforces something else.

A vault's copy diverges on purpose: it should name your real repos, your dated evidence, your concrete shas.
**Edit the template here; never port a copy back.**

The `.gitignore` earns its own template because three of its entries are load-bearing rather than tidy. The
pass log is appended concurrently by every role, so tracking it makes each pair of parallel passes a merge
conflict. `.lipika/` holds agent-to-agent reports, which are machinery
state rather than corpus. And agent worktrees get provisioned inside the vault, so a tracked one nests the repo
in itself and a recursive grep from the root double-counts every hit. All three are `.gitignore` rather than
`.git/info/exclude` precisely because exclude does not survive a clone.

## Records and views

One rule shapes everything: **every document is a record or a view.** A record — a dump, a dated trace, a
source, an orientation already written — is **never edited**; it is corrected by a newer document. A view —
the current orientation, the vault index — is **regenerated wholesale, never patched**, which is safe
precisely because the records behind it are intact. `architecture/` is the third case: a long-lived edited
view, and the owner's alone, because one written by an agent becomes the most-linked document in the
vault with nothing positioned to contradict it.

Removing the class of document that was mutable *and* authoritative is what retired seven tools, two roles
and the whole task tier. `design/retired.md` records each one and why.

## The two skills, and the two roles

| | when | what it does |
|---|---|---|
| **`pickup`** (skill) | session start | reads the current orientation, audits it against the last one, opens with what needs the owner, enters plan mode |
| **`context-dump`** (skill) | learned something, or ending | one dated dump — and at a handoff, a new dated orientation |
| **`curator`** | the index has drifted | regenerates the index, repairs links crossing threads, owns the shared surfaces |
| **`spin-out`** (skill) | the question changed | opens a new thread from its parent, carries what bears on it, reads its prior art, and ends as its first pickup |

The skills run in the main loop, where the context already is. The curator acts and then reports a change
list with a reversal per entry, rather than asking first — detect-propose-execute-on-approval produced
zero proposals in two separate homes.

## The tools

```bash
lipika                                  # every command, with what it does
lipika orientation-audit <workstream>   # did the newest orientation account for the last one?
lipika architecture-candidates          # traces cited across threads with no architecture document
lipika pass-log active                  # who else is working in this vault right now
lipika recall-check <ref> <path>        # did a rewrite of a DEFINITION drop a rule?
```

They are reached by name because a plugin's `bin/` is on `PATH`. `${CLAUDE_PLUGIN_ROOT}` is **not**
populated in a subagent's shell — measured — so no definition here interpolates a path.

## Changing a role

One copy of every definition, skill and tool exists, so authoring is the whole of it. The loop:

**author here → probe behaviourally → try it on real work → profile it → summarise the round where the next
agent will read it → feed the findings back.** That last edge is what makes it a loop.

Probe by asking a question the old and new text answer *differently* — never by asking a role to quote its
own definition, which one did, returning a rule that has never existed in any version of the file.
`lipika recall-check` proves a rewrite dropped no rule, and its subject is a definition here rather than a
vault document. It is **not** the way to check a deliberate deletion: a pass whose purpose is removing
rules flags every one, and the deletions are the deliverable.

Two things bite immediately. **A definition change is served stale for minutes** and the agent registry caches at
session start, so probe with a question the old and new text answer differently before trusting any measurement —
`SKILL.md` is exempt, being read from disk at invocation. And **`${CLAUDE_PLUGIN_ROOT}` is empty in a subagent's
shell**, measured, so no definition may interpolate a path; that is why tools are called by name.

`CLAUDE.md` here is the working guide for this repo. `design/` carries its own documents:
`vault-and-agent-ontology.md` (the shape, the forces, and what would falsify each invariant),
`agent-eval-method.md` (how a role gets changed and measured — read it before touching a definition),
`GOTCHAS.md` (what bites, all of it measured).
