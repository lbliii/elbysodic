# Transactional Workflow Coverage Map

Status: architecture coverage map
Last updated: 2026-07-20

This map inventories multi-write workflows that can strand writer, face, scene,
staff, notification, or director state if a late write fails. It names the
service transaction owner, writes performed, side effects, current rollback or
idempotency proof, and remaining gaps.

This is a read-only documentation and regression map. It does not approve new
idempotency storage, schema changes, repair behavior, or transaction-boundary
rewrites without a separate issue and steward review.

## Coverage Table

| Workflow | Actor Shape | Transaction Owner | Writes And Side Effects | Current Proof | Status |
| --- | --- | --- | --- | --- | --- |
| Start thread | explicit-character writer | `AppServices.start_thread()` via posting service/repository transaction | thread, opening post, participants, watch/read state, command reservation result | `tests/test_forum_slice.py::test_start_thread_rolls_back_when_late_write_fails`; `tests/test_forum_slice.py::test_start_thread_validation_error_discards_idempotency_reservation` | covered for rollback and validation retry |
| Reply to thread | explicit-character writer | `AppServices.reply_to_thread()` via posting service/repository transaction | post, notification fanout, watch/read state, command reservation result | `tests/test_forum_slice.py::test_reply_notification_failure_rolls_back_post`; `tests/test_forum_slice.py::test_reply_idempotency_key_prevents_duplicate_posts`; `tests/test_forum_slice.py::test_reply_validation_error_discards_idempotency_reservation` | covered for rollback, duplicate submit, and validation retry |
| Access request invite | staff-actor | Studio launch service method through `AppServices` repository transaction | invitation row, access-request status, linked invitation id, activity event | `tests/test_forum_slice.py::test_access_request_invitation_rolls_back_when_status_update_fails`; `tests/test_forum_slice.py::test_studio_launch_invites_writer_from_access_request` | covered for invite/status rollback and happy path |
| Invite acceptance | public token plus prospective membership | invite acceptance service path | user reuse/create, membership create, optional first face, selected session state | `tests/test_forum_slice.py::test_invited_writer_without_first_face_continues_to_application_form`; `tests/test_forum_slice.py::test_director_invites_writer_through_first_face_handoff`; `tests/test_forum_slice.py::test_invitation_acceptance_rolls_back_when_session_creation_fails` | covered for journey behavior and late session-creation rollback |
| First-face application start | membership-only or prospective-character | `AppServices.create_character()` application workflow | character, application room, default character, application field values, claims/reserves checks | `tests/test_forum_slice.py::test_application_start_rolls_back_when_review_room_creation_fails`; `tests/test_forum_slice.py::test_application_start_form_preserves_validation_errors_and_unique_slugs` | covered for rollback and validation preservation |
| Application acceptance | staff-actor | `AppServices.accept_character_application()` repository transaction | character status, mapped claims, reserve outcomes, revision notes, notifications where applicable | `tests/test_forum_slice.py::test_application_acceptance_rolls_back_claims_and_status_on_late_failure`; `tests/test_forum_slice.py::test_application_review_flags_mapped_claim_conflicts_before_accept` | covered for conflict guard and late claim/status/notification rollback |
| Wanted interest | explicit-character or prospective-character | `AppServices.express_wanted_interest()` / `express_prospective_wanted_interest()` repository transaction | interest row, prospective note, notification or queue side effects | `tests/test_forum_slice.py::test_wanted_interest_rolls_back_when_notification_fanout_fails`; `tests/test_forum_slice.py::test_wanted_hooks_accept_prospective_character_interest` | covered for duplicate/privacy posture and late notification rollback |
| Plotting room start | owner/staff handoff | `AppServices.create_plotting_room_from_*_interest()` repository transaction | plotting room, participants, source interest/hook status, notifications | `tests/test_forum_slice.py::test_plotting_room_start_rolls_back_room_participants_and_interest`; `tests/test_forum_slice.py::test_plot_hook_room_start_rolls_back_room_participants_and_hook`; `tests/test_forum_slice.py::test_plotting_room_notifications_do_not_leak_to_non_participants` | covered for wanted and plot-hook source rollback plus notification privacy |
| Plotting to scene | owner/staff handoff | `AppServices.start_scene_from_plotting_room()` plotting service/repository transaction | thread, opening post, room-scene attachment, notifications | `tests/test_forum_slice.py::test_plotting_room_scene_handoff_rolls_back_on_attach_failure`; `tests/test_forum_slice.py::test_plotting_room_plan_can_turn_into_scene` | covered for rollback and happy path |
| Program Blueprint apply | staff-actor/director | `services.blueprints.apply_program_blueprint_preview()` repository transaction | current-realm role, faces, boards/media, materials/variants, wanted hooks, theme, default face, command reservation/result, accepted audit event | `tests/test_program_blueprints.py::test_program_blueprint_create_only_hydrates_every_supported_primitive`; `tests/test_program_blueprints.py::test_program_blueprint_apply_rolls_back_when_transaction_fails_after_hydration`; `tests/test_program_blueprints.py::test_program_blueprint_apply_rolls_back_earlier_rows_after_late_material_failure`; `tests/test_program_blueprints.py::test_program_blueprint_apply_rejects_non_staff_before_transaction`; `tests/test_program_blueprints.py::test_program_blueprint_apply_rejects_live_collision_stale_fingerprint_in_transaction` | covered for mode/idempotency behavior, tenant and ownership scope, accepted/failed audit outcomes, late rollback, command-reservation rollback, and pre-transaction gates |
| Manual continuity proposal/review | participant author or `manage_world` reviewer | `services.continuity.create_manual_continuity_proposal()`, submission, and review repository transactions | proposal plus citation/affected links; state plus review event; public approval plus canon entry and staff audit | `tests/test_continuity_backend.py::test_manual_continuity_lifecycle_creates_reviewed_public_canon`; `tests/test_continuity_backend.py::test_continuity_review_rolls_back_state_canon_review_and_audit_on_late_failure` | covered for linked-create atomicity, duplicate submit/review retry, lifecycle, public gate, and late review/canon/audit rollback; notification work is a read-only target plan with no fanout |
| Repository transaction recovery | service/repository boundary | `ForumRepository.transaction()` | nested writes and failed commit recovery | `tests/test_backend_contracts.py::test_repository_transaction_rolls_back_and_recovers_when_commit_fails`; `tests/test_forum_slice.py::test_repository_transaction_rolls_back_nested_mixin_writes`; `tests/test_backend_contracts.py::test_request_service_cleanup_rolls_back_open_transactions` | covered for repository recovery |

