"""Community-scoped staff capability vocabulary."""

from __future__ import annotations

STAFF_CAPABILITIES: frozenset[str] = frozenset(
    {
        "manage_applications",
        "manage_casting",
        "manage_navigation",
        "manage_threads",
        "manage_world",
    }
)
