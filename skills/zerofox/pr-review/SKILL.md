---
name: pr-review
description: Reviews GitHub PRs. Use when reviewing a PR.
---

# PR review

Review one or more GitHub PRs with independent reviewer subagents, verify their
drafts with fresh subagents, raise only the findings that need the user's
judgment, and submit one review per PR.

Submit a `COMMENT` review of routine findings without asking. Keep every other
draft local until the user explicitly approves the review for that PR in this
session; one approval covers its routine findings too. Subagents are read-only
outside their assigned files.

## Setup

With more than one PR, also follow [Multiple PRs](references/multiple-prs.md).
When a tool to set the session title is available, follow [Session
title](references/session-title.md).

Create a private run directory with `mktemp -d`, with a folder per PR named
`<owner>__<repo>__<number>__<short-head-sha>`. Each folder holds `src/`,
`standards.md`, `spec.md`, `verify-<axis>-<round>-input.md`,
`verify-<axis>-<round>.md`, `triage.md`, `final-review.md`, and `review.json`.
These files, not the conversation, hold the draft text, so a summarized
conversation can't change what gets posted. Give subagents absolute paths to the
files they write and to `src/`, and report the run directory in updates.

Fetch each PR's head with
`<SKILL_DIR>/scripts/fetch-source.sh <owner>/<repo> <head-sha> <pr-folder>/src`.
An agent that needs another repository at a pinned commit fetches it the same
way into the run directory.

Every Markdown file starts with `## Target head` and the head SHA it was
produced against, and `review.json` records it in `commit_id`. Reject any file
whose head differs from its folder's. If the head moves before submission,
follow [When the head moves](references/head-moves.md).

## Check for an earlier review

Before starting reviewers, run
`<SKILL_DIR>/scripts/changes-since-review.py <owner>/<repo> <n>` per PR:

- `none`: review in full.
- `same`: nothing the PR changes differs from what the user reviewed. Start no
  reviewers. Report the status of that review's threads and ask whether to
  re-submit its event through [Submit](#submit) or stop. GitHub dismisses only
  approvals and change requests, so for a `DISMISSED` review, ask which it was.
- `changed`: review only the printed differences, with the full diff as
  context, and report only problems they introduce, including breakage they
  cause elsewhere.
- `unknown`: review in full and tell the user why.

A re-review covers every PR in this session's run directories unless the user
names some, repeating Setup and this check for each.

## Choose the review

| PR | Standards axis | Spec axis |
|---|---|---|
| riskive/API | Repository and Python standards, api-specialist lens | Only when the author is an active member of `t-executive-protection` |
| Other Python repositories | Repository and Python standards | Yes |
| Non-Python repositories | Repository conventions | Yes |
| Dependency bumps (for example, renovate) | Upgrade risk | No |

Dependency bumps take the upgrade-risk row everywhere, riskive/API included. For
riskive/API, non-Python infrastructure, and dependency bumps, read [Choosing the
review](references/choose-review.md) before starting reviewers. Python standards
live under `docs/` in `riskive/python-standards`; use the files relevant to the
diff.

## Review

Do the setup, the earlier-review check, and the review choice yourself; they
take a few commands. Then start one Standards subagent per PR and, when the
table calls for it, one Spec subagent, in the background. Gather no diffs,
threads, or source for them beyond `src/`. Each axis moves to verification as
soon as its own reviewer returns. Keep the axes in separate reports.

Wait only when no work can proceed, and when you must poll agents, wait several
minutes per call. In Codex, update at least every 60 seconds from what you know;
"still running" suffices.

Message a running agent only to stop it, when its head moved or its PR closed.

### Standards axis

The Standards agent judges code, documentation, and agent instructions against
the chosen standards, not the ticket or acceptance criteria. A repository's
standards are its `AGENTS.md`, the docs it points to, and any file under `docs/`
about how code is written. Always apply Fowler's code smells (*Refactoring*,
chapter 3); the repository wins a conflict. When the diff changes documentation,
agent instructions, or documentation automation, reviewers and verifiers read
[Documentation and agent instructions](references/documentation-review.md).

### Spec axis

Before starting a Spec agent, look for Linear issue IDs, such as `EPL-123`, in
the PR title, branch, body, and commit messages. With none, record "no spec
available" and start no Spec agent or verifier.

