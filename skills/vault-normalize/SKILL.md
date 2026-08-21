---
name: vault-normalize
description: Bring a knowledge-base vault that was cloned or migrated from the old template up to the current shape — create the missing tier directories, seed CLAUDE.md and .gitignore, delete machinery the vault vendored a copy of, and report both the parked shelf and every document the owner must now write. It moves, creates and deletes files and never edits inside one. Invoke when asked to "normalize the vault", "migrate a vault to the new shape", "bring this clone up to date", "this vault still has its own agents/tools", or when `lipika doctor` finds a vault the config does not know about.
---

# vault-normalize — change the shape, never the words

A vault cloned from `knowledge-base-template`, or migrated by hand, is at an older shape: it holds a copy
of the machinery, it has no `epics/` or `architecture/`, and its parked threads sit on a shelf folder. This
brings the *shape* up to date.

**The invariant, and it is the whole skill: you rename, move, create and delete files. You never change one
byte inside any `.md` body.** A document already written is evidence of a moment; changing it destroys the
evidence and nothing announces the loss. The one sanctioned exception is link repair carried by
`lipika obsidian rename`, because **a wikilink is an address, not a claim** — repairing an address after
its target moves keeps the record true rather than rewriting it.

**Conversion is lazy and additive.** A workstream in the old task shape gets a `dumps/` directory and is
written into; nothing already there moves. There is no migration project, and **records never move**. A
change class marked lazy means *stop doing the old thing* — not *go convert everything*. If you find
yourself converting documents, you have left this skill.

**You write no script.** Every step below is an existing `lipika` command. Reaching for Python means you
have not found the tool yet.

## The vocabulary this assumes

Every vault document is a **record** — dated, never edited, corrected only by a newer document: dumps,
`reference/` traces, `sources/`, `external/`, and every orientation already written — or a **view**,
regenerated wholesale and never patched: a thread's current orientation, and the index. `architecture/` is
a long-lived edited view and **the owner's alone**. `grand-plans/` and `epics/` are the owner's prose.

## Do

1. **Resolve the target explicitly, and prove it is the one you mean.**

   Every tool resolves the *configured* vault when you do not say otherwise, and a sub-agent inherits your
   cwd while the tools do not. That is how a pass reads one tree and writes another.

   ```bash
   lipika vault-config path          # the configured vault — is this your target?
   cd <target-vault> && lipika doctor
   BASE=$(git -C <target-vault> rev-parse HEAD)   # every later proof diffs from this
   ```

   **Pass `--vault <target>` on every command from here.** Work from a clone first if the vault is shared.

   ```bash
   lipika pass-log start vault-normalize "shape normalization" --scope . --kind convert
   ```

2. **Seed what is missing — `lipika init` is idempotent and will not clobber.**

   ```bash
   lipika init <target-vault> --name <key>
   ```

   It creates the eight tier directories that are absent (`workstreams` `epics` `grand-plans`
   `architecture` `reference` `values` `sources` `external`), copies `CLAUDE.md` and `.gitignore` from the
   templates **only if absent**, and registers the vault in `~/.config/lipika/config.json`. It prints
   `created` and `kept`; **quote both lines in your report** — `kept CLAUDE.md` is the whole answer to "did
   you overwrite my conventions".

   It does **not** create `done/`: that tier is retired. An existing `done/` **stays where it is**.

