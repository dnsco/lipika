#!/usr/bin/env python3
"""stamp — the UTC filename stamp for a new orientation or dump, checked against what is already there.

WHY THIS EXISTS
  `pickup` opens the LAST orientation by name, so a handoff that does not sort last is never read --
  and the failure is silent at every step: the file writes, the commit succeeds, the handoff reports
  done, and the next session reads a stale document.

  **A name is a UTC timestamp, and the seconds are there so it is always a truthful one.**

  Measured 2026-08-21: agents had been inventing names. Of four orientations on one thread only the
  first was a real time -- 1930 was written at 18:10Z, 2015 at 18:13Z (three minutes after 1930),
  2100 at 19:32Z. Each agent picked a number bigger than the last, so the names ratcheted up to 121
  minutes ahead of the clock and a truthful stamp could no longer sort last.

  The first version of this tool offered --after, which stepped past the newest name. That was the
  wrong fix: it made inventing a number the sanctioned path and guaranteed the drift never healed.
  It is gone. Minute-resolution names were the other half of the problem -- two handoffs in one
  minute forced a tie-break, and a tie-break is an invented number. Seconds remove the tie.

  A name that cannot sort last is now an ANOMALY to report, not a case to route around. It means an
  existing name is ahead of the clock, and it heals by itself as real time advances.

CONTRACT

  exit 0  the stamp is printed on stdout, and (with --for) it sorts last in that directory
  exit 1  the stamp would NOT sort last -- an existing name is ahead of the clock. Reports how long
          until it heals. Do not invent a name; wait, or fix the name that is wrong.
  exit 5  bad invocation

  A `reference/` target is the exception, and it is not a special case so much as a different
  question. A trace is `YYYY-MM-DD-<topic>.md` -- the conventions say so and so does the shape block
  in `context-dump` -- because nothing reads "the newest trace": they are addressed by subject, and
  several land on one day. So there is no sort-last property to check, and checking one would refuse
  every trace after the first each day. Measured 2026-09-17, following the step as written: the tool
  returned `2026-09-17-230233` for a `reference/` target and the two traces written that pass were
  renamed by hand against the diagram.

USAGE
  lipika stamp                                   # 2026-08-21-205131
  lipika stamp --date                            # 2026-08-21
  lipika stamp --for workstreams/<ws>/orientation      # stamp, checked against what is there
  lipika stamp --for workstreams/<ws>/reference        # 2026-08-21 -- date only, no sort check
"""

import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_config     # noqa: E402

# A leading YYYY-MM-DD-HHMM or YYYY-MM-DD. Anything else in the directory is not a stamped
# document and cannot be sorted against -- README.md in an orientation folder is not a rival.
STAMPED = re.compile(r"^(\d{4}-\d{2}-\d{2}(?:-\d{4,6})?)")

# Directories whose documents are dated to the DAY and addressed by subject. `orientation/` and
# `dumps/` are the opposite: one of them is read by being newest, and both can land twice in a
# minute, which is what the seconds are for.
DATE_ONLY_DIRS = {"reference"}


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def stamp(now, date_only=False):
    return now.strftime("%Y-%m-%d" if date_only else "%Y-%m-%d-%H%M%S")


def _heals_in(newest, now):
    """Minutes until a truthful stamp would sort after `newest`, or None if it never will.

    An ahead-of-clock name is temporary by construction: real time keeps advancing and the name
    does not. Saying WHEN turns a refusal into a wait instead of an invitation to invent."""
    for fmt in ("%Y-%m-%d-%H%M%S", "%Y-%m-%d-%H%M", "%Y-%m-%d"):
        try:
            t = datetime.datetime.strptime(newest, fmt).replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
        return max(0, int((t - now).total_seconds() // 60) + 1)
    return None


def existing_stamps(dirpath):
    """Every leading stamp already in the directory, as strings. Missing directory is not an
    error -- a thread's first orientation has nothing to sort against, which is the normal case."""
    try:
        names = os.listdir(dirpath)
    except FileNotFoundError:
        return []
    out = []
    for n in sorted(names):
        if n.startswith("."):
            continue
        m = STAMPED.match(n)
        if m:
            out.append((m.group(1), n))
    return out


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    ap.add_argument("--date", action="store_true",
                    help="YYYY-MM-DD only, for a document dated to the day")
    ap.add_argument("--for", dest="target", metavar="DIR",
                    help="check the stamp sorts last in this directory (vault-relative or absolute)")
    ap.add_argument("--vault", help="override the resolved vault")
    args = ap.parse_args(argv)

    now = utc_now()

    # A target the conventions date to the DAY, not to the second. Keyed on the directory's own
    # name rather than on a flag, because the caller following step 2a has a path in hand and no
    # reason to know which resolution that path wants -- and a step that hands you a tool whose
    # answer you then have to correct by hand is the step failing, not the caller.
    date_only = args.date or (args.target is not None and
                              os.path.basename(str(args.target).rstrip("/")) in DATE_ONLY_DIRS)
    s = stamp(now, date_only)

    if not args.target:
        print(s)
        return 0

    if date_only and not args.date:
        # No sort-last check: several traces land on one day by design, so every one after the
        # first would be refused for colliding with a name that is not its rival.
        print(s)
        print(f"date only -- a trace in {args.target} is addressed by subject, not by being newest."
              "\nName it YYYY-MM-DD-<topic>.md, where <topic> is what the trace is ABOUT.",
              file=sys.stderr)
        return 0

    target = args.target
    if not os.path.isabs(target):
        vault = vault_config.resolve_or_exit(args.vault, "stamp")
        target = os.path.join(str(vault.path), target)

    found = existing_stamps(target)
    # Compare on the leading stamp, string-wise, because that is how pickup picks the newest.
    # At seconds resolution a genuine tie needs two handoffs in the same second; anything blocking
    # here is a name that is ahead of the clock, which is a fact about the directory, not the clock.
    blocking = [(st, n) for st, n in found if st >= s]

    if blocking:
        print(s)
        print(f"\nthis stamp does NOT sort last in {args.target}", file=sys.stderr)
        for st, n in blocking:
            rel = "same minute" if st == s else "sorts after"
            print(f"  {n}   ({rel})", file=sys.stderr)
        newest = max(st for st, _ in blocking)
        heals = _heals_in(newest, now)
        print("\n  A new orientation must sort last by name or `pickup` will not read it.",
              file=sys.stderr)
        print(f"  An existing name is AHEAD OF THE CLOCK. UTC now is {s}.", file=sys.stderr)
        if heals is not None:
            print(f"  This heals by itself in ~{heals} minute(s), when real time passes {newest}.",
                  file=sys.stderr)
        print("  Do NOT invent a later name. That is how the drift above was created: each agent"
              "\n  picked a number bigger than the last, and the names ran up to 121 minutes ahead"
              "\n  of real time. Wait, or correct the name that is wrong.", file=sys.stderr)
        return 1

    print(s)
    if found:
        print(f"sorts after {found[-1][1]}  ({len(found)} stamped here)", file=sys.stderr)
    else:
        print(f"nothing stamped in {args.target} yet -- this would be the first", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BrokenPipeError:
        sys.exit(0)
