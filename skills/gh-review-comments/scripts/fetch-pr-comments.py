#!/usr/bin/env python3
"""
Fetch GitHub pull request feedback for one or more PRs using the GitHub CLI.

Return unresolved inline threads, top-level comments, and review bodies by default.

Usage:
  fetch-pr-comments.py https://github.com/owner/repo/pull/123
  fetch-pr-comments.py owner/repo#123 456
  fetch-pr-comments.py --threads-only owner/repo#123
  fetch-pr-comments.py --all-threads owner/repo#123
  fetch-pr-comments.py

With no PR argument, the script fetches the PR associated with the current
branch according to `gh pr view`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse

THREADS_QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      id
      number
      url
      title
      state
      isDraft
      reviewDecision
      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          diffSide
          startLine
          startDiffSide
          originalLine
          originalStartLine
          resolvedBy { login }
          comments(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              url
              body
              createdAt
              updatedAt
              path
              line
              originalLine
              diffHunk
              author { login }
            }
          }
        }
      }
    }
  }
}
"""

CONTEXT_QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $commentsCursor: String,
  $reviewsCursor: String,
  $threadsCursor: String,
  $includeComments: Boolean!,
  $includeReviews: Boolean!,
  $includeThreads: Boolean!
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      id
      number
      url
      title
      state
      isDraft
      reviewDecision
      comments(first: 100, after: $commentsCursor) @include(if: $includeComments) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          url
          body
          createdAt
          updatedAt
          author { login }
        }
      }
      reviews(first: 100, after: $reviewsCursor) @include(if: $includeReviews) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          url
          state
          body
          submittedAt
          author { login }
        }
      }
      reviewThreads(first: 100, after: $threadsCursor) @include(if: $includeThreads) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          diffSide
          startLine
          startDiffSide
          originalLine
          originalStartLine
          resolvedBy { login }
          comments(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              url
              body
              createdAt
              updatedAt
              path
              line
              originalLine
              diffHunk
              author { login }
            }
          }
        }
      }
    }
  }
}
"""

SHORT_PR_RE = re.compile(r"^(?P<owner>[^/\s#]+)/(?P<repo>[^/\s#]+)#(?P<number>\d+)$")
NUMBER_RE = re.compile(r"^#?(?P<number>\d+)$")


def run(cmd: list[str], stdin: str | None = None) -> str:
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout


def run_json(cmd: list[str], stdin: str | None = None) -> dict[str, Any]:
    output = run(cmd, stdin=stdin)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON from command output: {exc}\n{output}") from exc


def parse_pr_url(url: str) -> tuple[str, str, int] | None:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 4 and parts[2] == "pull" and parts[3].isdigit():
        return parts[0], parts[1], int(parts[3])
    return None


def resolve_with_gh(spec: str | None) -> tuple[str, str, int]:
    cmd = ["gh", "pr", "view"]
    if spec:
        cmd.append(spec)
    cmd.extend(["--json", "url"])

    payload = run_json(cmd)
    url = payload.get("url")
    if not isinstance(url, str):
        raise RuntimeError(f"gh pr view did not return a PR URL for {spec or 'current branch'}")

    parsed = parse_pr_url(url)
    if not parsed:
        raise RuntimeError(f"Could not parse GitHub PR URL: {url}")
    return parsed


def resolve_pr(spec: str | None) -> tuple[str, str, int]:
    if spec is None:
        return resolve_with_gh(None)

    parsed_url = parse_pr_url(spec)
    if parsed_url:
        return parsed_url

    short_match = SHORT_PR_RE.match(spec)
    if short_match:
        return (
            short_match.group("owner"),
            short_match.group("repo"),
            int(short_match.group("number")),
        )

    number_match = NUMBER_RE.match(spec)
    if number_match:
        return resolve_with_gh(number_match.group("number"))

    return resolve_with_gh(spec)


def graphql(owner: str, repo: str, number: int, query: str, variables: dict[str, str | bool | None]) -> dict[str, Any]:
    cmd = [
        "gh",
        "api",
        "graphql",
        "-F",
        "query=@-",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"number={number}",
    ]

    for name, value in variables.items():
        if isinstance(value, bool):
            cmd.extend(["-F", f"{name}={str(value).lower()}"])
        elif value:
            cmd.extend(["-F", f"{name}={value}"])

    return run_json(cmd, stdin=query)


def extend_unique(target: list[dict[str, Any]], seen: set[str], nodes: list[dict[str, Any]]) -> None:
    for node in nodes:
        node_id = str(node.get("id") or "")
        if node_id and node_id in seen:
            continue
        if node_id:
            seen.add(node_id)
        target.append(node)


def page_info(page: dict[str, Any]) -> str | None:
    info = page["pageInfo"]
    return info["endCursor"] if info["hasNextPage"] else None


def fetch_pr(owner: str, repo: str, number: int, include_context: bool, include_resolved: bool) -> dict[str, Any]:
    comments: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    threads: list[dict[str, Any]] = []
    seen_comments: set[str] = set()
    seen_reviews: set[str] = set()
    seen_threads: set[str] = set()
    cursors: dict[str, str | None] = {"threadsCursor": None}
    if include_context:
        cursors.update({"commentsCursor": None, "reviewsCursor": None})
    pending = set(cursors)

    pr_meta: dict[str, Any] | None = None
    query = CONTEXT_QUERY if include_context else THREADS_QUERY

    while pending:
        variables: dict[str, str | bool | None] = dict(cursors)
        if include_context:
            variables.update({
                "includeComments": "commentsCursor" in pending,
                "includeReviews": "reviewsCursor" in pending,
                "includeThreads": "threadsCursor" in pending,
            })
        payload = graphql(owner, repo, number, query, variables)
        errors = payload.get("errors")
        if errors:
            raise RuntimeError(json.dumps(errors, indent=2))

        pr = payload["data"]["repository"]["pullRequest"]
        if pr_meta is None:
            pr_meta = {
                "id": pr["id"],
                "owner": owner,
                "repo": repo,
                "number": pr["number"],
                "url": pr["url"],
                "title": pr["title"],
                "state": pr["state"],
                "isDraft": pr["isDraft"],
                "reviewDecision": pr["reviewDecision"],
            }

        for cursor, field, target, seen in (
            ("threadsCursor", "reviewThreads", threads, seen_threads),
            ("commentsCursor", "comments", comments, seen_comments),
            ("reviewsCursor", "reviews", reviews, seen_reviews),
        ):
            if cursor not in pending:
                continue
            page = pr[field]
            extend_unique(target, seen, page.get("nodes") or [])
            cursors[cursor] = page_info(page)
            if cursors[cursor] is None:
                pending.remove(cursor)

    if pr_meta is None:
        raise RuntimeError(f"GitHub returned no PR data for {owner}/{repo}#{number}")

    unresolved_threads = [thread for thread in threads if not thread.get("isResolved")]
    selected_threads = threads if include_resolved else unresolved_threads

    return {
        "pull_request": pr_meta,
        "context_included": include_context,
        "counts": {
            "conversation_comments": len(comments) if include_context else None,
            "reviews": len(reviews) if include_context else None,
            "review_threads": len(threads),
            "unresolved_review_threads": len(unresolved_threads),
            "resolved_review_threads_omitted": len(threads) - len(selected_threads),
        },
        "conversation_comments": comments,
        "reviews": reviews,
        "review_threads": selected_threads,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch unresolved threads, top-level comments, and review bodies for GitHub PRs."
    )
    parser.add_argument(
        "prs",
        nargs="*",
        help="PR URL, PR number, #number, or owner/repo#number. Defaults to current branch PR.",
    )
    parser.add_argument(
        "--all-threads",
        action="store_true",
        help="Include resolved review threads. By default only unresolved threads are returned.",
    )
    context = parser.add_mutually_exclusive_group()
    context.add_argument(
        "--threads-only",
        dest="include_context",
        action="store_false",
        help="Fetch only inline review threads, omitting top-level comments and review bodies.",
    )
    context.add_argument(
        "--include-context",
        dest="include_context",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(include_context=True)
    parser.add_argument(
        "--unresolved-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.unresolved_only and args.all_threads:
        print("--unresolved-only cannot be combined with --all-threads", file=sys.stderr)
        return 2

    specs = args.prs or [None]
    pull_requests = []

    try:
        for spec in specs:
            owner, repo, number = resolve_pr(spec)
            pull_requests.append(
                fetch_pr(
                    owner,
                    repo,
                    number,
                    include_context=args.include_context,
                    include_resolved=args.all_threads,
                )
            )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps({"pull_requests": pull_requests}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
