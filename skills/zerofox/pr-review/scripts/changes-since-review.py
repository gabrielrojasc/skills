#!/usr/bin/env python3
"""Compare a PR's own changes now with its changes at an earlier reviewed commit.

  changes-since-review.py <owner>/<repo> <number> [<reviewed-sha>]

Without <reviewed-sha>, the reviewed commit is the one the authenticated user's
latest submitted review of the PR was made on. A dismissed review is reported
with the event it had before dismissal.

Each side is the PR's diff against its merge base with the base branch, so a
rebase onto a newer base doesn't count as a change. Only added and removed
lines are compared, not context or line numbers.

The first line of output is one of:
  none       the user has no submitted review of this PR
  same       the PR's changes match the reviewed commit's
  changed    they differ; the files and line differences follow
  unknown    the comparison isn't possible; the reason follows

After `same` or `changed`, a second line says `rebased onto <sha>` when the
PR's merge base moved since the reviewed commit.
"""

import difflib
import json
import subprocess
import sys

# The compare API lists at most 300 files, so a longer list may be truncated.
MAX_FILES = 300


def gh(*args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh {' '.join(args)} failed")
    return result.stdout


def latest_review(repo, number):
    login = gh("api", "user", "--jq", ".login").strip()
    reviews = []
    for line in gh("api", f"repos/{repo}/pulls/{number}/reviews", "--paginate", "--jq", ".[] | @json").splitlines():
        if line.strip():
            reviews.append(json.loads(line))
    mine = [r for r in reviews
            if (r.get("user") or {}).get("login") == login and r.get("commit_id") and r.get("state") != "PENDING"]
    return max(mine, key=lambda r: r.get("submitted_at") or "") if mine else None


def review_state(repo, number, review):
    """Return the review's state, giving a dismissed review's event before dismissal."""
    if review["state"] != "DISMISSED":
        return review["state"]
    events = gh("api", f"repos/{repo}/issues/{number}/timeline", "--paginate", "--jq",
                '.[] | select(.event == "review_dismissed") | .dismissed_review | @json')
    for line in events.splitlines():
        dismissed = json.loads(line) if line.strip() else {}
        if dismissed.get("review_id") == review.get("id") and dismissed.get("state"):
            return f"dismissed {dismissed['state'].upper()}"
    return "dismissed (event unknown)"


def pr_changes(repo, base, sha):
    """Return ({file key: [added and removed lines]}, merge base sha) for base...sha, or raise ValueError."""
    data = json.loads(gh("api", f"repos/{repo}/compare/{base}...{sha}"))
    merge_base = (data.get("merge_base_commit") or {}).get("sha")
    files = data.get("files") or []
    if len(files) >= MAX_FILES:
        raise ValueError(f"{sha[:7]} changes {len(files)} files, more than the compare API lists")
    changes = {}
    for f in files:
        key = f["filename"]
        if f.get("previous_filename"):
            key = f"{f['previous_filename']} -> {key}"
        patch = f.get("patch")
        if patch is None and f.get("changes", 0) > 0:
            raise ValueError(f"{key} has no patch at {sha[:7]} (binary or too large)")
        changes[key] = [l for l in (patch or "").splitlines() if l[:1] in "+-"]
    return changes, merge_base


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__.strip())
    repo, number = sys.argv[1], sys.argv[2]
    try:
        pr = json.loads(gh("pr", "view", number, "-R", repo, "--json", "baseRefName,headRefOid"))
        base, head = pr["baseRefName"], pr["headRefOid"]
        if len(sys.argv) == 4:
            reviewed, label = sys.argv[3], "reviewed"
        else:
            review = latest_review(repo, number)
            if review is None:
                print("none")
                return
            reviewed = review["commit_id"]
            label = f"your {review_state(repo, number, review)} review from {review.get('submitted_at', '?')} was on"
        print_header = lambda status: print(f"{status}: {label} {reviewed[:7]}; head is {head[:7]}")
        if reviewed == head:
            print_header("same")
            return
        (before, old_base), (after, new_base) = pr_changes(repo, base, reviewed), pr_changes(repo, base, head)
    except (RuntimeError, ValueError) as exc:
        print(f"unknown: {exc}")
        return

    differing = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    print_header("changed" if differing else "same")
    if old_base and new_base and old_base != new_base:
        print(f"rebased onto {new_base[:7]}")
    if not differing:
        return
    print("Each line below is a line of the PR's diff. Its first character says whether the")
    print("current head gained (+) or lost (-) that line since the reviewed commit.")
    for key in differing:
        state = "new file in the PR" if key not in before else "dropped from the PR" if key not in after else "changed"
        print(f"\n### {key} ({state})")
        for line in difflib.unified_diff(before.get(key, []), after.get(key, []), lineterm="", n=1):
            if line.startswith("@@"):
                print("...")
            elif not line.startswith(("---", "+++")):
                print(line)


if __name__ == "__main__":
    main()
