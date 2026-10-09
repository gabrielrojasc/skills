---
name: pr-review
description: Reviews GitHub PRs. Use when reviewing a PR.
---

# PR review

Review one or more GitHub PRs with independent reviewer subagents, verify any
draft findings with fresh subagents, triage them with the user, and submit one
review per PR.

Keep every draft local until the user explicitly approves the complete review
for that PR in this session. Subagents are read-only outside their assigned
files.

Ask every question, including triage and approval, as plain text at the end of a
chat message. Never use a question or multiple-choice tool such as
`AskUserQuestion` or `request_user_input`: its fixed options can't express
decisions like "keep S1, reword S2 to ...".

## Setup

When reviewing more than one PR, also follow [Multiple
PRs](references/multiple-prs.md). When a tool to set the session title is
available, set it as [Session title](references/session-title.md) describes.

Create a private run directory with `mktemp -d`. Give each PR a folder named
`<owner>__<repo>__<number>__<short-head-sha>`. It holds `src/`, `standards.md`,
`spec.md`, `verify-<axis>-<round>-input.md`, `verify-<axis>-<round>.md`,
`triage.md`, `final-review.md`, and `review.json`. These files, not the
conversation, are the source of truth for draft text, so a summarized
conversation can't change what gets posted. Give subagents absolute paths to the
files they write and to `src/`. Report the run directory path in updates.

Fetch each PR's head into its folder with
`<SKILL_DIR>/scripts/fetch-source.sh <owner>/<repo> <head-sha> <pr-folder>/src`,
so agents read source with local tools instead of one API call per file. Agents
treat `src/` as read-only. An agent that needs another repository at a pinned
commit fetches it the same way into the run directory.

Every Markdown file starts with `## Target head` and the head SHA it was
produced against. `review.json` records the head in `commit_id`. Reject any file
whose target head differs from its folder's head. If the head moves before
submission, follow [When the head moves](references/head-moves.md).

## Check for an earlier review

Before starting reviewers, run
`<SKILL_DIR>/scripts/changes-since-review.py <owner>/<repo> <n>` for each PR and
act on its output:

