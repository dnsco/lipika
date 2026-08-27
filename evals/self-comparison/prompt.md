# Case — the installed copy is the only copy that runs, and it is not the checkout

There are two copies of this repo on any machine that has installed it: the **git checkout** someone
edits, and the **frozen snapshot** under `~/.claude/plugins/cache/lipika/lipika/<version>/` that the
plugin system actually runs. The deploy loop's step 6 exists to prove they match, because a
measurement taken against a stale snapshot measures the previous round and reports clean.

`0.3.0` shipped that comparison as `doctor`'s `installed_vs_tree()` and as `handoff-prompt --deployed`'s
exit-3 refusal. Both work out "the checkout" as **the folder the running script sits in**.

## The prompt

From a machine where the plugin is installed and the checkout differs from it — an edit not yet
deployed is enough — run each of these and read what it says:

> ```
> lipika doctor
> lipika handoff-prompt <a-thread-that-deployed> --deployed
> ```

Then run them again with `PATH` pointing only at the installed `bin/`, so no checkout is reachable.

## What this case exists to catch

Measured 2026-08-26, first session after the `0.3.0` restart:

- The installed `doctor` printed `ok installed 0.3.0 IS the tree (skills, agents, tools, bin)` while
  the checkout differed in **six files** and was missing `tools/threads.py` entirely. One line earlier
  the same run printed `WARNING that is NOT this checkout` — it had already computed the fact the
  comparison needed, and the comparison did not use it.
- The installed `handoff-prompt --deployed` emitted a gate block whose `T` and `I` were **the same
  directory**. Both absolute, which is all `0.3.0`'s own grader required. `differing()` was empty by
  construction, so the exit-3 refusal could not fire.
- The block that reached a human named `V=0.3.0` while pointing `T` at a checkout declaring `0.2.4`.
  The session that pasted it ran the loop by hand, got `STALE: skills` / `STALE: tools`, and had to
  reconstruct from `git archive` which branch was actually deployed before it could measure anything.

**The failure is not that a comparison can be wrong. It is that a comparison of a copy against itself
is indistinguishable, in the output, from a comparison that passed** — same word, same column, same
exit code. This is the same class as [[a proof that could not fail]], recorded on this thread
2026-08-24 and reproduced here inside the fix written for it.
