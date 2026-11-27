#!/usr/bin/env python3
"""Run trigger cases in Antigravity (`agy`) and grade them like `codex.py`.

    agy.py <out-dir> [--skills DIR] [--case GLOB] [--model MODEL] [--runs N] [-j N]

Antigravity loads workspace skills from `.agents/skills/<name>/SKILL.md`. Each
unique read of `.../<name>/SKILL.md` in a tool step counts as one `skills:<name>`
call, so the cases' Claude graders apply unchanged. Each run uses an isolated
HOME (symlinking only CLI state, config.json, and ~/Library for auth, leaving
global skills and AGENTS.md empty) and a clean git workspace containing only
the skills linked in --skills.
"""

import argparse
import concurrent.futures
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MAX_ACTIONS = 5
ATTEMPTS = 2
TIMEOUT_SECONDS = 180
DEFAULT_MODEL = "gemini-4-neon-high"
SKILL_READ = re.compile(r"/([\w.-]+)/SKILL\.md")


def frontmatter(path):
    text = path.read_text()
    _, head, body = text.split("---\n", 2)
    fields = {}
    for line in head.splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        fields[key.strip()] = value
    return fields, body.strip()


def regex_grader(path, fields):
    flags = fields.get("flags", "")
    if fields.get("target", "last_message") != "last_message" or set(flags) - set("is") \
            or fields.get("match", "contains") not in ("contains", "not_contains"):
        sys.exit(f"error: {path}: agy runs regex graders on last_message with flags i and s")
    compiled = re.compile(fields["pattern"], (re.I if "i" in flags else 0) | (re.S if "s" in flags else 0))
    return {"name": path.stem, "regex": compiled, "contains": fields.get("match", "contains") == "contains"}


def grade(grader, calls, final):
    if "regex" in grader:
        if not final:
            return False, "no final reply"
        found = grader["regex"].search(final)
        expected = "contains" if grader["contains"] else "does not contain"
        return grader["contains"] == bool(found), \
            f"final reply {expected} /{grader['regex'].pattern}/" + (f"; found {found.group(0)!r}" if found else "")
    count = sum(1 for call in calls if grader["pattern"].search(call))
    high = grader["max"]
    passed = grader["min"] <= count and (high is None or count <= high)
    return passed, f"Skill called {count}x (expected {grader['min']}..{'∞' if high is None else high})"


def load_cases(pattern):
    cases = []
    for prompt in sorted((HERE / "evals").glob("*/prompt.md")):
        name = prompt.parent.name
        if not fnmatch.fnmatch(name, pattern):
            continue
        graders = []
        for path in sorted((prompt.parent / "graders").glob("*.md")):
            fields, _ = frontmatter(path)
            if fields.get("type") == "regex":
                graders.append(regex_grader(path, fields))
                continue
            if fields.get("type") != "tool_used" or fields.get("tool") != "Skill":
                sys.exit(f"error: {path}: only tool_used Skill and regex graders run in agy")
            graders.append({
                "name": path.stem,
                "pattern": re.compile(fields["input_match"]),
                "min": int(fields.get("min", 1)),
                "max": int(fields["max"]) if "max" in fields else None,
            })
        fields, body = frontmatter(prompt)
        case_yaml = prompt.parent / "case.yaml"
        scaffold = re.search(r"scaffold_script:\s*(\S+)", case_yaml.read_text()) if case_yaml.exists() else None
        cases.append({
            "name": name,
            "prompt": body,
            "graders": graders,
            "max_actions": max(MAX_ACTIONS, int(fields.get("max_turns", 0))),
            "scaffold": prompt.parent / scaffold.group(1) if scaffold else None,
        })
    return cases


def isolated_home(out):
    home = out / "home"
    (home / ".gemini" / "config").mkdir(parents=True, exist_ok=True)
    real = Path.home()
    for rel in (
        Path(".gemini/antigravity-cli"),
        Path(".gemini/config/config.json"),
        Path("Library"),
    ):
        src = real / rel
        dst = home / rel
        if src.exists() and not dst.exists():
            dst.symlink_to(src)
    return home


