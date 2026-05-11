"""Service-owned route recovery policy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from elbysodic.domain.models import Community
from elbysodic.services.read_models import ForumView

RecoveryKind = Literal[
    "character",
    "application",
    "wanted",
    "material",
    "plotting",
    "board",
    "thread",
]


class RecoveryRepository(Protocol):
    def list_character_communities_by_slug(self, slug: str) -> list[Community]: ...

    def list_wanted_ad_communities_by_slug(self, slug: str) -> list[Community]: ...

    def list_published_material_communities_by_slug(self, slug: str) -> list[Community]: ...

    def list_board_communities_by_slug(self, slug: str) -> list[Community]: ...

    def list_thread_communities_by_slug(
        self,
        board_slug: str,
        thread_slug: str,
    ) -> list[Community]: ...


@dataclass(frozen=True, slots=True)
class RecoveryLink:
    label: str
    href: str
    variant: str = "secondary"


@dataclass(frozen=True, slots=True)
class RecoverySwitchAction:
    label: str
    membership_id: int
    character_id: int
    next_url: str
    community_name: str


@dataclass(frozen=True, slots=True)
class RecoveryView:
    kicker: str
    title: str
    summary: str
    detail: str
    links: list[RecoveryLink]
    switch_action: RecoverySwitchAction | None = None


def recovery_view(
    repo: RecoveryRepository,
    viewer: ForumView,
    *,
    kind: RecoveryKind,
    slug: str,
) -> RecoveryView:
    route = _route_for_kind(kind)
    communities = [
        community
        for community in route.communities(repo, slug)
        if community.id != viewer.community.id
    ]
    target = _first_switchable_community(viewer, communities)
    switch_action = (
        _switch_action(viewer, target, route.target_path(slug)) if target is not None else None
    )
    labels = route.labels
    if target is not None:
        title = f"That {labels.object_label} lives in {target.name}."
        summary = (
            f"{slug} is not part of {viewer.community.name}, but it exists in another "
            "program on this studio network."
        )
        detail = "Switch realms to open it there, or return to this program's local lane."
    elif communities:
        title = f"That {labels.object_label} is not in {viewer.community.name}."
        summary = (
            f"We could not find {slug} inside the current realm. It may belong to a "
            "program your current membership cannot enter."
        )
        detail = "Use the local hub to keep browsing here."
    else:
        title = f"That {labels.object_label} is not in {viewer.community.name}."
        summary = (
            f"We could not find {slug} inside the current realm. It may have moved, "
            "changed slug, or belonged to an older preview database."
        )
        detail = "Use the local hub to find the current version."
    return RecoveryView(
        kicker=labels.kicker,
        title=title,
        summary=summary,
        detail=detail,
        links=_fallback_links(route),
        switch_action=switch_action,
    )


def recover_next_url(repo: RecoveryRepository, identity: object, next_url: str) -> str:
    community_id = getattr(identity, "community_id", 0)
    community_slug = str(getattr(identity, "community_slug", "") or "")
    tenant_slug, local_next_url = _tenant_and_local_next_url(next_url)
    kind_and_slug = _kind_and_slug_for_next_url(local_next_url)
    if kind_and_slug is None:
        return next_url
    kind, slug = kind_and_slug
    route = _route_for_kind(kind)
    if tenant_slug is not None and tenant_slug != community_slug:
        fallback = route.fallback_path
        return _scoped_path(community_slug, fallback) if community_slug else fallback
    for community in route.communities(repo, slug):
        if community.id == community_id:
            return next_url
    fallback = route.fallback_path
    return (
        _scoped_path(community_slug, fallback)
        if tenant_slug is not None and community_slug
        else fallback
    )


@dataclass(frozen=True, slots=True)
class _KindLabels:
    kicker: str
    object_label: str


@dataclass(frozen=True, slots=True)
class _RecoveryRoute:
    kind: RecoveryKind
    labels: _KindLabels
    fallback_label: str
    fallback_path: str
    target_path: Callable[[str], str]
    communities: Callable[[RecoveryRepository, str], list[Community]]
    match_next_path: Callable[[str], str | None]


def _character_communities(repo: RecoveryRepository, slug: str) -> list[Community]:
    return repo.list_character_communities_by_slug(slug)


def _wanted_communities(repo: RecoveryRepository, slug: str) -> list[Community]:
    return repo.list_wanted_ad_communities_by_slug(slug)


def _material_communities(repo: RecoveryRepository, slug: str) -> list[Community]:
    return repo.list_published_material_communities_by_slug(slug)


def _plotting_communities(_repo: RecoveryRepository, _slug: str) -> list[Community]:
    return []


def _board_communities(repo: RecoveryRepository, slug: str) -> list[Community]:
    return repo.list_board_communities_by_slug(slug)


def _thread_communities(repo: RecoveryRepository, slug: str) -> list[Community]:
    board_slug, separator, thread_slug = slug.partition("/")
    if not separator or not board_slug or not thread_slug:
        return []
    return repo.list_thread_communities_by_slug(board_slug, thread_slug)


def _first_path_part_after(prefix: str) -> Callable[[str], str | None]:
    def match(path: str) -> str | None:
        if not path.startswith(prefix):
            return None
        slug = path.removeprefix(prefix).split("/", 1)[0]
        return slug or None

    return match


def _board_next_slug(path: str) -> str | None:
    if not path.startswith("/boards/"):
        return None
    parts = path.removeprefix("/boards/").split("/")
    if len(parts) >= 3 and parts[1] == "threads":
        return None
    return parts[0] or None


def _thread_next_slug(path: str) -> str | None:
    if not path.startswith("/boards/"):
        return None
    parts = path.removeprefix("/boards/").split("/")
    if len(parts) < 3 or parts[1] != "threads" or parts[2] == "new":
        return None
    return f"{parts[0]}/{parts[2]}" if parts[0] and parts[2] else None


def _thread_target_path(slug: str) -> str:
    board_slug, _, thread_slug = slug.partition("/")
    return f"/boards/{board_slug}/threads/{thread_slug}"


_RECOVERY_ROUTES: tuple[_RecoveryRoute, ...] = (
    _RecoveryRoute(
        kind="application",
        labels=_KindLabels("Application room", "face"),
        fallback_label="Back to Applications",
        fallback_path="/applications",
        target_path=lambda slug: f"/applications/{slug}",
        communities=_character_communities,
        match_next_path=_first_path_part_after("/applications/"),
    ),
    _RecoveryRoute(
        kind="character",
        labels=_KindLabels("Roster", "face"),
        fallback_label="Open Roster",
        fallback_path="/characters",
        target_path=lambda slug: f"/characters/{slug}",
        communities=_character_communities,
        match_next_path=_first_path_part_after("/characters/"),
    ),
    _RecoveryRoute(
        kind="wanted",
        labels=_KindLabels("Wanted hook", "wanted hook"),
        fallback_label="Open Wanted",
        fallback_path="/wanted",
        target_path=lambda slug: f"/wanted/{slug}",
        communities=_wanted_communities,
        match_next_path=_first_path_part_after("/wanted/"),
    ),
    _RecoveryRoute(
        kind="material",
        labels=_KindLabels("Guidebook", "world material"),
        fallback_label="Open Guidebook",
        fallback_path="/world",
        target_path=lambda slug: f"/world/{slug}",
        communities=_material_communities,
        match_next_path=_first_path_part_after("/world/"),
    ),
    _RecoveryRoute(
        kind="plotting",
        labels=_KindLabels("Plotting room", "planning room"),
        fallback_label="Open Plotting",
        fallback_path="/plotting",
        target_path=lambda slug: f"/plotting/{slug}",
        communities=_plotting_communities,
        match_next_path=_first_path_part_after("/plotting/"),
    ),
    _RecoveryRoute(
        kind="thread",
        labels=_KindLabels("Thread", "thread"),
        fallback_label="Open World Map",
        fallback_path="/locations",
        target_path=_thread_target_path,
        communities=_thread_communities,
        match_next_path=_thread_next_slug,
    ),
    _RecoveryRoute(
        kind="board",
        labels=_KindLabels("Board", "board"),
        fallback_label="Open World Map",
        fallback_path="/locations",
        target_path=lambda slug: f"/boards/{slug}",
        communities=_board_communities,
        match_next_path=_board_next_slug,
    ),
)

_RECOVERY_ROUTES_BY_KIND = {route.kind: route for route in _RECOVERY_ROUTES}


def _first_switchable_community(
    viewer: ForumView,
    communities: list[Community],
) -> Community | None:
    community_ids = {community.id for community in communities}
    for option in viewer.identity_options:
        if option.community.id in community_ids:
            return option.community
    return None


def _switch_action(
    viewer: ForumView,
    target: Community,
    next_url: str,
) -> RecoverySwitchAction | None:
    for option in viewer.identity_options:
        if option.community.id != target.id:
            continue
        return RecoverySwitchAction(
            label=f"Switch to {option.community.name}",
            membership_id=option.membership.id,
            character_id=option.current_character.id if option.current_character else 0,
            next_url=_scoped_path(target.slug, next_url),
            community_name=option.community.name,
        )
    return None


def _fallback_links(route: _RecoveryRoute) -> list[RecoveryLink]:
    fallback = route.fallback_path
    links = [RecoveryLink(route.fallback_label, fallback, "primary")]
    if fallback != "/desk":
        links.append(RecoveryLink("Open Writer Desk", "/desk"))
    return links


def _kind_and_slug_for_next_url(next_url: str) -> tuple[RecoveryKind, str] | None:
    normalized = next_url.split("?", 1)[0].rstrip("/")
    if normalized == "/applications/new":
        return None
    for route in _RECOVERY_ROUTES:
        slug = route.match_next_path(normalized)
        if slug:
            return route.kind, slug
    return None


def _route_for_kind(kind: RecoveryKind) -> _RecoveryRoute:
    return _RECOVERY_ROUTES_BY_KIND[kind]


def _tenant_and_local_next_url(next_url: str) -> tuple[str | None, str]:
    path, separator, suffix = next_url.partition("?")
    split = _split_tenant_path(path)
    if split is None:
        return None, next_url
    tenant_slug, local_path = split
    return tenant_slug, f"{local_path}{separator}{suffix}" if separator else local_path


def _scoped_path(tenant_slug: str, path: str) -> str:
    local_path = path if path.startswith("/") else f"/{path}"
    return f"/c/{tenant_slug}{local_path}"


def _split_tenant_path(path: str) -> tuple[str, str] | None:
    parts = path.split("/", 3)
    if len(parts) < 3 or parts[1] != "c" or not parts[2]:
        return None
    local = "/" if len(parts) == 3 else f"/{parts[3]}"
    return parts[2], local
