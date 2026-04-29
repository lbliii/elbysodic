"""Request identity resolution for the studio network boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from elbysodic.domain.context import RequestIdentityContext
from elbysodic.domain.models import Community, CommunityMembership, User

DEV_COMMUNITY_HEADER = "x-elbysodic-community"
DEV_MEMBERSHIP_HEADER = "x-elbysodic-membership-id"
DEV_USER_HEADER = "x-elbysodic-user-id"
DEV_IDENTITY_COOKIE = "elbysodic_dev_identity"


class AccessRepository(Protocol):
    def get_community(self, community_id: int) -> Community: ...

    def get_community_by_host(self, host: str) -> Community: ...

    def get_community_by_slug(self, slug: str) -> Community: ...

    def get_membership(self, community_id: int, membership_id: int) -> CommunityMembership: ...

    def get_membership_for_user(self, community_id: int, user_id: int) -> CommunityMembership: ...

    def get_user(self, user_id: int) -> User: ...


@dataclass(frozen=True, slots=True)
class DefaultRequestIdentity:
    community_id: int
    user_id: int
    membership_id: int


class RequestIdentityResolver:
    """Resolve community, user, and membership identity for a request.

    The current app does not have login/session UI yet, so this resolver supports
    explicit development headers and then falls back to the seeded dev identity.
    The boundary checks are intentionally real: the resolved membership must
    belong to both the resolved community and resolved user.
    """

    def __init__(self, repo: AccessRepository, default: DefaultRequestIdentity) -> None:
        self._repo = repo
        self._default = default

    def resolve(self, request: object | None = None) -> RequestIdentityContext:
        cookie_identity = _dev_identity_cookie(request)
        community = self._resolve_community(request)
        user_id = _optional_int_header(request, DEV_USER_HEADER)
        membership_id = _optional_int_header(request, DEV_MEMBERSHIP_HEADER)

        if cookie_identity is not None and cookie_identity.community_id == community.id:
            user_id = user_id if user_id is not None else cookie_identity.user_id
            membership_id = (
                membership_id if membership_id is not None else cookie_identity.membership_id
            )

        if membership_id is not None:
            membership = self._repo.get_membership(community.id, membership_id)
            if user_id is not None and membership.user_id != user_id:
                raise PermissionError(
                    f"membership {membership.id} does not belong to user {user_id}"
                )
            self._repo.get_user(membership.user_id)
            return RequestIdentityContext(
                community_id=community.id,
                community_slug=community.slug,
                user_id=membership.user_id,
                membership_id=membership.id,
            )

        resolved_user_id = user_id if user_id is not None else self._default.user_id
        self._repo.get_user(resolved_user_id)
        membership = self._repo.get_membership_for_user(community.id, resolved_user_id)
        return RequestIdentityContext(
            community_id=community.id,
            community_slug=community.slug,
            user_id=resolved_user_id,
            membership_id=membership.id,
        )

    def _resolve_community(self, request: object | None) -> Community:
        explicit = _optional_header(request, DEV_COMMUNITY_HEADER)
        if explicit:
            if explicit.isdecimal():
                return self._repo.get_community(int(explicit))
            return self._repo.get_community_by_slug(explicit)

        host = _request_host(request)
        if host and not _is_local_dev_host(host):
            return self._repo.get_community_by_host(host)

        cookie_identity = _dev_identity_cookie(request)
        if cookie_identity is not None:
            return self._repo.get_community(cookie_identity.community_id)

        return self._repo.get_community(self._default.community_id)


def _optional_int_header(request: object | None, name: str) -> int | None:
    value = _optional_header(request, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise PermissionError(f"{name} must be an integer") from exc


def _optional_header(request: object | None, name: str) -> str | None:
    headers = getattr(request, "headers", None)
    if headers is None:
        return None
    value = _header_value(headers, name)
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def dev_identity_cookie_value(identity: RequestIdentityContext) -> str:
    return f"{identity.community_id}:{identity.user_id}:{identity.membership_id}"


def _dev_identity_cookie(request: object | None) -> RequestIdentityContext | None:
    cookies = getattr(request, "cookies", None)
    if cookies is None:
        return None
    getter = getattr(cookies, "get", None)
    if getter is None:
        return None
    raw_value = getter(DEV_IDENTITY_COOKIE)
    if raw_value is None:
        return None
    parts = str(raw_value).split(":")
    if len(parts) != 3:
        return None
    try:
        community_id, user_id, membership_id = (int(part) for part in parts)
    except ValueError:
        return None
    return RequestIdentityContext(
        community_id=community_id,
        user_id=user_id,
        membership_id=membership_id,
    )


def _request_host(request: object | None) -> str | None:
    raw_host = _optional_header(request, "host")
    if raw_host is None:
        return None
    return raw_host.rsplit("@", 1)[-1].split(":", 1)[0].lower()


def _header_value(headers: object, name: str) -> object | None:
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    for key in (name, name.lower(), name.title()):
        value = getter(key)
        if value is not None:
            return value
    return None


def _is_local_dev_host(host: str) -> bool:
    return host == "localhost" or host == "::1" or host.startswith("127.")
