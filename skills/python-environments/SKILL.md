---
name: python-environments
description: Use when creating or repairing Python project environments.
---

# Python environments

Use `uv venv` for every Python virtual environment. Keep Python interpreters,
tools, and project dependencies out of global language installations.

## Precedence

Use guidance in this order:

1. The user's explicit Python version or environment requirement.
2. The repository's documented setup and dependency workflow.
3. Repository configuration such as `.python-version`, `requires-python`, CI,
   runtime files, and tool configuration.
4. The defaults in this skill.

Keep the repository's dependency manager. Creating the environment with `uv`
does not authorize migrating Poetry, pip, pip-tools, or another dependency
workflow to uv.

## Workflow

1. Identify the project root, required Python version, dependency manager, and
   documented setup command.
2. Inspect any existing environment before replacing it. Reuse it when it was
   created by `uv`, uses a compatible Python version, and is healthy.
3. Create a missing or approved replacement environment with `uv venv`.
   Request the repository's Python version explicitly when configuration does
   not make the choice unambiguous:

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

## Guardrails

- Do not install Python packages or Python-based tools globally.
- Do not recreate a working environment without a reason tied to the task.
- Do not change the repository's declared Python range, dependency manager, or
  lockfile format unless the user asks.
- If repository files give conflicting Python requirements, or satisfying them
  requires changing the declared range, stop and ask.

## Completion criteria

- The environment was created by `uv venv` or an existing compatible uv-created
  environment was reused.
- `python` resolves inside the project environment and reports a compatible
  version.
- Dependencies and commands use the repository's existing workflow.
- No Python package or tool was installed into a global Python environment.