The Spec agent judges whether the diff implements what the originating ticket
asks. It reports only requirements that are missing, partial, or implemented
wrong, quoting the ticket line for each. Extra changes are fine unless they are
wrong or risky. When the ticket has no real spec or doesn't describe this
change, it reports "no spec available" and stops, without inferring requirements
from the PR description.

### Finding bar

Report blockers (broken behavior, real defects, security holes, missing or wrong
requirements) and major tech-debt introduction. Report only problems the diff
introduces, including breakage it causes in unchanged code and requirements it
leaves missing. Every other finding needs a consequence of leaving it as is:

- a caller or reader who will get something wrong;
- a second copy the next edit will miss;
- a condition that cannot be false or code that cannot run, when you can name
  the case a reader would wrongly assume exists;
- a rule in the repository's docs or `riskive/python-standards` that the change
  breaks; or
- code that does nothing or prose from the list below, which later readers must
  read, trust, or maintain for nothing.

A finding with a consequence is reported however small. A true observation
without one goes in the notes, with preferences, equally valid alternatives, and
speculative benefits. "Cleaner", "could be shorter", "the precedent does it the
other way", or log volume alone is not a consequence. Documentation lost by
deletion is tested by the documentation guidance instead.

Allow no unnecessary code or prose in any PR: redundant wrappers, speculative
abstractions, duplicated state, needless configuration, custom logic that an
existing framework hook covers, defensive checks for impossible states, comments
that narrate code, and unsupported claims. Apply unslop to prose. Short
docstrings are fine even when they restate the code, especially on classes; flag
one only when it is wrong, misleading, or long enough that keeping it in sync is
real work. Group instances only when they share the problem and the fix; a
misleading claim and a redundant one are separate findings. Name the specific
problem instead of calling it slop, and leave out who or what wrote it.

When a broken standards rule is the only consequence, the draft cites the doc
and line, names the change, and says nothing else.

The correction preserves required behavior, useful information, contracts, and
conventions, and stays local and proportionate. Missing evidence is a
verification gap, not proof of redundancy. Cleanup findings are nonblocking
unless they meet the blocker or major-debt bar on their own.

### Rules for every reviewer

1. Read the PR metadata, diff, and review threads, and source from `src/`. Don't
   repeat a point already made or resolved in a thread; when an unresolved bot
   comment meets the finding bar, draft a +1 on it instead. If the user reviewed
   the PR before, report each of their earlier threads as addressed,
   unaddressed, or author replied.
2. Anchor a finding inline when a changed line owns the problem, otherwise in
   the review body. Never invent an anchor.
3. For defects and spec gaps, give a concrete example of what goes wrong; for
   cleanup, say what is unnecessary or misleading, its consequence, and the
   correction. Prefer a casual question ("do we need X here so Y happens?") when
   the author is senior or the fix is obvious.
4. Write the result with headings `## Target head`, `## Verdict` (APPROVE,
   COMMENT, or REQUEST_CHANGES with one line of reasoning), `## Comment drafts`
   (`- **file:line** — text` using new-file line numbers,
   `- **review body** — text`, or `- **+1 <comment URL>** — why it holds`),
   and `## Notes for the reviewer (not for posting)`. Spec agents use
   `## Spec verdict` and `## Spec findings`. Return only the file path and the
   verdict line.
5. If nothing qualifies, return APPROVE with no drafts and no praise.

## Verify

No draft reaches the user unverified. An axis with no drafts skips verification
and reports "no review issues found". When no axis has drafts, re-check the head
and PR state yourself and go to [Submit](#submit).

When an axis's reviewer returns drafts, assign stable axis-prefixed IDs (`S1`,
`P1`) and write only the IDs, draft text, and any `user-promoted` marker to the
round's input file. A fresh read-only verifier per axis per round checks every
draft against the diff and source at the target head, existing threads, the
applicable standards, and, for Spec, the ticket. It reads its input file and
primary sources, including fetched source in the run directory, and no other
run files. It returns one verdict per ID with one line of evidence:

- **confirmed:** the claim, anchor, and consequence hold, nothing elsewhere
  already handles it, and it meets the finding bar. For unnecessary code or
  prose, check each grouped instance: removing it must lose nothing a reader
  uses. Drop the instances that fail, and refute the finding if none are left. A
  rule-only draft that argues impact is trimmed to the citation and the change
  and still confirmed; the verifier keeps the removed argument in its evidence.
- **revise:** the concern is real but the claim, anchor, or consequence is off.
  Include a corrected draft.
