---
name: git-workspace
description: Clones repos, manages worktrees. Use when tasks start or merge.
---

# Git workspace

Keep each repository in a bare-container layout:

```text
~/git/<repo>/
  .git/
  <default-branch>/
  <ticket-or-task>/
```

`<SKILL_DIR>` is the directory containing this `SKILL.md`. Each helper lists its
options under `--help`.

## Add or repair a repository

```bash
<SKILL_DIR>/scripts/add-repo.sh --repos-root ~/git <repo-url>
```

Rerun it to repair a repository whose default-branch worktree is missing.

## Inspect or synchronize the workspace

```bash
<SKILL_DIR>/scripts/list-workspace.sh --repos-root ~/git
<SKILL_DIR>/scripts/sync-workspace.sh --repos-root ~/git
```

Sync fast-forwards clean default-branch worktrees and leaves task, dirty, and
detached worktrees as they are.

## Create task worktrees

Before implementing from a default-branch worktree, create a task worktree:

```bash
<SKILL_DIR>/scripts/create-task-worktree.sh \
  --repos-root ~/git \
  --repo <repo> \
  --ticket <LINEAR-123> \
  --task <short-name> \
  --branch-prefix feature
```

Repeat `--repo` for a task that spans repositories; each gets the same branch
and worktree name. For Linear-tracked work, choose the `--ticket` ID with
`linear-gh-linking`; otherwise omit `--ticket`. Rerunning the command reuses the
worktree.

Fresh task branches have no upstream. On the first authorized push, run `git
push -u origin HEAD`.

## Remove task worktrees

Cleanup is destructive. List the exact worktrees and branches with each one's
merge, push, and PR state and your pick of which to remove, then get explicit
approval. One list can cover several tasks. Run the helper once per task with
`--yes`, because an agent shell can't answer its prompt:

```bash
<SKILL_DIR>/scripts/remove-task-worktree.sh \
  --repos-root ~/git \
  --repo <repo> \
  --ticket <LINEAR-123> \
  --task <short-name> \
  --branch-prefix <prefix> \
  --yes
```

Pass the `--branch-prefix` the task was created with. The helper also deletes a
task branch whose worktree is already gone. It refuses dirty worktrees and
unmerged commits. A commit counts as merged when its patch is on the remote or
default branch, or when `gh` shows a merged PR whose head is the branch tip.
When it refuses, report why and leave the worktree and branch in place.
