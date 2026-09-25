---
type: regex
target: trace
pattern: 'does-the-queue-drop-messages(?:(?!\\n).)*\|(?:(?!\\n).)*\banswered\b'
---

A ledger row names `does-the-queue-drop-messages` and, on the same line, the disposition `answered`.
Its gate fired: the load-test dump exists.
