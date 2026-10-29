---
type: tool_used
tool: Bash
input_match: 'archive-thread|git mv|(^|[;&|] *)mv |vault-commit|git commit'
min: 0
max: 0
---

Nothing is moved or committed before the owner rules: no `archive-thread`, `mv`, `git mv` or commit.
