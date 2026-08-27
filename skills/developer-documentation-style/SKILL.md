---
name: developer-documentation-style
description: Applies Google's live guide. Use when working on developer docs.
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

## Use upstream selectively

Identify material editorial questions before browsing. Open only the official
`https://developers.google.com/style/` pages that answer those questions. Open
the guide overview for a broad Google-style review or when the relevant page is
unclear.

A narrow task may require no upstream lookup. Attribute a finding to Google or
claim Google-style compliance only after checking the relevant live page.

If a required live page is unavailable, report that and ask whether to continue
with a best-effort editorial pass.

## Workflow

1. Identify the audience, goal, document type, requested operation, and files in
   scope.
2. For repository work, read the applicable repository instructions and style
   conventions.
3. Read only the upstream pages required by the material editorial questions.
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
