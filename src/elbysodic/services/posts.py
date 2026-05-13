"""Post-facing read-model helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from elbysodic.domain.models import (
    Character,
    Community,
    CommunityMembership,
    Facet,
    Post,
    PostRevision,
    Role,
)
from elbysodic.services import policies
from elbysodic.services.facets import resolve_character_accent
from elbysodic.services.markup import MentionLink, post_snippet, render_post_body
from elbysodic.services.read_models import PostRevisionView, PostView
from elbysodic.services.timestamps import (
    relative_timestamp_label,
    timestamp_key,
    timestamp_label,
)


class PostViewRepository(Protocol):
    def get_community(self, community_id: int) -> Community: ...

    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def list_character_facets(self, community_id: int, character_id: int) -> list[Facet]: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def list_memberships(self, community_id: int) -> list[CommunityMembership]: ...


@dataclass(frozen=True, slots=True)
class PostViewContext:
    community: Community
    authors: dict[int, Character]
    memberships: dict[int, CommunityMembership]
    accent_colors: dict[int, str]
    mention_links: list[MentionLink]


@dataclass(slots=True)
class PostViewContextBuilder:
    """Build post views with request-local lookup reuse."""

    repo: PostViewRepository
    community_id: int
    _community: Community | None = None
    _mention_links: list[MentionLink] | None = None

    def context(self, posts: list[Post]) -> PostViewContext:
        community = self.community()
        author_ids = {post.author_character_id for post in posts}
        membership_ids = {post.author_membership_id for post in posts}
        authors = {
            character_id: self.repo.get_character(self.community_id, character_id)
            for character_id in sorted(author_ids)
        }
        memberships = {
            membership_id: self.repo.get_membership(self.community_id, membership_id)
            for membership_id in sorted(membership_ids)
        }
        accent_colors = {
            character_id: resolve_character_accent(self.repo, community, character)
            for character_id, character in authors.items()
        }
        return PostViewContext(
            community=community,
            authors=authors,
            memberships=memberships,
            accent_colors=accent_colors,
            mention_links=self.mention_links(),
        )

    def community(self) -> Community:
        if self._community is None:
            self._community = self.repo.get_community(self.community_id)
        return self._community

    def mention_links(self) -> list[MentionLink]:
        if self._mention_links is None:
            self._mention_links = post_mention_links(self.repo, self.community_id)
        return self._mention_links


def build_post_view_context(
    repo: PostViewRepository,
    community_id: int,
    posts: list[Post],
) -> PostViewContext:
    return PostViewContextBuilder(repo, community_id).context(posts)


def post_view(
    repo: PostViewRepository,
    community_id: int,
    post: Post,
    *,
    viewer_membership: CommunityMembership | None = None,
    viewer_role: Role | None = None,
    context: PostViewContext | None = None,
) -> PostView:
    context = context or build_post_view_context(repo, community_id, [post])
    author = context.authors[post.author_character_id]
    return PostView(
        post=post,
        author=author,
        author_accent_color=context.accent_colors.get(author.id, ""),
        author_membership=context.memberships[post.author_membership_id],
        rendered_body=render_post_body(
            post.body,
            mentions=context.mention_links,
        ),
        snippet=post_snippet(post.body),
        can_edit=(
            viewer_membership is not None
            and policies.can_edit_post(viewer_membership, post, viewer_role)
        ),
        is_edited=timestamp_key(post.updated_at) > timestamp_key(post.created_at),
        created_at_label=timestamp_label(post.created_at),
        created_at_relative_label=relative_timestamp_label(post.created_at),
        updated_at_label=timestamp_label(post.updated_at),
        updated_at_relative_label=relative_timestamp_label(post.updated_at),
        anchor=f"post-{post.post_number}",
    )


def post_revision_view(
    repo: PostViewRepository,
    community_id: int,
    revision: PostRevision,
) -> PostRevisionView:
    return PostRevisionView(
        revision=revision,
        editor_membership=repo.get_membership(community_id, revision.editor_membership_id),
        created_at_label=timestamp_label(revision.created_at),
    )


def post_mention_links(repo: PostViewRepository, community_id: int) -> list[MentionLink]:
    links: list[MentionLink] = []
    seen: set[str] = set()
    for character in repo.list_community_characters(community_id):
        for handle in _character_mention_handles(character):
            if handle.lower() in seen:
                continue
            links.append(
                MentionLink(
                    handle=handle,
                    href=f"/characters/{character.slug}",
                    label=character.name,
                    kind="character",
                )
            )
            seen.add(handle.lower())
    for membership in repo.list_memberships(community_id):
        if not membership.is_active or membership.username.lower() in seen:
            continue
        links.append(
            MentionLink(
                handle=membership.username,
                href=f"/members/{membership.username}",
                label=membership.display_name,
                kind="writer",
            )
        )
        seen.add(membership.username.lower())
    return links


def _character_mention_handles(character: Character) -> set[str]:
    handles = {character.slug}
    if re.fullmatch(r"[\w-]+", character.name):
        handles.add(character.name)
    return handles
