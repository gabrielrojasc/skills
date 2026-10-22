---
name: pr-review
description: Reviews GitHub PRs. Use when reviewing a PR.
---

# PR review

Review one or more GitHub PRs with independent reviewer subagents, verify their
drafts with fresh subagents, raise only the findings that need the user's
judgment, and submit one review per PR.

Follow [Submit](#submit) for permission to post. Subagents are read-only outside
their assigned files.

## Setup

With more than one PR, also follow [Multiple PRs](references/multiple-prs.md).
When a tool to set the session title is available, follow [Session
title](references/session-title.md).

Create a private run directory with `mktemp -d`, with a folder per PR named
`<owner>__<repo>__<number>__<short-head-sha>`. Each folder holds `src/`,
`standards.md`, `spec.md`, `risk.md`, `approach.md`,
`verify-<axis>-<round>-input.md`, `verify-<axis>-<round>.md`, `triage.md`,
`final-review.md`, and `review.json`.
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
- `same`: nothing the PR changes differs from what the user reviewed. Report
  the status of that review's threads. If the script reports the review as
  dismissed, ask whether to re-submit its event through [Submit](#submit);
  otherwise stop. Start no reviewers and report no problems of your own, unless
  the script reports a rebase: then, first, one Standards reviewer checks only
  the code, contracts, and config the patch relies on that changed on the base,
  and its drafts go through Verify and Triage.
- `changed`: review only the printed differences, with the full diff as
  context, and report only problems they introduce, including breakage they
  cause elsewhere. After a reported rebase, also check what the patch relies
  on that changed on the base.
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

Every PR also gets an Approach agent, and, unless the user authored it, a Risk
agent.

Pick the agent tier once per head, from the diff, and use it for every reviewer
and verifier on that head.

## Review

Do the setup, the earlier-review check, and the review choice yourself; they
take a few commands. Then start, in the background, one subagent per axis the
review choice selected for each PR. Gather no diffs, threads, or source for them
beyond `src/`. Each axis moves to verification as soon as its own reviewer
returns. Keep the axes in separate reports.

Wait only when no work can proceed, and when you must poll agents, wait several
minutes per call. In Codex, update at least every 60 seconds from what you know;
"still running" suffices.

Message a running agent only to stop it, when its head moved or its PR closed.

### Standards axis

The Standards agent judges code, documentation, and agent instructions against
the chosen standards, not the ticket or acceptance criteria. A repository's
standards are its `AGENTS.md`, `CLAUDE.md`, and `CONTRIBUTING.md`, the docs they
point to, the development sections of `README.md`, any file under `docs/`
about how code is written, and any review guide, such as `REVIEW.md` or a PR
review playbook, whose scope covers the diff. Always apply Fowler's code smells
(*Refactoring*, chapter 3); the repository wins a conflict. When the diff
changes documentation, agent instructions, or documentation automation, or
makes unchanged ones false, reviewers and verifiers read [Documentation and
agent instructions](references/documentation-review.md). Configuration the diff
makes false is a finding too. Guidance or configuration that was already stale
before this PR goes in the notes.

### Risk axis

The Risk agent writes `## Risk` with `low`, `medium`, or `high` and one line
per reason naming the paths, even when it finds nothing to draft. It looks for
changes to authentication, authorization, tenant isolation, secrets, stored-data
schemas, CI or infrastructure, and shared code with many callers, and for
effects a revert can't undo, such as dropped columns, backfills, or sent
messages. For each, it checks that the PR says how to undo or recover and how a
failure would be noticed, and checks authorization, tenant scoping, timing-safe
comparisons, secret handling, input validation, and whether data a serializer
or permission hides still leaks through ordering, filters, errors, or logs,
including logs in unchanged helpers on the call path. It also finds who else
writes the data the diff relies on, such as jobs writing tables with raw SQL,
and who consumes what it returns or emits, fetching a named repository at a
pinned commit, and checks the change still holds for each. Its drafts follow
the finding bar.

### Approach axis

The Approach agent reads the problem, the ticket and its parent, earlier review
threads, and the code around the change before the diff. It looks for one
concrete simpler route: existing code, a framework feature, a config change, or
a change in the service that owns the concern, fetched at a pinned commit.
Before judging a new class, function, or helper, it lists the existing ones in
the touched and imported modules that do the same kind of job, such as
permissions, pagination, or service helpers. It raises an alternative only when
the alternative preserves required behavior and removes a real maintenance,
operational, or coordination cost; equally valid alternatives go in its notes.
It reopens a decision made in a thread only with new evidence. It writes at most
two alternatives, each with the replacement, its evidence, the constraints it
preserves, and the switching cost, and names the context it lacked. Its
alternatives skip Verify and go to the user in Triage as notes.

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
requirements) and major tech-debt introduction. Report problems the diff
introduces, including breakage it causes in unchanged code and requirements it
leaves missing. Also report defects and broken documented rules that predate the
diff in code it touches, moved code included, as pre-existing findings. They
never block or count toward the event; mark a small one optional, and ask the
author to take on a larger one in this PR or a follow-up. Every finding other
than a blocker needs a consequence of leaving it as is:

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
verification gap, not proof of redundancy. Apart from pre-existing findings and
deciding questions, only mechanical local cleanup is nonblocking; every other
finding blocks. A deciding question asks for a fact only the author has, such
as intent or a deployment constraint, without which you can't tell whether the
PR is acceptable. Don't ask about a design preference or an option the PR body
already weighed; when the body accepts a defect, report the defect.

### Rules for every reviewer

1. Read the PR metadata, diff, and review threads, and source from `src/`. Don't
   repeat a point already made or resolved in a thread; when an unresolved bot
   comment meets the finding bar, draft a +1 on it instead. Skip a problem a CI
   check already reports on the same line. If the user reviewed the PR before,
   report each of their earlier threads as addressed, unaddressed, or author
   replied.
2. When you find a problem, search the diff and the files it touches for the
   same pattern, and list every instance in one finding. On a re-review, list
   only instances in the changes under review.
3. For each hook, signal, callback, task, or retry the diff adds or changes,
   state when it runs, what has already been saved or made visible by then,
   and what happens when it fails or runs twice.
4. Anchor a finding inline when a changed line owns the problem, otherwise in
   the review body. Never invent an anchor.
5. For defects and spec gaps, give a concrete example of what goes wrong; for
   cleanup, say what is unnecessary or misleading, its consequence, and the
   correction. Prefer a casual question ("do we need X here so Y happens?") when
   the author is senior or the fix is obvious.
6. Start every draft with its [Conventional Comments](https://conventionalcomments.org/)
   label: `issue (blocking):`, `nitpick (non-blocking):` for mechanical local
   cleanup, `issue (non-blocking, pre-existing):`, or `question:` for a deciding
   question.
7. Write the result with headings `## Target head`, `## Verdict` (APPROVE,
   COMMENT, or REQUEST_CHANGES with one line of reasoning), `## Comment drafts`
   (`- **file:line** — text` using new-file line numbers,
   `- **review body** — text`, or `- **+1 <comment URL>** — why it holds`),
   and `## Notes for the reviewer (not for posting)`. Spec agents use
   `## Spec verdict` and `## Spec findings`. Return only the file path and the
   verdict line.
8. If nothing qualifies, return APPROVE with no drafts and no praise.

## Verify

No draft reaches the user unverified. An axis with no drafts skips verification
and reports "no review issues found". When no axis has drafts, go to
[Triage](#triage).

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

Group confirmed findings across axes that share the problem and the fix, then
set the event from them, pre-existing ones excluded: `REQUEST_CHANGES` for a
blocker or more than 3 nitpicks; otherwise `COMMENT` for a deciding question,
or `APPROVE`. Refuted and dropped drafts, with
their reasons, and the reviewers' notes go in `triage.md`.

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

3. When an HTML render tool is available, show this step's content as one page
   built from [Rendered report](references/rendered-report.md); otherwise
   write it in Markdown as follows. Open with the Risk agent's line and
   reasons, if one ran, a three-line summary of what the change does, and the
   evidence: CI state at the head, what the author tested, and what the review
   didn't check. Then show each Approach alternative in one line, the event
   that would be posted, and, on a re-review, each earlier thread's status. On
   the third or later review that still has blockers, add a line suggesting a
   call or a rethink of the approach. Give each raised finding its own heading
   and each field its own paragraph:

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
   links the bot's comment and says why it holds. Show each note about
   direction or a new pattern others will copy in one line. End with the counts
   of refuted and dropped drafts and of other notes, and the path to
   `triage.md`.
4. On the user's own PR, stop after showing the findings; nothing posts.
   Otherwise, follow [Submit](#submit) to determine whether the package may
   post automatically. If it may not, show the whole batch in one message and
   ask one question, not one per finding, saying that approving the batch as
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
8. Write posted comments in lowercase, after their label, with no praise.
   Suggest a follow-up only for a pre-existing finding.

## Submit

Assemble `final-review.md` with the event, kept inline comments in order, kept
+1s, and a body only for unanchored findings or when the nitpick count alone
requires changes; then the body says the set needs fixing before merge.

A review with no kept findings is an `APPROVE` package, never a `COMMENT`, even
under an instruction to post only `COMMENT` reviews; don't offer one either.

The user grants standing permission to submit an `APPROVE` whose only findings
are at most three nitpicks, only when the Risk agent reports low risk and the
Approach agent raised no alternative. Changes to authentication, authorization,
stored-data schemas, CI or infrastructure, or irreversible behavior are
ineligible, and so are missing or uncertain Risk or Approach results. Submit a
`COMMENT` without asking only when it holds a deciding question and no raised
finding. When the user approved the batch as
shown, submit. For any other package, show it exactly and ask. An instruction
not to approve overrides the standing permission and forbids posting the
approval, not asking.

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
