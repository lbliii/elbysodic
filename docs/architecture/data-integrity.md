# Data Integrity Contracts

Elbysodic stores global users and community-scoped creative records. Repository
methods keep `community_id` explicit, but SQLite constraints must also prevent
impossible tenant pairings wherever the data model can express them.

## Tenant-Paired Rows

A tenant-paired row stores `community_id` and one or more foreign keys to rows
that also belong to a community. Those references must resolve in the same
community before the row is persisted.

High-risk tenant-paired rows include:

- memberships and roles
- characters and memberships
- boards, threads, posts, and public authorship
- command submissions and the membership that reserved the command
- applications and review events
- realm interaction definitions, responses, answers, and options
- wanted hooks, interests, reserves, and claims
- plotting rooms, source interests, target scenes, participants, and messages
- reactions, reads, watches, and thread participants
- notifications and sidebar counts
- user-session selected membership
- facet assignments and community presentation roots

## Enforcement Layers

Use all three layers:

- Schema: composite foreign keys, unique pairs, checks, or triggers.
- Repository: scoped methods that load parent rows by `community_id`.
- Services: workflow validation using resolved viewer, policy helpers, and
  explicit actor shapes.

Diagnostics are not a substitute for constraints. They are the repair and
operations surface for old data, migrations, imports, and local demo databases.
`ForumRepository.list_tenant_pair_integrity_issues()` is the shared repository
diagnostic for tenant-paired creative and workflow rows, including membership
roles, default faces, character ownership, command submissions, authorship,
claims, realm interactions, plotting rooms, reactions, thread state, and
notifications. Diagnostic rows report ids, table names, tenant ids, and
content-free relationship reasons so operators can plan repair work without
exposing private posts, room notes, application answers, or staff-only details.

`src/elbysodic/services/tenant_integrity.py` wraps those repository diagnostics
as a read-only service report. The report groups findings by `community_id` and
severity, preserves table/domain/row ids for repair planning, and keeps output
free of post bodies, private notes, applicant emails, room notes, and account
secrets. Director-scoped reads filter to the current community through
`tenant_integrity_audit_for_viewer`; ordinary members, inactive memberships,
public visitors, and staff from another community must not see a realm's audit
findings. CLI exposure and nonzero-exit behavior remain deferred until the
operator command shape is approved.

Schema version `23` adds the storage half of this contract. Before upgrading,
it runs content-free predicates for every row family emitted by the repository
diagnostic. The first invalid table/row blocks the migration at version `22`
with an instruction to run the audit; no private content is printed and no row
is moved, cleared, or deleted automatically. A clean database receives
insert/update triggers that reject tenant reassignment and invalid peer ids.
Fresh databases install the identical trigger set through `create_schema()`.

## Tenant Integrity Audit Matrix

This matrix is the planning spine for #55, #56, and #141. It does not approve
schema, migration, trigger, public command, lifecycle, concurrency, or repair
changes. Each future implementation slice should update the row for the family
it hardens and include the proof group named below.

