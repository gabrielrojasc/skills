#!/usr/bin/env python3
"""Workspace commands, callable through the existing shell entry points."""

import sys

if sys.version_info < (3, 10):
    sys.exit("error: Git workspace requires Python 3.10 or newer.")
sys.dont_write_bytecode = True

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import os
from pathlib import Path
import re
import tempfile

from workspace_core import (
    WorkspaceError, default_branch, git, is_container, is_dirty, log, redact,
    ref_exists, root_path, under, update_default_worktree, validate_repo_name,
    worktrees,
)
from workspace_tasks import create_tasks, remove_tasks


def ensure_default_worktree(repo: Path, branch: str) -> None:
    path = repo / branch
    registered = next((wt for wt in worktrees(repo) if wt.path == path), None)
    if registered and path.is_dir():
        log("info", update_default_worktree(repo, branch))
        return
    if registered:
        # Remove only this missing registration; Git still protects locked worktrees.
        git(repo, "worktree", "remove", str(path))
    if path.exists():
        raise WorkspaceError(f"Default worktree path exists but is not registered: {path}")
    local_ref = f"refs/heads/{branch}"
    remote_ref = f"refs/remotes/origin/{branch}"
    if not ref_exists(repo, local_ref):
        git(repo, "branch", "--no-track", branch, remote_ref)
    else:
        if git(repo, "merge-base", "--is-ancestor", local_ref, remote_ref, check=False).returncode:
            raise WorkspaceError(f"Local default branch cannot fast-forward to origin/{branch}.")
        # Only a fast-forward is allowed, and Git refuses a branch checked out elsewhere.
        git(repo, "branch", "-f", branch, remote_ref)
    git(repo, "branch", f"--set-upstream-to=origin/{branch}", branch)
    git(repo, "worktree", "add", str(path), branch)


