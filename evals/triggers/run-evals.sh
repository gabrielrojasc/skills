#!/usr/bin/env bash
# Check that each model-invoked skill fires on the prompts it should and stays
# silent on near misses. Arguments pass through to `claude plugin eval`, for
# example `--case 'python-environments*'`, `--runs 5`, or `-j 4`.
#
# Eval runs see only built-in skills and the ones linked under skills/, not the
# user's installed skills or global instructions. A run without the plugin has
# no skills to fire, so the baseline arm is off.
set -euo pipefail

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
exec claude plugin eval . --no-publish --trust-plugin --ablation none "$@"
