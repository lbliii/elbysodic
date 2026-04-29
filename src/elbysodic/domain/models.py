"""Typed domain records for the forum core."""

from __future__ import annotations

from dataclasses import dataclass

from elbysodic.domain.boards import BoardKind, BoardSidebarSection, SidebarRealm


@dataclass(frozen=True, slots=True)
class Community:
    id: int
    name: str
    slug: str
    host: str | None
    default_theme_id: int | None
    identity_accent_facet_group_id: int | None
    enabled_post_profile_variants: str
    enabled_post_accent_styles: str
    enabled_post_border_styles: str
    enabled_post_title_styles: str
    enabled_post_densities: str
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
    parent_board_id: int | None
    slug: str
    name: str
    board_kind: BoardKind
    sidebar_section: BoardSidebarSection
    tagline: str
    description: str
    image_url: str | None
    image_alt: str
    sort_order: int
    navigation_order: int
    show_in_navigation: bool
    is_private: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SidebarSectionConfig:
    id: int
    community_id: int
    realm: SidebarRealm
    section_key: BoardSidebarSection
    label: str
    description: str
    sort_order: int
    show_label: bool
    is_system: bool
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
    poster_url: str | None
    poster_alt: str
    tagline: str
    accent_color: str
    summary: str
    post_profile_variant: str
    post_accent_style: str
    post_border_style: str
    post_title_style: str
    post_density: str
    application_status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class FacetGroup:
    id: int
    community_id: int
    slug: str
    name: str
    description: str
    selection_mode: str
    visibility: str
    sort_order: int
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class Facet:
    id: int
    community_id: int
    facet_group_id: int
    slug: str
    name: str
    description: str
    accent_color: str
    sort_order: int
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class Material:
    id: int
    community_id: int
    slug: str
    title: str
    material_type: str
    summary: str
    body: str
    status: str
    sort_order: int
    is_featured: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class WantedAd:
    id: int
    community_id: int
    creator_membership_id: int
    creator_character_id: int | None
    related_material_id: int | None
    slug: str
    title: str
    wanted_type: str
    summary: str
    body: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class CharacterPlotHook:
    id: int
    community_id: int
    author_membership_id: int
    character_id: int
    related_material_id: int | None
    slug: str
    title: str
    hook_type: str
    summary: str
    body: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class CharacterPlotHookInterest:
    id: int
    community_id: int
    plot_hook_id: int
    membership_id: int
    character_id: int
    note: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class WantedAdInterest:
    id: int
    community_id: int
    wanted_ad_id: int
    membership_id: int
    character_id: int | None
    prospective_character_name: str
    note: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class PlottingRoom:
    id: int
    community_id: int
    owner_membership_id: int
    source_plot_hook_id: int | None
    source_plot_hook_interest_id: int | None
    source_wanted_ad_id: int | None
    source_wanted_ad_interest_id: int | None
    title: str
    summary: str
    notes: str
    next_step: str
    target_board_id: int | None
    target_thread_id: int | None
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class PlottingRoomParticipant:
    id: int
    community_id: int
    plotting_room_id: int
    membership_id: int
    character_id: int | None
    prospective_character_name: str
    participant_role: str
    created_at: str


@dataclass(frozen=True, slots=True)
class CharacterReserve:
    id: int
    community_id: int
    membership_id: int
    character_id: int
    wanted_ad_id: int | None
    wanted_ad_interest_id: int | None
    reserve_type: str
    title: str
    notes: str
    status: str
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
    status: str
    location: str
    timeline: str
    summary: str
    posting_mode: str
    is_locked: bool
    is_pinned: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ThreadParticipant:
    id: int
    community_id: int
    thread_id: int
    character_id: int
    added_at: str


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
    thread_id: int | None
    post_id: int | None
    wanted_ad_id: int | None
    wanted_ad_interest_id: int | None
    character_plot_hook_id: int | None
    plotting_room_id: int | None
    character_id: int | None
    actor_membership_id: int
    actor_character_id: int | None
    read_at: str | None
    created_at: str
