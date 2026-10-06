#!/usr/bin/env python3
"""Offline stand-in for the GitHub CLI, used by the pr-review evals.

It answers the `gh` calls pr-review makes from fixture files and never touches
the network. Each PR lives in ./fixtures/<number>/; repository file contents and
the team roster may sit in any PR's folder and are shared across them. Writes such as submitting a review are recorded in
./posted/ instead of being sent, so graders can check what would have been
posted. Every call is appended to ./gh-calls.log.
"""

import base64
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path.cwd()
FIXTURES = ROOT / "fixtures"
POSTED = ROOT / "posted"


def log(argv):
    with (ROOT / "gh-calls.log").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(argv) + "\n")


def fail(message, code=1):
    print(message, file=sys.stderr)
    sys.exit(code)


def pr_dirs():
    return sorted(p for p in FIXTURES.iterdir() if (p / "pr.json").is_file())


def pr_dir(number=None):
    """Return the fixture folder for a PR number, or the only one when unambiguous."""
    dirs = pr_dirs()
    if number is not None:
        for d in dirs:
            if d.name == str(number):
                return d
        fail(f"gh: Not Found (HTTP 404) [no fixture for PR {number}]")
    if len(dirs) == 1:
        return dirs[0]
    fail("gh: a PR number is required; several fixture PRs exist")


def pr_number(value):
    """Extract a PR number from `7`, `#7`, `owner/repo#7`, or a PR URL."""
    tail = str(value).rstrip("/").split("/")[-1].split("#")[-1]
    return int(tail) if tail.isdigit() else None


def load(name, number=None, optional=False):
    path = pr_dir(number) / name
    if not path.exists():
        if optional:
            return None
        fail(f"gh: Not Found (HTTP 404) [fixture {name} missing]")
    return path.read_text(encoding="utf-8")


def shared(relative):
    """Find a shared fixture path (contents or roster) in any PR folder."""
    for d in pr_dirs():
        if (d / relative).exists():
            return d / relative
    return None


def emit(text, jq_filter=None):
    """Print JSON text, applying a --jq filter with the real jq when given."""
    if jq_filter is None:
        print(text)
        return
    if shutil.which("jq") is None:
        fail("gh: --jq needs jq, which is not installed")
    result = subprocess.run(["jq", "-r", jq_filter], input=text, text=True, capture_output=True)
    if result.returncode != 0:
        fail(result.stderr.strip() or "jq failed")
    sys.stdout.write(result.stdout)


def take(args, flag):
    """Remove `flag value` from args and return the value, or None."""
    if flag in args:
        i = args.index(flag)
        value = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
        return value
    return None


def select_fields(data, fields):
    if not fields:
        return data
    return {key: data.get(key) for key in fields.split(",")}


def pr_command(args):
    sub = args.pop(0) if args else ""
    jq_filter = take(args, "--jq") or take(args, "-q")
    fields = take(args, "--json")
    take(args, "--repo")
    take(args, "-R")
    positional = [a for a in args if not a.startswith("-")]
    number = pr_number(positional[0]) if positional else None
    pr = json.loads(load("pr.json", number))
    if sub == "view":
        emit(json.dumps(select_fields(pr, fields)), jq_filter)
    elif sub == "diff":
        print(load("diff.patch", number), end="")
    elif sub in {"review", "comment", "merge", "close", "edit"}:
        record("pr-" + sub, args)
    else:
        fail(f"gh pr {sub}: not supported by the eval fixture")


def record(kind, args, body=None):
    POSTED.mkdir(exist_ok=True)
    path = POSTED / f"{int(time.time() * 1000)}-{kind}.json"
    path.write_text(json.dumps({"kind": kind, "args": args, "body": body}, indent=2), encoding="utf-8")
    print(json.dumps({"id": 1, "state": "RECORDED_NOT_SENT"}))


