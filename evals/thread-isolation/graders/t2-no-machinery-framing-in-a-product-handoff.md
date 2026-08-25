---
type: eval
kind: grader
life: evergreen
status: sealed
date: 2026-08-25
case: thread-isolation
---

# T2 — a handoff for a thread that deployed nothing says nothing about deploying

**Written and committed BEFORE the change.**

## The change under test

`tools/handoff_prompt.py:compose` emits the deploy sentence, the version, the four-directory gate and
the restart framing **unconditionally**, for every thread. It is being changed so that framing appears
only when a deploy actually happened, and so the tool **refuses rather than asserts** when it cannot
know.

**Precondition.** A thread must exist in the vault whose work is not this machinery and which has
never deployed the plugin. `embedded-jetty-docker` was that thread on 2026-08-25. If no such thread
exists, this is **UNEXERCISED**.

- **PASS** — for such a thread, the emitted prompt contains **no** version claim, **no** loop over
  `skills agents tools bin`, and **no** sentence asserting a redeploy or a restart.
- **PASS** — the tool never states as fact something it cannot check. It knows the *installed* version;
  it does not know whether **this session** deployed. So either it is told, or it says nothing — and
  being told is an argument, not an inference.
- **FAIL if** the machinery framing is emitted with a caveat attached, in any form — *"if you deployed,
  run this"*, *"skip if not applicable"*, a parenthetical, a line above the fence. **A conditional
  inside a pasteable block moves the judgement onto the reader with the least context**, which is the
  reasoning that made this a tool instead of prose in the first place.
- **FAIL if** the decision is inferred from the thread's name, path, tags, or which files its dumps
  mention. That is `up:` again: a value nothing declared, acquiring a meaning, read by one caller and
  explained by none. It must be **declared or absent**.
- **FAIL if** the gate, when it *is* correctly emitted, still resolves its four directories against
  whatever directory the next session happens to open in. Measured 2026-08-25: in a product checkout
  three legs error and the fourth prints `Only in agents: .gitignore` — a **plausible** finding, not an
  obvious one, because that repo's `agents/` holds Java agent jars.
- **FAIL if** a thread with no eval documents is told *"No graders are recorded against this thread;
  there is nothing to score."* For a thread that has never had graders, a confident negative about
  scoring is an answer to a question nobody asked. Omit the sentence.

## What a suspicious result looks like

**All six green would be suspicious**, and one clause is weaker than the others: the fifth is satisfied
by any absolute path and does not prove the path is *right*. If everything reads green, check that the
gate was actually run from a foreign directory rather than from this checkout, where the relative form
works and proves nothing.
