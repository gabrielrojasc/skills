---
name: python-environments
description: Use when running Python tests or installs.
---

# Python environments

Create environments with `uv venv`. Keep the repository's dependency manager;
uv creates the environment and doesn't replace Poetry or pip. Keep Python
packages and tools out of global installations.

## Workflow

1. Identify the project root, required Python version, dependency manager, and
   documented setup command.
2. Inspect any existing environment before replacing it. Reuse it when it uses a
   compatible Python version and is healthy, regardless of which tool created
   it.
3. Create a missing or approved replacement environment with `uv venv`. Request
   the repository's Python version explicitly when configuration does not make
   the choice unambiguous:

   ```bash
   uv venv --python <version> .venv
   ```

   Omit `--python` when the repository configuration already gives uv an
   unambiguous compatible version.
4. Activate the environment before running project commands:

   ```bash
   source .venv/bin/activate
   ```

5. Install dependencies with the repository's existing dependency manager and
   documented command. If the repository uses Poetry and Poetry is unavailable,
   install Poetry inside the active environment, never globally.
6. Run project commands inside the active environment. Use `uv run` only when
   the repository uses uv for its project workflow.
7. Verify the interpreter and environment before completion:

   ```bash
   command -v python
   python --version
   ```

When repository files conflict on the Python version, or satisfying them means
changing the declared range, stop and propose a version or range, citing what
each source requires.
