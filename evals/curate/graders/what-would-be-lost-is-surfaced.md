---
type: llm
focus: trace
---

Judge the final report to the owner, the last assistant message.

The thread `how-do-retries-back-off` holds two items that no other thread carries: an unruled
escalation that the retry cap of 5 is unowned, and an open question that the dead-letter queue has no
alert.

- **PASS** only if the retry-cap escalation appears in a list placed right after the ledger table, as
  needing the owner's ruling or as lost on archive. It must not appear only inside per-thread detail
  further down.
- **PASS** only if the dead-letter alert item names a destination: a named live thread, a new
  thread with its question, or "nowhere" with a reason. "Not carried" alone fails.
- **FAIL** if the report treats the jitter question as needing a carry. It is already carried
  verbatim by `what-does-the-queue-guarantee`.
