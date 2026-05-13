"""Request-local read model lookup helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from elbysodic.domain.models import Character, CommunityMembership, Role


class ReadSessionRepository(Protocol):
    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_membership(self, community_id: int, membership_id: int) -> CommunityMembership: ...

    def get_role(self, community_id: int, role_id: int) -> Role: ...

    def get_thread_read_at(
        self,
        community_id: int,
        thread_id: int,
        membership_id: int,
    ) -> str | None: ...


@dataclass(slots=True)
class ReadModelSession:
    """Cache repeated lookups only for one request/read-model assembly."""

    repo: ReadSessionRepository
    community_id: int
    _characters: dict[int, Character] = field(default_factory=dict)
    _memberships: dict[int, CommunityMembership] = field(default_factory=dict)
    _roles: dict[int, Role] = field(default_factory=dict)
    _thread_reads: dict[tuple[int, int], str | None] = field(default_factory=dict)

    def character(self, character_id: int) -> Character:
        if character_id not in self._characters:
            self._characters[character_id] = self.repo.get_character(
                self.community_id,
                character_id,
            )
        return self._characters[character_id]

    def membership(self, membership_id: int) -> CommunityMembership:
        if membership_id not in self._memberships:
            self._memberships[membership_id] = self.repo.get_membership(
                self.community_id,
                membership_id,
            )
        return self._memberships[membership_id]

    def role(self, role_id: int) -> Role:
        if role_id not in self._roles:
            self._roles[role_id] = self.repo.get_role(self.community_id, role_id)
        return self._roles[role_id]

    def thread_read_at(self, thread_id: int, membership_id: int) -> str | None:
        key = (thread_id, membership_id)
        if key not in self._thread_reads:
            self._thread_reads[key] = self.repo.get_thread_read_at(
                self.community_id,
                thread_id,
                membership_id,
            )
        return self._thread_reads[key]
