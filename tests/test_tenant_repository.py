from __future__ import annotations

import pytest

from elbysodic.db import ForumRepository, connect, create_schema
from elbysodic.db.repositories.base import TenantBoundaryError


@pytest.fixture
def repo() -> ForumRepository:
    connection = connect()
    create_schema(connection)
    repository = ForumRepository(connection)
    repository.seed_default_community()
    return repository


def test_boards_are_scoped_by_community(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")

    repo.create_board(default.id, "announcements", "Announcements")
    repo.create_board(hosted.id, "announcements", "Hosted Announcements")

    assert [board.name for board in repo.list_boards(default.id)] == ["Announcements"]
    assert [board.name for board in repo.list_boards(hosted.id)] == ["Hosted Announcements"]


def test_schema_migrates_existing_boards_for_place_navigation() -> None:
    connection = connect()
    connection.executescript(
        """
        CREATE TABLE communities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            host TEXT UNIQUE,
            default_theme_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE boards (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            slug TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_private INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, slug)
        );
        INSERT INTO communities (id, name, slug, host, default_theme_id, created_at, updated_at)
        VALUES (1, 'Default', 'default', NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        INSERT INTO boards (
            id, community_id, slug, name, description, sort_order, is_private, created_at, updated_at
        )
        VALUES (
            1, 1, 'ic', 'In Character', 'Old board shape.', 10, 0,
            '2026-01-01T00:00:00', '2026-01-01T00:00:00'
        );
        """
    )

    create_schema(connection)

    columns = {row["name"] for row in connection.execute("PRAGMA table_info(boards)").fetchall()}
    indexes = {row["name"] for row in connection.execute("PRAGMA index_list(boards)").fetchall()}
    board = connection.execute(
        """
        SELECT parent_board_id, board_kind, tagline, image_url, image_alt
        FROM boards
        WHERE id = 1
        """
    ).fetchone()

    assert {"parent_board_id", "board_kind", "tagline", "image_url", "image_alt"}.issubset(columns)
    assert "idx_boards_parent_sort" in indexes
    assert dict(board) == {
        "parent_board_id": None,
        "board_kind": "location",
        "tagline": "",
        "image_url": None,
        "image_alt": "",
    }


def test_schema_migrates_plot_hook_and_prospective_interest_columns() -> None:
    connection = connect()
    connection.executescript(
        """
        CREATE TABLE wanted_ad_interests (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            wanted_ad_id INTEGER NOT NULL,
            membership_id INTEGER NOT NULL,
            character_id INTEGER NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'interested',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, wanted_ad_id, membership_id, character_id)
        );
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            membership_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            thread_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            actor_membership_id INTEGER NOT NULL,
            actor_character_id INTEGER NOT NULL,
            read_at TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    create_schema(connection)

    wanted_columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(wanted_ad_interests)").fetchall()
    }
    notification_columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(notifications)").fetchall()
    }
    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert "character_plot_hooks" in tables
    assert "character_plot_hook_interests" in tables
    assert "plotting_rooms" in tables
    assert "plotting_room_participants" in tables
    assert wanted_columns["character_id"]["notnull"] == 0
    assert "prospective_character_name" in wanted_columns
    assert "character_plot_hook_id" in notification_columns
    assert "plotting_room_id" in notification_columns
    assert notification_columns["actor_character_id"]["notnull"] == 0


def test_schema_migrates_existing_characters_for_post_profile_variants() -> None:
    connection = connect()
    connection.executescript(
        """
        CREATE TABLE communities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            host TEXT UNIQUE,
            default_theme_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE community_memberships (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar_url TEXT,
            role_id INTEGER NOT NULL,
            default_character_id INTEGER,
            post_count INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            joined_at TEXT NOT NULL
        );
        CREATE TABLE characters (
            id INTEGER PRIMARY KEY,
            community_id INTEGER NOT NULL,
            membership_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            avatar_url TEXT,
            summary TEXT NOT NULL DEFAULT '',
            application_status TEXT NOT NULL DEFAULT 'accepted',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (community_id, slug)
        );
        INSERT INTO communities (id, name, slug, host, default_theme_id, created_at, updated_at)
        VALUES (1, 'Default', 'default', NULL, NULL, '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        INSERT INTO community_memberships (
            id, community_id, user_id, username, display_name, role_id, joined_at
        )
        VALUES (1, 1, 1, 'writer', 'Writer', 1, '2026-01-01T00:00:00');
        INSERT INTO characters (
            id, community_id, membership_id, name, slug, avatar_url, summary, created_at, updated_at
        )
        VALUES (
            1, 1, 1, 'Rogue', 'rogue', NULL, 'Careful hands.',
            '2026-01-01T00:00:00', '2026-01-01T00:00:00'
        );
        """
    )

    create_schema(connection)

    columns = {
        row["name"]: row for row in connection.execute("PRAGMA table_info(characters)").fetchall()
    }
    community_columns = {
        row["name"]: row for row in connection.execute("PRAGMA table_info(communities)").fetchall()
    }
    character = connection.execute(
        """
        SELECT
            post_profile_variant,
            post_accent_style,
            post_border_style,
            post_title_style,
            post_density
        FROM characters
        WHERE id = 1
        """
    ).fetchone()

    assert "post_profile_variant" in columns
    assert "post_accent_style" in columns
    assert "post_border_style" in columns
    assert "post_title_style" in columns
    assert "post_density" in columns
    assert "identity_accent_facet_group_id" in community_columns
    assert character["post_profile_variant"] == "bio"
    assert character["post_accent_style"] == "soft"
    assert character["post_border_style"] == "hairline"
    assert character["post_title_style"] == "standard"
    assert character["post_density"] == "calm"


def test_community_identity_accent_group_is_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_group = repo.create_facet_group(default.id, "house", "House")
    hosted_group = repo.create_facet_group(hosted.id, "house", "House")

    updated = repo.update_community_identity_accent_group(default.id, default_group.id)

    assert updated.identity_accent_facet_group_id == default_group.id
    with pytest.raises(LookupError):
        repo.update_community_identity_accent_group(default.id, hosted_group.id)


def test_board_hierarchy_is_tenant_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    parent = repo.create_board(default.id, "academy", "Academy", board_kind="location")
    hosted_parent = repo.create_board(hosted.id, "academy", "Academy", board_kind="location")

    child = repo.create_board(
        default.id,
        "med-bay",
        "Med Bay",
        parent_board_id=parent.id,
        board_kind="sublocation",
    )

    assert child.parent_board_id == parent.id
    assert [board.slug for board in repo.list_child_boards(default.id, parent.id)] == ["med-bay"]
    assert [board.slug for board in repo.list_child_boards(default.id, None)] == ["academy"]

    with pytest.raises(LookupError):
        repo.create_board(
            default.id,
            "wrong-house",
            "Wrong House",
            parent_board_id=hosted_parent.id,
        )


def test_board_cannot_parent_itself(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    board = repo.create_board(community.id, "academy", "Academy", board_kind="location")

    with pytest.raises(TenantBoundaryError):
        repo.update_board(
            community.id,
            board.id,
            name=board.name,
            description=board.description,
            sort_order=board.sort_order,
            parent_board_id=board.id,
            board_kind=board.board_kind,
            tagline=board.tagline,
            image_url=board.image_url,
            image_alt=board.image_alt,
            is_private=board.is_private,
        )


def test_public_identity_is_membership_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")

    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "admin", "Admin", is_admin=True)

    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "lark",
        "Lark",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "winterglass",
        "Winterglass",
    )

    assert default_membership.username == "lark"
    assert hosted_membership.username == "winterglass"
    assert repo.get_role(hosted.id, hosted_membership.role_id).is_admin is True
    assert repo.get_role(default.id, default_membership.role_id).is_admin is False


def test_characters_are_membership_owned_posting_identities(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")

    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "writer",
        "Writer Elsewhere",
    )

    rogue = repo.create_character(
        default.id,
        default_membership.id,
        "rogue",
        "Rogue",
        poster_url="https://example.test/rogue-poster.png",
        poster_alt="Rogue standing in the Danger Room",
        tagline="Careful hands, reckless heart.",
        accent_color="#79a889",
        post_profile_variant="dock",
        post_accent_style="glow",
        post_border_style="bracket",
        post_title_style="serif",
        post_density="dramatic",
        make_default=True,
    )
    magneto = repo.create_character(hosted.id, hosted_membership.id, "magneto", "Magneto")
    draft = repo.update_character_application_status(default.id, rogue.id, "draft")

    assert draft.application_status == "draft"
    assert draft.poster_url == "https://example.test/rogue-poster.png"
    assert draft.poster_alt == "Rogue standing in the Danger Room"
    assert draft.tagline == "Careful hands, reckless heart."
    assert draft.accent_color == "#79a889"
    assert draft.post_profile_variant == "dock"
    assert draft.post_accent_style == "glow"
    assert draft.post_border_style == "bracket"
    assert draft.post_title_style == "serif"
    assert draft.post_density == "dramatic"
    assert repo.get_character(default.id, rogue.id).application_status == "draft"
    assert repo.get_membership(default.id, default_membership.id).default_character_id == rogue.id
    assert repo.get_membership(hosted.id, hosted_membership.id).default_character_id is None
    assert repo.list_characters(default.id, default_membership.id) == [draft]
    assert repo.list_characters(hosted.id, hosted_membership.id) == [magneto]

    with pytest.raises(LookupError):
        repo.set_default_character(default.id, default_membership.id, magneto.id)


def test_character_updates_are_scoped_by_community(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "writer",
        "Writer Elsewhere",
    )
    rogue = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue Elsewhere")

    updated = repo.update_character(
        default.id,
        rogue.id,
        slug="rogue-prime",
        name="Rogue Prime",
        avatar_url="https://example.test/rogue.png",
        poster_url="https://example.test/rogue-prime-poster.png",
        poster_alt="Rogue Prime portrait",
        tagline="Nobody touches the plot without consequence.",
        accent_color="#79a889",
        summary="Still carrying the whole plot.",
        post_profile_variant="poster",
        post_accent_style="line",
        post_border_style="double",
        post_title_style="mono",
        post_density="compact",
    )

    assert updated.slug == "rogue-prime"
    assert updated.name == "Rogue Prime"
    assert updated.avatar_url == "https://example.test/rogue.png"
    assert updated.poster_url == "https://example.test/rogue-prime-poster.png"
    assert updated.poster_alt == "Rogue Prime portrait"
    assert updated.tagline == "Nobody touches the plot without consequence."
    assert updated.accent_color == "#79a889"
    assert updated.summary == "Still carrying the whole plot."
    assert updated.post_profile_variant == "poster"
    assert updated.post_accent_style == "line"
    assert updated.post_border_style == "double"
    assert updated.post_title_style == "mono"
    assert updated.post_density == "compact"
    assert repo.get_character_by_slug(hosted.id, "rogue").name == "Rogue Elsewhere"

    with pytest.raises(LookupError):
        repo.update_character(
            hosted.id,
            rogue.id,
            slug="bad",
            name="Bad",
            avatar_url=None,
            summary="Wrong community.",
        )


def test_world_facets_scope_characters_boards_and_threads(repo: ForumRepository) -> None:
    community = repo.get_community(1)
    role = repo.create_role(community.id, "member", "Member")
    user = repo.create_user("writer@example.com", "hash")
    membership = repo.create_membership(community.id, user.id, role.id, "writer", "Writer")
    rogue = repo.create_character(community.id, membership.id, "rogue", "Rogue")
    board = repo.create_board(community.id, "danger-room", "Danger Room")
    thread = repo.create_thread(
        community.id, board.id, rogue.id, "sentinel-drill", "Sentinel Drill"
    )

    species = repo.create_facet_group(community.id, "species", "Species", sort_order=10)
    affiliation = repo.create_facet_group(
        community.id,
        "affiliation",
        "Affiliation",
        sort_order=20,
    )
    mutant = repo.create_facet(community.id, species.id, "mutant", "Mutant")
    x_men = repo.create_facet(community.id, affiliation.id, "x-men", "X-Men")

    repo.assign_character_facet(community.id, rogue.id, mutant.id)
    repo.assign_character_facet(community.id, rogue.id, x_men.id)
    repo.assign_board_facet(community.id, board.id, x_men.id)
    repo.assign_thread_facet(community.id, thread.id, x_men.id)

    assert [facet.slug for facet in repo.list_character_facets(community.id, rogue.id)] == [
        "mutant",
        "x-men",
    ]
    assert [facet.slug for facet in repo.list_board_facets(community.id, board.id)] == ["x-men"]
    assert [facet.slug for facet in repo.list_thread_facets(community.id, thread.id)] == ["x-men"]
    assert repo.list_character_ids_for_facets(community.id, [mutant.id, x_men.id]) == {rogue.id}
    assert repo.list_thread_ids_for_facets(community.id, [x_men.id]) == {thread.id}


def test_world_materials_are_tenant_scoped_and_facet_tagged(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_group = repo.create_facet_group(default.id, "affiliation", "Affiliation")
    hosted_group = repo.create_facet_group(hosted.id, "affiliation", "Affiliation")
    x_men = repo.create_facet(default.id, default_group.id, "x-men", "X-Men")
    repo.create_facet(hosted.id, hosted_group.id, "x-men", "X-Men Elsewhere")

    premise = repo.create_material(
        default.id,
        "premise",
        "Premise",
        material_type="premise",
        summary="The core hook.",
        body="Mutants face a new machine.",
        is_featured=True,
    )
    repo.create_material(
        hosted.id,
        "premise",
        "Hosted Premise",
        material_type="premise",
        summary="Different world.",
    )
    repo.assign_material_facet(default.id, premise.id, x_men.id)
    updated = repo.update_material(
        default.id,
        premise.id,
        title="Updated Premise",
        material_type="premise",
        summary="Sharper hook.",
        body="Mutants face a machine with a budget.",
        status="published",
        sort_order=5,
        is_featured=False,
    )

    assert updated.title == "Updated Premise"
    assert updated.summary == "Sharper hook."
    assert updated.is_featured is False
    assert repo.get_material_by_slug(default.id, "premise").title == "Updated Premise"
    assert repo.get_material_by_slug(hosted.id, "premise").title == "Hosted Premise"
    assert [material.title for material in repo.list_materials(default.id)] == ["Updated Premise"]
    assert [facet.slug for facet in repo.list_material_facets(default.id, premise.id)] == ["x-men"]

    with pytest.raises(LookupError):
        repo.assign_material_facet(hosted.id, premise.id, x_men.id)


def test_wanted_ads_are_tenant_scoped_and_facet_tagged(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_user = repo.create_user("default@example.com", "hash")
    hosted_user = repo.create_user("hosted@example.com", "hash")
    default_membership = repo.create_membership(
        default.id,
        default_user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "hosted",
        "Hosted",
    )
    rogue = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    magneto = repo.create_character(default.id, default_membership.id, "magneto", "Magneto")
    hosted_character = repo.create_character(
        hosted.id,
        hosted_membership.id,
        "rogue",
        "Rogue Elsewhere",
    )
    group = repo.create_facet_group(default.id, "affiliation", "Affiliation")
    x_men = repo.create_facet(default.id, group.id, "x-men", "X-Men")

    wanted = repo.create_wanted_ad(
        default.id,
        default_membership.id,
        "rogue-rival",
        "Rogue rival",
        creator_character_id=rogue.id,
        summary="A sharp foil.",
    )
    repo.create_wanted_ad(
        hosted.id,
        hosted_membership.id,
        "rogue-rival",
        "Hosted rival",
        creator_character_id=hosted_character.id,
    )
    repo.add_wanted_ad_related_character(default.id, wanted.id, magneto.id)
    repo.assign_wanted_ad_facet(default.id, wanted.id, x_men.id)
    interest = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        default_membership.id,
        magneto.id,
    )
    notification = repo.create_notification(
        default.id,
        default_membership.id,
        kind="wanted_interest",
        wanted_ad_id=wanted.id,
        wanted_ad_interest_id=interest.id,
        actor_membership_id=default_membership.id,
        actor_character_id=magneto.id,
    )

    assert repo.get_wanted_ad_by_slug(default.id, "rogue-rival").title == "Rogue rival"
    assert repo.get_wanted_ad_by_slug(hosted.id, "rogue-rival").title == "Hosted rival"
    assert [item.title for item in repo.list_wanted_ads(default.id)] == ["Rogue rival"]
    assert [facet.slug for facet in repo.list_wanted_ad_facets(default.id, wanted.id)] == ["x-men"]
    assert repo.list_wanted_ad_related_characters(default.id, wanted.id) == [magneto]
    assert repo.list_wanted_ad_interests(default.id, wanted.id) == [interest]
    assert repo.list_wanted_ads_for_character(default.id, rogue.id) == [wanted]
    assert repo.list_wanted_ads_for_character(default.id, magneto.id) == [wanted]
    assert notification.wanted_ad_id == wanted.id
    assert notification.wanted_ad_interest_id == interest.id
    reserved_interest = repo.update_wanted_ad_interest_status(default.id, interest.id, "reserved")
    reserved_wanted = repo.update_wanted_ad_status(default.id, wanted.id, "reserved")
    assert reserved_interest.status == "reserved"
    assert reserved_wanted.status == "reserved"
    reserve = repo.create_character_reserve(
        default.id,
        default_membership.id,
        magneto.id,
        "Rogue rival",
        wanted_ad_id=wanted.id,
        wanted_ad_interest_id=interest.id,
        notes="Reserved from wanted hook: Rogue rival",
    )
    assert repo.get_character_reserve_for_wanted_interest(default.id, interest.id) == reserve
    assert repo.list_character_reserves(default.id, magneto.id) == [reserve]
    assert repo.list_character_reserves_for_wanted_ad(default.id, wanted.id) == [reserve]
    assert repo.list_character_reserves_for_community(default.id) == [reserve]
    assert repo.list_character_reserves_for_community(hosted.id) == []

    with pytest.raises(LookupError):
        repo.assign_wanted_ad_facet(hosted.id, wanted.id, x_men.id)
    with pytest.raises(LookupError):
        repo.create_wanted_ad_interest(
            hosted.id, wanted.id, hosted_membership.id, hosted_character.id
        )
    with pytest.raises(LookupError):
        repo.create_character_reserve(
            hosted.id,
            hosted_membership.id,
            hosted_character.id,
            "Wrong forum",
            wanted_ad_id=wanted.id,
        )


def test_plot_hooks_and_prospective_wanted_interest_are_tenant_scoped(
    repo: ForumRepository,
) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    owner_user = repo.create_user("owner@example.com", "hash")
    prospect_user = repo.create_user("prospect@example.com", "hash")
    hosted_user = repo.create_user("hosted-prospect@example.com", "hash")
    owner = repo.create_membership(default.id, owner_user.id, role.id, "owner", "Owner")
    prospect = repo.create_membership(
        default.id,
        prospect_user.id,
        role.id,
        "prospect",
        "Prospect",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "prospect",
        "Hosted Prospect",
    )
    rogue = repo.create_character(default.id, owner.id, "rogue", "Rogue")
    gambit = repo.create_character(default.id, prospect.id, "gambit", "Gambit")
    hosted_character = repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue")
    group = repo.create_facet_group(default.id, "affiliation", "Affiliation")
    x_men = repo.create_facet(default.id, group.id, "x-men", "X-Men")

    hook = repo.create_character_plot_hook(
        default.id,
        owner.id,
        rogue.id,
        "old-ghosts",
        "Old ghosts",
        hook_type="relationship",
        summary="A pressure point.",
    )
    repo.create_character_plot_hook(
        hosted.id,
        hosted_membership.id,
        hosted_character.id,
        "old-ghosts",
        "Hosted ghosts",
    )
    repo.assign_character_plot_hook_facet(default.id, hook.id, x_men.id)
    interest = repo.create_character_plot_hook_interest(
        default.id,
        hook.id,
        prospect.id,
        gambit.id,
    )
    notification = repo.create_notification(
        default.id,
        owner.id,
        kind="plot_hook_interest",
        character_plot_hook_id=hook.id,
        actor_membership_id=prospect.id,
        actor_character_id=gambit.id,
    )

    wanted = repo.create_wanted_ad(
        default.id,
        owner.id,
        "gambit-wanted",
        "Gambit wanted",
        creator_character_id=rogue.id,
    )
    prospective = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        prospect.id,
        prospective_character_name="Remy LeBeau",
        note="I would app him for this.",
    )
    room = repo.create_plotting_room(
        default.id,
        owner.id,
        "Old ghosts: Gambit",
        source_plot_hook_id=hook.id,
        source_plot_hook_interest_id=interest.id,
        summary="Planning the pressure point.",
    )
    owner_participant = repo.create_plotting_room_participant(
        default.id,
        room.id,
        owner.id,
        character_id=rogue.id,
        participant_role="owner",
    )
    prospect_participant = repo.create_plotting_room_participant(
        default.id,
        room.id,
        prospect.id,
        character_id=gambit.id,
    )
    room_notification = repo.create_notification(
        default.id,
        prospect.id,
        kind="plotting_room_created",
        plotting_room_id=room.id,
        actor_membership_id=owner.id,
        actor_character_id=rogue.id,
    )
    duplicate = repo.create_wanted_ad_interest(
        default.id,
        wanted.id,
        prospect.id,
        prospective_character_name="Remy LeBeau",
    )

    assert repo.get_character_plot_hook_by_slug(default.id, rogue.id, "old-ghosts") == hook
    assert (
        repo.get_character_plot_hook_by_slug(hosted.id, hosted_character.id, "old-ghosts").title
        == "Hosted ghosts"
    )
    assert repo.list_character_plot_hooks_for_character(default.id, rogue.id) == [hook]
    assert repo.list_character_plot_hook_facets(default.id, hook.id) == [x_men]
    assert repo.list_character_plot_hook_ids_for_facets(default.id, [x_men.id]) == {hook.id}
    assert interest.character_id == gambit.id
    assert notification.character_plot_hook_id == hook.id
    assert prospective.character_id is None
    assert prospective.prospective_character_name == "Remy LeBeau"
    assert duplicate.id == prospective.id
    assert repo.get_plotting_room_for_plot_hook_interest(default.id, interest.id) == room
    assert repo.list_plotting_rooms_for_membership(default.id, prospect.id) == [room]
    assert repo.list_plotting_rooms_for_character(default.id, rogue.id) == [room]
    assert repo.list_plotting_room_participants(default.id, room.id) == [
        owner_participant,
        prospect_participant,
    ]
    assert room_notification.plotting_room_id == room.id

    with pytest.raises(LookupError):
        repo.assign_character_plot_hook_facet(hosted.id, hook.id, x_men.id)
    with pytest.raises(LookupError):
        repo.create_wanted_ad_interest(hosted.id, wanted.id, hosted_membership.id)
    with pytest.raises(LookupError):
        repo.create_plotting_room(
            hosted.id,
            hosted_membership.id,
            "Crossed room",
            source_plot_hook_id=hook.id,
            source_plot_hook_interest_id=interest.id,
        )


def test_threads_and_posts_cannot_cross_community_boundaries(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("writer@example.com", "hash")

    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "lark",
        "Lark",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "lark",
        "Lark Elsewhere",
    )
    default_character = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    hosted_character = repo.create_character(hosted.id, hosted_membership.id, "magneto", "Magneto")
    default_board = repo.create_board(default.id, "ic", "In Character")
    hosted_board = repo.create_board(hosted.id, "ic", "In Character")

    thread = repo.create_thread(
        default.id,
        default_board.id,
        default_character.id,
        "opening-scene",
        "Opening Scene",
    )
    repo.create_thread(
        hosted.id,
        hosted_board.id,
        hosted_character.id,
        "opening-scene",
        "Opening Scene Elsewhere",
    )
    post = repo.create_post(default.id, thread.id, default_character.id, "First post.")

    assert [item.title for item in repo.list_threads(default.id)] == ["Opening Scene"]
    assert repo.get_thread(default.id, thread.id).author_character_id == default_character.id
    assert [item.body for item in repo.list_posts(default.id, thread.id)] == ["First post."]
    assert post.author_character_id == default_character.id
    assert post.author_membership_id == default_membership.id

    with pytest.raises(LookupError):
        repo.create_thread(default.id, hosted_board.id, default_character.id, "bad", "Bad")

    with pytest.raises(LookupError):
        repo.create_post(hosted.id, post.id, hosted_character.id, "Wrong community.")


def test_thread_flags_sort_pinned_threads_first(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    user = repo.create_user("flags@example.com", "hash")
    role = repo.create_role(default.id, "member", "Member")
    membership = repo.create_membership(default.id, user.id, role.id, "flags", "Flags")
    character = repo.create_character(default.id, membership.id, "rogue", "Rogue")
    board = repo.create_board(default.id, "ic", "In Character")

    regular = repo.create_thread(default.id, board.id, character.id, "regular", "Regular")
    pinned = repo.create_thread(
        default.id,
        board.id,
        character.id,
        "pinned",
        "Pinned",
        is_pinned=True,
    )
    locked = repo.update_thread_flags(default.id, regular.id, is_locked=True)

    assert locked.is_locked is True
    assert [thread.slug for thread in repo.list_threads(default.id, board.id)] == [
        pinned.slug,
        regular.slug,
    ]


def test_thread_scene_metadata_and_participants_are_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("scene@example.com", "hash")
    hosted_user = repo.create_user("hosted-scene@example.com", "hash")
    role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    membership = repo.create_membership(default.id, user.id, role.id, "scene", "Scene")
    hosted_membership = repo.create_membership(
        hosted.id,
        hosted_user.id,
        hosted_role.id,
        "scene",
        "Scene Elsewhere",
    )
    rogue = repo.create_character(default.id, membership.id, "rogue", "Rogue")
    storm = repo.create_character(default.id, membership.id, "storm", "Storm")
    gambit = repo.create_character(default.id, membership.id, "gambit", "Gambit")
    hosted_rogue = repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue")
    board = repo.create_board(default.id, "ic", "In Character")
    hosted_board = repo.create_board(hosted.id, "ic", "In Character")

    thread = repo.create_thread(
        default.id,
        board.id,
        rogue.id,
        "moonlight",
        "Moonlight",
        status="open",
        location="Lake",
        timeline="Night",
        summary="A quiet lakeside scene.",
        posting_mode="posting_order",
    )
    repo.create_thread(hosted.id, hosted_board.id, hosted_rogue.id, "moonlight", "Moonlight")
    repo.set_thread_participants(default.id, thread.id, [rogue.id, storm.id])

    stored = repo.get_thread(default.id, thread.id)
    assert stored.status == "open"
    assert stored.location == "Lake"
    assert stored.timeline == "Night"
    assert stored.summary == "A quiet lakeside scene."
    assert stored.posting_mode == "posting_order"
    assert [
        character.slug for character in repo.list_thread_participants(default.id, thread.id)
    ] == [
        "rogue",
        "storm",
    ]
    repo.create_post(default.id, thread.id, gambit.id, "Gambit joins the scene.")
    assert {
        character.slug for character in repo.list_thread_participants(default.id, thread.id)
    } == {"rogue", "storm", "gambit"}
    repo.set_thread_participants(default.id, thread.id, [rogue.id])
    assert {
        character.slug for character in repo.list_thread_participants(default.id, thread.id)
    } == {"rogue", "gambit"}

    with pytest.raises(LookupError):
        repo.add_thread_participant(default.id, thread.id, hosted_rogue.id)


def test_thread_reads_are_membership_scoped(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    user = repo.create_user("reads@example.com", "hash")
    other_user = repo.create_user("other-reads@example.com", "hash")
    role = repo.create_role(default.id, "member", "Member")
    membership = repo.create_membership(default.id, user.id, role.id, "reader", "Reader")
    other_membership = repo.create_membership(
        default.id,
        other_user.id,
        role.id,
        "other-reader",
        "Other Reader",
    )
    character = repo.create_character(default.id, membership.id, "rogue", "Rogue")
    board = repo.create_board(default.id, "ic", "In Character")
    thread = repo.create_thread(default.id, board.id, character.id, "scene", "Scene")

    repo.mark_thread_read(default.id, thread.id, membership.id, read_at="2026-01-01T00:00:00+00:00")

    assert repo.get_thread_read_at(default.id, thread.id, membership.id) == (
        "2026-01-01T00:00:00+00:00"
    )
    assert repo.get_thread_read_at(default.id, thread.id, other_membership.id) is None


def test_post_revisions_are_scoped_by_community(repo: ForumRepository) -> None:
    default = repo.get_community(1)
    hosted = repo.create_community("hosted", "Hosted Test")
    user = repo.create_user("revisions@example.com", "hash")
    default_role = repo.create_role(default.id, "member", "Member")
    hosted_role = repo.create_role(hosted.id, "member", "Member")
    default_membership = repo.create_membership(
        default.id,
        user.id,
        default_role.id,
        "writer",
        "Writer",
    )
    hosted_membership = repo.create_membership(
        hosted.id,
        user.id,
        hosted_role.id,
        "writer",
        "Writer Elsewhere",
    )
    default_character = repo.create_character(default.id, default_membership.id, "rogue", "Rogue")
    hosted_character = repo.create_character(hosted.id, hosted_membership.id, "rogue", "Rogue")
    default_board = repo.create_board(default.id, "ic", "In Character")
    hosted_board = repo.create_board(hosted.id, "ic", "In Character")
    default_thread = repo.create_thread(
        default.id, default_board.id, default_character.id, "a", "A"
    )
    hosted_thread = repo.create_thread(hosted.id, hosted_board.id, hosted_character.id, "a", "A")
    default_post = repo.create_post(default.id, default_thread.id, default_character.id, "Before.")
    hosted_post = repo.create_post(hosted.id, hosted_thread.id, hosted_character.id, "Before.")

    default_revision = repo.create_post_revision(
        default.id,
        default_post.id,
        default_membership.id,
        "Before.",
        "After.",
    )
    hosted_revision = repo.create_post_revision(
        hosted.id,
        hosted_post.id,
        hosted_membership.id,
        "Before.",
        "Elsewhere.",
    )

    assert [
        revision.new_body for revision in repo.list_post_revisions(default.id, default_post.id)
    ] == ["After."]
    assert [
        revision.new_body for revision in repo.list_post_revisions(hosted.id, hosted_post.id)
    ] == ["Elsewhere."]
    assert default_revision.community_id == default.id
    assert hosted_revision.community_id == hosted.id

    with pytest.raises(LookupError):
        repo.create_post_revision(
            default.id,
            hosted_post.id,
            default_membership.id,
            "Wrong.",
            "Wrong.",
        )
