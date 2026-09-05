# Thread Scene Media Contract


## Archival Note

Lifecycle: Deferred

Archived 2026-08-17 as not-now. Do not implement until schema, editor, and Blueprint surface are accepted on GitHub design issues.

Status: gated follow-up; do not implement until a human accepts the schema,
editor, and Blueprint surface
Owner: Product design, storage, service, web, Blueprint, privacy, and tests
Created: 2026-05-15
Last updated: 2026-05-15
Review by: 2026-06-12
Closure criteria: either thread-specific scene media is implemented through a
tenant-aware schema/repository/service/editor/Blueprint slice with privacy and
browser proof, or the product decides inherited location/event media is enough
and this plan is archived as not-now.

## Context

The archived scene context reader saga delivered no-schema inherited scene
media from visible board/location images. It deliberately deferred
thread-specific media because that crosses data model, editor, Blueprint,
import/export, privacy, and theme-safety boundaries.

Archive reference:
`plans/archive/2026/scene-context-reader-saga-2026-05-15.md`.

## Gate

Stop and ask before implementation. This plan changes schema and public editing
surface area.

Questions to settle first:

- Are thread-level media fields needed for alpha, or is inherited location media
  sufficient?
- Which directors can set scene media, and which writers can see it?
- Does thread media become part of Program Blueprint import/export?
- Which values are stored: `image_url`, `image_alt`, `image_focal_point`,
  `image_overlay`, `image_source_kind`, or a narrower set?
- Are external image URLs allowed, or only uploaded/seeded/static assets?

## Proposed Slice

1. Add explicit thread media fields through migration/schema/repository rows.
2. Add service-owned `SceneMediaBand` selection precedence:
   thread media, visible current event media if accepted, then visible board
   or parent board media.
3. Add staff/director scene editor controls with safe inputs only.
4. Update Program Blueprint parser/hydration/export only if media becomes a
   Blueprint contract.
5. Add seeded examples only after privacy and crop behavior are tested.

## Required Proof

- Repository tests for tenant-scoped thread media reads and writes.
- Migration tests for existing DBs.
- Service tests for media precedence and private board/event suppression.
- Rendered tests for staff/editor visibility and ordinary member/public
  visibility.
- Browser QA for desktop/mobile hero crop, alt text, no horizontal overflow,
  and text contrast.
- Changelog fragment and docs updates if director controls ship.

## Not Now

- Raw CSS, HTML, scripts, external fonts, arbitrary layout controls, or
  unreviewed theme overrides.
- Carousel behavior.
- AI-generated scene media workflow.
