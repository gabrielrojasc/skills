#!/usr/bin/env python3
"""Offline CLI integration tests, including standalone skill distribution."""

import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest


class Workspace:
    def __init__(self, root):
        self.root = root.resolve()
        self.cwd = self.root / "unrelated working directory"
        self.cwd.mkdir()
        self.repos = self.root / "repository containers"
        self.skill = self.root / "installed skill"
        shutil.copytree(Path(__file__).resolve().parents[1], self.skill,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update({
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "GIT_ALLOW_PROTOCOL": "file",
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            "PYTHONDONTWRITEBYTECODE": "1", "TERM": "dumb", "LC_ALL": "C",
        })

    def run_command(self, *args, ok=True, input="", env=None):
        result = subprocess.run([str(arg) for arg in args], cwd=self.cwd,
                                env=env or self.env, input=input, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=30)
        if ok:
            assert result.returncode == 0, result.stdout
        else:
            assert result.returncode != 0, result.stdout
        return result.stdout

    def git(self, repo, *args, **kwargs):
        return self.run_command("git", "-C", repo, *args, **kwargs).strip()

    def cli(self, command, *args, **kwargs):
        return self.run_command("bash", self.skill / "scripts" / f"{command}.sh",
                                "--repos-root", self.repos, *args, **kwargs)

    def remote(self, name):
        remote = self.root / f"remote-{name}"
        self.run_command("git", "init", "--initial-branch=main", remote)
        self.commit(remote)
        return remote

    def commit(self, repo):
        self.git(repo, "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "Fixture")
        return self.git(repo, "rev-parse", "HEAD")

    def add(self, name):
        remote = self.remote(name)
        self.cli("add-repo", "--repo-name", name, remote)
        return self.repos / name, remote

    def create(self, name, task="sample", **kwargs):
        return self.cli("create-task-worktree", "--repo", name, "--task", task, **kwargs)

    def remove(self, name, task="sample", *args, **kwargs):
        return self.cli("remove-task-worktree", "--repo", name, "--task", task, *args, **kwargs)

    def assert_no_branch(self, repo, branch):
        assert self.git(repo, "for-each-ref", "--format=%(refname)",
                        f"refs/heads/{branch}") == ""


@pytest.fixture
def workspace(tmp_path):
    return Workspace(tmp_path)


def test_add_repairs_missing_worktree_and_rejects_origin_mismatch(workspace):
    repo, remote = workspace.add("sample")
    assert workspace.git(repo, "rev-parse", "--is-bare-repository") == "true"
    workspace.git(repo, "worktree", "remove", repo / "main")
    advanced = workspace.commit(remote)
    workspace.cli("add-repo", "--repo-name", "sample", remote)
    assert workspace.git(repo / "main", "rev-parse", "HEAD") == advanced
    other = workspace.remote("other")
    workspace.cli("add-repo", "--repo-name", "sample", other, ok=False)
    assert workspace.git(repo, "remote", "get-url", "origin") == str(remote)
    assert workspace.git(repo / "main", "rev-parse", "HEAD") == advanced


def test_manifest_continues_after_invalid_entry(workspace):
    first, second = workspace.remote("first"), workspace.remote("second")
    manifest = workspace.root / "repositories.txt"
    manifest.write_text(f"# local fixtures\n\n{first} first # comment\n"
                        f"{first} invalid extra\n{second} second", encoding="utf-8")
    output = workspace.cli("add-repo", "--from-manifest", manifest, ok=False)
    assert re.search(r"Repos processed:\s+3", output)
    assert re.search(r"Repos ready:\s+2", output)
    assert re.search(r"Repos failed:\s+1", output)
    for name in ("first", "second"):
        assert (workspace.repos / name / "main" / ".git").is_file()
    assert not (workspace.repos / "invalid").exists()


def test_add_rejects_ssh_password_without_logging_it(workspace):
    password = "synthetic-fixture-password"
    output = workspace.cli("add-repo", f"ssh://fixture:{password}@example.invalid/repo.git",
                           ok=False)
    assert password not in output
    assert not (workspace.repos / "repo").exists()


def test_create_reuses_dirty_task_and_list_reports_it(workspace):
    repo, _ = workspace.add("sample")
    args = ("--repo", "sample", "--repo", "sample", "--task", "Fix Parser",
            "--ticket", "ENG-42", "--branch-prefix", "bugfix")
    workspace.cli("create-task-worktree", *args)
    task = repo / "eng-42-fix-parser"
    assert workspace.git(task, "symbolic-ref", "--short", "HEAD") == "bugfix/eng-42-fix-parser"
    assert workspace.git(task, "for-each-ref", "--format=%(upstream)",
                         "refs/heads/bugfix/eng-42-fix-parser") == ""
    (task / "local.txt").write_text("preserve me\n", encoding="utf-8")
    output = workspace.cli("create-task-worktree", *args)
    assert re.search(r"Created:\s+0", output)
    assert re.search(r"Reused:\s+1", output)
    output = workspace.cli("list-workspace")
    assert re.search(r"eng-42-fix-parser.*bugfix/eng-42-fix-parser.*\[dirty\]", output)
    assert re.search(r"Task worktrees:\s+1", output)
    assert (task / "local.txt").read_text() == "preserve me\n"


def test_create_preflights_all_repositories(workspace):
    repo, _ = workspace.add("first")
    workspace.cli("create-task-worktree", "--repo", "first", "--repo", "missing",
                  "--task", "sample", ok=False)
    assert not (repo / "sample").exists()
    workspace.assert_no_branch(repo, "feature/sample")


def test_create_rolls_back_new_worktrees_after_git_failure(workspace):
    first, _ = workspace.add("first")
    second, _ = workspace.add("second")
    # Fail only the second worktree add, after preflight and the first mutation.
    shim_dir = workspace.root / "shim"
    shim_dir.mkdir()
    shim = shim_dir / "git"
    shim.write_text("#!/usr/bin/env python3\nimport os, sys\n"
                    f"real_git = {shutil.which('git')!r}\n"
                    f"target = {str(second)!r}\n"
                    "args = sys.argv[1:]\n"
                    "if target in args and 'worktree' in args and 'add' in args:\n"
                    "    print('injected worktree add failure', file=sys.stderr)\n"
                    "    sys.exit(1)\n"
                    "os.execv(real_git, [real_git, *args])\n", encoding="utf-8")
    shim.chmod(0o755)
    env = dict(workspace.env, PATH=str(shim_dir) + os.pathsep + workspace.env["PATH"])
    output = workspace.cli("create-task-worktree", "--repo", "first", "--repo", "second",
                           "--task", "sample", env=env, ok=False)
    assert "injected worktree add failure" in output
    for repo in (first, second):
        assert not (repo / "sample").exists()
        workspace.assert_no_branch(repo, "feature/sample")
        assert f"worktree {repo / 'sample'}\n" not in workspace.git(repo, "worktree", "list", "--porcelain")


def test_sync_updates_clean_repo_and_preserves_skips_on_partial_failure(workspace):
    fixtures = {name: workspace.add(name) for name in
                ("clean", "dirty", "detached", "divergent", "unreachable")}
    clean, _ = fixtures["clean"]
    workspace.create("clean")
    task_head = workspace.git(clean / "sample", "rev-parse", "HEAD")
    before = {}
    for name, (repo, remote) in fixtures.items():
        if name == "dirty":
            (repo / "main" / "local.txt").write_text("keep\n", encoding="utf-8")
        elif name == "detached":
            workspace.git(repo / "main", "switch", "--detach")
        elif name == "divergent":
            workspace.git(repo / "main", "-c", "commit.gpgsign=false", "commit",
                          "--allow-empty", "-m", "Local divergence")
        before[name] = workspace.git(repo / "main", "rev-parse", "HEAD")
        workspace.git(remote, "-c", "commit.gpgsign=false", "commit", "--allow-empty",
                      "-m", "Remote advance")
    broken, _ = fixtures["unreachable"]
    workspace.git(broken, "remote", "set-url", "origin", workspace.root / "missing-remote")
    output = workspace.cli("sync-workspace", "--jobs", "2", "--no-prune", ok=False)
    assert re.search(r"Repos synced:\s+1", output)
    assert re.search(r"Repos skipped:\s+3", output)
    assert re.search(r"Repos failed:\s+1", output)
    assert workspace.git(clean / "main", "rev-parse", "HEAD") == workspace.git(fixtures["clean"][1], "rev-parse", "HEAD")
    assert workspace.git(clean / "sample", "rev-parse", "HEAD") == task_head
    for name in ("dirty", "detached", "divergent", "unreachable"):
        assert workspace.git(fixtures[name][0] / "main", "rev-parse", "HEAD") == before[name]
    assert (fixtures["dirty"][0] / "main" / "local.txt").read_text() == "keep\n"
    assert workspace.git(fixtures["detached"][0] / "main", "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"
    workspace.cli("sync-workspace", "--jobs", "0", ok=False)


@pytest.mark.parametrize("command", ["list-workspace", "sync-workspace"])
@pytest.mark.parametrize("healthy", [True, False], ids=["mixed", "only-broken"])
def test_discovery_reports_broken_repository_and_continues(workspace, command, healthy):
    if healthy:
        repo, remote = workspace.add("healthy")
        advanced = workspace.commit(remote)
    broken = workspace.repos / "aaa-broken" / ".git"
    broken.mkdir(parents=True)

    output = workspace.cli(command, ok=False)

    assert "aaa-broken" in output
    assert "not a git repository" in output
    assert "Summary" in output
    if command == "sync-workspace":
        assert re.search(rf"Repos synced:\s+{int(healthy)}", output)
        assert re.search(r"Repos failed:\s+1", output)
        if healthy:
            assert workspace.git(repo / "main", "rev-parse", "HEAD") == advanced
    else:
        assert re.search(rf"Repo containers:\s+{int(healthy)}", output)
        if healthy:
            assert "healthy (default: main)" in output
    assert broken.is_dir()
    assert list(broken.iterdir()) == []


def test_list_reports_corrupt_task_index_and_continues(workspace):
    repo, _ = workspace.add("aaa-broken")
    workspace.create("aaa-broken", "aaa-corrupt")
    workspace.create("aaa-broken", "zzz-healthy")
    workspace.add("healthy")
    task = repo / "aaa-corrupt"
    index = Path(workspace.git(task, "rev-parse", "--absolute-git-dir")) / "index"
    index.write_bytes(b"corrupt index\n")
    local_file = repo / "zzz-healthy" / "local.txt"
    local_file.write_text("preserve me\n", encoding="utf-8")

    output = workspace.cli("list-workspace", ok=False)

    assert "index file" in output
    assert "aaa-corrupt -> feature/aaa-corrupt [status unknown]" in output
    assert "zzz-healthy -> feature/zzz-healthy [dirty]" in output
    assert "healthy (default: main)" in output
    assert "Summary" in output
    assert re.search(r"Repo containers:\s+2", output)
    assert re.search(r"Task worktrees:\s+2", output)
    assert index.read_bytes() == b"corrupt index\n"
    assert local_file.read_text() == "preserve me\n"


def test_list_continues_when_git_cannot_enumerate_worktrees(workspace):
    broken, _ = workspace.add("aaa-broken")
    workspace.add("healthy")
    workspace.create("healthy")
    shim_dir = workspace.root / "shim"
    shim_dir.mkdir()
    shim = shim_dir / "git"
    shim.write_text("#!/usr/bin/env python3\nimport os, sys\n"
                    f"real_git = {shutil.which('git')!r}\n"
                    f"target = {str(broken)!r}\n"
                    "args = sys.argv[1:]\n"
                    "if args[:4] == ['-C', target, 'worktree', 'list']:\n"
                    "    print('injected worktree enumeration failure', file=sys.stderr)\n"
                    "    sys.exit(1)\n"
                    "os.execv(real_git, [real_git, *args])\n", encoding="utf-8")
    shim.chmod(0o755)
    env = dict(workspace.env, PATH=str(shim_dir) + os.pathsep + workspace.env["PATH"])

    output = workspace.cli("list-workspace", env=env, ok=False)

    assert "injected worktree enumeration failure" in output
    assert "(worktrees unknown)" in output
    assert "healthy (default: main)" in output
    assert "sample -> feature/sample" in output
    assert "Summary" in output
    assert re.search(r"Repo containers:\s+2", output)
    assert re.search(r"Task worktrees:\s+1", output)


@pytest.mark.parametrize("answer", ["n\n", ""], ids=["declined", "no-input"])
def test_remove_without_confirmation_fails_and_keeps_task(workspace, answer):
    # An agent shell has no stdin, so an unanswered prompt must not look like
    # a successful cleanup.
    repo, _ = workspace.add("sample")
    workspace.create("sample")
    output = workspace.remove("sample", input=answer, ok=False)
    assert "Aborted" in output
    assert (repo / "sample").is_dir()


def test_remove_yes_removes_only_matching_task(workspace):
    repo, _ = workspace.add("sample")
    workspace.create("sample")
    workspace.remove("sample", "sample", "--yes")
    assert not (repo / "sample").exists()
    workspace.assert_no_branch(repo, "feature/sample")
    assert (repo / "main").is_dir()


@pytest.mark.parametrize("merged", [True, False], ids=["merged", "unmerged"])
def test_remove_after_tracked_remote_branch_is_deleted(workspace, merged):
    repo, remote = workspace.add("sample")
    workspace.create("sample")
    task = repo / "sample"
    task_head = workspace.commit(task)
    workspace.git(task, "push", "-u", "origin", "HEAD")
    if merged:
        workspace.git(remote, "merge", "--ff-only", "feature/sample")
    workspace.git(task, "push", "origin", "--delete", "feature/sample")
    workspace.cli("sync-workspace")
    assert workspace.git(repo, "for-each-ref", "--format=%(refname)",
                         "refs/remotes/origin/feature/sample") == ""

    output = workspace.remove("sample", "sample", "--yes", ok=merged)

    if merged:
        assert not task.exists()
        workspace.assert_no_branch(repo, "feature/sample")
        assert workspace.git(repo / "main", "rev-parse", "HEAD") == task_head
    else:
        assert "unpushed commit" in output
        assert workspace.git(task, "rev-parse", "HEAD") == task_head
        assert workspace.git(task, "symbolic-ref", "--short", "HEAD") == "feature/sample"
    assert (repo / "main").is_dir()


def test_sync_rejects_zero_jobs_even_when_workspace_is_empty(workspace):
    workspace.repos.mkdir()
    workspace.cli("sync-workspace", "--jobs", "0", ok=False)
    assert list(workspace.repos.iterdir()) == []


@pytest.mark.parametrize("task", ["dirty", "unpushed", "mismatch"])
def test_remove_yes_still_checks_dirty_unpushed_and_mismatched_tasks(workspace, task):
    repo, _ = workspace.add("sample")
    for name in ("dirty", "unpushed", "mismatch"):
        workspace.create("sample", name)
    (repo / "dirty" / "local.txt").write_text("keep\n", encoding="utf-8")
    unpushed = workspace.commit(repo / "unpushed")
    workspace.git(repo / "mismatch", "switch", "-c", "feature/different")
    workspace.remove("sample", task, "--yes", ok=False)
    assert (repo / task).is_dir()
    assert (repo / "dirty" / "local.txt").read_text() == "keep\n"
    assert workspace.git(repo / "unpushed", "rev-parse", "HEAD") == unpushed
    assert workspace.git(repo / "mismatch", "symbolic-ref", "--short", "HEAD") == "feature/different"
