---
type: reference
status: reference
tags: [vault, meta, design, retired]
---

# Retired mechanisms

What this machinery once did and dropped, and why. Read it before a major change to the vault's shape,
so the change does not rebuild one of these. Each was a correct answer to a problem the current design
removes, or a mechanism measured and dropped. The design itself is `vault-and-agent-ontology.md`.

| retired | what it did | why it is gone |
|---|---|---|
| the task frontier and parent register | mutable, authoritative state per thread | mutable and authoritative; see `vault-and-agent-ontology.md` §3 |
| the `frontier-clerk` | reconciled a register against dumps | there is no register |
| the `librarian` | consolidated, merged, archived and closed on its own judgement | records are never consolidated; archiving needs the owner's ruling |
| `frontier_slice` | read a register without its prose | nothing edits a register surgically |
| `marker_licence_check` | caught an edit claiming more than its evidence | dispositions state their basis |
| `frontier_lag_check` | had the register fallen behind its dumps | the newest document is the state |
| `budget_check` and byte budgets | bounded an accumulating document | threads are kept small; a regenerated view cannot accumulate |
| `orientation_check`, `closure_check` | pulled warnings into a new task; decided a task was finished | no task tier; `orientation-audit` replaces both at pickup |
| the task tier, `done/`, `historical/`, carry-across | partitioned an accumulating register | splitting a thread |
| *never infer completion; a marker is the only authority* | stopped an agent upgrading an item without evidence | it made closure impossible; replaced by stating the basis |
| *one marker per separately-statused fact* | stopped a composite marker collapsing distinctions | compensated for downstream mechanical action that no longer exists |
| the clean-tree halt | protected a losslessness guarantee | the guarantee is gone; the pathspec protects a commit |
| the write-authority partition | kept parallel agents off each other's files | the pass log answers concurrency |
| worktree isolation | a tree per agent | its defects were tools answering about the wrong tree; the clobbers it targeted were bare commits, which a pathspec prevents |
| the epic tier, `epics/` | grouped a project's threads | `from:` already records which threads are one project; a hand-kept list went stale |
| `up:` frontmatter | named a document's parent | nothing read it, and most values restated the folder path |
| `about:` frontmatter | named the thread a document concerns | nothing read it once `handoff-prompt` stopped; graders are not tied to threads |
| the `scout` | found related threads in the background | `spin-out` reads them inline, with the parent's context |
| warning recall by search at read time | found other threads' warnings when someone looked | pull cannot fire when nobody asks; prior art is pushed at the split |
| machinery copied into each vault, and port tooling | kept N copies in step | one copy, installed as a plugin |
| blocked parent time as a cost | ranked the largest problem | it cost nothing: no tokens, children working throughout |
| a "turns that thought and called nothing" signal | flagged idle deliberation | the harness emits reasoning in its own message, so it counted every deliberation |
| loop detectors and scoring over reasoning | classified thrashing | the need was a read, not a classifier |
| banning mutable measurements | kept figures out of documents | dating them is the fix |
| a `.locked` suffix while working | marked a file in use | breaks links, Obsidian and git paths; a crash leaves it locked |
| a status or lock file beside the pass log | a second concurrency store | one store with a derived projection |
| git tags as pass baselines | one global name per scope | could say neither when a pass ran nor that two agents overlapped |
