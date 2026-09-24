---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?:[^"\\]|\\.)*## Live items(?:(?!## Settled|dies never)(?:[^"\\]|\\.))*Invalidating on read(?:(?!## Settled|dies never)(?:[^"\\]|\\.))*## Settled'
---

No `dies never` item in `## Live items`; the `[DEAD END]` about invalidating on read stays.
