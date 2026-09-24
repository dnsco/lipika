# What a handoff costs, and the two cases that measure the fix

**Written 2026-09-24, before the change, per step 1 of the loop.** A grader written afterwards
silently agrees with whatever happened — measured twice. These exist so the next round can be
wrong in a way somebody notices.

## The measurement this answers

`lipika span-report`, read 2026-09-18 over 107 completed passes:

```
context-dump   n=60   median 181s   worst 8045s   inside the 120s north star: 18/60
```

The same table in `vault-and-agent-ontology.md` §8, taken 2026-08-21, read 114 s and 11/18. The
operation has got **slower** as the skill grew, and it misses its own declared goal 70% of the time.

One pass was profiled phase by phase — 2026-09-17, `workstreams/2026-09-16-can-agentomatic-host-workloads`,
`span_s=600` in the pass log. Throughput was **flat at 150–230 B/s in every phase**: references at
156, the dump at 170, the orientation at 227. Time tracked bytes generated almost linearly, and tool
round trips were minor — 5 calls for 6 trace files cost ~20 s of a 179 s phase.

A flat-throughput cost has exactly two levers: **generate fewer bytes**, or **overlap the
generation**. One case per lever.

## `dispatched-traces` — overlap, and the trap inside it

Six reference traces cost 2 m 59 s / 27,900 B, of which ~11 KB was Slack message text copied by hand
out of `slack_read_thread` output that was already verbatim in the session's context.

**The trap, and A1 exists because of it.** If the parent passes the substance to a child in the
prompt, it generates the same bytes it was trying not to generate and parallelism buys nothing. The
saving only exists when the child **re-opens the artifact itself** — the parent sends an address and
a claim, ~200 B, and the child's reading happens in a context that is discarded. So the check is
that a dispatch occurred, not that the output got smaller.

**A3 is the other half, and it is the one a mechanism-shaped reading gets wrong.** Of the six traces
in the profiled pass, two were conversations (one artifact each, delegable) and four were synthesis
across many tool results (not). A child sent to write a synthesis trace has neither the artifacts in
view nor the judgement, and returns a confident summary of the wrong thing. `unopened.md` is the
sharpest instance: only the session knows what it did not open, so an absence cannot be delegated.

**A4 is the one that matters most.** A child that cannot reach its source can still produce a
fluent, correctly shaped, entirely fabricated trace. Every other grader here is about speed; this
one is about whether the record is still evidence. A fabricated trace is worse than the cost being
removed, and it fails silently — nobody re-reads a trace until the source is gone, which is exactly
when the fabrication cannot be caught.

The case seeds five subjects: two addressable, two synthesis, one unreachable.

## `orientation-carry` — fewer bytes, and the objection that reshaped it

The orientation cost 4 m 37 s / 62,817 B. Of that, ~50 KB was the previous orientation's live set
re-authored token by token; the session had introduced 17 items. `orientation-audit` then reported
"91 of 91 accounted for" — verifying work a program could have done.

The defect rate is the argument. The audit flagged three problems: one item matched on prose alone
at 56% content words, having been reworded while copied, and two lost death conditions they had
carried in the predecessor. **All three were in carried items; none in the 17 new ones.**

**The objection, raised by the owner 2026-09-18: a tool that carries verbatim will just accrete
nonsense.** It is right that nothing would bound the document, and wrong that typing was ever the
bound. That thread's orientation, every byte hand-typed:

```
9,067 → 17,095 → 19,890 → 28,160 → 36,545 → 45,470 → 49,867 → 62,817 B
```

Eight handoffs, 48 hours. Typing never slowed it once.

What is actually unbounded is the class of item that can never leave. Counting `[DEAD END]` plus
anything whose death condition reads `dies never`:

| orientation | bytes | items | immortal |
|---|---|---|---|
| `2026-09-16-can-agentomatic-host-workloads` | 62,817 | 125 | 30 (24%) |
| `2026-09-17-how-do-external-references-get-recorded` | 22,326 | 72 | 30 (42%) |

Both carry **the same 19** `dies never` items — the `Edit` tool needing its own `Read`, `grep
--include` under zsh, a refusal read through `tail` looking like a success. Facts about this
machine, true of every thread, duplicated per thread and re-typed at every handoff.

So B3: **an item whose death condition is `dies never` is a convention, not a live item.** It goes
on a durable surface once and the orientation cites it. `[DEAD END]` stays, because it is
thread-local — *do not re-propose this, here* — which no shared surface can say.

That inverts what the tool is for. It does not make carrying cheap; it makes the immortal fraction
**visible**, with an exit code, at the one moment an author is looking at it. `orientation-audit`
already reports staleness after the fact and gets read past.

**B4 is deliberately weak and says so.** B1 can be passed by careful retyping, and the profiled
handoff was careful too, until it was not.

## Where each of these dies

- `dispatched-traces` dies when a tracer's output is measured against a session-written trace on the
  same subject and found thinner. That is A2's failure mode and nothing has observed it yet.
- `orientation-carry` dies when an orientation written through the carry is audited and shows a
  defect the hand-typed version would not have had.
- **Both die if `context-dump`'s median span does not move.** Two handoffs is not a distribution;
  report two figures with their dates, not a new median.

## Running them

```
claude plugin eval . --case <name> --scaffold --allow-tools Bash Write Edit Task --trust-plugin
```

`--scaffold` is off by default and without it every `file_exists` grader fails for the wrong reason.
The run also starts **logged out** of the parent's session (commit `496d062`), which surfaces as
`judge call failed: Not logged in` on every `llm` grader — a credential fault, not a score.

Measured 2026-09-24 while writing these: `count:` is not a valid key on a `tool_used` grader, and
the loader rejects the whole case file for it. `tool_used` takes `tool:`; `tool_order` takes
`before:` and `after:`. Both cases load at `0.3.7`.
