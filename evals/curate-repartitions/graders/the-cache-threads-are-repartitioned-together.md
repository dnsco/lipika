---
type: regex
target: trace
pattern: '(?i)re-?partition(?:(?!\n).)*(?:how-does-the-price-cache-invalidate(?:(?!\n).)*why-are-stale-prices-served|why-are-stale-prices-served(?:(?!\n).)*how-does-the-price-cache-invalidate)'
---

One line proposes a re-partition naming both cache threads. They are one body of work: the second
split from the first on a reworded question, and carries its TTL item verbatim.
