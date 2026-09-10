# Gabriel's agent skills

Portable personal skills for Codex and other compatible coding agents.

This repository contains behavior that is specific to Gabriel's workflow but reusable across projects. Third-party skills remain installed from their upstream repositories. Project-specific skills stay in the projects that own their assumptions.

## Install

List the available skills:

```bash
npx skills add gabrielrojasc/skills --list
```

Install them globally:

```bash
npx skills add gabrielrojasc/skills -g
```

The repository does not provide a second skill installer. The `skills` CLI owns installation, updates, and lock tracking.

## Skills

- [`git-workspace`](skills/git-workspace/SKILL.md) manages bare-container repositories under `~/git`, persistent default-branch worktrees, and isolated task worktrees.
- [`linear-gh-linking`](skills/linear-gh-linking/SKILL.md) keeps Linear issues attached to their Git branches and pull requests with accurate status semantics.
- [`linear-work-structure`](skills/linear-work-structure/SKILL.md) chooses among Linear initiatives, projects, milestones, issues, and sub-issues before any tracker mutation.
- [`evidence-comparison-report`](skills/evidence-comparison-report/SKILL.md) creates persistent, auditable comparison reports with explicit write authority and evidence controls.
- [`gh-review-comments`](skills/gh-review-comments/SKILL.md) fetches unresolved GitHub review threads, top-level comments, and review bodies by default and proposes fix, dismissal, or already-addressed decisions before any mutation.
- [`developer-documentation-style`](skills/developer-documentation-style/SKILL.md) reads the live Google guide before writing, editing, or reviewing developer documentation.
- [`file-pr`](skills/file-pr/SKILL.md) reviews the committed branch diff and opens one concise pull request without changing code.
- [`python-environments`](skills/python-environments/SKILL.md) creates and manages project-local Python environments with `uv venv` while preserving each repository's dependency workflow.
- [`mermaid-validation`](skills/mermaid-validation/SKILL.md) renders and inspects changed Mermaid diagrams with Mermaid CLI.
- [`review-revise`](skills/review-revise/SKILL.md) runs bounded adversarial review-revise loops with independent reviewers and evidence-backed revisions.

Matt Pocock's skills cover general research, specification, implementation, TDD, architecture, and review. They are intentionally not copied here.

## Repository layout

```text
skills/       Installable personal skills
scripts/      Repository validation
```

## Development

Validation requires Python 3.10+, Git, and Bash, with no Python packages.
After changing a skill, metadata file, or script, stage the changes and run:

```bash
scripts/validate-skills.sh
```

The validator requires a staged snapshot with no unstaged changes or untracked
validation inputs. It checks skill names, strict Codex metadata shape,
invocation-policy consistency, README links, script executability, syntax,
retired AF directories, and whitespace errors.

Run all Python tests with uv and pytest:

```bash
uv run --no-project --with pytest pytest scripts/tests skills/*/tests
```

uv supplies pytest in a temporary environment. The helpers and validator still
use only the Python standard library. Run the shell regression suite separately:

```bash
bash skills/git-workspace/tests/test-upstream.sh
```

## License

[MIT](LICENSE)
