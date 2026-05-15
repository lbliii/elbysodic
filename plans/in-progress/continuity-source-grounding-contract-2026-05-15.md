# Continuity Source Grounding Contract

Status: gated follow-up; blocked on Continuity Graph provenance and review
Owner: Continuity Graph, product, storage, service, web, privacy, and tests
Created: 2026-05-15
Last updated: 2026-05-15
Review by: 2026-06-19
Closure criteria: source-linked continuity/canon grounding can appear in scene
context only after manual provenance, review state, visibility, and privacy
contracts exist; otherwise this remains deferred.

## Context

The scene context reader includes a `Linked story objects` section. It now
renders explicit plotting-room links. Canon/source grounding remains deferred
because Elbysodic does not yet have the reviewed Continuity Graph contract that
would make canon labels, source citations, staff-only material, and public
visibility safe.

Archive reference:
`plans/archive/2026/scene-context-reader-saga-2026-05-15.md`.

## Gate

Stop and ask before implementation. This work touches canon, provenance,
privacy, and likely schema.

Questions to settle first:

- What is the first manual continuity primitive: scene outcome, canon entry,
  source citation, proposed beat, or reviewed event?
- Which states exist: proposed, reviewed, staff-only, member-visible, public?
- Who can propose, review, publish, retract, and cite continuity?
- Can a scene show canon context before the scene itself is complete?
- Which source snippets can be quoted or summarized without leaking private
  posts, staff discussion, or writer boundaries?

## Proposed Slice

1. Define the Continuity Graph manual provenance model outside the scene reader
   first.
2. Add source-linked records with explicit review and visibility state.
3. Add service-owned scene grounding only for records tied to the current scene
   and visible to the current membership.
4. Render provenance labels every time: proposed, reviewed, staff-only,
   member-visible, or public.
5. Keep generated summaries out until consent, provenance, privacy, and review
   gates are implemented.

## Required Proof

- Repository and migration tests for source records and review state.
- Service tests for visibility across public, member, involved writer, staff,
  and cross-tenant attempts.
- Rendered tests proving staff/private/source snippets do not leak.
- Docs updates to Continuity Graph, privacy matrix, and product strategy.
- Changelog fragment if any visible continuity context ships.

## Not Now

- Generated canon, auto-summaries, or automatic dialogue/source extraction.
- Canon links inferred from matching names or facets.
- Public canon surfaces before manual review exists.
