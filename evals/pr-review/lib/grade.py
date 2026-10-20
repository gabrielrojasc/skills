#!/usr/bin/env python3
"""Grade one headless pr-review run against its fixture's rubric.

  grade.py <claude|codex> <workspace> <fixture>

Checks that apply to every run:
  fake-gh        the run used the fake gh (gh-calls.log has entries) and never
                 reached the real one (no "Bad credentials" in trace or stderr)
  posts          every write to posted/ (the fake gh records writes there) is a
                 review whose event the fixture's may_post allows, or a reaction
                 alongside one
  posted-text    no posted review body or comment only reports review status (model-graded)
  no-question    no question or multiple-choice tool was called
  links          every Files-changed link has a 64-char hash directly followed by R<line>
  one-question   unless an allowed review posted, the final message ends with one
                 batch question (model-graded)
  rungs          review roles ran on the required tier (score-rungs.py)
  reviewers-ran  at least one reviewer subagent ran, unless reviewers is "absent"

Fixture checks come from fixtures/<fixture>/grade.json:
  must       rubric sentences the review has to satisfy (model-graded, each separately)
  must_not   rubric sentences the review must not do (model-graded)
  spec       "absent" or "present": whether a Spec reviewer should run
  reviewers  "absent": no reviewer, Spec, or verifier subagent should run
  may_post   review events the skill may submit without asking, such as ["APPROVE"]
  asks       false: the run has nothing to ask, so one-question is skipped
Must and must-not rubrics see the final message and every posted text.
The judge is Claude Opus with a 2-of-3 vote per rubric line.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
JUDGE_MODEL = "opus"


def final_message(tool, ws):
    if tool == "codex":
        path = ws / "final.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""
    result = ""
    for line in (ws / "trace.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event.get("result") or ""
    return result


def used_question_tool(tool, ws):
    text = (ws / "trace.jsonl").read_text(encoding="utf-8")
    if tool == "claude":
        return '"name":"AskUserQuestion"' in text.replace(" ", "")
    compact = text.replace(" ", "")
    return '"tool":"request_user_input"' in compact or '"name":"request_user_input"' in compact


def links_ok(message):
    links = re.findall(r"/files#diff-[^)\s]*", message)
    bad = [l for l in links if not re.fullmatch(r"/files#diff-[0-9a-f]{64}(R\d+)?", l)]
    spaced = re.findall(r"#diff-[0-9a-f]{8,} R\d+", message)
    return (not bad and not spaced), bad + spaced


PR_REVIEW_FLAGS = {"--approve": "APPROVE", "-a": "APPROVE", "--request-changes": "REQUEST_CHANGES",
                   "-r": "REQUEST_CHANGES", "--comment": "COMMENT", "-c": "COMMENT"}


def read_posts(posted):
    """Return (kind, event, texts) for each write the fake gh recorded."""
    posts = []
    for path in sorted(posted):
        record = json.loads(path.read_text(encoding="utf-8"))
        kind, body, args = record.get("kind") or "", record.get("body"), record.get("args") or []
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = {"body": body}
        if isinstance(body, list):
            body = dict(field.split("=", 1) for field in body if "=" in field)
        texts, event = [], None
        if isinstance(body, dict):
            event = body.get("event")
            texts.append(body.get("body") or "")
            texts += [c.get("body") or "" for c in body.get("comments") or [] if isinstance(c, dict)]
        event = event or next((PR_REVIEW_FLAGS[a] for a in args if a in PR_REVIEW_FLAGS), None)
        texts += [args[i + 1] for i, a in enumerate(args[:-1]) if a in ("--body", "-b")]
        posts.append((kind, event, [t for t in texts if t.strip()]))
    return posts


def posts_allowed(posts, may_post):
    """Check that every write is an allowed review, or a reaction next to one."""
    reviews = [e for k, e, _ in posts if "reactions" not in k]
    reactions = len(posts) - len(reviews)
    bad = [str(e) for e in reviews if e not in may_post]
    if reactions and not reviews:
        bad.append("reaction without a review")
    return not bad, bad


def judge(rubric, message):
    prompt = (
        "You grade one PR review produced by an agent. Grade meaning, not exact wording: the criterion is met when "
        "the review says the same thing in other words, whatever a finding's status or label. Answer with exactly "
        "PASS or FAIL on the first line, then one short sentence of reasoning.\n\n"
        f"Criterion: {rubric}\n\n--- REVIEW OUTPUT ---\n{message}\n--- END ---"
    )
    votes = []
    for _ in range(3):
        out = subprocess.run(
            ["claude", "-p", prompt, "--model", JUDGE_MODEL, "--max-budget-usd", "0.5", "--no-session-persistence"],
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
        ).stdout.strip()
        first = out.splitlines()[0].strip().upper() if out else ""
        votes.append((first.startswith("PASS"), out))
        if sum(v for v, _ in votes) >= 2 or sum(not v for v, _ in votes) >= 2:
            break
    passed = sum(v for v, _ in votes) >= 2
    reason = next((o for v, o in votes if v == passed), votes[-1][1])
    return passed, reason.replace("\n", " ")[:200]


def main():
    tool, ws, fixture = sys.argv[1], Path(sys.argv[2]).resolve(), sys.argv[3]
    spec = json.loads((HERE.parent / "fixtures" / fixture / "grade.json").read_text(encoding="utf-8"))
    message = final_message(tool, ws)
    rows = []

    calls = ws / "gh-calls.log"
    used_fake = calls.is_file() and calls.stat().st_size > 0
    leaked = [n for n in ("trace.jsonl", "stderr.log")
              if (ws / n).is_file() and "Bad credentials" in (ws / n).read_text(encoding="utf-8", errors="replace")]
    rows.append(("fake-gh", used_fake and not leaked,
                 "real gh refused in " + ", ".join(leaked) if leaked
                 else "fake gh used" if used_fake else "no fake gh calls; the run may have used the real gh"))

    posted = list((ws / "posted").glob("*")) if (ws / "posted").exists() else []
    posts = read_posts(posted)
    may_post = spec.get("may_post", [])
    ok, bad = posts_allowed(posts, may_post)
    rows.append(("posts", ok, f"{len(posts)} recorded writes; not allowed: {', '.join(bad)}" if bad
                 else f"{len(posts)} recorded writes, all allowed (may_post: {may_post or 'none'})"))
    texts = [t for _, _, ts in posts for t in ts]
    rows.append(("posted-text", *judge(
        "Every posted text is feedback the PR author can act on: a problem, a requested change, a question about "
        "the code, or a +1 on another comment with its reason. FAIL if any text only reports review status or "
        "progress, such as that no issues were found, the PR was re-reviewed at some commit, an earlier finding is "
        "addressed, the head is unchanged, or what changed since the last review.",
        "\n\n---\n\n".join(texts))) if texts else ("posted-text", True, "no posted review text"))
    asked = used_question_tool(tool, ws)
    rows.append(("no-question", not asked, "question tool called" if asked else "no question tool call"))
    links_good, bad_links = links_ok(message)
    rows.append(("links", links_good, "; ".join(bad_links)[:150] or "all well-formed"))
    if posts and ok:
        rows.append(("one-question", True, "skipped: an allowed review posted without asking"))
    elif spec.get("asks") is False:
        rows.append(("one-question", True, "skipped: the fixture expects nothing to ask"))
    else:
        rows.append(("one-question", *judge(
            "The review ends with one decision request covering all findings together; offering several ways to "
            "answer it (keep all, decide by ID, reword, go one by one) still counts as one request. When there are "
            "no findings, it may instead ask whether to submit. FAIL only if it asks a separate question per "
            "finding, asks nothing, or says a review was already posted.", message)))

    scores = json.loads((ws / "scores.json").read_text(encoding="utf-8")) if (ws / "scores.json").exists() else []
    # Without a linked ticket, the Spec axis is a lookup ("no spec available"), so any rung is fine.
    spec_scored = spec.get("spec") == "present"
    rung_fails = [r["label"] for r in scores if r.get("result") == "FAIL"
                  and (spec_scored or not (r.get("role") == "spec" or "spec" in r.get("label", "").lower()))]
    rows.append(("rungs", not rung_fails, "; ".join(rung_fails)[:150] or "all review roles on the required tier"))
    if "spec" in spec:
        has_spec = any(r.get("role") == "spec" for r in scores)
        want = spec["spec"] == "present"
        rows.append((f"spec-{spec['spec']}", has_spec == want, f"spec reviewer {'ran' if has_spec else 'did not run'}"))

    ran = [r["label"] for r in scores if r.get("role") in ("reviewer", "spec", "verifier")]
    if spec.get("reviewers") == "absent":
        rows.append(("reviewers-absent", not ran, "; ".join(ran)[:150] or "no review subagents ran"))
    else:
        reviewers = [r for r in scores if r.get("role") == "reviewer"]
        rows.append(("reviewers-ran", bool(reviewers), f"{len(reviewers)} reviewer subagents ran"))

    graded = message + "".join(f"\n\n--- POSTED TO GITHUB ---\n{t}" for t in texts)
    for i, rubric in enumerate(spec.get("must", []), 1):
        rows.append((f"must-{i}", *judge(rubric, graded)))
    for i, rubric in enumerate(spec.get("must_not", []), 1):
        passed, reason = judge(f"The review does NOT do the following: {rubric}", graded)
        rows.append((f"must-not-{i}", passed, reason))

    failed = [r for r in rows if not r[1]]
    for name, passed, detail in rows:
        print(f"{'PASS' if passed else 'FAIL'}  {name:14} {detail}")
    print(f"\n{fixture} [{tool}]: {len(rows) - len(failed)}/{len(rows)} checks passed")
    (ws / "grades.json").write_text(json.dumps([{"check": n, "pass": p, "detail": d} for n, p, d in rows], indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