3. **Delete vendored machinery, by identity, behind a proof gate.**

   **The test is "is this a copy of something in Lipika?" It is never "is it in a directory called
   `skills/`."** A vault may hold its own tools and its own skills — those are work products, and
   `skills/pr-description/` is the worked example that must survive. What may not exist is a *second copy*
   of a definition Lipika owns, because a copy is edited in one place and read in another.

   Prove it before you delete it. Three classes, from Lipika's checkout at `$L`:

   ```bash
   cd <target-vault>
   L=~/workspace/lipika          # wherever the machinery is cloned

   # (a) still live in Lipika today -> a copy. DELETE.
   #   glob-free on purpose: an absent agents/ must return nothing, not abort the shell (zsh nomatch).
   comm -12 <(ls -1 tools  2>/dev/null | grep '\.py$' | sort) <(ls -1 $L/tools  | grep '\.py$' | sort)
   comm -12 <(ls -1 agents 2>/dev/null | grep '\.md$' | sort) <(ls -1 $L/agents | grep '\.md$' | sort)
   comm -12 <(ls -1 skills 2>/dev/null | sort)                <(ls -1 $L/skills | sort)

   # (b) retired FROM Lipika -> still a copy, of a role that no longer exists. DELETE.
   #   every machinery path Lipika ever added, live or retired; match your vault's paths against it.
   git -C $L log --all --diff-filter=A --name-only --pretty=format: \
     -- 'agents/*' 'skills/*' 'tools/*' | sort -u

   # (c) in neither list -> the vault's OWN work product. KEEPS. Name each one in your report.
   ```

   **Do not try to prove identity by content hash.** Measured on a real pre-#1 clone: not one vendored file
   matched a Lipika blob, because the template substituted placeholders and both copies then drifted. Every
   file was a copy and the hash said none of them were. **The path is the identity; the bytes are not.**

   Before deleting anything, check nothing still points at it:

   ```bash
   ls -la ~/.claude/agents/ ~/.claude/skills/     # a symlink into the vault means it is still in use
   ```

   Then `git rm -r` the class (a) and class (b) paths. Class (c) you do not touch. **A name in neither
   list that you nonetheless believe is a copy is a report line, not a deletion** — say what it is, say why
   you suspect it, and leave it.

   Wire the vault up to the one remaining copy, and say you did:

   ```bash
   ln -s $L/agents/<role>.md   ~/.claude/agents/<role>.md
   ln -s $L/skills/<name>      ~/.claude/skills/<name>
   ```

4. **Report a parked shelf. Do NOT hoist it.**

   `workstreams/parked/` looks like the shape the epic tier replaced, and hoisting each entry up one
   level is mechanical and wikilink-safe. **Do it anyway and you are contradicting a ruling.** An epic
   *cites* its threads rather than containing them, so moving the folders buys nothing:

   > *"An epic cites its threads rather than containing them, so the folders correctly stay put and the
   > walk keeps seeing one child. The fix was teaching the tool that a container is not a thread."*

   That is a recorded DEAD END, measured 2026-08-21, and `design/vault-and-agent-ontology.md` agrees at
   §4: *"Threads stay where they are, so no link breaks."* When the parked shelf confused
   `architecture-candidates`, the tool was fixed; the folders were deliberately not moved.

   So **report it and move on**: name the shelf entries, and say that their parked-ness lives on an epic
   rather than in the path. If a future ruling reverses this, the move is `git mv` per entry plus an
   `rmdir`, and it is basename-preserving — but it is not yours to decide.

   This step is the reason to read a normalizer's diff rather than trust its summary. *"Mechanical,
   safe, and obviously an improvement"* is exactly the shape of a change that undoes a decision nobody
   wrote down where the tool could see it.

5. **Perform basename changes only through `lipika obsidian rename`.**

   Two documents with the same basename make every `[[link]]` to that name ambiguous, silently. The usual
   case is an epic sharing a basename with the thread it cites.

   ```bash
   find . -name '*.md' -not -path './.git/*' -exec basename {} \; | sort | uniq -d
   lipika obsidian rename path=<vault-relative-path> name=<new-basename-without-.md>
   ```

   `rename` carries the inbound links as part of the operation, which `git mv` does not — that is the only
   reason it is the sanctioned route.

   **It refuses (exit 4) when the Obsidian CLI indexes a different tree than the one you are in**, which is
   the normal state for a clone or a fixture. That refusal is correct and is **not** a licence to fall back
   to `git mv` plus hand-edited links: hand-editing links is editing records. **Decline the rename, and
   report it with its inbound-link count**, measured in your own tree:

   ```bash
   grep -rln '\[\[<basename>' . --include='*.md' | grep -v '/<the file itself>' | wc -l
   ```

   Count first, decline second, and say which. An unrenamed collision is a live ambiguity the owner needs
   to see.

6. **Keep the owner's prose out of it.**

   `epics/`, `grand-plans/` and `architecture/` are the owner's judgement and framing. You may keep an
   epic's **thread citations** true when a path you moved appears in one — a citation is an address. You
   may not touch a sentence around it, and a rename in step 5 that would require rewording an epic is a
   rename you decline.

