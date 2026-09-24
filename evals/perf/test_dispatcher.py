#!/usr/bin/env python3
"""Graders for the timing `bin/lipika` adds around every tool.

Written before the change. Builds a throwaway plugin root -- a copy of `bin/lipika`, the real
`tools/_telemetry.py`, a manifest and one fixture tool -- so it tests the dispatcher, not the tools.
Run: `python3 evals/perf/test_dispatcher.py`. Exit 0 all pass, 1 any fail.
"""

import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

FIXTURE_TOOL = '''"""exit-with -- a fixture."""
import sys
if sys.argv[1:2] == ["echo"]:
    sys.stdout.write(sys.stdin.read())
    raise SystemExit(0)
raise SystemExit(int(sys.argv[1]))
'''

failures = []


def check(name, cond, detail=""):
    print(("ok    " if cond else "FAIL  ") + name + (f"  -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def build(root):
    os.makedirs(os.path.join(root, "bin"))
    os.makedirs(os.path.join(root, "tools"))
    os.makedirs(os.path.join(root, ".claude-plugin"))
    shutil.copy(os.path.join(REPO, "bin", "lipika"), os.path.join(root, "bin", "lipika"))
    tel = os.path.join(REPO, "tools", "_telemetry.py")
    if os.path.exists(tel):
        shutil.copy(tel, os.path.join(root, "tools", "_telemetry.py"))
    with open(os.path.join(root, "tools", "exit_with.py"), "w") as fh:
        fh.write(FIXTURE_TOOL)
    with open(os.path.join(root, ".claude-plugin", "plugin.json"), "w") as fh:
        json.dump({"name": "lipika", "version": "9.9.9"}, fh)
    return os.path.join(root, "bin", "lipika")


def run(lipika, args, env, stdin=None):
    return subprocess.run([sys.executable, lipika, *args], env=env, input=stdin,
                          capture_output=True, text=True)


def records(state):
    d = os.path.join(state, "telemetry")
    out = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            with open(os.path.join(d, f)) as fh:
                out += [json.loads(line) for line in fh if line.strip()]
    return out


def main():
    with tempfile.TemporaryDirectory() as root:
        lipika = build(root)
        state = os.path.join(root, "state")
        env = dict(os.environ, LIPIKA_STATE_DIR=state, CLAUDE_CODE_SESSION_ID="sess-1")
        env.pop("LIPIKA_TELEMETRY", None)

        for code in (0, 1, 2, 3, 5):
            r = run(lipika, ["exit-with", str(code)], env)
            check(f"exit {code} passes through", r.returncode == code, r.returncode)
        r = run(lipika, ["exit-with", "echo"], env, stdin="hello\n")
        check("stdin and stdout pass through", r.stdout == "hello\n", repr(r.stdout))

        recs = records(state)
        check("one record per call", len(recs) == 6, len(recs))
        if recs:
            last = recs[-1]
            want = {"ts", "cmd", "verb", "ms", "exit", "version", "session", "pid"}
            check("a record carries the named fields", want <= set(last), sorted(set(last)))
            check("cmd is the command name", last.get("cmd") == "exit-with", last.get("cmd"))
            check("version is the running copy's manifest", last.get("version") == "9.9.9")
            check("session is the Claude session id", last.get("session") == "sess-1")
            check("exit is recorded", recs[1].get("exit") == 1, recs[1].get("exit"))
            check("verb is a bare first word", last.get("verb") == "echo", last.get("verb"))
        r = run(lipika, ["exit-with", "--secret=/private/path"], env)
        leaked = [x for x in records(state) if "/private/path" in json.dumps(x)]
        check("no argument beyond the verb is recorded", not leaked, leaked)

        # An unwritable state dir: a regular file where the directory should be.
        blocked = os.path.join(root, "blocked")
        open(blocked, "w").close()
        env_b = dict(env, LIPIKA_STATE_DIR=blocked)
        r = run(lipika, ["exit-with", "echo"], env_b, stdin="x\n")
        check("an unwritable telemetry dir changes neither output nor exit",
              r.returncode == 0 and r.stdout == "x\n" and r.stderr == "", (r.returncode, r.stderr))

        env_off = dict(env, LIPIKA_TELEMETRY="0", LIPIKA_STATE_DIR=os.path.join(root, "off"))
        run(lipika, ["exit-with", "0"], env_off)
        check("LIPIKA_TELEMETRY=0 writes nothing", records(os.path.join(root, "off")) == [])

        # Overhead: telemetry on against off, where off is the old exec path.
        def med(e):
            xs = []
            for _ in range(20):
                t = time.perf_counter()
                run(lipika, ["exit-with", "0"], e)
                xs.append(time.perf_counter() - t)
            return statistics.median(xs)
        on, off = med(env), med(env_off)
        delta_ms = (on - off) * 1000
        print(f"      overhead: {delta_ms:.1f} ms median (on {on * 1000:.1f}, off {off * 1000:.1f})")
        check("added overhead under 20 ms", delta_ms < 20, f"{delta_ms:.1f} ms")

    print(f"\n{len(failures)} failed" if failures else "\nall passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
