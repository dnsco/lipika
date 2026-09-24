---
type: regex
target: trace
pattern: '"file_path":"(?![^"]*/workstreams/)[^"]*/reference/[^"]*\.md","content":"'
match: not_contains
---

Every write to a `reference/` file is under `workstreams/<thread>/`. A trace in the vault-root `reference/` belongs to no thread; a 2026-09-24 run at `0.4.2` wrote two there after the session sent its tracers no path.
