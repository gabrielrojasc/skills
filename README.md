# Gabriel's agent skills

Gabriel's reusable agent skills for Claude Code, Codex, and other coding agents.

This repository contains behavior that is specific to Gabriel's workflow but
reusable across projects. Third-party skills remain installed from their
upstream repositories. Project-specific skills stay in the projects that own
their assumptions.

## Install

List the available skills:

```bash
npx skills add gabrielrojasc/skills --list
```

Install them globally:

```bash
npx skills add gabrielrojasc/skills -g
```

The repository does not provide a second skill installer. The `skills` CLI owns
installation, updates, and lock tracking.

## Skills

### General

- [`git-workspace`](skills/git-workspace/SKILL.md) manages bare-container
  repositories under `~/git`, persistent default-branch worktrees, and isolated
  task worktrees.
- [`linear-gh-linking`](skills/linear-gh-linking/SKILL.md) keeps Linear issues
  attached to their Git branches and pull requests with accurate status
  semantics.
- [`linear-work-breakdown`](skills/linear-work-breakdown/SKILL.md) chooses among
  Linear initiatives, projects, milestones, issues, and sub-issues before any
  tracker mutation.
- [`gh-review-comments`](skills/gh-review-comments/SKILL.md) fetches unresolved
  GitHub review threads, top-level comments, and review bodies by default,
  handles routine fixes, replies, and resolutions on its own, and raises only
  the decisions that need the user's judgment.
- [`babysit-pr`](skills/babysit-pr/SKILL.md) fixes review feedback and the CI
  failures a PR causes in rounds through `gh-review-comments`, lists failures
  already on the base as follow-ups, pushes once per round, and hands the PR
  back as merge-ready, waiting on people, or blocked.
- [`full-stop`](skills/full-stop/SKILL.md) takes a change to a merge-ready PR
  while the user isn't watching: it proves the change, runs `cross-review`,
  files the PR, runs `babysit-pr`, and leaves the merge to the user.
- [`test-plan`](skills/test-plan/SKILL.md) lists the ways a feature could fail
  in prod, plans a check for each, probes which checks the agent's current
  access can run, and asks for the access the rest need.
- [`developer-documentation-style`](skills/developer-documentation-style/SKILL.md)
  reads the live Google guide before writing, editing, or reviewing developer
  documentation.
- [`python-environments`](skills/python-environments/SKILL.md) creates and
  manages project-local Python environments with `uv venv` while preserving each
  repository's dependency workflow.
- [`review-revise`](skills/review-revise/SKILL.md) runs adversarial
  review-revise loops with independent reviewers until findings are resolved or
  the loop stalls.
- [`cross-review`](skills/cross-review/SKILL.md) has the other agent review a
  code change through T3's `delegate_task`, triages the findings with
  `gh-review-comments`, fixes and commits each round, repeats until a round
  leaves nothing to fix within a budget of 3 rounds, or 5 for risky changes,
  and then pushes and records the reviewer's verdict in the PR.
- [`computer-use`](skills/computer-use/SKILL.md) drives the user's signed-in
  browser and native apps: Claude through Claude in Chrome, Codex through
  browser use and Computer Use, and Claude hands native apps to Codex.
- [`slack-message`](skills/slack-message/SKILL.md) writes Slack messages in the
  user's style with Slack markup, and uses standard Markdown when posting
  through the Slack connector.
- [`chief-of-staff`](skills/chief-of-staff/SKILL.md) tracks the user's open T3
  threads, opens each update with a GitHub stat panel from its `glance` script,
  and ranks what needs the user, with links to each chat.
- [`rewrite-it`](skills/rewrite-it/SKILL.md) rewrites text the user points at
  with the Writing section of the user's global `AGENTS.md`, and asks what to
  rewrite when the user names nothing.

Matt Pocock's skills cover general research, specification, implementation, TDD,
architecture, and review. They are intentionally not copied here.

### ZeroFox

- [`pr-review`](skills/zerofox/pr-review/SKILL.md) reviews PRs against
  repository and ZeroFox Python standards, applies the api-specialist lens to
  every riskive/API PR and adds a spec review for its own team's authors,
  verifies every finding independently, +1s bot comments it agrees with, raises
  only the findings that need the user's judgment, posts a `COMMENT` review of
  routine findings on its own, and asks before any other.

## Repository layout

```text
skills/          General personal skills
skills/zerofox/  ZeroFox-specific skills
scripts/         Repository validation
evals/           Claude Code and Codex eval harnesses
```

## Development

Validation requires Python 3.10+, Git, and Bash, with no Python packages. After
changing a skill, metadata file, or script, stage the changes and run:

```bash
scripts/validate-skills.sh
```

The validator requires a staged snapshot with no unstaged changes or untracked
validation inputs. It checks skill names, strict Codex metadata shape,
invocation-policy consistency, README links, script executability, syntax,
retired AF directories, and whitespace errors.

Run all Python tests with uv and pytest:

```bash
uv run --no-project --with pytest pytest scripts/tests skills
```

uv supplies pytest in a temporary environment. The helpers and validator still
use only the Python standard library. Run the shell regression suite separately:

```bash
bash skills/git-workspace/tests/test-upstream.sh
```

Trigger evals check that each model-invoked skill fires on the prompts it
should, and stays silent on near misses, in real Claude Code and Codex runs.
They need the `claude` and `codex` CLIs:

```bash
evals/triggers/run-evals.sh
```

The header of `run-evals.sh` documents its options. Add `--case '*<skill>*'` to
run one skill's cases, and `--installed` to make the repo skills compete with
every skill installed in `~/.agents/skills`. Cases named `hard-*` hide the
trigger inside a larger task, in the working directory, or in a terse request.
The summary reports them separately, and they don't affect the exit status.

## License

[MIT](LICENSE)
