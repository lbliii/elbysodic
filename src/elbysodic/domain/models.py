"""Typed domain records for the forum core."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Community:
    id: int
    name: str
    slug: str
    host: str | None
    default_theme_id: int | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class User:
    id: int
    email: str
    password_hash: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Role:
    id: int
    community_id: int
    slug: str
    name: str
    is_admin: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class CommunityMembership:
    id: int
    community_id: int
    user_id: int
    username: str
    display_name: str
    avatar_url: str | None
    role_id: int
    default_character_id: int | None
    post_count: int
    is_active: bool
    joined_at: str


@dataclass(frozen=True, slots=True)
class Board:
    id: int
    community_id: int
    slug: str
    name: str
    description: str
    sort_order: int
    is_private: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class Character:
    id: int
    community_id: int
    membership_id: int
    name: str
    slug: str
    avatar_url: str | None
    summary: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class Thread:
    id: int
    community_id: int
    board_id: int
    author_membership_id: int
    author_character_id: int
    slug: str
    title: str
    is_locked: bool
    is_pinned: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class Post:
    id: int
    community_id: int
    thread_id: int
    author_membership_id: int
    author_character_id: int
    body: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class PostRevision:
    id: int
    community_id: int
    post_id: int
    editor_membership_id: int
    previous_body: str
    new_body: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ThreadWatch:
    id: int
    community_id: int
    thread_id: int
    membership_id: int
    created_at: str


@dataclass(frozen=True, slots=True)
class Notification:
    id: int
    community_id: int
    membership_id: int
    kind: str
    thread_id: int
    post_id: int
    actor_membership_id: int
    actor_character_id: int
    read_at: str | None
    created_at: str
