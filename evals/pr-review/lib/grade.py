#!/usr/bin/env python3
"""Grade one headless pr-review run against its fixture's rubric.

  grade.py <claude|codex> <workspace> <fixture>

Checks that apply to every run:
  no-post        nothing was written to posted/ (the fake gh records writes there)
  no-question    no question or multiple-choice tool was called
  links          every Files-changed link has a 64-char hash directly followed by R<line>
  one-question   the final message ends with one batch question (model-graded)
  rungs          review roles ran on the required tier (score-rungs.py)

Fixture checks come from fixtures/<fixture>/grade.json:
  must       rubric sentences the review has to satisfy (model-graded, each separately)
  must_not   rubric sentences the review must not do (model-graded)
  spec       "absent" or "present": whether a Spec reviewer should run
  reviewers  "absent": no reviewer, Spec, or verifier subagent should run
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

    posted = list((ws / "posted").glob("*")) if (ws / "posted").exists() else []
    rows.append(("no-post", not posted, f"{len(posted)} recorded writes"))
    asked = used_question_tool(tool, ws)
    rows.append(("no-question", not asked, "question tool called" if asked else "no question tool call"))
    ok, bad = links_ok(message)
    rows.append(("links", ok, "; ".join(bad)[:150] or "all well-formed"))
    rows.append(("one-question", *judge(
        "The review ends with one decision request covering all findings together; offering several ways to answer "
        "it (keep all, decide by ID, reword, go one by one) still counts as one request. When there are no findings, "
        "it may instead ask whether to submit. FAIL only if it asks a separate question per finding, asks nothing, "
        "or says a review was already posted.", message)))

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

    if spec.get("reviewers") == "absent":
        ran = [r["label"] for r in scores if r.get("role") in ("reviewer", "spec", "verifier")]
        rows.append(("reviewers-absent", not ran, "; ".join(ran)[:150] or "no review subagents ran"))

    for i, rubric in enumerate(spec.get("must", []), 1):
        rows.append((f"must-{i}", *judge(rubric, message)))
    for i, rubric in enumerate(spec.get("must_not", []), 1):
        passed, reason = judge(f"The review does NOT do the following: {rubric}", message)
        rows.append((f"must-not-{i}", passed, reason))

    failed = [r for r in rows if not r[1]]
    for name, passed, detail in rows:
        print(f"{'PASS' if passed else 'FAIL'}  {name:14} {detail}")
    print(f"\n{fixture} [{tool}]: {len(rows) - len(failed)}/{len(rows)} checks passed")
    (ws / "grades.json").write_text(json.dumps([{"check": n, "pass": p, "detail": d} for n, p, d in rows], indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
