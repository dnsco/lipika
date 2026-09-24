---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?=(?:[^"\\]|\\.)*?timer restarts on config reload(?:[^"\\]|\\.)*?timer is made monotonic(?:[^"\\]|\\.)*?as-of(?:\\n|\s)+2026-09-20)(?=(?:[^"\\]|\\.)*?same status code(?:[^"\\]|\\.)*?as-of(?:\\n|\s)+2026-09-19)(?=(?:[^"\\]|\\.)*?measured the stale window)'
---

In the orientation written: the sweep-timer item keeps its death condition and `as-of 2026-09-20`, the status-code item keeps `as-of 2026-09-19`, and the unloaded-measurement gate survives.
