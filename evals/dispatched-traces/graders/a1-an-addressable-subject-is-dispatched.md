---
type: tool_used
tool: Task
---

# A1 — an addressable subject is dispatched, not transcribed

The mechanical half of the claim this round exists to test. Two of the five things named in the
prompt are **one addressable artifact each** — the `#platform-eng` export and the incident review.
Each is a subject a sub-agent can re-open on its own, having been given only a path and a claim.

Why this is the check and not a byte count: throughput during a handoff was measured flat at
150–230 B/s across every phase (2026-09-17, `span_s=600`), so the cost is the session generating
text. Passing the substance to a child in the prompt would generate the same bytes and buy nothing.
The saving only exists when the child **re-opens the artifact itself**, which means a dispatch has
to appear in the trace.

At least two dispatches. Fewer means the session transcribed a subject it could have delegated.

This is the mechanical complement to A3, which fails a run that dispatches everything.
