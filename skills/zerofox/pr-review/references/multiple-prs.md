# Multiple PRs

Do each PR's setup and start its reviewers as soon as that PR's own setup is
done, without waiting for other PRs. Each axis moves to verification without
waiting for other PRs. Sibling PRs with identical changes, such as matching
renovate configs, may share one Standards agent with a folder per PR.

Take one PR at a time, in the order they finish verification, and carry it
through triage and submission before showing the next. Other PRs keep reviewing
and verifying in the background, but the user sees only one open decision at a
time; about other PRs, send only short progress notes, never findings or
questions.

Some hosts, such as Codex, don't resume you when a background agent finishes,
so no review advances while a question waits for the user. There, carry every
PR through verification before asking the first triage question; after that,
each answer leads straight to the next ready PR. In hosts that resume you, show
each PR as soon as it is verified.

After submitting or skipping a PR, move to the next ready PR.
