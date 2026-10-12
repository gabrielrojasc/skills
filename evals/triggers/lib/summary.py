#!/usr/bin/env python3
"""Print one table of pass rates from a Claude and a Codex trigger run.

    summary.py <claude-result.json> <codex-summary.json>
"""

import json
import sys


def claude(path):
    cases = {}
    for case in json.load(open(path))["cases"]:
        runs = case["arms"]["with"]
        failures = sorted({f"{g['name']}: {g['explanation']}" for r in runs for g in r["graders"] if not g["passed"]})
        cases[case["name"]] = {"passRate": case["aggregates"]["passRate"], "failures": failures}
    return cases


def table(title, tools, names):
    width = max(map(len, names))
    print(f"{title:<{width}}  claude  codex")
    notes = []
    for name in names:
        rates = []
        for tool, cases in tools.items():
            case = cases.get(name)
            rates.append("   -  " if case is None else f"{case['passRate']:6.2f}")
            for failure in (case or {}).get("failures", []):
                notes.append(f"{tool} {name}: {failure}")
        print(f"{name:<{width}}  {rates[0]}  {rates[1]}")
    for note in notes:
        print(note)
    rates = [cases[n]["passRate"] for cases in tools.values() for n in names if n in cases]
    print(f"passed {sum(r == 1 for r in rates)}/{len(rates)} case-tool pairs\n")
    return all(r == 1 for r in rates)


def main():
    tools = {"claude": claude(sys.argv[1]), "codex": json.load(open(sys.argv[2]))["cases"]}
    names = sorted(set(tools["claude"]) | set(tools["codex"]))
    main_names = [n for n in names if not n.startswith("hard-")]
    hard_names = [n for n in names if n.startswith("hard-")]
    passed = table("case", tools, main_names) if main_names else True
    if hard_names:
        table("hard case", tools, hard_names)
    # Hard cases are expected to fail sometimes; only the main tier gates.
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
