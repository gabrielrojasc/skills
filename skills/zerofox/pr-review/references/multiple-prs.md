# Multiple PRs

Start each PR's reviewers as soon as its setup is done, without waiting for
other PRs. Sibling PRs with identical changes, such as matching renovate
configs, may share one Standards agent with a folder per PR. When one PR
changes a function, schema, or API that another PR in the session relies on,
the later PR's Standards reviewer checks the two against each other.

Take one PR at a time, in the order they finish verification, and carry it
through triage and submission before showing the next. Other PRs keep reviewing
and verifying in the background; about other PRs, send only short progress
notes, never findings or questions.

Some hosts, such as Codex, don't resume you when a background agent finishes.
There, carry every PR through verification before asking the first triage
question.
