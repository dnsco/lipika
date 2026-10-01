#!/usr/bin/env python3
"""Tests for acceptance: the optional `→ accepted when …` clause that replaced the death condition.

Run `python3 evals/acceptance/test_acceptance.py`. Exit 0 all pass, 1 any fail.

Ruled 2026-09-30. An item MAY say what would finish it (`→ accepted when …`); nothing requires it,
and the carrying agent judges liveness. Old records keep `→ dies when …` and `→ dies never`, which
the tools still read, because a record is never edited.

The regression this pins: `orientation-carry` separated any item whose PROSE contained `dies never`
as immortal, even one closing `→ dies when shipped`. Three false drops at the 2026-09-30 handoff.
Only the closing clause decides.

These drive `bin/lipika` in this tree against a fixture vault and import nothing from `tools/`.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"

PREV = """---
type: orientation
---

## Live items

- [OPEN Q] **Ship the acceptance wording.** → dies when the PR merges · as-of 2026-09-29
- [OPEN Q] **Carry the thing that has a goal.** → accepted when the tool reads both · as-of 2026-09-29
- [OPEN Q] **`orientation-carry` treats any item containing `dies never` as immortal.** → dies when fixed · as-of 2026-09-29
- [OPEN Q] **An item with no clause at all.** · as-of 2026-09-29
- [LANDMINE] **The `Edit` tool needs its own `Read`.** → dies never · as-of 2026-09-15
"""

# The successor rewrites one old clause into the new vocabulary, and carries the rest.
CUR = """---
type: orientation
---

## Live items

- [OPEN Q] **Ship the acceptance wording.** → accepted when the PR merges · as-of 2026-09-29
- [OPEN Q] **Carry the thing that has a goal.** → accepted when the tool reads both · as-of 2026-09-29
- [OPEN Q] **`orientation-carry` treats any item containing `dies never` as immortal.** → dies when fixed · as-of 2026-09-29
- [OPEN Q] **An item with no clause at all.** · as-of 2026-09-29
"""

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def lipika(vault, *args):
    env = dict(os.environ, LIPIKA_TELEMETRY="0")
    return subprocess.run([sys.executable, str(LIPIKA), *args, "--vault", str(vault)],
                          capture_output=True, text=True, env=env)


def fixture(d, docs):
    vault = Path(d)
    ws = vault / "workstreams" / "2026-09-20-t"
    (ws / "orientation").mkdir(parents=True)
    for stamp, text in docs:
        (ws / "orientation" / f"{stamp}.md").write_text(text)
    return vault, ws


def main():
    # orientation-carry: only the closing clause makes an item a standing warning.
    with tempfile.TemporaryDirectory() as d:
        vault, _ = fixture(d, [("2026-09-29-100000", PREV)])
        r = lipika(vault, "orientation-carry", "2026-09-20-t")
        out, err = r.stdout, r.stderr
        check("an item closing `→ dies when` is carried even when its prose says `dies never`",
              "treats any item containing" in out and "treats any item containing" not in err,
              f"stdout:\n{out}\nstderr:\n{err}")
        check("an item closing `→ accepted when` is carried", "Carry the thing that has a goal" in out, out)
        check("an item with no clause is carried", "An item with no clause at all" in out, out)
        check("an item closing `→ dies never` is still separated, since old records say it",
              "needs its own" in err and "needs its own" not in out, f"stdout:\n{out}\nstderr:\n{err}")
        check("the separation message speaks of warnings that stay true, not death conditions",
              "death condition" not in err, err)

    # orientation-audit: acceptance is optional, and a clause reworded to the new vocabulary is carried.
    with tempfile.TemporaryDirectory() as d:
        vault, _ = fixture(d, [("2026-09-29-100000", PREV), ("2026-09-30-100000", CUR)])
        r = lipika(vault, "orientation-audit", "workstreams/2026-09-20-t", "--today", "2026-09-30")
        out = r.stdout
        check("the audit no longer reports items for lacking a death condition",
              "death condition" not in out, out)
        check("an item without an acceptance clause is not flagged for it",
              "no clause at all" not in out, out)
        check("`→ dies when X` rewritten as `→ accepted when X` counts as carried, not reworded",
              "Ship the acceptance wording" not in out, out)
        check("the only unaccounted item is the standing warning the successor moved out",
              "4 accounted for" in out, out)

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
