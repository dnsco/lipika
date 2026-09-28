---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?:[^"\\]|\\.)*from: \\?"?\[\[2026-09-10-how-does-the-cache-invalidate'
---

# the run wrote a first orientation naming its parent

A guard. It checks that a new thread's orientation was written with `from:` naming the parent.
Without it, the not-contains graders pass on a run that did nothing.
