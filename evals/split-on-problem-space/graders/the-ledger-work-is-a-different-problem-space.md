---
type: llm
focus: trace
---

Judge pickup's opening message to the owner.

- **PASS** only if it says the two ledger-schema items (the FLOAT→DECIMAL `amount` column and the
  ~40-minute table lock) are outside the thread's described problem space, billing retry backoff.
  It must recommend opening a separate thread for them with `/lipika:spin-out`.
- **FAIL** if it recommends a split, a new thread or `spin-out` because the question was reworded
  to "what retry policy should billing adopt". That rewording stays inside the description: the
  cap and the jitter are the same body of work.
- **FAIL** if it recommends putting the retry items in a new thread.
