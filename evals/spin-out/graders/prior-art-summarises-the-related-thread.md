---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?:[^"\\]|\\.)*## Prior art(?:(?!\\n## )(?:[^"\\]|\\.))*why-is-the-cache-slow(?:(?!\\n- |\\n\\n)(?:[^"\\]|\\.))*?(?:[Ee]vict|sweep|allkeys|maxmemory)'
---

# prior art says what the related thread found

A bare link makes the reader open the thread to learn whether it matters. In the cache-latency thread's
bullet, `## Prior art` says what it found: eviction sweeps on a full instance were the
cost.
