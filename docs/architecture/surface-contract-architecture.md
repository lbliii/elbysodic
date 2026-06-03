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

## Extraction Pattern

When a surface grows enough orchestration to hide policy, batching, or privacy
decisions inside `AppServices` or a page handler, extract it in this order:

1. Keep the route handler thin. It may resolve request-local web settings,
   call one `AppServices` method, and render the template.
2. Keep `AppServices` as the route-facing facade. It resolves the viewer and
   passes request-scoped service inputs into a narrower module such as
   `services/activation.py`, `services/operations.py`, `services/network.py`,
   `services/boards.py`, or `services/materials.py`.
3. Put the read-model assembly in a domain-named service module. That module
   owns filtering, sorting, publication rules, capability checks, and batching
   for the surface.
4. Give the extracted module a repository `Protocol` that names the reads it
   needs. Prefer existing narrower protocols such as thread, material, facet,
   notification, or post-view protocols over a concrete `ForumRepository`
   dependency.
5. Keep `community_id` explicit in every repository call and cache-shaped map.
   Batch maps should be keyed by tenant-local ids or by `(community_id, id)`
   when results can cross realm boundaries.
6. Move focused proof with the extraction: service/read-model tests for pure
   contracts, rendered privacy tests for route output, query-budget tests for
   batching-sensitive surfaces, and browser QA when the interaction flow can
   regress outside HTML assertions.

The extracted module should be boring to call from `AppServices`: a small
function with explicit inputs, no request object, no template dependency, and no
page-local SQL fallback.

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

## Critical Surface Matrix

These repeated surfaces should stay tied to one route-facing service method.
When a row changes, update the rendered route privacy matrix and add proof for
both visible and absent state.

| Surface | Service Contract | Shell Count | Page List | Detail View | Action Availability | Notification Visibility | Current Proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Realm home | `AppServices.realm_home()` for member state; `public_realm_gateway()` for public previews | `ForumView.unread_notification_count` and identity options remain viewer-scoped | Location, community, attention, and activity lists are service-filtered | Gateway continuation is viewer-scoped; public preview omits member state | Director controls use `can_manage_home` from the service | No notification rows render on public/member home beyond scoped shell counts | `test_rendered_surface_contract_parity_across_realm_viewers`; production public preview tests |
| Claims directory | `AppServices.claims_page()` | No shell count contract | Claim groups, filters, and counts come from `ClaimsDirectory` | Character links stay current-community scoped | Maintenance forms and notes depend on `ClaimsDirectory.can_manage` | Claim state does not create inbox visibility by itself | `test_rendered_surface_contract_parity_across_realm_viewers`; claims directory tests |
| Roster and face pages | `AppServices.character_roster_page()` and `character_profile()` | Identity options may show switchable same-account realms, but page lists stay current-community scoped | Roster cards come from `CharacterRosterDashboard` | Character profiles reject inactive owners and cross-community slugs through service recovery | Add-face and style controls render only for the current membership surface | Character-targeted notifications are filtered by ownership or casting capability | roster/profile community-scope tests; rendered parity test |
| Thread and posting | `AppServices.board_page()`, `read_thread()`, and posting service methods | Board and unread counts are policy-filtered | Board thread filters use service-owned membership, roster, and board visibility | `ThreadView` owns cast, post views, watch/read state, and composer posture | Composer and staff controls derive from read-model capability flags | Watched-thread and mention notifications link only to visible targets after satisfying the registered target contract | thread filter, posting, notification, and rendered parity tests |
| Wanted and plotting | `wanted_ads()`, `read_wanted_ad()`, `plotting_desk()`, and `read_plotting_room()` | Wanted navigation stays public/member safe | Wanted lists split public open hooks from member/staff backstage state | Wanted detail owns interest notes, room links, reserves, and scene handoffs | Interest, reserve, and plotting-room actions are owner/staff/member scoped | Wanted and plotting notifications hide inaccessible notes and room titles, and new target kinds must declare required fields in the notification registry | wanted privacy, plotting notification, and rendered parity tests |
| Staff and director queues | `director_studio()`, `director_operations()`, `applications_desk()`, and `casting_desk()` | Studio counts are capability-scoped | Queue rows, first-action lane links, and production health come from service read models | Review rooms and operations details enforce staff capability before rendering | Mutating forms stay behind policy-backed service methods | Staff still sees only its own inbox, not a global notification feed | Studio launch/discovery/operations tests; rendered parity test |
