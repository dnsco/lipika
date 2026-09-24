#!/usr/bin/env python3
"""trace-check — can a later reader get back to the source each `reference/` trace rests on?

WHY THIS EXISTS
  `reference-check` answers the other half: every external URL a thread CITES is carried by some
  trace. It says nothing about whether the traces themselves are any good, and it cannot -- a
  thread with no traces and no URLs exits 0 on both counts.

  This became worth a tool when traces started being written by a DISPATCHED sub-agent rather than
  by the session. A child sent to trace a subject it cannot reach can still produce a fluent,
  correctly shaped, entirely fabricated document, and a fabricated trace is not a slower record --
  it is a false one, discovered only when somebody tries to re-open the source, which is years
  later and exactly when it cannot be repaired.

  Fabrication is not machine-detectable and this tool does not pretend to detect it. It checks the
  two things that ARE mechanical, and they are the two that make a fabricated trace survivable:

    1. **An address.** A trace with nothing to get back to the source with -- no URL, no repository
       path, no channel id, no command -- is an assertion, not evidence. This is the check that
       fires on a child that could not reach its source and wrote something anyway.
    2. **A name that says what it is about.** `YYYY-MM-DD-<topic>.md`. The aggregate shape
       `<stamp>-references.md` was ruled out 2026-09-17 after one produced forty heterogeneous
       references in 401 lines, 121 of them a machine-readable index -- and newest-wins over an
       aggregate means correcting one reference rewrites forty.

  Calibrated against the real vault 2026-09-24 rather than against a notion of the right shape.
  Every trace written under `0.3.7`'s per-subject rule passes as written; the three surviving
  aggregates from before it are what it names. They are records and they stay -- a finding here is
  a fact about a document, never an instruction to edit one.

WHAT IT DOES NOT CHECK
  Whether the trace states the fact it settled rather than describing the document, and whether a
  conversation's substance was carried or only its permalink. Both are judgement, both are graded
  by `evals/dispatched-traces`, and a regex pretending to score them would report a bibliography
  as evidence.

CONTRACT

  exit 0  every trace in the thread has an address and a topic-shaped name
  exit 1  findings, listed. A fact about the documents; NOT an instruction to edit a record
  exit 3  NOT CHECKED: the thread has no reference/ at all. Said out loud, because a thread that
          rested on external sources and traced none of them looks identical to one that read
          nothing, and only the session knows which
  exit 5  bad invocation

USAGE
  lipika trace-check <ws>
  lipika trace-check --self-test
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_config     # noqa: E402

# `YYYY-MM-DD-<topic>.md`, where <topic> is not itself a clock. `2026-09-17-211737-references.md`
# fails twice over: the HHMMSS says it was named by a stamp meant for a dump, and `references`
# names no subject.
NAMED = re.compile(r"^\d{4}-\d{2}-\d{2}-(?!\d{4,6}(?:-|\.))(?P<topic>[a-z0-9][a-z0-9-]*)\.md$")
GENERIC = {"references", "reference", "sources", "links", "urls", "notes"}

URL = re.compile(r"https?://[^\s<>\"'`)\]}|]+")
# An address that is not a URL, because most of what is worth tracing is not reachable by one.
# A Slack channel id, a repo path in backticks, a command that fetches it, a file path with an
# extension. Deliberately generous: the failure being caught is a document with NOTHING.
ROUTE = re.compile(
    r"\b[CDG][A-Z0-9]{7,}\b"                       # Slack channel / DM id
    r"|`[^`\n]*[/.][^`\n]*`"                        # a path, a command, a dotted name in backticks
    r"|\b(?:gh|git|curl|kubectl|aws|slack_read_\w+|mcp__\w+)\b"   # a route you can run
    r"|\b\d{10}\.\d{6}\b")                          # a Slack ts
# NOT case-insensitive, and the fixture is why. With `re.I` the Slack-id branch -- `[CDG]` then
# seven alphanumerics -- matched the ordinary English word `Decision`, so a trace with no address
# at all passed. Found 2026-09-24 by red case 2, not by reading the pattern.

# The unopened backlog is a trace of an ABSENCE. It has no address by definition -- that is what
# makes it the unopened list -- and it is exempt from the address rule, not from the naming one.
UNOPENED = re.compile(r"^\d{4}-\d{2}-\d{2}-unopened\.md$")


def findings(ref_dir):
    """[(filename, problem)] for every trace that cannot be got back from, or is misnamed."""
    out = []
    for f in sorted(os.listdir(ref_dir)):
        if not f.endswith(".md"):
            continue
        m = NAMED.match(f)
        if not m:
            out.append((f, "not named YYYY-MM-DD-<topic>.md -- a trace is addressed by its "
                           "subject, and a bare stamp names none"))
        elif m.group("topic") in GENERIC:
            out.append((f, f"named `{m.group('topic')}`, which is the aggregate shape ruled out "
                            "2026-09-17 -- name it for the subject it covers"))
        if UNOPENED.match(f):
            continue
        text = open(os.path.join(ref_dir, f), errors="replace").read()
        if not (URL.search(text) or ROUTE.search(text)):
            out.append((f, "NO ADDRESS -- nothing here gets a later reader back to the source. "
                           "A URL, a repository and path, a channel id, or the command that "
                           "fetches it"))
    return out


def run(ws, out=sys.stdout):
    ref = os.path.join(ws, "reference")
    if not os.path.isdir(ref):
        print(f"NOT CHECKED: no reference/ under {os.path.basename(ws)}.", file=out)
        print("  A thread whose work was entirely in-repo writes no trace, and that is correct.\n"
              "  A thread that rested on external sources and traced none of them looks exactly\n"
              "  the same from here. Only the session knows which this is.", file=out)
        return 3

    traces = [f for f in sorted(os.listdir(ref)) if f.endswith(".md")]
    bad = findings(ref)
    print(f"-- traces in {os.path.basename(ws)}/reference: {len(traces)}", file=out)
    print(f"-- with an address and a topic-shaped name: {len(traces) - len({f for f, _ in bad})}",
          file=out)
    if not bad:
        return 0

    print(f"\n== FINDINGS: {len(bad)}", file=out)
    for f, why in bad:
        print(f"   {f}\n       {why}", file=out)
    print("\nA finding is a fact about a document, not an instruction to edit one. A trace is a\n"
          "record: correct it with a NEWER dated trace, and rename only through\n"
          "`lipika obsidian rename`, which moves the links as part of the operation.", file=out)
    return 1


def self_test():
    """Hand-audited: one green trace, three distinct reds, and the unopened exemption."""
    import io
    import tempfile
    failures = []
    cases = {
        # green: named for its subject, and reachable two different ways
        "2026-09-17-wasm-as-an-option.md":
            "# wasm as an option — settled: the boundary is the MicroVM\n\n"
            "Two threads in `#eng-core` (`C0BMX0788F7`), read with `slack_read_thread`.\n",
        # green: a plain public URL is an address
        "2026-09-17-the-vendor-pricing-page.md":
            "# Vendor pricing — metered per checkpoint\n\n"
            "https://docs.example-vendor.io/pricing · opened 2026-09-17\n",
        # green: the unopened backlog, which has no address BY DEFINITION
        "2026-09-17-unopened.md":
            "# Cited and never opened\n\n- the enterprise tier page — would settle the ceiling\n",
    }
    reds = {
        # red 1: the aggregate shape, named by a dump's stamp
        "2026-09-17-211737-references.md": "# References\n\nhttps://example.com/a\n",
        # red 2: dated and topic-shaped, but nothing to get back with
        "2026-09-17-the-restart-argument.md":
            "# The restart argument — settled: TTL goes to 180s\n\n"
            "Priya said the lease dies on restart. Tomas agreed. Decision was 180 seconds.\n",
        # red 3: a generic topic, which names no subject
        "2026-09-17-sources.md": "# Sources\n\nhttps://example.com/b\n",
    }

    with tempfile.TemporaryDirectory() as tmp:
        green = os.path.join(tmp, "green", "reference")
        os.makedirs(green)
        for n, body in cases.items():
            open(os.path.join(green, n), "w").write(body)
        buf = io.StringIO()
        if run(os.path.dirname(green), out=buf) != 0:
            failures.append("green: a correctly written reference/ must pass\n" + buf.getvalue())

        for n, body in reds.items():
            red = os.path.join(tmp, "red-" + n[:24], "reference")
            os.makedirs(red)
            open(os.path.join(red, n), "w").write(body)
            buf = io.StringIO()
            if run(os.path.dirname(red), out=buf) != 1:
                failures.append(f"red {n}: expected a finding\n{buf.getvalue()}")

        bare = os.path.join(tmp, "bare")
        os.makedirs(bare)
        if run(bare, out=io.StringIO()) != 3:
            failures.append("a thread with no reference/ must be exit 3, not a clean 0")

    for f in failures:
        print("FAIL", f, file=sys.stderr)
    print("self-test: " + ("FAILED" if failures
                           else "green, three reds and not-checked all as specified"))
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scope", nargs="?",
                    help="workstream: a thread name, vault-relative path, or absolute path")
    ap.add_argument("--self-test", action="store_true", help="run the hand-audited cases and exit")
    vault_config.add_argument(ap)
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.scope:
        ap.print_usage(sys.stderr)
        print("trace-check: name a workstream, or pass --self-test", file=sys.stderr)
        return 5

    vault = str(vault_config.resolve_or_exit(args.vault, tool="trace-check").path)
    scope = args.scope.rstrip("/")
    for cand in (scope, os.path.join(vault, scope), os.path.join(vault, "workstreams", scope)):
        if os.path.isdir(cand):
            ws = os.path.abspath(cand)
            break
    else:
        print(f"trace-check: no such workstream: {args.scope}", file=sys.stderr)
        return 5
    return run(ws)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
