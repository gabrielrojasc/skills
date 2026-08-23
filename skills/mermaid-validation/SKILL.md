---
name: mermaid-validation
description: Validate Mermaid diagrams by rendering them with Mermaid CLI. Use when creating or editing Mermaid blocks or `.mmd` files, or when diagnosing Mermaid parse and rendering failures.
---

# Mermaid validation

Render every created or modified Mermaid diagram before calling it valid. A
plausible-looking code block is not enough.

Resolve `<SKILL_DIR>` as the directory containing this `SKILL.md` before running
the bundled helper.

## Workflow

1. Identify every Mermaid block or `.mmd` file changed by the task.
2. Use the repository's Mermaid validation command when one exists. Otherwise,
   render each diagram outside the sandbox with the bundled helper. It prefers a
   repository-local `mmdc`, then `mmdc` on `PATH`, and points Puppeteer at the
   installed Chrome executable:

   ```bash
   <SKILL_DIR>/scripts/render-mermaid.sh --input <diagram.mmd>
   ```

   If Mermaid CLI is unavailable and fetching it is within the approved task
   scope, add `--allow-fetch` to use the official package through `npx`.
3. For Mermaid embedded in Markdown, copy each changed block into a temporary
   `.mmd` file before calling the helper.
4. Treat a nonzero exit as a validation failure. Fix the source and render
   again.
5. Inspect the rendered image when layout, labels, clipping, contrast, or edge
   routing matters. Syntax success alone does not verify those properties.

## Guardrails

- Run browser-backed rendering outside the sandbox.
- Keep temporary inputs and outputs outside the repository unless the user asks
  for a rendered artifact.
- Do not install Mermaid CLI globally. The helper's optional `npx` path runs the
  package without a global installation.
- Preserve the diagram's intended meaning while fixing syntax or layout.

## Completion criteria

- Every changed Mermaid diagram renders successfully with `mmdc`.
- Relevant rendered output was visually inspected.
- Validation leaves no unrequested repository files or global installation.
