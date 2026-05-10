# UAT

Use `uat/` for task-based evaluation of Elbysodic product flows.

This folder has two tracks:

- `simulated/`: synthetic users attempting concrete tasks against routes,
  screenshots, copy, plans, or prototypes.
- `observed/`: consent-safe observations from real users attempting concrete
  tasks.

Simulated UAT is useful for finding likely friction early. Observed UAT is what
validates or corrects those assumptions.

## Directory Map

```text
research/uat/
  README.md
  protocols/
  simulated/
  observed/
```

## What Counts As A Task

Good UAT tasks are concrete:

- Find whether this realm is accepting new faces.
- Start a first-face application from a wanted hook.
- Reply to the scene as the right face.
- Raise interest in a wanted hook without leaking private notes.
- Review an application and send an applicant-visible revision request.
- Check what blocks launch.

Weak tasks are broad preferences:

- Do you like this page?
- What features do you want?
- Is this modern?

## Required Fields

Every UAT note should include:

- task
- artifact inspected
- user or synthetic panelist
- starting state
- expected path
- actual or simulated path
- failure points
- trust concerns
- recommended changes
- required proof
- confidence

## Promotion

Use UAT findings to update:

- `docs/product/` for accepted UX doctrine or vocabulary.
- `plans/` for sequenced work.
- `tests/` for privacy, identity, rendered state, and journey proof.
- `research/synthesis/` for cross-session patterns.
