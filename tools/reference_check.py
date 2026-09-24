#!/usr/bin/env python3
"""reference-check — external URLs a thread cites but no `reference/` trace carries.

WHY THIS EXISTS
  Measured 2026-09-17 on workstreams/2026-09-16-can-agentomatic-host-workloads: five dumps and three
  orientations built from a doc site, a gist, thirteen Slack messages, a repo branch and two vendor
  pages named none of them, and when the owner asked outright, the inventory landed in `dumps/` under
  frontmatter typing itself `type: reference`. Vault-wide, `reference/` had fired in 2 of 14 threads.

  `context-dump` step 2a now names the destination: the URL lives in
  `workstreams/<ws>/reference/YYYY-MM-DD-references.md` and a dump cites the trace. So a URL left
  inline in a dump, or dropped when a newer trace was written, is a mechanical finding -- which is
  the half of this that a tool can see.

WHAT IT CANNOT SEE, AND THIS IS THE IMPORTANT PART
  It cannot catch a dump that never wrote the link at all. With no URL there is nothing to flag, so
  the thread that motivated the whole change would have exited 0 at the time. **A clean exit is not a
  clean bill.** That failure is covered by prose in the skill and by a hand-scored grader
  (evals/external-references/graders/r1-*), and nothing can do better: no tool sees what a session
  read and did not write down.

EXCLUSION CLASSES, printed before the findings the way dangling_links.py prints its own. A check that
stays red on correct content gets dismissed, so the known false positives are named rather than left
to drown the real ones:
  forge        all of github.com -- a repository is a code-repo path, and those are named
               literally with the repo, per the conventions. gist.github.com and *.github.io are
               NOT here: different hosts, and both are documents.
  local        localhost, 127.0.0.1, 0.0.0.0 -- a dev server is not a reference
  placeholder  <url>, example.com, and anything holding an angle bracket -- template text

  Vault-root `reference/` counts as carrying a URL, not just the thread's own: a cross-thread trace
  lives there by convention, with `about:` naming the thread.

CONTRACT
  exit 0  no untraced external URL
  exit 1  at least one -- read the exclusion classes before believing it
  exit 3  NOTHING WAS CHECKED -- the thread has no dumps/ or orientation/ to scan
  exit 5  bad invocation
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_config                               # noqa: E402

URL = re.compile(r"https?://[^\s<>\"'`)\]}|]+")
# All of github.com, not just its PR and commit paths. A repository is a code-repo path, which the
# conventions already cover -- "literal text for code-repo paths, with the repo named" -- so a clone
# URL is not an external reference. A bare clone URL, `https://github.com/dnsco/lipika.git`, was this
# tool's only false positive across six threads.
# `gist.github.com` and `*.github.io` are DIFFERENT HOSTS and are not excluded: a gist and a
# rendered Pages site are documents, and both are in the case this check was built for.
FORGE = re.compile(r"^https?://(www\.)?github\.com(/|$)", re.I)
LOCAL = re.compile(r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:|/|$)", re.I)
PLACEHOLDER = re.compile(r"(^https?://(www\.)?example\.(com|org|net)\b)|[<>]", re.I)
TRAILING = ".,;:!?)\"'`*_]}>"


def normalise(raw):
    """A URL as written, minus markdown punctuation that is not part of it."""
    u = raw.strip()
    while u and u[-1] in TRAILING:
        u = u[:-1]
    return u


def forms(url):
    """The URL plus its fragment- and query-stripped forms.

    A dump citing `…/m2/workflow-engine.md#tasks` is carried by a trace listing the page itself.
    Matching only verbatim would report that as untraced, which is the false positive most likely
    to get this tool switched off.
    """
    out = [url]
    for cut in ("#", "?"):
        if cut in url:
            out.append(url.split(cut, 1)[0])
    return out


def md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for f in sorted(filenames):
            if f.endswith(".md"):
                yield os.path.join(dirpath, f)


FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def outside_fences(text):
    """(lineno, line) for every line NOT inside a fenced code block.

    A URL in a fenced block is a COMMAND, not a citation. Measured 2026-09-17: this check flagged

        curl -s -A "<agent>" "https://crates.io/api/v1/crates/wrpc-transport/reverse_dependencies"

    out of a dump's own `Reusable commands` block, and reaching exit 0 meant appending a
    verbatim-URL section to a trace for a URL that was never a source for that trace's subject.
    **The check pushed the record toward a small dishonesty**, which is a worse failure than the one
    it exists to catch.

    Inline backticks are deliberately NOT stripped. A trace's required header line is
    `` `<url>` · opened <date> · <route> `` -- the URL in backticks is the citation form, so
    stripping them here would turn a false positive into a silent false negative, and losing a
    reference is the failure this tool exists for.
    """
    inside, marker = False, ""
    for i, line in enumerate(text.splitlines(), 1):
        m = FENCE.match(line)
        if m:
            if not inside:
                inside, marker = True, m.group(1)[0]
            elif m.group(1)[0] == marker:
                inside = False
            continue
        if not inside:
            yield i, line


def scan(paths):
    """Every URL in those files, as {url: [(relpath, lineno)]}, first occurrence order."""
    found = {}
    for p in paths:
        try:
            text = open(p, errors="replace").read()
        except OSError:
            continue
        for i, line in outside_fences(text):
            for raw in URL.findall(line):
                u = normalise(raw)
                if u:
                    found.setdefault(u, []).append((p, i))
    return found


def classify(url):
    if PLACEHOLDER.search(url):
        return "placeholder"
    if LOCAL.match(url):
        return "local"
    if FORGE.match(url):
        return "forge"
    return None


def run(ws, vault, out=sys.stdout):
    cited_dirs = [os.path.join(ws, d) for d in ("dumps", "orientation")]
    cited_dirs = [d for d in cited_dirs if os.path.isdir(d)]
    if not cited_dirs:
        print(f"NOT CHECKED: no dumps/ or orientation/ under {ws}", file=out)
        return 3

    trace_dirs = [os.path.join(ws, "reference"), os.path.join(vault, "reference")]
    trace_text = ""
    trace_count = 0
    for d in trace_dirs:
        if not os.path.isdir(d):
            continue
        for p in md_files(d):
            trace_count += 1
            trace_text += open(p, errors="replace").read()

    cited = scan(p for d in cited_dirs for p in md_files(d))
    excluded = {"forge": [], "local": [], "placeholder": []}
    untraced = []
    traced = 0
    for url, hits in cited.items():
        kind = classify(url)
        if kind:
            excluded[kind].append((url, hits))
            continue
        if any(f in trace_text for f in forms(url)):
            traced += 1
        else:
            untraced.append((url, hits))

    rel = lambda p: os.path.relpath(p, ws)                             # noqa: E731
    for kind in ("forge", "local", "placeholder"):
        print(f"-- excluded ({kind}): {len(excluded[kind])}", file=out)
        for url, hits in excluded[kind]:
            print(f"     {url}   {rel(hits[0][0])}:{hits[0][1]}", file=out)
    print(f"\n-- reference/ documents scanned: {trace_count}"
          f"   ({os.path.basename(ws)}/reference + vault reference/)", file=out)
    print(f"-- external URLs carried by a trace: {traced}", file=out)

    print(f"\n== UNTRACED: {len(untraced)}", file=out)
    for url, hits in untraced:
        print(f"   {url}", file=out)
        for p, i in hits:
            print(f"       {rel(p)}:{i}", file=out)
    if untraced:
        print("\nThese belong in workstreams/<ws>/reference/YYYY-MM-DD-references.md, cited from the\n"
              "dump rather than repeated in it. Correct an existing trace with a NEWER dated one.\n"
              "Nothing here reports what this thread read and never wrote down.", file=out)
    return 1 if untraced else 0


def self_test():
    """A red thread and a green one, built from scratch. Named cases, not a smoke test."""
    import tempfile
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, trace in (("red", None), ("green", "https://docs.example-vendor.io/workflows")):
            ws = os.path.join(tmp, "workstreams", name)
            os.makedirs(os.path.join(ws, "dumps"))
            with open(os.path.join(ws, "dumps", "2026-09-17-000000-x.md"), "w") as fh:
                fh.write("- engine picked — https://docs.example-vendor.io/workflows\n"
                         "- merged https://github.com/org/repo/pull/41\n"
                         "- dev at http://localhost:3000\n")
            if trace:
                os.makedirs(os.path.join(ws, "reference"))
                with open(os.path.join(ws, "reference", "2026-09-17-references.md"), "w") as fh:
                    fh.write(f"## Read\n- **vendor docs** — settled the engine. `{trace}` · opened 2026-09-17\n")
            import io
            buf = io.StringIO()
            code = run(ws, tmp, out=buf)
            want = 1 if name == "red" else 0
            if code != want:
                failures.append(f"{name}: exit {code}, expected {want}\n{buf.getvalue()}")
            if "github.com/org/repo/pull/41" not in buf.getvalue():
                failures.append(f"{name}: the forge URL was not reported as excluded")
            if "localhost" not in buf.getvalue():
                failures.append(f"{name}: the local URL was not reported as excluded")
        # A third case, hand-audited: a dump whose ONLY external URL is inside a fenced command
        # block, and no trace at all. Red before 2026-09-24, green after -- the URL is an
        # incantation to re-run, not a source to re-open, and demanding a trace for it is what
        # produced a falsified one.
        fenced = os.path.join(tmp, "workstreams", "fenced")
        os.makedirs(os.path.join(fenced, "dumps"))
        with open(os.path.join(fenced, "dumps", "2026-09-17-000000-x.md"), "w") as fh:
            fh.write("## Reusable commands\n\n```bash\n"
                     'curl -s "https://crates.io/api/v1/crates/x/reverse_dependencies"\n'
                     "```\n")
        import io
        buf = io.StringIO()
        if run(fenced, tmp, out=buf) != 0:
            failures.append("a URL inside a fenced block must not be reported as untraced\n"
                            + buf.getvalue())

        # And its own red partner: the SAME URL in prose, with no trace, still fails. A check that
        # went green on both would have stopped measuring anything.
        prose = os.path.join(tmp, "workstreams", "prose")
        os.makedirs(os.path.join(prose, "dumps"))
        with open(os.path.join(prose, "dumps", "2026-09-17-000000-x.md"), "w") as fh:
            fh.write("- the dependents list settled it — "
                     "https://crates.io/api/v1/crates/x/reverse_dependencies\n")
        buf = io.StringIO()
        if run(prose, tmp, out=buf) != 1:
            failures.append("the same URL in prose, untraced, must still be reported\n"
                            + buf.getvalue())

        empty = os.path.join(tmp, "workstreams", "empty")
        os.makedirs(empty)
        import io
        if run(empty, tmp, out=io.StringIO()) != 3:
            failures.append("a thread with no dumps/ must be exit 3, not a clean 0")
    for f in failures:
        print("FAIL", f, file=sys.stderr)
    print("self-test: " + ("FAILED" if failures else "red, green and not-checked all as specified"))
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scope", nargs="?",
                    help="workstream: a thread name, vault-relative path, or absolute path")
    ap.add_argument("--self-test", action="store_true", help="run the red and green cases and exit")
    vault_config.add_argument(ap)
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.scope:
        ap.print_usage(sys.stderr)
        print("reference-check: name a workstream, or pass --self-test", file=sys.stderr)
        return 5

    vault = str(vault_config.resolve_or_exit(args.vault, tool="reference-check").path)
    scope = args.scope.rstrip("/")
    for cand in (scope, os.path.join(vault, scope), os.path.join(vault, "workstreams", scope)):
        if os.path.isdir(cand):
            ws = os.path.abspath(cand)
            break
    else:
        print(f"reference-check: no such workstream: {args.scope}", file=sys.stderr)
        return 5
    return run(ws, vault)


if __name__ == "__main__":
    sys.exit(main())
