# Documentation and agent instructions

Apply developer-documentation-style and writing-for-agents. Review both
additions and deletions.

Flag:

- New hand-maintained copies of executable definitions when an authoritative
  source or generated reference would serve the reader.
- Claims contradicted by current code, configuration, scripts, or CI.
- Duplicated or conflicting agent rules, broken instruction imports, and
  pointers to missing or unsupported instruction locations.
- Removal of useful prerequisites, examples, troubleshooting, rationale,
  compatibility requirements, or security and operational constraints.
- Automation changes that recreate duplicated or stale documentation.

For duplication findings, identify both sources and propose a working pointer
or generated reference. Preserve task guidance that explains how to use the
system; overlap with code alone does not justify deletion.

Verify changed links, anchors, imports, and examples with safe checks within
the review's read-only boundaries. Before recommending removal of planning
material, establish whether its work is complete. Route ticket-status questions
to the Spec axis. If that axis does not run or status cannot be established,
record the evidence gap rather than recommending deletion on that basis.

Keep findings tied to the diff. Do not turn a PR review into a repository-wide
cleanup or propose unrelated tooling changes. Follow repository guidance for
tool usage and instruction layout rather than imposing EP-specific conventions.
