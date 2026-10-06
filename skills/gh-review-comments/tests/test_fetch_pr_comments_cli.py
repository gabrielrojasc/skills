#!/usr/bin/env python3
"""Offline regression checks for feedback selection and pagination."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "fetch_comments", Path(__file__).parents[1] / "scripts" / "fetch-pr-comments.py"
)
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class FeedbackTests(unittest.TestCase):
    def run_cli(self, *flags):
        calls = []

        def graphql(owner, repo, number, query, cursors):
            calls.append(query)
            if len(calls) > 4:
                self.fail("Pagination restarted an exhausted connection")
            pr = dict(id="pr", number=number, url="https://example.test/pr/1",
                      title="Example", state="OPEN", isDraft=False, reviewDecision=None)
            # Unequal page counts expose repeated pagination of finished sources.
            for field, cursor, count in [
                ("reviewThreads", "threadsCursor", 2),
                ("comments", "commentsCursor", 3),
                ("reviews", "reviewsCursor", 4),
            ]:
                page = int(cursors.get(cursor) or 0)
                node = dict(id=f"{field}-{page}", body=f"Concern {page}")
                if field == "reviewThreads":
                    node["isResolved"] = page == 1
                    # Model GitHub's field selection for a truncated thread.
                    node["comments"] = {"nodes": [{"id": "first-comment"}]}
                    if re.search(r"comments\(first: 100\)\s*\{\s*pageInfo\s*\{\s*hasNextPage\s+endCursor\s*\}", query):
                        node["comments"]["pageInfo"] = {
                            "hasNextPage": True, "endCursor": "comment-100"
                        }
                pr[field] = dict(
                    nodes=[node],
                    pageInfo=dict(hasNextPage=page + 1 < count,
                                  endCursor=str(page + 1)),
                )
            return {"data": {"repository": {"pullRequest": pr}}}

        output = io.StringIO()
        with patch.object(sys, "argv", ["fetch-pr-comments.py", "owner/repo#1", *flags]), \
                patch.object(fetch, "graphql", side_effect=graphql), \
                contextlib.redirect_stdout(output):
            self.assertEqual(fetch.main(), 0)
        return json.loads(output.getvalue())["pull_requests"][0], calls

    def test_default_includes_all_feedback_without_resolved_threads(self):
        result, calls = self.run_cli()
        self.assertTrue(result["context_included"])
        self.assertEqual(len(result["conversation_comments"]), 3)
        self.assertEqual(len(result["reviews"]), 4)
        self.assertEqual(len(result["review_threads"]), 1)
        self.assertEqual(result["counts"]["resolved_review_threads_omitted"], 1)
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(query == fetch.CONTEXT_QUERY for query in calls))

    def test_threads_only_omits_context(self):
        result, calls = self.run_cli("--threads-only")
        self.assertFalse(result["context_included"])
        self.assertEqual(result["conversation_comments"], [])
        self.assertEqual(result["reviews"], [])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(query == fetch.THREADS_QUERY for query in calls))

    def test_all_threads_preserves_default_context(self):
        result, _ = self.run_cli("--all-threads")
        self.assertEqual(len(result["review_threads"]), 2)
        self.assertTrue(result["context_included"])

    def test_legacy_include_context_remains_accepted(self):
        result, _ = self.run_cli("--include-context")
        self.assertTrue(result["context_included"])

    def test_incomplete_thread_history_is_visible_in_both_modes(self):
        for flags in [(), ("--threads-only",)]:
            with self.subTest(flags=flags):
                result, _ = self.run_cli(*flags)
                page = result["review_threads"][0]["comments"]["pageInfo"]
                self.assertTrue(page["hasNextPage"])
                self.assertEqual(page["endCursor"], "comment-100")


if __name__ == "__main__":
    unittest.main()
