# Static Community Landing V2 Notes

Status: design artifact
Date: 2026-05-15
Artifact: `design/static-community-landing-v2-mock.html`
Concrete target: `/c/x-men-apocalypse`

## Purpose

This prototype explores a V2 community landing page as a public realm gateway.
It applies `docs/product/experience-direction.md` and
`design/composition-bible.md` to the current X-Men seeded realm.

The second pass treats atmosphere as a programmable community layer, not a
hard-coded current-event layout. The mock includes event-state controls for:

- one active event
- no active event
- multiple active events

The design implication is that a realm gateway needs an atmosphere slot and a
realm pulse even when there is no current event. Events should intensify or
focus the page; they should not be the only way the page feels alive.

The page should answer:

- What is this realm?
- What is happening right now?
- What can I play here?
- Which wanted hooks, locations, and public scenes are active?
- What should a visitor read before applying?
- What is public, applicant-only, or member-only?

## Research And Source Inputs

Evidence mode: design synthesis and static mock, grounded in existing repo
content.

Sources inspected:

- current public route: `src/elbysodic/web/pages/page.py`
- current landing template: `src/elbysodic/web/pages/page.html`
- public preview service: `AppServices.public_studio_program()` and
  `AppServices.public_world_hub()`
- seed content in `src/elbysodic/db/seed.py`
- X-Men seed media in `src/elbysodic/web/static/seed-media/`
- `docs/product/experience-direction.md`
- `design/composition-bible.md`

The local server was not running during this pass, so the artifact is based on
templates and seed data rather than a live browser capture of
`http://localhost:8001/c/x-men-apocalypse`.

## Accepted Design Moves

- Treat `/c/{community_slug}` as a **realm gateway**, not a forum index.
- Make the current event the hero-level story pressure: `B-24 Winter`.
- Let the event state change without breaking the composition. `B-24 Winter`
  is one example of the active atmosphere source, not the page's permanent
  structure.
- Provide a no-event state where standing tensions, open scene hubs, wanted
  hooks, and public premise carry atmosphere.
- Provide a multi-event state where the gateway clarifies arcs instead of
  forcing visitors to decode a schedule or announcement thread.
- Keep the first viewport cinematic, but include immediate PBP actions:
  `Request access`, `Browse wanted`, `Reply as Rogue`, and `Read premise`.
- Preserve a hint of the next section below the hero through page rhythm rather
  than a full-screen poster page.
- Use a layered chrome model: outer rail, inner world-home shell, page-local
  sections.
- Separate audience states:
  - signed-out visitor: request access, wanted, guidebook, public scenes
  - applicant: continue application, review claims, public fit signals
  - member: active face, reply pressure, Desk continuation
- Use public-safe rows for open scenes. These show story motion without exposing
  private queues, staff load, or active-face state.
- Replace generic metrics with a realm pulse: faces in play, scene hubs under
  pressure or ready, and wanted hooks open.
- Make wanted hooks feel like story invitations rather than a single CTA.
- Show first-entry path language on wanted hooks, such as the location, scene,
  faction, or relationship pressure that can bring the wanted role into play.
- Let location cards carry strong media and atmosphere, then lead into playable
  scene hubs.
- Weight the hottest location more strongly than the rest instead of making
  every place card equal.
- Use a bento-style location field when scene hubs have different current
  importance. Event-important or high-activity places can occupy larger cells;
  quieter locations stay as smaller but still playable doors.
- Include a no-media mode to test that the layout still has identity without
  images.
- Use subtle signal motion as atmosphere, guarded by reduced-motion rules.

## Rejected Patterns

- No public staff workload, application-review counts, private room names, or
  member-only queue details.
- No generic dashboard metric grid as the page's main identity.
- No streaming clone: cinematic media supports writing actions and public realm
  fit, not passive browsing.
- No channel model: locations are places and scene hubs, not Slack channels.
- No old forum index as the first contact surface.

## Component Candidates

- `realm_gateway_hero`: public or member-aware hero for community home.
- `realm_signal_strip`: launch/access/event/wanted/public-state badges.
- `public_playable_scene_row`: public-safe open scene preview.
- `realm_entry_path`: visitor/applicant checklist for read, fit, apply.
- `realm_location_card`: media-backed location card with public-safe scene hub
  link.
- `member_continuation_lane`: signed-in continuation card using active face and
  Desk obligations without turning public home into Desk.

## Read Model Implications

The current public page has `public_program` and `public_world_hub`, but V2
needs a stronger service-owned contract before implementation:

- public realm gateway identity
- public current event
- published premise/rules/application guide summaries
- public-safe open scene previews
- public-safe wanted hook summaries
- public-safe location cards with media and scene counts
- location emphasis fields, such as featured, hot now, event-linked, high
  activity, or director-pinned
- event state: none, one, or many active public events
- atmosphere source: event, season, premise, director pulse, or featured
  location/material
- access posture and request-access/application CTA state
- optional signed-in continuation lane from Writer Desk
- optional applicant continuation lane

The service must decide privacy, filtering, ranking, and audience copy before
the template renders. The template should not decide whether a scene, count,
wanted hook, or application state is safe to show.

## Product Questions

- Should `/c/{community_slug}` always be the realm gateway, with `/world`
  remaining the guidebook/material room?
- Which public scene rows should qualify for the gateway: active only, open
  only, recently updated, or director-featured?
- Should wanted hooks rank by current event relationship, creator activity,
  open status, or director curation?
- Do applicant states belong on the public gateway, or should accepted request
  access redirect applicants into `/applications`?
- Which access posture labels are public-safe: public preview, request access,
  invite-only, applications open, casting open?
- Should location cards expose public scene counts or only qualitative state
  until public activity/privacy rules are more mature?

## Proof Needed Before Implementation

- Service tests for public/member/applicant gateway read model differences.
- Rendered privacy tests that private boards, staff rooms, staff counts,
  application-review state, active-face state, and member Desk details do not
  leak to signed-out visitors.
- Browser QA for desktop and mobile with media on/off.
- Long title/name/facet checks.
- No-media fallback verification.
- Accessibility pass for focus order, labels, contrast, and reduced motion.

## Not Now

- Schema changes for featured public scenes or curated gateway rows.
- Thread-specific hero media.
- Public personalization beyond signed-in continuation.
- Route changes from `/c/{community_slug}`.
- Raw director layout controls.
