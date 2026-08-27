---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-08-27
case: definition-source
---

# D1 — the gate names where definitions are actually read from

**Written and committed BEFORE the change.**

## The change under test

`lipika doctor` compares the installed snapshot against the checkout and prints
`installed <v> IS <tree>`. It is being changed to also state **which copy a session loads definitions
from**, read from the marketplace entry rather than assumed.

- **PASS** — `doctor` names the marketplace `source` kind and its `installLocation`, as a path, from
  `known_marketplaces.json`. Read, not hardcoded.
- **PASS** — when `installLocation` is the checkout, it says so and says what follows: an
  uncommitted edit is live for any process that reads it, so a version number does not describe what
  runs.
- **PASS** — it is stated whether or not the file comparison passes. A green comparison is exactly
  when this is most misread.
- **FAIL if** the marketplace entry is absent or unreadable and `doctor` stays silent about it. An
  unstated source is the defect, not a clean run.
- **FAIL if** it claims which copy a *session* loaded. `doctor` is a separate process and cannot know
  that; the probe step does. Naming the configured source is the honest claim, and overreaching here
  rebuilds the thing this catches.
- **FAIL if** the new line changes `doctor`'s exit code on its own. A directory source is the owner's
  deliberate setup, not a fault, and turning a working configuration red trains the reader to ignore
  a red line.

## What a suspicious result looks like

Clause 1 is satisfied by printing any path and does not prove it came from the marketplace file —
read the code. Clause 2 will read green on this machine whatever is written, because the source *is*
a directory here; a machine with a `github` source would exercise the other branch and none is
available, so say UNEXERCISED rather than inventing one.
