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

## 2. Reads are free; writes go through the two skills

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
  Nothing else writes.

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
