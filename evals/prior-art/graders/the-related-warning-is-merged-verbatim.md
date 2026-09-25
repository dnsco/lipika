---
type: regex
target: trace
pattern: '## From[^"\\]*why-is-the-cache-slow(?:[^"\\]|\\.)*Running `MONITOR` on the cache doubles its latency\.'
---

# the related thread's bearing warning is merged into the new gotchas.md, verbatim

Measuring eviction is exactly when someone reaches for `MONITOR`, and the archived thread measured
that it doubles latency. The warning travels verbatim, so the new thread's `gotchas.md` carries it
under a `## From` heading naming the thread it came from. Matched inside one written string, so a
scout's report quoting it does not pass.