def configure_repo(repo: Path) -> str:
    if not is_container(repo):
        raise WorkspaceError(f"Expected a bare repo at {repo}/.git.")
    git(repo, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
    git(repo, "fetch", "origin", "--quiet")
    return default_branch(repo, refresh=True)


def add_repo(root_value: str, url: str, name: str | None) -> None:
    if re.match(r"https?://[^/]*@|[^:/]+://[^/]*:[^/]*@", url):
        raise WorkspaceError("Repo URL contains embedded credentials; use a credential helper.", 2)
    if not name:
        name = url.rsplit("/", 1)[-1].split("?", 1)[0].removesuffix(".git")
        if not name or name == url:
            name = url.rsplit(":", 1)[-1].rsplit("/", 1)[-1].removesuffix(".git")
    validate_repo_name(name)
    root = root_path(root_value, create=True)
    repo = root / name
    if repo.exists():
        if not under(repo, root):
            raise WorkspaceError(f"Destination resolves outside repos root: {repo}")
        if not is_container(repo):
            raise WorkspaceError(f"Destination exists but is not a bare-container repo: {repo}")
        remotes = git(repo, "remote").stdout.splitlines()
        if "origin" not in remotes:
            git(repo, "remote", "add", "origin", url)
        else:
            origin = git(repo, "remote", "get-url", "origin").stdout.strip()
            if origin != url:
                raise WorkspaceError(f"Destination origin differs from requested URL: {redact(origin)}")
        log("info", f"Repairing existing bare-container repo: {repo}")
        branch = configure_repo(repo)
    else:
        git(None, "ls-remote", url, "HEAD")
        with tempfile.TemporaryDirectory(prefix=f".{name}.git-workspace-", dir=root) as temporary:
            staging = Path(temporary) / "container"
            staging.mkdir()
            git(None, "clone", "--bare", url, str(staging / ".git"))
            git(staging, "remote", "set-url", "origin", url)
            branch = configure_repo(staging)
            staging.rename(repo)
    ensure_default_worktree(repo, branch)
    log("success", f"Repo ready: {repo}")


def add_command(args: argparse.Namespace) -> int:
    if args.from_manifest:
        if args.url or args.repo_name:
            raise WorkspaceError("Use --from-manifest without a repo URL or --repo-name.", 2)
        manifest = Path(args.from_manifest)
        if not manifest.is_file():
            raise WorkspaceError(f"Manifest file not found: {manifest}", 2)
        total = ready = 0
        for line in manifest.read_text().splitlines():
            line = re.split(r"\s+#", line.strip(), maxsplit=1)[0].strip()
            if not line or line.startswith("#"):
                continue
            total += 1
            fields = line.split()
            print(f"\n[{total}] {redact(fields[0])}")
            try:
                if len(fields) > 2:
                    raise WorkspaceError(f"Manifest entry [{total}] has too many fields; expected '<repo-url> [repo-name]'.")
                add_repo(args.repos_root, fields[0], fields[1] if len(fields) == 2 else None)
                ready += 1
            except (WorkspaceError, OSError) as error:
                log("error", str(error))
        print(f"\nManifest summary\nRepos processed: {total}\nRepos ready:     {ready}")
        if total != ready:
            print(f"Repos failed:    {total - ready}")
        return int(total != ready)
    if not args.url:
        raise WorkspaceError("Repo URL is required.", 2)
    add_repo(args.repos_root, args.url, args.repo_name)
    return 0


def workspace_entries(root: Path) -> list[Path]:
    return sorted(path for path in root.iterdir() if not path.name.startswith(".") and path.is_dir())


def list_command(args: argparse.Namespace) -> int:
    root = root_path(args.repos_root)
    containers = tasks = 0
    failed = False
    other = []
    print(f"Workspace {root}\n")
    for repo in workspace_entries(root):
        try:
            managed = is_container(repo)
        except (WorkspaceError, OSError) as error:
            log("error", f"{repo.name}: {error}")
            failed = True
            continue
        if not managed:
            other.append(repo.name)
            continue
        containers += 1
        try:
            branch = default_branch(repo)
        except WorkspaceError as error:
            log("warning", str(error))
            branch = "unknown"
        print(f"{repo.name} (default: {branch})")
        try:
            registered = worktrees(repo)
        except (WorkspaceError, OSError) as error:
            log("error", f"{repo.name}: {error}")
            failed = True
            print("  (worktrees unknown)")
            continue
        found = 0
        for wt in registered:
            if wt.bare or wt.path == repo / branch:
                continue
            try:
                status = " [dirty]" if wt.path.is_dir() and is_dirty(wt.path) else ""
            except (WorkspaceError, OSError) as error:
                log("error", f"{wt.path}: {error}")
                failed = True
                status = " [status unknown]"
            print(f"  {wt.path.name} -> {wt.branch or '(detached)'}{status}")
            found += 1
        tasks += found
        if not found:
            print("  (no task worktrees)")
    if other:
        print("\nNot bare-container repos")
        for name in other:
            print(f"  {name}")
    print(f"\nSummary\nRepo containers:      {containers}\nTask worktrees:       {tasks}")
    return int(failed)


@dataclass(frozen=True)
class SyncResult:
    outcome: str
    message: str


def sync_repo(repo: Path, prune: bool) -> SyncResult:
    try:
        git(repo, "fetch", "--prune", "--quiet", "origin")
        branch = default_branch(repo, refresh=True)
    except (WorkspaceError, OSError) as error:
        return SyncResult("failed", f"{repo.name}: {error}")
    try:
        message = update_default_worktree(repo, branch)
        result = SyncResult("synced", f"{repo.name}: {message}")
    except (WorkspaceError, OSError) as error:
        result = SyncResult("skipped", f"{repo.name}: {error}")
    if prune:
        try:
            git(repo, "worktree", "prune", "--expire=1.week.ago")
        except (WorkspaceError, OSError) as error:
            return SyncResult("failed", f"{result.message}; pruning failed: {error}")
    return result


def sync_command(args: argparse.Namespace) -> int:
    jobs = args.jobs if args.jobs is not None else min(os.cpu_count() or 4, 8)
    if jobs < 1:
        raise WorkspaceError("--jobs must be a positive integer.")
    root = root_path(args.repos_root)
    repos = []
    counts = dict.fromkeys(("synced", "skipped", "failed"), 0)
    for repo in workspace_entries(root):
        try:
            if is_container(repo):
                repos.append(repo)
        except (WorkspaceError, OSError) as error:
            log("warning", f"{repo.name}: {error}")
            counts["failed"] += 1
    if not repos and not counts["failed"]:
        log("info", f"No bare-container repos found under {root}")
        return 0
    log("info", f"Syncing {len(repos)} repo(s) with up to {jobs} parallel jobs")
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        for result in executor.map(lambda repo: sync_repo(repo, not args.no_prune), repos):
            counts[result.outcome] += 1
            log("info" if result.outcome == "synced" else "warning", result.message)
    print(f"\nSummary\nRepos root:      {root}\nRepos synced:    {counts['synced']}")
    for outcome in ("skipped", "failed"):
        if counts[outcome]:
            print(f"Repos {outcome}:  {counts[outcome]}")
    return int(counts["failed"] > 0)


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = cli.add_subparsers(dest="command", required=True)
    for name, action, description in (
        ("add-repo", add_command, "Clone or repair a bare-container repository."),
        ("list-workspace", list_command, "List repositories and task worktrees."),
        ("sync-workspace", sync_command, "Fetch repositories and fast-forward default worktrees."),
        ("create-task-worktree", create_tasks, "Create or reuse exact task worktrees."),
        ("remove-task-worktree", remove_tasks, "Remove exact task worktrees after safety checks and confirmation."),
    ):
        command = commands.add_parser(name, description=description, allow_abbrev=False)
        command.add_argument("--repos-root", default="~/git")
        command.set_defaults(action=action)
        if name == "add-repo":
            command.add_argument("url", nargs="?")
            command.add_argument("--repo-name")
            command.add_argument("--from-manifest")
        elif name == "sync-workspace":
            command.add_argument("--jobs", type=int)
            command.add_argument("--no-prune", action="store_true")
        elif name in {"create-task-worktree", "remove-task-worktree"}:
            command.add_argument("--repo", action="append", required=True)
            command.add_argument("--task", required=True)
            command.add_argument("--ticket", default="")
            command.add_argument("--branch-prefix", default="feature")
            if name == "remove-task-worktree":
                command.add_argument("--yes", action="store_true", help="Skip the confirmation prompt after external approval.")
    return cli


def main() -> int:
    try:
        args = parser().parse_args()
        return args.action(args)
    except WorkspaceError as error:
        log("error", str(error))
        return error.exit_code
    except OSError as error:
        log("error", str(error))
        return 1
    except KeyboardInterrupt:
        log("error", "Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
