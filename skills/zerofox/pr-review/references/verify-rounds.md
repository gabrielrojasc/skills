# Further verification rounds

Revised drafts and new findings go through the next round, with the same inputs
and limits as in Verify. An agent never verifies a draft it wrote or revised.
Run at most 3 rounds per axis.

After the last round, keep every draft whose concern a verifier accepted,
through a `confirmed` or `revise` verdict, unless a later verifier refuted it.
If its wording or anchor is still unsettled, keep the latest draft, mark it
`wording unsettled`, and record the sticking point; it counts as confirmed.
Drop a draft as "unverified, dropped", with its sticking point, only when no
verifier accepted its concern or the latest verdict refuted it.
