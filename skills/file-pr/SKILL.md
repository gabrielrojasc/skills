---
name: file-pr
description: Creates a ready PR. Use when asked to file or open one.
---

# File a pull request

Create one concise ready-for-review pull request whose title and description
explain why the change matters.

The user's request to file, open, or create a pull request authorizes the
read-only inspection, one necessary non-force branch push, and one
ready-for-review pull request creation described here. It does not authorize
code changes, rebases, comments, review-thread resolution, merge, closure, or
changing the state of an existing pull request.

## Preflight

1. Read the repository's agent guidance, contribution guide, pull request
   template, and relevant workflow documentation.
2. Identify the current branch, its upstream, the remote default branch, and the
   intended base branch.
3. Check whether an open or closed pull request already exists for the branch.
   If one is open, verify and return it without changing its state. If one is
   closed or merged, report it and ask before creating another pull request.
4. Review the complete commit list and diff against the base branch. Confirm that
   the committed changes match the user's goal and contain no unrelated work.
5. If relevant changes remain uncommitted, or the committed diff does not match
   the requested goal, stop and report the mismatch. Do not edit or commit code
   as part of this skill.
6. Inspect recent merged pull request titles and the repository's documented
   conventions before choosing the title and body format.

## Write the pull request

- Use the repository's title convention. Prefer a concise title that states the
  user-visible or operational reason for the change.
- Open the body with a plain-language explanation of the problem from the
  user's request.
- Explain the solution after the problem. Do not lead with a file or commit
  inventory.
- Include validation performed and any known limitations.
- Follow the repository template when one exists. Remove empty boilerplate that
  the template does not require.
- Include screenshots, recordings, or artifact links only when they already
  exist within the authorized scope.

## Publish

1. Push the current branch once when the remote branch is missing or behind. Use
   a normal push; never force-push.
2. Create the pull request in ready-for-review state with the selected base
   branch, title, and body.
3. Read the created pull request back and verify its base, head, ready state,
   title, and body.
4. Return the pull request URL and any unresolved limitation.

## Guardrails

- Do not change code while preparing the pull request.
- Do not include unrelated commits or let the description expand the requested
  scope.
- Do not create a second pull request for the same branch.
- Do not comment, request reviewers, change labels, change the state of an
  existing pull request, merge, or close unless the user separately asks.
- If authentication or repository permissions fail, follow the global external
  service recovery policy. Do not change authentication.

## Completion criteria

- If a new pull request was required, exactly one ready-for-review pull request
  was created for the branch.
- If an open pull request already existed, it was verified and returned with its
  current state unchanged.
- The base and head branches are correct.
- For a newly created pull request, the title follows repository conventions and
  the body explains the problem, solution, and validation.
- The returned URL opens the verified pull request.
