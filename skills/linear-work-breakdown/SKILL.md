---
name: linear-work-breakdown
description: Structures Linear work. Use when planning levels or tickets.
---

# Linear work breakdown

Place work in the right Linear layer, from initiative to sub-issue, and create
it the way the team expects. An organization's documented Linear conventions
override these defaults.

## When to use

- Choosing the layer for new work: initiative, sub-initiative, project,
  milestone, issue, or sub-issue.
- Turning an accepted proposal into Linear structure.
- Deciding where a bug or sustaining item goes.
- Reviewing an existing structure.

## When not to use

- Linking branches and pull requests to issues. Use `linear-gh-linking`.
- Work tracked outside Linear.

## Propose the full structure

Propose the hierarchy the work needs, including initiatives and sub-initiatives,
with your reasoning. Some choices need sign-off from whoever owns product and
planning decisions: whether an initiative or sub-initiative exists, whether a
project is communicable, its outcome, and its priority. Mark those as pending
that sign-off so the user can settle them with the owner, and don't record them
as final until the owner agrees. Don't create or change Linear work without
explicit user approval.

## Layers

- **Initiative:** a high-level goal that groups projects, such as "halve billing
  support tickets this quarter".
- **Sub-initiative:** groups projects that share a domain, product, or mission
  under one outcome. Nothing ships as the sub-initiative itself; if it could
  ship on its own, it is a project. It may sit under more than one initiative.
- **Project:** shippable on its own, with a clear goal and a target date. See
  the boundary test below.
- **Milestone:** a stage of one project, seeded by the project's template when
  it has one.
- **Issue:** the base ticket, clear enough for the assignee to do the work and
  for teammates to know what is happening.
- **Sub-issue:** an atomic, independently executable piece of its issue.

Improve a vague title instead of promoting the work to a higher layer. A project
doesn't need an initiative.

## The project boundary is the release

Ask "would this be announced or released separately, or bundled with the rest?",
not "could engineering build it on its own?" Independently buildable features
that reach users together are one project, with each feature as an issue. Two
approaches to one goal that ship at different times are separate projects. An
issue with its own user-facing outcome becomes a project.

Discovery and investigation are a milestone inside the project, not a separate
project.

## Communicable or not

A project is communicable when users would notice the change, or when whoever
supports them needs training or communication to handle it. Otherwise it is
non-communicable, such as a language version upgrade. Communicable projects need
release communication, such as release notes or an announcement;
non-communicable projects still get an outcome, a target date, and milestones,
but no release communication. The product owner makes the call; say which way
you lean and why.

## Create from templates

- Use the team's project and issue templates when they exist. If none fits, say
  so.
- New issues go to the team's triage inbox. If the issue belongs to a project,
  set the project and the milestone it belongs to, except for bugs, which follow
  "Sustaining work and bugs" below.
- Labels come from the template. Don't add others unless asked.

## Milestones

- Keep the template's stages and add one only when the project needs it. Delete
  stages the project won't use instead of leaving them empty.
- Give every milestone a target date.
- A project issue sits in one milestone and doesn't move between milestones.
  Standalone team issues have none.
- A project can't pass a milestone until that milestone's issues are done.

## Before In Development

A project needs a target date and an agreed outcome before it moves to In
Development, In Progress, or the team's equivalent status. Check for both. If
one is missing, propose it and mark it pending the owner's agreement.

## Sustaining work and bugs

- Sustaining work and tech debt are standalone team issues that go through
  triage. Make a project only when the work is project-sized.
- A bug goes into a project, in the milestone where it was found, only when it
  belongs to that active project and blocks its release. Otherwise it stays a
  team issue through triage, even if it loosely relates to a sub-initiative.

## Record dependencies

Use `blocked by` only for a prerequisite that prevents work from starting or
finishing. Don't encode preference or ordinary ordering as a blocker. Use
project dependencies when one whole project gates another. The unblocked issues
form the executable frontier.

When the user invokes `to-tickets`, let it draft vertical slices and blocking
edges, then apply this skill's issue and sub-issue tests to place each slice.
This skill owns that placement and the surrounding Linear levels. `to-tickets`
must preserve the approved parent and sub-issue hierarchy when publishing
tickets.

## Output

A proposed tree, with each project marked communicable or not and each choice
pending sign-off named with its owner:

```text
Sub-initiative: Guided setup: halve time to first working account
├── Project: Guided setup wizard [proposed: communicable]
│   ├── Milestone: Discovery / Investigation
│   │   └── Issue: Test the guided setup with five users
│   ├── Milestone: Development
│   │   └── Issue: Implement guided setup
│   │       ├── Sub-issue: Add completion-state persistence
│   │       └── Sub-issue: Instrument setup completion
│   └── Milestone: Release
│       └── Issue: Release guided setup [blocked by: implement guided setup]
└── Project: Setup progress emails [proposed: communicable]
Pending sign-off: sub-initiative, communicability, and outcomes (product owner),
  project and milestone target dates (engineering lead with product owner)
```

For an existing structure, show `current -> proposed` for every move and name
the rule that requires it. State uncertain ownership, scope, or outcomes instead
of inventing them.
