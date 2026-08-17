"""Small domain identity context records.

Runtime request identity is resolved in the service/web boundary because it
needs repository access for tenant prefixes, hosts, sessions, memberships, and
inactive-membership checks. This module only owns typed context records and the
development/default constants shared by tests and seed data.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_COMMUNITY_ID = 1
DEFAULT_COMMUNITY_SLUG = "x-men-apocalypse"


@dataclass(frozen=True, slots=True)
class CommunityContext:
    """The tenant scope attached to a request.

    Field defaults exist for seed data and tests. They are not a request minting
    path. Web request identity uses `AppServices.for_request()` and
    `RequestIdentityResolver` only.
    """

    community_id: int = DEFAULT_COMMUNITY_ID
    slug: str = DEFAULT_COMMUNITY_SLUG


@dataclass(frozen=True, slots=True)
class RequestIdentityContext:
    """Resolved studio-network identity for a request."""

    community_id: int
    user_id: int
    membership_id: int
    community_slug: str = DEFAULT_COMMUNITY_SLUG


def resolve_current_community(request: object | None = None) -> CommunityContext:
    """Return the legacy default community context.

    This helper ignores the request and returns `CommunityContext()` defaults.
    It is not a request minting path. Web routes must use
    `AppServices.for_request()` and `RequestIdentityResolver` instead. Seed
    and session code may still use `DEFAULT_COMMUNITY_SLUG` /
    `DEFAULT_COMMUNITY_ID` directly.
    """

    _ = request
    return CommunityContext()
