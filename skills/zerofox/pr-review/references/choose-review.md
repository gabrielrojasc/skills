# Choosing the review

## riskive/API

Run
`<SKILL_DIR>/scripts/team-member.sh riskive/t-executive-protection <author>`.
On `member`, run the Spec axis; on `not-member`, skip it. On `unknown`, start
the Standards axis, which is the same either way, and ask the user whether to
run the Spec axis.

The api-specialist lens follows `docs/api_specialist_review.md` in riskive/API.
Read it and the convention docs it links that are relevant to the diff, from
the PR's base branch. Keep its exclusions. Correctness and acceptance criteria
belong to the Spec axis when it runs.

## Non-Python infrastructure

Also check secrets handling, environment separation, and pipeline correctness
against sibling `riskive/*-terra` repositories and `riskive/zf-ci` workflows.

## Dependency bumps

Review CI state, changelog breaking changes, uses of removed APIs, and lockfile
consistency (`pyproject.toml` and `poetry.lock` change together).
