---
name: git-workspace
description: Manage bare-container repositories under ~/git and their isolated task worktrees. Use when adding, repairing, listing, or syncing repository containers, or when implementation needs a task worktree outside the persistent default-branch checkout.
---

# Git workspace

Keep each repository in a bare-container layout:

```text
~/git/<repo>/
  .git/
  <default-branch>/
  <ticket-or-task>/
```

The default-branch worktree is for browsing and synchronization. Implementation normally happens in a task worktree. An explicit user choice to use the current checkout overrides that default.

Resolve `<SKILL_DIR>` as the directory containing this `SKILL.md` before running a bundled helper.

## Add or repair a repository

```bash
<SKILL_DIR>/scripts/add-repo.sh --repos-root ~/git <repo-url>
```

Use `--repo-name <name>` to override the directory derived from the URL. Use `--from-manifest <file>` for lines formatted as `<repo-url> [repo-name]`.

The helper creates or repairs the bare repository, detects the remote default branch, and creates its persistent default-branch worktree. It stops if an existing destination is not a matching bare-container repository.

## Inspect or synchronize the workspace

```bash
<SKILL_DIR>/scripts/list-workspace.sh --repos-root ~/git
<SKILL_DIR>/scripts/sync-workspace.sh --repos-root ~/git
```

Synchronization fetches every managed repository and fast-forwards only clean default-branch worktrees. Task worktrees are reported but not modified.

## Create task worktrees

Create the worktree before implementation when the current checkout is a persistent default-branch worktree:

```bash
<SKILL_DIR>/scripts/create-task-worktree.sh \
  --repos-root ~/git \
  --repo <repo> \
  --ticket <LINEAR-123> \
  --task <short-name> \
  --branch-prefix feature
```

Repeat `--repo` when one task changes multiple repositories. The helper creates the same branch and worktree name in each selected repository. Omit `--ticket` for work without a tracker issue.

Rerunning the same command reuses an exact registered worktree. A conflicting path, branch, or registration stops the run.

## Remove task worktrees

Cleanup is destructive. Present the exact worktrees and branches first, then get explicit human approval before running:

```bash
<SKILL_DIR>/scripts/remove-task-worktree.sh \
  --repos-root ~/git \
  --repo <repo> \
  --ticket <LINEAR-123> \
  --task <short-name>
```

The helper blocks dirty worktrees and branches with unpushed commits. It uses `git worktree remove` and safe branch deletion with `git branch -d`. Never replace those operations with force deletion.

## Completion criteria

- Every selected repository resolves inside the requested repositories root.
- Default branches come from current remote refs.
- Existing worktrees are reused only when path and branch both match.
- Synchronization leaves task worktrees unchanged.
- Cleanup preserves dirty, unpushed, or unmerged work.
