"""Service-owned route recovery policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from elbysodic.domain.models import Community
from elbysodic.services.read_models import ForumView

RecoveryKind = Literal["character", "application", "wanted", "material", "plotting"]


class RecoveryRepository(Protocol):
    def list_character_communities_by_slug(self, slug: str) -> list[Community]: ...

    def list_wanted_ad_communities_by_slug(self, slug: str) -> list[Community]: ...

    def list_published_material_communities_by_slug(self, slug: str) -> list[Community]: ...


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
    communities = [
        community
        for community in _communities_for_slug(repo, kind, slug)
        if community.id != viewer.community.id
    ]
    target = _first_switchable_community(viewer, communities)
    switch_action = (
        _switch_action(viewer, target, _target_path(kind, slug)) if target is not None else None
    )
    labels = _kind_labels(kind)
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
        links=_fallback_links(kind),
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
    if tenant_slug is not None and tenant_slug != community_slug:
        fallback = _fallback_path(kind)
        return _scoped_path(community_slug, fallback) if community_slug else fallback
    for community in _communities_for_slug(repo, kind, slug):
        if community.id == community_id:
            return next_url
    fallback = _fallback_path(kind)
    return (
        _scoped_path(community_slug, fallback)
        if tenant_slug is not None and community_slug
        else fallback
    )


@dataclass(frozen=True, slots=True)
class _KindLabels:
    kicker: str
    object_label: str


def _kind_labels(kind: RecoveryKind) -> _KindLabels:
    match kind:
        case "application":
            return _KindLabels("Application room", "face")
        case "character":
            return _KindLabels("Roster", "face")
        case "wanted":
            return _KindLabels("Wanted hook", "wanted hook")
        case "material":
            return _KindLabels("Guidebook", "world material")
        case "plotting":
            return _KindLabels("Plotting room", "planning room")


def _communities_for_slug(
    repo: RecoveryRepository,
    kind: RecoveryKind,
    slug: str,
) -> list[Community]:
    match kind:
        case "application" | "character":
            return repo.list_character_communities_by_slug(slug)
        case "wanted":
            return repo.list_wanted_ad_communities_by_slug(slug)
        case "material":
            return repo.list_published_material_communities_by_slug(slug)
        case "plotting":
            return []


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


def _fallback_links(kind: RecoveryKind) -> list[RecoveryLink]:
    fallback = _fallback_path(kind)
    links = [RecoveryLink(_fallback_label(kind), fallback, "primary")]
    if fallback != "/desk":
        links.append(RecoveryLink("Open Writer Desk", "/desk"))
    return links


def _fallback_label(kind: RecoveryKind) -> str:
    match kind:
        case "application":
            return "Back to Applications"
        case "character":
            return "Open Roster"
        case "wanted":
            return "Open Wanted"
        case "material":
            return "Open Guidebook"
        case "plotting":
            return "Open Plotting"


def _fallback_path(kind: RecoveryKind) -> str:
    match kind:
        case "application":
            return "/applications"
        case "character":
            return "/characters"
        case "wanted":
            return "/wanted"
        case "material":
            return "/world"
        case "plotting":
            return "/plotting"


def _target_path(kind: RecoveryKind, slug: str) -> str:
    match kind:
        case "application":
            return f"/applications/{slug}"
        case "character":
            return f"/characters/{slug}"
        case "wanted":
            return f"/wanted/{slug}"
        case "material":
            return f"/world/{slug}"
        case "plotting":
            return f"/plotting/{slug}"


def _kind_and_slug_for_next_url(next_url: str) -> tuple[RecoveryKind, str] | None:
    normalized = next_url.split("?", 1)[0].rstrip("/")
    if normalized == "/applications/new":
        return None
    patterns: tuple[tuple[str, RecoveryKind], ...] = (
        ("/applications/", "application"),
        ("/characters/", "character"),
        ("/wanted/", "wanted"),
        ("/world/", "material"),
    )
    for prefix, kind in patterns:
        if not normalized.startswith(prefix):
            continue
        slug = normalized.removeprefix(prefix).split("/", 1)[0]
        if slug:
            return kind, slug
    return None


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
