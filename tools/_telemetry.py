"""Telemetry: one appended line per `lipika` call.

- Written by `bin/lipika`, so every tool is timed and a new tool needs nothing. The tool writes
  it, not an agent, which keeps it inside the 2026-08-19 ruling against agents emitting metrics.
- Record: ts, cmd, verb, ms, exit, version, session, pid. `verb` is the first argument only when
  it is a bare word (`start`, `path`); other arguments are never recorded.
- No project field: the skills `cd` into the vault first. `lipika perf` resolves the project
  from `session`.
- Path: $LIPIKA_STATE_DIR, else $XDG_STATE_HOME/lipika, else ~/.local/state/lipika; then
  telemetry/<YYYY-MM>.jsonl. One O_APPEND write under PIPE_BUF, so concurrent writers do not
  interleave.
- Never breaks a tool: every failure is swallowed. LIPIKA_TELEMETRY=0 turns it off.
"""

import json
import os
import re
import time
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
VERB = re.compile(r"^[a-z][a-z-]{0,23}$")


def enabled():
    return os.environ.get("LIPIKA_TELEMETRY", "1") != "0"


def state_dir():
    d = os.environ.get("LIPIKA_STATE_DIR")
    if d:
        return Path(d)
    xdg = os.environ.get("XDG_STATE_HOME")
    return Path(xdg) / "lipika" if xdg else Path.home() / ".local" / "state" / "lipika"


def version():
    """The running copy's manifest version."""
    try:
        with open(PLUGIN_ROOT / ".claude-plugin" / "plugin.json") as fh:
            return json.load(fh).get("version") or "unknown"
    except (OSError, ValueError):
        return "unknown"


def session():
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or None


def verb_of(args):
    return args[0] if args and VERB.match(args[0]) else None


def record(cmd, args, ms, exit_code):
    if not enabled():
        return
    try:
        now = time.time()
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now)) + f".{int(now % 1 * 1000):03d}Z",
               "cmd": cmd, "verb": verb_of(args), "ms": round(ms, 1), "exit": exit_code,
               "version": version(), "session": session(), "pid": os.getpid()}
        d = state_dir() / "telemetry"
        d.mkdir(parents=True, exist_ok=True)
        line = (json.dumps(rec, separators=(",", ":")) + "\n").encode()
        fd = os.open(d / time.strftime("%Y-%m.jsonl", time.gmtime(now)),
                     os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, line)
        finally:
            os.close(fd)
    except Exception:
        pass
