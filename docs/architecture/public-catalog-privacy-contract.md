# Public Catalog Privacy Contract

Writer Network catalog and search surfaces use service-owned
`PublicCatalogCard` read models. Templates may render catalog cards and suppress
actions for the current viewer, but they must not infer public visibility,
request-access paths, ranking, or searchable posture from private membership
state.

## Viewer Modes

The public catalog contract is the same for these viewer modes:

- `signed_out`
- `account_visitor`
- `same_community_member`
- `staff`
- `inactive_member`
- `cross_community_viewer`

Signed-in members and staff may receive separate Network return-path or Studio
Network read models elsewhere in the shell. Those continuation lanes must not
be mixed into public catalog cards.

## Searchable Signals

Public catalog search and browse may use only these service-owned public
signals:

- `community_name`
- `published_premise_title`
- `published_premise_summary`
- `published_current_event_title`
- `published_current_event_summary`
- `public_discovery_profile`
- `public_discovery_tags`
- `open_wanted_count`
- `published_application_material_count`
- `public_claim_type_count`
- `public_theme_preview`
- `request_access_href`
- `invite_posture_label`

These fields answer public fit questions: premise, play engine, lore aperture,
access posture, first-face/application posture, age/content rating, activity
pace, roster posture, current chapter, wanted pressure, and public entry path.
They are editorial discovery signals, not generic marketplace metrics.

## Excluded Signals

Public catalog cards and search text must not include:

- `membership`
- `role`
- `current_character`
- `active_face`
- `unread_notification_count`
- `application_count`
- `plotting_room_count`
- `staff_queue`
- `staff_signal`
- `private_note`
- `private_count`
- `draft_material`
- `draft_application`
- `private_plotting_room`
- `backstage_realm`
- `cross_community_private_state`
- `is_current`

Backstage or invite-only realms remain outside public catalog/search until the
service read model says the realm is public-preview ready. Draft materials,
private scene or plotting state, staff queues, active-face continuation, unread
counts, another writer's applications, and cross-community records must not be
used for public ranking, filtering, snippets, or action availability.

## Batching Contract

Catalog generation should stay bounded for realistic multi-realm fixtures by
using batch repository reads:

- `list_materials_for_communities`
- `list_discovery_profiles_for_communities`
- `list_discovery_tags_for_communities`
- `network_program_counts`
- `public_scene_hub_community_ids`
- `default_themes_for_communities`

If a new filter or ranking signal cannot be loaded through a tenant-aware batch
read, do not add it to public catalog search until the repository contract and
query-budget proof move with it.

## Proof

Current proof lives in:

- `tests/test_public_catalog_privacy_contract.py`
- `test_public_catalog_read_models_are_public_only`
- `test_public_catalog_helpers_reject_member_network_read_models`
- `test_public_network_catalog_hides_member_state`
- `test_scaled_signed_in_network_stays_within_batched_query_budget`
- `test_production_signed_in_non_member_sees_account_posture_on_public_realm`
- `test_public_realm_gateway_contract_uses_fallbacks_and_denies_backstage`
