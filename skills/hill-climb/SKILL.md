---
name: hill-climb
description: Use when asked to hill climb work against an eval.
---

# Hill-climb

Improve work in rounds against an eval until it meets an agreed target or stops
gaining.

## Agree first

Before round 0, agree these terms with the user:

- The eval. A measurement is a command that prints a number, such as p99 latency
  or tests passed; say whether lower or higher is better. A graded review uses a
  full written rubric.
- The target, such as "9.5 or higher from both reviewers on every criterion".
- The guardrails that must not regress, and the regression check that tests
  them.
- The stall count: rounds in a row without a gain that end a pass. Default 2.
- The round cap per pass, not counting round 0. Default 6.
- Where the revision log, round files, and final version go. Default
  `~/tmp/hill-climb/<task>/`. For work in a repository, the log and frozen files
  still go there, each round is a commit on the task branch, and the final
  version is the last accepted commit.

If the request sets or approves every term, log them and start. Otherwise
propose the missing ones in one message and wait.

When pass one ends, propose pass two the same way. Pass two trims the delivered
version and holds its score, and pass one's final score is its round 0. Its
target is a measure and a goal, such as "word count down to a third". A request
to only trim skips pass one. Each pass has its own round 0.

## Freeze

Before round 0, save these next to the revision log and log each sha256:

- the rubric and the reviewer brief
- each reviewer's model and effort
- the regression check
- every input that is not the work, such as reviewer sources, tests, or fixtures
- the commands for a measurement, the pass two measure, or UI renders

Confirm the sha256s before each round. Only two changes are allowed, and each
needs its new sha256 logged:

- You may add regression cases. A new case may fail on the last accepted
  version, and the next accepted round must pass it. Regression cases never
  count toward a measurement.
- The user may add a requirement. For a graded review, it becomes a new
  criterion logged as theirs. For a measurement, stop and agree with the user
  how to check it. Then rescore the last accepted version as the pass's new
  round 0, keeping the round and stall counts.

Stop and report any other change.

## Each round

Round 0 scores the starting work unchanged and becomes the first accepted
version. If its regression check fails or it can't be scored, stop and report.

1. Start from the last accepted version. Fix a known factual or calculation
   error in a round of its own, even when no reviewer saw it or it costs score,
   and add a regression case that fails on the last accepted version. Otherwise,
   address every reason and blocker logged since the last accepted version that
   still applies.
2. Run the regression check. If it fails, fix the work and run it once more. If
   it still fails, log the round as rejected and start the next one.
3. Save the exact files to score in a round folder, or commit them, and log each
   file's sha256 and any commit.
4. Score it.
   - Measurement: run the command three times. A run is valid when it exits
     cleanly and prints one number. The result is the median. The spread is the
     gap between round 0's highest and lowest runs. With fewer than three valid
     runs, the round is unscored.
   - Graded review: start two fresh reviewers, one Claude and one Codex, as the
     user-level Multi-agent work section says. Give both the frozen brief, the
     file path and sha256, the frozen inputs, and the rubric, and nothing else.
     For UI, add fresh renders at 1440px and 390px wide. Ask each to confirm the
     sha256, give a strict score and reason per criterion, and quote each
     blocker or say "none".
   - A review is valid when it has all of that. Replace an invalid reviewer
     once, and use the first valid review from each. If the replacement also
     fails, the round is unscored.
5. Log the round:
   - the pass and round number, the changes, the sha256, and the regression
     output
   - each reviewer's scores, reasons, and blockers exactly as given, or the
     measured runs
   - the floor and total or the result, and the pass two measure
   - whether the round was accepted and why, and the stall count

## Accepting a round

For a graded review, the floor is the lowest score any reviewer gave on any
criterion, and the total is the sum of all scores. A blocker is new when this
round's changes caused it. Decide that from the diff against the last accepted
version, and log the lines you relied on. A blocker a reviewer quoted on the
last accepted version is not new.

A round is accepted only when it was scored, the regression check passes, no new
blocker appears, and it has one of these:

- A gain over the last accepted version.
  - Graded, pass one: the floor rises, or holds while the total rises by 2 or
    more. No criterion's lowest score drops.
  - Measurement, pass one: the result beats the last accepted result by more
    than the spread.
  - Pass two: the measure moves toward its goal and the score holds. For a
    graded review, each criterion's lowest score stays at or above its score in
    the pass's round 0. A measurement stays within the spread of its round 0
    result, or better.
- An error fix, proved by its new regression case.
- A blocker fix: it clears a logged blocker that no reviewer raises again, and
  no criterion's lowest score drops.

An accepted round becomes the accepted version. An accepted gain resets the
stall count. Any other round adds one, fix and unscored rounds included.

## Stop

End a pass when the target is met, at the stall count, at the round cap, or when
the next round needs a decision only the user can make or evidence you can't
get. Log which one. A stall is any stop short of the target.

At the end of each pass, confirm the last accepted version's sha256 matches the
logged one and run the current regression check on it. If the check fails,
report that as a blocker and deliver nothing. Otherwise deliver it to the agreed
place and score it once more, the same way as a round, since keeping only the
best rounds inflates the last score. The target is met only when this final
score meets it, the regression check passes, no blocker is open, and in pass
two, the score still holds. If the final score misses, report a stall with both
scores. If it can't be scored, report the target as unconfirmed.

## Report

At the end of each pass, lead with whether the target was met. Then give the
final file path and sha256, the final scores with each reviewer's reasons, the
regression output, and the revision log path. Quote every open blocker. After a
stall, also give the floor or result per round, what's left, and why it stalled.
