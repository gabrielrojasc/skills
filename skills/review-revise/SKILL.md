---
name: review-revise
description: Use when adversarial review loops are requested.
---

# Review-revise

Have independent reviewers attack a piece of work, such as code, prose, or a
plan, and revise it until no reviewer has a material objection or the loop
stalls. A skill that runs this loop, such as `cross-review`, may set the
reviewer, the budget, and additions to the brief.

## Set up

Name the target, its requirements, and what you may edit. A review-only request
lets you revise your assessment or proposed patch, not the work itself. Use one
reviewer and no round limit unless the user or the calling skill sets them, and
state both before the first round.

## Review

Start read-only subagents that don't edit, publish, or start subagents. Give
each the target at an exact revision, its requirements and constraints, the
source locations, and one assignment. With several reviewers, split the
concerns so together they cover the target. If you can't start a subagent,
report that; reviewing your own work doesn't count.

Adapt this brief:

> Find material reasons this work fails its requirements. Check assumptions,
> edge cases, and needless complexity against the source. Return each
> objection with its location, consequence, evidence or counterexample, and the
> smallest correction that fixes it. Keep evidence gaps apart from shown
> defects. Report `No material objection` if none remain. You don't need to
> find a problem, and a preference isn't a defect.

## Adjudicate

Check every objection against the evidence and merge duplicates. Fix the
supported ones within scope, and reject the rest with a concrete reason. Settle
disagreements with a source check or a small experiment, not by vote. Keep a
record in the conversation of each objection, its outcome, the revision, and
its check. If an objection needs authority or a decision you don't have, finish
the rest and report it.

## Next round

Run the checks each revision needs. Send every reviewer whose assignment the
revision touches the new revision, the changes, the check results, and your
reason for each rejection, and ask it to confirm the outcomes and look for
regressions. A round is one review and your response to it; parallel reviewers
share a round.

## Stop

Finish when every reviewer returns `No material objection` on the current
revision and the checks pass. Otherwise, after each round, check your record
for a stall: an objection repeats without new evidence, revisions cycle between
equivalent versions, or progress needs evidence or a decision you can't get.
Keep going while another round has a concrete way to settle an objection; a
high round count alone isn't a reason to stop. A stall, a spent budget, a
missing reviewer, or an open disagreement isn't a clean result.

## Report

Report the changes, the checks, the reviewer count, the rounds, and any open
objections or unverified changes. After a stall, write "Stopped after <N>
rounds because <reason>" and what would let the loop continue.
