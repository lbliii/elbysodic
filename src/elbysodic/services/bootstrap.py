"""Production bootstrap helpers for the first director account."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from elbysodic.domain.models import Community, CommunityMembership, Role, User
from elbysodic.services.auth import hash_password

ADMIN_ROLE_NAME = "Admin"
ADMIN_ROLE_SLUG = "admin"


class BootstrapRepository(Protocol):
    def create_community(self, slug: str, name: str, host: str | None = None) -> Community: ...

    def list_communities(self) -> list[Community]: ...

    def get_community_by_name(self, name: str) -> Community: ...

    def create_role(
        self,
        community_id: int,
        slug: str,
        name: str,
        *,
        is_admin: bool = False,
    ) -> Role: ...

    def get_role_by_slug(self, community_id: int, slug: str) -> Role: ...

    def update_role_admin(self, community_id: int, role_id: int, *, is_admin: bool) -> Role: ...

    def create_user(self, email: str, password_hash: str) -> User: ...

    def get_user_by_email(self, email: str) -> User: ...

    def update_user_password(self, user_id: int, password_hash: str) -> User: ...

    def create_membership(
        self,
        community_id: int,
        user_id: int,
        role_id: int,
        username: str,
        display_name: str,
        avatar_url: str | None = None,
    ) -> CommunityMembership: ...

    def get_membership_for_user(self, community_id: int, user_id: int) -> CommunityMembership: ...

    def update_membership_role(
        self,
        community_id: int,
        membership_id: int,
        role_id: int,
    ) -> CommunityMembership: ...


@dataclass(frozen=True, slots=True)
class BootstrapAdminResult:
    community: Community
    role: Role
    user: User
    membership: CommunityMembership
    created_community: bool
    created_user: bool
    reset_password: bool
    created_membership: bool
    promoted_membership: bool


def bootstrap_admin(
    repo: BootstrapRepository,
    *,
    email: str,
    password: str,
    username: str,
    display_name: str,
    community_name: str | None,
    reset_password: bool = False,
) -> BootstrapAdminResult:
    normalized_email = email.strip().lower()
    normalized_username = username.strip()
    normalized_display_name = display_name.strip()
    normalized_community_name = (community_name or "").strip() or None

    if not normalized_email:
        raise ValueError("email is required")
    if not password:
        raise ValueError("password is required")
    if not normalized_username:
        raise ValueError("username is required")
    if not normalized_display_name:
        raise ValueError("display name is required")

    community, created_community = _resolve_bootstrap_community(
        repo,
        normalized_community_name,
    )
    role = _ensure_admin_role(repo, community.id)
    user, created_user, password_was_reset = _ensure_user(
        repo,
        normalized_email,
        password,
        reset_password=reset_password,
    )
    membership, created_membership = _ensure_membership(
        repo,
        community.id,
        user.id,
        role.id,
        normalized_username,
        normalized_display_name,
    )
    promoted_membership = False
    if membership.role_id != role.id:
        membership = repo.update_membership_role(community.id, membership.id, role.id)
        promoted_membership = True

    return BootstrapAdminResult(
        community=community,
        role=role,
        user=user,
        membership=membership,
        created_community=created_community,
        created_user=created_user,
        reset_password=password_was_reset,
        created_membership=created_membership,
        promoted_membership=promoted_membership,
    )


def _resolve_bootstrap_community(
    repo: BootstrapRepository,
    community_name: str | None,
) -> tuple[Community, bool]:
    if community_name:
        try:
            return repo.get_community_by_name(community_name), False
        except LookupError:
            return repo.create_community(_slugify(community_name), community_name), True

    communities = repo.list_communities()
    if len(communities) == 1:
        return communities[0], False
    if not communities:
        default_name = "Elbysodic"
        return repo.create_community(_slugify(default_name), default_name), True
    raise ValueError("multiple communities exist; pass --community-name")


def _ensure_admin_role(repo: BootstrapRepository, community_id: int) -> Role:
    try:
        role = repo.get_role_by_slug(community_id, ADMIN_ROLE_SLUG)
    except LookupError:
        return repo.create_role(
            community_id,
            ADMIN_ROLE_SLUG,
            ADMIN_ROLE_NAME,
            is_admin=True,
        )
    return repo.update_role_admin(community_id, role.id, is_admin=True)


def _ensure_user(
    repo: BootstrapRepository,
    email: str,
    password: str,
    *,
    reset_password: bool,
) -> tuple[User, bool, bool]:
    try:
        user = repo.get_user_by_email(email)
    except LookupError:
        return repo.create_user(email, hash_password(password)), True, False
    if reset_password:
        return repo.update_user_password(user.id, hash_password(password)), False, True
    return user, False, False


def _ensure_membership(
    repo: BootstrapRepository,
    community_id: int,
    user_id: int,
    role_id: int,
    username: str,
    display_name: str,
) -> tuple[CommunityMembership, bool]:
    try:
        return repo.get_membership_for_user(community_id, user_id), False
    except LookupError:
        return (
            repo.create_membership(
                community_id,
                user_id,
                role_id,
                username,
                display_name,
            ),
            True,
        )


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "elbysodic"