## Failure-Injection Pattern

Prefer deterministic failure injection at a repository method that runs after
the earliest visible write. A useful rollback test should:

1. Capture the relevant row state before the command.
2. Patch a late repository method to raise a named exception.
3. Execute the service method or rendered POST.
4. Assert the exception is surfaced or converted according to the route
   contract.
5. Assert no partial rows, default-face changes, notification rows, watches,
   read markers, claims, reserves, or activity events survived.
6. Assert the repository connection is usable after rollback.

Avoid client-only duplicate prevention as proof. Browser submit guards are
feedback; service idempotency and duplicate policies own correctness.

## Remaining Gaps

No known rollback gap remains for the multi-write workflows currently listed
in the coverage table. Keep the map open to new workflow families under these
follow-on rules:

- Claim/reserve maintenance should add duplicate behavior and rollback proof if
  those workflows grow beyond their current single-row updates.
- Every new notification target family must add rollback or visibility proof
  before it can affect shell counts.
- New multi-write workflows enter this table as `partial` until deterministic
  late-failure injection proves both rollback and connection recovery.

## Standard Proof Gate

Use this focused gate for transaction coverage work:

```bash
uv run pytest tests/test_forum_slice.py tests/test_program_blueprints.py tests/test_backend_contracts.py -q --tb=short
```

Use the broad local gate before merging transaction-boundary changes:

```bash
uv run ruff check .
uv run ruff format . --check
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
uv run pytest -q --tb=short
```
