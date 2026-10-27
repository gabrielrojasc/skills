---
name: pr-review
description: Use when reviewing a GitHub PR.
---

# PR review

Review one or more GitHub PRs with a reviewer subagent, check its findings with
a fresh verifier, raise only what needs the user's judgment, and submit one
review per PR. `<SKILL_DIR>` is this file's directory.

## Setup

Create a run directory with `mktemp -d`, with a folder per PR named
`<owner>__<repo>__<number>__<short-head-sha>`, and fetch the head with
`<SKILL_DIR>/scripts/fetch-source.sh <owner>/<repo> <head-sha> <pr-folder>/src`.
Subagents write their reports to the folder, and the review is built from those
files, not from the conversation. Every report starts with `## Target head` and
the head SHA; reject one whose head differs from its folder's. If the head
moves before you submit, follow [When the head moves](references/head-moves.md).

When a tool sets the session title, such as T3's `t3_thread_update` with
`action: "rename"`, follow [Session title](references/session-title.md). With
several PRs, start each PR's review as soon as its setup is done, and triage
them one at a time in the order their verification finishes.

Run `<SKILL_DIR>/scripts/changes-since-review.py <owner>/<repo> <n>` per PR:

- `none` or `unknown`: review in full, and for `unknown` say why.
- `same` without a rebase: report the status of the user's earlier threads and
  stop. If the script reports that review as dismissed, ask whether to submit
  its event again.
- `changed`, or `same` after a rebase: review only the printed differences and
  what the patch relies on that changed on the base, with the full diff as
  context. Report only problems they introduce.

## Review

Start, in the background, one reviewer subagent per PR, and a Spec reviewer
when the PR's title, branch, body, or commits name a Linear issue, such as
`EPL-123`. When the commits or branch show which agent wrote the PR, such as a
`Co-Authored-By: Claude` trailer or a `codex/` branch, run the reviewer on the
other provider through `delegate_task`. Pick one rung per head from the diff
and use it for every reviewer and verifier.

The reviewer judges the diff against these standards, read from `src/`: the
repository's `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, the docs they point
to, any file under `docs/` about how code is written, and any review guide
whose scope covers the diff, such as `REVIEW.md`. Add more by repository:

| PR | Also apply | Spec reviewer |
|---|---|---|
| riskive/API | Python standards and the api-specialist lens | Only for `t-executive-protection` authors |
| Other Python repositories | Python standards | Yes |
| Dependency bumps | Upgrade risk instead of the rest | No |

Python standards live under `docs/` in `riskive/python-standards`. For
riskive/API, non-Python infrastructure, and dependency bumps, read
[Choosing the review](references/choose-review.md) first. When the diff changes
documentation or agent instructions, or makes them false, the reviewer and
verifier read [Documentation and agent
instructions](references/documentation-review.md).

The reviewer also:

- Reads the problem, its ticket, and the earlier threads before the diff, and
  names at most two simpler routes, such as existing code, a framework feature,
  or a config change, that keep required behavior and remove a real cost.
  These go in its notes, unverified.
- Rates the risk `low`, `medium`, or `high` with a reason per path. It checks
  authentication, authorization, tenant isolation, secrets, stored-data
  schemas, CI and infrastructure, shared code with many callers, and effects a
  revert can't undo, and whether the PR says how to undo or notice a failure.
  It finds who else writes the data the diff relies on and who consumes what
  it returns, and checks the change holds for each.
- States, for each hook, signal, callback, task, or retry the diff adds or
  changes, when it runs, what is saved by then, and what happens when it fails
  or runs twice.
- Skips points already made in a thread and problems CI reports on the same
  line, and drafts a +1 on an unresolved bot comment that meets the finding
  bar.
- Lists every instance of a problem in one finding, anchored to a changed line
  that owns it or else to the review body.

The Spec reviewer reports only requirements the diff misses, implements
partly, or gets wrong, quoting the ticket line for each. When the ticket has no
real spec for this change, it reports `no spec available` and stops.

Each writes `## Target head`, `## Risk` (the reviewer only), `## Findings`, and
`## Notes`, and returns the file path.

## Finding bar

A finding is a problem the diff introduces, or one that predates it in code it
touches, with a consequence someone will hit:

- a caller, user, or reader gets something wrong;
- a second copy that the next edit will miss;
- a broken rule from the repository's docs or `riskive/python-standards`; or
- code or prose that does nothing but must still be read and maintained, such
  as a redundant wrapper, speculative abstraction, duplicated state, needless
  configuration, a check for an impossible state, a comment that narrates
  code, or prose that `unslop` would cut.

