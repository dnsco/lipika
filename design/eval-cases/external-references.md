# The `external-references` case — why it exists, and what it cannot see

Not read at run time. The runnable half is `evals/external-references/`; this holds the
measurements it was built from. Running and writing graders: `design/agent-eval-method.md`,
*Graders*.

## What it measures

A session works a question whose evidence is **outside every repo it can read** — a docs site, a
Slack argument, a Notion page named as source of record, vendor pages — reaches a conclusion, and
dumps. The case checks that each reference lands as **one dated trace per subject** under the
thread's `reference/`, carries its substance when it is mutable, and that what was cited but never
opened has its own list.

## The two defects behind it

**No destination, 2026-09-16** (`workstreams/2026-09-16-can-agentomatic-host-workloads/`):

- Five dumps and three orientations written from a docs site, a gist, thirteen Slack messages and
  two vendor pages named **none of them** until the owner asked.
- Asked, the session wrote the right content into `dumps/`, typed `type: reference`. The dumps that
  rested on it still cited nothing.
- Vault-wide, `reference/` had fired in 2 of 14 threads; no step of `context-dump` pointed at it.

"Write down the sources" has a default destination, and it is `dumps/`.

**No unit, 2026-09-17**, on the fix (`0.3.6`): one aggregate per thread put forty references into
401 lines, 121 of them an index restating URLs so `reference-check` would exit 0. Correcting one
reference rewrites forty. Same class, one level in.

## Vocabulary

**Reference**, never *source* — `sources/` at vault root means frozen eval measurements.

## What no grader here can see

- **An unprompted citation.** The case is one turn, so every dump is unprompted — but the owner's
  real sequence was two (*"Dump the sources too"*, after which the artefact still went to the wrong
  place). Covering that needs a second case with a `history_file`.
- **Whether a later `pickup` surfaces the unopened list.** Needs a second session.
- **What the session read and did not write down.** A clean exit is not a clean bill.

The graders were hand-scored prose until 2026-09-24; their provenance is in git at `d89cf76`.
