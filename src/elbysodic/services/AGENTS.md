# Service Layer Steward

## Steward

Service layer steward for `src/elbysodic/services/`: workflow commands, policy
checks, request identity resolution, read models, and product orchestration.

## Protects

- Page handlers call services instead of reaching around them into ad hoc SQL.
- Services accept or resolve community, membership, role, and active-face
  context deliberately.
- Permission decisions route through named policy helpers in
  `services/policies.py`.
- Read models stay shaped for PBP workflows: writing queues, cast faces,
  wanted interest, plotting rooms, materials, notifications, and Studio tools.

## Must Not Become

- A thin pass-through that leaves tenant checks to templates.
- A hidden global singleton model for current community or current user.
- A place where HTML, CSS, route wiring, or SQL schema details take over.

## Documentation Ownership

Co-owns architecture docs for security boundaries, request identity, and
service/repository separation. Update product docs when a workflow changes
visible writer or director behavior.

## Local Checks

- `uv run pytest tests/test_forum_slice.py -q --tb=short`
- `uv run pytest tests/test_policies.py -q --tb=short`
- `uv run pytest tests/test_tenant_repository.py -q --tb=short`
- `uv run ty check src/elbysodic/ tests/`

## Public Contracts And Safety

- Validate community ownership before connecting two scoped objects.
- Validate membership and character ownership for writer actions.
- Keep inactive memberships and non-staff roles out of staff workflows.
- Preserve notification, watch, read-state, and revision-history semantics when
  editing posting or thread workflows.
