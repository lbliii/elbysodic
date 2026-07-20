"""Rendered surface contract registry.

The registry is executable documentation for route families that must keep
privacy, counts, and action availability owned by services before templates
render them.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

type ViewerMode = Literal[
    "public",
    "account_visitor",
    "member",
    "owner",
    "staff",
    "director",
    "inactive",
    "faceless",
    "cross_tenant",
]

type SurfaceDimension = Literal[
    "shell_count",
    "page_list",
    "detail_view",
    "action_availability",
    "notification_visibility",
    "recovery",
    "diagnostics",
]


@dataclass(frozen=True, slots=True)
class SurfaceContract:
    key: str
    route_family: str
    page_path: str
    service_calls: tuple[str, ...]
    read_models: tuple[str, ...]
    viewer_modes: tuple[ViewerMode, ...]
    dimensions: tuple[SurfaceDimension, ...]
    privacy_matrix_label: str
    proof_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SurfaceContractValidationIssue:
    code: str
    contract_key: str
    message: str


SURFACE_CONTRACTS: tuple[SurfaceContract, ...] = (
    SurfaceContract(
        key="realm_home",
        route_family="/ and /c/{community}/",
        page_path="src/elbysodic/web/pages/page.py",
        service_calls=("services.realm_home()",),
        read_models=("RealmHome", "PublicRealmGateway", "NetworkHome"),
        viewer_modes=("public", "account_visitor", "member", "staff", "cross_tenant"),
        dimensions=("shell_count", "page_list", "action_availability", "recovery"),
        privacy_matrix_label="/c/{community}/",
        proof_references=(
            "tests/test_forum_slice.py::test_rendered_surface_contract_parity_across_realm_viewers",
            "tests/test_web_security.py::test_production_signed_out_public_realm_keeps_anonymous_posture",
        ),
    ),
    SurfaceContract(
        key="claims_directory",
        route_family="/claims",
        page_path="src/elbysodic/web/pages/claims/page.py",
        service_calls=("services.claims_page(",),
        read_models=("ClaimsDirectory",),
        viewer_modes=("member", "staff", "director", "cross_tenant"),
        dimensions=("page_list", "detail_view", "action_availability"),
        privacy_matrix_label="/claims",
        proof_references=(
            "tests/test_forum_slice.py::test_claims_directory_renders_seeded_claims_and_studio_summary",
            "tests/test_forum_slice.py::test_rendered_surface_contract_parity_across_realm_viewers",
        ),
    ),
    SurfaceContract(
        key="roster",
        route_family="/characters and /characters/{character}",
        page_path="src/elbysodic/web/pages/characters/page.py",
        service_calls=("services.character_roster_page(",),
        read_models=("CharacterRosterDashboard", "CharacterProfile"),
        viewer_modes=("member", "owner", "staff", "inactive", "cross_tenant"),
        dimensions=("page_list", "detail_view", "action_availability", "recovery"),
        privacy_matrix_label="/members",
        proof_references=(
            "tests/test_forum_slice.py::test_character_roster_and_profiles_are_community_scoped",
            "tests/test_forum_slice.py::test_rendered_surface_contract_parity_across_realm_viewers",
        ),
    ),
    SurfaceContract(
        key="thread_and_posting",
        route_family=(
            "/boards/{board}, /boards/{board}/threads/{thread}, and "
            "/c/{community}/boards/{board}/threads/{thread}"
        ),
        page_path="src/elbysodic/web/pages/boards/{board_slug}/threads/{thread_slug}/page.py",
        service_calls=(
            "services.read_scene_context(",
            "services.public_scene_preview(",
        ),
        read_models=("ThreadView", "PostView", "PublicScenePreview"),
        viewer_modes=(
            "public",
            "account_visitor",
            "member",
            "owner",
            "staff",
            "faceless",
            "cross_tenant",
        ),
        dimensions=(
            "shell_count",
            "page_list",
            "detail_view",
            "action_availability",
            "notification_visibility",
            "recovery",
        ),
        privacy_matrix_label="/boards/{board}",
        proof_references=(
            "tests/test_forum_slice.py::test_forum_pages_render_seeded_boards_and_thread",
            "tests/test_forum_slice.py::test_rendered_surface_contract_parity_across_realm_viewers",
            "tests/test_forum_slice.py::test_reply_notification_failure_rolls_back_post",
            "tests/test_web_security.py::test_production_signed_out_public_scene_stops_after_four_posts",
            "tests/test_web_security.py::test_production_public_scene_route_fails_closed_for_member_only_and_private_scenes",
        ),
    ),
    SurfaceContract(
        key="wanted",
        route_family="/wanted and /c/{community}/wanted",
        page_path="src/elbysodic/web/pages/wanted/page.py",
        service_calls=("services.wanted_ads()",),
        read_models=("WantedBoard", "WantedAdDetail"),
        viewer_modes=("public", "account_visitor", "member", "owner", "staff", "cross_tenant"),
        dimensions=("page_list", "detail_view", "action_availability", "notification_visibility"),
        privacy_matrix_label="/c/{community}/wanted",
        proof_references=(
            "tests/test_forum_slice.py::test_public_wanted_routes_hide_non_open_hooks",
            "tests/test_forum_slice.py::test_wanted_ads_render_board_detail_and_character_hub",
        ),
    ),
    SurfaceContract(
        key="plotting",
        route_family="/plotting and /plotting/{room}",
        page_path="src/elbysodic/web/pages/plotting/page.py",
        service_calls=("services.plotting_desk()",),
        read_models=("PlottingDesk", "PlottingRoomView"),
        viewer_modes=("member", "owner", "staff", "inactive", "cross_tenant"),
        dimensions=("page_list", "detail_view", "action_availability", "notification_visibility"),
        privacy_matrix_label="/plotting",
        proof_references=(
            "tests/test_forum_slice.py::test_tenant_prefixed_plotting_room_id_does_not_leak_cross_realm_room",
            "tests/test_forum_slice.py::test_plotting_room_notifications_do_not_leak_to_non_participants",
        ),
    ),
    SurfaceContract(
        key="applications",
        route_family="/applications and /applications/{character}",
        page_path="src/elbysodic/web/pages/applications/page.py",
        service_calls=("services.applications_desk()",),
        read_models=("ApplicationsDesk", "ApplicationReviewRoom"),
        viewer_modes=("member", "owner", "staff", "faceless", "cross_tenant"),
        dimensions=("page_list", "detail_view", "action_availability", "recovery"),
        privacy_matrix_label="/applications",
        proof_references=(
            "tests/test_forum_slice.py::test_applications_desk_tracks_character_statuses",
            "tests/test_forum_slice.py::test_application_room_for_other_program_renders_realm_recovery",
        ),
    ),
    SurfaceContract(
        key="notifications",
        route_family="/notifications and shell/sidebar counts",
        page_path="src/elbysodic/web/pages/notifications/page.py",
        service_calls=("services.notification_center()",),
        read_models=("NotificationCenter", "NotificationInboxItem"),
        viewer_modes=("member", "owner", "staff", "inactive", "faceless", "cross_tenant"),
        dimensions=("shell_count", "page_list", "detail_view", "notification_visibility"),
        privacy_matrix_label="/notifications",
        proof_references=(
            "tests/test_notification_contracts.py::test_notification_target_contracts_name_visibility_rules",
            "tests/test_forum_slice.py::test_notifications_track_watched_thread_replies_and_open_read_state",
            "tests/test_forum_slice.py::test_notification_inbox_limit_applies_after_visibility_filtering",
        ),
    ),
    SurfaceContract(
        key="network_catalog",
        route_family="/network",
        page_path="src/elbysodic/web/pages/network/page.py",
        service_calls=("services.network_explore(",),
        read_models=("NetworkExplore", "PublicCatalogCard", "StudioNetworkProgramView"),
        viewer_modes=("public", "account_visitor", "member", "staff", "cross_tenant"),
        dimensions=("page_list", "action_availability", "recovery"),
        privacy_matrix_label="/network",
        proof_references=(
            "tests/test_web_security.py::test_public_network_catalog_hides_membership_and_staff_signals",
            "tests/test_web_security.py::test_network_read_models_split_public_cards_from_viewer_state",
            "tests/test_forum_slice.py::test_network_directory_lists_programs_and_realm_entry_actions",
        ),
    ),
    SurfaceContract(
        key="studio",
        route_family="/studio and /studio/*",
        page_path="src/elbysodic/web/pages/studio/page.py",
        service_calls=("services.director_studio()",),
        read_models=("DirectorStudio",),
        viewer_modes=("member", "staff", "director", "inactive", "cross_tenant"),
        dimensions=("shell_count", "page_list", "detail_view", "action_availability", "recovery"),
        privacy_matrix_label="/studio",
        proof_references=(
            "tests/test_forum_slice.py::test_director_studio_surfaces_community_production_work",
            "tests/test_forum_slice.py::test_studio_launch_moderates_access_requests",
            "tests/test_forum_slice.py::test_realm_launch_room_requires_director_membership",
        ),
    ),
    SurfaceContract(
        key="studio_operations",
        route_family="/studio/operations",
        page_path="src/elbysodic/web/pages/studio/operations/page.py",
        service_calls=("services.director_operations(",),
        read_models=("DirectorOperations", "OperationsInspection"),
        viewer_modes=("member", "staff", "director", "inactive", "cross_tenant"),
        dimensions=("page_list", "action_availability", "diagnostics"),
        privacy_matrix_label="/studio",
        proof_references=(
            "tests/test_forum_slice.py::test_studio_operations_tracks_writer_activation_oversight",
            "tests/test_forum_slice.py::test_studio_operations_hides_review_queue_from_non_staff_members",
        ),
    ),
)


def surface_contracts_by_key() -> dict[str, SurfaceContract]:
    return {contract.key: contract for contract in SURFACE_CONTRACTS}


def validate_surface_contracts(
    contracts: Iterable[SurfaceContract] = SURFACE_CONTRACTS,
    *,
    repo_root: Path | None = None,
    privacy_matrix_text: str | None = None,
) -> tuple[SurfaceContractValidationIssue, ...]:
    """Validate the read-only surface registry against code, proof, and docs."""
    root = repo_root
    matrix = privacy_matrix_text
    if matrix is None and root is not None:
        matrix_path = root / "docs" / "architecture" / "rendered-route-privacy-matrix.md"
        matrix = matrix_path.read_text(encoding="utf-8")

    issues: list[SurfaceContractValidationIssue] = []
    seen_keys: set[str] = set()
    duplicate_keys: set[str] = set()
    contract_tuple = tuple(contracts)

    for contract in contract_tuple:
        if contract.key in seen_keys:
            duplicate_keys.add(contract.key)
        seen_keys.add(contract.key)

    issues.extend(
        [
            SurfaceContractValidationIssue(
                code="duplicate_key",
                contract_key=duplicate_key,
                message=f"{duplicate_key} is registered more than once.",
            )
            for duplicate_key in sorted(duplicate_keys)
        ]
    )

    for contract in contract_tuple:
        issues.extend(_validate_required_fields(contract))

        if matrix is not None and contract.privacy_matrix_label not in matrix:
            issues.append(
                SurfaceContractValidationIssue(
                    code="missing_privacy_matrix_label",
                    contract_key=contract.key,
                    message=(
                        f"{contract.key} references privacy matrix label "
                        f"{contract.privacy_matrix_label!r}, but that label is absent from the "
                        "rendered route privacy matrix."
                    ),
                )
            )

        if root is not None:
            issues.extend(_validate_page_contract(root, contract))
            issues.extend(_validate_proof_references(root, contract))

    return tuple(issues)


def _validate_required_fields(
    contract: SurfaceContract,
) -> tuple[SurfaceContractValidationIssue, ...]:
    missing: list[str] = []
    if not contract.key:
        missing.append("key")
    if not contract.route_family:
        missing.append("route_family")
    if not contract.page_path:
        missing.append("page_path")
    if not contract.service_calls:
        missing.append("service_calls")
    if not contract.read_models:
        missing.append("read_models")
    if not contract.viewer_modes:
        missing.append("viewer_modes")
    if not contract.dimensions:
        missing.append("dimensions")
    if not contract.privacy_matrix_label:
        missing.append("privacy_matrix_label")
    if not contract.proof_references:
        missing.append("proof_references")

    return tuple(
        SurfaceContractValidationIssue(
            code="missing_required_field",
            contract_key=contract.key or "<empty>",
            message=(
                f"{contract.key or '<empty>'} is missing required surface contract field {field}."
            ),
        )
        for field in missing
    )


def _validate_page_contract(
    root: Path,
    contract: SurfaceContract,
) -> tuple[SurfaceContractValidationIssue, ...]:
    page_path = root / contract.page_path
    if not page_path.exists():
        return (
            SurfaceContractValidationIssue(
                code="missing_page",
                contract_key=contract.key,
                message=f"{contract.key} page path does not exist: {contract.page_path}.",
            ),
        )

    source = page_path.read_text(encoding="utf-8")
    return tuple(
        SurfaceContractValidationIssue(
            code="missing_service_call",
            contract_key=contract.key,
            message=(
                f"{contract.key} page {contract.page_path} does not call "
                f"registered service contract {service_call!r}."
            ),
        )
        for service_call in contract.service_calls
        if service_call not in source
    )


def _validate_proof_references(
    root: Path,
    contract: SurfaceContract,
) -> tuple[SurfaceContractValidationIssue, ...]:
    issues: list[SurfaceContractValidationIssue] = []
    for reference in contract.proof_references:
        path_text, separator, symbol = reference.partition("::")
        path = root / path_text
        if not path.exists():
            issues.append(
                SurfaceContractValidationIssue(
                    code="missing_proof_reference",
                    contract_key=contract.key,
                    message=f"{contract.key} proof reference does not exist: {reference}.",
                )
            )
            continue

        if separator and path_text.startswith("tests/"):
            source = path.read_text(encoding="utf-8")
            if f"def {symbol}(" not in source and f"class {symbol}" not in source:
                issues.append(
                    SurfaceContractValidationIssue(
                        code="missing_proof_symbol",
                        contract_key=contract.key,
                        message=(
                            f"{contract.key} proof reference {reference} names a test symbol "
                            "that does not exist."
                        ),
                    )
                )

    return tuple(issues)
