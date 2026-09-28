---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?:[^"\\]|\\.)*## Prior art(?:(?!\\n## )(?:[^"\\]|\\.))*what-carries-billing-traffic'
match: not_contains
---

# prior art leaves out the unrelated thread

The billing-traffic thread is about another system. A prior-art section that lists every thread
is an index, and nobody reads an index.
