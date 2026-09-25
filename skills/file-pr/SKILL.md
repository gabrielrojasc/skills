---
name: file-pr
description: Creates a PR. Use when asked to file or open one.
---

# File a pull request

Create one concise pull request whose title and description explain why the
change matters.

Interpret the PR request using the full conversation. A request to file a PR for
agreed work authorizes completing that implementation, running its checks,
committing the relevant changes, one necessary branch push, and creating the PR.
Preserve explicit instructions such as "don't commit yet" and other applicable
approval gates.

The request does not expand the agreed scope or authorize unrelated edits,
rebases, comments, review-thread resolution, merge, closure, or changing the
state of an existing PR.

## Preflight

1. Read the repository's agent guidance, contribution guide, pull request
   template, and relevant workflow documentation.
2. Identify the current branch, its upstream, the remote default branch, and the
   intended base branch.
3. Check whether an open or closed pull request already exists for the branch.
   If one is open, verify and return it without changing its state. If one is
   closed or merged, report it and ask before creating another pull request.
4. Review the commit list, diff against the base branch, and uncommitted
   changes. Determine the intended scope from the conversation and repository
   evidence.
5. Finish and validate the agreed work, then commit only its relevant changes
   using repository conventions. Preserve unrelated work. Ask only when a
   material scope decision or an unmet approval gate prevents progress. Before
   publishing, verify that the complete committed diff matches the agreed scope.
   Uncommitted work alone is not a reason to stop.
6. Inspect recent merged pull request titles and the repository's documented
   conventions before choosing the title and body format.

## Write the pull request

- Use the repository's title convention. Prefer a concise title that states the
  user-visible or operational reason for the change.
- Open the body with a plain-language explanation of the problem from the user's
  request.
- Explain the solution after the problem. Do not lead with a file or commit
  inventory.
- Include validation performed and any known limitations.
- Follow the repository template when one exists. Remove empty boilerplate that
  the template does not require.
- Include screenshots, recordings, or artifact links only when they already
  exist within the authorized scope.
- For Linear-tracked work, apply `linear-gh-linking` to choose the issue
  references and relationship words.

## Publish

1. Push the current branch once when the remote branch is missing or behind. Use
   a normal push. If the branch is yours and was rebased onto its base, use
   `git push --force-with-lease`. Never force-push in any other case.
2. Create the pull request in ready-for-review state unless the user or
   repository explicitly requests a draft. Use the selected base branch, title,
   and body.
3. Read the created pull request back and verify its base, head, requested draft
   or ready state, title, and body. For Linear-tracked work, also run
   `linear-gh-linking`'s link verification.
4. Return the pull request URL and any unresolved limitation.

## Guardrails

- Do not comment, request reviewers, change labels, change the state of an
  existing pull request, merge, or close unless the user separately asks.
- If authentication or repository permissions fail, follow the global external
  service recovery policy. Do not change authentication.
