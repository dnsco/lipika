# Case — two live threads, and neither is the other's business

The vault this runs against holds at least two threads accruing on the same day: one whose work **is
this machinery** (`skills/`, `agents/`, `tools/`, a plugin version, a deploy), and one whose work is a
**product change in another repo entirely** (a service migration, a chart, a Dockerfile). The vault's
commit log interleaves them, so "most recently touched" alternates between them hour by hour.

## The prompt

Open a session with no thread named, and ask it to orient and then hand off.

> Pick up where we left off, then write the handoff when we're done.

## What this case exists to catch

Measured 2026-08-25 on a vault with exactly this shape:

- `lipika handoff-prompt embedded-jetty-docker` — a Docker/Jetty migration thread that has never
  deployed this plugin — emitted *"The plugin was redeployed to 0.2.6 and this session is the first to
  run after the restart"*, followed by a gate diffing `skills agents tools bin`, followed by *"No
  graders are recorded against this thread; there is nothing to score."* **Exit 0.**
- Pasted into that thread's own checkout, the gate prints `diff: skills: No such file or directory`
  for three legs, and for the fourth prints `Only in agents: .gitignore` — because that repo has an
  `agents/` directory holding `opentelemetry-javaagent.jar` and `postgresql.jar`. The block says *"Any
  output means stop and deploy before measuring."*
- So a product-thread handoff instructs the next session to stop and deploy this plugin, and one of
  its four legs produces a **plausible-looking** staleness finding rather than an obvious category
  error.

Both capture skills resolve their thread as "usually the most recently touched workstream". With the
log interleaved, that hands a product session the machinery thread and a machinery session the product
thread, with nothing anywhere reporting a mismatch.

**The failure is not that the wrong thread is possible. It is that every wrong answer is silent and
confident.**
