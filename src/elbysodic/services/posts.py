"""Post-facing read-model helpers."""

from __future__ import annotations

import re
from typing import Protocol

from elbysodic.domain.models import Character, CommunityMembership, Post, PostRevision, Role
from elbysodic.services import policies
from elbysodic.services.markup import MentionLink, post_snippet, render_post_body
from elbysodic.services.read_models import PostRevisionView, PostView
from elbysodic.services.timestamps import (
    relative_timestamp_label,
    timestamp_key,
    timestamp_label,
)


class PostViewRepository(Protocol):
    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_membership(
        self,
        community_id: int,
        membership_id: int,
    ) -> CommunityMembership: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def list_memberships(self, community_id: int) -> list[CommunityMembership]: ...


def post_view(
    repo: PostViewRepository,
    community_id: int,
    post: Post,
    *,
    viewer_membership: CommunityMembership | None = None,
    viewer_role: Role | None = None,
) -> PostView:
    return PostView(
        post=post,
        author=repo.get_character(community_id, post.author_character_id),
        author_membership=repo.get_membership(
            community_id,
            post.author_membership_id,
        ),
        rendered_body=render_post_body(
            post.body,
            mentions=post_mention_links(repo, community_id),
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
        anchor=f"post-{post.id}",
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
