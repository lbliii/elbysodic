# Non-AI PBP Studio Roadmap

Status: active research-backed sequencing snapshot
Owner: Product, research, web, service, storage, design, and test stewardship
Created: 2026-05-10
Last updated: 2026-05-10
Review by: 2026-05-31
Closure criteria: Split the top roadmap phases into PR-sized implementation
plans or mark them superseded by existing active plans; archive when Elbysodic
has a verified non-AI alpha path from first realm setup through daily writing,
director operations, and invite-first onboarding.

## Purpose

This roadmap answers where Elbysodic is now, where it needs to be before AI
work should matter, and how to sequence the non-AI product into a credible
modern PBP studio.

AI is intentionally parked. The research-backed product center is still the
forum-PBP backbone: faces, rosters, scene hubs, threads, posts, applications,
claims, reserves, wanted hooks, plotters, guidebooks, archives, Studio, and
community atmosphere. Rapid-touch and AI features can only work after this
backbone is stable, trusted, and visually current.

This plan sequences the strategy spine in `docs/product/strategy-spine.md`:
first harden the shared trust foundation, then prove Realm Studio and Writer
Network through a non-AI alpha loop, then defer Continuity Graph expansion until
manual provenance, rendered privacy, and transaction proof are solid.

## Research Basis

Use these as input signal:

- `research/synthesis/2014-delta-agenda.md`
- `research/synthesis/2026-wave-2-modern-pbp-delta.md`
- `research/synthesis/2026-05-10-simulated-user-panel.md`
- `docs/product/roleplay-ecosystem-research.md`
- `docs/product/user-personas-panel.md`
- `docs/product/appearance-studio.md`
- `docs/product/mission.md`

Current conclusion:

Modern roleplay is fragmented, not dead. Elbysodic should not position itself
as the only roleplay tool. It should position itself as the PBP-native
source-of-truth studio for running a durable writing community, with a modern
design bar and controlled escape hatches later.

Strategy doctrine:

- `docs/product/strategy-spine.md`

## Current State

### What Is Already Real

The codebase already has substantial non-AI backbone:

- Tenant-aware SQLite schema with explicit `community_id` across core rows.
- Global users, community-local memberships, roles, sessions, and default
  faces.
- Character-authored posts with membership ownership.
- Boards, child boards, threads, posts, revisions, safe markup, composer draft
  behavior, read state, watches, mentions, notifications, and first-unread
  navigation.
- Applications, application review rooms, claim types, claim values, reserves,
  wanted hooks, prospective wanted interest, character plot hooks, plotting
  rooms, and plotting-room-to-scene handoff.
- World materials for premise, rules, events, factions, and application
  guidance.
- Director-defined facets across characters, boards, threads, materials, and
  wanted hooks.
- Studio surfaces for operations, launch readiness, board editing, intake,
  Blueprint dry-run preview, theme tokens, post style policy, and navigation.
- Public/network shell, tenant-prefixed routes, request-access placeholder,
  production auth/session/CSRF scaffolding, development persona tools, and
  first-realm bootstrap CLI.
- Safe Appearance Studio direction through theme tokens, media slots, health
  warnings, and disallowed raw CSS/script/template boundaries.

Proof already exists in roughly 244 collected test functions across web slice,
security, tenant repository, Blueprint, policy, CLI, domain, and markup tests.

### What Is Not Yet Solid Enough

The product is not yet alpha-solid because the core loop is broader than the
hardening proof:

- Live Railway smoke and production operations proof are still plan-level
  gates.
- Public catalog/search needs a service-owned read model and signed-out privacy
  proof.
- Rendered privacy matrix still has gaps for applications, plotting,
  notifications/counts, claims/reserves, Studio, and responsive surfaces.
- Request access is still a placeholder; invitation lifecycle is not real yet.
- First-face onboarding exists in pieces but is not a complete invited-writer
  journey.
- First realm setup has a CLI path, but guided builder writes, launch status,
  and invite-first opening are still future slices.
- Program Blueprint apply remains correctly gated behind diff, transaction,
  rollback, collision, and tenant proof.
- Studio has many surfaces, but director operations need daily workflow polish.
- The visual bar has been raised by RPHub-style modernity; defaults must feel
  contemporary before directors customize anything.
- Rapid-touch formats are not yet modeled and should wait until the backbone
  can absorb them without fragmenting continuity.

## Target State: Non-AI Alpha

Elbysodic is ready for a serious non-AI alpha when one director can open and
run one realm, and invited writers can join, bring faces, find story, and write
without needing Discord, spreadsheets, or manual forum templates for core
workflow.

The alpha promise by pillar:

Realm Studio:

- A director can bootstrap or create the first realm, shape the minimum launch
  packet, invite staff/writers, and see what blocks opening.
- Staff can review applications, claims, reserves, reports/manual issues, and
  private production material without leaking staff context.

Writer Network:

- A writer can accept access, understand the realm, create or apply with a
  first face, set a default face, and reach a first scene or wanted hook.
- An active writer can enter the realm, see active face, find `needs reply`,
  `waiting`, watched, mentioned, unread, plotting, and application states, then
  reply with draft/preview confidence.