- **refuted:** the claim doesn't hold or the finding misses the bar. Never
  refute a finding for being small.

For a `user-promoted` draft, check only the claim and anchor; for a +1, the
bot's comment is the claim. New findings from the verifier get fresh IDs. When a
round leaves a draft at `revise` or adds a finding, follow [Further verification
rounds](references/verify-rounds.md) before triage.

Set the axis verdict from the confirmed set: none means APPROVE, and nonblocking
findings alone mean COMMENT. The review event is the most severe axis verdict.
Refuted and dropped drafts, with their reasons, and the reviewers' notes go in
`triage.md`.

## Triage

1. Re-check the PR's head, state, last update time, and reviews. A moved head
   follows [When the head moves](references/head-moves.md); a merge or close
   ends the review.
2. Raise a confirmed finding for the user's judgment when any of these holds;
   every other confirmed finding, +1s included, is routine:

   - It is `wording unsettled`.
   - It is blocking, so the event would be `REQUEST_CHANGES`.
   - It contradicts what the author explained in the PR body or a thread, or
     another human reviewer's position.
   - It is a Spec finding that rests on an ambiguous ticket line.

3. Show the event that would be posted, each axis's verdict, and, on a
   re-review, each earlier thread's status. Give each raised finding its own
   heading and each field its own paragraph:

   ```markdown
   ### S1 · blocking

   Inline at [path:line](link)

   **Problem:** what the code does, and the concrete input or case where it
   goes wrong.

   **Why it matters:** who is affected and how. For Spec, quote the ticket line.

   **Comment:**

   > the exact draft that would be posted

   ---
   ```

   Keep the problem and the reason to a sentence or two each, but always show
   the full draft. Add the trimmed impact argument when the verifier removed
   one. A raised +1 quotes and links the bot's comment in place of the draft.
   Mark a `wording unsettled` finding in its heading, and add a **Wording:**
   line with the sticking point.

   Then list routine findings one line each, with ID, link, and full draft; a +1
   links the bot's comment and says why it holds. End with the counts of refuted
   and dropped drafts and of reviewer notes, and the path to `triage.md`.
4. When nothing is raised and the event is `COMMENT`, go to [Submit](#submit)
   and report what was posted. Otherwise, show the whole batch in one message
   and ask one question, not one per finding, saying that approving the batch as
   shown posts the review. The user may instead decide or reword by ID, go one
   by one, or mix the two. Record every decision in `triage.md`.
5. One by one means one raised finding at a time, with a short explanation of
   the surrounding code, waiting for a decision before the next and skipping
   findings already decided.
6. A note the user wants posted becomes a new draft marked `user-promoted`. It
   gets one verification round for claim and anchor only.
7. Link every file mention shown to the user with one run of
   `<SKILL_DIR>/scripts/file-links.sh <owner>/<repo> <n> <path>:<line>...` per
   PR, pasted unchanged: hand-typed links carry the old MD5 hash or a space
   before `R<line>`, which GitHub can't resolve. Posted comment bodies stay
   plain.
8. Write posted comments in lowercase, with no praise or follow-up-ticket
   suggestions.

## Submit

Assemble `final-review.md` with the review event, every kept inline comment in
order, a review body only for kept findings without an inline anchor, and every
kept +1. When the user hasn't been asked to decide on this review's findings or
package and Triage step 4 came straight here, or the user approved the batch as
shown, submit. Otherwise, including an `APPROVE` with no drafts, show the exact
package and ask. An instruction not to approve forbids posting the approval, not
asking.

Immediately before submitting, re-check the head, confirm every target line is
still in the diff, and build `review.json` in the PR folder from
`final-review.md`. Confirm both match what Triage settled, including the user's
approval when asked. A moved head follows [When the head
moves](references/head-moves.md); any other change means rebuilding the package,
showing it, and asking. Submit once, as one review with all inline comments, and
publish no standalone PR comments:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews -X POST --input <pr-folder>/review.json
```

The JSON has `commit_id` (the verified head), `event`, `body` (omit when empty),
and `comments`, each with `path`, `line`, `side: "RIGHT"`, and `body`. Then add
a `+1` reaction to each kept +1's comment.

After posting or skipping a PR, start the next PR's triage in the same message,
waiting for its verification if needed. After the last PR, end with the run
directory path and, per PR, whether the review was posted, skipped, or deferred.
