# Case — a thread built on Slack threads and web pages, and no trace of either

The session under test works a question whose evidence is **outside every repo it can read**: a
rendered documentation site behind SSO, a Slack thread of a dozen messages, a gist, a Notion page
named as a programme's source of record, two vendor pages. It reaches conclusions from them and then
dumps.

## The prompt

> Work out whether <system> can host <workload>. The mandate is on the project site, there's a thread
> in #<channel> where the owners argued about it, and the proposal itself is in Notion. Dump when
> you've got something.

Then, in a later turn of the same session:

> Dump the sources too.

The second turn matters and is not a hint. It is the instruction the owner actually gave on
2026-09-16, and the run **still** put the artefact in the wrong place. A version that only behaves
when told the destination has not fixed anything.

## What this case exists to catch

Measured on `workstreams/2026-09-16-can-agentomatic-host-workloads/` in the vault at
`~/workspace/ai_docs`, 2026-09-16; the vault-wide counts were taken 2026-09-17.

- Five dumps and three orientations were written from a GitHub Pages site, a gist, thirteen Slack
  messages, a repo branch and two vendor pages. **Not one link appeared in any of them** until the
  owner asked — and he asked only after scanning the dumps and finding the references he had assumed
  would be there were absent.
- Asked directly, the session wrote `dumps/2026-09-16-222023-primary-sources.md`. Its content was
  right — read / cited-but-not-opened split, what each reference supplied, and the access route that
  actually works (*behind GitHub auth; clone `vlognow/core-platform-proj-management` instead*). Its
  **frontmatter types itself `type: reference`** while the file sits in `dumps/`.
- The four dumps that *rest on* those references still name none of them. The provenance is
  quarantined in one late document rather than being reachable from the claims it settles.
- Hours later the project was renamed and every URL moved. That break was only visible because by
  then the links existed to break.
- Vault-wide, `reference/` had fired in **2 of 14 threads**, 6 documents total. In
  `skills/context-dump/SKILL.md` the word `reference` appeared exactly twice: once in the list of
  things that are immutable, once as a line in the shape diagram. **No step pointed at it.**

**The failure is not that the agent was careless. It is that "write down the sources" has a default
destination, and the default is `dumps/`.** An instruction with no named destination gets obeyed into
the wrong folder, and the one artefact produced is then superseded by the next dump.

## Vocabulary this case uses

**Reference**, never *source*. `sources/` at vault root means frozen eval measurements, never edited.
A grader that says "source" is testing a word the change deliberately retired.
