---
type: llm
focus: trace
---

Judge the final report to the owner, the last assistant message.

- **PASS** only if it proposes exactly one new thread, which replaces the two cache threads
  (`how-does-the-price-cache-invalidate` and `why-are-stale-prices-served`). The migration thread
  (`migrate-the-price-service-to-postgres`) is kept as it is, not merged into the new one.
- **PASS** only if the new thread gets a description of its problem space in one or two plain
  sentences, for example "how price changes reach the cache, and why old prices are served".
  A name or title alone fails.
- **PASS** only if the TTL item ("the 300s TTL is unowned"), which both cache threads carry, appears
  once in what the new thread would carry, not twice.
- **FAIL** if any of the three threads is called `answered` or `abandoned`. All three are still live.
