# Steward Regression Pack

Status: architecture test map
Last updated: 2026-06-03

This map turns repeated steward concerns into durable regression entry points.
It does not replace local steward files or full CI. It gives future agents a
fast way to find which tests prove tenant, identity, rendered privacy,
notification, transaction, export/restore, auth posture, and continuity
contracts.

## How To Use This Map

1. Identify the steward concern touched by the change.
2. Run the primary focused gate for that concern before broader CI.
3. Add new focused regression cases near the existing module when a bug escapes
   a steward or a new invariant becomes product doctrine.
4. Update this map when a test file is renamed, split, or becomes the primary
   gate for a concern.

## Tenancy And Data Integrity

Point of view: community-local ownership is the storage backstop for every
service and rendered surface.

Primary tests:

- `tests/test_tenant_repository.py`
- `tests/test_backend_contracts.py`

Focused gate:

```bash
uv run pytest tests/test_tenant_repository.py tests/test_backend_contracts.py -q --tb=short
```

What this catches:

- cross-community row joins
- wrong-membership character ownership
- inactive or malformed selected identity state
- repository transaction rollback recovery
- page-handler raw SQL drift

Extend this section when new row families become tenant-paired, such as future
continuity proposal source links or audit-event targets.

## Identity And Auth Posture

Point of view: global users, community memberships, roles, sessions, and public
faces remain separate, even when a single login can enter several realms.

Primary tests:

- `tests/test_auth_contracts.py`
- `tests/test_web_security.py`
- `tests/test_forum_slice.py`

Focused gate:

```bash
uv run pytest tests/test_auth_contracts.py tests/test_web_security.py -q --tb=short
```

What this catches:

- production auth trust posture drift
- seed password and demo-mode posture
- signed-out and signed-in account visitor privacy
- CSRF coverage on sensitive forms
- stale, inactive, or cross-user membership recovery

Do not use this map to approve auth enforcement changes by itself. Auth,
session, CSRF, or security behavior changes still require the root stop-and-ask
review posture.

## Rendered Surface Contracts

Point of view: page handlers call named services, templates render read models,
and privacy/ranking/lifecycle decisions stay out of markup.

Primary tests:

- `tests/test_backend_contracts.py`
- `tests/test_forum_slice.py`
- `tests/test_web_security.py`
- `tests/test_shell_navigation.py`

Focused gate:

```bash
uv run pytest tests/test_backend_contracts.py tests/test_shell_navigation.py -q --tb=short
```

What this catches:

- surface registry and privacy matrix drift
- page handlers bypassing service contracts
- shell/sidebar count and navigation privacy regressions
- public preview, account visitor, inactive, faceless, staff, and
  cross-community rendered privacy errors

Add browser QA when layout, focus, responsive behavior, or visual trust is part
of the accepted finding.

## Notification Target Visibility

Point of view: an inbox row delivered to the right membership is still hidden
when its target is malformed, inaccessible, private, or cross-community.

Primary tests:

- `tests/test_notification_contracts.py`
- `tests/test_forum_slice.py`

Focused gate:

```bash
uv run pytest tests/test_notification_contracts.py -q --tb=short
```

What this catches:

- notification target contract registration drift
- missing required target fields
- private plotting-room and wanted-interest leakage
- inbox-window parity after hidden rows are filtered
- unread count and mark-read visibility errors

Add target-family tests before a new notification kind can affect shell counts,
inbox rows, redirects, or mark-read behavior.

## Transactional Workflows

Point of view: multi-write workflows should not strand scenes, posts,
notifications, applications, claims, reserves, plotting rooms, or Blueprint
rows after a late failure.

Primary tests:

- `tests/test_forum_slice.py`
- `tests/test_program_blueprints.py`
- `tests/test_backend_contracts.py`

Focused gate:

```bash
uv run pytest tests/test_forum_slice.py tests/test_program_blueprints.py -q --tb=short
```

What this catches:

- thread start and reply rollback failures
- application start rollback failures
- plotting-room scene handoff rollback failures
- Blueprint apply transaction proof
- repository commit-failure recovery

Prefer failure-injection helpers that fail at the service/repository seam and
then assert no partial rows survived.

## Export, Restore, And Operations

Point of view: operator diagnostics and exports should be useful during
incidents without leaking global accounts, passwords, token hashes, raw invite
tokens, or private cross-community details.

Primary tests:

- `tests/test_community_exports.py`
- `tests/test_forum_slice.py`
- `tests/test_cli.py`

Focused gate:

```bash
uv run pytest tests/test_community_exports.py tests/test_cli.py -q --tb=short
```

What this catches:

- export manifest privacy drift
- operations inspection and integrity output regressions
- CLI smoke and command contract drift
- restore-check and future restore-plan output shape changes

Human-confirmation, destructive recovery, schema repair, and deployment changes
remain outside this regression pack unless a separate issue approves them.

## Continuity Readiness

Point of view: Continuity Graph work stays gated until source-linked memory,
canon review, privacy, notification, and export boundaries are proven.

Primary tests:

- `tests/test_continuity_domain.py`
- `tests/test_continuity_readiness.py`

Focused gate:

```bash
uv run pytest tests/test_continuity_domain.py tests/test_continuity_readiness.py -q --tb=short
```

What this catches:

- continuity primitive invariants
- readiness gate drift
- source visibility expectations before public route families exist
- docs/test disagreement around future canon review boundaries

Future rendered continuity routes need Surface Contract, Notification, Export,
Auth, and Tenancy proof before this section can become implementation coverage.

## Blueprint Import And Apply

Point of view: director-authored Program Blueprints can create setup material
only through the validated, tenant-scoped, rollback-proven import contract.

Primary tests:

- `tests/test_program_blueprints.py`
- `tests/test_forum_slice.py`

Focused gate:

```bash
uv run pytest tests/test_program_blueprints.py -q --tb=short
```

What this catches:

- parser and validation diagnostics
- unknown-key and vocabulary validation drift
- tenant-scoped hydration behavior
- apply transaction and rollback proof

Keep Blueprint behavior out of generic plugin language. The current extension
contract is Program Blueprints, not a general plugin system.

## Not-Now Gaps

- Performance budgets are covered only where focused query-budget tests already
  exist; broader benchmark gates are still not part of the pack.
- Live Railway production smoke remains an operations record, not a local test.
- Browser-only findings belong in operations QA notes and should be promoted
  into rendered tests only when behavior can be proven semantically.
- Partial staff capability storage and tenant-scoped audit-event rows are
  covered by policy, repository, migration, raw storage-negative, service-read,
  and representative workflow integration tests. Rendered role editing and an
  audit room remain separate product-surface work.
- Real UXR and observed UAT are outside this test pack and must keep consent
  and evidence labels in `research/`.

## Standard Broad Gate

Run the broad local gate before merging high-risk or cross-steward changes:

```bash
uv run ruff check .
uv run ruff format . --check
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
uv run pytest -q --tb=short
```
