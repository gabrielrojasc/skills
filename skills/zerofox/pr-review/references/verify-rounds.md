# Further verification rounds

Revised drafts and new findings go through the next round, with the same inputs
and limits as in Verify. An agent never verifies a draft it wrote or revised.
After each round that leaves drafts unconfirmed, a fresh read-only progress
agent reads the round files so far and decides whether another round can make
progress. It doesn't judge the findings. It stops the loop when objections
repeat without new evidence, revisions cycle between equivalent drafts, or
resolution needs evidence or a decision outside the review.

When the loop stops, keep every draft whose concern a verifier accepted, through
a `confirmed` or `revise` verdict, unless a later verifier refuted it. If its
wording or anchor is still unsettled, keep the latest draft, mark it
`wording unsettled`, and record the sticking point; it counts as confirmed.
Drop a draft as "unverified, dropped", with its sticking point and the progress
agent's reason, only when no verifier accepted its concern or the latest verdict
refuted it.
