# UAT Protocol: Wanted Hook To Plotting Handoff

Status: reusable UAT protocol
Flow: wanted hook, prospective interest, plotting room, and scene start
Primary users: Hook Hunter, Reddit 1x1 Seeker, Active Scene Writer, Community
Director, Staff Moderator
Last updated: 2026-05-10

## Research Question

Can a writer move from a wanted hook to private plotting and then to a scene
without losing the handoff, leaking private intent, or drifting to Discord as
the real source of truth?

## Artifact Options

- wanted board
- wanted detail page
- prospective interest form
- hook owner queue
- plotting room
- ready-for-scene handoff
- linked scene page
- screenshots or clickable prototype

## Starting State

- User is browsing playable openings.
- User may have an existing face or only a prospective concept.
- Hook owner and/or staff can see interest depending on state.

## Task

Find a wanted hook that fits, raise interest safely, understand what happens
next, and follow the handoff into plotting or a scene.

## Success Criteria

- User can tell whether the hook is open, raised-hand, checking-fit, in
  plotting, reserved, ready for scene, scene started, filled, paused, passed,
  or archived.
- User can raise interest with an existing face or prospective concept.
- User knows what is public, hook-owner-visible, participant-visible, and
  staff-visible.
- Hook owner has a clear next action.
- Plotting room connects back to the wanted hook and forward to the scene.
- Public surfaces show safe movement without leaking private notes.

## What The Researcher May Explain

- Wanted hooks are story openings that should become scenes.
- Some hooks can accept prospective interest before a face is approved.

## What The Researcher Should Not Explain

- Which status means the hook is still available.
- Where private plotting moved.
- Whether other users can see interest notes.

## Observation Prompts

- What makes this hook feel available or unavailable?
- What would you need to know before raising interest?
- Who do you think sees your note?
- What do you expect the hook owner to do next?
- Where did the conversation move?
- When does this become a scene?

## Synthetic Panelists

Use:

- Hook Hunter and Reddit 1x1 Seeker
- Active Scene Writer
- Community Director
- Staff Moderator and Safety-Boundary Writer

Optional adversarial lenses:

- Discord Loyalist
- Low-Commitment 1x1 Drifter
- Private Friend-Group Operator

## Risks To Watch

- Hook looks open after it is socially unavailable.
- Compatibility fields become too heavy or dating-profile-like.
- Private interest notes leak through counts, labels, room links, or
  notifications.
- Plotting becomes a generic DM with no source-of-truth connection.
- Hook owner queue is invisible, so raised hands stall.
- Scene start does not update wanted status.

## Required Proof Candidates

- Service tests for lifecycle transitions.
- Rendered tests for hook owner, interested writer, ordinary member,
  participant, staff, director, outsider, and cross-community states.
- Browser QA for wanted board, detail, interest, plotting room, and scene
  handoff.
- Copy review for lifecycle labels and compatibility fields.