- A hook hunter can move from wanted or plotter interest to a plotting room and
  scene without private note leakage.

Shared trust and presentation:

- The public front door looks modern and roleplay-native, not like a dated
  forum index.
- Every sensitive rendered surface has explicit privacy proof or a documented
  not-now boundary.

Continuity Graph:

- Source-linked canon remains deliberately not-now for alpha except where
  existing scene/thread/material primitives need to preserve future compatibility.

## Roadmap

### Phase 0: Plan Hygiene And Production Truth

Goal: stop building on stale assumptions.

Deliverables:

- Reconcile active plan statuses with the current codebase, especially where
  progress logs say work started or landed.
- Archive plans that are implemented and only waiting for a final note.
- Keep this roadmap as the product sequencing layer; keep implementation
  details in narrower plans.
- Run and record the local gate before any alpha-facing milestone claim.

Existing plans:

- `plans/in-progress/production-readiness-roadmap-2026-05-09.md`
- `plans/in-progress/post-pr31-priority-roadmap-2026-05-10.md`

Proof:

- Updated `plans/README.md`.
- Local gate or explicit skipped-check note.

### Phase 1: Production Trust Gate

Goal: make the current app trustworthy before expanding product surface.

Deliverables:

- Recorded Railway/staging smoke.
- Storage persistence proof for director-edited rows across restart.
- Fresh-vs-upgraded schema/index parity kept green.
- Backup and restore drill for SQLite.
- Release-smoke script covering login, tenant route, active face, write,
  notifications, Studio, and logout.
- Transaction boundaries for high-risk multi-write workflows.

Existing plans:

- `plans/in-progress/production-readiness-roadmap-2026-05-09.md`
- `plans/in-progress/railway-auth-hardening-2026-05-02.md`
- `plans/in-progress/tenant-routing-and-shell-release-2026-05-02.md`

Proof:

- `uv run pytest tests/test_web_security.py tests/test_tenant_repository.py -q --tb=short`
- Recorded Railway smoke note.
- File-backed persistence tests.

### Phase 2: Privacy And Identity Closure

Goal: prove the PBP trust model through rendered pages.

Deliverables:

- Rendered privacy matrix updated to `covered`, `partial`, or `missing` for
  every route family.
- Close first gaps for applications, plotting rooms, notifications/counts,
  claims/reserves, shell/sidebar counts, and faceless states.
- Ensure wrong-face prevention, active-face visibility, no-face states, and
  same-user-different-community recovery are consistently rendered.
- Keep staff power capability-scoped through `CommunityMembership`.

Existing docs/plans:

- `docs/architecture/rendered-route-privacy-matrix.md`
- `docs/product/user-personas-panel.md`
- `plans/in-progress/production-readiness-roadmap-2026-05-09.md`

Proof:

- Focused rendered tests in `tests/test_forum_slice.py`.
- Security tests for production route and POST boundaries.
- Browser QA for any responsive shell/sidebar count changes.

### Phase 3: Director Opening And Invite-First Onboarding

Goal: make opening one real realm possible without hand-editing data.

Deliverables:

- First realm setup path finalized: CLI now, Studio setup later only with a
  clear authority model.
- Guided Realm Builder minimum writes for realm identity, first scene hub,
  required director materials, intake posture, and launch checklist.
- Persisted launch status: backstage, invite-only, public preview.
- Real invitation lifecycle: create, accept, expire, revoke, replay denial.
- First-face handoff after invite acceptance.

Existing plans:

- `plans/in-progress/first-realm-setup-2026-05-10.md`
- `plans/in-progress/community-creator-onboarding-2026-05-10.md`

Proof:

- CLI/service tests for first realm and rollback.
- Invite lifecycle repository/service tests.
- Rendered tests for no-realm, empty configured realm, director, signed-out,
  invited writer, replay, and no-face states.

### Phase 4: Daily Writer Loop

Goal: make the ordinary writing session excellent.

Deliverables:

- Writer Desk and My Threads agree on obligations: `needs reply`, `waiting`,
  `caught up`, `watching`, mentions, unread, plotting, applications.
- Composer start/reply/edit flow is stable on desktop and mobile: active face,
  preview, safe markup, draft restore, selected cast, and wrong-face
  prevention.
- Thread and board cards carry first-unread, latest, next-unread, cast, status,
  and active-face relevance without visual overload.
- No-face writer states route cleanly to character/application setup.

Existing docs/plans:

- `docs/product/user-personas-panel.md`
- `docs/product/information-hierarchy.md`
- `docs/product/paragraph-rhythm.md`
- `plans/in-progress/production-readiness-roadmap-2026-05-09.md`

Proof:

- Rendered tests for writer desk, board, thread, composer, notifications, and
  character hub.
- Browser QA at mobile and desktop widths for one active scene and one empty
  roster path.

### Phase 5: Board-Running Backbone

Goal: make the old forum labor native.

Deliverables:

- Application and claims review queue that connects applicant state, claim
  conflicts, reserves, revision requests, staff notes, and acceptance.
