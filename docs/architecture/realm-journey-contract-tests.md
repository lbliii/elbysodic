# Realm Journey Contract Tests

Elbysodic's realm journey proof is a rendered and service contract pack, not a
single browser scenario. The pack ties public discovery, account-visitor access,
invite acceptance, first-face onboarding, application and claim review, scene
posting, staff controls, notifications, inactive membership denial, and
cross-community recovery into one regression surface.

## Current Coverage Matrix

| Journey leg | Audience | Primary proof |
|---|---|---|
| Public discovery and tenant preview | signed-out visitor | `test_production_routes_require_session`, `test_production_signed_out_public_realm_keeps_anonymous_posture`, `test_production_release_smoke_core_user_flow` |
| Account visitor access request | signed-in account without membership | `test_production_signed_in_non_member_sees_account_posture_on_public_realm`, `test_production_signed_in_duplicate_access_request_links_existing_record` |
| Invite acceptance and first face | director, invited writer, faceless member | `test_director_invites_writer_through_first_face_handoff`, `test_invited_writer_without_first_face_continues_to_application_form`, `test_invitation_acceptance_uses_writer_activation_handoff` |
| Existing-account cross-realm invite | global account with another membership | `test_invitation_acceptance_keeps_existing_account_memberships_local` |
| Applications and claims | member, applicant, staff | `test_applications_desk_tracks_character_statuses`, `test_rendered_surface_contract_parity_across_realm_viewers` |
| Posting and active face | character-backed writer | `test_production_release_smoke_core_user_flow`, `test_tenant_prefixed_thread_routes_scope_composer_redirects` |
| Notifications and continuation | member, faceless member, staff | `test_rendered_surface_contract_parity_across_realm_viewers`, `test_notifications_track_watched_thread_replies_and_open_read_state`, `test_faceless_writer_does_not_count_unowned_character_notifications` |
| Staff/director controls | current-community staff and director | `test_rendered_surface_contract_parity_across_realm_viewers`, `test_director_studio_surfaces_community_production_work` |
| Inactive and cross-community recovery | inactive member, cross-community viewer | `test_request_identity_rejects_inactive_membership_viewer`, `test_rendered_surface_contract_parity_across_realm_viewers`, `test_prefixed_cross_realm_recovery_switches_to_target_tenant` |

## Required Assertions

The pack should keep asserting all of these conditions:

- public and account visitors see public-safe realm material without active
  face, unread count, staff queue, private notes, or mutating controls
- access requests do not grant membership, role, face, session, reserve, claim,
  or invitation state
- invite acceptance creates or reuses the global account while creating only
  the invited community's membership and optional first face
- faceless members are routed toward first-face/application work before posting
  and notification continuation can expose character-backed state
- posting, notifications, and shell counts stay tied to the selected
  membership and active face in the current community
- staff/director controls render only for current-community capability holders
- inactive and cross-community viewers fail closed or enter recovery without
  private rows, staff notes, or mutating controls

When a journey leg changes, update the rendered test and this matrix in the
same PR so the contract remains discoverable.
