#!/usr/bin/env python3
"""Create and remove task worktrees after checking every selected repository."""

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
import re

from workspace_core import (
    WorkspaceError,
    checked_container,
    current_branch,
    default_branch,
    git,
    is_dirty,
    log,
    ref_exists,
    root_path,
    under,
    validate_repo_name,
    worktrees,
)


@dataclass
class TaskPlan:
    repository: Path
    path: Path
    branch: str
    action: str
    base: str = ""


def task_identity(args: Namespace) -> tuple[str, str]:
    if not args.task or not args.repo:
        raise WorkspaceError("Pass --task and at least one --repo.", 2)
    prefix = args.branch_prefix
    if (
        prefix in ("", ".", "..")
        or prefix.startswith("-")
        or not re.fullmatch(r"[A-Za-z0-9._-]+", prefix)
    ):
        raise WorkspaceError(f"Unsafe branch prefix: {prefix}", 2)
    name = f"{args.ticket}-{args.task}" if args.ticket else args.task
    identifier = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not identifier:
        raise WorkspaceError("Task and ticket do not produce a safe worktree name.", 2)
    branch = f"{prefix}/{identifier}"
    if git(None, "check-ref-format", "--branch", branch, check=False).returncode:
        raise WorkspaceError(f"Invalid branch name: {branch}", 2)
    return identifier, branch


def task_path(repository: Path, identifier: str) -> Path:
    path = repository / identifier
    if not under(path.resolve(), repository):
        raise WorkspaceError(f"Worktree resolves outside the repository: {path}")
    return path


def rollback(plan: TaskPlan) -> bool:
    """Leave unknown paths and any branch Git refuses to delete untouched."""
    try:
        registered = worktrees(plan.repository)
        if any(item.path == plan.path for item in registered):
            git(plan.repository, "worktree", "remove", str(plan.path))
        elif plan.path.exists() or plan.path.is_symlink():
            raise WorkspaceError(
                f"Rollback found an unregistered path at {plan.path}; left it untouched."
            )
        if plan.action == "create" and ref_exists(
            plan.repository, f"refs/heads/{plan.branch}"
        ):
            if any(item.branch == plan.branch for item in worktrees(plan.repository)):
                raise WorkspaceError(
                    f"Rollback could not delete attached branch {plan.branch} in {plan.repository}."
                )
            git(plan.repository, "branch", "-d", "--", plan.branch)
        return True
    except WorkspaceError as error:
        log("error", f"Rollback failed for {plan.path}: {error}")
        return False


def create_tasks(args: Namespace) -> int:
    identifier, branch = task_identity(args)
    root = root_path(args.repos_root)
    plans: list[TaskPlan] = []
    for name in dict.fromkeys(args.repo):
        repository = checked_container(root, validate_repo_name(name))
        path = task_path(repository, identifier)
        registered = worktrees(repository)
        if any(item.path == path for item in registered):
            actual = current_branch(path)
            if actual != branch:
                raise WorkspaceError(
                    f"Registered worktree uses {actual or 'HEAD'}, expected {branch}: {path}"
                )
            plans.append(TaskPlan(repository, path, branch, "reuse"))
            continue
        if path.exists() or path.is_symlink():
            raise WorkspaceError(f"Path exists but is not the expected registered worktree: {path}")
        if ref_exists(repository, f"refs/heads/{branch}"):
            if any(item.branch == branch for item in registered):
                raise WorkspaceError(f"Branch is already attached to another worktree: {name} {branch}")
            plans.append(TaskPlan(repository, path, branch, "attach"))
        else:
            git(repository, "fetch", "--quiet", "--prune", "origin")
            base = default_branch(repository, refresh=True)
            plans.append(TaskPlan(repository, path, branch, "create", base))

    completed: list[TaskPlan] = []
    reused = 0
    for plan in plans:
        if plan.action == "reuse":
            log("info", f"Reusing {plan.path}")
            reused += 1
            continue
        try:
            if plan.action == "attach":
                git(plan.repository, "worktree", "add", str(plan.path), plan.branch)
                log("success", f"Attached {plan.path} to {plan.branch}")
            else:
                # A task gets its upstream on first push, not from its starting point.
                git(
                    plan.repository, "worktree", "add", "--no-track", str(plan.path),
                    "-b", plan.branch, f"refs/remotes/origin/{plan.base}",
                )
                log("success", f"Created {plan.path} from origin/{plan.base}")
            completed.append(plan)
        except WorkspaceError as error:
            log("error", f"Could not {plan.action} {plan.path}: {error}")
            results = [rollback(item) for item in [plan, *reversed(completed)]]
            if all(results):
                log("info", "Rolled back worktrees created by this invocation.")
            else:
                log("error", "Rollback was incomplete. Inspect the paths reported above.")
            return 1
    print(f"\nTask: {identifier}\nBranch: {branch}\nCreated: {len(completed)}\nReused: {reused}")
    return 0


