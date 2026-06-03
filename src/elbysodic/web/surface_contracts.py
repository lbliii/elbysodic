"""Rendered surface contract registry.

The registry is executable documentation for route families that must keep
privacy, counts, and action availability owned by services before templates
render them.
"""

from __future__ import annotations

from dataclasses import dataclass
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
    ),
    SurfaceContract(
        key="thread_and_posting",
        route_family="/boards/{board} and /boards/{board}/threads/{thread}",
        page_path="src/elbysodic/web/pages/boards/{board_slug}/page.py",
        service_calls=("services.board_page(",),
        read_models=("BoardPage", "ThreadView", "PostView"),
        viewer_modes=("member", "owner", "staff", "faceless", "cross_tenant"),
        dimensions=(
            "shell_count",
            "page_list",
            "detail_view",
            "action_availability",
            "notification_visibility",
            "recovery",
        ),
        privacy_matrix_label="/boards/{board}",
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
    ),
)


def surface_contracts_by_key() -> dict[str, SurfaceContract]:
    return {contract.key: contract for contract in SURFACE_CONTRACTS}
