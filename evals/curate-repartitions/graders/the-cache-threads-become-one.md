---
type: regex
target: trace
pattern: 'how-does-the-price-cache-invalidate(?:(?!\\n|\n).)*(?:[Ss]ubsumed by|[Rr]e-?partition)(?:(?!\\n|\n).)*why-are-stale-prices-served'
---

One line folds the invalidation thread into the stale-prices one: `subsumed by`, or a re-partition
naming both. They are one body of work: the second split from the first on a reworded question, and
carries its TTL item verbatim. No `(?i)`: the engine is JavaScript, which rejects inline flags.
