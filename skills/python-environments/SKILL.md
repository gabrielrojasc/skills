---
name: python-environments
description: Use when running Python tests or installs.
---

# Python environments

Create the environment with `uv venv`, and install with the repository's own
dependency manager, such as Poetry or pip. Keep Python packages and tools out
of global installs.

1. Reuse an existing environment when it works and its Python version fits the
   repository, whichever tool made it.
2. Otherwise run `uv venv .venv`. Add `--python <version>` when the
   repository's config doesn't settle the version.
3. Run `source .venv/bin/activate`, then install with the repository's
   documented command. If the repository uses Poetry and it's missing, install
   Poetry inside the environment.
4. Run project commands inside the environment. Use `uv run` only when the
   repository uses uv for its own workflow.

When the repository's files disagree on the Python version, or meeting them
means changing the declared range, stop and propose a version, citing what each
file requires.
