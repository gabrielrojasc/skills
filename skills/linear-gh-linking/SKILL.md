---
name: linear-gh-linking
description: Defines Linear links. Use when naming branches or linking PRs.
---

# Linear GitHub linking

Supply Linear linking rules to the workflows that own Git branches and pull
requests. `git-workspace` creates branches. `file-pr` pushes branches and creates
pull requests. This skill selects issue IDs and relationship semantics.
Repository conventions take precedence over its examples.

## Choose the issue

1. Apply these rules only to Linear-tracked work. Work without a Linear issue
   needs no Linear link.
2. Confirm that the work has an executable Linear issue or sub-issue.
   - If none exists, stop before branching and apply `linear-work-structure` to
     propose the missing executable work.
   - If one may exist but its exact ID is unavailable, retrieve it through a
     read-only Linear lookup. If it cannot be verified, stop and request the ID.
3. Preserve the verified ID. Do not infer it from another tracker or reuse its
   number with a different prefix.

## Link the branch

Tell `git-workspace` to pass the exact issue ID through `--ticket ENG-123`. Its
helper lowercases the ID while preserving the repository's required branch
prefix. For example:

```text
feature/eng-123-short-description
```

Prefer one primary Linear issue per branch. A pull request may link other issues
when the delivered work genuinely spans them.

## Link the pull request

The issue ID in the branch name or pull request title is enough to create a
link and may trigger the team's configured workflow automation.

Add a magic word when the branch does not contain every intended issue or when
the relationship must control merge automation.

- A closing word such as `Fixes ENG-123` enables the configured merge
  transition. Use it when the pull request completes the issue scope.
- A non-closing word such as `Part of ENG-123` preserves intermediate workflow
  automation but skips the merge transition. Use it when the issue remains open.
- A relation word such as `Related to ENG-123` creates a relationship without
  status changes.

One magic word may precede several issue IDs when they share the same
relationship. Use separate lines when their relationships differ. Use `skip` or
`ignore` with an issue ID when the user wants to suppress its automatic link.

Commit-message linking depends on workspace configuration. Do not rely on it as
the only link.

## Verify the link

After a pull request is published, read every intended Linear issue and confirm
that:

- the intended branch or pull request is attached
- every referenced issue is correct
- closing, non-closing, and relation words match what the change delivers

For a local branch created by `git-workspace`, attachment verification remains
pending until a publication-owning workflow runs.

## Completion criteria

- Every intended Linear issue and relationship type is identified.
- For a new Linear-tracked branch, `git-workspace` receives the exact issue ID.
- For a published pull request, every intended Linear attachment and
  relationship type is verified.
- Branch-only work reports that attachment verification is pending.
- Repository branch and pull request conventions remain intact.
- No closing relationship claims more completion than the pull request delivers.
