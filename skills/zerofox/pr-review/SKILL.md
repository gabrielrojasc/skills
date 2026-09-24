---
name: pr-review
description: Reviews GitHub PRs. Use when reviewing a PR.
---

# PR review

Review one or more GitHub PRs with independent reviewer and verifier subagents, triage the verified findings with the user, and submit one review per PR. The skill is self-contained and does not depend on any other review skill.

Keep every draft local until the user explicitly approves the complete review for that PR in this session. Subagents are read-only outside their assigned files.

## Setup

Accept PR URLs or `<repo>#<number>` refs. Resolve a bare number against the current directory's repository when it is a git checkout; otherwise ask.

Create a private run directory with `mktemp -d` under `${TMPDIR:-/tmp}` and mode `0700`. Give each PR a folder named `<owner>__<repo>__<number>__<short-head-sha>`. It holds `standards.md`, `spec.md`, `verify-<axis>-<round>-input.md`, `verify-<axis>-<round>.md`, `triage.md`, `final-review.md`, and `review.json`. These files, not the conversation, are the source of truth for draft text, so a summarized conversation can't change what gets posted. Give subagents absolute paths to the files they write. Report the run directory path in updates and in the final tally.

Every Markdown file starts with `## Target head` and the head SHA it was produced against. `review.json` records the head in `commit_id`. Reject any file whose target head differs from its folder's head. If a PR's head moves before submission, start a new folder for the new head and rerun review and verification against the full diff.

## Choose the review

| PR | Standards axis | Spec axis |
|---|---|---|
| riskive/API, author is an active member of `t-executive-protection` | Repository and Python standards, api-specialist lens | Yes |
| riskive/API, any other author | Repository and Python standards, api-specialist lens | No |
| Other Python repositories | Repository and Python standards | Yes |
| Non-Python repositories | Repository conventions | Yes |
| Dependency bumps (for example, renovate) | Upgrade risk | No |

Dependency bumps take the upgrade-risk row in every repository, riskive/API included. Check team membership with `gh api orgs/riskive/teams/t-executive-protection/memberships/<author>`: Only `state: active` counts as a member; `pending` or a 404 does not.

Python standards live in `riskive/python-standards` under `docs/`. List the directory and fetch the files relevant to the diff as raw content.

The api-specialist lens (source: Linear doc `api-specialist-role-summary-9525ac5b9fc7`; re-fetch it if it may have changed) checks adherence to API patterns and standards, code placement and organization, use of Django and DRF to reduce risk and debt, code smells, and consistency across implementations. The lens excludes validating business correctness or acceptance criteria, which the Spec axis covers when it runs, and solving the team's problems for them.

For non-Python infrastructure, also check secrets handling, environment separation, and pipeline correctness against sibling `riskive/*-terra` repositories and `riskive/zf-ci` workflows. For dependency bumps, review CI state, changelog breaking changes, uses of removed APIs, and lockfile consistency (`pyproject.toml` and `poetry.lock` change together).

## Review

For each PR, run one Standards subagent and, when the table calls for it, one Spec subagent, in parallel and in the background. Sibling PRs with identical changes, such as matching renovate configs, may share one Standards agent with a folder per PR. Keep the axes in separate reports so one never masks the other: standards-clean code can implement the wrong thing, and spec-faithful code can break conventions.

### Standards axis

The Standards agent judges code, documentation, and agent instructions against the chosen standards. It does not check the ticket or acceptance criteria. Use Fowler's code smells (*Refactoring*, chapter 3) as shared vocabulary; repository conventions override them.

When the diff changes documentation, agent instructions, or documentation automation, reviewers and verifiers read [Documentation and agent instructions](references/documentation-review.md).

### Spec axis

The Spec agent judges whether the diff implements what the originating ticket asks:

1. Find the Jira key or Linear ref in the PR title, branch, body, or commits. Fetch it with `acli jira workitem view <key> --fields '*all'` or the Linear MCP `get_issue`.
2. Report only requirements that are missing, partial, or implemented wrong, and quote the ticket line for each. Extra changes are fine unless they are themselves wrong or risky.
3. If there is no ticket or no real spec on it, report "no spec available" and stop. Don't infer requirements from the PR description.

### Finding bar

Report blockers (broken behavior, real defects, security holes, missing or wrong requirements) and major tech-debt introduction. Report only problems the diff introduces, including breakage it causes in unchanged code and requirements it leaves missing. Don't flag unrelated existing debt. Every other finding needs a consequence of leaving it as is:

- a caller or reader who will get something wrong;
- a second copy the next edit will miss;
- a condition that cannot be false or code that cannot run, when you can name the case a reader would wrongly assume exists; or
- a rule in the repository's docs or `riskive/python-standards` that the change breaks; or
- unnecessary code or prose from the list below, which later readers must read, trust, or maintain for nothing.

The bar works in both directions. A finding with a consequence is reported however small it is. A true observation without one goes in the notes however tempting it is, along with preferences, equally valid alternatives, and speculative future benefits. "Cleaner", "could be shorter", "the precedent does it the other way", or log volume alone is not a consequence. A documentation loss caused by deletion is tested by the documentation guidance instead.

Hold every PR to this bar for unnecessary code and prose: redundant wrappers, speculative abstractions, duplicated state, needless configuration, custom logic that an existing framework hook covers, defensive checks for impossible states, comments that narrate code, boilerplate docstrings, and unsupported claims. Apply unslop to prose. Allow none of this in any PR, and name the specific consequence in each draft. Group repeated instances that share one fix into a single finding. Name the specific problem rather than calling it slop, and don't speculate about who or what wrote it.

