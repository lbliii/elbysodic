from __future__ import annotations

import elbysodic.domain as domain


def test_domain_exports_current_first_class_primitives() -> None:
    exported = set(domain.__all__)

    assert {
        "ApplicationFieldValue",
        "ApplicationTemplateField",
        "Board",
        "Character",
        "CharacterApplication",
        "CharacterApplicationEvent",
        "CharacterClaim",
        "CharacterPlotHook",
        "CharacterPlotHookInterest",
        "CharacterReserve",
        "ClaimType",
        "Community",
        "CommunityMembership",
        "CommunityTheme",
        "Facet",
        "FacetGroup",
        "Material",
        "Notification",
        "PlottingRoom",
        "PlottingRoomMessage",
        "PlottingRoomParticipant",
        "Post",
        "PostRevision",
        "RealmInteraction",
        "RealmInteractionAnswer",
        "RealmInteractionOption",
        "RealmInteractionQuestion",
        "RealmInteractionResponse",
        "Role",
        "SidebarSectionConfig",
        "Thread",
        "ThreadParticipant",
        "ThreadWatch",
        "User",
        "UserSession",
        "WantedAd",
        "WantedAdInterest",
    }.issubset(exported)
