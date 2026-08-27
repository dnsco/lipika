---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-08-27
case: definition-source
---

# D2 — the STALE line's advice matches the client that will read it

**Written and committed BEFORE the change.**

## The change under test

`tools/doctor.py:96` prints, under every `STALE`, *"what runs is the installed copy, so these edits
are not live."* That is true for a client reading the cache snapshot and **false** for one reading a
`directory` source's `installLocation`, which is the working tree.

Measured 2026-08-27: a `claude -p` subprocess whose `pickup` base directory was the checkout printed
that exact sentence about its own uncommitted edits, which were live for it. The verdict was correct;
the advice inverted the risk.

- **PASS** — when the definitions source is a `directory` whose `installLocation` is the tree being
  compared, the STALE advice says the edits **are** live for a process reading it, and that deploying
  is what makes the snapshot agree — not what makes the edits take effect.
- **PASS** — when it is not, the original wording is unchanged. This is a narrowing, and a fix that
  rewrites the common case to cover the rare one has made the common case wrong.
- **PASS** — the STALE verdict and the exit code are untouched. The snapshot is behind either way,
  and other clients read it.
- **FAIL if** the advice is hedged into covering both — *"these edits may or may not be live"*. A
  sentence a reader cannot act on is the failure this replaces, not a safer version of it.
- **FAIL if** it decides from the tree's path, the repo's name, or anything but the marketplace
  entry. Inference here is the ruled-out class, one level down.
- **FAIL if** `doctor` claims which copy the *reading* process loaded. It cannot know that. It knows
  what the configured source is, and that is the whole of the honest claim.

## What a suspicious result looks like

Clause 2 is the one that will go unexercised — this machine has only a `directory` source, so the
unchanged branch cannot be observed here. Read the code for it and say UNEXERCISED rather than
inventing a second marketplace.
