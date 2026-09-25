---
type: regex
target: trace
pattern: 'how-do-retries-back-off(?:(?!\\n).)*\|(?:(?!\\n).)*subsumed by(?:(?!\\n).)*what-does-the-queue-guarantee'
---

A ledger row names `how-do-retries-back-off` and, on the same line, `subsumed by` the thread that
took it over. The successor's routing note says so, and carries the jitter question verbatim.
