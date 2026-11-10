---
type: regex
target: trace
pattern: '/orientation/[^"]*\.md","content":"(?:[^"\\]|\\.)*?\\n## (?:(?:Live items|Needs the owner)\\n(?:(?!\\n## )(?:[^"\\]|\\.))*?\\n- (?:(?!\\n- |\\n#)(?:[^"\\]|\\.))*?61(?:–|-|\\u2013)64s(?:(?!\\n- |\\n#)(?:[^"\\]|\\.))*?as-of 2026-09-23|Settled since the last orientation\\n(?:(?!\\n## )(?:[^"\\]|\\.))*?\\n- (?:(?!\\n- |\\n#)(?:[^"\\]|\\.))*?(?:61(?:–|-|\\u2013)64s(?:(?!\\n- |\\n#)(?:[^"\\]|\\.))*?\[\[(?:[^\]"\\]*/)?2026-09-23-091500-harness-measured-the-window[\]|#]|\[\[(?:[^\]"\\]*/)?2026-09-23-091500-harness-measured-the-window[\]|#](?:(?!\\n- |\\n#)(?:[^"\\]|\\.))*?61(?:–|-|\\u2013)64s))'
---

The message's item — the stale window under load is 61–64s — is one item of the new orientation: under
`## Live items` or `## Needs the owner` with its own `as-of 2026-09-23`, or under `## Settled since the
last orientation` linking the message as its basis. A mention only in narrative is not a disposition.
A regex, not a judge: on 2026-11-10 a judge voted FAIL three times on an orientation that carried the
item under `## Live items` with its as-of, most likely because it never saw the file.