- `none`: the user hasn't reviewed the PR. Review it in full.
- `same`: nothing the PR changes differs from what the user reviewed. Start no
  reviewers. Report it with the status of that review's threads, and ask
  whether to re-submit its event through [Submit](#submit) or stop. GitHub
  dismisses only approvals and change requests, so for a `DISMISSED` review,
  ask which it was.
- `changed`: review only the printed differences, reading the full diff for
  context. Report only problems the differences introduce, including breakage
  they cause elsewhere.
- `unknown`: review the full diff and tell the user why.

## Re-review

A re-review covers every PR in this session's run directories unless the user
names some. Repeat Setup and the earlier-review check for each.

## Choose the review

| PR | Standards axis | Spec axis |
|---|---|---|
| riskive/API | Repository and Python standards, api-specialist lens | Only when the author is an active member of `t-executive-protection` |
| Other Python repositories | Repository and Python standards | Yes |
| Non-Python repositories | Repository conventions | Yes |
| Dependency bumps (for example, renovate) | Upgrade risk | No |

Dependency bumps take the upgrade-risk row in every repository, riskive/API
included. For riskive/API, non-Python infrastructure, and dependency bumps, read
[Choosing the review](references/choose-review.md) before starting reviewers.

Python standards live in `riskive/python-standards` under `docs/`; use the files
relevant to the diff.

## Review

For each PR, run one Standards subagent and, when the table calls for it, one
Spec subagent. Do the setup yourself: the head check, fetching the source, the
earlier-review check, and choosing the review take a few commands. Then start
the reviewers in the background. Beyond `src/`, don't gather diffs, threads, or
source for reviewers; they read the PR themselves. Each axis moves to
verification as soon as its own reviewer returns, without waiting for the other
axis. Keep the axes in separate reports so one never masks the other:
standards-clean code can implement the wrong thing, and spec-faithful code can
break conventions.

Wait only when no work can proceed. When the host makes you poll agents, wait
several minutes per call. Codex asks for a progress update at least every 60
seconds. Write it from what you already know, such as which agents are running
and which files exist; "still running" is a complete update. Don't message a
running agent for status or to pass along CI results, threads, or other PR
state. Each agent reads the PR itself, and triage step 1 re-checks it. Message
an agent only to stop it, when its head moved or its PR closed.

### Standards axis

The Standards agent judges code, documentation, and agent instructions against
the chosen standards. It does not check the ticket or acceptance criteria. The
repository's standards are its `AGENTS.md`, the docs it points to, and any file
under `docs/` about how code is written. Alongside them, always apply Fowler's
code smells (*Refactoring*, chapter 3); where the two conflict, the repository
wins.

When the diff changes documentation, agent instructions, or documentation
automation, reviewers and verifiers read [Documentation and agent
instructions](references/documentation-review.md).

### Spec axis

Before starting a Spec agent, look for Linear issue IDs, such as `EPL-123`, in
the PR title, branch, body, and commit messages. With none, record "no spec
available" for the axis and start no Spec agent or verifier.

The Spec agent judges whether the diff implements what the originating ticket
asks:

1. Report only requirements that are missing, partial, or implemented wrong, and
   quote the ticket line for each. Extra changes are fine unless they are
   themselves wrong or risky.
2. If the ticket has no real spec, or doesn't describe this change, report "no
   spec available" and stop. Don't infer requirements from the PR description.

### Finding bar

Report blockers (broken behavior, real defects, security holes, missing or wrong
requirements) and major tech-debt introduction. Report only problems the diff
introduces, including breakage it causes in unchanged code and requirements it
leaves missing. Don't flag unrelated existing debt. Every other finding needs a
consequence of leaving it as is:

- a caller or reader who will get something wrong;
- a second copy the next edit will miss;
- a condition that cannot be false or code that cannot run, when you can name
  the case a reader would wrongly assume exists;
- a rule in the repository's docs or `riskive/python-standards` that the change
  breaks; or
- code that does nothing or prose from the list below, which later readers must
  read, trust, or maintain for nothing.

The bar works in both directions. A finding with a consequence is reported
however small it is. A true observation without one goes in the notes however
tempting it is, along with preferences, equally valid alternatives, and
speculative future benefits. "Cleaner", "could be shorter", "the precedent does
it the other way", or log volume alone is not a consequence. A documentation
loss caused by deletion is tested by the documentation guidance instead.

Hold every PR to this bar for unnecessary code and prose: redundant wrappers,
speculative abstractions, duplicated state, needless configuration, custom logic
that an existing framework hook covers, defensive checks for impossible states,
comments that narrate code, and unsupported claims. Apply unslop to prose. Allow
none of it in any PR. Short docstrings are fine even when they restate the code,
especially on classes; flag a docstring only when it is wrong or misleading, or
long enough that keeping it in sync with the code is real work. Group instances
only when they share the same problem and the same fix; a misleading claim and a
redundant one are separate findings. Name the specific problem rather than
calling it slop, and don't speculate about who or what wrote it.

When a broken standards rule is the only consequence, the draft cites the doc
and line, then names the change, and says nothing else. The team settled the
impact when it wrote the rule.

The correction must preserve required behavior, useful information, contracts,
and conventions, and should be local and proportionate. Missing evidence is a
verification gap, not proof of redundancy. Cleanup findings are nonblocking
unless they independently meet the blocker or major-debt bar.

### Rules for every reviewer

1. Read the PR metadata, diff, and existing review threads, and read source from
   `src/` in the PR folder. Don't repeat a point already raised or resolved. If
   the user reviewed the PR before, report the status of each of their earlier
   threads: addressed, unaddressed, or author replied.
2. Anchor a finding inline when a specific changed line owns the problem;
   otherwise draft it for the review body. Never invent an anchor.
3. Each draft states the problem concisely. For defects and spec gaps, give a
   concrete example of what goes wrong. For cleanup, say what is unnecessary or
   misleading, its consequence, and the correction. Prefer a casual question
   ("do we need X here so Y happens?") when the author is senior or the fix is
   obvious.
4. Write the result with headings `## Target head`, `## Verdict` (APPROVE,
   COMMENT, or REQUEST_CHANGES with one line of reasoning), `## Comment drafts`
   (`- **file:line** — text` using new-file line numbers, or
   `- **review body** — text`), and
   `## Notes for the reviewer (not for posting)`. Spec agents use
   `## Spec verdict` and `## Spec findings`. Return only the file path and the
   verdict line.
5. If nothing qualifies, return APPROVE with no drafts. No praise.

## Verify

No draft reaches the user unverified. An axis with no drafts skips verification;
report it as "no review issues found". When no axis has drafts, re-check the
head and PR state yourself and go to [Submit](#submit).

After an axis's reviewer returns drafts, the orchestrator assigns stable
axis-prefixed IDs (`S1`, `P1`) and writes only the IDs, draft text, and any
`user-promoted` marker to the round's input file. A fresh, read-only verifier
per axis per round checks every draft against the diff and source at the target
head, existing threads, the applicable standards, and, for Spec, the ticket. It
reads only its input file and primary sources, including the fetched source in
the run directory, never other files there.

The verifier returns one verdict per ID with one line of evidence:

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

For a `user-promoted` draft, check only the claim and anchor.

The verifier may add new findings, which get fresh IDs. When a round leaves a
draft at `revise` or adds a finding, follow [Further verification
rounds](references/verify-rounds.md) before triage.

The orchestrator then sets the axis verdict from the confirmed set. Nonblocking
findings alone mean COMMENT, not REQUEST_CHANGES. Refuted and dropped drafts
stay in `triage.md` with their reasons so the user can overrule.

## Triage

1. Re-check the PR's head, state, last update time, and reviews. A moved head
   follows [When the head moves](references/head-moves.md); a merge or close
   ends the review.
2. Show the Standards verdict and findings, then the Spec verdict and findings.
   Give each confirmed finding its own heading and each field its own paragraph,
   so the user can scan the batch and decide without opening any file:

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
   one. Show a `wording unsettled` finding with the confirmed ones, marked in
   its heading, and add a **Wording:** line with the sticking point. After the
   confirmed findings, show refuted and dropped drafts with reasons, then the
   reviewer notes.
3. Show the whole batch in one message, then ask one question at the end, not
   one per finding. The user may keep all, give decisions by ID (for example,
   "keep S1 S3, drop S2, reword P1 to ..."), go one by one, or decide some by ID
   and go one by one through the rest. Record every decision in `triage.md`.
4. One by one means one block at a time, with a short explanation of the
   surrounding code, waiting for a decision before the next. Findings the user
   already decided are skipped.
5. A note the user wants raised becomes a new draft marked `user-promoted`. It
   gets one verification round for claim and anchor only; the user's decision
   replaces the consequence test.
6. Link every file mention shown to the user to the PR's Files changed view.
   Print all of a PR's links with one run of
   `<SKILL_DIR>/scripts/file-links.sh <owner>/<repo> <n> <path>:<line>...` and
   paste each printed link unchanged, even for a familiar path. A link typed by
   hand tends to carry the old MD5 hash or a space before `R<line>`, and GitHub
   resolves neither. Posted comment bodies stay plain.
7. Write posted comments in lowercase, with no praise or follow-up-ticket
   suggestions.

## Submit

Assemble `final-review.md` with the review event, every kept inline comment in
order, and a review body only for kept findings without an inline anchor. Show
the exact package and ask for explicit approval. Deciding to keep a finding is
not approval to submit.

Immediately before submitting, re-check the head, confirm every target line is
still in the diff, and confirm `final-review.md` matches what the user approved.
Build `review.json` in the PR folder from that file and confirm its head, event,
body, and comments match it. A moved head follows [When the head
moves](references/head-moves.md). Any other change means rebuilding the package
and asking again. Submit it once, as one review with all inline comments, and
publish no standalone PR comments:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews -X POST --input <pr-folder>/review.json
```

The JSON has `commit_id` (the verified head), `event`, `body` (omit when empty),
and `comments`, each with `path`, `line`, `side: "RIGHT"`, and `body`.

End with the run directory path and, per PR, whether the review was posted,
skipped, or deferred.