def unmerged_count(repository: Path, branch: str) -> int:
    ref = f"refs/heads/{branch}"
    upstream = git(repository, "for-each-ref", "--format=%(upstream)", ref).stdout.strip()
    if upstream and ref_exists(repository, upstream):
        reference = upstream
    elif ref_exists(repository, f"refs/remotes/origin/{branch}"):
        reference = f"refs/remotes/origin/{branch}"
    else:
        reference = f"refs/remotes/origin/{default_branch(repository)}"
    # Rebase and cherry-pick merges give merged commits new hashes, so compare patches.
    lines = git(repository, "cherry", reference, ref).stdout.splitlines()
    if any(not line.startswith(("+ ", "- ")) for line in lines):
        raise WorkspaceError(f"Cannot determine whether {branch} has unpushed commits.")
    return sum(line.startswith("+ ") for line in lines)


def delete_branch(plan: TaskPlan) -> bool:
    if not git(plan.repository, "branch", "-d", "--", plan.branch, check=False).returncode:
        log("success", f"Deleted {plan.branch}")
        return True
    if unmerged_count(plan.repository, plan.branch):
        log("warning", f"Safe branch deletion refused {plan.branch}; it has unmerged commits.")
        return False
    git(plan.repository, "branch", "-D", "--", plan.branch)
    log("success", f"Deleted {plan.branch}; every commit's patch is on the base branch")
    return True


def remove_tasks(args: Namespace) -> int:
    identifier, branch = task_identity(args)
    root = root_path(args.repos_root)
    plans: list[TaskPlan] = []
    for name in dict.fromkeys(args.repo):
        repository = checked_container(root, validate_repo_name(name))
        path = task_path(repository, identifier)
        registered = worktrees(repository)
        matching = next((item for item in registered if item.path == path), None)
        if matching is None:
            if path.exists() or path.is_symlink():
                raise WorkspaceError(f"Path exists but is not a registered task worktree: {path}")
            if not ref_exists(repository, f"refs/heads/{branch}"):
                log("info", f"No matching worktree or branch in {name}; skipping.")
                continue
            action = "branch"
        else:
            actual = current_branch(path)
            if actual != branch:
                raise WorkspaceError(f"Worktree uses {actual or 'HEAD'}, expected {branch}: {path}")
            if matching.locked:
                raise WorkspaceError(f"Worktree is locked: {path}")
            if is_dirty(path):
                raise WorkspaceError(f"Worktree has uncommitted changes: {path}")
            action = "remove"
        git(repository, "fetch", "--quiet", "--prune", "origin")
        ahead = unmerged_count(repository, branch)
        if ahead:
            raise WorkspaceError(f"Branch has {ahead} unpushed commit(s): {name} {branch}")
        plans.append(TaskPlan(repository, path, branch, action))

    if not plans:
        log("info", "No matching task worktrees or branches found.")
        return 0
    print("Cleanup plan:")
    for plan in plans:
        if plan.action == "remove":
            print(f"  - {plan.path}, branch {plan.branch}")
        else:
            print(f"  - branch {plan.branch} (its worktree is already gone)")
    if not args.yes:
        try:
            answer = input("Proceed? [y/N] ")
        except EOFError:
            answer = ""
        if answer not in ("y", "Y"):
            # Nonzero so a declined or unanswered prompt never reads as success.
            log("error", "Aborted. Nothing was removed.")
            return 1

    failed = 0
    for plan in plans:
        if plan.action == "remove":
            try:
                git(plan.repository, "worktree", "remove", str(plan.path))
            except WorkspaceError as error:
                log("error", f"Could not remove {plan.path}: {error}")
                failed = 1
                continue
            log("success", f"Removed {plan.path}")
        try:
            if not delete_branch(plan):
                failed = 1
        except WorkspaceError as error:
            log("warning", f"Could not delete {plan.branch}: {error}")
            failed = 1
    return failed