Everything else goes in the notes: preferences, style that hides no bug,
"cleaner" or "shorter", equally valid alternatives, speculative benefits, extra
defense or error handling for cases the code can't reach, and short docstrings
that restate the code.

Label each finding:

- `issue (blocking):` breaks intended behavior, an existing caller, or a
  documented rule, risks security or stored data, or is unneeded code that
  isn't a local cleanup.
- `suggestion (non-blocking):` a defect that shows only on a path outside the
  PR's purpose, in a rare case, or as a small performance cost.
- `nitpick (non-blocking):` mechanical local cleanup.
- `issue (non-blocking, pre-existing):` a problem that predates the diff.
  Mark a small fix optional, and suggest a follow-up for a larger one.
- `question:` a fact only the author has, such as intent or a deployment
  constraint, without which you can't judge the PR. Never a preference or an
  option the PR body already weighed.

Give a defect a concrete case that goes wrong, and cleanup the correction and
what it saves. For a broken rule, cite the doc and line and name the change,
nothing else. The correction is the smallest that works, deleting or narrowing
code before adding a lock, cache, helper, or option. Prefer a casual question
("do we need X here so Y happens?") when the author is senior or the fix is
obvious. Name the specific problem, never "slop", and leave out who or what
wrote it.

## Verify

A fresh read-only verifier per report checks each finding against the source
at the head, the threads, the standards, and, for Spec, the ticket. It reads
the report and primary sources only, and returns `confirmed`, `revised` with a
corrected draft, or `refuted`, each with one line of evidence. It never refutes
a finding for being small. Drop refuted findings, with their reasons, into
`triage.md`.

Set the event from confirmed findings, pre-existing ones excluded:
`REQUEST_CHANGES` for any `issue (blocking)`; otherwise `COMMENT` for a
`question`; otherwise `APPROVE`.

## Triage

Re-check the PR's head and state first. A moved head follows [When the head
moves](references/head-moves.md); a merge or close ends the review.

Raise a finding for the user's judgment when it blocks, contradicts what the
author or another human reviewer said, or rests on an ambiguous ticket line.
Every other finding, +1s included, is routine.

When an HTML render tool is available, show the verdict header from [Rendered
header](references/rendered-report.md). Then report in Markdown:

1. The risk line, what the change does in three lines, CI at the head, what
   the author tested, and what the review didn't check. On a re-review, each
   earlier thread as addressed, unaddressed, or author replied. On the third or
   later review with blockers still open, suggest a call or rethinking the
   approach.
2. Each raised finding under its own heading, with its link, the problem and
   the case where it goes wrong, why it matters, and the full draft.
3. Routine findings one line each, with link and full draft, then each simpler
   route from the notes in one line.

Link files with one run of
`<SKILL_DIR>/scripts/file-links.sh <owner>/<repo> <n> <path>:<line>...` per PR,
pasted unchanged; hand-typed links don't resolve. Write posted comments in
lowercase after their label, with no praise.

On the user's own PR, stop here; nothing posts. Otherwise post as
[Submit](#submit) allows, or ask one question for the whole batch: approving it
as shown posts it, or the user decides or rewords by ID. A note the user wants
posted becomes a finding, and a verifier checks its claim and anchor. Record
every decision in `triage.md`.

## Submit

A review with no findings is an `APPROVE`, never a `COMMENT`, even under an
instruction to post only `COMMENT` reviews.

The user grants standing permission to submit an `APPROVE` whose only findings
are at most three nitpicks, when the risk is `low`, the reviewer named no
simpler route, and the diff doesn't touch authentication, authorization,
stored-data schemas, CI or infrastructure, or irreversible behavior. Also
submit without asking a `COMMENT` that holds a question and no raised finding,
and a batch the user approved as shown. Show any other review exactly and ask.
An instruction not to approve forbids posting the approval, not asking.

Right before submitting, re-check the head and that every target line is still
in the diff. Build `review.json` with `commit_id` (the verified head), `event`,
`body` only for unanchored findings, and `comments`, each with `path`, `line`,
`side: "RIGHT"`, and `body`. Submit once:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews -X POST --input <pr-folder>/review.json
```

Then add a `+1` reaction to each kept +1's comment. After the last PR, end with
the run directory and, per PR, whether the review was posted, skipped, or
deferred.
