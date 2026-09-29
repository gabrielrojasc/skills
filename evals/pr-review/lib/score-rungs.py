#!/usr/bin/env python3
"""Score which model and effort ran each pr-review role in a headless run.

Reads a Claude Code stream-json trace or a Codex exec JSON trace, finds every
subagent the run spawned, and checks each review role against the acceptance
criteria for its PR's risk class:

  trivial  any tier
  normal   reviewers and verifiers run on tier 3 or higher
           (Claude: effort high, xhigh, or max; Codex: any model except gpt-6-luna)
  risky    reviewers and verifiers run on tier 4
           (Claude: effort xhigh or max; Codex: gpt-6-astra)

Progress checks and other helpers are reported but not scored.

Usage:
  score-rungs.py claude <trace.jsonl> --expect 7=normal 8=trivial 9=risky
  score-rungs.py codex  <trace.jsonl> --expect 7=normal [--sessions ~/.codex/sessions]
"""

import argparse
import json
import re
import sys
from pathlib import Path

CLAUDE_AGENTS = Path.home() / ".claude" / "agents"
SCORED_ROLES = {"reviewer", "spec", "verifier"}


def role_of(label):
    text = label.lower()
    if "progress" in text:
        return "progress"
    if "verif" in text:
        return "verifier"
    if "spec" in text:
        return "spec"
    if "review" in text or "standards" in text:
        return "reviewer"
    return "other"


def pr_of(label, known):
    for number in sorted(known, key=len, reverse=True):
        if re.search(rf"(?<![0-9]){number}(?![0-9])", label):
            return number
    return next(iter(known)) if len(known) == 1 else "?"


def claude_rung(name):
    """Return (model, effort) from a Claude agent file's frontmatter."""
    path = CLAUDE_AGENTS / f"{name}.md"
    if not path.is_file():
        return ("inherit", "inherit")
    fields = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return (fields.get("model", "inherit"), fields.get("effort", "inherit"))


def claude_spawns(trace):
    spawns = []
    for line in trace.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") in ("Agent", "Task"):
                args = block.get("input") or {}
                rung = args.get("subagent_type") or "general-purpose"
                model, effort = claude_rung(rung)
                spawns.append({"label": args.get("description", ""), "rung": rung,
                               "model": args.get("model") or model, "effort": effort, "forked": False})
    return spawns


def codex_spawns(trace, sessions, thread_id=None):
    for line in ([] if thread_id else trace.read_text(encoding="utf-8").splitlines()):
        event = json.loads(line)
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id")
            break
    if thread_id is None:
        sys.exit("no thread.started event in the Codex trace")
    metas = {}
    for path in sessions.rglob("rollout-*.jsonl"):
        with path.open(encoding="utf-8") as fh:
            meta = json.loads(fh.readline()).get("payload", {})
            if not meta.get("parent_thread_id"):
                continue
            model = effort = None
            for raw in fh:
                event = json.loads(raw)
                if event.get("type") == "turn_context":
                    model, effort = event["payload"].get("model"), event["payload"].get("effort")
                    break
        metas[meta["id"]] = {**meta, "model": model, "effort": effort}
    # Walk descendants of the run's thread so nested delegation is included.
    family, frontier = set(), {thread_id}
    while frontier:
        children = {sid for sid, m in metas.items() if m["parent_thread_id"] in frontier} - family
        family |= children
        frontier = children
    # Codex's own approval reviewers ("guardian") aren't pr-review roles.
    family = {sid for sid in family if metas[sid].get("agent_path")}
    return [{"label": metas[sid].get("agent_path") or "", "rung": metas[sid].get("agent_role"),
             "model": metas[sid]["model"], "effort": metas[sid]["effort"],
             "forked": bool(metas[sid].get("forked_from_id"))} for sid in sorted(family)]


def passes(tool, risk, spawn):
    if risk == "trivial":
        return True
    if tool == "claude":
        allowed = {"normal": {"high", "xhigh", "max"}, "risky": {"xhigh", "max"}}[risk]
        return spawn["effort"] in allowed
    if risk == "normal":
        return bool(spawn["model"]) and spawn["model"] != "gpt-6-luna"
    return spawn["model"] == "gpt-6-astra"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tool", choices=["claude", "codex"])
    parser.add_argument("trace", type=Path, nargs="?", help="headless run trace (omit with --thread)")
    parser.add_argument("--thread", help="Codex parent thread id to score instead of a trace")
    parser.add_argument("--expect", nargs="+", required=True, help="PR=risk pairs, e.g. 7=normal")
    parser.add_argument("--sessions", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--json", type=Path, help="also write the scored rows as JSON")
    args = parser.parse_args()
    expect = dict(pair.split("=", 1) for pair in args.expect)

    spawns = claude_spawns(args.trace) if args.tool == "claude" else codex_spawns(args.trace, args.sessions, args.thread)
    rows = []
    for spawn in spawns:
        role = role_of(spawn["label"])
        pr = pr_of(spawn["label"], expect)
        risk = expect.get(pr, "?")
        scored = role in SCORED_ROLES and risk != "?"
        rows.append({**spawn, "role": role, "pr": pr, "risk": risk,
                     "result": ("PASS" if passes(args.tool, risk, spawn) else "FAIL") if scored else "-"})

    print(f"{'PR':4} {'risk':8} {'role':9} {'rung':15} {'model':18} {'effort':8} {'fork':5} result  label")
    for r in sorted(rows, key=lambda r: (r["pr"], r["role"])):
        print(f"{r['pr']:4} {r['risk']:8} {r['role']:9} {str(r['rung']):15} {str(r['model']):18} "
              f"{str(r['effort']):8} {'yes' if r['forked'] else 'no':5} {r['result']:7} {r['label'][:60]}")
    scored = [r for r in rows if r["result"] != "-"]
    failed = [r for r in scored if r["result"] == "FAIL"]
    print(f"\n{len(spawns)} subagents, {len(scored)} scored, {len(failed)} failed")
    if args.json:
        args.json.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
