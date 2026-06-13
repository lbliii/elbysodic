# Front-End Surface Conversion Pack

Status: implementation audit pack for #117
Owner: Web, product design, surface-contract, and test stewardship
Last updated: 2026-06-04

This pack turns the front-end debt epic into a repeatable audit. It does not
change route, auth, privacy, schema, or service behavior. Use it when a PR
touches rendered auth/access, onboarding, public preview, Writer Desk, Studio,
applications, claims/reserves, wanted, composer, or shell-adjacent surfaces.

## Audience And Risk

The high-risk audiences are signed-out visitors, signed-in account visitors,
faceless members, applicant writers, active-face writers, hook hunters,
directors, staff, inactive members, and cross-community recovery visitors.

The failure modes are:

- public or account visitors seeing a community shell, unread counts, active
  face controls, staff controls, private queues, application review state, or
  invitation material
- members and applicants losing the next first-face, application, claims,
  reserve, reply, or plotting action behind generic setup language
- staff and directors seeing Studio as a generic admin dashboard instead of a
  realm production room
- repeated PBP UI shapes drifting into page-local CSS or ad hoc templates
- forms, filters, drawers, and action panels losing labels, focus visibility,
  keyboard reachability, or mobile tap room

## Shared Pattern Inventory

| Pattern | Shared Owner | Current High-Risk Surfaces | Conversion Rule | Required Proof |
|---|---|---|---|---|
| Product/account access posture | `_components/access.html` | login, request access, invite acceptance, Network account return | Use `product_identity()` and `access_account_notice()` before page-local account panels. Account posture never grants a realm shell or membership affordance. | Rendered auth/access tests, negative shell/count assertions, labelled form checks |
| Empty or caught-up policy block | `_components/ui.html` | Desk, applications, casting, claims, notifications, plotting, wanted | Use `empty_policy_block()` when the empty state reduces anxiety or points to the next PBP action. Hide optional empty lanes that only prove nothing exists. | Rendered page tests for the empty state and absent private/staff data |
| Page section rhythm | `_components/ui.html` | Desk, applications, Studio, long workflow rooms | Use `page_section()` before inventing page-local section headers around repeated workflow regions. | Semantic heading/region assertions and app check |
| Command/pulse/metric vocabulary | `_components/vocabulary.html` | Desk, applications, members, Network, notifications, Studio rooms | Use `page_pulse()`, `command_panel()`, `command_action()`, `lane_preview()`, and `metric_item()` for workflow signals. Counts must change confidence, urgency, privacy, availability, or next action. | Rendered tests for labels and available actions |
| Thread and queue previews | `_components/thread_summary.html` | My Threads, board pages, character/member scenes, community activity | Use thread summary components for needs reply, waiting, watched, caught up, and activity rows before duplicating scene cards. | Rendered queue tests with face/writer distinction |
| Wanted and plotting hook cards | `_components/wanted.html`, `_components/plot_hooks.html` | wanted index/detail, casting, character hooks | Use wanted/hook components for hook identity, relationship, reserve, interest, and plotting handoff. Do not stamp every child with `Wanted hook` when the parent section already says it. | Wanted/application/privacy tests with negative private-note assertions |
| Realm gateway/public preview | `_components/realm_gateway.html`, `_components/network_catalog.html` | root community home, Network, public catalog, account visitor preview | Public surfaces sell premise, places, wanted, guidebook paths, activity, and access posture without launch blockers or staff setup state. | Public/account/member/staff rendered tests and browser QA |
| Director controls and production rooms | `_components/director_controls.html`, `_components/vocabulary.html` | Studio, board/studio board pages, launch, operations, discovery | Director controls attach to the production object and stay visually behind story/writer context unless the director is in Studio. | Staff/director rendered tests and privacy matrix updates when behavior changes |
| Composer controls and post style preview | `_components/composer.html`, `_components/post_style_preview.html` | new thread, reply, edit post, character/post style | Composer toolbar, preview, active face, draft state, and post style controls stay shared. | Markup safety tests, form tests, browser QA for desktop/mobile writing surfaces |
| Facets and claims/intake context | `_components/facets.html`, claims/intake templates | claims, applications, characters, world, discover, wanted | Facets are not generic tags. Clickable filters must look distinct from descriptive chips, and claims/reserves must stay current-community scoped. | Rendered claims/application tests and tenant boundary tests |

## CSS And Token Audit

CSS movement uses `docs/architecture/theme-css-architecture.md` as the owner
ledger. A PR that touches CSS should classify each touched selector as one of:

- Chirp primitive adoption or narrow Chirp override
- Elbysodic PBP component
- product-family selector
- temporary page composition
- legacy ledger item with a replacement path

Do not add a new page-local selector when a shared component or existing theme
layer already owns the shape. Elbysodic-specific tokens belong in
`src/elbysodic/web/static/elbysodic-theme.css` and
`src/elbysodic/web/static/elbysodic-theme/00-tokens.css`; product-family files
should reference tokens rather than inventing one-off color, spacing, border,
or shadow systems.

## Label And Typography Audit

Every audited page should pass these checks before visual QA:

- One dominant phrase in each heading cluster.
- No child card repeats the parent section's object type unless the set mixes
  object types or the state changes the next action.
- Kicker, badge, metric label, helper line, and footer each add a distinct axis:
  privacy, lifecycle, urgency, ownership, relationship, active-face relevance,
  or action.
- Counts appear only when they change confidence, urgency, privacy,
  availability, or next action.
- PBP vocabulary wins over generic labels: face, roster, thread, scene,
  plotter, wanted, claims, reserves, needs reply, waiting, caught up, and
  watching.

## Accessibility Audit

For form, filter, drawer, navigation, or command changes, prove:

- visible controls have an accessible label or labelled control wrapper
- hidden controls are limited to command context, CSRF, idempotency, selected
  object ids, or return paths
- submit buttons name the PBP action, not a generic `Continue`
- alerts use `role="alert"` and passive confirmations use `role="status"`
- keyboard focus is visible and remains near the object being changed
- mobile tap targets do not overlap and preserve the next action plus privacy
  state

## Browser QA Profiles

Run browser QA when layout, interaction, or responsive behavior changes. Keep a
desktop and mobile capture for the changed surface family:

| Profile | Routes/States |
|---|---|
| Auth/access | `/login`, `/request-access`, `/invite/{token}` valid/error/recovery |
| Public preview | `/`, `/network`, public community home, wanted detail, guidebook material |
| Account visitor | Network return panel and realm preview without member shell, Desk, active face, unread counts, or staff controls |
| Writer onboarding | faceless Desk, application draft/revision, claims/reserves, first scene handoff |
| Writer work | `/desk`, `/my/threads`, `/notifications`, thread reply composer |
| Wanted/plotting | wanted index/detail, interest state, plotting room handoff |
| Studio | `/studio`, `/studio/launch`, `/studio/operations`, `/studio/intake`, `/studio/discovery` |
| Public catalog | `/network`, `/network?q=...`, catalog cards, request-access entry actions |

Browser QA should check first viewport priority, text fit, focus/tap behavior,
private/staff state absence, active-face or account posture, and whether the
screen still reads as modern PBP software instead of a generic SaaS dashboard
or old forum index.

## Not Now

- SPA conversion
- raw CSS or external font inputs
- self-serve public registration
- auth/session enforcement changes
- schema or migration work
- email/push notification preferences
- broad visual redesign without surface-specific proof
