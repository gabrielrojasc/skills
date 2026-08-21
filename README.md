# Gabriel's agent skills

Portable personal skills and workstation guidance for Codex and other compatible coding agents.

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
- [`evidence-comparison-report`](skills/evidence-comparison-report/SKILL.md) creates persistent, auditable comparison reports with explicit write authority and evidence controls.
- [`gh-review-comments`](skills/gh-review-comments/SKILL.md) fetches unresolved GitHub review threads and proposes fix, dismissal, or already-addressed decisions before any mutation.

Matt Pocock's skills cover general research, specification, implementation, TDD, architecture, and review. They are intentionally not copied here.

## Global guidance

Print the Linear-first user-level `AGENTS.md` section:

```bash
scripts/render-global-agents-snippet.sh
```

The renderer writes to stdout only. See [`docs/global-agents-guidance.md`](docs/global-agents-guidance.md) for the ownership boundary and merge instructions.

## Repository layout

```text
skills/       Installable personal skills
scripts/      Repository validation and guidance rendering
templates/    Source templates for generated guidance
docs/         Supporting documentation
```

## Development

After changing a skill, metadata file, or script, run:

```bash
scripts/validate-skills.sh
```

The validator checks skill names, strict Codex metadata shape, invocation-policy consistency, README links, script executability, syntax, retired AF directories, and whitespace errors in staged or unstaged changes.

## License

[MIT](LICENSE)
