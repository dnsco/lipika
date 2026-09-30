#!/usr/bin/env python3
"""
Where the vault is, and the numbers that govern it — resolved once, imported by every tool.

WHY THIS FILE EXISTS
  This machinery used to live *inside* the vault it maintains, so every tool could assume the
  vault was the current directory (`--vault default="."`) and every definition could name a
  literal path. Both assumptions are now wrong: the tools live in their own repo, and the
  definitions are shared with anyone who installs the plugin.

  The mechanism that papered over this was a placeholder substitution — a token in the text of
  every definition, replaced when the files were copied into a vault. It broke in a new way
  almost every time it was touched, and the last count was six files needing hand-ports. One
  copy plus one resolver removes the need for it entirely, which is the point of this file.

  The second job is the tunables. A budget written in prose gets read past; the same budget in
  a config a tool reads has an exit code behind it. Measured repeatedly in this project's own
  history, which is why the numbers live here rather than in a document.

THE CHAIN, first hit wins
  1. an explicit `--vault` (or `vault=` argument)   — the caller knows
  2. $LIPIKA_VAULT                                  — the session knows
  3. ~/.config/lipika/config.json                   — the machine knows
  4. the current git checkout, if it looks like a vault

  **A tool that cannot resolve a vault refuses.** It does not fall back to the current
  directory and hope, because the failure mode of guessing is an agent curating the wrong tree
  and reporting success — which is exactly the class of silent success this project keeps
  measuring. `resolve()` raises; the CLI exits non-zero.

CONFIG SHAPE
  {
    "default": "ai_docs",
    "vaults":  {"ai_docs": "/Users/you/workspace/ai_docs"},
    # Only the roles somebody WAITS on carry a ceiling. The background roles had 300 s and 480 s
    # and never met either, on any pass ever measured -- and a ceiling nothing meets makes an
    # honest report read as a failure, so one was overridden twice in a single run by an agent
    # that had priced the overrun correctly. They carry observed baselines instead (see
    # `span_baselines_s` in the config), which say "beat this" rather than "you have failed".
    "spans_s": {"context-dump": 120, "frontier-clerk": 120},
    "frozen_tiers": ["done", "sources", "external"]
  }

  Named vaults with a default, so a second vault never needs a CLI change. Every key except
  `vaults` is optional and falls back to the constants below.

  Byte budgets are gone. They measured the wrong quantity: a workstream is heavy when it carries
  more than one concurrent thread, not when it is large, and a document that is regenerated
  cannot accumulate its way over a line. `budget_check.py` is retired with them.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "lipika" / "config.json"
ENV_VAULT = "LIPIKA_VAULT"

#: Directory names that carry meaning wherever they appear. A tree with none of these at its
#: root is not a vault, whatever else it is.
TIER_NAMES = ("workstreams", "grand-plans", "reference", "design",
              "values", "done", "sources", "external", "historical")

DEFAULT_SPANS_S = {"context-dump": 120, "pickup": 120}
DEFAULT_FROZEN_TIERS = ("done", "sources", "external")


class Unresolved(Exception):
    """No vault could be resolved. Carries the exit code a CLI should use."""

    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Vault:
    """A vault that exists, on disk, at a path that has been checked.

    Holding one of these *is* the proof — nothing downstream re-checks, and there is no way to
    construct one from a path that failed. That is the whole reason this is a type and not a
    string (see the vault's own `parse-dont-validate`).
    """

    path: Path
    name: str
    source: str  # which rung of the chain produced it — for error messages and reports
    spans_s: dict = field(default_factory=lambda: dict(DEFAULT_SPANS_S))
    frozen_tiers: tuple = DEFAULT_FROZEN_TIERS

    def __str__(self):
        return str(self.path)

    def joined(self, *parts):
        return self.path.joinpath(*parts)

    def span_budget(self, role):
        """Seconds, or None for a role deliberately exempt (evals, profiling)."""
        return self.spans_s.get(role)

    def is_frozen(self, relpath):
        """True if a path sits in a tier corrected by appending, never by editing. Only a
        directory names a tier, so a file called `sources.md` elsewhere is not frozen."""
        parts = Path(relpath).parts[:-1]
        return any(p in self.frozen_tiers for p in parts)


def load_config(path=CONFIG_PATH):
    """The config file as a dict, or {} if there is none. A malformed one is an error, not a
    missing one — silently treating unparseable JSON as absent hides a typo forever."""
    p = Path(path).expanduser()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as e:
        raise Unresolved(f"{p} is unreadable: {e}", code=4)
    if not isinstance(data, dict):
        raise Unresolved(f"{p} must contain a JSON object", code=4)
    return data


def tier_count(path):
    p = Path(path)
    return sum(1 for t in TIER_NAMES if (p / t).is_dir())


def looks_like_vault(path, need=1):
    """Whether a tree carries enough vault shape to be treated as one.

    `need` is 2 for the *implicit* rung — the checkout we happen to be standing in — and 1 when
    a caller named the path. The asymmetry is deliberate and was found by a red case coming out
    green: this repo grew a `design/` directory, which is a legitimate tier name, and one tier
    was enough to make the machinery resolve *itself* as the vault it maintains. A caller who
    passes `--vault` has asserted intent and may point at a one-tier tree; nobody asserted
    anything about the current directory, so it has to earn it.
    """
    return tier_count(path) >= need and Path(path).is_dir()


def git_main_checkout(start=None):
    """The shared tree, resolved correctly from inside a worktree as well as from the main one.

    Same trick `pass_log.py` uses: `--git-common-dir` points at the *main* .git for a worktree,
    so a sub-agent in a worktree resolves the vault it was cut from rather than its own copy.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, check=True, cwd=start or os.getcwd(),
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    common = out.stdout.strip()
    if not common:
        return None
    parent = os.path.dirname(common.rstrip("/"))
    return parent or None


def _tunables(cfg):
    spans = dict(DEFAULT_SPANS_S)
    spans.update(cfg.get("spans_s") or {})
    frozen = tuple(cfg.get("frozen_tiers") or DEFAULT_FROZEN_TIERS)
    return spans, frozen


def resolve(vault=None, config_path=CONFIG_PATH, cwd=None):
    """Return a Vault, or raise Unresolved. Never returns a guess.

    `vault` may be a path or a name defined in the config's `vaults` map — an agent that knows
    only "the ai_docs vault" should not have to know where it lives.
    """
    cfg = load_config(config_path)
    named = cfg.get("vaults") or {}

    def build(path, name, source, need=1):
        p = Path(path).expanduser()
        if not p.is_dir():
            raise Unresolved(f"{source} names {p}, which is not a directory", code=3)
        p = p.resolve()
        if not looks_like_vault(p, need):
            found = tier_count(p)
            raise Unresolved(
                f"{source} names {p}, which carries {found} of the recognized tier directories "
                f"({', '.join(TIER_NAMES[:4])}…) and needs {need} — it does not look like a "
                f"vault", code=3)
        spans, frozen = _tunables(cfg)
        return Vault(path=p, name=name, source=source, spans_s=spans, frozen_tiers=frozen)

    # 1. explicit
    if vault:
        if vault in named:
            return build(named[vault], vault, f"--vault {vault} (config)")
        return build(vault, Path(vault).expanduser().name, "--vault")

    # 2. environment
    env = os.environ.get(ENV_VAULT)
    if env:
        if env in named:
            return build(named[env], env, f"${ENV_VAULT} (config)")
        return build(env, Path(env).expanduser().name, f"${ENV_VAULT}")

    # 3. config default
    if named:
        name = cfg.get("default")
        if name and name not in named:
            raise Unresolved(f"config default '{name}' is not in vaults", code=4)
        if not name:
            if len(named) > 1:
                raise Unresolved(
                    f"config defines {len(named)} vaults and no default; pass --vault", code=4)
            name = next(iter(named))
        return build(named[name], name, "config default")

    # 4. the checkout we are standing in
    root = git_main_checkout(cwd)
    if root and looks_like_vault(root, need=2):
        return build(root, Path(root).name, "current git checkout", need=2)

    raise Unresolved(
        "cannot locate a vault: no --vault, no $" + ENV_VAULT + f", no {config_path}, and the "
        "current checkout does not look like one. Refusing rather than guessing — a tool that "
        "guesses its target curates the wrong tree and reports success.", code=2)


def add_argument(parser, flag="--vault"):
    """Give a tool the standard flag, with the chain documented where --help shows it."""
    parser.add_argument(
        flag, default=None,
        help="vault path, or a name from ~/.config/lipika/config.json. "
             f"Default: ${ENV_VAULT}, then the config, then the current checkout")


def from_args(args, attr="vault"):
    return resolve(getattr(args, attr, None))


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("what", nargs="?", default="path",
                    choices=("path", "name", "show", "spans"),
                    help="path (default) prints the resolved vault root, for `cd $(…)`")
    add_argument(ap)
    a = ap.parse_args(argv)
    try:
        v = resolve(a.vault)
    except Unresolved as e:
        print(f"vault_config: {e}", file=sys.stderr)
        return e.code
    if a.what == "path":
        print(v.path)
    elif a.what == "name":
        print(v.name)
    elif a.what == "spans":
        for role, s in sorted(v.spans_s.items()):
            print(f"{role:16} {s}s")
    else:
        print(f"vault   {v.path}")
        print(f"name    {v.name}")
        print(f"via     {v.source}")
        print(f"frozen  {', '.join(v.frozen_tiers)}")
        for role, sec in sorted(v.spans_s.items()):
            print(f"span    {role:16} {sec}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))


def anchor(path, vault=None):
    """Resolve a path that may be given relative to cwd OR to the vault root.

    Every tool here used to run with the vault as the current directory, so its arguments were
    vault-relative by accident of where it was invoked. Now that the tools live elsewhere, both
    readings are legitimate: an agent may `cd` into the vault, or stay put and name a workstream.
    cwd wins when both exist, because an explicit local path should never be overridden by a
    same-named path in the vault.

    Returns a str for the first reading that exists, else None — the caller decides whether a
    missing path is an error, since some tools accept paths that are about to be created.
    """
    p = Path(path)
    if p.exists():
        return str(p)
    if p.is_absolute():
        return None
    try:
        v = vault or resolve()
    except Unresolved:
        return None
    candidate = v.path / p
    return str(candidate) if candidate.exists() else None


def resolve_or_exit(vault=None, tool=None):
    """For a tool that WRITES: resolve, or die with the chain's own exit code and message.

    Kept separate from `resolve()` so the refusal is one call rather than a try/except copied
    into every tool — the pattern that let each one drift its own way last time.
    """
    try:
        return resolve(vault)
    except Unresolved as e:
        print(f"{tool or 'lipika'}: {e}", file=sys.stderr)
        raise SystemExit(e.code)


def vault_relative(path, vault=None):
    """The vault-relative form of a path, for arguments handed to git.

    The mirror of `anchor()`, and needed for the same reason: `git show <ref>:<path>` only accepts
    a path relative to the repository root, so a tool that resolved its argument to an absolute
    path has broken its own git call. Anchor for the filesystem, relativise for git.
    """
    v = vault or resolve()
    p = Path(path)
    if not p.is_absolute():
        p = (Path.cwd() / p) if Path(path).exists() else (v.path / p)
    try:
        return str(p.resolve().relative_to(v.path))
    except ValueError:
        return str(p)


def repo_for(path):
    """The git root containing `path`, or None.

    Some tools ask a question about a *file* rather than about a vault — `recall_check` asks whether
    a rewrite dropped a fact, which is true or false regardless of which repository the file is in.
    Wiring those to the configured vault would make them useless for the machinery's own files, now
    that the machinery is its own repo. So: follow the file, and fall back to the vault.
    """
    p = Path(path).expanduser()
    start = p if p.is_dir() else p.parent
    # Walk up to the nearest EXISTING ancestor. A path that no longer exists is the normal case
    # for the one question this is asked: `recall_check <ref> <old-path> --into <new-path>` names
    # a file that MOVED, so `<old-path>` is gone from the working tree. Returning None there sent
    # the caller to the configured vault instead of to the file's own repo, which then reported
    # the source absent at a ref where `git cat-file -e` confirms it present -- the third recorded
    # `--into` defect, and it disabled the losslessness gate on exactly the change most likely to
    # drop a fact.
    start = start.absolute()
    while not start.exists() and start != start.parent:
        start = start.parent
    if not start.exists():
        return None
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(start),
                             capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip() or None
