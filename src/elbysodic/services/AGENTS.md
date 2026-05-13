# Service Layer Steward

This domain represents Elbysodic workflows: policy checks, request identity
resolution, read models, and product orchestration between repositories and
rendered pages.

Related docs:

- root `AGENTS.md`
- `docs/architecture/security-boundaries.md`
- `docs/architecture/multi-tenancy.md`
- `docs/architecture/rendered-route-privacy-matrix.md`
- `docs/architecture/surface-contract-architecture.md`
- `docs/product/information-hierarchy.md`

## Point Of View

Represent writers, directors, moderators, and route handlers that need workflows
to be tenant-aware, permission-aware, and shaped for PBP rituals rather than
raw database operations.

## Protect

- Page handlers call services instead of reaching around them into ad hoc SQL.
- Services accept or resolve community, membership, role, and active-face
  context deliberately.
- Permission decisions route through named policy helpers in
  `services/policies.py`.
- Cross-object workflows validate community ownership before connecting scoped
  records.
- Writer actions validate membership and character ownership.
- Read models preserve queue language, cast faces, wanted interest, plotting
  room context, materials, notifications, Studio tools, and privacy.
- Posting, thread lifecycle, watches, read state, revision history, and
  notifications keep their semantics when workflows change.

## Contract Checklist

- Services: command/query methods accept the right context and return stable
  read models.
- Surface contracts: page-level service methods own filtering, sorting,
  publication posture, permission posture, and workflow assembly before the
  template renders.
- Policies: role, membership, active, and staff checks stay centralized.
- Storage: repository calls are tenant-scoped and do not bypass boundary
  errors.
- UI: pages render the intended workflow state and hide private/staff-only data.
- Docs: security boundaries, tenant docs, and product docs reflect changed
  workflows.
- Tests: `tests/test_forum_slice.py`, `tests/test_policies.py`,
  `tests/test_tenant_repository.py`, and targeted service tests cover the path.
- Changelog: add a fragment for user-visible workflow changes.

## Advocate

- Add small service methods before route handlers grow policy or orchestration
  branches.
- Improve read model names and diagnostics when workflows become hard to
  review.
- Push workflow changes to include rendered proof, not only repository tests.

## Serve Peers

- Give web pages compact read models and explicit errors.
- Give storage clear repository method needs and tenant-boundary expectations.
- Give domain steward feedback when primitives lack authorship, state, or role
  vocabulary.
- Give tests deterministic workflow seams and realistic PBP fixture needs.

## Do Not

- Become a thin pass-through that leaves tenant checks to templates.
- Hide global current-community or current-user state in services.
- Put HTML, CSS, route wiring, schema DDL, or raw page rendering in services.
- Let inactive memberships or non-staff roles into staff workflows.

## Own

- `src/elbysodic/services/`
- policy and read-model contracts used by `src/elbysodic/web/`
- service-facing portions of security, multi-tenancy, and rendered privacy docs
- workflow tests in `tests/test_forum_slice.py`, `tests/test_policies.py`,
  and related focused tests
- type-check proof for service signatures and read models