- Wanted lifecycle: open, interested, reserved, plotting, ready for scene,
  scene started, filled, archived.
- Plotting room handoff from interest to scene with clear participants,
  privacy, next step, and notification behavior.
- Studio Operations organized around attention needed, not tables.
- Claims/reserves/intake configuration exposed through Studio without unsafe
  public self-registration.

Existing plans:

- `plans/in-progress/studio-production-workflows-2026-05-02.md`
- `plans/in-progress/wanted-backstage-handoff-2026-05-09.md`
- `plans/in-progress/community-creator-onboarding-2026-05-10.md`

Proof:

- Service tests for lifecycle transitions.
- Rendered privacy tests for owner, interested writer, ordinary member, staff,
  director, outsider, and cross-tenant states.
- Browser QA for casting/wanted/applications/Studio operations.

### Phase 6: Modern Public Face And Appearance Defaults

Goal: raise the design bar before alpha users decide the product is dated.

Deliverables:

- `/` and `/network` split into platform home and Explore/catalog with a
  service-owned public read model.
- Public realm cards expose premise, activity, public media, wanted pressure,
  and request/invite posture without membership or staff leakage.
- Default seeded realms demonstrate contemporary visual quality, strong media,
  mobile-conscious layouts, and dense-but-calm information hierarchy.
- Appearance Studio V1 focuses on safe token editing, health warnings, media
  slots, and a small number of ritual-surface variants.
- RPHub-level modernity is treated as a minimum bar, not a style reference to
  copy.

Existing docs/plans:

- `docs/product/appearance-studio.md`
- `plans/in-progress/studio-network-homepage-2026-05-03.md`
- `plans/in-progress/appearance-studio-roadmap-2026-05-01.md`

Proof:

- Signed-out and signed-in public catalog tests.
- Browser screenshots for `/`, `/network`, a realm gateway, board, thread,
  wanted detail, application page, and Studio at mobile and desktop widths.
- Accessibility/readability warnings for theme health.

### Phase 7: Portability And Alpha Operations

Goal: make real communities trust their writing archive.

Deliverables:

- Backup/export guidance that a director can actually follow.
- Snapshot and restore drill documented from staging.
- Minimum content export format for community, boards, threads, posts,
  characters, applications, claims, wanted hooks, materials, and plotting
  rooms.
- Operator runbook for demo/staging/production posture.
- Alpha feedback protocol connected to `research/interviews/` and
  `research/outreach/`.

Existing plans:

- `plans/in-progress/production-readiness-roadmap-2026-05-09.md`
- `research/outreach/README.md`
- `research/interviews/README.md`

Proof:

- Restore drill note.
- Export smoke test or documented manual export prototype.
- Alpha checklist and consent-safe feedback protocol.

### Phase 8: Rapid-Touch Escape Hatches

Goal: support lite rapid play without breaking the source of truth.

Do this only after Phases 1-6 are materially solid.

Candidate deliverables:

- Scene subtype model for `long-form scene`, `IC text`, `IC call transcript`,
  `micro-scene`, `OOC plotting`, and `external Discord reference`.
- Clear canon level: canon, pending, non-canon, OOC, atmosphere.
- Thread/scene UI that keeps rapid-touch content tied to face, participants,
  privacy, and archive behavior.
- Import/link affordances for Discord or chatbox transcripts before building
  full chat parity.

Proof:

- Product spec and rendered prototype before schema work.
- Privacy tests for participant-only rapid-touch records.
- User panel review with Rapid-Touch Writer, Active Scene Writer, Safety
  Writer, and Director lenses.

## Explicitly Parked Until Non-AI Backbone Holds

AI Studio remains a strong opportunity, but it should not lead the roadmap.
Before implementing AI moderation, NPCs, chaos prompts, generated media, or
continuity assistance, Elbysodic needs:

- stable community/face/thread/wanted/application/Studio context
- strong privacy and provenance rules
- clear canon/pending/non-canon states
- opt-in controls
- human acceptance workflows

Reference only: `docs/product/ai-studio.md`.

## Immediate PR Queue

1. Plan hygiene: update/close active plans whose progress logs are stale.
2. Public catalog read model: service-owned `/network` cards and signed-out
   privacy proof.
3. Privacy matrix pass: close one route-family gap at a time, starting with
   applications or plotting rooms.
4. Invitation lifecycle: director-created invites through first-face handoff.
5. Guided Realm Builder minimum writes: scene hub plus director materials.
6. Studio Operations polish: attention-needed lanes for application, claims,
   wanted, reserves, and launch readiness.
7. Modern design QA pass: screenshots and issue list for the public home,
   realm gateway, board, thread, wanted, applications, and Studio.
8. Backup/restore drill and alpha operations notes.

## Not Now

- AI features.
- Public self-serve creator onboarding.
- Billing, custom domains, or hosted multi-tenant admin console.
- Generic Discord replacement.
- Raw CSS skins, arbitrary templates, external font URLs, or per-community
  JavaScript.
- Broad marketplace discovery before invite-first onboarding and catalog
  privacy are solid.
- Rapid-touch posting until long-form scene continuity is stable.
