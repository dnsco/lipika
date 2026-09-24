#!/usr/bin/env python3
"""perf — every skill run and lipika tool call over time, as one HTML page.

One panel per project and operation, in run order, after rue-lang.dev/performance: a trailing
median with an IQR band, version changes as rules, and a point flagged only when it leaves the
trailing dispersion, in either direction.

Sources, none written by an agent:
  skill runs  Claude transcripts, ~/.claude/projects/*/*.jsonl; spans defined in _perf_parse.py
  tool calls  bin/lipika telemetry (_telemetry.py)
  passes      the vault's pass-log.jsonl
  eval runs   <checkout>/evals/results/*/aggregate-result.json

A project is a repo: the cwd's origin remote name, worktrees folded in. The page is a view,
rebuilt from the logs each run; nothing is stored.

USAGE
  lipika perf [--days N] [--project NAME] [--out PATH] [--json]
  lipika perf --self-test

EXIT
  0  wrote the page or JSON, including when nothing was measured
  1  --self-test failed
  5  bad invocation
"""

import argparse
import glob
import html
import json
import math
import re
import os
import statistics
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _perf_parse as pp     # noqa: E402
import _telemetry            # noqa: E402

NORTH_STAR_S = 120
WINDOW, K = 8, 3.0
PROJECTS = os.path.expanduser("~/.claude/projects")


# ---------- statistics ----------

def flag(series, window=WINDOW, k=K):
    """'history' until the window is full, then 'flag' if more than k sigma from its median.

    Sigma is 1.4826 x MAD, floored at 2% of the median so identical values do not flag every wobble.
    """
    out = []
    for i, x in enumerate(series):
        if i < window:
            out.append("history")
            continue
        w = series[i - window:i]
        med = statistics.median(w)
        disp = max(1.4826 * statistics.median(abs(v - med) for v in w), 0.02 * abs(med))
        out.append("flag" if abs(x - med) > k * disp else "ok")
    return out


def trailing(series, window=WINDOW):
    """(median, q1, q3) over the trailing window, or None under three points."""
    out = []
    for i in range(len(series)):
        w = series[max(0, i - window + 1):i + 1]
        if len(w) < 3:
            out.append(None)
            continue
        q = statistics.quantiles(w, n=4, method="inclusive")
        out.append((statistics.median(w), q[0], q[2]))
    return out


def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def version_of(rec):
    return rec.get("version") or "unknown"


def project_of(rec, sessions):
    return project_key(sessions.get(rec.get("session")))


_PROJECT = {}


def project_key(cwd):
    """The origin remote's repo name, else the directory name, worktrees folded in."""
    if not cwd or cwd == "unknown":
        return "unknown"
    if cwd in _PROJECT:
        return _PROJECT[cwd]
    root = cwd.split("/.claude/worktrees/")[0].rstrip("/")
    name = os.path.basename(root) or root
    try:
        url = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"], capture_output=True,
                             text=True, timeout=5).stdout.strip()
        if url:
            name = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1].removesuffix(".git")
    except (OSError, subprocess.SubprocessError):
        pass
    _PROJECT[cwd] = name
    return name


LIPIKA_SKILLS = {p.name for p in (_telemetry.PLUGIN_ROOT / "skills").iterdir() if p.is_dir()} \
    if (_telemetry.PLUGIN_ROOT / "skills").is_dir() else set()


def skill_name(name):
    """`context-dump`, from before the plugin install, is `lipika:context-dump`."""
    return f"lipika:{name}" if name in LIPIKA_SKILLS else name


def group_skills(spans):
    by = {}
    for s in spans:
        by.setdefault((skill_name(s["skill"]), project_key(s["project"])), []).append(s)
    return by


# ---------- gathering ----------

