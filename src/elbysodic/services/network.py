"""Network catalog search helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol
from urllib.parse import quote_plus

from elbysodic.domain.context import RequestIdentityContext
from elbysodic.domain.models import (
    Board,
    Character,
    ClaimType,
    Community,
    CommunityDiscoveryProfile,
    CommunityDiscoveryTag,
    CommunityMembership,
    CommunityTheme,
    Facet,
    FacetGroup,
    Material,
    Role,
    WantedAd,
)
from elbysodic.domain.vocabulary import material_type_label
from elbysodic.services import policies
from elbysodic.services.facets import facet_tags_with_groups
from elbysodic.services.markup import post_snippet
from elbysodic.services.materials import MaterialSummaryRepository
from elbysodic.services.materials import material_summary as _material_summary
from elbysodic.services.notifications import (
    NotificationRepository,
    visible_unread_notification_counts,
)
from elbysodic.services.read_models import (
    DiscoveryProfileChoice,
    DiscoveryProfileChoiceGroup,
    ForumView,
    MaterialSummary,
    NetworkBrowseFacet,
    NetworkDiscoveryFilterGroup,
    NetworkEmptyState,
    NetworkExploreLane,
    NetworkExploreView,
    NetworkHomeView,
    NetworkReturnPath,
    NetworkSlice,
    PublicCatalogCard,
    StudioNetworkDirectory,
    StudioNetworkProgramView,
    StudioNetworkThemePreview,
)
from elbysodic.services.themes import community_theme_view

DISCOVERY_PROFILE_CHOICE_VALUES: dict[str, tuple[str, ...]] = {
    "premise_archetype": (
        "small-town-social-web",
        "weird-town-mystery",
        "urban-supernatural-pressure-cooker",
        "court-and-faction-fantasy",
        "original-canon-adjacent-au",
        "fame-and-industry-drama",
        "survival-trials",
        "occult-historical-pressure",
        "strange-frontier",
    ),
    "play_engine": (
        "character-driven",
        "event-driven",
        "mystery-driven",
        "faction-driven",
        "institution-driven",
        "canon-adjacent",
        "survival-driven",
    ),
    "lore_aperture": (
        "low-lore-real-life",
        "open-lore",
        "semi-open-lore",
        "original-lore",
        "canon-divergent",
        "closed-canon",
    ),
    "access_model": (
        "public-preview",
        "invite-only",
        "interest-form",
        "request-access",
    ),
    "application_model": (
        "profile-app",
        "short-app",
        "canon-app",
        "member-app",
        "interest-form",
    ),
    "age_rating": ("13+", "16+", "18+", "21+"),
    "content_rating": ("1/1/1", "2/2/2", "3/3/3"),
    "activity_pace": ("rapid", "weekly", "relaxed", "slow-burn"),
    "forum_adjunct": (
        "forum-first",
        "discord-light",
        "discord-for-plotting",
        "discord-for-onboarding",
    ),
}

DISCOVERY_TAG_TYPES: tuple[str, ...] = (
    "genre",
    "tone",
    "premise",
    "pressure",
    "entry_path",
    "pace",
    "format",
    "content",
    "roster",
    "access",
    "lore",
)

DISCOVERY_PROFILE_CHOICE_LABELS: dict[str, str] = {
    "premise_archetype": "Premise archetype",
    "play_engine": "Play engine",
    "lore_aperture": "Lore aperture",
    "access_model": "Access model",
    "application_model": "Application model",
    "age_rating": "Age rating",
    "content_rating": "Content rating",
    "activity_pace": "Activity pace",
    "forum_adjunct": "Forum adjunct",
}

PUBLIC_CATALOG_CARD_FIELDS: tuple[str, ...] = tuple(PublicCatalogCard.__dataclass_fields__.keys())
PUBLIC_CATALOG_FORBIDDEN_VIEWER_FIELDS: tuple[str, ...] = (
    "membership",
    "role",
    "current_character",
    "application_count",
    "plotting_room_count",
    "unread_notification_count",
    "is_current",
)

type PublicCatalogViewerMode = Literal[
    "signed_out",
    "account_visitor",
    "same_community_member",
    "staff",
    "inactive_member",
    "cross_community_viewer",
]


@dataclass(frozen=True, slots=True)
class PublicCatalogPrivacyContract:
    card_fields: tuple[str, ...]
    searchable_signals: tuple[str, ...]
    excluded_signals: tuple[str, ...]
    viewer_modes: tuple[PublicCatalogViewerMode, ...]
    batching_contract: tuple[str, ...]


PUBLIC_CATALOG_PRIVACY_CONTRACT = PublicCatalogPrivacyContract(
    card_fields=PUBLIC_CATALOG_CARD_FIELDS,
    searchable_signals=(
        "community_name",
        "published_premise_title",
        "published_premise_summary",
        "published_current_event_title",
        "published_current_event_summary",
        "public_discovery_profile",
        "public_discovery_tags",
        "open_wanted_count",
        "published_application_material_count",
        "public_claim_type_count",
        "public_theme_preview",
        "latest_public_activity_at",
        "activity_freshness_label",
        "request_access_href",
        "invite_posture_label",
        "access_posture_label",
    ),
    excluded_signals=(
        "membership",
        "role",
        "current_character",
        "active_face",
        "unread_notification_count",
        "application_count",
        "plotting_room_count",
        "staff_queue",
        "staff_signal",
        "private_note",
        "private_count",
        "draft_material",
        "draft_application",
        "private_plotting_room",
        "backstage_realm",
        "cross_community_private_state",
        "is_current",
    ),
    viewer_modes=(
        "signed_out",
        "account_visitor",
        "same_community_member",
        "staff",
        "inactive_member",
        "cross_community_viewer",
    ),
    batching_contract=(
        "list_materials_for_communities",
        "list_discovery_profiles_for_communities",
        "list_discovery_tags_for_communities",
        "network_program_counts",
        "public_scene_hub_community_ids",
        "default_themes_for_communities",
    ),
)


class NetworkMembershipContext(Protocol):
    community: Community
    membership: CommunityMembership
    role: Role
    current_character: Character | None


class NetworkCatalogRepository(
    MaterialSummaryRepository,
    NotificationRepository,
    Protocol,
):
    def get_community_by_slug(self, slug: str) -> Community: ...

    def get_default_theme(self, community_id: int) -> CommunityTheme | None: ...

    def list_boards(self, community_id: int) -> list[Board]: ...

    def list_characters_by_ids(
        self,
        community_id: int,
        character_ids: list[int],
    ) -> dict[int, Character]: ...

    def list_claim_types(self, community_id: int) -> list[ClaimType]: ...

    def list_communities(self) -> list[Community]: ...

    def list_discovery_profiles_for_communities(
        self,
        community_ids: Sequence[int],
    ) -> dict[int, CommunityDiscoveryProfile]: ...

    def list_discovery_tags_for_communities(
        self,
        community_ids: Sequence[int],
    ) -> dict[int, list[CommunityDiscoveryTag]]: ...

    def list_community_characters(self, community_id: int) -> list[Character]: ...

    def list_facet_groups_for_communities(
        self,
        community_ids: list[int],
    ) -> dict[int, list[FacetGroup]]: ...

    def list_materials_for_communities(
        self,
        community_ids: list[int],
        *,
        status: str | None = None,
    ) -> dict[int, list[Material]]: ...

    def list_memberships_by_ids(
        self,
        community_id: int,
        membership_ids: list[int],
    ) -> dict[int, CommunityMembership]: ...

    def list_thread_participants_for_threads(
        self,
        community_id: int,
        thread_ids: list[int],
    ) -> dict[int, list[Character]]: ...

    def list_wanted_ads(
        self,
        community_id: int,
        *,
        status: str | None = "open",
    ) -> list[WantedAd]: ...

    def network_membership_counts(
        self,
        membership_ids: list[int],
    ) -> dict[int, dict[str, int]]: ...

    def network_program_counts(
        self,
        community_ids: list[int],
    ) -> dict[int, dict[str, int | str]]: ...

    def public_scene_hub_community_ids(self, community_ids: list[int]) -> set[int]: ...

    def default_themes_for_communities(
        self,
        community_ids: list[int],
    ) -> dict[int, CommunityTheme]: ...


def studio_network(
    repo: NetworkCatalogRepository,
    identity: RequestIdentityContext,
    contexts: Sequence[NetworkMembershipContext],
) -> StudioNetworkDirectory:
    programs: list[StudioNetworkProgramView] = []
    community_ids = [context.community.id for context in contexts]
    materials_by_community = repo.list_materials_for_communities(community_ids)
    themes_by_community = repo.default_themes_for_communities(community_ids)
    facet_groups_by_community = repo.list_facet_groups_for_communities(community_ids)
    material_facets = repo.list_material_facets_for_materials(
        community_ids,
        [material.id for materials in materials_by_community.values() for material in materials],
    )
    counts_by_community = repo.network_program_counts(community_ids)
    counts_by_membership = repo.network_membership_counts(
        [context.membership.id for context in contexts]
    )
    unread_counts = visible_unread_notification_counts(
        repo,
        [(context.community.id, context.membership, context.role) for context in contexts],
    )
    for context in contexts:
        community = context.community
        membership = context.membership
        role = context.role
        materials = materials_by_community.get(community.id, [])
        theme = community_theme_view(themes_by_community.get(community.id))
        counts = counts_by_community.get(community.id, {})
        membership_counts = counts_by_membership.get(membership.id, {})
        can_review_applications = policies.can_manage_applications(membership, role)
        programs.append(
            StudioNetworkProgramView(
                community=community,
                membership=membership,
                role=role,
                current_character=context.current_character,
                premise=first_material_summary_from_batch(
                    materials,
                    "premise",
                    facet_groups_by_community.get(community.id, []),
                    material_facets,
                ),
                current_event=first_material_summary_from_batch(
                    materials,
                    "event",
                    facet_groups_by_community.get(community.id, []),
                    material_facets,
                ),
                roster_count=_network_count(counts, "roster_count"),
                open_wanted_count=_network_count(counts, "open_wanted_count"),
                application_material_count=_network_count(
                    counts,
                    "application_material_count",
                ),
                claim_type_count=_network_count(counts, "claim_type_count"),
                application_count=membership_counts.get(
                    (
                        "reviewable_application_count"
                        if can_review_applications
                        else "own_application_count"
                    ),
                    0,
                ),
                plotting_room_count=membership_counts.get("plotting_room_count", 0),
                unread_notification_count=unread_counts.get(membership.id, 0),
                theme_preview=network_theme_preview(theme),
                is_current=(
                    community.id == identity.community_id
                    and membership.id == identity.membership_id
                ),
                latest_public_activity_at=_network_count_text(
                    counts,
                    "latest_public_activity_at",
                ),
            )
        )
    return StudioNetworkDirectory(
        programs=sorted(
            programs,
            key=lambda program: (
                0 if program.is_current else 1,
                program.community.name,
                program.membership.display_name,
                program.membership.id,
            ),
        )
    )


def public_studio_network(repo: NetworkCatalogRepository) -> StudioNetworkDirectory:
    programs: list[StudioNetworkProgramView] = []
    communities = repo.list_communities()
    community_ids = [community.id for community in communities]
    materials_by_community = repo.list_materials_for_communities(
        community_ids,
        status="published",
    )
    public_scene_hub_community_ids = repo.public_scene_hub_community_ids(community_ids)
    themes_by_community = repo.default_themes_for_communities(community_ids)
    facet_groups_by_community = repo.list_facet_groups_for_communities(community_ids)
    material_facets = repo.list_material_facets_for_materials(
        community_ids,
        [material.id for materials in materials_by_community.values() for material in materials],
    )
    counts_by_community = repo.network_program_counts(community_ids)
    for community in communities:
        materials = materials_by_community.get(community.id, [])
        if not is_public_network_ready_from_batches(
            community,
            materials,
            public_scene_hub_community_ids,
        ):
            continue
        theme = community_theme_view(themes_by_community.get(community.id))
        counts = counts_by_community.get(community.id, {})
        programs.append(
            StudioNetworkProgramView(
                community=community,
                membership=None,
                role=None,
                current_character=None,
                premise=first_material_summary_from_batch(
                    materials,
                    "premise",
                    facet_groups_by_community.get(community.id, []),
                    material_facets,
                ),
                current_event=first_material_summary_from_batch(
                    materials,
                    "event",
                    facet_groups_by_community.get(community.id, []),
                    material_facets,
                ),
                roster_count=_network_count(counts, "roster_count"),
                open_wanted_count=_network_count(counts, "open_wanted_count"),
                application_material_count=_network_count(
                    counts,
                    "application_material_count",
                ),
                claim_type_count=_network_count(counts, "claim_type_count"),
                application_count=0,
                plotting_room_count=0,
                unread_notification_count=0,
                theme_preview=network_theme_preview(theme),
                is_current=False,
                latest_public_activity_at=_network_count_text(
                    counts,
                    "latest_public_activity_at",
                ),
            )
        )
    return StudioNetworkDirectory(programs=programs)


def network_home(cards: list[PublicCatalogCard], viewer: ForumView | None) -> NetworkHomeView:
    cards = ensure_public_catalog_cards(cards, surface="network_home")
    return_path = None
    if viewer is not None:
        return_path = NetworkReturnPath(
            desk_href=f"/c/{viewer.community.slug}/desk",
            notification_href="/notifications",
            unread_notification_count=viewer.unread_notification_count,
        )
    return NetworkHomeView(
        featured=cards[0] if cards else None,
        slices=[
            NetworkSlice("Top 10 realms", "/network", cards[:10]),
            *_network_home_premise_slices(cards),
        ],
        browse_facets=network_browse_facets(cards),
        filter_groups=network_filter_groups(cards),
        return_path=return_path,
    )


def _network_home_premise_slices(cards: list[PublicCatalogCard]) -> list[NetworkSlice]:
    slices = []
    for premise in DISCOVERY_PROFILE_CHOICE_VALUES["premise_archetype"]:
        matching_cards = _cards_matching_profile(cards, "premise_archetype", premise)
        if matching_cards:
            slices.append(
                NetworkSlice(
                    _premise_slice_title(premise),
                    f"/network?q={quote_plus(premise)}",
                    matching_cards,
                )
            )
    return slices


def _cards_matching_profile(
    cards: list[PublicCatalogCard],
    field_name: str,
    value: str,
) -> list[PublicCatalogCard]:
    return [
        card
        for card in cards
        if card.discovery_profile is not None
        and str(getattr(card.discovery_profile, field_name, "") or "").lower() == value
    ]


def _premise_slice_title(value: str) -> str:
    titles = {
        "small-town-social-web": "Small-town social webs",
        "weird-town-mystery": "Weird-town mysteries",
        "urban-supernatural-pressure-cooker": "Urban supernatural pressure cookers",
        "court-and-faction-fantasy": "Court and faction fantasy",
        "original-canon-adjacent-au": "Original canon-adjacent AUs",
        "fame-and-industry-drama": "Fame and industry dramas",
        "survival-trials": "Survival trials",
        "occult-historical-pressure": "Occult historical pressure",
        "strange-frontier": "Strange frontiers",
    }
    return titles.get(value, _discovery_filter_label(value))


def network_explore(cards: list[PublicCatalogCard], query: str = "") -> NetworkExploreView:
    cards = ensure_public_catalog_cards(cards, surface="network_explore")
    normalized_query = query.strip()
    return NetworkExploreView(
        query=normalized_query,
        browse_facets=network_browse_facets(cards),
        filter_groups=network_filter_groups(cards),
        relationship_lanes=network_explore_lanes(cards),
        results=search_public_catalog(cards, normalized_query),
        empty_state=network_empty_state(query=normalized_query),
    )


def network_empty_state(*, query: str = "") -> NetworkEmptyState:
    if query:
        return NetworkEmptyState(
            kicker="No search match",
            title="No public realms match that search yet.",
            summary=(
                "The request completed, but no public-ready realm currently matches that "
                "premise, pace, hook, roster, or chapter signal."
            ),
        )
    return NetworkEmptyState(
        kicker="No public-ready realms",
        title="No public-ready realms are open yet.",
        summary=(
            "The request completed, but this database has no realm that is both public-preview "
            "and ready for catalog discovery. Directors can confirm realm count, public-ready "
            "count, seed posture, and database path from Studio Operations."
        ),
    )


def public_catalog_cards(repo: NetworkCatalogRepository) -> list[PublicCatalogCard]:
    directory = public_studio_network(repo)
    community_ids = [program.community.id for program in directory.programs]
    profiles_by_community = repo.list_discovery_profiles_for_communities(community_ids)
    tags_by_community = repo.list_discovery_tags_for_communities(community_ids)
    return [
        public_catalog_card_from_program(
            program,
            profiles_by_community.get(program.community.id),
            tuple(tags_by_community.get(program.community.id, ())),
        )
        for program in directory.programs
    ]


def public_studio_program(
    repo: NetworkCatalogRepository,
    community_slug: str,
) -> StudioNetworkProgramView:
    community = public_preview_community(repo, community_slug)
    materials = repo.list_materials(community.id, status="published")
    wanted_ads = repo.list_wanted_ads(community.id, status=None)
    community_characters = repo.list_community_characters(community.id)
    counts = repo.network_program_counts([community.id]).get(community.id, {})
    theme = community_theme_view(repo.get_default_theme(community.id))
    return StudioNetworkProgramView(
        community=community,
        membership=None,
        role=None,
        current_character=None,
        premise=first_material_summary(materials, "premise", repo, community.id),
        current_event=first_material_summary(
            materials,
            "event",
            repo,
            community.id,
        ),
        roster_count=len(community_characters),
        open_wanted_count=sum(1 for wanted_ad in wanted_ads if wanted_ad.status == "open"),
        application_material_count=sum(
            1 for material in materials if material.material_type == "application"
        ),
        claim_type_count=len(repo.list_claim_types(community.id)),
        application_count=0,
        plotting_room_count=0,
        unread_notification_count=0,
        theme_preview=network_theme_preview(theme),
        is_current=False,
        latest_public_activity_at=_network_count_text(counts, "latest_public_activity_at"),
    )


def public_preview_community(repo: NetworkCatalogRepository, community_slug: str) -> Community:
    community = repo.get_community_by_slug(community_slug)
    materials = repo.list_materials(community.id)
    if not is_public_network_ready(repo, community, materials):
        raise LookupError(f"community not available for public preview: {community_slug}")
    return community


def _network_count(counts: dict[str, int | str], key: str) -> int:
    value = counts.get(key, 0)
    if isinstance(value, int):
        return value
    if not value:
        return 0
    return int(value)


def _network_count_text(counts: dict[str, int | str], key: str) -> str:
    return str(counts.get(key, "") or "")


def search_studio_network(
    directory: StudioNetworkDirectory,
    query: str,
) -> list[StudioNetworkProgramView]:
    """Return network programs matching a public catalog query."""

    normalized_query = query.strip().lower()
    if not normalized_query:
        return list(directory.programs)
    return [
        program
        for program in directory.programs
        if normalized_query in _program_search_text(program)
    ]


def search_public_catalog(
    cards: list[PublicCatalogCard],
    query: str,
) -> list[PublicCatalogCard]:
    """Return public catalog cards matching a public discovery query."""

    cards = ensure_public_catalog_cards(cards, surface="search_public_catalog")
    normalized_query = query.strip().lower()
    if not normalized_query:
        return list(cards)
    return [card for card in cards if normalized_query in _public_catalog_search_text(card)]


def ensure_public_catalog_cards(
    cards: Sequence[object],
    *,
    surface: str,
) -> list[PublicCatalogCard]:
    public_cards: list[PublicCatalogCard] = []
    for card in cards:
        if not isinstance(card, PublicCatalogCard):
            raise TypeError(f"{surface} requires PublicCatalogCard read models")
        leaked_fields = [
            field_name
            for field_name in PUBLIC_CATALOG_FORBIDDEN_VIEWER_FIELDS
            if hasattr(card, field_name)
        ]
        if leaked_fields:
            raise ValueError(
                f"{surface} public catalog card includes viewer-only fields: "
                f"{', '.join(leaked_fields)}"
            )
        public_cards.append(card)
    return public_cards


def _cards_matching_discovery(
    cards: list[PublicCatalogCard],
    query: str,
) -> list[PublicCatalogCard]:
    normalized_query = query.strip().lower()
    if not normalized_query:
        return list(cards)
    return [card for card in cards if normalized_query in _public_catalog_search_text(card)]


def is_public_network_ready(
    repo: NetworkCatalogRepository,
    community: Community,
    materials: list[Material],
) -> bool:
    if community.launch_status != "public-preview":
        return False
    has_public_premise = any(
        material.material_type == "premise" and material.status == "published"
        for material in materials
    )
    has_public_scene_hub = any(
        board.board_kind in {"location", "community"} and not board.is_private
        for board in repo.list_boards(community.id)
    )
    return has_public_premise and has_public_scene_hub


def is_public_network_ready_from_batches(
    community: Community,
    materials: list[Material],
    public_scene_hub_community_ids: set[int],
) -> bool:
    if community.launch_status != "public-preview":
        return False
    has_public_premise = any(
        material.material_type == "premise" and material.status == "published"
        for material in materials
    )
    return has_public_premise and community.id in public_scene_hub_community_ids


def first_material_summary(
    materials: list[Material],
    material_type: str,
    repo: NetworkCatalogRepository,
    community_id: int,
) -> MaterialSummary | None:
    for material in materials:
        if material.material_type == material_type:
            return _material_summary(repo, community_id, material)
    return None


def first_material_summary_from_batch(
    materials: list[Material],
    material_type: str,
    facet_groups: list[FacetGroup],
    facets_by_material: dict[tuple[int, int], list[Facet]],
) -> MaterialSummary | None:
    for material in materials:
        if material.material_type != material_type:
            continue
        return MaterialSummary(
            material=material,
            facets=facet_tags_with_groups(
                facet_groups,
                facets_by_material.get((material.community_id, material.id), []),
            ),
            rendered_summary=material.summary or post_snippet(material.body, limit=160),
            type_label=material_type_label(material.material_type),
        )
    return None


def public_catalog_card_from_program(
    program: StudioNetworkProgramView,
    discovery_profile: CommunityDiscoveryProfile | None = None,
    discovery_tags: tuple[CommunityDiscoveryTag, ...] = (),
) -> PublicCatalogCard:
    return PublicCatalogCard(
        community=program.community,
        premise=program.premise,
        current_event=program.current_event,
        discovery_profile=discovery_profile,
        discovery_tags=discovery_tags,
        roster_count=program.roster_count,
        open_wanted_count=program.open_wanted_count,
        application_material_count=program.application_material_count,
        claim_type_count=program.claim_type_count,
        theme_preview=program.theme_preview,
        latest_public_activity_at=program.latest_public_activity_at,
    )


def network_browse_facets(cards: list[PublicCatalogCard]) -> list[NetworkBrowseFacet]:
    def count(query: str) -> int:
        return len(_cards_matching_discovery(cards, query))

    return [
        NetworkBrowseFacet(
            "small-town social web",
            "/network?q=small-town-social-web",
            "hot",
            count("small-town-social-web"),
        ),
        NetworkBrowseFacet(
            "weird-town mystery",
            "/network?q=weird-town-mystery",
            result_count=count("weird-town-mystery"),
        ),
        NetworkBrowseFacet(
            "urban supernatural",
            "/network?q=urban-supernatural",
            result_count=count("urban-supernatural"),
        ),
        NetworkBrowseFacet(
            "court politics",
            "/network?q=court-and-faction",
            result_count=count("court-and-faction"),
        ),
        NetworkBrowseFacet(
            "fame and industry",
            "/network?q=fame-industry",
            result_count=count("fame-industry"),
        ),
        NetworkBrowseFacet(
            "current chapters",
            "/network?q=current-chapter",
            "hot",
            count("current-chapter"),
        ),
        NetworkBrowseFacet(
            "open wanted hooks",
            "/network?q=wanted",
            result_count=count("wanted"),
        ),
        NetworkBrowseFacet(
            "relaxed activity",
            "/network?q=relaxed",
            result_count=count("relaxed"),
        ),
        NetworkBrowseFacet(
            "forum-first",
            "/network?q=forum-first",
            result_count=count("forum-first"),
        ),
    ]


def network_filter_groups(cards: list[PublicCatalogCard]) -> list[NetworkDiscoveryFilterGroup]:
    groups = [
        NetworkDiscoveryFilterGroup(
            "Premise engine",
            _profile_filter_options(cards, "premise_archetype"),
        ),
        NetworkDiscoveryFilterGroup(
            "Play engine",
            _profile_filter_options(cards, "play_engine"),
        ),
        NetworkDiscoveryFilterGroup(
            "Lore aperture",
            _profile_filter_options(cards, "lore_aperture"),
        ),
        NetworkDiscoveryFilterGroup(
            "Start here",
            _profile_filter_options(cards, "access_model")
            + _profile_filter_options(cards, "application_model"),
        ),
        NetworkDiscoveryFilterGroup(
            "Pace and touchpoints",
            _profile_filter_options(cards, "activity_pace")
            + _profile_filter_options(cards, "forum_adjunct"),
        ),
        NetworkDiscoveryFilterGroup(
            "Roster posture",
            _profile_filter_options(cards, "roster_posture", limit=6),
        ),
    ]
    return [group for group in groups if group.options]


def discovery_profile_choice_groups() -> tuple[DiscoveryProfileChoiceGroup, ...]:
    return tuple(
        DiscoveryProfileChoiceGroup(
            field_name=field_name,
            label=DISCOVERY_PROFILE_CHOICE_LABELS[field_name],
            choices=tuple(
                DiscoveryProfileChoice(value=value, label=_discovery_filter_label(value))
                for value in values
            ),
        )
        for field_name, values in DISCOVERY_PROFILE_CHOICE_VALUES.items()
    )


def network_explore_lanes(cards: list[PublicCatalogCard]) -> list[NetworkExploreLane]:
    return [
        NetworkExploreLane(
            "Start with a premise",
            "Find the story engine before choosing a face.",
            "/network",
            "premise",
            len(cards),
        ),
        NetworkExploreLane(
            "Start with a current chapter",
            "World-state pressure and scenes already moving.",
            "/network?q=current-chapter",
            "story",
            len(_cards_matching_discovery(cards, "current-chapter")),
        ),
        NetworkExploreLane(
            "Start with roster energy",
            "Find realms with visible faces, canons, and claims in motion.",
            "/network?q=faces",
            "roster",
            len(_cards_matching_discovery(cards, "faces")),
        ),
        NetworkExploreLane(
            "Start with a wanted hook",
            "Open roles, rivals, factions, and face requests.",
            "/network?q=wanted",
            "wanted",
            len(_cards_matching_discovery(cards, "wanted")),
        ),
    ]


def _profile_filter_options(
    cards: list[PublicCatalogCard],
    field_name: str,
    *,
    limit: int | None = None,
) -> list[NetworkBrowseFacet]:
    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    for card in cards:
        profile = card.discovery_profile
        if profile is None:
            continue
        raw_value = str(getattr(profile, field_name, "") or "").strip()
        if not raw_value:
            continue
        key = raw_value.lower()
        counts[key] = counts.get(key, 0) + 1
        labels.setdefault(key, _discovery_filter_label(raw_value))
    options = [
        NetworkBrowseFacet(
            labels[key],
            f"/network?q={quote_plus(key)}",
            "hot" if field_name == "premise_archetype" else "neutral",
            counts[key],
        )
        for key in sorted(counts, key=lambda value: (-counts[value], labels[value]))
    ]
    if limit is not None:
        return options[:limit]
    return options


def _discovery_filter_label(value: str) -> str:
    normalized = " ".join(value.replace("_", " ").replace("-", " ").split())
    if not normalized:
        return value
    compact_upper = {"AU", "OC", "OCs", "IP"}
    return " ".join(
        word.upper() if word.upper() in compact_upper else word.capitalize()
        for word in normalized.split()
    )


def network_theme_preview(theme: object | None) -> StudioNetworkThemePreview:
    variables = dict(getattr(theme, "dark_variables", ()) or ())
    base_variables = dict(getattr(theme, "base_variables", ()) or ())
    return StudioNetworkThemePreview(
        accent=variables.get("--chirpui-accent", "var(--chirpui-accent)"),
        surface=variables.get("--chirpui-surface", "var(--chirpui-surface)"),
        text=variables.get("--chirpui-text", "var(--chirpui-text)"),
        display_font=base_variables.get(
            "--elbysodic-display-font-family",
            "var(--elbysodic-display-font-family)",
        ),
    )


def _program_search_text(program: StudioNetworkProgramView) -> str:
    catalog_keywords: list[str] = []
    if program.open_wanted_count:
        catalog_keywords.append("wanted hooks casting open roles")
    if program.application_count:
        catalog_keywords.append("application applications")
    if program.plotting_room_count:
        catalog_keywords.append("plotting rooms")
    if program.current_event:
        catalog_keywords.append("event current event")
    if "hp" in program.community.slug or "magic" in program.community.name.lower():
        catalog_keywords.append("magic school fantasy")
    if "jurassic" in program.community.slug:
        catalog_keywords.append("survival sci-fi science island")
    if "x-men" in program.community.slug or "mutant" in program.community.name.lower():
        catalog_keywords.append("superhero crisis mutants")
    if "small-town" in program.community.slug:
        catalog_keywords.append("small town found family")
    if "nyc" in program.community.slug:
        catalog_keywords.append("urban real life city")
    haystack_parts = [
        program.community.name,
        program.membership.display_name if program.membership else "",
        program.membership.username if program.membership else "",
        program.role.name if program.role else "",
        program.current_character.name if program.current_character else "",
        program.premise.material.title if program.premise else "",
        program.premise.material.summary if program.premise else "",
        program.current_event.material.title if program.current_event else "",
        program.current_event.material.summary if program.current_event else "",
        *catalog_keywords,
    ]
    return " ".join(haystack_parts).lower()


def _public_catalog_search_text(card: PublicCatalogCard) -> str:
    catalog_keywords: list[str] = []
    if card.open_wanted_count:
        catalog_keywords.append("wanted hooks casting open roles")
    if card.application_material_count:
        catalog_keywords.append("application applications first face")
    if card.current_event:
        catalog_keywords.append("event current event current chapter")
    catalog_keywords.extend(
        [
            card.access_posture_label,
            card.activity_freshness_label,
        ]
    )
    profile = card.discovery_profile
    if profile is not None:
        catalog_keywords.extend(
            [
                profile.premise_archetype,
                profile.play_engine,
                profile.lore_aperture,
                profile.access_model,
                profile.application_model,
                profile.age_rating,
                profile.content_rating,
                profile.activity_pace,
                profile.activity_expectation,
                profile.forum_adjunct,
                profile.roster_posture,
                profile.catalog_pitch,
                profile.onboarding_pitch,
                profile.staff_pick_label,
            ]
        )
    for tag in card.discovery_tags:
        catalog_keywords.extend([tag.tag_type, tag.tag_key, tag.label, tag.search_text])
    haystack_parts = [
        card.community.name,
        card.premise.material.title if card.premise else "",
        card.premise.material.summary if card.premise else "",
        card.current_event.material.title if card.current_event else "",
        card.current_event.material.summary if card.current_event else "",
        *catalog_keywords,
    ]
    return " ".join(haystack_parts).lower()
