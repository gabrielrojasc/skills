---
name: linear-work-structure
description: Structures Linear work. Use when planning levels or tickets.
---

# Linear work structure

Choose the smallest Linear level that gives the work the ownership, visibility,
and dependency tracking it needs. Produce a proposal first. Do not create or
update Linear work without explicit user approval.

## Choose the level

Start with the outcome, then apply these tests. Choose the level from the item's
role, not its current title. Improve a vague title instead of promoting the item
to a higher level.

- **Initiative:** a broader objective served by multiple independently managed
  projects. Use it to explain why those projects belong together.
- **Project:** a coordinated body of issues with one clear terminal outcome and
  a bounded lifecycle. The outcome may be a shipped change or a decision.
- **Milestone:** a meaningful stage within one project's outcome, such as an
  internal release or public launch. Use milestones for delivery checkpoints,
  not to hide separate discovery and implementation projects. A milestone does
  not replace dependency links.
- **Issue:** an independently assignable unit with a verifiable completion
  condition. Use issue relations for real blockers.
- **Sub-issue:** a contained part of a parent issue, including work too large for
  one issue but too small for a project or pieces split across teammates. The
  parent remains the useful planning unit. Promote a child to an issue when it
  needs independent design, prioritization, dependencies outside the parent, or
  a lifecycle of its own.

Use labels or views for cross-cutting categories. Do not create a new project
only to group work by discipline, component, or team.

## Separate discovery from implementation

Create a discovery project when its terminal output is a go, change, or stop
decision and implementation is not yet approved. Put experiments and comparisons
inside that project as issues. End with an issue that records the decision and
supporting evidence.

Create a separate implementation project only after the decision authorizes it.
Its terminal output is working behavior. Keep discovery and implementation in
separate projects; milestones record delivery checkpoints within either project.

Alternative approaches belong as discovery issues while they are being compared.
After selection, each approach pursued toward working behavior gets its own
implementation project.

## Record dependencies

Use `blocked by` only for a prerequisite that prevents work from starting or
finishing. Do not encode preference or ordinary ordering as a blocker. Use
project dependencies when one whole project gates another. The unblocked issues
form the executable frontier.

Classify every executable unit as an issue or sub-issue. When the user invokes
`to-tickets`, let it draft vertical slices and blocking edges, then apply this
skill's issue and sub-issue tests to place each slice. This skill owns that
placement and the surrounding Linear levels. `to-tickets` must preserve the
approved parent and sub-issue hierarchy when publishing tickets.

## Produce the proposal

Show the proposed structure as a tree. Include initiatives, projects,
milestones, issues, and sub-issues when the proposal uses them. Annotate every
project with its terminal output and every real dependency inline. For example:

```text
Initiative: Improve account setup
├── Project: Validate guided setup [output: go, change, or stop decision]
│   ├── Issue: Define success measures
│   ├── Issue: Test the guided setup
│   └── Issue: Record the recommendation [blocked by: test]
└── Project: Ship guided setup [output: working customer behavior]
    ├── Milestone: Internal release
    │   ├── Issue: Implement guided setup
    │   │   ├── Sub-issue: Add completion-state persistence
    │   │   └── Sub-issue: Instrument setup completion
    │   └── Issue: Run internal release [blocked by: implement guided setup]
    └── Milestone: Public release
        └── Issue: Release guided setup [blocked by: run internal release]
```

For an existing Linear structure, show `current -> proposed` for every move and
name the decision rule that requires it. State uncertain ownership, scope, or
outcomes instead of inventing them.

## Completion criteria

- Every proposed item has exactly one level and a reason for that level.
- Each project names one terminal output.
- Discovery and implementation use separate projects.
- Every executable unit is classified as an issue or sub-issue, and every
  sub-issue appears beneath its parent.
- Milestones describe stages within a project rather than hidden project
  boundaries.
- Blocking relationships represent actual prerequisites.
- The proposal is reviewable without changing Linear.