def gather_skills(cutoff):
    spans, sessions = [], {}
    for path in glob.glob(os.path.join(PROJECTS, "*", "*.jsonl")):
        try:
            if os.path.getmtime(path) < cutoff:
                continue
        except OSError:
            continue
        events, _ = pp.transcript_events(path, 0)
        for e in events:
            if e.get("s") and e.get("cwd"):
                sessions.setdefault(e["s"], e["cwd"])
                break
        spans += [s for s in pp.skill_spans(events) if s["start"] >= cutoff]
    return spans, sessions


def gather_telemetry(cutoff):
    rows = []
    for path in sorted(glob.glob(str(_telemetry.state_dir() / "telemetry" / "*.jsonl"))):
        got, _ = pp.jsonl_rows(path)
        rows += [r for r in got if (pp.epoch(r.get("ts")) or 0) >= cutoff]
    return rows


def gather_passes(cutoff, vault_arg):
    try:
        import vault_config
        from span_report import pair_passes
        vault = vault_config.resolve(vault_arg)
    except Exception:
        return [], None
    path = os.path.join(str(vault.path), "pass-log.jsonl")
    recs, _ = pp.jsonl_rows(path)
    done, _ = pair_passes(recs)
    return [(s, e) for s, e in done if (pp.epoch(s.get("ts")) or 0) >= cutoff], path


def gather_evals(cutoff):
    rows = []
    root = _telemetry.PLUGIN_ROOT / "evals" / "results"
    for path in sorted(glob.glob(str(root / "*" / "aggregate-result.json"))):
        try:
            with open(path) as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        ver = next((p.get("version") for p in d.get("suite", {}).get("plugins", [])
                    if p.get("name") == "lipika"), None)
        for c in d.get("cases", []):
            for arm, runs in (c.get("arms") or {}).items():
                for r in runs:
                    t = pp.epoch(r.get("startedAt"))
                    if t and t >= cutoff and r.get("durationSeconds") is not None:
                        rows.append({"case": c.get("name"), "t": t, "s": r["durationSeconds"],
                                     "cost": r.get("costUsd"), "turns": r.get("turns"),
                                     "score": r.get("score"), "version": ver or "unknown"})
    return rows


def pass_session(start, spans):
    """For a pass without `session`: the session of the skill run it started inside."""
    t = pp.epoch(start.get("ts")) or 0
    return next((s["session"] for s in spans if s["start"] - 2 <= t <= s["end"] + 2), None)


def span_version(span, telemetry):
    """The version of any lipika call inside the span."""
    for r in telemetry:
        t = pp.epoch(r.get("ts")) or 0
        if r.get("session") == span["session"] and span["start"] <= t <= span["end"] + 1:
            return version_of(r)
    return "unknown"


# ---------- rendering ----------

CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink-2:#52514e;
--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--band:#cde2fb;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;
--s4:#eda100;--critical:#d03b3b;--ring:rgba(11,11,11,.10)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
--surface-1:#1a1a19;--page:#0d0d0d;--ink:#fff;--ink-2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;
--band:#104281;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--ring:rgba(255,255,255,.10)}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--page:#0d0d0d;--ink:#fff;
--ink-2:#c3c2b7;--grid:#2c2c2a;--axis:#383835;--band:#104281;--s1:#3987e5;--s2:#d95926;--s3:#199e70;
--s4:#c98500;--ring:rgba(255,255,255,.10)}
body{margin:0;background:var(--page)}
.viz-root{font:14px system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:var(--page);
padding:24px;max-width:1100px;margin:auto}
h1{font-size:20px;margin:0 0 4px} h2{font-size:15px;margin:0 0 2px} .sub{color:var(--ink-2);margin:0 0 16px}
.panel{background:var(--surface-1);border:1px solid var(--ring);border-radius:8px;padding:16px;margin:0 0 16px}
.meta{color:var(--ink-2);font-size:12px;margin:0 0 8px} .flagtxt{color:var(--critical)}
svg text{font:11px system-ui,sans-serif;fill:var(--muted);font-variant-numeric:tabular-nums}
table{border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:12px;width:100%}
th,td{text-align:right;padding:3px 8px;border-bottom:1px solid var(--grid)} th:first-child,td:first-child{text-align:left}
th{color:var(--ink-2);font-weight:600} details{margin-top:8px} summary{cursor:pointer;color:var(--ink-2);font-size:12px}
.legend{display:flex;gap:14px;font-size:12px;color:var(--ink-2);margin:4px 0 8px}
a{color:var(--ink-2)} .sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
"""


def fmt_s(s):
    if s is None:
        return "–"
    return f"{s:.0f} s" if s < 600 else f"{s / 60:.1f} min"


def fmt_t(t):
    return time.strftime("%m-%d %H:%M", time.localtime(t))


def scatter(points, reference=None):
    """points: [(t, seconds, version, label)]. Log y; x is run order, not clock time."""
    W, H, L, R, T, B = 1040, 220, 52, 12, 12, 28
    ys = [p[1] for p in points]
    lo = max(1.0, min(ys + ([reference] if reference else [])) / 1.4)
    hi = max(ys + ([reference] if reference else [])) * 1.4
    lg = lambda v: math.log10(max(v, lo))
    ymap = lambda v: T + (H - T - B) * (1 - (lg(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)))
    n = len(points)
    xmap = lambda i: L + (W - L - R) * ((i + 0.5) / n)
    marks, trail = flag(ys), trailing(ys)
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for e in range(int(math.floor(math.log10(lo))), int(math.ceil(math.log10(hi))) + 1):
        for m in (1, 2, 5):
            v = m * 10 ** e
            if lo <= v <= hi:
                y = ymap(v)
                out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--grid)"/>'
                           f'<text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end">{fmt_s(v)}</text>')
    band = [(xmap(i), q) for i, q in enumerate(trail) if q]
    if len(band) > 1:
        top = " ".join(f"{x:.1f},{ymap(q[2]):.1f}" for x, q in band)
        bot = " ".join(f"{x:.1f},{ymap(q[1]):.1f}" for x, q in reversed(band))
        out.append(f'<polygon points="{top} {bot}" fill="var(--band)" opacity=".55"/>')
        med = " ".join(f"{x:.1f},{ymap(q[0]):.1f}" for x, q in band)
        out.append(f'<polyline points="{med}" fill="none" stroke="var(--ink-2)" stroke-width="2"/>')
    if reference:
        y = ymap(reference)
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--muted)" '
                   f'stroke-dasharray="4 4"/><text x="{W - R}" y="{y - 4:.1f}" text-anchor="end">'
                   f'{reference} s target</text>')
    prev = None
    for i, (t, s, ver, label) in enumerate(points):
        if i == 0:
            out.append(f'<text x="{L + 3}" y="{T + 10}">{html.escape(ver)}</text>')
        elif ver != prev:
            x = xmap(i) - (W - L - R) / n / 2
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T}" y2="{H - B}" stroke="var(--axis)"/>'
                       f'<text x="{x + 3:.1f}" y="{T + 10}">{html.escape(ver)}</text>')
        prev = ver
    for i, (t, s, ver, label) in enumerate(points):
        x, y = xmap(i), ymap(s)
        tip = html.escape(f"{fmt_t(t)} · {fmt_s(s)} · {ver} · {label}")
        if marks[i] == "flag":
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="none" stroke="var(--critical)" '
                       f'stroke-width="2"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="var(--s1)" stroke="var(--surface-1)" '
                   f'stroke-width="2"><title>{tip}{" · FLAGGED" if marks[i] == "flag" else ""}</title></circle>')
    out.append(f'<text x="{L}" y="{H - 8}">{fmt_t(points[0][0])}</text>'
               f'<text x="{W - R}" y="{H - 8}" text-anchor="end">{fmt_t(points[-1][0])}</text></svg>')
    return "".join(out), marks


STACK = [("model_s", "model", "--s1"), ("subagent_s", "sub-agents", "--s2"),
         ("other_tools_s", "other tools", "--s3"), ("lipika_s", "lipika tools", "--s4")]


def stack(spans):
    W, H, L, T, B = 1040, 130, 52, 8, 22
    spans = spans[-40:]
    top = max(s["active_s"] for s in spans) or 1
    bw = min(24, (W - L - 12) / len(spans))
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img">']
    for f in (0.5, 1.0):
        y = T + (H - T - B) * (1 - f)
        out.append(f'<line x1="{L}" x2="{W - 12}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--grid)"/>'
                   f'<text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end">{fmt_s(top * f)}</text>')
    for i, s in enumerate(spans):
        x, base = L + i * bw + 1, H - B
        for key, name, var in STACK:
            h = (H - T - B) * s[key] / top
            if h >= 0.5:
                out.append(f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{max(1, bw - 2):.1f}" '
                           f'height="{h:.1f}" fill="var({var})" stroke="var(--surface-1)" stroke-width="1">'
                           f'<title>{html.escape(f"{fmt_t(s["start"])} · {name} {fmt_s(s[key])}")}</title></rect>')
                base -= h
    out.append("</svg>")
    legend = "".join(f'<span><i class="sw" style="background:var({v})"></i>{n}</span>' for _, n, v in STACK)
    return f'<div class="legend">{legend}</div>' + "".join(out)


def table(headers, rows):
    h = "".join(f"<th>{html.escape(x)}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{h}</tr>{b}</table>"


def anchor(title):
    return "p-" + "".join(c if c.isalnum() else "-" for c in title)


def panel(title, points, extra="", reference=None, cols=None):
    svg, marks = scatter(points, reference)
    ys = [p[1] for p in points]
    flagged = [points[i] for i, m in enumerate(marks) if m == "flag"]
    state = ("not enough history -- the trailing window is not full" if len(points) <= WINDOW
             else f'<span class="flagtxt">⚠ {len(flagged)} flagged</span>' if flagged else "no flags")
    meta = (f"n={len(ys)} · median {fmt_s(statistics.median(ys))} · p90 {fmt_s(pct(ys, 90))} · "
            f"range {fmt_s(min(ys))}–{fmt_s(max(ys))} · {state}")
    rows = [(fmt_t(t), fmt_s(s), v, l, marks[i]) for i, (t, s, v, l) in enumerate(points)]
    return (f'<section class="panel" id="{anchor(title)}"><h2>{html.escape(title)}</h2><p class="meta">{meta}</p>{svg}{extra}'
            f'<details><summary>table</summary>{table(cols or ["when", "span", "version", "detail", "mark"], rows[::-1])}'
            f'</details></section>')


def render(skills, passes, tel, evals, sessions, days):
    parts = [f'<div class="viz-root"><h1>lipika performance</h1><p class="sub">last {days} days · '
             f'generated {time.strftime("%Y-%m-%d %H:%M")} · a point is flagged when it is more than '
             f'{K:g}× the trailing dispersion from the trailing median of {WINDOW} runs</p>']
    by = group_skills(skills)
    for key in sorted(by, key=lambda k: (k[1], -len(by[k]))):
        ss = sorted(by[key], key=lambda s: s["start"])
        pts = [(s["start"], max(s["active_s"], 0.5), s["version"], f'ended by {s["ended_by"]}'
                + (f' · owner wait {fmt_s(s["wait_s"])}' if s["wait_s"] else "")) for s in ss]
        parts.append(panel(f"{key[1]} · {key[0]}", pts, stack(ss), NORTH_STAR_S))
    bypass = {}
    for s, e in passes:
        bypass.setdefault((s.get("role"), project_of(s, sessions)), []).append((s, e))
    for key in sorted(bypass, key=lambda k: (k[1], -len(bypass[k]))):
        pts = [(pp.epoch(s["ts"]), max(e["span_s"], 0.5), version_of(e), s.get("scope") or "vault")
               for s, e in bypass[key]]
        parts.append(panel(f"{key[1]} · pass {key[0]} (pass-log)", pts, "", NORTH_STAR_S))
    bycase = {}
    for r in evals:
        bycase.setdefault(r["case"], []).append(r)
    for case, rs in sorted(bycase.items()):
        rs.sort(key=lambda r: r["t"])
        pts = [(r["t"], r["s"], r["version"], f'${r["cost"] or 0:.2f} · {r["turns"]} turns · score {r["score"]}')
               for r in rs]
        parts.append(panel(f"lipika · eval {case}", pts))
    if tel:
        groups = {}
        for r in tel:
            groups.setdefault((r.get("cmd"), r.get("verb") or "", version_of(r)), []).append(r["ms"])
        rows = [(f"{c} {v}".strip(), ver, len(ms), f"{pct(ms, 50):.0f}", f"{pct(ms, 95):.0f}")
                for (c, v, ver), ms in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
        parts.append('<section class="panel"><h2>lipika tools</h2><p class="meta">every call through '
                     f'<code>bin/lipika</code> · {len(tel)} calls</p>'
                     + table(["command", "version", "calls", "p50 ms", "p95 ms"], rows) + "</section>")
    else:
        parts.append('<section class="panel"><h2>lipika tools</h2><p class="meta">no telemetry yet -- '
                     'it starts with the first call through a dispatcher that records it</p></section>')
    if not (skills or passes or evals):
        parts.append('<p class="sub">NOTHING WAS MEASURED in this window.</p>')
    titles = [t for t in re.findall(r'<section class="panel" id="[^"]*"><h2>([^<]*)</h2>', "".join(parts))]
    index = {}
    for t in titles:
        proj, _, rest = html.unescape(t).partition(" · ")
        index.setdefault(proj, []).append((rest, t))
    nav = "".join(f'<p class="meta"><b>{html.escape(p)}</b> · ' + " · ".join(
        f'<a href="#{anchor(html.unescape(t))}">{html.escape(r)}</a>' for r, t in items) + "</p>"
        for p, items in index.items())
    parts.insert(1, f'<section class="panel">{nav}</section>')
    parts.append("</div>")
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>lipika performance</title>"
            f"<style>{CSS}</style></head><body>{''.join(parts)}</body></html>")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--project", help="only skill runs and passes whose project contains this")
    ap.add_argument("--out", default=os.path.expanduser("~/.cache/lipika/perf.html"))
    ap.add_argument("--json", action="store_true", help="print the rows instead of writing the page")
    ap.add_argument("--vault", help="override the resolved vault, for the pass log")
    ap.add_argument("--self-test", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 5
    if args.self_test:
        test = _telemetry.PLUGIN_ROOT / "evals" / "perf" / "test_perf.py"
        return subprocess.call([sys.executable, str(test)])

    cutoff = time.time() - args.days * 86400
    skills, sessions = gather_skills(cutoff)
    tel = gather_telemetry(cutoff)
    passes, log = gather_passes(cutoff, args.vault)
    evals = gather_evals(cutoff)
    for s in skills:
        s["skill"] = skill_name(s["skill"])
        v = span_version(s, tel) if s["skill"].startswith("lipika:") else "unknown"
        if s["version"] in ("unknown", "unversioned") and v != "unknown":
            s["version"] = v
    for st, _ in passes:
        if not st.get("session"):
            st["session"] = pass_session(st, skills)
    if args.project:
        skills = [s for s in skills if args.project in project_key(s["project"])]
        passes = [(s, e) for s, e in passes if args.project in project_of(s, sessions)]

    if args.json:
        json.dump({"skills": skills, "passes": [e for _, e in passes], "tools": tel, "evals": evals},
                  sys.stdout, indent=1)
        print()
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write(render(skills, passes, tel, evals, sessions, args.days))
    print(f"wrote {args.out}")
    print(f"  {len(skills)} skill run(s) from transcripts · {len(passes)} pass(es) from "
          f"{log or 'no vault'} · {len(tel)} tool call(s) · {len(evals)} eval run(s)")
    if not log:
        print("  pass log NOT read -- no vault resolved; pass --vault")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
