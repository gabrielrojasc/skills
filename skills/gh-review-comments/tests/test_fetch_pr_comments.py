#!/usr/bin/env python3

import importlib.util
import itertools
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch-pr-comments.py"
SPEC = importlib.util.spec_from_file_location("fetch_pr_comments", SCRIPT)
fetch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch)


def fetch_pages(monkeypatch, lengths, *, include_context=True, include_resolved=False):
    calls = []
    positions = dict.fromkeys(lengths, 0)
    connections = (
        ("comments", "commentsCursor", "includeComments"),
        ("reviews", "reviewsCursor", "includeReviews"),
        ("reviewThreads", "threadsCursor", "includeThreads"),
    )

    def graphql(owner, repo, number, query, variables):
        calls.append(dict(variables))
        assert len(calls) <= max(lengths.values())
        pr = {
            "id": "pr1", "number": number,
            "url": f"https://github.com/{owner}/{repo}/pull/{number}",
            "title": "Example", "state": "OPEN", "isDraft": False,
            "reviewDecision": "CHANGES_REQUESTED",
        }
        for field, cursor, flag in connections:
            enabled = variables[flag] if include_context else field == "reviewThreads"
            if include_context:
                assert f"@include(if: ${flag})" in query
            if not enabled:
                continue
            position = positions[field]
            assert position < lengths[field], f"Refetched completed {field}"
            assert variables.get(cursor) == (str(position) if position else None)
            positions[field] += 1
            node = {"id": f"{field}-{position}"}
            if field == "reviewThreads":
                node["isResolved"] = position % 2 == 1
            pr[field] = {
                "nodes": [node],
                "pageInfo": {
                    "hasNextPage": position + 1 < lengths[field],
                    "endCursor": str(position + 1),
                },
            }
        return {"data": {"repository": {"pullRequest": pr}}}

    monkeypatch.setattr(fetch, "graphql", graphql)
    result = fetch.fetch_pr("owner", "repo", 123, include_context, include_resolved)
    assert positions == lengths
    assert len(calls) == max(lengths.values())
    return result, calls


@pytest.mark.parametrize("lengths", tuple(itertools.permutations((2, 3, 4))))
def test_unequal_connections_finish_without_restarting(monkeypatch, lengths):
    comments, reviews, threads = lengths
    result, _ = fetch_pages(monkeypatch, dict(zip(
        ("comments", "reviews", "reviewThreads"), lengths
    )), include_resolved=True)
    for output, field, count in (
        ("conversation_comments", "comments", comments),
        ("reviews", "reviews", reviews),
        ("review_threads", "reviewThreads", threads),
    ):
        assert [node["id"] for node in result[output]] == [
            f"{field}-{i}" for i in range(count)
        ]
        assert result["counts"][output] == count


def test_threads_only_paginates_without_context_variables(monkeypatch):
    result, calls = fetch_pages(monkeypatch, {"reviewThreads": 3}, include_context=False)
    assert calls == [
        {"threadsCursor": None}, {"threadsCursor": "1"}, {"threadsCursor": "2"},
    ]
    assert not result["context_included"]
    assert result["conversation_comments"] == []
    assert result["reviews"] == []
    assert result["counts"]["conversation_comments"] is None
    assert result["counts"]["reviews"] is None


@pytest.mark.parametrize("include_resolved", (False, True))
def test_resolved_filter_preserves_counts_after_pagination(monkeypatch, include_resolved):
    result, _ = fetch_pages(
        monkeypatch, {"comments": 1, "reviews": 1, "reviewThreads": 4},
        include_resolved=include_resolved,
    )
    assert result["counts"] == {
        "conversation_comments": 1, "reviews": 1, "review_threads": 4,
        "unresolved_review_threads": 2,
        "resolved_review_threads_omitted": 0 if include_resolved else 2,
    }
    assert [thread["id"] for thread in result["review_threads"]] == [
        f"reviewThreads-{i}" for i in (range(4) if include_resolved else (0, 2))
    ]


def test_graphql_sends_typed_booleans_including_false(monkeypatch):
    calls = []

    def run_json(command, *, stdin):
        calls.append((command, stdin))
        return {}

    monkeypatch.setattr(fetch, "run_json", run_json)
    fetch.graphql("owner", "repo", 123, fetch.CONTEXT_QUERY, {
        "commentsCursor": None, "reviewsCursor": "next-page",
        "includeComments": False, "includeReviews": True, "includeThreads": False,
    })
    command, stdin = calls[-1]
    fields = [command[i + 1] for i, value in enumerate(command) if value == "-F"]
    assert "includeComments=false" in fields
    assert "includeReviews=true" in fields
    assert "includeThreads=false" in fields
    assert "reviewsCursor=next-page" in fields
    assert not any(field.startswith("commentsCursor=") for field in fields)
    assert stdin == fetch.CONTEXT_QUERY
