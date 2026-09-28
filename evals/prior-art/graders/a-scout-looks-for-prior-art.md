---
type: tool_used
tool: Agent
input_match: 'lipika:scout'
min: 1
---

# a scout is sent to find prior art

Opening a thread is when warnings from other threads can be pushed into it. Later, finding them
depends on someone searching, and a search that nobody runs never fires. The session sends a
`lipika:scout` rather than reading every thread in its own context. The scout returns candidates
and reasons. Deciding which ones apply stays with the session.
