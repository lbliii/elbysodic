"""Episode-level metrics for scenes and threads."""

from __future__ import annotations

import re

from elbysodic.db import ForumRepository
from elbysodic.domain.models import CommunityMembership, Post
from elbysodic.services.read_models import EpisodeCredits


def episode_credits(
    repo: ForumRepository,
    community_id: int,
    posts: list[Post],
) -> EpisodeCredits:
    word_count = sum(body_word_count(post.body) for post in posts)
    read_minutes = max(1, (word_count + 224) // 225)
    writer_memberships: list[CommunityMembership] = []
    seen_membership_ids: set[int] = set()
    for post in posts:
        if post.author_membership_id in seen_membership_ids:
            continue
        seen_membership_ids.add(post.author_membership_id)
        writer_memberships.append(repo.get_membership(community_id, post.author_membership_id))
    return EpisodeCredits(
        word_count=word_count,
        read_minutes=read_minutes,
        read_estimate_label=f"~{read_minutes} min read",
        post_count=len(posts),
        writer_memberships=writer_memberships,
    )


def body_word_count(body: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", body))
