"""Service-layer commands and read models for the forum slice."""

from __future__ import annotations

import os
import re
import secrets
import sqlite3
from contextlib import AbstractContextManager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from elbysodic.blueprints import ProgramBlueprintPreview
from elbysodic.db import Database, ForumRepository, connect, create_schema
from elbysodic.db.seed import (
    SEED_PERSONAS,
    DemoSeed,
    SeedPersona,
    resolve_seed_persona,
    seed_demo_forum,
    seed_persona_by_key,
)
from elbysodic.domain.boards import (
    BOARD_IMAGE_FOCAL_POINTS,
    BOARD_IMAGE_OVERLAYS,
    BOARD_IMAGE_TREATMENTS,
    BOARD_KIND_GUIDANCE,
    BOARD_KIND_LABELS,
    BOARD_KIND_REALMS,
    BOARD_KIND_SIDEBAR_LABELS,
    BOARD_SIDEBAR_SECTION_GUIDANCE,
    BOARD_SIDEBAR_SECTION_LABELS,
    BoardKind,
    is_community_sidebar_board,
    is_desk_sidebar_board,
    is_location_board,
    is_location_sidebar_board,
    is_studio_sidebar_board,
    normalize_board_kind,
    normalize_board_sidebar_section,
)
from elbysodic.domain.context import RequestIdentityContext
from elbysodic.domain.models import (
    Board,
    Character,
    CharacterReserve,
    Community,
    CommunityInvitation,
    CommunityMembership,
    Material,
    Post,
    Role,
    SidebarSectionConfig,
    Thread,
    WantedAd,
    WantedAdInterest,
)
from elbysodic.services import policies
from elbysodic.services.access import DefaultRequestIdentity, RequestIdentityResolver
from elbysodic.services.applications import (
    accept_character_application as _accept_character_application,
)
from elbysodic.services.applications import applications_desk as _applications_desk
from elbysodic.services.applications import (
    read_application_review_room as _read_application_review_room,
)
from elbysodic.services.applications import (
    request_character_application_revision as _request_character_application_revision,
)
from elbysodic.services.applications import (
    submit_character_application as _submit_character_application,
)
from elbysodic.services.applications import update_application_draft as _update_application_draft
from elbysodic.services.applications import update_application_review as _update_application_review
from elbysodic.services.auth import (
    SESSION_TTL,
    LoginSession,
    create_login_session,
    hash_password,
    session_for_session_token,
    session_token_hash,
    verify_password,
)
from elbysodic.services.blueprints import preview_program_blueprint as _preview_program_blueprint
from elbysodic.services.casting import casting_desk as _casting_desk
from elbysodic.services.casting import (
    create_reserve_for_wanted_interest as _create_reserve_for_wanted_interest,
)
from elbysodic.services.casting import (
    express_prospective_wanted_interest as _express_prospective_wanted_interest,
)
from elbysodic.services.casting import express_wanted_interest as _express_wanted_interest
from elbysodic.services.casting import public_read_wanted_ad as _public_read_wanted_ad
from elbysodic.services.casting import public_wanted_ad_summary as _public_wanted_ad_summary
from elbysodic.services.casting import public_wanted_board as _public_wanted_board
from elbysodic.services.casting import read_wanted_ad as _read_wanted_ad
from elbysodic.services.casting import reserve_wanted_interest as _reserve_wanted_interest
from elbysodic.services.casting import (
    update_wanted_ad_lifecycle_status as _update_wanted_ad_lifecycle_status,
)
from elbysodic.services.casting import wanted_ad_summary as _wanted_ad_summary
from elbysodic.services.casting import wanted_board as _wanted_board
from elbysodic.services.claims import (
    application_claim_checks as _application_claim_checks,
)
from elbysodic.services.claims import (
    application_template_field_view as _application_template_field_view,
)
from elbysodic.services.claims import claims_directory as _claims_directory
from elbysodic.services.discovery import discover_plots as _discover_plots
from elbysodic.services.facets import (
    current_character_facet_ids as _current_character_facet_ids,
)
from elbysodic.services.facets import (
    facet_tags as _facet_tags,
)
from elbysodic.services.facets import resolve_facets as _resolve_facets
from elbysodic.services.identity import character_profile as _character_profile
from elbysodic.services.identity import (
    character_roster_dashboard as _character_roster_dashboard,
)
from elbysodic.services.identity import member_directory as _member_directory
from elbysodic.services.identity import member_profile as _member_profile
from elbysodic.services.identity import roster_activity as _roster_activity
from elbysodic.services.identity import selected_character as _selected_character
from elbysodic.services.interactions import read_realm_interaction as _read_realm_interaction
from elbysodic.services.interactions import realm_interaction_hub as _realm_interaction_hub
from elbysodic.services.interactions import (
    realm_interaction_summary as _realm_interaction_summary,
)
from elbysodic.services.interactions import submit_realm_interaction as _submit_realm_interaction
from elbysodic.services.markup import post_snippet
from elbysodic.services.materials import (
    current_event_for_facet_ids as _current_event_for_facet_ids,
)
from elbysodic.services.materials import material_detail as _material_detail
from elbysodic.services.materials import material_summary as _material_summary
from elbysodic.services.materials import public_material_detail as _public_material_detail
from elbysodic.services.materials import (
    update_material_production_state as _update_material_production_state,
)
from elbysodic.services.network import search_public_catalog as _search_public_catalog
from elbysodic.services.notifications import (
    count_visible_unread_notifications as _count_visible_unread_notifications,
)
from elbysodic.services.notifications import (
    mark_all_notifications_read as _mark_all_notifications_read,
)
from elbysodic.services.notifications import notification_inbox as _notification_inbox
from elbysodic.services.notifications import open_notification as _open_notification
from elbysodic.services.plot_hooks import (
    create_plot_hook as _create_plot_hook,
)
from elbysodic.services.plot_hooks import express_plot_hook_interest as _express_plot_hook_interest
from elbysodic.services.plot_hooks import read_plot_hook as _read_plot_hook
from elbysodic.services.plot_hooks import update_plot_hook as _update_plot_hook
from elbysodic.services.plotting import (
    create_plotting_room_from_plot_hook_interest as _create_plotting_room_from_plot_hook_interest,
)
from elbysodic.services.plotting import (
    create_plotting_room_from_wanted_interest as _create_plotting_room_from_wanted_interest,
)
from elbysodic.services.plotting import (
    create_plotting_room_message as _create_plotting_room_message,
)
from elbysodic.services.plotting import (
    create_thread_from_plotting_room as _create_thread_from_plotting_room,
)
from elbysodic.services.plotting import plotting_desk as _plotting_desk
from elbysodic.services.plotting import read_plotting_room as _read_plotting_room
from elbysodic.services.plotting import subscribe_plotting_room_live, unsubscribe_plotting_room_live
from elbysodic.services.plotting import update_plotting_room_plan as _update_plotting_room_plan
from elbysodic.services.posting import join_thread_as_current_character as _join_thread
from elbysodic.services.posting import read_post_editor as _read_post_editor
from elbysodic.services.posting import read_post_revisions as _read_post_revisions
from elbysodic.services.posting import reply_to_thread as _reply_to_thread
from elbysodic.services.posting import search_mentionables as _search_mentionables
from elbysodic.services.posting import start_thread as _start_thread
from elbysodic.services.posting import update_post as _update_post
from elbysodic.services.posting import update_thread_scene as _update_thread_scene
from elbysodic.services.posts import post_view as _post_view
from elbysodic.services.read_models import (
    MATERIAL_STATUSES,
    MATERIAL_TYPES,
    POST_ACCENT_STYLES,
    POST_BORDER_STYLES,
    POST_DENSITIES,
    POST_PROFILE_VARIANTS,
    POST_STYLE_PRESETS,
    POST_TITLE_STYLES,
    ActivityItem,
    ApplicationClaimCheck,
    ApplicationOnboarding,
    ApplicationReviewRoom,
    ApplicationsDesk,
    AttentionItem,
    BoardNavigationItem,
    BoardSummary,
    BoardTaxonomyItem,
    BoardThreadFilter,
    CastingDesk,
    CharacterPlotHookDetail,
    CharacterProfile,
    CharacterRosterDashboard,
    ClaimsDirectory,
    CreatedThread,
    DevPersonaView,
    DirectorStudio,
    EditablePostView,
    FacetTag,
    FirstRealmSetupResult,
    ForumView,
    LocationNavigationGroup,
    MaterialDetail,
    MaterialSummary,
    MemberDirectory,
    MemberProfile,
    Mentionable,
    MyThreadsDashboard,
    NavigationHealthWarning,
    NavigationPreviewItem,
    NavigationPreviewSection,
    NetworkBrowseFacet,
    NetworkExploreLane,
    NetworkExploreView,
    NetworkHomeView,
    NetworkReturnPath,
    NetworkSlice,
    NotificationInbox,
    PlotDiscovery,
    PlottingDesk,
    PlottingRoomDetail,
    PostRevisionHistory,
    PostStylePolicy,
    PublicCatalogCard,
    RealmInteractionDetail,
    RealmInteractionHub,
    RealmLaunchChecklistItem,
    RealmLaunchReadiness,
    StudioBoardEditor,
    StudioIdentityOption,
    StudioNetworkDirectory,
    StudioNetworkProgramView,
    StudioNetworkThemePreview,
    ThreadNavigationItem,
    ThreadSummary,
    ThreadView,
    WantedAdDetail,
    WantedAdSummary,
    WantedBoard,
    WorldHub,
)
from elbysodic.services.read_models import (
    POSTING_MODES as POSTING_MODES,
)
from elbysodic.services.read_models import (
    THREAD_STATUSES as THREAD_STATUSES,
)
from elbysodic.services.recovery import RecoveryKind, RecoveryView
from elbysodic.services.recovery import recovery_view as _recovery_view
from elbysodic.services.themes import (
    DEFAULT_THEME_TOKENS,
    ThemeHealthWarning,
    build_theme_tokens,
    community_theme_editor,
    community_theme_view,
    theme_health_warnings,
    theme_tokens_json,
)
from elbysodic.services.threads import (
    board_thread_summaries as _board_thread_summaries,
)
from elbysodic.services.threads import is_live_queue_thread as _is_live_queue_thread
from elbysodic.services.threads import is_unread as _is_unread
from elbysodic.services.threads import next_unread_thread as _next_unread_thread
from elbysodic.services.threads import read_thread_view as _read_thread_view
from elbysodic.services.threads import thread_needs_attention as _thread_needs_attention
from elbysodic.services.threads import thread_obligations as _thread_obligations
from elbysodic.services.timestamps import timestamp_key as _timestamp_key

DEFAULT_DATABASE_PATH = Path("var/elbysodic.sqlite3")
DATABASE_PATH_ENV = "ELBYSODIC_DB_PATH"
RAILWAY_VOLUME_MOUNT_PATH_ENV = "RAILWAY_VOLUME_MOUNT_PATH"
HERO_TREATMENTS = frozenset({"split", "background", "poster", "text"})
HERO_FOCAL_POINTS = frozenset({"center", "top", "bottom", "left", "right"})
HERO_OVERLAYS = frozenset({"none", "light", "medium", "heavy"})
HERO_HEIGHTS = frozenset({"compact", "standard", "immersive"})


def _load_viewer_role(
    repo: ForumRepository,
    community: Community,
    membership: CommunityMembership,
) -> Role:
    try:
        return repo.get_role(community.id, membership.role_id)
    except LookupError as exc:
        raise PermissionError("realm membership role is not valid for this community") from exc


@dataclass(frozen=True, slots=True)
class CreatedInvitation:
    invitation: CommunityInvitation
    token: str

    @property
    def path(self) -> str:
        return f"/invite/{self.token}"


@dataclass(frozen=True, slots=True)
class AcceptedInvitation:
    invitation: CommunityInvitation
    session: LoginSession
    identity: RequestIdentityContext
    first_character: Character | None

    @property
    def next_path(self) -> str:
        if self.first_character is not None:
            return f"/c/{self.identity.community_slug}/desk"
        return f"/c/{self.identity.community_slug}/applications/new"


@dataclass(frozen=True, slots=True)
class GuidedRealmBuilderResult:
    scene_hub: Board
    premise: Material
    application_guide: Material
    created_labels: tuple[str, ...]

    @property
    def status_message(self) -> str:
        if not self.created_labels:
            return "Realm Builder found the minimum launch pieces already in place."
        return f"Realm Builder added {', '.join(self.created_labels)}."


@dataclass(frozen=True, slots=True)
class InvitationManagementItem:
    invitation: CommunityInvitation
    status_label: str
    can_revoke: bool


