#!/usr/bin/env python3
"""Run the trigger cases in Codex and grade them like `claude plugin eval`.

    codex.py <out-dir> [--skills DIR] [--case GLOB] [--runs N] [-j N]

Codex has no Skill tool: it loads a skill by reading its SKILL.md. Each read of
`.../<name>/SKILL.md` counts as one `skills:<name>` call, so the cases' Claude
graders apply unchanged. Each run gets a private HOME and CODEX_HOME holding only
the skills linked in --skills (default ../skills) and auth, so the user's other
skills, AGENTS.md, and config stay out. A case's scaffold script fills the run's
working directory first. The model and reasoning effort come from the user's
config. Runs are read-only, have no connectors, plugins, or web search, and stop
after MAX_ACTIONS tool calls, or the case's max_turns if higher, like the Claude
cases' turn cap.
"""

import argparse
import os
import concurrent.futures
import fnmatch
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MAX_ACTIONS = 5
ATTEMPTS = 3
TIMEOUT_SECONDS = 600
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


def load_cases(pattern):
    cases = []
    for prompt in sorted((HERE / "evals").glob("*/prompt.md")):
        name = prompt.parent.name
        if not fnmatch.fnmatch(name, pattern):
            continue
        graders = []
        for path in sorted((prompt.parent / "graders").glob("*.md")):
            fields, _ = frontmatter(path)
            if fields.get("type") != "tool_used" or fields.get("tool") != "Skill":
                sys.exit(f"error: {path}: only tool_used Skill graders run in Codex")
            graders.append({
                "name": path.stem,
                "pattern": re.compile(fields["input_match"]),
                "min": int(fields.get("min", 1)),
                "max": int(fields["max"]) if "max" in fields else None,
            })
        fields, body = frontmatter(prompt)
        case_yaml = prompt.parent / "case.yaml"
        scaffold = re.search(r"scaffold_script:\s*(\S+)", case_yaml.read_text()) if case_yaml.exists() else None
        cases.append({"name": name, "prompt": body, "graders": graders,
                      "max_actions": max(MAX_ACTIONS, int(fields.get("max_turns", 0))),
                      "scaffold": prompt.parent / scaffold.group(1) if scaffold else None})
    return cases


def user_model():
    # Top-level keys only: tables later in the file reuse the same names.
    config = (Path.home() / ".codex" / "config.toml").read_text().split("\n[", 1)[0]
    args = []
    for key, flag in (("model", "model"), ("model_reasoning_effort", "model_reasoning_effort")):
        match = re.search(rf'^{key}\s*=\s*"([^"]+)"', config, re.M)
        if match:
            args += ["-c", f'{flag}="{match.group(1)}"']
    return args


def isolated_homes(out, skills_dir):
    home, codex_home = out / "home", out / "codex-home"
    skills = home / ".agents" / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    codex_home.mkdir(exist_ok=True)
    for link in sorted(skills_dir.iterdir()):
        target = skills / link.name
        if not target.exists():
            target.symlink_to(link.resolve())
    auth = codex_home / "auth.json"
    if not auth.exists():
        auth.symlink_to(Path.home() / ".codex" / "auth.json")
    return home, codex_home


def run(case, run_dir, env, model_args):
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["codex", "exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
           "-s", "read-only", "--json", "--disable", "apps", "--disable", "plugins",
           "-c", 'web_search="disabled"', *model_args, case["prompt"]]
    # `codex exec` can hang without output or fail on capacity, so a timer
    # enforces the deadline and such runs are retried instead of graded.
    for attempt in range(1, ATTEMPTS + 1):
        reads, actions, error = [], 0, None
        start = time.monotonic()
        # An empty directory outside out/ keeps Codex from finding other runs'
        # prompts and traces when it searches upward.
        with tempfile.TemporaryDirectory(prefix="codex-trigger-") as cwd, \
                open(run_dir / "trace.jsonl", "w") as trace, open(run_dir / "stderr.log", "w") as stderr:
            if case["scaffold"]:
                subprocess.run(["bash", case["scaffold"]], cwd=cwd, env=env, check=True,
                               stdout=stderr, stderr=stderr)
            proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=stderr, text=True)
            timer = threading.Timer(TIMEOUT_SECONDS, proc.kill)
            timer.start()
            try:
                for line in proc.stdout:
                    trace.write(line)
                    trace.flush()
                    event = json.loads(line)
                    item = event.get("item") or {}
                    if event.get("type") == "item.started":
                        reads += SKILL_READ.findall(item.get("command") or "")
                        actions += 1
                    if event.get("type") == "turn.failed":
                        error = event["error"]["message"]
                        break
                    if actions >= case["max_actions"] or event.get("type") == "turn.completed":
                        break
                else:
                    # Codex can exit without turn.failed, e.g. on a startup error.
                    error = "codex exited before turn.completed; see stderr.log"
            finally:
                if not timer.is_alive():
                    error = f"timeout after {TIMEOUT_SECONDS}s"
                timer.cancel()
                proc.kill()
                proc.wait()
        if error is None:
            break
        error = f"{error} (attempt {attempt} of {ATTEMPTS})"
    calls = [f"skills:{name}" for name in reads]
    graders = []
    for grader in case["graders"]:
        count = sum(1 for call in calls if grader["pattern"].search(call))
        high = grader["max"]
        passed = grader["min"] <= count and (high is None or count <= high)
        graders.append({"name": grader["name"], "passed": passed,
                        "explanation": f"Skill called {count}x (expected {grader['min']}..{'∞' if high is None else high})"})
    result = {"case": case["name"], "skills": calls, "actions": actions, "error": error,
              "seconds": round(time.monotonic() - start), "graders": graders,
              "passed": error is None and all(g["passed"] for g in graders)}
    (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--skills", type=Path, default=HERE / "skills")
    parser.add_argument("--case", default="*")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("-j", type=int, default=4)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    home, codex_home = isolated_homes(out, args.skills)
    env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(codex_home)}
    model_args = user_model()
    cases = load_cases(args.case)
    jobs = [(c, out / c["name"] / f"r{i}") for c in cases for i in range(1, args.runs + 1)]
    with concurrent.futures.ThreadPoolExecutor(args.j) as pool:
        results = list(pool.map(lambda job: run(*job, env, model_args), jobs))
    summary = {"model": model_args, "cases": {}}
    for case in cases:
        runs = [r for r in results if r["case"] == case["name"]]
        summary["cases"][case["name"]] = {
            "passRate": sum(r["passed"] for r in runs) / len(runs),
            "failures": sorted({f"{g['name']}: {g['explanation']}" for r in runs for g in r["graders"] if not g["passed"]}
                               | {f"error: {r['error']}" for r in runs if r["error"]}),
        }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if all(c["passRate"] == 1 for c in summary["cases"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
