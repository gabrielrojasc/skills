# Repository guidance

## Scope

- This repository owns Gabriel's portable personal agent skills.
- Maintain this repository in its existing `main` checkout. Create a branch or worktree only when the user asks for one.
- Install third-party skills from their upstream repositories. Keep their source out of this repository.
- Keep project-specific skills in the project that owns their assumptions and tooling.

## Skill structure

- Put each installable skill under `skills/<name>/`.
- Give every skill a `SKILL.md` whose frontmatter name matches its directory.
- Add `agents/openai.yaml` for Codex display metadata and invocation policy.
- Write each description as a compact, unquoted, single-line `Use when...` entrypoint. Keep the `SKILL.md` description and `agents/openai.yaml` `interface.short_description` identical so agents receive the same trigger from either source.
- Keep ordered agent steps in `SKILL.md`. Move branch-specific reference material behind a direct pointer under `references/`.
- Put repeatable mechanics in `scripts/`. Keep cross-task policy in the global guidance template and domain-specific workflow in the skill that triggers it.
- Choose model invocation only when the agent must discover the skill itself. Otherwise set `disable-model-invocation: true`.

## Change rules

- Keep `README.md` and the skill inventory in sync.
- Run `scripts/validate-skills.sh` after changing skills, metadata, or scripts.
- Preserve approval gates for external writes, worktree removal, and branch deletion.
- Do not change global installations, global agent guidance, or external services as part of a repository edit without explicit approval.
