# What a handoff costs, and the two cases that measure the fix

Not read at run time. The runnable halves are `evals/dispatched-traces/` and
`evals/orientation-carry/`; running them: `design/agent-eval-method.md`, *Graders*.

## The measurement

`lipika span-report`, 2026-09-18, 107 passes:

```
context-dump   n=60   median 181s   worst 8045s   inside the 120s north star: 18/60
```

2026-08-21 read 114 s and 11/18 — the skill got slower as it grew. One pass profiled phase by phase
(2026-09-17, `span_s=600`) ran **flat at 150–230 B/s**; tool round trips were ~20 s of 179. A
flat-throughput cost has two levers — generate fewer bytes, or overlap the generation. One case each.

## `dispatched-traces` — overlap

Six traces cost 2 m 59 s / 27,900 B, ~11 KB of it Slack text copied out of tool output already in
context. The fix dispatches a `tracer` per addressable subject.

- **The saving exists only if the child re-opens the source.** Passing it the substance regenerates
  the bytes. So the check is that a dispatch happened, with an address and a path, not the content.
- **Synthesis is not dispatched.** Four of those six traces were across many artifacts plus the
  session's judgement; a child has neither. `unopened.md` least of all.
- **An unreachable source must be refused, not invented.** A fabricated trace is found only when
  someone re-opens the source — when it can no longer be caught.

Seeded: two addressable subjects, two synthesis, one unreachable URL.

## `orientation-carry` — fewer bytes

The orientation cost 4 m 37 s / 62,817 B, ~50 KB of it the previous live set retyped.
`orientation-audit` found three defects in the 91 carried items and none in the 17 new ones.

The owner's objection, 2026-09-18: a verbatim carry accretes. True, and typing never bounded it —
`9,067 → 62,817 B` over eight hand-typed handoffs. What is unbounded is the item that can never
leave:

| orientation | bytes | items | `[DEAD END]` + `dies never` |
|---|---|---|---|
| `2026-09-16-can-agentomatic-host-workloads` | 62,817 | 125 | 30 (24%) |
| `2026-09-17-how-do-external-references-get-recorded` | 22,326 | 72 | 30 (42%) |

Both carried **the same 19** `dies never` items — facts about the machine. So a `dies never` item
is a convention: written once to a durable surface, cited by the orientation. `[DEAD END]` stays; it
is thread-local.

## Where these die

- `dispatched-traces`: when a tracer's trace is found thinner than a session's on the same subject.
  No grader measures that.
- `orientation-carry`: when a carried orientation shows a defect a typed one would not have.
- **Both**, if `context-dump`'s median span does not move over real handoffs.
