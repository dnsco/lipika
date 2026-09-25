---
type: llm
focus: trace
---

Judge the final report to the owner, the last assistant message.

- **PASS** only if its first substantive block is a table with one row per thread (three rows). Each
  row has what the thread asked, its disposition and why. No per-item detail or per-thread section
  comes before the table. A sentence or two of framing above the table is allowed.
- **PASS** only if every row's "what it asked" is one plain sentence a reader who never saw the
  thread would understand. It must not just restate the thread's name or title (for example
  "Does the queue drop messages?" alone fails).
- **PASS** only if every row's "why" cites evidence: a check run, a named document, or a quoted line.
  "No recent activity" alone fails.
- **FAIL** if any disposition falls outside: `answered`, `subsumed by <thread>`,
  `superseded by <thread>`, `abandoned`, `still live`.
