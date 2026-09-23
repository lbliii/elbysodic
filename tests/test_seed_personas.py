from __future__ import annotations

from elbysodic.db.seed import resolve_seed_persona
from elbysodic.services import create_services

X_MEN_STAFF_CAPABILITIES = frozenset(
    {
        "manage_applications",
        "manage_casting",
        "manage_navigation",
        "manage_threads",
        "manage_world",
    }
)


def test_xmen_moderator_seed_purpose_and_capabilities_match() -> None:
    services = create_services(path=":memory:")
    try:
        moderator = resolve_seed_persona(services.repo, "xmen_mod")
        writer = resolve_seed_persona(services.repo, "xmen_writer")

        assert moderator.persona.purpose == (
            "Full staff QA across application review, claims/reserves, board navigation, "
            "thread lifecycle, and world/Studio management."
        )
        assert moderator.role.capabilities == X_MEN_STAFF_CAPABILITIES
        assert writer.role.capabilities.isdisjoint(X_MEN_STAFF_CAPABILITIES)
    finally:
        services.close()
