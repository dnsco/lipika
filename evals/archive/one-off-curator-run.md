# One-off: the curator archives the vault's finished threads

Written 2026-09-24, before the run, so it can be wrong. Run after 0.6.0 is deployed and the session
restarted. A human asks; the curator proposes and moves.

1. Dispatch `lipika:curator`: "Which threads in this vault are finished? Propose; move nothing."
2. Put its proposal to the owner. Relay the rulings to the same curator with `SendMessage`.
3. It runs `lipika archive-thread` per ruled thread, commits, and regenerates the index.

## What should be true, each checkable after
- **P1** The proposal moves nothing: `git status` in the vault is clean after step 1.
- **P2** It proposes at least the August lipika threads (`2026-08-21-does-the-machinery-hold-up`,
  `2026-08-21-records-and-views`, `2026-08-25-do-the-tools-tell-the-truth`,
  `2026-08-31-which-copy-does-a-client-load`) and `vault-maintenance`, which the 2026-09-24 sweep found
  held nothing that is not a duplicate, a convention, or fired.
- **P3** It proposes no thread that accrued on 2026-09-24.
- **P4** Every move goes through `lipika archive-thread`; none through `mv` or `git mv`. Read the
  curator's transcript.
- **P5** Every archived thread's commit is 100% renames: `git show --stat -M` lists only renames.
- **P6** `lipika dangling-links .` from the vault root reports no more dangling links after than before.
  Record the before count first.
- **P7** `lipika threads` no longer lists an archived thread; `lipika threads --all` lists it as
  `archive/<thread>`.
- **P8** The regenerated index lists archived threads as finished, not as live.

## Run 1, 2026-09-24 — cancelled at the proposal
Run through a `claude -p --plugin-dir <worktree>` subprocess, with the branch's `bin` first on PATH.
P1–P3 held. The owner cancelled before any move: the proposal judged each thread from its routing note
and orientation headline, gave nothing to rule on, and repeated a stale claim from an orientation
(unmerged commits on lipika `main`; `git rev-list --count origin/main..main` was 0).

## What a curation report must do (for run 2, written before the definition change)
- **P9** For each thread it reads, it lists every item in that thread's newest orientation and classes it:
  **done** (its death condition fired, with the check it ran), **live**, **always true**, **duplicate**
  (naming the other thread), or **uncheckable**.
- **P10** Each live item names where it should be carried: an existing live thread, a new thread, or
  nowhere, with the reason.
- **P11** A claim about the state of a repo or PR is checked by a command in this run, not repeated from
  a document. The stale local-`main` claim from run 1 does not reappear.
- **P12** Each thread gets a recommendation (archive, keep, or merge into a named thread) with its
  basis, and the report opens with a plain one-paragraph summary of what each thread was for.
- **P13** It still moves, writes and commits nothing (P1).

## Run 2, 2026-09-24 — the seven-thread lipika chain, proposal only
Same subprocess route; $3.37, 404 s. Vault clean after (P13).
- **P9 partial.** Items are classed, but runs of ~30 `dies never` items are classed as one group.
- **P10 mostly.** Most live items name a destination; a few say only "not carried".
- **P11 held.** PR and git claims were checked with `gh` and `git log`; run 1's stale local-`main`
  claim now reads "landed via #21".
- **P12 held.** A plain summary and a recommendation per thread.
- It recommended archiving six and keeping `2026-09-17-how-do-external-references-get-recorded`, and
  surfaced two unruled escalations whose last home is in the chain (`c085ca2` edited a record in place;
  contradictory restart measurements).
- It read the installed `lipika doctor` as blocking any move. The conclusion is right until 0.6.0 is
  deployed, because other sessions still run a `lipika threads` that lists `archive` as a thread.
