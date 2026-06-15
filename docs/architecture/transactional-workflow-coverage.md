# Transactional Workflow Coverage Map

Status: architecture coverage map
Last updated: 2026-06-03

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
| Application acceptance | staff-actor | application review service methods | character status, mapped claims, reserve outcomes, revision notes, notifications where applicable | `tests/test_forum_slice.py::test_application_review_flags_mapped_claim_conflicts_before_accept`; `tests/test_forum_slice.py::test_application_start_form_creates_draft_face_and_review_room` | partial; claim-conflict guard covered, late acceptance rollback not isolated |
| Wanted interest | explicit-character or prospective-character | wanted service path | interest row, prospective note, notification or queue side effects | `tests/test_forum_slice.py::test_wanted_hooks_accept_prospective_character_interest`; `tests/test_tenant_repository.py::test_community_access_requests_are_tenant_scoped` | partial; duplicate and privacy proof exists, rollback injection still not isolated |
| Plotting room start | owner/staff handoff | plotting service/repository transaction | plotting room, participants, source wanted interest, notifications | `tests/test_forum_slice.py::test_plotting_rooms_start_from_wanted_interest`; `tests/test_forum_slice.py::test_plotting_room_notifications_do_not_leak_to_non_participants` | partial; visibility covered, start-room rollback injection still not isolated |
| Plotting to scene | owner/staff handoff | `AppServices.start_scene_from_plotting_room()` plotting service/repository transaction | thread, opening post, room-scene attachment, notifications | `tests/test_forum_slice.py::test_plotting_room_scene_handoff_rolls_back_on_attach_failure`; `tests/test_forum_slice.py::test_plotting_room_plan_can_turn_into_scene` | covered for rollback and happy path |
| Program Blueprint apply | staff-actor/director | `services.blueprints.apply_blueprint()` repository transaction | boards, materials, facets, launch/setup rows, hydration actions | `tests/test_program_blueprints.py::test_program_blueprint_apply_gate_rolls_back_transaction_probe`; `tests/test_program_blueprints.py::test_program_blueprint_apply_gate_rolls_back_nested_repository_writes`; `tests/test_program_blueprints.py::test_program_blueprint_apply_rejects_non_staff_before_transaction`; `tests/test_program_blueprints.py::test_program_blueprint_apply_rejects_stale_fingerprint_before_transaction` | covered for rollback, nested repository write recovery, and pre-transaction gates |
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

- Application acceptance needs a late-failure rollback test after mapped claims
  or notifications begin.
- Wanted interest and plotting-room start need dedicated rollback probes beyond
  current duplicate, visibility, and notification privacy proof.
- Claim/reserve maintenance should name duplicate behavior and rollback proof
  when those workflows become broader than single-row updates.
- Notification fanout proof exists for thread replies; new notification target
  families should add their own rollback or visibility proof before affecting
  shell counts.

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
