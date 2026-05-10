# Terminology Map

This is the product-design steward's UX writing map for PBP-native interface
language. It is guidance for rendered UI, labels, empty states, and design
reviews; it does not rename routes, schema, services, or repository concepts.

## Principles

- Use the term writers use at the moment of action.
- Keep public story language warmer and more immersive than implementation
  language.
- Keep staff and moderation controls precise when the object is technical.
- Do not collapse PBP vocabulary into generic forum, SaaS, or social-network
  labels.

## Scene Vs Thread

Use `scene` when the user-facing meaning is a playable story unit:

- Primary action labels: `Start scene`, `Open scene`, `Post reply`.
- Location and board browsing: `Scenes here`, `Active scenes`, `No scenes have
  opened here yet`.
- Composer setup: `Scene draft`, `Scene setup`, `Scene summary`.
- Wanted and plotting handoff: `Ready for scene`, `Start scene`.
- Queue state: `Needs reply`, `Waiting`, `Caught up`, `Watching`.

Use `thread` when the interface is describing the structural container,
history, or moderation object:

- Route, code, repository, and service names.
- Technical or staff actions: `Watch thread`, `Unwatch thread`, `Pin thread`,
  `Lock thread`, `Move thread`.
- Non-story community boards where the unit is discussion rather than play.
- Filter labels only when the board is explicitly not a location or play
  surface.

Rule of thumb: if the button starts play or the heading frames playable canon,
say `scene`; if the control manages the container, say `thread`.

## Canon And Guidebook

- `Guidebook` is the user-facing home for director-authored world material.
- `Material` is acceptable for staff editing and internal design-system
  language.
- `Canon` names the durable in-world text on detail pages.
- `Progression` names the way a canon item moves into events, scenes, hooks,
  and locations.
- `Event` should feel like live plot pressure, not a calendar item.

## Identity

- `Face` is the active public posting identity.
- `Character` is acceptable in forms and profile pages where precision matters.
- `Roster` is the writer's owned set of faces in one community.
- `Member` or `membership` is used for community identity, permissions, and
  staff context; do not use `user` in community-facing copy unless login scope
  is the point.

## Navigation And Production

- `World` is the primary play surface for canon and locations.
- `Desk` is the writer's operational view for reply obligations and queues.
- `Studio` is the director/staff production surface.
- `Wanted` is casting demand; `plotter` is relationship/connection planning.
- `Claims` and `reserves` are formal community-management concepts and should
  keep those names.

## Design Review Checklist

- Does the primary CTA use `scene` when it starts playable story?
- Does metadata avoid becoming a row of unexplained badges?
- Do staff controls name the managed object precisely?
- Does the copy preserve face, roster, wanted, claims, reserves, needs reply,
  waiting, caught up, and watching where those concepts apply?
- Are route/code words leaking into rendered UI without a user reason?
