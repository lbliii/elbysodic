# Wanted To Scene Relationship Contract

Status: gated follow-up; relationship contract required before implementation
Owner: Product, service, storage, web, privacy, and tests
Created: 2026-05-15
Last updated: 2026-05-15
Review by: 2026-06-12
Closure criteria: wanted hooks can be explicitly attached to scenes through a
tenant-aware service-owned relationship with privacy/rendered proof, or this is
archived as superseded by plotting-room source links.

## Context

The scene context reader now surfaces plotting rooms that are explicitly
threaded into a scene. Some plotting rooms come from wanted hooks, so those
links already appear indirectly as `Wanted hook source` when a participant can
see the room.

This plan covers the separate question: should a scene directly know which
wanted hook it is fulfilling, beyond plotting-room source data?

Archive reference:
`plans/archive/2026/scene-context-reader-saga-2026-05-15.md`.

## Gate

Stop and ask before implementation. Direct wanted-to-scene links create a new
public/product relationship and may require schema, Studio controls, and
Blueprint/export decisions.

Questions to settle first:

- Is a wanted hook attached to a scene, a thread participant, a plotting room,
  a reserve, an application, or a character?
- Who can attach/detach the relationship: hook creator, staff, director,
  accepted applicant, or scene starter?
- What should non-participants see for reserved, filled, archived, or staff-only
  wanted hooks?
- Does the link become public discovery evidence or member-only context?
- Should this remain entirely mediated through plotting rooms for now?

## Proposed Slice

1. Define a narrow relationship model only after the ownership question is
   answered.
2. Add repository/service APIs that validate `community_id`, hook status,
   membership/character ownership, and scene visibility.
3. Extend `SceneStoryLink` with direct wanted links only when the service has
   proven visibility.
4. Render direct wanted links in `Linked story objects` without exposing
   applicant notes, staff notes, or private plotting context.

## Required Proof

- Tenant-boundary tests for wanted hook, scene, membership, and character.
- Rendered privacy tests for public visitor, ordinary member, hook creator,
  scene participant, staff, and same-user-different-community attempts.
- Tests for archived/reserved/filled hooks.
- Changelog and docs updates if the relationship becomes user-facing.

## Not Now

- Inferring wanted links from matching facets, title text, or character names.
- Displaying wanted interest notes or staff notes in scene context.
- Treating a direct wanted link as reviewed canon.
