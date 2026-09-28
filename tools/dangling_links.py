#!/usr/bin/env python3
"""Vault-wide dangling-[[link]] sweep.

Skips fenced code blocks and inline code spans -- Obsidian renders no wikilink inside
code, so a wikilink there is not a link. Then classifies what is left, because three
classes are known false positives and would otherwise drown the real findings:
  prose   generic words used as examples of the syntax ([[links]], [[wikilink]])
  tool    tools/*.py targets -- real files, just not notes
  memory  project-memory notes wikilinked as if they were vault docs
A name that is BOTH a memory note and a real vault doc is NOT excluded.

Given a subdirectory, it scans only that subdirectory but resolves links against the whole git
repository holding it. With no argument it scans the configured vault.

Linked worktrees under the vault root are skipped: they are other trees, and resolving
against them answers about the wrong one.

NOT A SUBSTITUTE FOR `obsidian.py unresolved`, NOR IT FOR THIS. Each is blind to a class the
other catches, so a thorough sweep runs both. The index sees `links:`-style FRONTMATTER link
fields, which this never scans; this has exclusion classes (prose examples, tools/*.py
targets, project-memory notes) the index has no concept of. Measured 2026-08-18 on one vault:
this reported 0 dangling while the index reported 6 unresolved, and both were right.
"""
import re, subprocess, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import vault_config  # noqa: E402

if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
    print("usage: dangling_links.py [dir] [memory-dir]\n"
          "  dir defaults to the configured vault; a subdirectory resolves against its repository\n"
          "  exit 0 = no dangling links, 1 = at least one (read the classes it excluded)")
    sys.exit(0)

scan = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else vault_config.resolve().path).resolve()
if not scan.is_dir():
    sys.exit(f"not a directory: {scan}")
top = subprocess.run(["git", "-C", str(scan), "rev-parse", "--show-toplevel"],
                     capture_output=True, text=True).stdout.strip()
root = pathlib.Path(top).resolve() if top else scan
memdir = pathlib.Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else None

SKIP_DIRS = {".git", "obsidian-skills", ".obsidian", "node_modules"}
# Linked worktrees live under the vault root and are OTHER trees. Walking them reported every
# finding once per worktree, and -- worse, because it is silent -- put docs existing only in a
# worktree into the resolved-notes set, so a genuinely dangling link resolved against a tree
# the caller never asked about. Same answering-about-the-wrong-tree failure the Obsidian
# wrapper refuses with exit 4, in the tool that exists to be the worktree-safe fallback.
SKIP_PREFIXES = {(".claude", "worktrees")}
PROSE = {"links", "link", "wikilink", "wikilinks", "pointer", "pointers", "pointer]]",
         "name", "their-name", "links]]"}

def md_files(base):
    for p in base.rglob("*.md"):
        parts = p.relative_to(base).parts
        if SKIP_DIRS & set(parts):
            continue
        if any(parts[:len(pre)] == pre for pre in SKIP_PREFIXES):
            continue
        yield p

notes = {p.stem for p in md_files(root)}
notes_lc = {n.lower() for n in notes}
tool_files = {p.name for p in (root / "tools").glob("*")} if (root / "tools").is_dir() else set()
mem_notes = {p.stem for p in memdir.glob("*.md")} if memdir and memdir.is_dir() else set()

FENCE = re.compile(r"^\s*(```|~~~)")
WIKI = re.compile(r"\[\[([^\]\n]+)\]\]")

def strip_inline_code(line):
    return re.sub(r"`[^`\n]*`", "", line)

findings = {"dangling": [], "prose": [], "tool": [], "memory": []}

for p in sorted(md_files(scan)):
    in_fence = False
    for i, raw in enumerate(p.read_text(errors="replace").splitlines(), 1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in WIKI.findall(strip_inline_code(raw)):
            name = target.split("|")[0].split("#")[0].strip()
            name = name.split("/")[-1]
            if not name:
                continue
            base = name[:-3] if name.endswith(".md") else name
            if base in notes or base.lower() in notes_lc:
                continue
            rel = p.relative_to(root)
            item = (str(rel), i, target)
            if name in tool_files or name.endswith(".py"):
                findings["tool"].append(item)
            elif base in mem_notes:
                findings["memory"].append(item)
            elif base.lower() in PROSE:
                findings["prose"].append(item)
            else:
                findings["dangling"].append(item)

for k in ("prose", "tool", "memory"):
    print(f"-- excluded ({k}): {len(findings[k])}")
    for f, i, t in findings[k]:
        print(f"     {f}:{i}  [[{t}]]")
print(f"\n== DANGLING: {len(findings['dangling'])}")
for f, i, t in findings["dangling"]:
    print(f"   {f}:{i}  [[{t}]]")
sys.exit(1 if findings["dangling"] else 0)
