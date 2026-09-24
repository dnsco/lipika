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
