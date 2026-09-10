#!/usr/bin/env python3
"""Shared Git inspection and errors for the workspace commands."""

from dataclasses import dataclass
from pathlib import Path
import re
import shlex
import subprocess
import sys


class WorkspaceError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def redact(text: str) -> str:
    text = re.sub(r"(https?://)[^\s/]*@", r"\1<redacted>@", text)
    return re.sub(r"([A-Za-z][A-Za-z0-9+.-]*://)[^\s/]*:[^\s/]*@", r"\1<redacted>@", text)


def log(level: str, message: str) -> None:
    print(f"{level} {redact(message)}", file=sys.stderr if level in {"error", "warning"} else sys.stdout)


def git(repo: Path | None, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["git"]
    if repo is not None:
        command.extend(["-C", str(repo)])
    command.extend(args)
    result = subprocess.run(command, capture_output=True, text=True, errors="surrogateescape")
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorkspaceError(redact(f"{shlex.join(command)} failed ({result.returncode}): {detail}"))
    return result


def root_path(value: str, create: bool = False) -> Path:
    if not value:
        raise WorkspaceError("Repositories root cannot be empty.", 2)
    root = Path(value).expanduser()
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise WorkspaceError(f"Repositories root does not exist: {root}")
    return root.resolve()


def validate_repo_name(name: str) -> str:
    if not name or name in {".", ".."} or "/" in name:
        raise WorkspaceError(f"Unsafe repository name: {name}", 2)
    return name


def under(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def is_container(path: Path) -> bool:
    if not (path / ".git").is_dir():
        return False
    return git(path, "rev-parse", "--is-bare-repository").stdout.strip() == "true"


def checked_container(root: Path, name: str) -> Path:
    repo = root / validate_repo_name(name)
    if not repo.is_dir() or not is_container(repo):
        raise WorkspaceError(f"Not a bare-container repository: {repo}")
    if not under(repo, root):
        raise WorkspaceError(f"Repository resolves outside the repositories root: {repo} -> {repo.resolve()}")
    return repo


def ref_exists(repo: Path, ref: str) -> bool:
    result = git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
    if result.returncode not in {0, 1}:
        raise WorkspaceError(f"Could not inspect {ref}: {result.stderr.strip()}")
    return result.returncode == 0


def default_branch(repo: Path, refresh: bool = False) -> str:
    if refresh:
        # Remote HEAD discovery can fail even when fetched branches are available.
        result = git(repo, "remote", "set-head", "origin", "--auto", check=False)
        if result.returncode:
            log("warning", f"{repo.name}: remote HEAD discovery failed; checking local remote refs")
    result = git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD", check=False)
    if result.returncode == 0:
        return result.stdout.strip().removeprefix("refs/remotes/origin/")
    if result.returncode != 1:
        raise WorkspaceError(f"Could not read origin/HEAD: {result.stderr.strip()}")
    for name in ("main", "master"):
        if ref_exists(repo, f"refs/remotes/origin/{name}"):
            return name
    raise WorkspaceError(f"Cannot detect default branch for {repo.name}.")


@dataclass(frozen=True)
class Worktree:
    path: Path
    branch: str | None
    bare: bool = False
    locked: bool = False


def worktrees(repo: Path) -> list[Worktree]:
    output = git(repo, "worktree", "list", "--porcelain", "-z").stdout
    result = []
    fields: dict[str, str] = {}
    for entry in output.split("\0"):
        if entry:
            key, _, value = entry.partition(" ")
            fields[key] = value
        elif fields:
            branch = fields.get("branch")
            result.append(Worktree(
                Path(fields["worktree"]),
                branch.removeprefix("refs/heads/") if branch else None,
                "bare" in fields,
                "locked" in fields,
            ))
            fields = {}
    return result


def current_branch(worktree: Path) -> str | None:
    result = git(worktree, "symbolic-ref", "--quiet", "HEAD", check=False)
    if result.returncode == 1:
        return None
    if result.returncode:
        raise WorkspaceError(f"Could not read branch at {worktree}: {result.stderr.strip()}")
    return result.stdout.strip().removeprefix("refs/heads/")


def is_dirty(worktree: Path) -> bool:
    return bool(git(worktree, "status", "--porcelain").stdout)


def update_default_worktree(repo: Path, branch: str) -> str:
    """Restore the clean named checkout before advancing the default branch."""
    path = repo / branch
    if not any(wt.path == path for wt in worktrees(repo)):
        raise WorkspaceError("Default worktree missing; run add-repo.sh to repair.")
    if not path.is_dir():
        raise WorkspaceError("Default worktree registered but path is gone; run add-repo.sh to repair.")
    if is_dirty(path):
        raise WorkspaceError(f"Default worktree has local changes: {path}")
    current = current_branch(path)
    if current is None:
        raise WorkspaceError(f"Default worktree has a detached HEAD: {path}")
    if current != branch:
        git(path, "switch", "--quiet", branch)
    git(repo, "branch", f"--set-upstream-to=origin/{branch}", branch)
    before = git(path, "rev-parse", "HEAD").stdout
    git(path, "merge", "--ff-only", f"origin/{branch}")
    after = git(path, "rev-parse", "HEAD").stdout
    state = "already up to date" if before == after else f"fast-forwarded to origin/{branch}"
    restored = f"restored {branch} from {current}; " if current != branch else ""
    return f"{restored}{branch} {state}"
