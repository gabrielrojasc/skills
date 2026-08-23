---
name: developer-documentation-style
description: Use when writing, editing, or reviewing developer docs.
metadata:
  source: https://developers.google.com/style/
  source_owner: Google LLC
  status: unofficial-personal-skill
---

# Developer documentation style

Use the live Google Developer Documentation Style Guide as the default editorial
reference for developer-facing documentation. This is an unofficial personal
workflow. Google has not authored or endorsed it.

## Scope

Use this skill for READMEs, tutorials, procedures, conceptual documentation,
CLI reference, API reference prose, and documentation reviews. Apply it to code
comments only when the user explicitly asks.

A review is read-only. Return findings and suggested changes without modifying
files or external content unless the user asks for edits.

## Authority

Apply guidance in this order:

1. The user's explicit requirements.
2. The repository or product's documented conventions.
3. The live Google Developer Documentation Style Guide.
4. General editorial judgment.

Depart from the guide when a higher authority requires it or when the guide
allows a clearer, more consistent choice for the intended readers. Do not
present personal judgment as a Google rule.

## Read upstream first

Read `https://developers.google.com/style/` on every invocation. Identify the
document type and editorial questions, then open the official `/style/` pages
that govern them before drafting, editing, or reporting findings. Do not replace
this step with remembered or locally distilled rules.

Use only the relevant upstream pages. Do not browse the entire guide when the
task has a narrow scope.

If the live guide is unavailable, report that the required source could not be
read and ask whether to continue with a best-effort editorial pass. Do not claim
Google-style compliance without reading the upstream guidance.

## Workflow

1. Identify the audience, goal, document type, requested operation, and files in
   scope.
2. For repository work, read the applicable repository instructions and style
   conventions.
3. Read the upstream guide and the official pages relevant to the task.
4. Draft, edit, or review within the user's authorization.
5. Preserve technical meaning, exact identifiers, required terminology, code,
   commands, paths, and citations.
6. Check the result against every upstream page consulted and the repository's
   conventions.

## Reviews and edits

For a review, report only material findings. Each finding includes:

- Its location.
- The editorial problem.
- The governing repository rule or official Google page.
- A concrete correction.

Cite the official page for every finding attributed to Google. Separate
technical ambiguity from editorial findings. If no material findings remain,
say so.

For a rewrite, return revised copy and list unresolved technical ambiguities
separately. Do not invent behavior, requirements, or claims to improve the
prose.

For file edits, change only the authorized files and preserve unrelated content.

## API documentation boundary

Apply editorial guidance to API reference prose. Do not infer API behavior,
schemas, compatibility, generated output, or design requirements from a style
guide. Preserve or flag unsupported technical claims unless the user separately
requests technical verification.

## Attribution

Adapted from the Google Developer Documentation Style Guide, copyright Google
LLC, under Creative Commons Attribution 4.0. Google states that code samples use
the Apache 2.0 License; this skill does not copy code samples.

- Source: https://developers.google.com/style/
- License: https://creativecommons.org/licenses/by/4.0/
