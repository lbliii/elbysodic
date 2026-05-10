# UAT Protocol: First-Face Onboarding

Status: reusable UAT protocol
Flow: account, membership, first face, application, claim, and reserve
Primary users: Invited/New Face Applicant, Active Scene Writer, Staff
Moderator, Safety-Boundary Writer
Last updated: 2026-05-10

## Research Question

Can a new writer move from access to a first face without confusing account,
membership, public character identity, application status, claims, or reserves?

## Artifact Options

- invite acceptance route
- request-access flow
- first-face setup page
- application form
- claims/reserves page
- accepted-face handoff screen
- screenshots or clickable prototype

## Starting State

- User has accepted an invite or received access.
- User has a global account and a community membership.
- User has no public face in this community yet.

## Task

Create or apply with a first face, understand what is public or private, and
find the next writing move after acceptance.

## Success Criteria

- User can distinguish account, membership, face, application, claim, and
  reserve.
- User can tell what staff sees, what other members see, and what remains
  private.
- User can identify required fields and optional character material.
- User can understand application state after submit: draft, submitted, needs
  revision, accepted, declined, withdrawn.
- Accepted user reaches a character hub, wanted hook, plotting room, or first
  scene path.

## What The Researcher May Explain

- A face is the public posting identity inside one community.
- Staff may review applications before a face becomes playable.

## What The Researcher Should Not Explain

- Which fields are required.
- Which notes are staff-only.
- What the next step is after acceptance.

## Observation Prompts

- What identity are you creating right now?
- Who do you think can see this text?
- What happens when you submit?
- What would make you worry about privacy here?
- How do you know whether the face claim or reserve is available?
- Once accepted, where would you go to start writing?

## Synthetic Panelists

Use:

- Invited/New Face Applicant
- Active Scene Writer
- Staff Moderator and Safety-Boundary Writer
- Community Director

Optional adversarial lenses:

- Low-Commitment 1x1 Drifter
- Accessibility-First Writer
- Alpha Breaker

## Risks To Watch

- Account identity, membership identity, and face identity blur together.
- Staff-only notes and applicant-visible requests share one visual treatment.
- Reserve/claim conflict or expiry is unclear.
- Application status exists only as a transient toast.
- Acceptance dead-ends without a first writing move.
- Same-user-different-community state leaks or confuses default face.

## Required Proof Candidates

- Service tests for membership ownership and character authorship.
- Rendered tests for applicant, member, staff, director, outsider, and
  same-user-different-community states.
- Browser QA for mobile application drafting and accepted-face handoff.
- Copy review for `face`, `application`, `claims`, `reserves`, and `wanted`.