When a broken standards rule is the only consequence, the draft cites the doc and line, then names the change, and says nothing else. The team settled the impact when it wrote the rule.

Inspect callers, framework behavior, and configuration before proposing a correction. The correction must preserve required behavior, useful information, contracts, and conventions, and should be local and proportionate. Missing evidence is a verification gap, not proof of redundancy. Cleanup findings are nonblocking unless they independently meet the blocker or major-debt bar.

### Rules for every reviewer

1. Read the PR metadata, diff, and existing review threads. Don't repeat a point already raised or resolved. If the user reviewed the PR before, report the status of each of their earlier threads: addressed, unaddressed, or author replied.
2. Anchor a finding inline when a specific changed line owns the problem; otherwise draft it for the review body. Never invent an anchor.
3. Each draft states the problem concisely. For defects and spec gaps, give a concrete example of what goes wrong. For cleanup, say what is unnecessary or misleading, its consequence, and the correction. Prefer a casual question ("do we need X here so Y happens?") when the author is senior or the fix is obvious.
4. Write the result with headings `## Target head`, `## Verdict` (APPROVE, COMMENT, or REQUEST_CHANGES with one line of reasoning), `## Comment drafts` (`- **file:line** — text` using new-file line numbers, or `- **review body** — text`), and `## Notes for the reviewer (not for posting)`. Spec agents use `## Spec verdict` and `## Spec findings`. Return only the file path and the verdict line.
5. If nothing qualifies, return APPROVE with no drafts. No praise.

## Verify

No draft reaches the user unverified. After an axis's reviewer returns, the orchestrator assigns stable axis-prefixed IDs (`S1`, `P1`) and writes only the IDs, draft text, and any `user-promoted` marker to the round's input file. A fresh, read-only verifier per axis per round checks every draft against the diff and source at the target head, existing threads, the applicable standards, and, for Spec, the ticket. It reads only its input file and primary sources, never other files in the run directory.

The verifier returns one verdict per ID with one line of evidence:

- **confirmed:** the claim, anchor, and consequence hold, nothing elsewhere already handles it, and it meets the finding bar. A rule-only draft that argues impact is trimmed to the citation and the change and still confirmed; the verifier keeps the removed argument in its evidence.
- **revise:** the concern is real but the claim, anchor, or consequence is off. Include a corrected draft.
- **refuted:** the claim doesn't hold or the finding misses the bar. Never refute a finding for being small.

For a `user-promoted` draft, check only the claim and anchor.

The verifier may add new findings. They get fresh IDs and go through the next round with the revised drafts. An agent never verifies a draft it wrote or revised. Stop after three rounds; anything still unconfirmed is dropped and listed as "unverified, dropped" with its sticking point. Then the orchestrator sets the axis verdict from the confirmed set. Nonblocking findings alone mean COMMENT, not REQUEST_CHANGES. Refuted and dropped drafts stay in `triage.md` with their reasons so the user can overrule.

## Triage

Take one PR at a time.

1. Re-check `updatedAt`, `headRefOid`, `reviews`, and `state`. A moved head, a merge, or a close changes the plan.
2. Show the Standards verdict and findings, then the Spec verdict and findings. Give each confirmed finding its own block so the user can decide without opening any file:

   ```markdown
   **S1** · blocking · inline at [path:line](link)
   Problem: what the code does, and the concrete input or case where it goes wrong.
   Why it matters: who is affected and how. For Spec, quote the ticket line.
   Comment:
   > the exact draft that would be posted
   ```

   Keep the problem and the reason to a sentence or two each, but always show the full draft. Add the trimmed impact argument when the verifier removed one. After the confirmed findings, show refuted and dropped drafts with reasons, then the reviewer notes.
3. Show the whole batch in one message, then ask one question at the end, not one per finding. The user may keep all, give decisions by ID (for example, "keep S1 S3, drop S2, reword P1 to ..."), go one by one, or decide some by ID and go one by one through the rest. Record every decision in `triage.md`.
4. One by one means one block at a time, with a short explanation of the surrounding code, waiting for a decision before the next. Findings the user already decided are skipped.
5. A note the user wants raised becomes a new draft marked `user-promoted`. It gets one verification round for claim and anchor only; the user's decision replaces the consequence test.
6. Link every file mention shown to the user to the PR's Files changed view: `[<path>:<line>](https://github.com/<owner>/<repo>/pull/<n>/files#diff-<sha256 of path>R<line>)`. Posted comment bodies stay plain.
7. Write posted comments in lowercase, with no praise or follow-up-ticket suggestions.

## Submit

Assemble `final-review.md` with the review event, every kept inline comment in order, and a review body only for kept findings without an inline anchor. Show the exact package and ask for explicit approval. Keep decisions on individual findings are not approval to submit.

Immediately before submitting, re-check the head, confirm every target line is still in the diff, and confirm `final-review.md` matches what the user approved. Build `review.json` in the PR folder from that file and confirm its head, event, body, and comments match it. Any change means rebuilding the package and asking again. Submit it once, as one review with all inline comments, and publish no standalone PR comments:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews -X POST --input <pr-folder>/review.json
```

The JSON has `commit_id` (the verified head), `event`, `body` (omit when empty), and `comments`, each with `path`, `line`, `side: "RIGHT"`, and `body`.

End with the run directory path and, per PR, whether the review was posted, skipped, or deferred.
