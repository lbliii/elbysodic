"""SQLite row mappers for forum-domain records."""

from __future__ import annotations

import sqlite3

from elbysodic.domain.boards import (
    BOARD_SIDEBAR_SECTION_REALMS,
    normalize_board_image_focal_point,
    normalize_board_image_overlay,
    normalize_board_image_treatment,
    normalize_board_kind,
    normalize_board_sidebar_section,
)
from elbysodic.domain.models import (
    ApplicationFieldValue,
    ApplicationTemplateField,
    Board,
    Character,
    CharacterApplication,
    CharacterApplicationEvent,
    CharacterClaim,
    CharacterPlotHook,
    CharacterPlotHookInterest,
    CharacterReserve,
    ClaimType,
    Community,
    CommunityDiscoveryProfile,
    CommunityDiscoveryTag,
    CommunityInvitation,
    CommunityMembership,
    CommunityTheme,
    Facet,
    FacetGroup,
    Material,
    Notification,
    PlottingRoom,
    PlottingRoomMessage,
    PlottingRoomParticipant,
    Post,
    PostRevision,
    RealmInteraction,
    RealmInteractionAnswer,
    RealmInteractionOption,
    RealmInteractionQuestion,
    RealmInteractionResponse,
    Role,
    SidebarSectionConfig,
    Thread,
    ThreadParticipant,
    ThreadWatch,
    User,
    UserSession,
    WantedAd,
    WantedAdInterest,
)


