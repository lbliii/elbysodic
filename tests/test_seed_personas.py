from __future__ import annotations

from elbysodic.db.seed import resolve_seed_persona, seed_demo_forum
from elbysodic.services import create_services

X_MEN_ALL_STAFF_CAPABILITIES = frozenset(
    {
        "manage_applications",
        "manage_casting",
        "manage_navigation",
        "manage_threads",
        "manage_world",
    }
)
X_MEN_MODERATOR_CAPABILITIES = frozenset({"manage_threads"})


def test_xmen_moderator_seed_purpose_and_capabilities_match() -> None:
    services = create_services(path=":memory:")
    try:
        moderator = resolve_seed_persona(services.repo, "xmen_mod")
        writer = resolve_seed_persona(services.repo, "xmen_writer")
        staff = resolve_seed_persona(services.repo, "xmen_staff")

        assert moderator.persona.purpose == (
            "Thread moderation QA on readable boards: pin, lock, and move threads; "
            "update scene status and details."
        )
        assert moderator.persona.default_path == "/boards/med-bay/threads/med-bay-lights"
        assert moderator.role.is_admin is False
        assert moderator.role.capabilities == X_MEN_MODERATOR_CAPABILITIES
        assert writer.role.capabilities.isdisjoint(X_MEN_ALL_STAFF_CAPABILITIES)
        assert staff.role.is_admin is True
        assert staff.role.capabilities == X_MEN_ALL_STAFF_CAPABILITIES
    finally:
        services.close()


def test_seed_demo_forum_reconciles_an_existing_broad_moderator_role() -> None:
    services = create_services(path=":memory:")
    try:
        moderator = resolve_seed_persona(services.repo, "xmen_mod")
        services.repo.update_role(
            moderator.community.id,
            moderator.role.id,
            name="Moderator",
            is_admin=True,
            capabilities=X_MEN_ALL_STAFF_CAPABILITIES,
        )

        seed_demo_forum(services.repo)

        reconciled = resolve_seed_persona(services.repo, "xmen_mod")
        assert reconciled.role.is_admin is False
        assert reconciled.role.capabilities == X_MEN_MODERATOR_CAPABILITIES
    finally:
        services.close()
