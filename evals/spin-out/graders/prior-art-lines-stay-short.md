---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?:[^"\\]|\\.)*## Prior art(?:(?!\\n## )(?:[^"\\]|\\.))*why-is-the-cache-slow(?:(?!\\n- |\\n\\n)(?:[^"\\]|\\.)){350}'
match: not_contains
---

# a prior-art bullet stays short

One or two sentences on what the related thread found. Caveats, dates and detail stay in that
thread, one link away; an orientation that restates its prior art grows with every split.