def _community_from_row(row: sqlite3.Row) -> Community:
    return Community(
        id=row["id"],
        name=row["name"],
        slug=row["slug"],
        host=row["host"],
        launch_status=row["launch_status"],
        default_theme_id=row["default_theme_id"],
        identity_accent_facet_group_id=row["identity_accent_facet_group_id"],
        community_mark_url=row["community_mark_url"],
        community_mark_alt=row["community_mark_alt"],
        world_hero_image_url=row["world_hero_image_url"],
        world_hero_image_alt=row["world_hero_image_alt"],
        world_hero_treatment=row["world_hero_treatment"],
        world_hero_focal_point=row["world_hero_focal_point"],
        world_hero_overlay=row["world_hero_overlay"],
        world_hero_height=row["world_hero_height"],
        enabled_post_profile_variants=row["enabled_post_profile_variants"],
        enabled_post_accent_styles=row["enabled_post_accent_styles"],
        enabled_post_border_styles=row["enabled_post_border_styles"],
        enabled_post_title_styles=row["enabled_post_title_styles"],
        enabled_post_densities=row["enabled_post_densities"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _community_theme_from_row(row: sqlite3.Row) -> CommunityTheme:
    return CommunityTheme(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        name=row["name"],
        tokens_json=row["tokens_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _user_from_row(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


def _user_session_from_row(row: sqlite3.Row) -> UserSession:
    return UserSession(
        id=row["id"],
        user_id=row["user_id"],
        token_hash=row["token_hash"],
        selected_community_id=row["selected_community_id"],
        selected_membership_id=row["selected_membership_id"],
        created_at=row["created_at"],
        last_seen_at=row["last_seen_at"],
        expires_at=row["expires_at"],
        revoked_at=row["revoked_at"],
    )


def _community_invitation_from_row(row: sqlite3.Row) -> CommunityInvitation:
    return CommunityInvitation(
        id=row["id"],
        community_id=row["community_id"],
        email=row["email"],
        role_id=row["role_id"],
        invited_by_membership_id=row["invited_by_membership_id"],
        token_hash=row["token_hash"],
        status=row["status"],
        expires_at=row["expires_at"],
        accepted_user_id=row["accepted_user_id"],
        accepted_membership_id=row["accepted_membership_id"],
        created_at=row["created_at"],
        accepted_at=row["accepted_at"],
        revoked_at=row["revoked_at"],
    )


def _role_from_row(row: sqlite3.Row) -> Role:
    return Role(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        name=row["name"],
        is_admin=bool(row["is_admin"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _community_discovery_profile_from_row(row: sqlite3.Row) -> CommunityDiscoveryProfile:
    return CommunityDiscoveryProfile(
        community_id=row["community_id"],
        premise_archetype=row["premise_archetype"],
        play_engine=row["play_engine"],
        lore_aperture=row["lore_aperture"],
        access_model=row["access_model"],
        application_model=row["application_model"],
        age_rating=row["age_rating"],
        content_rating=row["content_rating"],
        activity_pace=row["activity_pace"],
        activity_expectation=row["activity_expectation"],
        forum_adjunct=row["forum_adjunct"],
        roster_posture=row["roster_posture"],
        catalog_pitch=row["catalog_pitch"],
        onboarding_pitch=row["onboarding_pitch"],
        staff_pick_label=row["staff_pick_label"],
        featured_event_material_id=row["featured_event_material_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _community_discovery_tag_from_row(row: sqlite3.Row) -> CommunityDiscoveryTag:
    return CommunityDiscoveryTag(
        id=row["id"],
        community_id=row["community_id"],
        tag_type=row["tag_type"],
        tag_key=row["tag_key"],
        label=row["label"],
        search_text=row["search_text"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _membership_from_row(row: sqlite3.Row) -> CommunityMembership:
    return CommunityMembership(
        id=row["id"],
        community_id=row["community_id"],
        user_id=row["user_id"],
        username=row["username"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        role_id=row["role_id"],
        default_character_id=row["default_character_id"],
        post_count=row["post_count"],
        is_active=bool(row["is_active"]),
        joined_at=row["joined_at"],
    )


def _board_from_row(row: sqlite3.Row) -> Board:
    return Board(
        id=row["id"],
        community_id=row["community_id"],
        parent_board_id=row["parent_board_id"],
        slug=row["slug"],
        name=row["name"],
        board_kind=normalize_board_kind(row["board_kind"]),
        sidebar_section=normalize_board_sidebar_section(
            row["sidebar_section"],
            row["board_kind"],
        ),
        tagline=row["tagline"],
        description=row["description"],
        image_url=row["image_url"],
        image_alt=row["image_alt"],
        image_treatment=normalize_board_image_treatment(row["image_treatment"]),
        image_focal_point=normalize_board_image_focal_point(row["image_focal_point"]),
        image_overlay=normalize_board_image_overlay(row["image_overlay"]),
        sort_order=row["sort_order"],
        navigation_order=row["navigation_order"],
        show_in_navigation=bool(row["show_in_navigation"]),
        is_private=bool(row["is_private"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _sidebar_section_config_from_row(row: sqlite3.Row) -> SidebarSectionConfig:
    section_key = normalize_board_sidebar_section(row["section_key"])
    return SidebarSectionConfig(
        id=row["id"],
        community_id=row["community_id"],
        realm=BOARD_SIDEBAR_SECTION_REALMS[section_key],
        section_key=section_key,
        label=row["label"],
        description=row["description"],
        sort_order=row["sort_order"],
        show_label=bool(row["show_label"]),
        is_system=bool(row["is_system"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _character_from_row(row: sqlite3.Row) -> Character:
    return Character(
        id=row["id"],
        community_id=row["community_id"],
        membership_id=row["membership_id"],
        name=row["name"],
        slug=row["slug"],
        avatar_url=row["avatar_url"],
        poster_url=row["poster_url"],
        poster_alt=row["poster_alt"],
        tagline=row["tagline"],
        accent_color=row["accent_color"],
        summary=row["summary"],
        post_profile_variant=row["post_profile_variant"],
        post_accent_style=row["post_accent_style"],
        post_border_style=row["post_border_style"],
        post_title_style=row["post_title_style"],
        post_density=row["post_density"],
        application_status=row["application_status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _character_application_from_row(row: sqlite3.Row) -> CharacterApplication:
    return CharacterApplication(
        id=row["id"],
        community_id=row["community_id"],
        membership_id=row["membership_id"],
        character_id=row["character_id"],
        source_wanted_ad_id=row["source_wanted_ad_id"],
        source_wanted_ad_interest_id=row["source_wanted_ad_interest_id"],
        title=row["title"],
        summary=row["summary"],
        body=row["body"],
        status=row["status"],
        revision_notes=row["revision_notes"],
        staff_notes=row["staff_notes"],
        checklist=row["checklist"],
        submitted_at=row["submitted_at"],
        reviewed_at=row["reviewed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _character_application_event_from_row(row: sqlite3.Row) -> CharacterApplicationEvent:
    return CharacterApplicationEvent(
        id=row["id"],
        community_id=row["community_id"],
        application_id=row["application_id"],
        actor_membership_id=row["actor_membership_id"],
        actor_character_id=row["actor_character_id"],
        from_status=row["from_status"],
        to_status=row["to_status"],
        note=row["note"],
        created_at=row["created_at"],
    )


def _facet_group_from_row(row: sqlite3.Row) -> FacetGroup:
    return FacetGroup(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        selection_mode=row["selection_mode"],
        visibility=row["visibility"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _facet_from_row(row: sqlite3.Row) -> Facet:
    return Facet(
        id=row["id"],
        community_id=row["community_id"],
        facet_group_id=row["facet_group_id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        accent_color=row["accent_color"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _material_from_row(row: sqlite3.Row) -> Material:
    return Material(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        title=row["title"],
        material_type=row["material_type"],
        summary=row["summary"],
        body=row["body"],
        status=row["status"],
        sort_order=row["sort_order"],
        is_featured=bool(row["is_featured"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _wanted_ad_from_row(row: sqlite3.Row) -> WantedAd:
    return WantedAd(
        id=row["id"],
        community_id=row["community_id"],
        creator_membership_id=row["creator_membership_id"],
        creator_character_id=row["creator_character_id"],
        related_material_id=row["related_material_id"],
        slug=row["slug"],
        title=row["title"],
        wanted_type=row["wanted_type"],
        summary=row["summary"],
        body=row["body"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _character_plot_hook_from_row(row: sqlite3.Row) -> CharacterPlotHook:
    return CharacterPlotHook(
        id=row["id"],
        community_id=row["community_id"],
        author_membership_id=row["author_membership_id"],
        character_id=row["character_id"],
        related_material_id=row["related_material_id"],
        slug=row["slug"],
        title=row["title"],
        hook_type=row["hook_type"],
        summary=row["summary"],
        body=row["body"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _character_plot_hook_interest_from_row(row: sqlite3.Row) -> CharacterPlotHookInterest:
    return CharacterPlotHookInterest(
        id=row["id"],
        community_id=row["community_id"],
        plot_hook_id=row["plot_hook_id"],
        membership_id=row["membership_id"],
        character_id=row["character_id"],
        note=row["note"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _wanted_ad_interest_from_row(row: sqlite3.Row) -> WantedAdInterest:
    return WantedAdInterest(
        id=row["id"],
        community_id=row["community_id"],
        wanted_ad_id=row["wanted_ad_id"],
        membership_id=row["membership_id"],
        character_id=row["character_id"],
        prospective_character_name=row["prospective_character_name"],
        note=row["note"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _plotting_room_from_row(row: sqlite3.Row) -> PlottingRoom:
    return PlottingRoom(
        id=row["id"],
        community_id=row["community_id"],
        owner_membership_id=row["owner_membership_id"],
        source_plot_hook_id=row["source_plot_hook_id"],
        source_plot_hook_interest_id=row["source_plot_hook_interest_id"],
        source_wanted_ad_id=row["source_wanted_ad_id"],
        source_wanted_ad_interest_id=row["source_wanted_ad_interest_id"],
        title=row["title"],
        summary=row["summary"],
        notes=row["notes"],
        next_step=row["next_step"],
        target_board_id=row["target_board_id"],
        target_thread_id=row["target_thread_id"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _plotting_room_participant_from_row(row: sqlite3.Row) -> PlottingRoomParticipant:
    return PlottingRoomParticipant(
        id=row["id"],
        community_id=row["community_id"],
        plotting_room_id=row["plotting_room_id"],
        membership_id=row["membership_id"],
        character_id=row["character_id"],
        prospective_character_name=row["prospective_character_name"],
        participant_role=row["participant_role"],
        created_at=row["created_at"],
    )


def _plotting_room_message_from_row(row: sqlite3.Row) -> PlottingRoomMessage:
    return PlottingRoomMessage(
        id=row["id"],
        community_id=row["community_id"],
        plotting_room_id=row["plotting_room_id"],
        author_membership_id=row["author_membership_id"],
        author_character_id=row["author_character_id"],
        body=row["body"],
        created_at=row["created_at"],
    )


def _character_reserve_from_row(row: sqlite3.Row) -> CharacterReserve:
    return CharacterReserve(
        id=row["id"],
        community_id=row["community_id"],
        membership_id=row["membership_id"],
        character_id=row["character_id"],
        wanted_ad_id=row["wanted_ad_id"],
        wanted_ad_interest_id=row["wanted_ad_interest_id"],
        reserve_type=row["reserve_type"],
        title=row["title"],
        notes=row["notes"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _claim_type_from_row(row: sqlite3.Row) -> ClaimType:
    return ClaimType(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        name=row["name"],
        claim_kind=row["claim_kind"],
        description=row["description"],
        visibility=row["visibility"],
        is_required=bool(row["is_required"]),
        is_exclusive=bool(row["is_exclusive"]),
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _character_claim_from_row(row: sqlite3.Row) -> CharacterClaim:
    return CharacterClaim(
        id=row["id"],
        community_id=row["community_id"],
        claim_type_id=row["claim_type_id"],
        character_id=row["character_id"],
        application_id=row["application_id"],
        source_reserve_id=row["source_reserve_id"],
        value=row["value"],
        label=row["label"],
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _application_template_field_from_row(row: sqlite3.Row) -> ApplicationTemplateField:
    return ApplicationTemplateField(
        id=row["id"],
        community_id=row["community_id"],
        field_key=row["field_key"],
        label=row["label"],
        field_type=row["field_type"],
        help_text=row["help_text"],
        placeholder=row["placeholder"],
        options_json=row["options_json"],
        maps_to_claim_type_id=row["maps_to_claim_type_id"],
        is_required=bool(row["is_required"]),
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _application_field_value_from_row(row: sqlite3.Row) -> ApplicationFieldValue:
    return ApplicationFieldValue(
        id=row["id"],
        community_id=row["community_id"],
        application_id=row["application_id"],
        field_id=row["field_id"],
        value=row["value"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _realm_interaction_from_row(row: sqlite3.Row) -> RealmInteraction:
    return RealmInteraction(
        id=row["id"],
        community_id=row["community_id"],
        slug=row["slug"],
        title=row["title"],
        interaction_type=row["interaction_type"],
        placement=row["placement"],
        summary=row["summary"],
        body=row["body"],
        status=row["status"],
        result_mode=row["result_mode"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _realm_interaction_question_from_row(row: sqlite3.Row) -> RealmInteractionQuestion:
    return RealmInteractionQuestion(
        id=row["id"],
        community_id=row["community_id"],
        interaction_id=row["interaction_id"],
        prompt=row["prompt"],
        help_text=row["help_text"],
        question_type=row["question_type"],
        is_required=bool(row["is_required"]),
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _realm_interaction_option_from_row(row: sqlite3.Row) -> RealmInteractionOption:
    return RealmInteractionOption(
        id=row["id"],
        community_id=row["community_id"],
        question_id=row["question_id"],
        slug=row["slug"],
        label=row["label"],
        description=row["description"],
        result_key=row["result_key"],
        score=row["score"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _realm_interaction_response_from_row(row: sqlite3.Row) -> RealmInteractionResponse:
    return RealmInteractionResponse(
        id=row["id"],
        community_id=row["community_id"],
        interaction_id=row["interaction_id"],
        membership_id=row["membership_id"],
        character_id=row["character_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _realm_interaction_answer_from_row(row: sqlite3.Row) -> RealmInteractionAnswer:
    return RealmInteractionAnswer(
        id=row["id"],
        community_id=row["community_id"],
        response_id=row["response_id"],
        question_id=row["question_id"],
        option_id=row["option_id"],
        text_answer=row["text_answer"],
        created_at=row["created_at"],
    )


def _thread_from_row(row: sqlite3.Row) -> Thread:
    return Thread(
        id=row["id"],
        community_id=row["community_id"],
        board_id=row["board_id"],
        author_membership_id=row["author_membership_id"],
        author_character_id=row["author_character_id"],
        slug=row["slug"],
        title=row["title"],
        status=row["status"],
        location=row["location"],
        timeline=row["timeline"],
        summary=row["summary"],
        posting_mode=row["posting_mode"],
        is_locked=bool(row["is_locked"]),
        is_pinned=bool(row["is_pinned"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _thread_participant_from_row(row: sqlite3.Row) -> ThreadParticipant:
    return ThreadParticipant(
        id=row["id"],
        community_id=row["community_id"],
        thread_id=row["thread_id"],
        character_id=row["character_id"],
        added_at=row["added_at"],
    )


def _post_from_row(row: sqlite3.Row) -> Post:
    return Post(
        id=row["id"],
        community_id=row["community_id"],
        thread_id=row["thread_id"],
        post_number=row["post_number"],
        author_membership_id=row["author_membership_id"],
        author_character_id=row["author_character_id"],
        body=row["body"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _post_revision_from_row(row: sqlite3.Row) -> PostRevision:
    return PostRevision(
        id=row["id"],
        community_id=row["community_id"],
        post_id=row["post_id"],
        editor_membership_id=row["editor_membership_id"],
        previous_body=row["previous_body"],
        new_body=row["new_body"],
        created_at=row["created_at"],
    )


def _thread_watch_from_row(row: sqlite3.Row) -> ThreadWatch:
    return ThreadWatch(
        id=row["id"],
        community_id=row["community_id"],
        thread_id=row["thread_id"],
        membership_id=row["membership_id"],
        created_at=row["created_at"],
    )


def _notification_from_row(row: sqlite3.Row) -> Notification:
    return Notification(
        id=row["id"],
        community_id=row["community_id"],
        membership_id=row["membership_id"],
        kind=row["kind"],
        thread_id=row["thread_id"],
        post_id=row["post_id"],
        wanted_ad_id=row["wanted_ad_id"],
        wanted_ad_interest_id=row["wanted_ad_interest_id"],
        character_plot_hook_id=row["character_plot_hook_id"],
        plotting_room_id=row["plotting_room_id"],
        character_id=row["character_id"],
        actor_membership_id=row["actor_membership_id"],
        actor_character_id=row["actor_character_id"],
        read_at=row["read_at"],
        created_at=row["created_at"],
    )
