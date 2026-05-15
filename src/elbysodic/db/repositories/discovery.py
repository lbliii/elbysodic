"""Community discovery profile repository methods."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from elbysodic.db.repositories.base import _utc_now
from elbysodic.db.repositories.posts import PostRepositoryMixin
from elbysodic.db.repositories.rows import (
    _community_discovery_profile_from_row,
    _community_discovery_tag_from_row,
)
from elbysodic.domain.models import CommunityDiscoveryProfile, CommunityDiscoveryTag


@dataclass(frozen=True, slots=True)
class DiscoveryTagInput:
    tag_type: str
    tag_key: str
    label: str
    search_text: str = ""
    sort_order: int = 0


class DiscoveryRepositoryMixin(PostRepositoryMixin):
    def get_discovery_profile(self, community_id: int) -> CommunityDiscoveryProfile:
        row = self.connection.execute(
            """
            SELECT
                community_id,
                premise_archetype,
                play_engine,
                lore_aperture,
                access_model,
                application_model,
                age_rating,
                content_rating,
                activity_pace,
                activity_expectation,
                forum_adjunct,
                roster_posture,
                catalog_pitch,
                onboarding_pitch,
                staff_pick_label,
                featured_event_material_id,
                created_at,
                updated_at
            FROM community_discovery_profiles
            WHERE community_id = ?
            """,
            (community_id,),
        ).fetchone()
        if row is None:
            raise LookupError(f"discovery profile not found in community {community_id}")
        return _community_discovery_profile_from_row(row)

    def list_discovery_profiles_for_communities(
        self,
        community_ids: Sequence[int],
    ) -> dict[int, CommunityDiscoveryProfile]:
        ids = _community_id_list(community_ids)
        if not ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                community_id,
                premise_archetype,
                play_engine,
                lore_aperture,
                access_model,
                application_model,
                age_rating,
                content_rating,
                activity_pace,
                activity_expectation,
                forum_adjunct,
                roster_posture,
                catalog_pitch,
                onboarding_pitch,
                staff_pick_label,
                featured_event_material_id,
                created_at,
                updated_at
            FROM community_discovery_profiles
            WHERE community_id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(ids, separators=(",", ":")),),
        ).fetchall()
        return {
            profile.community_id: profile
            for profile in (_community_discovery_profile_from_row(row) for row in rows)
        }

    def upsert_discovery_profile(
        self,
        community_id: int,
        *,
        premise_archetype: str = "",
        play_engine: str = "",
        lore_aperture: str = "",
        access_model: str = "",
        application_model: str = "",
        age_rating: str = "",
        content_rating: str = "",
        activity_pace: str = "",
        activity_expectation: str = "",
        forum_adjunct: str = "",
        roster_posture: str = "",
        catalog_pitch: str = "",
        onboarding_pitch: str = "",
        staff_pick_label: str = "",
        featured_event_material_id: int | None = None,
    ) -> CommunityDiscoveryProfile:
        self.get_community(community_id)
        if featured_event_material_id is not None:
            material = self.get_material(community_id, featured_event_material_id)
            if material.material_type != "event":
                raise ValueError("featured_event_material_id must reference an event material")
        now = _utc_now()
        self.connection.execute(
            """
            INSERT INTO community_discovery_profiles (
                community_id,
                premise_archetype,
                play_engine,
                lore_aperture,
                access_model,
                application_model,
                age_rating,
                content_rating,
                activity_pace,
                activity_expectation,
                forum_adjunct,
                roster_posture,
                catalog_pitch,
                onboarding_pitch,
                staff_pick_label,
                featured_event_material_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(community_id) DO UPDATE SET
                premise_archetype = excluded.premise_archetype,
                play_engine = excluded.play_engine,
                lore_aperture = excluded.lore_aperture,
                access_model = excluded.access_model,
                application_model = excluded.application_model,
                age_rating = excluded.age_rating,
                content_rating = excluded.content_rating,
                activity_pace = excluded.activity_pace,
                activity_expectation = excluded.activity_expectation,
                forum_adjunct = excluded.forum_adjunct,
                roster_posture = excluded.roster_posture,
                catalog_pitch = excluded.catalog_pitch,
                onboarding_pitch = excluded.onboarding_pitch,
                staff_pick_label = excluded.staff_pick_label,
                featured_event_material_id = excluded.featured_event_material_id,
                updated_at = excluded.updated_at
            """,
            (
                community_id,
                premise_archetype.strip(),
                play_engine.strip(),
                lore_aperture.strip(),
                access_model.strip(),
                application_model.strip(),
                age_rating.strip(),
                content_rating.strip(),
                activity_pace.strip(),
                activity_expectation.strip(),
                forum_adjunct.strip(),
                roster_posture.strip(),
                catalog_pitch.strip(),
                onboarding_pitch.strip(),
                staff_pick_label.strip(),
                featured_event_material_id,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_discovery_profile(community_id)

    def list_discovery_tags_for_communities(
        self,
        community_ids: Sequence[int],
    ) -> dict[int, list[CommunityDiscoveryTag]]:
        ids = _community_id_list(community_ids)
        if not ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                tag_type,
                tag_key,
                label,
                search_text,
                sort_order,
                created_at,
                updated_at
            FROM community_discovery_tags
            WHERE community_id IN (SELECT value FROM json_each(?))
            ORDER BY community_id, tag_type, sort_order, id
            """,
            (json.dumps(ids, separators=(",", ":")),),
        ).fetchall()
        tags_by_community: dict[int, list[CommunityDiscoveryTag]] = defaultdict(list)
        for row in rows:
            tag = _community_discovery_tag_from_row(row)
            tags_by_community[tag.community_id].append(tag)
        return dict(tags_by_community)

    def replace_discovery_tags(
        self,
        community_id: int,
        tags: Sequence[DiscoveryTagInput],
    ) -> list[CommunityDiscoveryTag]:
        self.get_community(community_id)
        now = _utc_now()
        with self.transaction():
            self.connection.execute(
                "DELETE FROM community_discovery_tags WHERE community_id = ?",
                (community_id,),
            )
            for index, tag in enumerate(tags, start=1):
                tag_type = tag.tag_type.strip()
                tag_key = tag.tag_key.strip()
                label = tag.label.strip()
                if not tag_type or not tag_key or not label:
                    raise ValueError("discovery tags require tag_type, tag_key, and label")
                self.connection.execute(
                    """
                    INSERT INTO community_discovery_tags (
                        community_id,
                        tag_type,
                        tag_key,
                        label,
                        search_text,
                        sort_order,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        community_id,
                        tag_type,
                        tag_key,
                        label,
                        tag.search_text.strip(),
                        tag.sort_order or index * 10,
                        now,
                        now,
                    ),
                )
        return self.list_discovery_tags_for_communities([community_id]).get(community_id, [])

    def upsert_discovery_tag(
        self,
        community_id: int,
        tag: DiscoveryTagInput,
    ) -> CommunityDiscoveryTag:
        self.get_community(community_id)
        tag_type = tag.tag_type.strip()
        tag_key = tag.tag_key.strip()
        label = tag.label.strip()
        if not tag_type or not tag_key or not label:
            raise ValueError("discovery tags require tag_type, tag_key, and label")
        now = _utc_now()
        self.connection.execute(
            """
            INSERT INTO community_discovery_tags (
                community_id,
                tag_type,
                tag_key,
                label,
                search_text,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(community_id, tag_type, tag_key) DO UPDATE SET
                label = excluded.label,
                search_text = excluded.search_text,
                sort_order = excluded.sort_order,
                updated_at = excluded.updated_at
            """,
            (
                community_id,
                tag_type,
                tag_key,
                label,
                tag.search_text.strip(),
                tag.sort_order,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_discovery_tag(community_id, tag_type, tag_key)

    def get_discovery_tag(
        self,
        community_id: int,
        tag_type: str,
        tag_key: str,
    ) -> CommunityDiscoveryTag:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                tag_type,
                tag_key,
                label,
                search_text,
                sort_order,
                created_at,
                updated_at
            FROM community_discovery_tags
            WHERE community_id = ? AND tag_type = ? AND tag_key = ?
            """,
            (community_id, tag_type, tag_key),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"discovery tag not found in community {community_id}: {tag_type}/{tag_key}"
            )
        return _community_discovery_tag_from_row(row)


def _community_id_list(community_ids: Sequence[int]) -> list[int]:
    return list(dict.fromkeys(community_ids))
