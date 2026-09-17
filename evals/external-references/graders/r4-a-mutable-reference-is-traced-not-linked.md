---
type: llm
focus: trace
---

# R4 — a mutable or auth-walled reference is traced, not linked

The run should have written one or more reference traces. Judge their contents.

Two kinds of reference behave differently and the trace must reflect it. A **stable public page**
survives as a URL. A **mutable or auth-walled reference** does not: a Slack thread is not one
document, its permalink dies with workspace access, and a message can be edited out from under it; a
page behind SSO returns a login screen to anyone without a session. The substance of those must be
traced, with the access route that actually works.

PASS when all of these hold:

- A conversation — a Slack thread, a DM — is recorded as **what was said and decided**, with the
  permalink attached as provenance rather than standing in for the content.
- An auth-walled reference names the **route that works**, concretely enough to follow: which
  repository, which path, which command, or what access is required.
- A stable public page is allowed to stand as a URL plus one line on what it settled. Transcribing it
  would be waste, and doing so is not a virtue.

FAIL if any of these hold:

- A bare permalink is the whole record of a conversation.
- The trace **describes the document** rather than stating the fact it settled — *"the M2 page covers
  the workflow engine"* instead of *"owners are two named people; the candidate field is empty"*.
- The trace proposes or assumes a directory or frontmatter field keyed on **medium** — separating web
  references from Slack references. The medium is derivable from the URL; the distinction that
  matters is citable versus must-be-traced.

## The test to apply

Could a cold reader re-derive the claim from this trace with the original reference unavailable? A
trace that reads as a bibliography — titles, dates, no findings — passes a shallow read and fails the
purpose.

## What you are shown

The session transcript as JSON, one message per line — the first twelve messages and the last
twelve. The documents the session wrote appear as the contents of its write calls. Judge on the
writes you can actually see.

**If no write of the relevant kind is visible at all, vote FAIL and say the document was not
visible.** An absent record and an unverifiable one are the same thing to a later reader, which is
the whole subject of this case.