def extract_tool_info(event):
    if event.get("event") != "step_update":
        return None, []
    upd = event.get("step_update") or {}
    step_type = str(upd.get("type") or upd.get("step_type") or "")
    # Ignore pure user input or thinking/text-only updates unless tool fields appear.
    payload = json.dumps(upd)
    is_tool = any(k in payload for k in (
        "view_file", "read_file", "run_command", "grep_search", "find_by_name",
        "list_dir", "tool_call", "VIEW_FILE", "RUN_COMMAND", "CORTEX_STEP_TYPE_VIEW_FILE",
        "CORTEX_STEP_TYPE_RUN_COMMAND", "CORTEX_STEP_TYPE_FIND", "CORTEX_STEP_TYPE_GREP",
    ))
    step_id = upd.get("step_index") if "step_index" in upd else upd.get("index")
    if step_id is None:
        step_id = f"{step_type}:{hash(payload)}"
    reads = SKILL_READ.findall(payload) if is_tool else []
    return (step_id if is_tool else None), reads


def run(case, run_dir, env, skills_dir, model):
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "agy",
        "--model", model,
        "--output-format", "stream-json",
        "--sandbox",
        "--print-timeout", f"{TIMEOUT_SECONDS}s",
        "-p", case["prompt"],
    ]
    for attempt in range(1, ATTEMPTS + 1):
        read_steps = {}
        tool_steps = set()
        error, final = None, ""
        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="agy-trigger-") as cwd, \
                open(run_dir / "trace.jsonl", "w") as trace, \
                open(run_dir / "stderr.log", "w") as stderr:
            ws = Path(cwd)
            subprocess.run(["git", "init", "-q"], cwd=ws, env=env, check=True, stdout=stderr, stderr=stderr)
            sk = ws / ".agents" / "skills"
            sk.mkdir(parents=True)
            for link in sorted(skills_dir.iterdir()):
                (sk / link.name).symlink_to(link.resolve())
            if case["scaffold"]:
                subprocess.run(["bash", case["scaffold"]], cwd=ws, env=env, check=True, stdout=stderr, stderr=stderr)
            proc = subprocess.Popen(cmd, cwd=ws, env=env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=stderr, text=True)
            timer = threading.Timer(TIMEOUT_SECONDS, proc.kill)
            timer.start()
            try:
                for line in proc.stdout:
                    trace.write(line)
                    trace.flush()
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    step_id, reads = extract_tool_info(event)
                    if step_id is not None:
                        tool_steps.add(step_id)
                        if reads:
                            read_steps.setdefault(step_id, set()).update(reads)
                    if event.get("event") == "result":
                        res = event.get("result") or {}
                        if res.get("status") == "ERROR" or res.get("error"):
                            error = res.get("error") or f"status={res.get('status')}"
                        else:
                            final = res.get("response") or ""
                        break
                    if len(tool_steps) >= case["max_actions"]:
                        break
                else:
                    error = "agy exited before result; see stderr.log"
            finally:
                if not timer.is_alive():
                    error = f"timeout after {TIMEOUT_SECONDS}s"
                timer.cancel()
                proc.kill()
                proc.wait()
        if error is None:
            break
        error = f"{error} (attempt {attempt} of {ATTEMPTS})"
    calls = [f"skills:{name}" for names in read_steps.values() for name in sorted(names)]
    graders = []
    for grader in case["graders"]:
        passed, explanation = grade(grader, calls, final)
        graders.append({"name": grader["name"], "passed": passed, "explanation": explanation})
    result = {
        "case": case["name"],
        "skills": calls,
        "actions": len(tool_steps),
        "error": error,
        "final_reply": final,
        "seconds": round(time.monotonic() - start),
        "graders": graders,
        "passed": error is None and all(g["passed"] for g in graders),
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--skills", type=Path, default=HERE / "skills")
    parser.add_argument("--case", default="*council*")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("-j", type=int, default=4)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    home = isolated_home(out)
    env = {**os.environ, "HOME": str(home)}
    cases = load_cases(args.case)
    jobs = [(c, out / c["name"] / f"r{i}") for c in cases for i in range(1, args.runs + 1)]
    with concurrent.futures.ThreadPoolExecutor(args.j) as pool:
        results = list(pool.map(lambda job: run(*job, env, args.skills, args.model), jobs))
    summary = {"model": args.model, "cases": {}}
    for case in cases:
        runs = [r for r in results if r["case"] == case["name"]]
        summary["cases"][case["name"]] = {
            "passRate": sum(r["passed"] for r in runs) / len(runs),
            "failures": sorted(
                {f"{g['name']}: {g['explanation']}" for r in runs for g in r["graders"] if not g["passed"]}
                | {f"error: {r['error']}" for r in runs if r["error"]}
            ),
        }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if all(c["passRate"] == 1 for c in summary["cases"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
