# Surface Contract Architecture

Surface Contract Architecture is Elbysodic's rule for keeping page behavior
tenant-safe, PBP-native, and reviewable. Every meaningful rendered surface
should have a named contract between service-owned workflow state and the
template that presents it.

## Terms

- **Domain model**: product facts such as `Community`, `CommunityMembership`,
  `Character`, `Thread`, `Material`, `WantedAd`, claim, reserve, and plotting
  room records.
- **Workflow service**: the place that resolves identity, policy, lifecycle,
  tenant ownership, and orchestration.
- **Surface contract**: the named service method plus read model a page is
  allowed to render.
- **Template**: presentation only. It may choose markup and components, but it
  should not decide privacy, staff capability, publication status, ranking, or
  lifecycle inclusion.

## Contract Shape

For each rendered surface, record or make obvious:

- audience: public, member, owner, character-backed writer, staff, director,
  inactive, or cross-tenant recovery
- route family and canonical service method
- read model name and repeated card/list/action models it uses
- community, membership, character, staff, and publication boundaries
- search, filtering, sorting, grouping, and ranking owner
- expected empty states, recovery states, and forbidden states
- rendered tests and docs collateral

## Rules

- Public pages render public read models. They can show published public realm
  material, public wanted posture, roster counts, and safe calls to action.
  They must not carry membership names, active faces, unread counts, staff
  signals, private queues, drafts, or mutating forms.
- Member pages render membership-scoped read models. They may include the
  writer's active face, obligations, notifications, watches, and private
  continuation paths only after the selected membership is resolved.
- Character surfaces render character-aware read models when public authorship
  or story context matters. They must keep membership ownership and public face
  authorship distinct.
- Staff and director pages render capability-scoped workflow read models. Staff
  controls, draft material, review queues, private notes, reserves, and
  lifecycle actions must stay behind named policy helpers.
- Templates do not query repositories, choose between draft and published
  material, decide staff capability, or assemble cross-object workflow state.
- Repeated PBP concepts such as face cards, wanted hooks, scene obligations,
  claim rows, reserve rows, application lanes, notification targets, and
  Studio rooms should become shared read models or shared components before
  markup forks across pages.

## Audit Questions

Use these questions when a page feels hard to reason about:

1. Can the route handler name exactly one service method that owns the page
   state?
2. Can the template render without checking role, membership ownership,
   publication status, or cross-community ownership itself?
3. Does the read model separate public catalog state from signed-in return
   paths?
4. Does the surface use PBP vocabulary: face, roster, scene, thread, plotter,
   wanted, claims, reserves, needs reply, waiting, caught up, and watching?
5. Are empty, inactive, faceless, forbidden, and cross-tenant recovery states
   explicit?
6. Do rendered tests prove what appears and what stays hidden?
7. Do `security-boundaries.md` and `rendered-route-privacy-matrix.md` still
   describe the current behavior?

## Steward Routing

Consult the Surface Contract Steward for new or changed rendered surfaces,
page-level read models, public discovery/search behavior, shell/sidebar counts,
staff queues, and route handlers that are accumulating filtering, privacy, or
ranking decisions.

The Surface Contract Steward coordinates these local owners:

- Service Layer Steward for workflow methods, policy checks, and read models.
- Rendering And UI Steward for route handlers, templates, components, and
  visual hierarchy.
- Test Steward for route, service, rendered privacy, and regression proof.
- Product And Architecture Docs Steward for architecture docs, product
  vocabulary, and privacy matrix collateral.

## Proof

The lightest acceptable proof depends on risk:

- doc-only guidance: no runtime gate required unless examples include code
- read-model-only change: focused service tests, Ruff, ty, and app check when
  imports or page context can change
- rendered page change: app check plus focused rendered tests
- privacy boundary change: signed-in/signed-out, staff/member, inactive or
  cross-tenant rendered proof as applicable
- public discovery change: proof that drafts, backstage realms, member state,
  active faces, unread counts, staff signals, and mutating forms stay out of
  public output
