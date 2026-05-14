from __future__ import annotations

from dataclasses import dataclass, field

from elbysodic.domain.models import Character, Community, CommunityMembership, Facet, Post
from elbysodic.services.posts import PostViewContextBuilder

NOW = "2026-01-01T00:00:00+00:00"


@dataclass(slots=True)
class CountingPostRepo:
    community: Community
    characters: dict[int, Character]
    memberships: dict[int, CommunityMembership]
    list_community_characters_calls: int = 0
    list_memberships_calls: int = 0
    get_community_calls: int = 0
    list_character_facets_calls: list[int] = field(default_factory=list)

    def get_community(self, community_id: int) -> Community:
        assert community_id == self.community.id
        self.get_community_calls += 1
        return self.community

    def get_character(self, community_id: int, character_id: int) -> Character:
        assert community_id == self.community.id
        return self.characters[character_id]

    def get_membership(self, community_id: int, membership_id: int) -> CommunityMembership:
        assert community_id == self.community.id
        return self.memberships[membership_id]

    def list_characters_by_ids(
        self,
        community_id: int,
        character_ids: list[int],
    ) -> dict[int, Character]:
        assert community_id == self.community.id
        return {character_id: self.characters[character_id] for character_id in character_ids}

    def list_memberships_by_ids(
        self,
        community_id: int,
        membership_ids: list[int],
    ) -> dict[int, CommunityMembership]:
        assert community_id == self.community.id
        return {membership_id: self.memberships[membership_id] for membership_id in membership_ids}

    def list_character_facets(self, community_id: int, character_id: int) -> list[Facet]:
        assert community_id == self.community.id
        self.list_character_facets_calls.append(character_id)
        return []

    def list_character_facets_for_characters(
        self,
        community_id: int,
        character_ids: list[int],
    ) -> dict[int, list[Facet]]:
        assert community_id == self.community.id
        self.list_character_facets_calls.extend(character_ids)
        return {}

    def list_community_characters(self, community_id: int) -> list[Character]:
        assert community_id == self.community.id
        self.list_community_characters_calls += 1
        return list(self.characters.values())

    def list_memberships(self, community_id: int) -> list[CommunityMembership]:
        assert community_id == self.community.id
        self.list_memberships_calls += 1
        return list(self.memberships.values())


def test_post_view_context_builder_caches_request_mention_links() -> None:
    repo = CountingPostRepo(
        community=_community(),
        characters={
            10: _character(10, membership_id=100, slug="alice-face", name="Alice"),
            11: _character(11, membership_id=101, slug="bob-face", name="Bob"),
        },
        memberships={
            100: _membership(100, username="alice"),
            101: _membership(101, username="bob"),
        },
    )
    builder = PostViewContextBuilder(repo, 1)

    first = builder.context(
        [
            _post(1, author_character_id=10, author_membership_id=100),
            _post(2, author_character_id=11, author_membership_id=101),
        ]
    )
    second = builder.context([_post(3, author_character_id=10, author_membership_id=100)])

    assert first.mention_links is second.mention_links
    assert repo.list_community_characters_calls == 1
    assert repo.list_memberships_calls == 1
    assert repo.get_community_calls == 1


def _community() -> Community:
    return Community(
        id=1,
        name="Test Realm",
        slug="test-realm",
        host=None,
        launch_status="open",
        default_theme_id=None,
        identity_accent_facet_group_id=None,
        community_mark_url=None,
        community_mark_alt="",
        world_hero_image_url=None,
        world_hero_image_alt="",
        world_hero_treatment="natural",
        world_hero_focal_point="center",
        world_hero_overlay="none",
        world_hero_height="standard",
        enabled_post_profile_variants="default",
        enabled_post_accent_styles="default",
        enabled_post_border_styles="default",
        enabled_post_title_styles="default",
        enabled_post_densities="default",
        created_at=NOW,
        updated_at=NOW,
    )


def _character(character_id: int, *, membership_id: int, slug: str, name: str) -> Character:
    return Character(
        id=character_id,
        community_id=1,
        membership_id=membership_id,
        name=name,
        slug=slug,
        avatar_url=None,
        poster_url=None,
        poster_alt="",
        tagline="",
        accent_color="",
        summary="",
        post_profile_variant="default",
        post_accent_style="default",
        post_border_style="default",
        post_title_style="default",
        post_density="default",
        application_status="accepted",
        created_at=NOW,
        updated_at=NOW,
    )


def _membership(membership_id: int, *, username: str) -> CommunityMembership:
    return CommunityMembership(
        id=membership_id,
        community_id=1,
        user_id=membership_id,
        username=username,
        display_name=username.title(),
        avatar_url=None,
        role_id=1,
        default_character_id=None,
        post_count=0,
        is_active=True,
        joined_at=NOW,
    )


def _post(post_id: int, *, author_character_id: int, author_membership_id: int) -> Post:
    return Post(
        id=post_id,
        community_id=1,
        thread_id=1,
        post_number=post_id,
        author_membership_id=author_membership_id,
        author_character_id=author_character_id,
        body="Hello @Alice",
        created_at=NOW,
        updated_at=NOW,
    )
