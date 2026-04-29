"""Community resolution primitives.

The MVP always resolves the seeded default community. Routes and services still
receive this context explicitly so the code stays tenant-aware.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_COMMUNITY_ID = 1
DEFAULT_COMMUNITY_SLUG = "default"


@dataclass(frozen=True, slots=True)
class CommunityContext:
    """The tenant scope attached to a request."""

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
    """Resolve the current community for a request.

    The argument is accepted now so route handlers can call the same function
    after hosted multi-tenancy adds host, subdomain, or path-prefix routing.
    """

    _ = request
    return CommunityContext()
