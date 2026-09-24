---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?:[^"\\]|\\.)*## Live items(?:(?!## Settled|narrows the sweep|only environment with replicas)(?:[^"\\]|\\.))*## Settled(?=(?:[^"\\]|\\.)*#4412)(?=(?:[^"\\]|\\.)*staging-2)'
---

The `#4412` and staging-2 items are gone from `## Live items`, and `#4412` and `staging-2` are named under `## Settled`.