class AppServices:
    """Small application service facade for the dev forum."""

    def __init__(
        self,
        repo: ForumRepository,
        seed: DemoSeed | None,
        *,
        database: Database | None = None,
        identity_resolver: RequestIdentityResolver | None = None,
        identity_context: RequestIdentityContext | None = None,
        allow_development_identity: bool = True,
        require_session: bool = False,
        repo_context: AbstractContextManager[ForumRepository] | None = None,
        owns_repo: bool = True,
    ) -> None:
        self.repo = repo
        self._database = database
        self._seed = seed
        self._allow_development_identity = allow_development_identity
        self._require_session = require_session
        self._identity_resolver = identity_resolver or RequestIdentityResolver(
            repo,
            _default_request_identity(seed),
            allow_development_identity=allow_development_identity,
            require_session=require_session,
        )
        self._identity_context = identity_context
        self._viewer: ForumView | None = None
        self._repo_context = repo_context
        self._owns_repo = owns_repo
        self._closed = False

    @property
    def seed(self) -> DemoSeed:
        if self._seed is None:
            raise RuntimeError("demo seed is not configured for these services")
        return self._seed

    def for_request(self, request: object) -> AppServices:
        """Return a request-scoped facade."""

        if self._database is not None:
            repo_context = self._database.repository()
            repo = repo_context.__enter__()
            identity_resolver = RequestIdentityResolver(
                repo,
                _default_request_identity(self._seed),
                allow_development_identity=self._allow_development_identity,
                require_session=self._require_session,
            )
            return AppServices(
                repo,
                self._seed,
                database=self._database,
                identity_resolver=identity_resolver,
                identity_context=identity_resolver.resolve(request),
                allow_development_identity=self._allow_development_identity,
                require_session=self._require_session,
                repo_context=repo_context,
            )
        return AppServices(
            self.repo,
            self._seed,
            identity_resolver=self._identity_resolver,
            identity_context=self._identity_resolver.resolve(request),
            allow_development_identity=self._allow_development_identity,
            require_session=self._require_session,
            owns_repo=False,
        )

    def with_request_auth(self, *, production: bool) -> AppServices:
        """Return a facade with request identity rules for the runtime mode."""

        return AppServices(
            self.repo,
            self._seed,
            database=self._database,
            identity_resolver=RequestIdentityResolver(
                self.repo,
                _default_request_identity(self._seed),
                allow_development_identity=not production,
                require_session=production,
            ),
            allow_development_identity=not production,
            require_session=production,
            owns_repo=self._owns_repo,
        )

    def close(self) -> None:
        """Release the shared repository connection owned by this service facade."""

        if self._closed:
            return
        self._closed = True
        if self._repo_context is not None:
            self._repo_context.__exit__(None, None, None)
            return
        if not self._owns_repo:
            return
        connection = self.repo.connection
        with suppress(sqlite3.Error):
            if connection.in_transaction:
                connection.rollback()
        with suppress(sqlite3.Error):
            if _connection_has_filesystem_database(connection):
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        with suppress(sqlite3.Error):
            connection.close()

    def viewer(self) -> ForumView:
        if self._identity_context is not None and self._viewer is not None:
            return self._viewer
        identity = self._identity_context or self._identity_resolver.resolve()
        community = self.repo.get_community(identity.community_id)
        try:
            membership = self.repo.get_membership(community.id, identity.membership_id)
        except LookupError as exc:
            raise PermissionError("realm membership is no longer available") from exc
        if membership.user_id != identity.user_id:
            raise PermissionError(
                f"membership {membership.id} does not belong to user {identity.user_id}"
            )
        if not membership.is_active:
            raise PermissionError(f"membership {membership.id} is not active")
        role = _load_viewer_role(self.repo, community, membership)
        roster = self.repo.list_characters(community.id, membership.id)
        current_character = _resolve_current_character(self.repo, membership, roster)
        navigation_boards = _board_navigation(self.repo, community.id, membership, role)
        sidebar_sections = _sidebar_sections_by_key(self.repo, community.id)
        viewer = ForumView(
            community=community,
            membership=membership,
            role=role,
            current_character=current_character,
            roster=roster,
            navigation_boards=navigation_boards,
            location_navigation_boards=[
                item
                for item in navigation_boards
                if item.board.parent_board_id is None
                and is_location_board(item.board)
                and is_location_sidebar_board(item.board)
            ],
            location_navigation_groups=_location_navigation_groups(navigation_boards),
            location_sidebar_section=sidebar_sections["locations"],
            community_navigation_boards=[
                item
                for item in navigation_boards
                if item.board.parent_board_id is None and is_community_sidebar_board(item.board)
            ],
            community_sidebar_section=sidebar_sections["community"],
            desk_navigation_boards=[
                item for item in navigation_boards if is_desk_sidebar_board(item.board)
            ],
            desk_sidebar_section=sidebar_sections["desk"],
            studio_navigation_boards=[
                item for item in navigation_boards if is_studio_sidebar_board(item.board)
            ],
            studio_sidebar_section=sidebar_sections["studio"],
            unread_notification_count=_count_visible_unread_notifications(
                self.repo,
                community.id,
                membership,
                role,
            ),
            identity_options=self._identity_options(identity),
            program_theme=community_theme_view(self.repo.get_default_theme(community.id)),
        )
        if self._identity_context is not None:
            self._viewer = viewer
        return viewer

    def _invalidate_viewer(self) -> None:
        self._viewer = None

    def _identity_options(self, identity: RequestIdentityContext) -> list[StudioIdentityOption]:
        options: list[StudioIdentityOption] = []
        for membership in self.repo.list_memberships_for_user(identity.user_id):
            if not membership.is_active:
                continue
            community = self.repo.get_community(membership.community_id)
            try:
                role = self.repo.get_role(community.id, membership.role_id)
            except LookupError:
                continue
            roster = self.repo.list_characters(community.id, membership.id)
            options.append(
                StudioIdentityOption(
                    community=community,
                    membership=membership,
                    role=role,
                    current_character=_resolve_current_character(self.repo, membership, roster),
                    unread_notification_count=_count_visible_unread_notifications(
                        self.repo,
                        community.id,
                        membership,
                        role,
                    ),
                    is_current=(
                        community.id == identity.community_id
                        and membership.id == identity.membership_id
                    ),
                )
            )
        return sorted(
            options,
            key=lambda option: (
                0 if option.is_current else 1,
                option.community.name,
                option.membership.display_name,
                option.membership.id,
            ),
        )

    def switch_dev_identity(self, membership_id: int) -> RequestIdentityContext:
        identity = self._identity_context or self._identity_resolver.resolve()
        return self._identity_for_membership(identity.user_id, membership_id)

    def command_result(self, command_key: str, token: str) -> str | None:
        if not token:
            return None
        viewer = self.viewer()
        submission = self.repo.get_command_submission(
            viewer.community.id,
            viewer.membership.id,
            command_key=command_key,
            token=token,
        )
        return None if submission is None else submission.result_path

    def reserve_command(self, command_key: str, token: str) -> bool:
        if not token:
            return True
        viewer = self.viewer()
        return self.repo.reserve_command_submission(
            viewer.community.id,
            viewer.membership.id,
            command_key=command_key,
            token=token,
        )

    def complete_command(self, command_key: str, token: str, result_path: str) -> None:
        if not token:
            return
        viewer = self.viewer()
        self.repo.complete_command_submission(
            viewer.community.id,
            viewer.membership.id,
            command_key=command_key,
            token=token,
            result_path=result_path,
        )

    def recovery_view(self, *, kind: RecoveryKind, slug: str) -> RecoveryView:
        return _recovery_view(self.repo, self.viewer(), kind=kind, slug=slug)

    def switch_session_identity(
        self,
        session_token: str,
        membership_id: int,
    ) -> RequestIdentityContext:
        session = session_for_session_token(self.repo, session_token)
        if session is None:
            raise PermissionError("login is required")
        identity = self._identity_for_membership(session.user_id, membership_id)
        self.repo.update_user_session_identity(
            session.id,
            community_id=identity.community_id,
            membership_id=identity.membership_id,
        )
        return identity

    def _identity_for_membership(
        self,
        user_id: int,
        membership_id: int,
    ) -> RequestIdentityContext:
        for membership in self.repo.list_memberships_for_user(user_id):
            if membership.id != membership_id:
                continue
            if not membership.is_active:
                raise PermissionError(f"membership {membership.id} is not active")
            community = self.repo.get_community(membership.community_id)
            _load_viewer_role(self.repo, community, membership)
            return RequestIdentityContext(
                community_id=community.id,
                community_slug=community.slug,
                user_id=user_id,
                membership_id=membership.id,
            )
        raise PermissionError(f"user {user_id} cannot switch to membership {membership_id}")

    def dev_personas(self) -> list[DevPersonaView]:
        identity = self._identity_context or self._identity_resolver.resolve()
        return [self._dev_persona_view(persona, identity) for persona in SEED_PERSONAS]

    def switch_dev_persona(self, persona_key: str) -> RequestIdentityContext:
        persona = seed_persona_by_key(persona_key)
        view = self._dev_persona_view(
            persona,
            self._identity_context or self._identity_resolver.resolve(),
        )
        if not view.can_switch:
            raise PermissionError(f"persona {persona.key} is inactive")
        return RequestIdentityContext(
            community_id=view.community.id,
            community_slug=view.community.slug,
            user_id=view.user.id,
            membership_id=view.membership.id,
        )

    def _dev_persona_view(
        self,
        persona: SeedPersona,
        identity: RequestIdentityContext,
    ) -> DevPersonaView:
        context = resolve_seed_persona(self.repo, persona.key)
        return DevPersonaView(
            key=persona.key,
            label=persona.label,
            purpose=persona.purpose,
            default_path=persona.default_path,
            user=context.user,
            community=context.community,
            membership=context.membership,
            role=context.role,
            character=context.character,
            can_switch=context.membership.is_active,
            is_current=(
                identity.community_id == context.community.id
                and identity.membership_id == context.membership.id
            ),
            can_manage_studio=(
                policies.can_manage_world(context.membership, context.role)
                or policies.can_manage_casting(context.membership, context.role)
                or policies.can_manage_navigation(context.membership, context.role)
            ),
        )

    def login(self, email: str, password: str) -> tuple[LoginSession, RequestIdentityContext]:
        session = create_login_session(self.repo, email, password)
        try:
            current_identity = self._identity_context or self._identity_resolver.resolve()
            preferred_community_id = current_identity.community_id
        except PermissionError:
            preferred_community_id = None if self._seed is None else self._seed.community.id
        identity = self._default_identity_for_user(
            session.user.id,
            preferred_community_id=preferred_community_id,
        )
        self.repo.update_user_session_identity(
            session.session_id,
            community_id=identity.community_id,
            membership_id=identity.membership_id,
        )
        return session, identity

    def logout(self, session_token: str) -> None:
        if session_token:
            self.repo.revoke_user_session_by_token_hash(session_token_hash(session_token))

    def create_first_realm(
        self,
        *,
        realm_name: str,
        realm_slug: str,
        director_email: str,
        director_password: str,
        director_username: str,
        director_display_name: str,
    ) -> FirstRealmSetupResult:
        clean_realm_name = realm_name.strip()
        if not clean_realm_name:
            raise ValueError("realm name is required")
        clean_realm_slug = _slugify_with_fallback(realm_slug or clean_realm_name, "realm")
        clean_email = director_email.strip().lower()
        if not clean_email:
            raise ValueError("director email is required")
        if not director_password:
            raise ValueError("director password is required")
        clean_display_name = director_display_name.strip() or "Director"
        clean_username = _slugify_with_fallback(
            director_username or clean_display_name or clean_email.split("@", 1)[0],
            "director",
        )
        with self.repo.transaction():
            if self.repo.list_communities():
                raise ValueError("first realm setup requires an empty community table")
            community = self.repo.create_community(clean_realm_slug, clean_realm_name)
            role = self.repo.create_role(
                community.id,
                "director",
                "Director",
                is_admin=True,
            )
            self.repo.create_role(community.id, "member", "Member")
            user = self.repo.create_user(clean_email, hash_password(director_password))
            self.repo.create_membership(
                community.id,
                user.id,
                role.id,
                clean_username,
                clean_display_name,
            )
            self.repo.ensure_sidebar_section_defaults(community.id)
            self.repo.upsert_default_theme(
                community.id,
                slug=str(DEFAULT_THEME_TOKENS["slug"]),
                name=str(DEFAULT_THEME_TOKENS["name"]),
                tokens_json=theme_tokens_json(DEFAULT_THEME_TOKENS),
            )
        return FirstRealmSetupResult(
            community=self.repo.get_community_by_slug(clean_realm_slug),
            user=self.repo.get_user_by_email(clean_email),
            membership=self.repo.get_membership_for_user(community.id, user.id),
            role=self.repo.get_role_by_slug(community.id, "director"),
        )

    def create_writer_invitation(self, email: str, *, days_valid: int = 14) -> CreatedInvitation:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError("director access is required to invite writers")
        clean_email = email.strip().lower()
        if "@" not in clean_email:
            raise ValueError("invitee email is required")
        if days_valid <= 0:
            raise ValueError("invite expiration must be in the future")
        try:
            role = self.repo.get_role_by_slug(viewer.community.id, "member")
        except LookupError:
            role = self.repo.create_role(viewer.community.id, "member", "Member")
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(UTC) + timedelta(days=days_valid)).isoformat(timespec="seconds")
        invitation = self.repo.create_community_invitation(
            viewer.community.id,
            email=clean_email,
            role_id=role.id,
            invited_by_membership_id=viewer.membership.id,
            token_hash=session_token_hash(token),
            expires_at=expires_at,
        )
        return CreatedInvitation(invitation=invitation, token=token)

    def writer_invitations(self) -> list[InvitationManagementItem]:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError("director access is required to manage invitations")
        return [
            _invitation_management_item(invitation)
            for invitation in self.repo.list_community_invitations(viewer.community.id)
        ]

    def revoke_writer_invitation(self, invitation_id: int) -> CommunityInvitation:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError("director access is required to revoke invitations")
        invitation = self.repo.get_community_invitation(viewer.community.id, invitation_id)
        item = _invitation_management_item(invitation)
        if not item.can_revoke:
            raise ValueError("only pending invitations can be revoked")
        return self.repo.revoke_community_invitation(viewer.community.id, invitation.id)

    def update_realm_launch_status(self, launch_status: str) -> Community:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError("director access is required to update launch status")
        return self.repo.update_community_launch_status(viewer.community.id, launch_status)

    def apply_guided_realm_builder_minimum(
        self,
        *,
        scene_hub_name: str = "",
        premise_summary: str = "",
        application_summary: str = "",
    ) -> GuidedRealmBuilderResult:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError("director access is required to shape the realm")
        clean_scene_hub_name = scene_hub_name.strip() or "Opening Scenes"
        clean_premise_summary = premise_summary.strip() or (
            f"{viewer.community.name} is taking shape. Directors can replace this "
            "premise with the realm's opening pitch before inviting writers."
        )
        clean_application_summary = application_summary.strip() or (
            "Application guidance will tell incoming writers what to bring for their first face."
        )
        created_labels: list[str] = []
        with self.repo.transaction():
            self.repo.ensure_sidebar_section_defaults(viewer.community.id)
            self.repo.upsert_default_theme(
                viewer.community.id,
                slug=str(DEFAULT_THEME_TOKENS["slug"]),
                name=str(DEFAULT_THEME_TOKENS["name"]),
                tokens_json=theme_tokens_json(DEFAULT_THEME_TOKENS),
            )
            scene_hub = _first_public_scene_hub(self.repo, viewer.community.id)
            if scene_hub is None:
                scene_hub = self.repo.create_board(
                    viewer.community.id,
                    _slugify_with_fallback(clean_scene_hub_name, "opening-scenes"),
                    clean_scene_hub_name,
                    "A public scene hub for first threads and opening beats.",
                    board_kind="location",
                    sidebar_section="locations",
                    tagline="First scenes and opening threads.",
                    sort_order=10,
                    navigation_order=10,
                )
                created_labels.append("scene hub")
            premise = _first_material_of_type(self.repo, viewer.community.id, "premise")
            if premise is None:
                premise = self.repo.create_material(
                    viewer.community.id,
                    "realm-premise",
                    f"{viewer.community.name} Premise",
                    material_type="premise",
                    summary=clean_premise_summary,
                    body=clean_premise_summary,
                    status="published",
                    sort_order=10,
                    is_featured=True,
                )
                created_labels.append("premise material")
            application_guide = _first_material_of_type(
                self.repo,
                viewer.community.id,
                "application",
            )
            if application_guide is None:
                application_guide = self.repo.create_material(
                    viewer.community.id,
                    "application-guide",
                    "Application Guide",
                    material_type="application",
                    summary=clean_application_summary,
                    body=clean_application_summary,
                    status="published",
                    sort_order=20,
                )
                created_labels.append("application guide")
        return GuidedRealmBuilderResult(
            scene_hub=scene_hub,
            premise=premise,
            application_guide=application_guide,
            created_labels=tuple(created_labels),
        )

    def read_invitation(self, token: str) -> tuple[CommunityInvitation, Community]:
        invitation = self.repo.get_community_invitation_by_token_hash(session_token_hash(token))
        self._ensure_invitation_can_be_accepted(invitation)
        return invitation, self.repo.get_community(invitation.community_id)

    def accept_invitation(
        self,
        token: str,
        *,
        password: str,
        username: str,
        display_name: str,
        first_face_name: str = "",
    ) -> AcceptedInvitation:
        invitation = self.repo.get_community_invitation_by_token_hash(session_token_hash(token))
        self._ensure_invitation_can_be_accepted(invitation)
        if not password:
            raise ValueError("password is required")
        clean_display_name = display_name.strip() or invitation.email.split("@", 1)[0]
        clean_username = _unique_membership_username(
            self.repo,
            invitation.community_id,
            _slugify_with_fallback(username or clean_display_name, "writer"),
        )
        clean_face_name = first_face_name.strip()
        with self.repo.transaction():
            try:
                user = self.repo.get_user_by_email(invitation.email)
            except LookupError:
                user = self.repo.create_user(invitation.email, hash_password(password))
            else:
                if not verify_password(password, user.password_hash):
                    raise PermissionError("email or password is incorrect")
            try:
                self.repo.get_membership_for_user(invitation.community_id, user.id)
            except LookupError:
                membership = self.repo.create_membership(
                    invitation.community_id,
                    user.id,
                    invitation.role_id,
                    clean_username,
                    clean_display_name,
                )
            else:
                raise ValueError("this account is already a member of the invited realm")
            character = None
            if clean_face_name:
                character = self.repo.create_character(
                    invitation.community_id,
                    membership.id,
                    _unique_character_slug(
                        self.repo,
                        invitation.community_id,
                        _slugify_with_fallback(clean_face_name, "face"),
                    ),
                    clean_face_name,
                    application_status="accepted",
                    make_default=True,
                )
            accepted_invitation = self.repo.accept_community_invitation(
                invitation.id,
                user_id=user.id,
                membership_id=membership.id,
            )
            session = self._create_session_for_user(
                user.id,
                community_id=invitation.community_id,
                membership_id=membership.id,
            )
        community = self.repo.get_community(invitation.community_id)
        identity = RequestIdentityContext(
            community_id=community.id,
            community_slug=community.slug,
            user_id=user.id,
            membership_id=membership.id,
        )
        return AcceptedInvitation(
            invitation=accepted_invitation,
            session=session,
            identity=identity,
            first_character=character,
        )

    def _create_session_for_user(
        self,
        user_id: int,
        *,
        community_id: int,
        membership_id: int,
    ) -> LoginSession:
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(UTC) + SESSION_TTL).isoformat(timespec="seconds")
        stored_session = self.repo.create_user_session(
            user_id,
            session_token_hash(token),
            expires_at=expires_at,
        )
        self.repo.update_user_session_identity(
            stored_session.id,
            community_id=community_id,
            membership_id=membership_id,
        )
        return LoginSession(
            session_id=stored_session.id,
            user=self.repo.get_user(user_id),
            token=token,
            expires_at=expires_at,
        )

    def _ensure_invitation_can_be_accepted(self, invitation: CommunityInvitation) -> None:
        if invitation.status != "pending" or invitation.revoked_at is not None:
            raise PermissionError("this invitation is no longer open")
        if invitation.accepted_at is not None:
            raise PermissionError("this invitation has already been accepted")
        if invitation.expires_at is not None:
            try:
                expires_at = datetime.fromisoformat(invitation.expires_at)
            except ValueError as exc:
                raise PermissionError("this invitation has an invalid expiration") from exc
            if expires_at <= datetime.now(UTC):
                raise PermissionError("this invitation has expired")

    def _default_identity_for_user(
        self,
        user_id: int,
        *,
        preferred_community_id: int | None = None,
    ) -> RequestIdentityContext:
        if preferred_community_id is not None:
            try:
                membership = self.repo.get_membership_for_user(preferred_community_id, user_id)
                if membership.is_active:
                    community = self.repo.get_community(preferred_community_id)
                    return RequestIdentityContext(
                        community_id=community.id,
                        community_slug=community.slug,
                        user_id=user_id,
                        membership_id=membership.id,
                    )
            except LookupError:
                pass
        for membership in self.repo.list_memberships_for_user(user_id):
            if not membership.is_active:
                continue
            community = self.repo.get_community(membership.community_id)
            return RequestIdentityContext(
                community_id=community.id,
                community_slug=community.slug,
                user_id=user_id,
                membership_id=membership.id,
            )
        raise PermissionError(f"user {user_id} has no active memberships")

    def studio_network(self) -> StudioNetworkDirectory:
        identity = self._identity_context or self._identity_resolver.resolve()
        programs: list[StudioNetworkProgramView] = []
        for membership in self.repo.list_memberships_for_user(identity.user_id):
            if not membership.is_active:
                continue
            community = self.repo.get_community(membership.community_id)
            role = self.repo.get_role(community.id, membership.role_id)
            roster = self.repo.list_characters(community.id, membership.id)
            materials = self.repo.list_materials(community.id)
            wanted_ads = self.repo.list_wanted_ads(community.id)
            community_characters = self.repo.list_community_characters(community.id)
            theme = community_theme_view(self.repo.get_default_theme(community.id))
            programs.append(
                StudioNetworkProgramView(
                    community=community,
                    membership=membership,
                    role=role,
                    current_character=_resolve_current_character(self.repo, membership, roster),
                    premise=_first_material_summary(materials, "premise", self.repo, community.id),
                    current_event=_first_material_summary(
                        materials,
                        "event",
                        self.repo,
                        community.id,
                    ),
                    roster_count=len(community_characters),
                    open_wanted_count=sum(
                        1 for wanted_ad in wanted_ads if wanted_ad.status == "open"
                    ),
                    application_material_count=sum(
                        1 for material in materials if material.material_type == "application"
                    ),
                    claim_type_count=len(self.repo.list_claim_types(community.id)),
                    application_count=_network_application_count(
                        community_characters,
                        can_review=policies.can_manage_applications(membership, role),
                        membership_id=membership.id,
                    ),
                    plotting_room_count=len(
                        self.repo.list_plotting_rooms_for_membership(
                            community.id,
                            membership.id,
                        )
                    ),
                    unread_notification_count=_count_visible_unread_notifications(
                        self.repo,
                        community.id,
                        membership,
                        role,
                    ),
                    theme_preview=_network_theme_preview(theme),
                    is_current=(
                        community.id == identity.community_id
                        and membership.id == identity.membership_id
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

    def public_studio_network(self) -> StudioNetworkDirectory:
        programs: list[StudioNetworkProgramView] = []
        for community in self.repo.list_communities():
            materials = self.repo.list_materials(community.id, status="published")
            if not _is_public_network_ready(self.repo, community, materials):
                continue
            wanted_ads = self.repo.list_wanted_ads(community.id)
            community_characters = self.repo.list_community_characters(community.id)
            theme = community_theme_view(self.repo.get_default_theme(community.id))
            programs.append(
                StudioNetworkProgramView(
                    community=community,
                    membership=None,
                    role=None,
                    current_character=None,
                    premise=_first_material_summary(materials, "premise", self.repo, community.id),
                    current_event=_first_material_summary(
                        materials,
                        "event",
                        self.repo,
                        community.id,
                    ),
                    roster_count=len(community_characters),
                    open_wanted_count=sum(
                        1 for wanted_ad in wanted_ads if wanted_ad.status == "open"
                    ),
                    application_material_count=sum(
                        1 for material in materials if material.material_type == "application"
                    ),
                    claim_type_count=len(self.repo.list_claim_types(community.id)),
                    application_count=0,
                    plotting_room_count=0,
                    unread_notification_count=0,
                    theme_preview=_network_theme_preview(theme),
                    is_current=False,
                )
            )
        return StudioNetworkDirectory(programs=programs)

    def network_home(self) -> NetworkHomeView:
        cards = self._public_catalog_cards()
        return_path = None
        try:
            viewer = self.viewer()
        except PermissionError:
            viewer = None
        if viewer is not None:
            return_path = NetworkReturnPath(
                desk_href=f"/c/{viewer.community.slug}/desk",
                notification_href="/notifications",
                unread_notification_count=viewer.unread_notification_count,
            )
        return NetworkHomeView(
            featured=cards[0] if cards else None,
            slices=[
                NetworkSlice("Trending realms", "/network", cards),
                NetworkSlice("Superhero crisis", "/network?q=superhero", cards),
                NetworkSlice("Magic, survival, and small towns", "/network?q=magic", cards),
            ],
            browse_facets=_network_browse_facets(),
            return_path=return_path,
        )

    def network_explore(self, query: str = "") -> NetworkExploreView:
        cards = self._public_catalog_cards()
        return NetworkExploreView(
            query=query.strip(),
            browse_facets=_network_browse_facets(),
            relationship_lanes=_network_explore_lanes(),
            results=_search_public_catalog(cards, query),
        )

    def _public_catalog_cards(self) -> list[PublicCatalogCard]:
        return [
            _public_catalog_card_from_program(program)
            for program in self.public_studio_network().programs
        ]

    def public_studio_program(self, community_slug: str) -> StudioNetworkProgramView:
        community = self._public_preview_community(community_slug)
        materials = self.repo.list_materials(community.id, status="published")
        wanted_ads = self.repo.list_wanted_ads(community.id, status=None)
        community_characters = self.repo.list_community_characters(community.id)
        theme = community_theme_view(self.repo.get_default_theme(community.id))
        return StudioNetworkProgramView(
            community=community,
            membership=None,
            role=None,
            current_character=None,
            premise=_first_material_summary(materials, "premise", self.repo, community.id),
            current_event=_first_material_summary(
                materials,
                "event",
                self.repo,
                community.id,
            ),
            roster_count=len(community_characters),
            open_wanted_count=sum(1 for wanted_ad in wanted_ads if wanted_ad.status == "open"),
            application_material_count=sum(
                1 for material in materials if material.material_type == "application"
            ),
            claim_type_count=len(self.repo.list_claim_types(community.id)),
            application_count=0,
            plotting_room_count=0,
            unread_notification_count=0,
            theme_preview=_network_theme_preview(theme),
            is_current=False,
        )

    def public_world_hub(self, community_slug: str) -> WorldHub:
        community = self._public_preview_community(community_slug)
        materials = [
            _material_summary(self.repo, community.id, material)
            for material in self.repo.list_materials(community.id)
        ]
        additional_materials = [item for item in materials if not item.material.is_featured]
        return WorldHub(
            featured=[item for item in materials if item.material.is_featured],
            guides=[
                item
                for item in additional_materials
                if item.material.material_type in {"premise", "guide", "factions"}
            ],
            events=[item for item in materials if item.material.material_type == "event"],
            application_materials=[
                item
                for item in additional_materials
                if item.material.material_type == "application"
            ],
            can_manage=False,
        )

    def public_read_material(self, community_slug: str, material_slug: str) -> MaterialDetail:
        community = self._public_preview_community(community_slug)
        material = self.repo.get_material_by_slug(community.id, material_slug)
        if material.status != "published":
            raise LookupError(f"material not found in community {community.id}: {material_slug}")
        return _public_material_detail(
            self.repo,
            community.id,
            material,
            wanted_summary_factory=lambda wanted_ad: _public_wanted_ad_summary(
                self.repo,
                community.id,
                wanted_ad,
            ),
        )

    def public_wanted_ads(self, community_slug: str) -> WantedBoard:
        community = self._public_preview_community(community_slug)
        return _public_wanted_board(self.repo, community.id)

    def public_read_wanted_ad(self, community_slug: str, wanted_slug: str) -> WantedAdDetail:
        community = self._public_preview_community(community_slug)
        return _public_read_wanted_ad(self.repo, community.id, wanted_slug)

    def _public_preview_community(self, community_slug: str) -> Community:
        community = self.repo.get_community_by_slug(community_slug)
        materials = self.repo.list_materials(community.id)
        if not _is_public_network_ready(self.repo, community, materials):
            raise LookupError(f"community not available for public preview: {community_slug}")
        return community

    def list_boards(self) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        summaries: list[BoardSummary] = []
        for board in self.repo.list_boards(viewer.community.id):
            if not policies.can_view_board(viewer.membership, board, viewer.role):
                continue
            summaries.append(_board_summary(self.repo, viewer, board, current_facet_ids))
        return summaries

    def child_board_summaries(self, board: Board) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        return [
            _board_summary(self.repo, viewer, child, current_facet_ids)
            for child in self.repo.list_child_boards(viewer.community.id, board.id)
            if policies.can_view_board(viewer.membership, child, viewer.role)
        ]

    def sibling_board_summaries(self, board: Board) -> list[BoardSummary]:
        viewer = self.viewer()
        current_facet_ids = _current_character_facet_ids(self.repo, viewer)
        siblings = self.repo.list_child_boards(viewer.community.id, board.parent_board_id)
        return [
            _board_summary(self.repo, viewer, sibling, current_facet_ids)
            for sibling in siblings
            if sibling.id != board.id
            and is_location_board(sibling)
            and policies.can_view_board(viewer.membership, sibling, viewer.role)
        ]

    def board_summary(self, board: Board) -> BoardSummary:
        viewer = self.viewer()
        return _board_summary(
            self.repo,
            viewer,
            board,
            _current_character_facet_ids(self.repo, viewer),
        )

    def parent_board(self, board: Board) -> Board | None:
        if board.parent_board_id is None:
            return None
        viewer = self.viewer()
        parent = self.repo.get_board(viewer.community.id, board.parent_board_id)
        if not policies.can_view_board(viewer.membership, parent, viewer.role):
            return None
        return parent

    def recent_activity(self, *, limit: int = 6) -> list[ActivityItem]:
        viewer = self.viewer()
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items: list[ActivityItem] = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            for post in self.repo.list_posts(viewer.community.id, thread.id):
                post_view = _post_view(self.repo, viewer.community.id, post)
                items.append(
                    ActivityItem(
                        board=board,
                        thread=thread,
                        post=post_view,
                        snippet=post_view.snippet,
                        is_unread=_is_unread(
                            self.repo,
                            viewer.community.id,
                            viewer.membership.id,
                            thread,
                        ),
                    )
                )
        return sorted(
            items,
            key=lambda item: (_timestamp_key(item.post.post.created_at), item.post.post.id),
            reverse=True,
        )[:limit]

    def needs_attention(self, *, limit: int = 5) -> list[AttentionItem]:
        viewer = self.viewer()
        roster_character_ids = {character.id for character in viewer.roster}
        visible_boards = {
            board.id: board
            for board in self.repo.list_boards(viewer.community.id)
            if policies.can_view_board(viewer.membership, board, viewer.role)
        }
        items: list[AttentionItem] = []
        for thread in self.repo.list_threads(viewer.community.id):
            board = visible_boards.get(thread.board_id)
            if board is None:
                continue
            if not _is_live_queue_thread(thread):
                continue
            posts = self.repo.list_posts(viewer.community.id, thread.id)
            latest_post = posts[-1] if posts else None
            if latest_post is None:
                continue
            if not _thread_needs_attention(
                self.repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
                latest_post,
                roster_character_ids,
            ):
                continue
            items.append(
                AttentionItem(
                    board=board,
                    thread=thread,
                    latest_post=_post_view(self.repo, viewer.community.id, latest_post),
                    reply_count=max(0, len(posts) - 1),
                    snippet=post_snippet(latest_post.body),
                )
            )
        return sorted(
            items,
            key=lambda item: (
                _timestamp_key(item.latest_post.post.created_at),
                item.latest_post.post.id,
            ),
            reverse=True,
        )[:limit]

    def my_threads(self, *, character_slug: str | None = None) -> MyThreadsDashboard:
        viewer = self.viewer()
        selected_character = _selected_character(self.repo, viewer, character_slug)
        target_ids = (
            {selected_character.id}
            if selected_character is not None
            else {character.id for character in viewer.roster}
        )
        sorted_items = _thread_obligations(self.repo, viewer, target_ids)
        return MyThreadsDashboard(
            needs_reply=[item for item in sorted_items if item.needs_reply],
            waiting_on_others=[item for item in sorted_items if item.waiting_on_others],
            started_by_me=[item for item in sorted_items if item.is_started_by_roster],
            participated=sorted_items,
            selected_character=selected_character,
            roster_activity=_roster_activity(self.repo, viewer),
        )

    def character_roster(self) -> CharacterRosterDashboard:
        viewer = self.viewer()
        return _character_roster_dashboard(self.repo, viewer)

    def applications_desk(self) -> ApplicationsDesk:
        viewer = self.viewer()
        return _applications_desk(self.repo, viewer)

    def application_onboarding(self) -> ApplicationOnboarding:
        viewer = self.viewer()
        return ApplicationOnboarding(
            facets=_facet_tags(
                self.repo,
                viewer.community.id,
                self.repo.list_facets(viewer.community.id),
            ),
            application_materials=[
                _material_summary(self.repo, viewer.community.id, material)
                for material in self.repo.list_materials(viewer.community.id)
                if material.material_type == "application"
            ],
            interactions=[
                _realm_interaction_summary(self.repo, viewer, interaction)
                for interaction in self.repo.list_realm_interactions(
                    viewer.community.id,
                    placement="application",
                )
            ],
            template_fields=[
                _application_template_field_view(self.repo, viewer.community.id, field)
                for field in self.repo.list_application_template_fields(viewer.community.id)
            ],
        )

    def application_claim_checks(
        self,
        field_values: dict[int, str],
        *,
        character_id: int | None = None,
        application_id: int | None = None,
    ) -> dict[int, ApplicationClaimCheck]:
        viewer = self.viewer()
        return _application_claim_checks(
            self.repo,
            viewer.community.id,
            field_values,
            character_id=character_id,
            application_id=application_id,
        )

    def claims_directory(
        self,
        *,
        status_filter: str | None = None,
        search_query: str = "",
    ) -> ClaimsDirectory:
        viewer = self.viewer()
        return _claims_directory(
            self.repo,
            viewer,
            status_filter=status_filter,
            search_query=search_query,
        )

    def claimable_characters(self) -> list[Character]:
        viewer = self.viewer()
        if not policies.can_manage_applications(viewer.membership, viewer.role):
            return []
        return self.repo.list_community_characters(viewer.community.id)

    def create_director_claim(
        self,
        claim_type_id: int,
        *,
        label: str,
        status: str = "claimed",
        character_id: int | None = None,
        notes: str = "",
    ):
        viewer = self.viewer()
        if not policies.can_manage_applications(viewer.membership, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot manage claims")
        clean_label = label.strip()
        if not clean_label:
            raise ValueError("claim label is required")
        claim_status = _normalize_claim_status(status)
        if claim_status == "claimed" and character_id is None:
            raise ValueError("claimed rows need a face")
        return self.repo.create_character_claim(
            viewer.community.id,
            claim_type_id,
            _claim_value_key(clean_label),
            clean_label,
            character_id=character_id,
            status=claim_status,
            notes=notes.strip(),
        )

    def update_director_claim(
        self,
        claim_id: int,
        *,
        label: str,
        status: str = "claimed",
        character_id: int | None = None,
        notes: str = "",
    ):
        viewer = self.viewer()
        if not policies.can_manage_applications(viewer.membership, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot manage claims")
        clean_label = label.strip()
        if not clean_label:
            raise ValueError("claim label is required")
        claim_status = _normalize_claim_status(status)
        if claim_status == "claimed" and character_id is None:
            raise ValueError("claimed rows need a face")
        return self.repo.update_character_claim(
            viewer.community.id,
            claim_id,
            value=_claim_value_key(clean_label),
            label=clean_label,
            character_id=character_id,
            status=claim_status,
            notes=notes.strip(),
        )

    def create_claim_type_config(
        self,
        *,
        name: str,
        claim_kind: str,
        description: str,
        visibility: str = "public",
        is_required: bool = False,
        is_exclusive: bool = False,
        sort_order: int = 0,
    ):
        viewer = self.viewer()
        if not policies.can_manage_applications(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage intake configuration"
            )
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("claim type name is required")
        return self.repo.create_claim_type(
            viewer.community.id,
            _unique_claim_type_slug(self.repo, viewer.community.id, cleaned_name),
            cleaned_name,
            claim_kind=claim_kind.strip() or "custom",
            description=description.strip(),
            visibility=visibility.strip() or "public",
            is_required=is_required,
            is_exclusive=is_exclusive,
            sort_order=sort_order,
        )

    def update_claim_type_config(
        self,
        claim_type_id: int,
        *,
        name: str,
        claim_kind: str,
        description: str,
        visibility: str = "public",
        is_required: bool = False,
        is_exclusive: bool = False,
        sort_order: int = 0,
    ):
        viewer = self.viewer()
        if not policies.can_manage_applications(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage intake configuration"
            )
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("claim type name is required")
        return self.repo.update_claim_type(
            viewer.community.id,
            claim_type_id,
            name=cleaned_name,
            claim_kind=claim_kind.strip() or "custom",
            description=description.strip(),
            visibility=visibility.strip() or "public",
            is_required=is_required,
            is_exclusive=is_exclusive,
            sort_order=sort_order,
        )

    def create_application_template_field_config(
        self,
        *,
        label: str,
        field_type: str,
        help_text: str,
        placeholder: str,
        options_json: str = "[]",
        maps_to_claim_type_id: int | None = None,
        is_required: bool = False,
        sort_order: int = 0,
    ):
        viewer = self.viewer()
        if not policies.can_manage_applications(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage intake configuration"
            )
        cleaned_label = label.strip()
        if not cleaned_label:
            raise ValueError("application field label is required")
        return self.repo.create_application_template_field(
            viewer.community.id,
            _unique_application_field_key(self.repo, viewer.community.id, cleaned_label),
            cleaned_label,
            field_type=field_type.strip() or "text",
            help_text=help_text.strip(),
            placeholder=placeholder.strip(),
            options_json=options_json,
            maps_to_claim_type_id=maps_to_claim_type_id,
            is_required=is_required,
            sort_order=sort_order,
        )

    def update_application_template_field_config(
        self,
        field_id: int,
        *,
        label: str,
        field_type: str,
        help_text: str,
        placeholder: str,
        options_json: str = "[]",
        maps_to_claim_type_id: int | None = None,
        is_required: bool = False,
        sort_order: int = 0,
    ):
        viewer = self.viewer()
        if not policies.can_manage_applications(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage intake configuration"
            )
        cleaned_label = label.strip()
        if not cleaned_label:
            raise ValueError("application field label is required")
        return self.repo.update_application_template_field(
            viewer.community.id,
            field_id,
            label=cleaned_label,
            field_type=field_type.strip() or "text",
            help_text=help_text.strip(),
            placeholder=placeholder.strip(),
            options_json=options_json,
            maps_to_claim_type_id=maps_to_claim_type_id,
            is_required=is_required,
            sort_order=sort_order,
        )

    def realm_interactions(self) -> RealmInteractionHub:
        viewer = self.viewer()
        return _realm_interaction_hub(self.repo, viewer)

    def read_realm_interaction(self, slug: str) -> RealmInteractionDetail:
        viewer = self.viewer()
        return _read_realm_interaction(self.repo, viewer, slug)

    def submit_realm_interaction(
        self,
        slug: str,
        selected_option_ids: dict[int, int],
    ) -> RealmInteractionDetail:
        viewer = self.viewer()
        return _submit_realm_interaction(self.repo, viewer, slug, selected_option_ids)

    def members_directory(self) -> MemberDirectory:
        viewer = self.viewer()
        return _member_directory(self.repo, viewer)

    def read_member(self, username: str) -> MemberProfile:
        viewer = self.viewer()
        return _member_profile(self.repo, viewer, username)

    def board_threads(
        self,
        board_slug: str,
        *,
        filter_by: BoardThreadFilter = "all",
    ) -> tuple[Board, list[ThreadSummary]]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return board, _board_thread_summaries(
            self.repo,
            viewer,
            board,
            filter_by=filter_by,
        )

    def board_direct_thread_count(self, board: Board) -> int:
        viewer = self.viewer()
        if board.community_id != viewer.community.id:
            raise PermissionError(f"board {board.id} does not belong to current community")
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return self.repo.count_threads(viewer.community.id, board.id)

    def next_unread_thread(self, board_slug: str) -> ThreadNavigationItem | None:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return _next_unread_thread(self.repo, viewer, board)

    def can_start_thread(self, board: Board) -> bool:
        viewer = self.viewer()
        return policies.can_start_thread(viewer.membership, board, viewer.role)

    def board_facets(self, board_slug: str) -> list[FacetTag]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        return _facet_tags(
            self.repo,
            viewer.community.id,
            self.repo.list_board_facets(viewer.community.id, board.id),
        )

    def read_thread(self, board_slug: str, thread_slug: str) -> ThreadView:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        thread_view = _read_thread_view(self.repo, viewer, board, thread)
        self.repo.mark_thread_read(viewer.community.id, thread.id, viewer.membership.id)
        self._invalidate_viewer()
        return thread_view

    def watch_thread(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        self.repo.watch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def unwatch_thread(self, board_slug: str, thread_slug: str) -> None:
        viewer = self.viewer()
        _board, thread = self._visible_thread(viewer, board_slug, thread_slug)
        self.repo.unwatch_thread(viewer.community.id, thread.id, viewer.membership.id)

    def join_thread_as_current_character(self, board_slug: str, thread_slug: str) -> None:
        _join_thread(self.repo, self.viewer(), board_slug, thread_slug)

    def discover_plots(self, *, facet_slugs: list[str] | None = None) -> PlotDiscovery:
        return _discover_plots(self.repo, self.viewer(), facet_slugs=facet_slugs)

    def world_hub(self) -> WorldHub:
        viewer = self.viewer()
        materials = [
            _material_summary(self.repo, viewer.community.id, material)
            for material in self.repo.list_materials(viewer.community.id)
        ]
        additional_materials = [item for item in materials if not item.material.is_featured]
        return WorldHub(
            featured=[item for item in materials if item.material.is_featured],
            guides=[
                item
                for item in additional_materials
                if item.material.material_type in {"premise", "guide", "factions"}
            ],
            events=[item for item in materials if item.material.material_type == "event"],
            application_materials=[
                item
                for item in additional_materials
                if item.material.material_type == "application"
            ],
            can_manage=policies.can_manage_world(viewer.membership, viewer.role),
        )

    def director_studio(self) -> DirectorStudio:
        viewer = self.viewer()
        can_manage_world = policies.can_manage_world(viewer.membership, viewer.role)
        can_manage_casting = policies.can_manage_casting(viewer.membership, viewer.role)
        can_manage_navigation = policies.can_manage_navigation(viewer.membership, viewer.role)
        can_manage_studio = can_manage_world or can_manage_casting or can_manage_navigation
        material_status = None if can_manage_world else "published"
        materials = [
            _material_summary(self.repo, viewer.community.id, material)
            for material in self.repo.list_materials(
                viewer.community.id,
                status=material_status,
            )
        ]
        board_summaries = self.list_boards()
        boards_by_id = {item.board.id: item.board for item in board_summaries}
        child_counts: dict[int, int] = {item.board.id: 0 for item in board_summaries}
        for item in board_summaries:
            if item.board.parent_board_id is not None:
                child_counts[item.board.parent_board_id] = (
                    child_counts.get(item.board.parent_board_id, 0) + 1
                )
        board_taxonomy = [
            _board_taxonomy_item(
                summary,
                parent=(
                    boards_by_id.get(summary.board.parent_board_id)
                    if summary.board.parent_board_id is not None
                    else None
                ),
                child_count=child_counts.get(summary.board.id, 0),
            )
            for summary in board_summaries
        ]
        location_boards = [
            item
            for item in board_summaries
            if item.board.parent_board_id is None and item.board.board_kind == "location"
        ]
        sublocation_boards = [
            item for item in board_summaries if item.board.board_kind == "sublocation"
        ]
        wanted_status = None if can_manage_casting else "open"
        wanted_ads = [
            _wanted_ad_summary(self.repo, viewer.community.id, wanted_ad)
            for wanted_ad in self.repo.list_wanted_ads(
                viewer.community.id,
                status=wanted_status,
            )
        ]
        events = [item for item in materials if item.material.material_type == "event"]
        current_event = next((item for item in events if item.material.is_featured), None)
        if current_event is None:
            current_event = events[0] if events else None
        sidebar_sections = self.repo.list_sidebar_sections(viewer.community.id)
        facet_groups = self.repo.list_facet_groups(viewer.community.id)
        default_theme = self.repo.get_default_theme(viewer.community.id)
        theme_editor = community_theme_editor(default_theme)
        theme_warnings = theme_health_warnings(theme_editor)
        identity_accent_group = next(
            (
                group
                for group in facet_groups
                if group.id == viewer.community.identity_accent_facet_group_id
            ),
            None,
        )
        applications = self.applications_desk()
        claims = _claims_directory(self.repo, viewer)
        return DirectorStudio(
            can_manage=can_manage_studio,
            launch_readiness=_realm_launch_readiness(
                viewer=viewer,
                board_taxonomy=board_taxonomy,
                materials=materials,
                applications=applications,
                claims=claims,
                open_wanted_ads=[item for item in wanted_ads if item.wanted_ad.status == "open"],
                theme_warnings=theme_warnings,
            ),
            theme_editor=theme_editor,
            theme_warnings=theme_warnings,
            facet_groups=facet_groups,
            identity_accent_group=identity_accent_group,
            post_style_policy=_post_style_policy(viewer.community),
            materials=materials,
            draft_materials=[item for item in materials if item.material.status == "draft"],
            featured_materials=[item for item in materials if item.material.is_featured],
            events=events,
            current_event=current_event,
            application_materials=[
                item for item in materials if item.material.material_type == "application"
            ],
            board_taxonomy=board_taxonomy,
            sidebar_sections=sidebar_sections,
            navigation_preview_sections=_navigation_preview_sections(
                board_taxonomy,
                sidebar_sections=_sidebar_section_map(sidebar_sections),
                current_event=current_event,
                unread_notification_count=viewer.unread_notification_count,
                active_face=viewer.current_character,
                open_wanted_ads=[item for item in wanted_ads if item.wanted_ad.status == "open"],
            ),
            navigation_warnings=_navigation_health_warnings(
                board_taxonomy,
                sidebar_sections=_sidebar_section_map(sidebar_sections),
            ),
            location_boards=location_boards,
            sublocation_boards=sublocation_boards,
            wanted_ads=wanted_ads,
            open_wanted_ads=[item for item in wanted_ads if item.wanted_ad.status == "open"],
            applications=applications,
            claims=claims,
        )

    def update_default_theme(
        self,
        *,
        slug: str,
        name: str,
        typography_display: str,
        typography_body: str,
        typography_mono: str,
        radius: str,
        density: str,
        texture: str,
        light: dict[str, str],
        dark: dict[str, str],
    ) -> None:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot manage appearance")
        tokens = build_theme_tokens(
            slug=slug,
            name=name,
            typography_display=typography_display,
            typography_body=typography_body,
            typography_mono=typography_mono,
            radius=radius,
            density=density,
            texture=texture,
            light=light,
            dark=dark,
        )
        self.repo.upsert_default_theme(
            viewer.community.id,
            slug=str(tokens["slug"]),
            name=str(tokens["name"]),
            tokens_json=theme_tokens_json(tokens),
        )

    def preview_program_blueprint(self, source: str) -> ProgramBlueprintPreview:
        return _preview_program_blueprint(self.repo, self.viewer(), source)

    def update_board_taxonomy(
        self,
        board_id: int,
        *,
        board_kind: str,
        parent_board_id: int | None,
        sidebar_section: str | None = None,
    ) -> Board:
        viewer = self.viewer()
        if not policies.can_manage_navigation(viewer.membership, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot manage boards")
        board = self.repo.get_board(viewer.community.id, board_id)
        normalized_kind = normalize_board_kind(board_kind)
        normalized_sidebar_section = normalize_board_sidebar_section(
            sidebar_section,
            normalized_kind,
        )
        normalized_parent_id = _validate_board_parent(
            self.repo.list_boards(viewer.community.id),
            board,
            normalized_kind,
            parent_board_id,
        )
        return self.repo.update_board(
            viewer.community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=normalized_parent_id,
            board_kind=normalized_kind,
            sidebar_section=normalized_sidebar_section,
            tagline=board.tagline,
            image_url=board.image_url,
            image_alt=board.image_alt,
            image_treatment=board.image_treatment,
            image_focal_point=board.image_focal_point,
            image_overlay=board.image_overlay,
            is_private=board.is_private,
        )

    def update_board_navigation(
        self,
        board_id: int,
        *,
        navigation_order: int,
        show_in_navigation: bool,
        sidebar_section: str | None = None,
    ) -> Board:
        viewer = self.viewer()
        if not policies.can_manage_navigation(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage board navigation"
            )
        board = self.repo.get_board(viewer.community.id, board_id)
        return self.repo.update_board(
            viewer.community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=board.parent_board_id,
            board_kind=board.board_kind,
            sidebar_section=sidebar_section,
            tagline=board.tagline,
            image_url=board.image_url,
            image_alt=board.image_alt,
            image_treatment=board.image_treatment,
            image_focal_point=board.image_focal_point,
            image_overlay=board.image_overlay,
            is_private=board.is_private,
            navigation_order=navigation_order,
            show_in_navigation=show_in_navigation,
        )

    def update_sidebar_section_config(
        self,
        section_key: str,
        *,
        label: str,
        description: str,
        sort_order: int,
        show_label: bool,
    ) -> SidebarSectionConfig:
        viewer = self.viewer()
        if not policies.can_manage_navigation(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage sidebar sections"
            )
        return self.repo.update_sidebar_section(
            viewer.community.id,
            section_key,
            label=label,
            description=description,
            sort_order=sort_order,
            show_label=show_label,
        )

    def studio_board_editor(self, board_slug: str) -> StudioBoardEditor:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        summary = _board_summary(
            self.repo,
            viewer,
            board,
            _current_character_facet_ids(self.repo, viewer),
        )
        parent = (
            self.repo.get_board(viewer.community.id, board.parent_board_id)
            if board.parent_board_id is not None
            else None
        )
        kind = normalize_board_kind(board.board_kind)
        parent_options = [
            candidate
            for candidate in self.repo.list_boards(viewer.community.id)
            if candidate.id != board.id
            and candidate.parent_board_id is None
            and candidate.board_kind == "location"
        ]
        return StudioBoardEditor(
            board=board,
            summary=summary,
            parent=parent,
            parent_options=parent_options,
            kind_label=BOARD_KIND_LABELS[kind],
            realm_label=BOARD_KIND_REALMS[kind],
            sidebar_label=BOARD_KIND_SIDEBAR_LABELS[kind],
            sidebar_section_label=BOARD_SIDEBAR_SECTION_LABELS[board.sidebar_section],
            sidebar_section_guidance=BOARD_SIDEBAR_SECTION_GUIDANCE[board.sidebar_section],
            guidance=BOARD_KIND_GUIDANCE[kind],
            can_manage=policies.can_manage_navigation(viewer.membership, viewer.role),
        )

    def update_studio_board(
        self,
        board_slug: str,
        *,
        name: str,
        board_kind: str,
        parent_board_id: int | None,
        tagline: str,
        description: str,
        image_url: str,
        image_alt: str,
        image_treatment: str,
        image_focal_point: str,
        image_overlay: str,
        sort_order: int,
        navigation_order: int,
        show_in_navigation: bool,
        sidebar_section: str,
        is_private: bool,
    ) -> Board:
        viewer = self.viewer()
        if not policies.can_manage_navigation(viewer.membership, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot manage boards")
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("board name is required")
        cleaned_image_url = image_url.strip()
        cleaned_image_alt = image_alt.strip()
        if cleaned_image_url and not cleaned_image_alt:
            raise ValueError("board image alt text is required when an image URL is set")
        cleaned_image_treatment = image_treatment.strip()
        cleaned_image_focal_point = image_focal_point.strip()
        cleaned_image_overlay = image_overlay.strip()
        if cleaned_image_treatment not in BOARD_IMAGE_TREATMENTS:
            raise ValueError("choose a supported board image treatment")
        if cleaned_image_focal_point not in BOARD_IMAGE_FOCAL_POINTS:
            raise ValueError("choose a supported board image focal point")
        if cleaned_image_overlay not in BOARD_IMAGE_OVERLAYS:
            raise ValueError("choose a supported board image overlay")
        normalized_kind = normalize_board_kind(board_kind)
        normalized_sidebar_section = normalize_board_sidebar_section(
            sidebar_section,
            normalized_kind,
        )
        normalized_parent_id = _validate_board_parent(
            self.repo.list_boards(viewer.community.id),
            board,
            normalized_kind,
            parent_board_id,
        )
        return self.repo.update_board(
            viewer.community.id,
            board.id,
            name=cleaned_name,
            description=description.strip(),
            sort_order=sort_order,
            parent_board_id=normalized_parent_id,
            board_kind=normalized_kind,
            sidebar_section=normalized_sidebar_section,
            tagline=tagline.strip(),
            image_url=cleaned_image_url or None,
            image_alt=cleaned_image_alt,
            image_treatment=cleaned_image_treatment,
            image_focal_point=cleaned_image_focal_point,
            image_overlay=cleaned_image_overlay,
            is_private=is_private,
            navigation_order=navigation_order,
            show_in_navigation=show_in_navigation,
        )

    def update_identity_accent_group(self, facet_group_id: int | None) -> None:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage community direction"
            )
        self.repo.update_community_identity_accent_group(
            viewer.community.id,
            facet_group_id,
        )

    def update_community_media(
        self,
        *,
        community_mark_url: str,
        community_mark_alt: str,
        world_hero_image_url: str,
        world_hero_image_alt: str,
        world_hero_treatment: str,
        world_hero_focal_point: str,
        world_hero_overlay: str,
        world_hero_height: str,
    ) -> None:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot manage media")
        cleaned_mark_url = community_mark_url.strip()
        cleaned_mark_alt = community_mark_alt.strip()
        cleaned_hero_url = world_hero_image_url.strip()
        cleaned_hero_alt = world_hero_image_alt.strip()
        cleaned_treatment = world_hero_treatment.strip() or "split"
        cleaned_focal_point = world_hero_focal_point.strip() or "center"
        cleaned_overlay = world_hero_overlay.strip() or "medium"
        cleaned_height = world_hero_height.strip() or "standard"
        if cleaned_mark_url and not cleaned_mark_alt:
            raise ValueError("community mark alt text is required when a mark URL is set")
        if cleaned_hero_url and not cleaned_hero_alt:
            raise ValueError("world hero alt text is required when a hero image URL is set")
        if cleaned_treatment not in HERO_TREATMENTS:
            raise ValueError("world hero treatment is not supported")
        if cleaned_focal_point not in HERO_FOCAL_POINTS:
            raise ValueError("world hero focal point is not supported")
        if cleaned_overlay not in HERO_OVERLAYS:
            raise ValueError("world hero overlay is not supported")
        if cleaned_height not in HERO_HEIGHTS:
            raise ValueError("world hero height is not supported")
        self.repo.update_community_media(
            viewer.community.id,
            community_mark_url=cleaned_mark_url or None,
            community_mark_alt=cleaned_mark_alt,
            world_hero_image_url=cleaned_hero_url or None,
            world_hero_image_alt=cleaned_hero_alt,
            world_hero_treatment=cleaned_treatment,
            world_hero_focal_point=cleaned_focal_point,
            world_hero_overlay=cleaned_overlay,
            world_hero_height=cleaned_height,
        )

    def post_style_policy(self) -> PostStylePolicy:
        return _post_style_policy(self.viewer().community)

    def update_post_style_policy(
        self,
        *,
        enabled_post_profile_variants: list[str],
        enabled_post_accent_styles: list[str],
        enabled_post_border_styles: list[str],
        enabled_post_title_styles: list[str],
        enabled_post_densities: list[str],
    ) -> None:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage post style policy"
            )
        self.repo.update_community_post_style_policy(
            viewer.community.id,
            enabled_post_profile_variants=",".join(
                _clean_enabled_style_values(
                    enabled_post_profile_variants,
                    POST_PROFILE_VARIANTS,
                    "post profile variants",
                )
            ),
            enabled_post_accent_styles=",".join(
                _clean_enabled_style_values(
                    enabled_post_accent_styles,
                    POST_ACCENT_STYLES,
                    "post accent styles",
                )
            ),
            enabled_post_border_styles=",".join(
                _clean_enabled_style_values(
                    enabled_post_border_styles,
                    POST_BORDER_STYLES,
                    "post border styles",
                )
            ),
            enabled_post_title_styles=",".join(
                _clean_enabled_style_values(
                    enabled_post_title_styles,
                    POST_TITLE_STYLES,
                    "post title styles",
                )
            ),
            enabled_post_densities=",".join(
                _clean_enabled_style_values(
                    enabled_post_densities,
                    POST_DENSITIES,
                    "post densities",
                )
            ),
        )

    def read_material(self, material_slug: str) -> MaterialDetail:
        viewer = self.viewer()
        material = self.repo.get_material_by_slug(viewer.community.id, material_slug)
        if material.status != "published" and not policies.can_manage_world(
            viewer.membership,
            viewer.role,
        ):
            raise LookupError(
                f"material not found in community {viewer.community.id}: {material_slug}"
            )
        return _material_detail(
            self.repo,
            viewer,
            material,
            board_summary_factory=lambda board: _board_summary(
                self.repo,
                viewer,
                board,
                _current_character_facet_ids(self.repo, viewer),
            ),
            wanted_summary_factory=lambda wanted_ad: _wanted_ad_summary(
                self.repo,
                viewer.community.id,
                wanted_ad,
            ),
        )

    def current_event_for_board(self, board: Board) -> MaterialSummary | None:
        viewer = self.viewer()
        facet_ids = {
            facet.id for facet in self.repo.list_board_facets(viewer.community.id, board.id)
        }
        return _current_event_for_facet_ids(self.repo, viewer.community.id, facet_ids)

    def current_event_for_thread(self, thread: Thread, board: Board) -> MaterialSummary | None:
        viewer = self.viewer()
        facet_ids = {
            facet.id for facet in self.repo.list_thread_facets(viewer.community.id, thread.id)
        }
        facet_ids.update(
            facet.id for facet in self.repo.list_board_facets(viewer.community.id, board.id)
        )
        return _current_event_for_facet_ids(self.repo, viewer.community.id, facet_ids)

    def update_material(
        self,
        material_slug: str,
        *,
        title: str,
        material_type: str,
        summary: str,
        body: str,
        status: str = "published",
        is_featured: bool = False,
    ) -> Material:
        viewer = self.viewer()
        if not policies.can_manage_world(viewer.membership, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot manage world materials"
            )
        material = self.repo.get_material_by_slug(viewer.community.id, material_slug)
        cleaned_title = title.strip()
        cleaned_material_type = material_type.strip()
        cleaned_status = status.strip()
        if not cleaned_title:
            raise ValueError("material title is required")
        if cleaned_material_type not in MATERIAL_TYPES:
            raise ValueError("choose a supported material type")
        if cleaned_status not in MATERIAL_STATUSES:
            raise ValueError("choose a supported material status")
        return self.repo.update_material(
            viewer.community.id,
            material.id,
            title=cleaned_title,
            material_type=cleaned_material_type,
            summary=summary.strip(),
            body=body.strip(),
            status=cleaned_status,
            sort_order=material.sort_order,
            is_featured=is_featured,
        )

    def update_material_production_state(
        self,
        material_slug: str,
        *,
        status: str,
        is_featured: bool | None = None,
    ) -> Material:
        return _update_material_production_state(
            self.repo,
            self.viewer(),
            material_slug,
            status=status,
            is_featured=is_featured,
        )

    def wanted_ads(self) -> WantedBoard:
        return _wanted_board(self.repo, self.viewer())

    def casting_desk(self) -> CastingDesk:
        return _casting_desk(self.repo, self.viewer())

    def read_wanted_ad(self, wanted_slug: str) -> WantedAdDetail:
        return _read_wanted_ad(self.repo, self.viewer(), wanted_slug)

    def express_wanted_interest(self, wanted_slug: str) -> WantedAdInterest:
        return _express_wanted_interest(self.repo, self.viewer(), wanted_slug)

    def express_prospective_wanted_interest(
        self,
        wanted_slug: str,
        *,
        prospective_character_name: str,
        note: str = "",
    ) -> WantedAdInterest:
        return _express_prospective_wanted_interest(
            self.repo,
            self.viewer(),
            wanted_slug,
            prospective_character_name=prospective_character_name,
            note=note,
        )

    def reserve_wanted_interest(
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> WantedAdInterest:
        return _reserve_wanted_interest(self.repo, self.viewer(), wanted_slug, interest_id)

    def update_wanted_ad_lifecycle_status(self, wanted_slug: str, *, status: str) -> WantedAd:
        return _update_wanted_ad_lifecycle_status(
            self.repo,
            self.viewer(),
            wanted_slug,
            status=status,
        )

    def create_reserve_for_wanted_interest(
        self,
        wanted_slug: str,
        interest_id: int,
    ) -> CharacterReserve:
        return _create_reserve_for_wanted_interest(
            self.repo,
            self.viewer(),
            wanted_slug,
            interest_id,
        )

    def notifications(self, *, limit: int = 50) -> NotificationInbox:
        return _notification_inbox(self.repo, self.viewer(), limit=limit)

    def search_mentionables(
        self,
        query: str,
        *,
        scope: str = "all",
        limit: int = 8,
    ) -> list[Mentionable]:
        return _search_mentionables(self.repo, self.viewer(), query, scope=scope, limit=limit)

    def open_notification(self, notification_id: int) -> str:
        return _open_notification(self.repo, self.viewer(), notification_id)

    def mark_all_notifications_read(self) -> None:
        _mark_all_notifications_read(self.repo, self.viewer())

    def set_default_character(self, character_id: int) -> ForumView:
        viewer = self.viewer()
        character = self.repo.get_character(viewer.community.id, character_id)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot use character {character_id}"
            )
        self.repo.set_default_character(viewer.community.id, viewer.membership.id, character_id)
        return self.viewer()

    def submit_character_application(self, character_slug: str) -> Character:
        viewer = self.viewer()
        return _submit_character_application(self.repo, viewer, character_slug)

    def accept_character_application(self, character_slug: str) -> Character:
        viewer = self.viewer()
        return _accept_character_application(self.repo, viewer, character_slug)

    def request_character_application_revision(
        self,
        character_slug: str,
        *,
        note: str = "",
    ) -> Character:
        viewer = self.viewer()
        return _request_character_application_revision(
            self.repo,
            viewer,
            character_slug,
            note=note,
        )

    def read_application_review_room(self, character_slug: str) -> ApplicationReviewRoom:
        return _read_application_review_room(self.repo, self.viewer(), character_slug)

    def update_application_draft(
        self,
        character_slug: str,
        *,
        summary: str,
        body: str,
        application_field_values: dict[int, str] | None = None,
    ):
        return _update_application_draft(
            self.repo,
            self.viewer(),
            character_slug,
            summary=summary,
            body=body,
            application_field_values=application_field_values,
        )

    def update_application_review(
        self,
        character_slug: str,
        *,
        revision_notes: str,
        staff_notes: str,
        checklist: str,
    ):
        return _update_application_review(
            self.repo,
            self.viewer(),
            character_slug,
            revision_notes=revision_notes,
            staff_notes=staff_notes,
            checklist=checklist,
        )

    def read_character(self, character_slug: str) -> CharacterProfile:
        viewer = self.viewer()
        return _character_profile(self.repo, viewer, character_slug)

    def read_plot_hook(self, character_slug: str, hook_slug: str) -> CharacterPlotHookDetail:
        return _read_plot_hook(self.repo, self.viewer(), character_slug, hook_slug)

    def create_plot_hook(
        self,
        character_slug: str,
        *,
        title: str,
        hook_type: str,
        summary: str,
        body: str,
        facet_slugs: list[str],
    ):
        return _create_plot_hook(
            self.repo,
            self.viewer(),
            character_slug,
            title=title,
            hook_type=hook_type,
            summary=summary,
            body=body,
            facet_slugs=facet_slugs,
        )

    def update_plot_hook(
        self,
        character_slug: str,
        hook_slug: str,
        *,
        title: str,
        hook_type: str,
        summary: str,
        body: str,
        status: str,
        facet_slugs: list[str],
    ):
        return _update_plot_hook(
            self.repo,
            self.viewer(),
            character_slug,
            hook_slug,
            title=title,
            hook_type=hook_type,
            summary=summary,
            body=body,
            status=status,
            facet_slugs=facet_slugs,
        )

    def express_plot_hook_interest(self, character_slug: str, hook_slug: str):
        return _express_plot_hook_interest(self.repo, self.viewer(), character_slug, hook_slug)

    def plotting_desk(self) -> PlottingDesk:
        return _plotting_desk(self.repo, self.viewer())

    def read_plotting_room(self, room_id: int) -> PlottingRoomDetail:
        return _read_plotting_room(self.repo, self.viewer(), room_id)

    def update_plotting_room_plan(
        self,
        room_id: int,
        *,
        notes: str,
        next_step: str,
        target_board_id: int | None,
        status: str,
    ):
        return _update_plotting_room_plan(
            self.repo,
            self.viewer(),
            room_id,
            notes=notes,
            next_step=next_step,
            target_board_id=target_board_id,
            status=status,
        )

    def create_thread_from_plotting_room(
        self,
        room_id: int,
        *,
        board_id: int,
        character_id: int,
        title: str,
        summary: str,
        body: str,
        location: str = "",
        timeline: str = "",
        posting_mode: str = "freeform",
    ) -> CreatedThread:
        return _create_thread_from_plotting_room(
            self.repo,
            self.viewer(),
            room_id,
            board_id=board_id,
            character_id=character_id,
            title=title,
            summary=summary,
            body=body,
            location=location,
            timeline=timeline,
            posting_mode=posting_mode,
        )

    async def create_plotting_room_message(self, room_id: int, body: str):
        return await _create_plotting_room_message(self.repo, self.viewer(), room_id, body)

    async def subscribe_plotting_room_live(self, room_id: int):
        self.read_plotting_room(room_id)
        return await subscribe_plotting_room_live(room_id)

    async def unsubscribe_plotting_room_live(self, room_id: int, queue):
        await unsubscribe_plotting_room_live(room_id, queue)

    def create_plotting_room_from_plot_hook_interest(
        self,
        character_slug: str,
        hook_slug: str,
        interest_id: int,
    ):
        return _create_plotting_room_from_plot_hook_interest(
            self.repo,
            self.viewer(),
            character_slug,
            hook_slug,
            interest_id,
        )

    def create_plotting_room_from_wanted_interest(self, wanted_slug: str, interest_id: int):
        return _create_plotting_room_from_wanted_interest(
            self.repo,
            self.viewer(),
            wanted_slug,
            interest_id,
        )

    def read_post_editor(
        self,
        board_slug: str,
        thread_slug: str,
        post_number: int,
    ) -> EditablePostView:
        return _read_post_editor(self.repo, self.viewer(), board_slug, thread_slug, post_number)

    def read_post_revisions(
        self,
        board_slug: str,
        thread_slug: str,
        post_number: int,
    ) -> PostRevisionHistory:
        return _read_post_revisions(self.repo, self.viewer(), board_slug, thread_slug, post_number)

    def create_character(
        self,
        *,
        name: str,
        summary: str = "",
        application_body: str = "",
        application_field_values: dict[int, str] | None = None,
        facet_slugs: list[str] | None = None,
        avatar_url: str | None = None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
        post_style_preset: str = "",
        make_default: bool = False,
    ) -> Character:
        viewer = self.viewer()
        style_policy = _post_style_policy(viewer.community)
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        cleaned_poster_url = (poster_url or "").strip() or None
        cleaned_poster_alt = poster_alt.strip()
        cleaned_tagline = tagline.strip()
        cleaned_accent_color = accent_color.strip()
        (
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density,
        ) = _apply_post_style_preset(
            post_style_preset.strip(),
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
        )
        cleaned_post_profile_variant = post_profile_variant.strip() or "bio"
        _ensure_enabled_style_value(
            cleaned_post_profile_variant,
            style_policy.enabled_profile_variants,
            POST_PROFILE_VARIANTS,
            "post profile variant",
        )
        cleaned_post_accent_style = post_accent_style.strip() or "soft"
        _ensure_enabled_style_value(
            cleaned_post_accent_style,
            style_policy.enabled_accent_styles,
            POST_ACCENT_STYLES,
            "post accent style",
        )
        cleaned_post_border_style = post_border_style.strip() or "hairline"
        _ensure_enabled_style_value(
            cleaned_post_border_style,
            style_policy.enabled_border_styles,
            POST_BORDER_STYLES,
            "post border style",
        )
        cleaned_post_title_style = post_title_style.strip() or "standard"
        _ensure_enabled_style_value(
            cleaned_post_title_style,
            style_policy.enabled_title_styles,
            POST_TITLE_STYLES,
            "post title style",
        )
        cleaned_post_density = post_density.strip() or "calm"
        _ensure_enabled_style_value(
            cleaned_post_density,
            style_policy.enabled_densities,
            POST_DENSITIES,
            "post density",
        )
        slug = _unique_character_slug(self.repo, viewer.community.id, cleaned_name)
        character = self.repo.create_character(
            viewer.community.id,
            viewer.membership.id,
            slug,
            cleaned_name,
            avatar_url=cleaned_avatar_url,
            poster_url=cleaned_poster_url,
            poster_alt=cleaned_poster_alt,
            tagline=cleaned_tagline,
            accent_color=cleaned_accent_color,
            summary=cleaned_summary,
            post_profile_variant=cleaned_post_profile_variant,
            post_accent_style=cleaned_post_accent_style,
            post_border_style=cleaned_post_border_style,
            post_title_style=cleaned_post_title_style,
            post_density=cleaned_post_density,
            application_status="draft",
            make_default=make_default,
        )
        for facet in _resolve_facets(self.repo, viewer.community.id, facet_slugs or []):
            self.repo.assign_character_facet(viewer.community.id, character.id, facet.id)
        application = self.repo.ensure_character_application(viewer.community.id, character.id)
        cleaned_application_body = application_body.strip()
        if cleaned_application_body:
            if len(cleaned_application_body) > 5000:
                raise ValueError("application body must be 5000 characters or fewer")
            self.repo.update_character_application_draft(
                viewer.community.id,
                application.id,
                title=character.name,
                summary=character.summary,
                body=cleaned_application_body,
            )
        for field_id, value in (application_field_values or {}).items():
            cleaned_value = value.strip()
            if cleaned_value:
                self.repo.set_application_field_value(
                    viewer.community.id,
                    application.id,
                    field_id,
                    cleaned_value,
                )
        return character

    def update_character(
        self,
        character_slug: str,
        *,
        name: str,
        summary: str = "",
        avatar_url: str | None = None,
        poster_url: str | None = None,
        poster_alt: str = "",
        tagline: str = "",
        accent_color: str = "",
        post_profile_variant: str = "bio",
        post_accent_style: str = "soft",
        post_border_style: str = "hairline",
        post_title_style: str = "standard",
        post_density: str = "calm",
        post_style_preset: str = "",
    ) -> Character:
        viewer = self.viewer()
        style_policy = _post_style_policy(viewer.community)
        character = self.repo.get_character_by_slug(viewer.community.id, character_slug)
        if not policies.can_post_as(viewer.membership, character):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot update character {character.id}"
            )
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("character name is required")
        cleaned_summary = summary.strip()
        cleaned_avatar_url = (avatar_url or "").strip() or None
        cleaned_poster_url = (poster_url or "").strip() or None
        cleaned_poster_alt = poster_alt.strip()
        cleaned_tagline = tagline.strip()
        cleaned_accent_color = accent_color.strip()
        (
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density,
        ) = _apply_post_style_preset(
            post_style_preset.strip(),
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
        )
        cleaned_post_profile_variant = post_profile_variant.strip() or "bio"
        _ensure_enabled_style_value(
            cleaned_post_profile_variant,
            style_policy.enabled_profile_variants,
            POST_PROFILE_VARIANTS,
            "post profile variant",
            current_value=character.post_profile_variant,
        )
        cleaned_post_accent_style = post_accent_style.strip() or "soft"
        _ensure_enabled_style_value(
            cleaned_post_accent_style,
            style_policy.enabled_accent_styles,
            POST_ACCENT_STYLES,
            "post accent style",
            current_value=character.post_accent_style,
        )
        cleaned_post_border_style = post_border_style.strip() or "hairline"
        _ensure_enabled_style_value(
            cleaned_post_border_style,
            style_policy.enabled_border_styles,
            POST_BORDER_STYLES,
            "post border style",
            current_value=character.post_border_style,
        )
        cleaned_post_title_style = post_title_style.strip() or "standard"
        _ensure_enabled_style_value(
            cleaned_post_title_style,
            style_policy.enabled_title_styles,
            POST_TITLE_STYLES,
            "post title style",
            current_value=character.post_title_style,
        )
        cleaned_post_density = post_density.strip() or "calm"
        _ensure_enabled_style_value(
            cleaned_post_density,
            style_policy.enabled_densities,
            POST_DENSITIES,
            "post density",
            current_value=character.post_density,
        )
        slug = character.slug
        if cleaned_name != character.name:
            slug = _unique_character_slug(
                self.repo,
                viewer.community.id,
                cleaned_name,
                current_character_id=character.id,
            )
        return self.repo.update_character(
            viewer.community.id,
            character.id,
            slug=slug,
            name=cleaned_name,
            avatar_url=cleaned_avatar_url,
            poster_url=cleaned_poster_url,
            poster_alt=cleaned_poster_alt,
            tagline=cleaned_tagline,
            accent_color=cleaned_accent_color,
            summary=cleaned_summary,
            post_profile_variant=cleaned_post_profile_variant,
            post_accent_style=cleaned_post_accent_style,
            post_border_style=cleaned_post_border_style,
            post_title_style=cleaned_post_title_style,
            post_density=cleaned_post_density,
        )

    def update_post(self, board_slug: str, thread_slug: str, post_number: int, body: str) -> Post:
        return _update_post(self.repo, self.viewer(), board_slug, thread_slug, post_number, body)

    def update_thread_state(
        self,
        board_slug: str,
        thread_slug: str,
        *,
        is_locked: bool | None = None,
        is_pinned: bool | None = None,
    ) -> Thread:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_moderate_thread(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot moderate thread {thread.id}"
            )
        return self.repo.update_thread_flags(
            viewer.community.id,
            thread.id,
            is_locked=is_locked,
            is_pinned=is_pinned,
        )

    def update_thread_scene(
        self,
        board_slug: str,
        thread_slug: str,
        *,
        status: str,
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> Thread:
        return _update_thread_scene(
            self.repo,
            self.viewer(),
            board_slug,
            thread_slug,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        )

    def move_thread(
        self,
        board_slug: str,
        thread_slug: str,
        target_board_id: int,
    ) -> tuple[Board, Thread]:
        viewer = self.viewer()
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        if not policies.can_moderate_thread(viewer.membership, thread, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot moderate thread {thread.id}"
            )
        target_board = self.repo.get_board(viewer.community.id, target_board_id)
        if not policies.can_view_board(viewer.membership, target_board, viewer.role):
            raise PermissionError(
                f"membership {viewer.membership.id} cannot move thread into board {target_board.id}"
            )
        if target_board.id == board.id:
            return target_board, thread
        try:
            conflicting = self.repo.get_thread_by_slug(
                viewer.community.id,
                target_board.id,
                thread.slug,
            )
        except LookupError:
            conflicting = None
        if conflicting is not None and conflicting.id != thread.id:
            raise ValueError(
                f"board {target_board.slug} already has a thread at slug {thread.slug}"
            )
        moved = self.repo.move_thread(viewer.community.id, thread.id, target_board.id)
        return target_board, moved

    def reply_to_thread(
        self, board_slug: str, thread_slug: str, character_id: int, body: str
    ) -> Post:
        return _reply_to_thread(
            self.repo, self.viewer(), board_slug, thread_slug, character_id, body
        )

    def start_thread(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
        status: str = "active",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> Thread:
        return self.start_thread_with_post(
            board_slug=board_slug,
            character_id=character_id,
            title=title,
            body=body,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        ).thread

    def start_thread_with_post(
        self,
        *,
        board_slug: str,
        character_id: int,
        title: str,
        body: str,
        status: str = "active",
        location: str = "",
        timeline: str = "",
        summary: str = "",
        posting_mode: str = "freeform",
        participant_ids: list[int] | None = None,
    ) -> CreatedThread:
        return _start_thread(
            self.repo,
            self.viewer(),
            board_slug=board_slug,
            character_id=character_id,
            title=title,
            body=body,
            status=status,
            location=location,
            timeline=timeline,
            summary=summary,
            posting_mode=posting_mode,
            participant_ids=participant_ids,
        )

    def _visible_thread(
        self,
        viewer: ForumView,
        board_slug: str,
        thread_slug: str,
    ) -> tuple[Board, Thread]:
        board = self.repo.get_board_by_slug(viewer.community.id, board_slug)
        if not policies.can_view_board(viewer.membership, board, viewer.role):
            raise PermissionError(f"membership {viewer.membership.id} cannot view board {board.id}")
        thread = self.repo.get_thread_by_slug(viewer.community.id, board.id, thread_slug)
        return board, thread


def create_services(path: str | Path | None = None, *, seed_demo: bool = True) -> AppServices:
    database_path = _resolve_database_path(path)
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = connect(database_path, check_same_thread=False)
    create_schema(connection)
    repo = ForumRepository(connection)
    seed = seed_demo_forum(repo) if seed_demo else None
    database = None if database_path == ":memory:" else Database(database_path)
    return AppServices(repo, seed, database=database, owns_repo=True)


def _connection_has_filesystem_database(connection: sqlite3.Connection) -> bool:
    return any(row["file"] for row in connection.execute("PRAGMA database_list").fetchall())


def initialize_database(path: str | Path | None = None, *, seed_demo: bool = False) -> Path:
    database_path = _resolve_database_path(path)
    if database_path == ":memory:":
        raise ValueError("persistent database initialization requires a filesystem path")
    resolved_path = Path(database_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(resolved_path)
    try:
        create_schema(connection)
        if seed_demo:
            seed_demo_forum(ForumRepository(connection))
    finally:
        connection.close()
    return resolved_path


def bootstrap_first_realm(
    path: str | Path | None = None,
    *,
    realm_name: str,
    realm_slug: str,
    director_email: str,
    director_password: str,
    director_username: str,
    director_display_name: str,
) -> FirstRealmSetupResult:
    database_path = _resolve_database_path(path)
    if database_path == ":memory:":
        raise ValueError("first realm setup requires a filesystem database path")
    resolved_path = Path(database_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(resolved_path)
    try:
        create_schema(connection)
        services = AppServices(ForumRepository(connection), None)
        return services.create_first_realm(
            realm_name=realm_name,
            realm_slug=realm_slug,
            director_email=director_email,
            director_password=director_password,
            director_username=director_username,
            director_display_name=director_display_name,
        )
    finally:
        connection.close()


def default_database_path() -> Path:
    configured = os.environ.get(DATABASE_PATH_ENV)
    if configured:
        return Path(configured)
    railway_volume = os.environ.get(RAILWAY_VOLUME_MOUNT_PATH_ENV)
    if railway_volume:
        return Path(railway_volume) / "elbysodic.sqlite3"
    return DEFAULT_DATABASE_PATH


def _resolve_database_path(path: str | Path | None) -> str | Path:
    if path is None:
        return default_database_path()
    return path


def _default_request_identity(seed: DemoSeed | None) -> DefaultRequestIdentity | None:
    if seed is None:
        return None
    return DefaultRequestIdentity(
        community_id=seed.community.id,
        user_id=seed.user.id,
        membership_id=seed.membership.id,
    )


def _resolve_current_character(
    repo: ForumRepository,
    membership: CommunityMembership,
    roster: list[Character],
) -> Character | None:
    if not roster:
        return None
    if membership.default_character_id is not None:
        return repo.get_character(membership.community_id, membership.default_character_id)
    return roster[0]


def _sidebar_sections_by_key(
    repo: ForumRepository,
    community_id: int,
) -> dict[str, SidebarSectionConfig]:
    return _sidebar_section_map(repo.list_sidebar_sections(community_id))


def _sidebar_section_map(
    sections: list[SidebarSectionConfig],
) -> dict[str, SidebarSectionConfig]:
    return {section.section_key: section for section in sections}


def _board_navigation(
    repo: ForumRepository,
    community_id: int,
    membership: CommunityMembership,
    role: Role,
) -> list[BoardNavigationItem]:
    items: list[BoardNavigationItem] = []
    boards = sorted(
        repo.list_boards(community_id),
        key=lambda board: (board.navigation_order, board.name, board.id),
    )
    for board in boards:
        if not board.show_in_navigation:
            continue
        if not policies.can_view_board(membership, board, role):
            continue
        threads = repo.list_threads(community_id, board.id)
        unread_thread_count = sum(
            1 for thread in threads if _is_unread(repo, community_id, membership.id, thread)
        )
        items.append(BoardNavigationItem(board=board, unread_thread_count=unread_thread_count))
    return items


def _location_navigation_groups(
    navigation_boards: list[BoardNavigationItem],
) -> list[LocationNavigationGroup]:
    parents = [
        item
        for item in navigation_boards
        if item.board.parent_board_id is None
        and is_location_board(item.board)
        and is_location_sidebar_board(item.board)
    ]
    children_by_parent: dict[int, list[BoardNavigationItem]] = {
        item.board.id: [] for item in parents
    }
    for item in navigation_boards:
        parent_id = item.board.parent_board_id
        if (
            parent_id is None
            or not is_location_board(item.board)
            or not is_location_sidebar_board(item.board)
        ):
            continue
        if parent_id in children_by_parent:
            children_by_parent[parent_id].append(item)
    return [
        LocationNavigationGroup(
            parent=parent,
            children=children_by_parent[parent.board.id],
        )
        for parent in parents
    ]


def _board_summary(
    repo: ForumRepository,
    viewer: ForumView,
    board: Board,
    current_facet_ids: set[int],
) -> BoardSummary:
    child_boards = [
        child
        for child in repo.list_child_boards(viewer.community.id, board.id)
        if policies.can_view_board(viewer.membership, child, viewer.role)
    ]
    boards_for_activity = [board, *child_boards]
    board_facets = _facet_tags(
        repo,
        viewer.community.id,
        repo.list_board_facets(viewer.community.id, board.id),
    )
    threads_with_boards: list[tuple[Board, Thread]] = []
    posts_by_thread: dict[int, list[Post]] = {}
    for activity_board in boards_for_activity:
        for thread in repo.list_threads(viewer.community.id, activity_board.id):
            threads_with_boards.append((activity_board, thread))
            posts_by_thread[thread.id] = repo.list_posts(viewer.community.id, thread.id)
    latest_board: Board | None = None
    latest_thread: Thread | None = None
    if threads_with_boards:
        latest_board, latest_thread = max(
            threads_with_boards,
            key=lambda item: (_timestamp_key(item[1].updated_at), item[1].id),
        )
    latest_thread_posts = posts_by_thread.get(latest_thread.id, []) if latest_thread else []
    latest_post = (
        _post_view(repo, viewer.community.id, latest_thread_posts[-1])
        if latest_thread_posts
        else None
    )
    threads = [thread for _, thread in threads_with_boards]
    return BoardSummary(
        board=board,
        child_boards=child_boards,
        thread_count=len(threads),
        post_count=sum(len(posts) for posts in posts_by_thread.values()),
        unread_thread_count=sum(
            1
            for thread in threads
            if _is_unread(
                repo,
                viewer.community.id,
                viewer.membership.id,
                thread,
            )
        ),
        latest_thread=latest_thread,
        latest_board=latest_board,
        latest_post=latest_post,
        facets=board_facets,
        is_relevant_to_current_face=bool(
            current_facet_ids
            and {tag.facet.id for tag in board_facets}.intersection(current_facet_ids)
        ),
    )


def _latest_thread(threads: list[Thread]) -> Thread | None:
    if not threads:
        return None
    return max(threads, key=lambda thread: (_timestamp_key(thread.updated_at), thread.id))


def _first_public_scene_hub(repo: ForumRepository, community_id: int) -> Board | None:
    return next(
        (
            board
            for board in repo.list_boards(community_id)
            if board.board_kind in {"location", "community"} and not board.is_private
        ),
        None,
    )


def _first_material_of_type(
    repo: ForumRepository,
    community_id: int,
    material_type: str,
) -> Material | None:
    return next(
        (
            material
            for material in repo.list_materials(community_id, status=None)
            if material.material_type == material_type
        ),
        None,
    )


def _invitation_management_item(invitation: CommunityInvitation) -> InvitationManagementItem:
    expired = _invitation_is_expired(invitation)
    if invitation.status == "accepted" or invitation.accepted_at is not None:
        return InvitationManagementItem(invitation, "Accepted", can_revoke=False)
    if invitation.status == "revoked" or invitation.revoked_at is not None:
        return InvitationManagementItem(invitation, "Revoked", can_revoke=False)
    if expired:
        return InvitationManagementItem(invitation, "Expired", can_revoke=False)
    return InvitationManagementItem(invitation, "Pending", can_revoke=True)


def _invitation_is_expired(invitation: CommunityInvitation) -> bool:
    if invitation.expires_at is None:
        return False
    try:
        return datetime.fromisoformat(invitation.expires_at) <= datetime.now(UTC)
    except ValueError:
        return True


def _realm_launch_readiness(
    *,
    viewer: ForumView,
    board_taxonomy: list[BoardTaxonomyItem],
    materials: list[MaterialSummary],
    applications: ApplicationsDesk,
    claims: ClaimsDirectory,
    open_wanted_ads: list[WantedAdSummary],
    theme_warnings: tuple[ThemeHealthWarning, ...],
) -> RealmLaunchReadiness:
    public_scene_hubs = [
        item
        for item in board_taxonomy
        if item.board.board_kind in {"location", "community"} and not item.board.is_private
    ]
    premise_materials = [item for item in materials if item.material.material_type == "premise"]
    application_materials = [
        item for item in materials if item.material.material_type == "application"
    ]
    return RealmLaunchReadiness(
        items=[
            RealmLaunchChecklistItem(
                label="Realm identity",
                summary=(
                    f"{viewer.community.name} has a community-local director "
                    f"membership for {viewer.membership.display_name}."
                ),
                href="/studio#identity-appearance",
                cta="Review identity",
                is_complete=(
                    bool(viewer.community.name.strip())
                    and bool(viewer.community.slug.strip())
                    and viewer.membership.community_id == viewer.community.id
                    and viewer.role.community_id == viewer.community.id
                ),
            ),
            RealmLaunchChecklistItem(
                label="Scene hubs",
                summary="At least one public place or community room exists for scenes.",
                href="/studio#world-structure",
                cta="Review scene hubs",
                is_complete=bool(public_scene_hubs),
            ),
            RealmLaunchChecklistItem(
                label="Director materials",
                summary="Premise and guidebook material give writers the board frame.",
                href="/studio#continuity-events",
                cta="Review materials",
                is_complete=bool(premise_materials),
            ),
            RealmLaunchChecklistItem(
                label="Intake and claims",
                summary="Application guidance and claim tables are visible to directors.",
                href="/studio/intake",
                cta="Review intake",
                is_complete=bool(application_materials)
                and (bool(claims.groups) or bool(applications.application_materials)),
            ),
            RealmLaunchChecklistItem(
                label="Wanted hooks",
                summary="Open hooks can give incoming writers a first plotting lane.",
                href="/wanted",
                cta="Review wanted",
                is_complete=bool(open_wanted_ads),
                is_required=False,
            ),
            RealmLaunchChecklistItem(
                label="Appearance",
                summary="Theme tokens are valid and ready for the realm shell.",
                href="/studio#appearance-theme",
                cta="Review appearance",
                is_complete=not theme_warnings,
            ),
            RealmLaunchChecklistItem(
                label="Launch checklist",
                summary="Public preview can open after required setup lanes are complete.",
                href="/studio/launch",
                cta="Open checklist",
                is_complete=bool(public_scene_hubs)
                and bool(premise_materials)
                and bool(application_materials)
                and viewer.membership.community_id == viewer.community.id,
            ),
        ]
    )


def _is_public_network_ready(
    repo: ForumRepository,
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


def _post_style_policy(community: Community) -> PostStylePolicy:
    return PostStylePolicy(
        enabled_profile_variants=tuple(
            _stored_style_values(
                community.enabled_post_profile_variants,
                POST_PROFILE_VARIANTS,
            )
        ),
        enabled_accent_styles=tuple(
            _stored_style_values(
                community.enabled_post_accent_styles,
                POST_ACCENT_STYLES,
            )
        ),
        enabled_border_styles=tuple(
            _stored_style_values(
                community.enabled_post_border_styles,
                POST_BORDER_STYLES,
            )
        ),
        enabled_title_styles=tuple(
            _stored_style_values(
                community.enabled_post_title_styles,
                POST_TITLE_STYLES,
            )
        ),
        enabled_densities=tuple(
            _stored_style_values(
                community.enabled_post_densities,
                POST_DENSITIES,
            )
        ),
    )


def _stored_style_values(raw_values: str, allowed_values: tuple[str, ...]) -> list[str]:
    values = [value.strip() for value in raw_values.split(",") if value.strip()]
    cleaned = [value for value in values if value in allowed_values]
    return cleaned or list(allowed_values)


def _clean_enabled_style_values(
    values: list[str],
    allowed_values: tuple[str, ...],
    label: str,
) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        candidate = value.strip()
        if candidate in allowed_values and candidate not in cleaned:
            cleaned.append(candidate)
    if not cleaned:
        raise ValueError(f"choose at least one {label}")
    return cleaned


def _board_taxonomy_item(
    summary: BoardSummary,
    *,
    parent: Board | None,
    child_count: int,
) -> BoardTaxonomyItem:
    kind = normalize_board_kind(summary.board.board_kind)
    return BoardTaxonomyItem(
        summary=summary,
        parent=parent,
        child_count=child_count,
        kind_label=BOARD_KIND_LABELS[kind],
        realm_label=BOARD_KIND_REALMS[kind],
        sidebar_label=BOARD_KIND_SIDEBAR_LABELS[kind],
        sidebar_section_label=BOARD_SIDEBAR_SECTION_LABELS[summary.board.sidebar_section],
        guidance=BOARD_KIND_GUIDANCE[kind],
    )


def _validate_board_parent(
    boards: list[Board],
    board: Board,
    board_kind: BoardKind,
    parent_board_id: int | None,
) -> int | None:
    if board_kind != "sublocation":
        return None
    if parent_board_id is None:
        raise ValueError("choose a parent location for sublocations")
    boards_by_id = {candidate.id: candidate for candidate in boards}
    parent = boards_by_id.get(parent_board_id)
    if parent is None:
        raise LookupError(
            f"board parent not found in community {board.community_id}: {parent_board_id}"
        )
    if parent.id == board.id:
        raise ValueError("board cannot be its own parent")
    if parent.parent_board_id is not None or parent.board_kind != "location":
        raise ValueError("choose a major location parent for sublocations")
    return parent.id


def _navigation_preview_sections(
    board_taxonomy: list[BoardTaxonomyItem],
    *,
    sidebar_sections: dict[str, SidebarSectionConfig],
    current_event: MaterialSummary | None,
    unread_notification_count: int,
    active_face: Character | None,
    open_wanted_ads: list[WantedAdSummary],
) -> list[NavigationPreviewSection]:
    location_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=(
                f"{item.child_count} sublocations" if item.child_count else "Major location"
            ),
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation
        and item.board.sidebar_section == "locations"
        and item.board.parent_board_id is None
        and item.board.board_kind == "location"
    ]
    community_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=item.kind_label,
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation and item.board.sidebar_section == "community"
    ]
    desk_board_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=item.kind_label,
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation and item.board.sidebar_section == "desk"
    ]
    staff_board_items = [
        NavigationPreviewItem(
            label=item.board.name,
            href=item.summary.href,
            source_label="Board-derived",
            behavior_label=item.kind_label,
            count=item.summary.unread_thread_count or None,
        )
        for item in board_taxonomy
        if item.board.show_in_navigation and item.board.sidebar_section == "studio"
    ]
    studio_items = [
        NavigationPreviewItem("Overview", "/studio", "App-owned", "Realm home"),
        NavigationPreviewItem(
            "Board taxonomy",
            "/studio#board-taxonomy",
            "App-owned",
            "Production control",
        ),
        NavigationPreviewItem(
            "Navigation composer",
            "/studio#navigation-composer",
            "App-owned",
            "Production preview",
        ),
        NavigationPreviewItem("Guidebook", "/world", "App-owned", "Cross-realm shortcut"),
        NavigationPreviewItem("World map", "/", "App-owned", "Cross-realm shortcut"),
        NavigationPreviewItem("Applications", "/applications", "App-owned", "Production queue"),
        NavigationPreviewItem("Wanted board", "/wanted", "App-owned", "Casting surface"),
        NavigationPreviewItem("Casting desk", "/casting", "App-owned", "Casting queue"),
    ]
    if current_event is not None:
        studio_items.append(
            NavigationPreviewItem(
                current_event.material.title,
                f"/world/{current_event.material.slug}",
                "Material-derived",
                "Current event",
            )
        )
    studio_items.extend(staff_board_items)
    return [
        NavigationPreviewSection(
            realm_label="World",
            title="World sidebar",
            description="World lanes use director language while board placement stays constrained.",
            label_visible=(
                sidebar_sections["locations"].show_label or sidebar_sections["community"].show_label
            ),
            items=[
                NavigationPreviewItem("Overview", "/", "App-owned", "Realm home"),
                NavigationPreviewItem(
                    sidebar_sections["locations"].label,
                    "/locations",
                    "Configured section",
                    "Location index",
                    len(location_items),
                ),
                *location_items,
                NavigationPreviewItem(
                    sidebar_sections["community"].label,
                    "/community",
                    "Configured section",
                    "Community index",
                    len(community_items),
                ),
                NavigationPreviewItem("Members", "/members", "App-owned", "Directory"),
                *community_items,
            ],
        ),
        NavigationPreviewSection(
            realm_label="Writer Desk",
            title="Desk sidebar",
            description=sidebar_sections["desk"].description,
            label_visible=sidebar_sections["desk"].show_label,
            items=[
                NavigationPreviewItem("Overview", "/desk", "App-owned", "Realm home"),
                NavigationPreviewItem("Queue", "/my/threads", "App-owned", "Writing lane"),
                NavigationPreviewItem(
                    "Inbox",
                    "/notifications",
                    "App-owned",
                    "Attention surface",
                    unread_notification_count or None,
                ),
                NavigationPreviewItem("Roster", "/characters", "App-owned", "Identity lane"),
                NavigationPreviewItem("Plotting", "/plotting", "App-owned", "Collaboration"),
                NavigationPreviewItem("Applications", "/applications", "App-owned", "Intake"),
                NavigationPreviewItem("Discovery", "/discover", "App-owned", "Find play"),
                *desk_board_items,
            ],
        ),
        NavigationPreviewSection(
            realm_label="Studio",
            title="Studio sidebar",
            description=sidebar_sections["studio"].description,
            label_visible=sidebar_sections["studio"].show_label,
            items=studio_items,
        ),
        NavigationPreviewSection(
            realm_label="Wanted",
            title="Casting sidebar",
            description=(
                "Casting navigation stays lean: app-owned surfaces first, then the active "
                "face and context-specific wants."
            ),
            label_visible=False,
            items=[
                NavigationPreviewItem("Wanted board", "/wanted", "App-owned", "Realm home"),
                NavigationPreviewItem("Casting desk", "/casting", "App-owned", "Pipeline"),
                NavigationPreviewItem("Applications", "/applications", "App-owned", "Intake"),
                NavigationPreviewItem(
                    active_face.name if active_face else "Active face",
                    f"/characters/{active_face.slug}" if active_face else "/characters",
                    "Identity-derived",
                    "Current lens" if active_face else "Choose a face",
                ),
                NavigationPreviewItem(
                    "Open wants",
                    "/wanted",
                    "Wanted-derived",
                    "Context list",
                    len(open_wanted_ads) or None,
                ),
            ],
        ),
    ]


def _navigation_health_warnings(
    board_taxonomy: list[BoardTaxonomyItem],
    sidebar_sections: dict[str, SidebarSectionConfig],
) -> list[NavigationHealthWarning]:
    warnings: list[NavigationHealthWarning] = []
    items_by_board_id = {item.board.id: item for item in board_taxonomy}
    visible_items_by_section: dict[str, list[BoardTaxonomyItem]] = {
        "locations": [],
        "community": [],
        "desk": [],
        "studio": [],
    }
    visible_children_by_parent: dict[int, list[BoardTaxonomyItem]] = {}
    for item in board_taxonomy:
        if item.board.show_in_navigation:
            visible_items_by_section.setdefault(item.board.sidebar_section, []).append(item)
            if item.board.parent_board_id is not None:
                visible_children_by_parent.setdefault(item.board.parent_board_id, []).append(item)

    for item in board_taxonomy:
        board = item.board
        visible_children = visible_children_by_parent.get(board.id, [])
        if not board.show_in_navigation and visible_children:
            warnings.append(
                NavigationHealthWarning(
                    severity="warning",
                    title="Hidden parent with visible children",
                    message=(
                        f"{board.name} is hidden from navigation, but "
                        f"{len(visible_children)} child board(s) are still visible."
                    ),
                    board=board,
                    href=f"/studio/boards/{board.slug}",
                )
            )
        if (
            board.show_in_navigation
            and board.parent_board_id is not None
            and (parent := items_by_board_id.get(board.parent_board_id)) is not None
            and not parent.board.show_in_navigation
        ):
            warnings.append(
                NavigationHealthWarning(
                    severity="warning",
                    title="Visible child under hidden parent",
                    message=(
                        f"{board.name} is visible, but its parent {parent.board.name} "
                        "is hidden from the sidebar."
                    ),
                    board=board,
                    href=f"/studio/boards/{board.slug}",
                )
            )
        if board.board_kind in {"location", "sublocation"} and board.sidebar_section != "locations":
            warnings.append(
                NavigationHealthWarning(
                    severity="warning",
                    title="Place outside the map",
                    message=(
                        f"{board.name} is a {item.kind_label.lower()}, but it appears in "
                        f"the {sidebar_sections[board.sidebar_section].label} section."
                    ),
                    board=board,
                    section=sidebar_sections[board.sidebar_section],
                    href=f"/studio/boards/{board.slug}",
                )
            )
        if board.board_kind in {"community", "archive"} and board.sidebar_section == "locations":
            warnings.append(
                NavigationHealthWarning(
                    severity="warning",
                    title="Community board in the location map",
                    message=(
                        f"{board.name} is a {item.kind_label.lower()}, but it is placed "
                        "with playable locations."
                    ),
                    board=board,
                    section=sidebar_sections["locations"],
                    href=f"/studio/boards/{board.slug}",
                )
            )
        if board.is_private and board.sidebar_section in {"locations", "community"}:
            warnings.append(
                NavigationHealthWarning(
                    severity="attention",
                    title="Private board in a public-facing section",
                    message=(
                        f"{board.name} is private, but it is placed in "
                        f"{sidebar_sections[board.sidebar_section].label}."
                    ),
                    board=board,
                    section=sidebar_sections[board.sidebar_section],
                    href=f"/studio/boards/{board.slug}",
                )
            )
        if (
            not board.is_private
            and board.sidebar_section == "studio"
            and board.board_kind != "staff"
        ):
            warnings.append(
                NavigationHealthWarning(
                    severity="note",
                    title="Public board in Studio",
                    message=(
                        f"{board.name} is public, but it appears in the director Studio sidebar."
                    ),
                    board=board,
                    section=sidebar_sections["studio"],
                    href=f"/studio/boards/{board.slug}",
                )
            )

    for section_key, section in sidebar_sections.items():
        if section.show_label and not visible_items_by_section.get(section_key):
            warnings.append(
                NavigationHealthWarning(
                    severity="note",
                    title="Visible label without board links",
                    message=(
                        f"{section.label} is set to show as a section label, but no "
                        "visible board-derived links currently live there."
                    ),
                    section=section,
                    href="/studio#navigation-composer",
                )
            )

    for section in sidebar_sections.values():
        first_route = {
            "locations": section.label,
            "community": section.label,
            "desk": "Overview",
            "studio": "Production",
        }.get(section.section_key)
        if (
            section.show_label
            and first_route
            and section.label.strip().lower() == first_route.lower()
        ):
            warnings.append(
                NavigationHealthWarning(
                    severity="note",
                    title="Repeated sidebar label",
                    message=(
                        f"{section.label} is both the visible section label and the first "
                        "route row. Hiding the label may make the sidebar cleaner."
                    ),
                    section=section,
                    href="/studio#navigation-composer",
                )
            )

    return warnings


def _ensure_enabled_style_value(
    value: str,
    enabled_values: tuple[str, ...],
    allowed_values: tuple[str, ...],
    label: str,
    *,
    current_value: str | None = None,
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{label} is not supported")
    if value not in enabled_values and value != current_value:
        raise ValueError(f"{label} is not available in this community")


def _first_material_summary(
    materials: list[Material],
    material_type: str,
    repo: ForumRepository,
    community_id: int,
) -> MaterialSummary | None:
    for material in materials:
        if material.material_type == material_type:
            return _material_summary(repo, community_id, material)
    return None


def _public_catalog_card_from_program(program: StudioNetworkProgramView) -> PublicCatalogCard:
    return PublicCatalogCard(
        community=program.community,
        premise=program.premise,
        current_event=program.current_event,
        roster_count=program.roster_count,
        open_wanted_count=program.open_wanted_count,
        application_material_count=program.application_material_count,
        claim_type_count=program.claim_type_count,
        theme_preview=program.theme_preview,
    )


def _network_browse_facets() -> list[NetworkBrowseFacet]:
    return [
        NetworkBrowseFacet("superhero crisis", "/network?q=superhero", "hot"),
        NetworkBrowseFacet("magic school", "/network?q=magic"),
        NetworkBrowseFacet("survival sci-fi", "/network?q=survival"),
        NetworkBrowseFacet("small town", "/network?q=town"),
        NetworkBrowseFacet("urban real life", "/network?q=nyc"),
        NetworkBrowseFacet("wanted hooks", "/network?q=wanted", "hot"),
        NetworkBrowseFacet("current events", "/network?q=event"),
        NetworkBrowseFacet("plotting rooms", "/network?q=plotting"),
        NetworkBrowseFacet("claims", "/network?q=claims"),
        NetworkBrowseFacet("reserves", "/network?q=reserves"),
    ]


def _network_explore_lanes() -> list[NetworkExploreLane]:
    return [
        NetworkExploreLane(
            "Start with a wanted hook",
            "Open roles, rivals, factions, and face requests.",
            "/network?q=wanted",
            "casting",
        ),
        NetworkExploreLane(
            "Start with a mood",
            "Magic, crisis, survival, town, or urban play.",
            "/network?q=magic",
            "tags",
        ),
        NetworkExploreLane(
            "Start with an active roster",
            "Find realms with visible faces already in motion.",
            "/network?q=faces",
            "roster",
        ),
        NetworkExploreLane(
            "Start with current events",
            "World-state pressure and scenes already moving.",
            "/network?q=event",
            "story",
        ),
    ]


def _network_application_count(
    characters: list[Character],
    *,
    can_review: bool,
    membership_id: int,
) -> int:
    statuses = {"draft", "submitted", "revision_requested"}
    if can_review:
        return sum(1 for character in characters if character.application_status in statuses)
    return sum(
        1
        for character in characters
        if character.membership_id == membership_id and character.application_status in statuses
    )


def _network_theme_preview(theme: object | None) -> StudioNetworkThemePreview:
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


def _apply_post_style_preset(
    preset_slug: str,
    *,
    post_profile_variant: str,
    post_accent_style: str,
    post_border_style: str,
    post_title_style: str,
    post_density: str,
) -> tuple[str, str, str, str, str]:
    preset = POST_STYLE_PRESETS.get(preset_slug)
    if preset is None:
        return (
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density,
        )
    return (
        preset["post_profile_variant"],
        preset["post_accent_style"],
        preset["post_border_style"],
        preset["post_title_style"],
        preset["post_density"],
    )


def _unique_character_slug(
    repo: ForumRepository,
    community_id: int,
    name: str,
    *,
    current_character_id: int | None = None,
) -> str:
    base = _slugify(name)
    slug = base
    suffix = 2
    while True:
        try:
            existing = repo.get_character_by_slug(community_id, slug)
        except LookupError:
            return slug
        if existing.id == current_character_id:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def _unique_membership_username(repo: ForumRepository, community_id: int, username: str) -> str:
    base = _slugify_with_fallback(username, "writer")
    candidate = base
    suffix = 2
    while True:
        try:
            repo.get_membership_by_username(community_id, candidate)
        except LookupError:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "character"


def _unique_claim_type_slug(repo: ForumRepository, community_id: int, name: str) -> str:
    base = _slugify_with_fallback(name, "claim")
    slug = base
    suffix = 2
    while True:
        try:
            repo.get_claim_type_by_slug(community_id, slug)
        except LookupError:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1


def _unique_application_field_key(repo: ForumRepository, community_id: int, label: str) -> str:
    base = _slugify_with_fallback(label, "field").replace("-", "_")
    field_key = base
    suffix = 2
    while True:
        try:
            repo.get_application_template_field_by_key(community_id, field_key)
        except LookupError:
            return field_key
        field_key = f"{base}_{suffix}"
        suffix += 1


def _slugify_with_fallback(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def _claim_value_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or value.strip().lower()


def _normalize_claim_status(status: str) -> str:
    normalized = status.strip() or "claimed"
    if normalized == "open":
        normalized = "available"
    if normalized not in {"claimed", "reserved", "available"}:
        raise ValueError(f"unsupported claim status: {normalized}")
    return normalized