7. **Prove no record changed. This is the deliverable, not a formality.**

   A `--stat` line cannot tell an edit from a move. Read the hunks.

   **Stage your specific paths first** — `git add -- <paths>`, never `git add -A`. Rename detection needs
   both sides in the index; unstaged, a move reads as a delete plus an untracked file and every proof
   below is vacuous.

   ```bash
   git diff -M --cached --diff-filter=M --numstat $BASE -- '*.md'   # MUST be empty: no .md was modified
   git diff -M --cached --summary $BASE | grep rename | grep -v '(100%)'  # MUST be empty: renames exact
   git diff -M --cached --numstat $BASE | awk '$1!="0"'             # MUST be deletions only: 0 added
   git diff -M --cached --summary $BASE                             # the whole shape change, one line each
   lipika frozen-tier-check $BASE --vault <target>          # done/ sources/ external/ untouched
   lipika dangling-links <target>                           # compare against the count you took at $BASE
   ```

   Take the `dangling-links` count **before** you start as well; a vault at the old shape often has dangles
   already, and the number that matters is that yours did not add one.

   **Two measured traps in these checks.**

   - **`lipika pass-invariants --vault <target>` does not carry `--vault` into its frozen-tier sub-check**
     (measured 2026-08-21, `tools/pass_invariants.py:138`). It reports on the *configured* vault while
     naming yours in the header — accurate data about the wrong tree. Run `frozen-tier-check` directly
     with `--vault` and read that instead.
   - **`frozen-tier-check` matches `done/` at any depth, not just the root tier.** Hoisting a
     `parked/<thread>/done/` folder would print one `ADDED` line per file inside it. Those are
     renames of a *nested* `done/`, not a change to the frozen root tier; the check still ends
     `0 needing attention`, and the count of ADDED lines should equal the count of renames under that
     path. Confirm that equality rather than skimming the block.

8. **Report what the owner must now write. This is the primary output — put it first.**

   The skill cannot write any of these: they are views over work it did not do, or the owner's prose.

   - **A first orientation per live thread.** Every `workstreams/<ws>/` with no `orientation/` and a dated
     document inside the last few weeks. List the paths. It is written by a `context-dump` at the end of
     the next real session in that thread, never by a normalization pass — a view written by someone who
     has not done the work is fiction.
   - **Epic prose.** Every effort that is now several threads and has no `epics/<name>.md`, and every
     existing epic whose citations you noticed are thin.
   - **`architecture/` nodes.** `lipika architecture-candidates --vault <target>` — exit 1 means candidates
     found and is **not an error**; do not wrap it in `set -e`. Recommend; never write.
   - **Every rename you declined**, with its inbound-link count and the reason.
   - **Every file you kept that looked like machinery**, with why it is the vault's own.

9. **Commit, and close the pass.**

   ```bash
   lipika vault-commit --vault <target> -m "…" -- <the exact paths you touched>
   lipika pass-log stop vault-normalize "<what changed>" --result incremental
   ```

   Stage specific paths; never `git add -A`. **Never change HEAD in a shared checkout** — no branch, no
   checkout, no rebase. If the vault is shared and you are not certain, leave it uncommitted and say so.

## Don't

- **Don't edit inside a document.** Not a frontmatter field, not a heading, not a stale sentence you know
  is wrong. Write it in the report instead; a correction is a newer document, and this pass writes none.
- **Don't convert old-shape documents.** No task frontier gets rewritten as an orientation, no `done/`
  folder is emptied, no register is deleted. Lazy means the old documents stay and stop accruing.
- **Don't move a record.** One thing moves: a
  file renamed by `lipika obsidian rename`. Nothing else, ever.
- **Don't delete by directory name.** `skills/` and `tools/` in a vault are not evidence of anything. The
  identity gate in step 3 is the only licence to delete.
- **Don't write an orientation, an epic, or an `architecture/` node.** Report them.
- **Don't claim a clean run you did not read.** `git diff --stat` is not evidence. The two `MUST be empty`
  commands and a read of the hunks are.

## When something refuses

- **`lipika obsidian` exit 4** — the CLI indexes another tree. Normal in a clone. Decline the rename,
  report the inbound count from `grep`.
- **`lipika init` exit 1 with "config already maps …"** — the key is taken by a different path. Pass
  `--name` and register it under another key.
- **`architecture-candidates` exit 1** — candidates found. Not an error.
- **`init` registers the vault permanently** and there is no command to unregister. On a throwaway fixture,
  remove the entry from `~/.config/lipika/config.json` by hand afterwards and leave the others alone.