def api_command(args):
    jq_filter = take(args, "--jq") or take(args, "-q")
    method = (take(args, "-X") or take(args, "--method") or "GET").upper()
    input_file = take(args, "--input")
    accept = ""
    while "-H" in args:
        header = take(args, "-H") or ""
        if header.lower().startswith("accept:"):
            accept = header.split(":", 1)[1].strip()
    fields = []
    for flag in ("-f", "-F", "--field", "--raw-field"):
        while flag in args:
            fields.append(take(args, flag))
    for flag in ("--paginate", "--silent", "-i", "--include"):
        while flag in args:
            args.remove(flag)
    if not args:
        fail("gh api: missing endpoint")
    endpoint = args[0].lstrip("/").split("?")[0]

    if endpoint == "graphql":
        emit(json.dumps({"data": {"repository": {"pullRequest": {"reviewThreads": {
            "nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}}}}}), jq_filter)
        return

    parts = endpoint.split("/")
    if method != "GET":
        body = Path(input_file).read_text(encoding="utf-8") if input_file and Path(input_file).exists() else fields
        record(endpoint.replace("/", "_"), args, body)
        return

    # repos/<owner>/<repo>/pulls/<n>/<resource>
    if len(parts) == 6 and parts[0] == "repos" and parts[3] == "pulls":
        name = {"reviews": "reviews.json", "comments": "review-comments.json", "files": "files.json"}.get(parts[5])
        if name:
            emit(load(name, pr_number(parts[4]), optional=True) or "[]", jq_filter)
            return
    if len(parts) == 5 and parts[0] == "repos" and parts[3] == "pulls":
        emit(load("pr.json", pr_number(parts[4])), jq_filter)
        return
    # repos/<owner>/<repo>/issues/<n>/comments
    if len(parts) == 6 and parts[0] == "repos" and parts[3] == "issues" and parts[5] == "comments":
        emit(load("issue-comments.json", pr_number(parts[4]), optional=True) or "[]", jq_filter)
        return
    # orgs/<org>/teams/<team>/memberships/<user>
    if len(parts) == 6 and parts[0] == "orgs" and parts[2] == "teams" and parts[4] == "memberships":
        # Mirror GitHub for a token without admin:org: memberships are hidden.
        fail("gh: Not Found (HTTP 404)\nThis API operation needs the \"admin:org\" scope.")
    # orgs/<org>/teams/<team> and orgs/<org>/teams/<team>/members
    if parts[:1] == ["orgs"] and len(parts) in (4, 5) and parts[2] == "teams" and parts[4:] in ([], ["members"]):
        roster = shared("teams.json")
        teams = json.loads(roster.read_text(encoding="utf-8")) if roster else {}
        team = teams.get(parts[3])
        if team is None:
            fail("gh: Not Found (HTTP 404)")
        if len(parts) == 4:
            emit(json.dumps({"slug": parts[3], "members_count": len(team)}), jq_filter)
        else:
            emit(json.dumps([{"login": login} for login in team]), jq_filter)
        return
    # repos/<owner>/<repo>/compare/<base>...<head>: compare-<head>.json in any PR folder
    if len(parts) == 5 and parts[0] == "repos" and parts[3] == "compare":
        head = parts[4].split("...")[-1]
        path = next((d / name for d in pr_dirs() for name in (f"compare-{head}.json",) if (d / name).is_file()), None)
        if path is None:
            fail(f"gh: Not Found (HTTP 404) [no compare fixture for {head}]")
        emit(path.read_text(encoding="utf-8"), jq_filter)
        return
    if endpoint == "user":
        emit(json.dumps({"login": "eval-user"}), jq_filter)
        return
    # repos/<owner>/<repo>/tarball/<ref>. A PR's head SHA selects that PR's
    # folder; any other ref, such as a pinned python-standards commit, falls
    # back to every folder.
    if len(parts) == 5 and parts[0] == "repos" and parts[3] == "tarball":
        heads = [d for d in pr_dirs()
                 if json.loads((d / "pr.json").read_text(encoding="utf-8"))["headRefOid"].startswith(parts[4])]
        roots = [d / "contents" / parts[1] / parts[2] for d in heads or pr_dirs()]
        roots = [root for root in roots if root.is_dir()]
        if not roots:
            fail("gh: Not Found (HTTP 404)")
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            for root in roots:
                tar.add(root, arcname=f"{parts[1]}-{parts[2]}-{parts[4][:7]}")
        sys.stdout.buffer.write(buffer.getvalue())
        return
    # repos/<owner>/<repo>/contents/<path>
    if len(parts) >= 4 and parts[0] == "repos" and parts[3] == "contents":
        repo = f"{parts[1]}/{parts[2]}"
        rel = "/".join(parts[4:])
        target = shared(Path("contents") / repo / rel) or FIXTURES / "missing"
        if target.is_dir():
            listing = [{"name": p.name, "path": f"{rel}/{p.name}".lstrip("/"), "type": "dir" if p.is_dir() else "file"}
                       for p in sorted(target.iterdir())]
            emit(json.dumps(listing), jq_filter)
        elif target.is_file():
            raw = target.read_text(encoding="utf-8")
            if "raw" in accept:
                print(raw, end="")
            else:
                emit(json.dumps({"path": rel, "encoding": "base64",
                                 "content": base64.b64encode(raw.encode()).decode()}), jq_filter)
        else:
            fail("gh: Not Found (HTTP 404)")
        return
    fail(f"gh: Not Found (HTTP 404) [no fixture for {endpoint}]")


def main():
    argv = sys.argv[1:]
    log(argv)
    if not argv:
        fail("usage: gh <command>")
    command, args = argv[0], argv[1:]
    if command == "pr":
        pr_command(args)
    elif command == "api":
        api_command(args)
    elif command == "auth":
        print("github.com\n  ✓ Logged in to github.com account eval-user (fixture)")
    elif command == "repo" and args[:1] == ["view"]:
        emit(json.dumps({"nameWithOwner": json.loads(pr_dirs()[0].joinpath("pr.json").read_text())["repository"]["nameWithOwner"]}),
             take(args, "--jq"))
    else:
        fail(f"gh {command}: not supported by the eval fixture")


if __name__ == "__main__":
    os.umask(0o077)
    main()
