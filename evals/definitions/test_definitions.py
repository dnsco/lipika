#!/usr/bin/env python3
"""Tests over the shipped definitions: what they tell an agent to run must run.

Run `python3 evals/definitions/test_definitions.py`. Exit 0 all pass, 1 any fail.

`--kind` values are checked by invoking `bin/lipika pass-log start` against a scratch log, so the
test follows the tool rather than a copy of its kind list.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIPIKA = REPO / "bin" / "lipika"
DEFS = sorted([*REPO.glob("agents/*.md"), *REPO.glob("skills/*/SKILL.md")])
KIND = re.compile(r"lipika pass-log start\b[^\n`]*?--kind\s+([A-Za-z_-]+)")

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def kind_accepted(kind, log):
    env = dict(os.environ, LIPIKA_TELEMETRY="0")
    r = subprocess.run([sys.executable, str(LIPIKA), "pass-log", "--log", str(log), "start", "test",
                        "probe", "--kind", kind], capture_output=True, text=True, env=env)
    return r.returncode == 0, r.stderr.strip()


def main():
    kinds = {}
    for p in DEFS:
        for k in KIND.findall(p.read_text()):
            kinds.setdefault(k, []).append(str(p.relative_to(REPO)))
    check("the definitions name at least one --kind", bool(kinds))
    with tempfile.TemporaryDirectory() as d:
        for k, where in sorted(kinds.items()):
            ok, err = kind_accepted(k, Path(d) / f"{k}.jsonl")
            check(f"pass-log accepts --kind {k} ({', '.join(where)})", ok, err)

    for p in DEFS:
        t = p.read_text()
        rel = p.relative_to(REPO)
        check(f"{rel} does not dispatch the retired scout", "lipika:scout" not in t)
        check(f"{rel} does not call the retired scope-recon", "scope-recon" not in t)
    check("agents/scout.md is gone", not (REPO / "agents" / "scout.md").exists())
    check("skills/spin-out/SKILL.md exists", (REPO / "skills" / "spin-out" / "SKILL.md").exists())

    dump = (REPO / "skills" / "context-dump" / "SKILL.md").read_text()
    check("context-dump's post-deploy handoff prompt passes --deployed, which carries the gate",
          "lipika handoff-prompt <workstream> --deployed" in dump)
    ext = (REPO / "evals" / "external-references" / "prompt.md").read_text()
    allowed = re.search(r"^allowed_tools:\s*\[([^\]]*)\]", ext, re.M)
    check("the external-references case allows Agent, since context-dump dispatches tracers",
          bool(allowed) and "Agent" in [s.strip() for s in allowed.group(1).split(",")])

    spin = REPO / "skills" / "spin-out" / "SKILL.md"
    t = spin.read_text() if spin.exists() else ""
    check("spin-out opens a pass for the run and one for prior-art reading",
          "pass-log start spin-out" in t and "pass-log start prior-art" in t)
    nested = sorted(set(re.findall(r"/lipika:([a-z-]+)", t)) - {"spin-out"})
    check("spin-out names no other /lipika: skill -- a nested Skill call ends its perf span",
          not nested, ", ".join(nested))

    # The ontology of 2026-09-30: a workstream is a body of work described by its problem space;
    # "project" is gone; a death condition is now an optional acceptance clause; curate re-partitions.
    ruled = [*DEFS, REPO / "CLAUDE.md", REPO / "design" / "vault-and-agent-ontology.md",
             REPO / "tools" / "lineage.py", REPO / "tools" / "init.py"]
    one_q = re.compile(r"workstream is one question|one question being answered|"
                       r"(?:because|when|finds) the question (?:has )?changed", re.I)
    project = re.compile(r"project is a split lineage|\bone project\b|a project's threads|"
                         r"\bis a project\b|chain is (?:one|a) project|cuts (?:one|a) project|"
                         r"one project's|\bprojects\b", re.I)
    for p in ruled:
        t = p.read_text()
        rel = p.relative_to(REPO)
        hit = one_q.search(t)
        check(f"{rel} does not define a workstream as one question", not hit, hit and hit.group(0))
        hit = project.search(t)
        check(f"{rel} does not call a lineage a project", not hit, hit and hit.group(0))

    def body(rel):
        p = REPO / rel
        return p.read_text() if p.exists() else ""

    pickup, dump, spin = body("skills/pickup/SKILL.md"), body("skills/context-dump/SKILL.md"), body(
        "skills/spin-out/SKILL.md")
    curate, curator = body("skills/curate/SKILL.md"), body("agents/curator.md")
    for rel, t in (("pickup", pickup), ("context-dump", dump), ("spin-out", spin)):
        check(f"{rel} splits on a different problem space", "problem space" in t)
        check(f"{rel} names the thread's `## What this is`", "## What this is" in t)
    check("context-dump teaches `→ accepted when`", "accepted when" in dump)
    check("context-dump no longer requires a death condition on every item",
          "Every item carries a death condition" not in dump)
    check("pickup checks acceptance, not death conditions", "accepted when" in pickup and
          "death condition" not in pickup)
    check("curate offers a re-partition ruling", "re-partition" in curate.lower() and "Re-partition" in curate)
    check("curate reads `lineages` from `lineage --json`", "`lineages`" in curate)
    check("curate writes `from:` with every parent", re.search(r"from:.*\n?\s*-\s*\"\[\[", curate) is not None
          or "every parent" in curate)
    check("the curator returns a REPARTITION block", "REPARTITION" in curator)
    check("the curator still moves nothing", "Move, write and commit nothing" in curator or
          "moves nothing" in curator)

    # The inbox: a dated record one thread leaves for another, absorbed by the receiver's next handoff.
    for rel, t in (("pickup", pickup), ("context-dump", dump), ("curate", curate), ("curator", curator)):
        check(f"{rel} reads the inbox with `lipika inbox`", "lipika inbox" in t)
    check("context-dump sends with `lipika inbox send`", "lipika inbox send" in dump)
    check("curate hands items on through the inbox, not 'by name'",
          "lipika inbox send" in curate and "by name" not in curate)
    check("the vault template lists inbox/", "inbox/" in body("templates/vault-CLAUDE.md.template"))
    # The 2026-11-10 audit: commands a skill prescribes must run as written.
    for m in re.finditer(r"lipika inbox send[^\n`]*", curate):
        check(f"curate's send names a slug: `{m.group(0)[:60]}`", "--slug" in m.group(0))
    check("curate's archive notification slug is unique per parent", "--slug archived-" in curate)
    check("curate commits the messages it sends", "commit" in curate.split("Carry out the rulings")[-1].lower())
    check("context-dump does not promise a recovery the carry does not make",
          "returns the message at the next handoff" not in dump)
    check("context-dump routes a report around an archived parent", "parent is archived" in dump)

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
