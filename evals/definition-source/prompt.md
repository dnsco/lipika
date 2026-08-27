# Case — the gate compares two folders and never says which one a session will read

`doctor` proves the installed snapshot equals the checkout. That is a fact about **files**. It says
nothing about which copy a *running* session loads its definitions from, and on this machine the two
answers differ by client.

Measured 2026-08-27, twice, from two different working directories: a fresh `claude -p` subprocess
reported its `pickup` base directory as `/Users/dennis.collinson/workspace/lipika/skills/pickup` — the
**checkout**. The app session that spawned it reported
`~/.claude/plugins/cache/lipika/lipika/0.3.2/skills/pickup` — a **cache snapshot**, and one already
marked `.orphaned_at`.

The cause is in `~/.claude/plugins/known_marketplaces.json`: lipika's source is `directory` and its
`installLocation` is the working tree itself, not a copy under `marketplaces/`.

## What this case exists to catch

`CLAUDE.md` states that what runs is the installed version rather than the checked-out branch, with
the stated payoff that *"an unmerged branch is no longer silently live."* For a CLI subprocess on this
machine that is false: it reads the tree, so an uncommitted edit is live and a branch switch changes
definitions everywhere.

That property is the reason the plugin install replaced the hand-made symlinks. A gate that reports
green while it holds only for one of two clients is the same class as a comparison of a copy against
itself: **true about what it measured, and read as a claim about something else.**