| Row Family | Invalid Pairings To Reject | Runtime Owner | Storage/Diagnostic Owner | Current Proof Or Gap | Migration Risk |
|---|---|---|---|---|---|
| Memberships and roles | Membership role from another community; inactive membership selected as active viewer; user-level staff power inferred outside membership. | Request identity resolver and policy helpers. | `community_memberships`, roles, session diagnostics, and v23 guards. | Negative writes, corrupt-row audit, migration rejection, and selected-session triggers are covered. | Legacy drift blocks upgrade for deliberate repair. |
| Characters and default faces | Character owned by another membership or community; default face points at a wrong-community or inactive face. | Character services and viewer resolution. | Character/default-face diagnostics and v23 guards. | Wrong-community and wrong-owner writes are rejected; legacy drift remains auditable. | Legacy drift blocks upgrade for deliberate repair. |
| Threads, posts, and participants | Thread board, author membership, author face, post author face, participants, watches, and read state cross community or membership. | Posting/thread services and explicit-character validation. | Thread/post/revision/participant/read/watch diagnostics and v23 guards. | Repository boundaries, storage-negative tests, rollback proof, and trigger parity are covered. | Story-visible drift is never auto-repaired. |
| Command submissions | Idempotency key reserved for a membership or community that does not match the executed command. | Command binding and service transaction owners. | `command_submissions` diagnostics and v23 guards. | Scoped retries remain service-owned; storage rejects cross-realm reservations. | Stale invalid reservations block upgrade. |
| Applications and review events | Application face, applicant membership, reviewer membership, mapped claims/reserves, and review events disagree on community. | Application/review services. | Application/event/field diagnostics and v23 guards. | Storage-negative and legacy-audit proof cover applications, events, template mappings, and values. | Private review rows are never printed or auto-repaired. |
| Access requests and invitations | Request, event, linked invitation, account link, inviter, and accepted membership drift across community or create permission before invite acceptance. | Access-request and invitation services. | Request/event/invitation diagnostics and v23 guards. | Cross-realm links, actors, roles, and accepted memberships fail at storage. | Token/applicant data stays out of migration errors. |
| Wanted hooks, interests, reserves, and claims | Wanted hook, interested membership or face, claim type, reserve owner, claimed face, and staff reviewer disagree on community or membership. | Wanted, claim, reserve, and application handoff services. | Wanted/claim/reserve/facet diagnostics and v23 guards. | Storage-negative proof covers creator faces, interests, reserves, claims, and assignments. | Public/private rows are never auto-moved. |
| Plotting rooms, messages, and scene handoffs | Room community, source wanted interest, target scene, participants, messages, and attached scene cross community or exclude authorized participants. | Plotting and scene handoff services. | Plotting diagnostics, transactions, and v23 guards. | Sources, targets, owners, participant faces, and message authors fail closed at storage. | Room content remains absent from diagnostics. |
| Realm interactions and answers | Prompt, option, response, answer, membership, face, and community point to different tenant roots. | Interaction/application services. | Realm-interaction diagnostics and v23 guards. | Question/option/response/answer joins have negative storage and migration parity proof. | Malformed answers block upgrade for explicit repair. |
| Notifications and shell counts | Notification membership, target community, target row, href, read state, and visibility resolver disagree. | Notification target resolver and shell/inbox read models. | Notification diagnostics, target resolver, and v23 guards. | Stored recipients, actors, faces, and typed targets must share one community. | Hidden target rows are never included in errors. |
| Sessions and selected identity | Session user, selected membership, selected community, role, active face, and route tenant prefix drift. | Auth service and request identity resolver. | Session diagnostics and selected-identity triggers. | User/community/membership selection fails closed at storage and request resolution. | Stale sessions fail closed without cross-realm recovery leakage. |
| Continuity/export source links | Source family, source community, source row, source thread for posts, affected object, and viewer visibility disagree. | Continuity/export services. | Future continuity/export diagnostics. | Continuity source visibility and export redaction proof exists for readiness; backend expansion remains future work. | Medium-high; export must preserve provenance without leaking private source material. |

## Hardening Slices And Proof

Use these slices to keep future PRs reviewable:

1. Diagnostic slice: add or expand repository diagnostics for one row family,
   prove corrupt legacy rows are detected, and keep output content-free.
2. Negative repository slice: add tenant-pair tests showing wrong-community or
   wrong-membership writes fail before or at persistence.
3. Service rollback/idempotency slice: add failure-injection or duplicate-submit
   proof for one workflow family from
   `docs/architecture/transactional-workflow-coverage.md`.
4. Migration/constraint slice: after diagnostics and tests exist, add the fresh
   schema, ordered migration, parity proof, and repair or rejection policy.
5. Operations slice: expose read-only diagnostics only after operator output,
   redaction, exit behavior, and runbook language are approved.

Proof groups:

| Proof Group | Required Coverage |
|---|---|
| Repository | Multiple communities, same global user in different communities, wrong-membership faces, wrong-role memberships, and direct corrupt-row diagnostics. |
| Service | Resolved viewer, explicit actor shape, policy failure, stale command behavior, rollback after late write failure, and duplicate/idempotency behavior where the workflow creates visible rows. |
| Rendered POST | CSRF, tenant-prefixed route, hidden `next` or return path, active-face/staff-role drift, and privacy-safe failure copy. |
| Migration parity | Fresh schema and upgraded schema include the same tables, indexes, triggers, constraints, `PRAGMA foreign_key_check` behavior, and migration ledger version. |
| Operations | Redacted report output, no private story text or applicant notes, director-scoped audit visibility, and non-destructive default behavior. |

Stop and ask before any slice adds schema, migrations, triggers, repair
behavior, public CLI/API/route contracts, persistence lifecycle changes,
concurrency changes, or command protocol changes.

## Session Selection

A persisted selected session identity must identify one active membership owned
by the session user. The selected community and selected membership cannot drift.

The preferred long-term shape is to store one selected membership and derive the
community and user. If redundant columns remain, the database must enforce the
pair with triggers or composite constraints.

## Authorship

Story-visible rows must preserve authorship:

- a post's thread, author membership, and author character belong to one
  community
- a post character belongs to the post membership
- a thread author character belongs to the thread author membership
- staff actor rows name staff membership separately from public character
  context

Wrong-face authorship is a product safety issue, not only a database bug.

## Migration Rules

Schema hardening should land in waves:

1. Add diagnostics and negative tests.
2. Repair or clear invalid existing rows in a migration.
3. Add constraints or triggers.
4. Prove fresh and upgraded schema parity.
5. Run `PRAGMA foreign_key_check` and targeted integrity checks.

Each migration should keep fresh schema and ordered migrations equivalent.
