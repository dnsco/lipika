---
type: regex
target: trace
pattern: '/dumps/[^"]*\.md","content":"(?:[^"\\]|\\.)*\[\[\d{4}-\d{2}-\d{2}-(?!unopened|references)[a-z0-9-]+\]\]'
---

The dump links at least one of its own traces, `[[YYYY-MM-DD-<topic>]]`, not only the unopened list. Weaker than "names the page in words", which no mechanical check can see.
