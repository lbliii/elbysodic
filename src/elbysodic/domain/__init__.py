"""Domain models and community context for Elbysodic."""

from elbysodic.domain.boards import (
    BOARD_KINDS,
    BoardKind,
    is_community_board,
    is_desk_board,
    is_location_board,
    normalize_board_kind,
)
from elbysodic.domain.context import DEFAULT_COMMUNITY_ID, CommunityContext
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Notification,
    Post,
    Role,
    Thread,
    ThreadParticipant,
    ThreadWatch,
    User,
)

__all__ = [
    "BOARD_KINDS",
    "DEFAULT_COMMUNITY_ID",
    "Board",
    "BoardKind",
    "Character",
    "Community",
    "CommunityContext",
    "CommunityMembership",
    "Notification",
    "Post",
    "Role",
    "Thread",
    "ThreadParticipant",
    "ThreadWatch",
    "User",
    "is_community_board",
    "is_desk_board",
    "is_location_board",
    "normalize_board_kind",
]
