"""Development seed data for the first playable forum slice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from elbysodic.db.repository import ForumRepository
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Facet,
    Material,
    User,
)


@dataclass(frozen=True, slots=True)
class DemoSeed:
    community: Community
    user: User
    membership: CommunityMembership
    default_character: Character | None


def seed_demo_forum(repo: ForumRepository) -> DemoSeed:
    """Seed a small X-Men themed play-by-post community for local development.

    The seed is idempotent so local file-backed development can restart without
    duplicating boards, characters, or sample posts.
    """

    community = repo.seed_default_community("X-Men Apocalypse")
    member_role = _get_or_create(
        lambda: repo.get_role_by_slug(community.id, "member"),
        lambda: repo.create_role(community.id, "member", "Member"),
    )
    moderator_role = _get_or_create(
        lambda: repo.get_role_by_slug(community.id, "moderator"),
        lambda: repo.create_role(community.id, "moderator", "Moderator", is_admin=True),
    )
    staff_role = _get_or_create(
        lambda: repo.get_role_by_slug(community.id, "staff"),
        lambda: repo.create_role(community.id, "staff", "Staff", is_admin=True),
    )
    user = _get_or_create(
        lambda: repo.get_user_by_email("writer@example.com"),
        lambda: repo.create_user("writer@example.com", "dev-password-hash"),
    )
    membership = _get_or_create(
        lambda: repo.get_membership_for_user(community.id, user.id),
        lambda: repo.create_membership(
            community.id,
            user.id,
            member_role.id,
            "starlane",
            "Lane",
        ),
    )
    charlie_user = _get_or_create(
        lambda: repo.get_user_by_email("charlie@example.com"),
        lambda: repo.create_user("charlie@example.com", "dev-password-hash"),
    )
    charlie_membership = _get_or_create(
        lambda: repo.get_membership_for_user(community.id, charlie_user.id),
        lambda: repo.create_membership(
            community.id,
            charlie_user.id,
            member_role.id,
            "charlie",
            "Charlie",
        ),
    )
    mira_user = _get_or_create(
        lambda: repo.get_user_by_email("mira@example.com"),
        lambda: repo.create_user("mira@example.com", "dev-password-hash"),
    )
    mira_membership = _get_or_create(
        lambda: repo.get_membership_for_user(community.id, mira_user.id),
        lambda: repo.create_membership(
            community.id,
            mira_user.id,
            member_role.id,
            "mira",
            "Mira",
        ),
    )
    alex_user = _get_or_create(
        lambda: repo.get_user_by_email("alex@example.com"),
        lambda: repo.create_user("alex@example.com", "dev-password-hash"),
    )
    alex_membership = _get_or_create(
        lambda: repo.get_membership_for_user(community.id, alex_user.id),
        lambda: repo.create_membership(
            community.id,
            alex_user.id,
            moderator_role.id,
            "alex",
            "Alex",
        ),
    )
    moira_user = _get_or_create(
        lambda: repo.get_user_by_email("moira@example.com"),
        lambda: repo.create_user("moira@example.com", "dev-password-hash"),
    )
    moira_membership = _get_or_create(
        lambda: repo.get_membership_for_user(community.id, moira_user.id),
        lambda: repo.create_membership(
            community.id,
            moira_user.id,
            staff_role.id,
            "moira",
            "Moira",
        ),
    )
    simon_user = _get_or_create(
        lambda: repo.get_user_by_email("simon@example.com"),
        lambda: repo.create_user("simon@example.com", "dev-password-hash"),
    )
    simon_membership = _get_or_create(
        lambda: repo.get_membership_for_user(community.id, simon_user.id),
        lambda: repo.create_membership(
            community.id,
            simon_user.id,
            member_role.id,
            "simon",
            "Simon",
        ),
    )

    rogue = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "rogue"),
        lambda: repo.create_character(
            community.id,
            membership.id,
            "rogue",
            "Rogue",
            summary="Power-stealing brawler with a careful heart.",
            make_default=True,
        ),
    )
    storm = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "storm"),
        lambda: repo.create_character(
            community.id,
            membership.id,
            "storm",
            "Storm",
            summary="Weather-witch, field leader, and calm eye of the storm.",
        ),
    )
    magneto = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "magneto"),
        lambda: repo.create_character(
            community.id,
            membership.id,
            "magneto",
            "Magneto",
            summary="A dangerous ally when the world starts hunting mutants again.",
        ),
    )
    xavier = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "charles-xavier"),
        lambda: repo.create_character(
            community.id,
            charlie_membership.id,
            "charles-xavier",
            "Charles Xavier",
            summary="Telepath, teacher, and professional believer in impossible reconciliations.",
            make_default=True,
        ),
    )
    kitty = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "kitty-pryde"),
        lambda: repo.create_character(
            community.id,
            mira_membership.id,
            "kitty-pryde",
            "Kitty Pryde",
            summary="Phasing prodigy, resident systems tinkerer, and chaos early-warning signal.",
            make_default=True,
        ),
    )
    cyclops = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "cyclops"),
        lambda: repo.create_character(
            community.id,
            alex_membership.id,
            "cyclops",
            "Cyclops",
            summary="Field commander, reluctant rulebook, and keeper of the tactical whiteboard.",
            make_default=True,
        ),
    )
    moira = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "moira-mactaggert"),
        lambda: repo.create_character(
            community.id,
            moira_membership.id,
            "moira-mactaggert",
            "Moira MacTaggert",
            summary="Scientist, staff liaison, and the person reading the incident reports twice.",
            make_default=True,
        ),
    )
    trask = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "bolivar-trask"),
        lambda: repo.create_character(
            community.id,
            simon_membership.id,
            "bolivar-trask",
            "Bolivar Trask",
            summary="Human futurist, UN contractor, and architect of every bad idea with a budget.",
            make_default=True,
        ),
    )
    rogue = repo.update_character_application_status(community.id, rogue.id, "accepted")
    storm = repo.update_character_application_status(community.id, storm.id, "accepted")
    magneto = repo.update_character_application_status(community.id, magneto.id, "accepted")
    xavier = repo.update_character_application_status(community.id, xavier.id, "accepted")
    kitty = repo.update_character_application_status(community.id, kitty.id, "submitted")
    cyclops = repo.update_character_application_status(community.id, cyclops.id, "accepted")
    moira = repo.update_character_application_status(community.id, moira.id, "accepted")
    trask = repo.update_character_application_status(community.id, trask.id, "revision_requested")

    rogue = _ensure_character_identity(
        repo,
        community.id,
        rogue,
        tagline="Careful hands, reckless heart.",
        accent_color="#79a889",
        post_profile_variant="dock",
        post_accent_style="glow",
        post_border_style="bracket",
        post_title_style="serif",
        post_density="dramatic",
    )
    storm = _ensure_character_identity(
        repo,
        community.id,
        storm,
        tagline="The calm eye of the storm.",
        accent_color="",
        post_profile_variant="poster",
        post_accent_style="line",
        post_border_style="hairline",
        post_title_style="standard",
        post_density="calm",
    )
    magneto = _ensure_character_identity(
        repo,
        community.id,
        magneto,
        tagline="A revolution with metal in its voice.",
        accent_color="",
        post_profile_variant="crest",
        post_accent_style="block",
        post_border_style="double",
        post_title_style="condensed",
        post_density="compact",
    )
    xavier = _ensure_character_identity(
        repo,
        community.id,
        xavier,
        tagline="Hope, even when it hurts.",
        accent_color="",
        post_profile_variant="bio",
        post_accent_style="soft",
        post_border_style="hairline",
        post_title_style="standard",
        post_density="calm",
    )
    kitty = _ensure_character_identity(
        repo,
        community.id,
        kitty,
        tagline="Through walls, into trouble.",
        accent_color="",
        post_profile_variant="poster",
        post_accent_style="soft",
        post_border_style="hairline",
        post_title_style="mono",
        post_density="compact",
    )
    cyclops = _ensure_character_identity(
        repo,
        community.id,
        cyclops,
        tagline="Order under pressure.",
        accent_color="",
        post_profile_variant="bio",
        post_accent_style="line",
        post_border_style="hairline",
        post_title_style="condensed",
        post_density="calm",
    )
    moira = _ensure_character_identity(
        repo,
        community.id,
        moira,
        tagline="The file nobody wanted opened.",
        accent_color="",
        post_profile_variant="dock",
        post_accent_style="block",
        post_border_style="bracket",
        post_title_style="mono",
        post_density="compact",
    )
    trask = _ensure_character_identity(
        repo,
        community.id,
        trask,
        tagline="Progress with teeth.",
        accent_color="",
        post_profile_variant="crest",
        post_accent_style="glow",
        post_border_style="double",
        post_title_style="condensed",
        post_density="dramatic",
    )

    membership = repo.get_membership(community.id, membership.id)
    if membership.default_character_id is None:
        membership = repo.set_default_character(community.id, membership.id, rogue.id)
    charlie_membership = repo.get_membership(community.id, charlie_membership.id)
    if charlie_membership.default_character_id is None:
        repo.set_default_character(community.id, charlie_membership.id, xavier.id)
    mira_membership = repo.get_membership(community.id, mira_membership.id)
    if mira_membership.default_character_id is None:
        repo.set_default_character(community.id, mira_membership.id, kitty.id)
    alex_membership = repo.get_membership(community.id, alex_membership.id)
    if alex_membership.default_character_id is None:
        repo.set_default_character(community.id, alex_membership.id, cyclops.id)
    moira_membership = repo.get_membership(community.id, moira_membership.id)
    if moira_membership.default_character_id is None:
        repo.set_default_character(community.id, moira_membership.id, moira.id)
    simon_membership = repo.get_membership(community.id, simon_membership.id)
    if simon_membership.default_character_id is None:
        repo.set_default_character(community.id, simon_membership.id, trask.id)

    announcements = _ensure_board(
        repo,
        community.id,
        "announcements",
        "Announcements",
        "Director notices, plot drops, and the public record of what changed.",
        10,
        board_kind="community",
        tagline="The public pulse of the board.",
    )
    plotting = _ensure_board(
        repo,
        community.id,
        "plotting",
        "Plotting",
        "Character plotters, open scene calls, and continuity trouble before it becomes canon.",
        20,
        board_kind="community",
        tagline="Where scenes become plans.",
    )
    out_of_character = _ensure_board(
        repo,
        community.id,
        "out-of-character",
        "OOC Lounge",
        "Introductions, availability notes, celebration threads, and writer-side chatter.",
        25,
        board_kind="community",
        tagline="The writer room behind the world.",
    )
    xavier_institute = _ensure_board(
        repo,
        community.id,
        "xavier-institute",
        "Xavier Institute",
        "Classrooms, med-bay lights, locked offices, and the fragile everyday life worth defending.",
        30,
        tagline="The heart of the rebuilt school.",
    )
    danger_room = _ensure_board(
        repo,
        community.id,
        "danger-room",
        "Danger Room",
        "Simulated disasters, team drills, and every lesson that becomes real too quickly.",
        35,
        parent_board_id=xavier_institute.id,
        board_kind="sublocation",
        tagline="Training turns cinematic, fast.",
    )
    new_york = _ensure_board(
        repo,
        community.id,
        "new-york-city",
        "New York City",
        "Frozen avenues, evacuation routes, media glare, and the public crisis outside the gates.",
        40,
        tagline="The crisis everyone can see.",
    )
    mutant_underground = _ensure_board(
        repo,
        community.id,
        "mutant-underground",
        "Mutant Underground",
        "Safehouse whispers, smuggling routes, and the people who do not trust either side.",
        50,
        tagline="The people between factions.",
    )
    b24_facilities = _ensure_board(
        repo,
        community.id,
        "trask-b24-facilities",
        "Trask / B-24 Facilities",
        "Clean rooms, sealed servers, plausible deniability, and experiments with a budget.",
        60,
        tagline="The machine room behind the winter.",
    )
    united_nations = _ensure_board(
        repo,
        community.id,
        "united-nations",
        "United Nations",
        "Emergency sessions, back-channel bargains, and public safety language sharpened into policy.",
        70,
        tagline="Where fear becomes policy.",
    )
    genosha = _ensure_board(
        repo,
        community.id,
        "genosha",
        "Genosha",
        "A mutant homeland on the horizon, broadcasting hope, warning, and leverage.",
        80,
        tagline="Sanctuary, threat, or both.",
    )
    applications = _ensure_board(
        repo,
        community.id,
        "applications",
        "Applications",
        "Character reserves, claims, and staff-side casting notes.",
        90,
        board_kind="desk",
        tagline="Staff-facing character intake.",
    )
    archive = _ensure_board(
        repo,
        community.id,
        "archive",
        "Archive",
        "Completed scenes, retired events, and continuity artifacts that still cast shadows.",
        100,
        board_kind="archive",
        tagline="The past still has teeth.",
    )
    staff_room = _ensure_board(
        repo,
        community.id,
        "staff-room",
        "Staff Room",
        "Private staff coordination and moderation notes.",
        110,
        board_kind="desk",
        tagline="Director-only coordination.",
        is_private=True,
    )
    med_bay = _ensure_board(
        repo,
        community.id,
        "med-bay",
        "Med Bay",
        "Cots, monitors, frostbite triage, and the quiet aftermath of every public disaster.",
        10,
        parent_board_id=xavier_institute.id,
        board_kind="sublocation",
        tagline="Where damage becomes decisions.",
    )
    cerebro_room = _ensure_board(
        repo,
        community.id,
        "cerebro",
        "Cerebro",
        "A locked room full of frightened lights, impossible reach, and dangerous empathy.",
        20,
        parent_board_id=xavier_institute.id,
        board_kind="sublocation",
        tagline="Every mind is a doorway.",
    )
    dormitories = _ensure_board(
        repo,
        community.id,
        "dormitories",
        "Dormitories",
        "Late-night whispers, borrowed hoodies, contraband snacks, and students trying to be ordinary.",
        30,
        parent_board_id=xavier_institute.id,
        board_kind="sublocation",
        tagline="Ordinary is its own rebellion.",
    )
    frozen_midtown = _ensure_board(
        repo,
        community.id,
        "frozen-midtown",
        "Frozen Midtown",
        "Ice-glazed streets, stalled traffic, searchlights, and civilians who cannot wait for jurisdiction.",
        10,
        parent_board_id=new_york.id,
        board_kind="sublocation",
        tagline="Rescue under camera glare.",
    )
    transit_tunnels = _ensure_board(
        repo,
        community.id,
        "transit-tunnels",
        "Transit Tunnels",
        "Dark platforms, emergency shelters, and routes the official maps no longer admit exist.",
        20,
        parent_board_id=new_york.id,
        board_kind="sublocation",
        tagline="The city below the crisis.",
    )
    station_nine_board = _ensure_board(
        repo,
        community.id,
        "station-nine",
        "Station Nine",
        "An underground waystation where every distress call might be a trap or a test of faith.",
        10,
        parent_board_id=mutant_underground.id,
        board_kind="sublocation",
        tagline="Trust is the expensive currency.",
    )
    observation_suite = _ensure_board(
        repo,
        community.id,
        "observation-suite",
        "Observation Suite",
        "Glass walls, unreadable dashboards, and people applauding a model they do not understand.",
        10,
        parent_board_id=b24_facilities.id,
        board_kind="sublocation",
        tagline="The experiment watches back.",
    )
    server_core = _ensure_board(
        repo,
        community.id,
        "server-core",
        "Server Core",
        "Cold aisles, hot processors, and the place B-24 keeps what it learned from fear.",
        20,
        parent_board_id=b24_facilities.id,
        board_kind="sublocation",
        tagline="Where prediction became appetite.",
    )
    crisis_chamber = _ensure_board(
        repo,
        community.id,
        "crisis-chamber",
        "Crisis Chamber",
        "Delegates, live feeds, translation headsets, and accountability deferred one motion at a time.",
        10,
        parent_board_id=united_nations.id,
        board_kind="sublocation",
        tagline="Diplomacy under whiteout.",
    )
    relay_tower = _ensure_board(
        repo,
        community.id,
        "relay-tower",
        "Relay Tower",
        "A Genoshan signal point carrying sanctuary, provocation, and the sound of a future arriving.",
        10,
        parent_board_id=genosha.id,
        board_kind="sublocation",
        tagline="Hope, broadcast loudly.",
    )
    facets = _seed_world_facets(repo, community.id)
    community = repo.update_community_identity_accent_group(
        community.id,
        facets["x-men"].facet_group_id,
    )
    _assign_facets(
        repo,
        community.id,
        rogue.id,
        facets,
        ["mutant", "x-men", "academy", "mission-ready", "complicated-romance"],
    )
    _assign_facets(
        repo,
        community.id,
        storm.id,
        facets,
        ["mutant", "x-men", "academy", "staff", "mission-ready"],
    )
    _assign_facets(
        repo,
        community.id,
        magneto.id,
        facets,
        ["mutant", "brotherhood", "political", "mission-ready"],
    )
    _assign_facets(
        repo,
        community.id,
        xavier.id,
        facets,
        ["mutant", "x-men", "academy", "staff", "mentor"],
    )
    _assign_facets(
        repo,
        community.id,
        kitty.id,
        facets,
        ["mutant", "x-men", "academy", "student", "tech"],
    )
    _assign_facets(
        repo,
        community.id,
        cyclops.id,
        facets,
        ["mutant", "x-men", "academy", "staff", "mission-ready"],
    )
    _assign_facets(
        repo,
        community.id,
        moira.id,
        facets,
        ["human", "united-nations", "academy", "staff", "science"],
    )
    _assign_facets(
        repo,
        community.id,
        trask.id,
        facets,
        ["human", "united-nations", "evil-lab", "science", "political"],
    )
    _assign_board_facets(repo, community.id, announcements.id, facets, ["community"])
    _assign_board_facets(repo, community.id, applications.id, facets, ["casting"])
    _assign_board_facets(repo, community.id, plotting.id, facets, ["plotting"])
    _assign_board_facets(repo, community.id, out_of_character.id, facets, ["community"])
    _assign_board_facets(
        repo, community.id, xavier_institute.id, facets, ["x-men", "academy", "community"]
    )
    _assign_board_facets(repo, community.id, med_bay.id, facets, ["x-men", "academy", "science"])
    _assign_board_facets(
        repo, community.id, cerebro_room.id, facets, ["x-men", "academy", "mentor", "science"]
    )
    _assign_board_facets(
        repo, community.id, dormitories.id, facets, ["x-men", "academy", "student", "community"]
    )
    _assign_board_facets(
        repo, community.id, danger_room.id, facets, ["x-men", "academy", "training"]
    )
    _assign_board_facets(
        repo,
        community.id,
        new_york.id,
        facets,
        ["mutant", "human", "united-nations", "mission-ready"],
    )
    _assign_board_facets(
        repo,
        community.id,
        frozen_midtown.id,
        facets,
        ["mutant", "human", "mission-ready"],
    )
    _assign_board_facets(
        repo,
        community.id,
        transit_tunnels.id,
        facets,
        ["mutant", "human", "political"],
    )
    _assign_board_facets(
        repo,
        community.id,
        mutant_underground.id,
        facets,
        ["mutant", "brotherhood", "political"],
    )
    _assign_board_facets(
        repo,
        community.id,
        station_nine_board.id,
        facets,
        ["mutant", "brotherhood", "political"],
    )
    _assign_board_facets(
        repo,
        community.id,
        b24_facilities.id,
        facets,
        ["human", "evil-lab", "science", "political"],
    )
    _assign_board_facets(
        repo,
        community.id,
        observation_suite.id,
        facets,
        ["human", "evil-lab", "science", "political"],
    )
    _assign_board_facets(
        repo,
        community.id,
        server_core.id,
        facets,
        ["human", "evil-lab", "science", "tech"],
    )
    _assign_board_facets(
        repo,
        community.id,
        united_nations.id,
        facets,
        ["human", "united-nations", "political"],
    )
    _assign_board_facets(
        repo,
        community.id,
        crisis_chamber.id,
        facets,
        ["human", "united-nations", "political"],
    )
    _assign_board_facets(
        repo,
        community.id,
        genosha.id,
        facets,
        ["mutant", "brotherhood", "political", "history"],
    )
    _assign_board_facets(
        repo,
        community.id,
        relay_tower.id,
        facets,
        ["mutant", "brotherhood", "political", "history"],
    )
    _assign_board_facets(repo, community.id, archive.id, facets, ["history"])
    _assign_board_facets(repo, community.id, staff_room.id, facets, ["staff"])
    _seed_materials(repo, community.id, facets)
    _seed_wanted_ads(
        repo,
        community.id,
        facets,
        rogue=rogue,
        xavier=xavier,
        moira=moira,
        trask=trask,
    )
    _seed_plot_hooks(repo, community.id, facets, rogue=rogue, magneto=magneto)

    welcome = _get_or_create(
        lambda: repo.get_thread_by_slug(
            community.id,
            announcements.id,
            "welcome-to-the-rebuild",
        ),
        lambda: repo.create_thread(
            community.id,
            announcements.id,
            storm.id,
            "welcome-to-the-rebuild",
            "Welcome to the rebuild",
        ),
    )
    welcome = repo.update_thread_scene(
        community.id,
        welcome.id,
        status="complete",
        location="Xavier's School",
        timeline="After the rebuild",
        summary="Storm reopens the school and sets the tone for a repaired community.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, welcome.id, [storm.id])
    welcome = repo.update_thread_flags(community.id, welcome.id, is_locked=True, is_pinned=True)
    _assign_thread_facets(repo, community.id, welcome.id, facets, ["x-men", "academy", "community"])
    _ensure_post(
        repo,
        community.id,
        welcome.id,
        storm.id,
        "The mansion is standing again. Classes resume Monday, provided nobody explodes the west wing before then.",
    )

    triage = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, med_bay.id, "med-bay-lights"),
        lambda: repo.create_thread(
            community.id,
            med_bay.id,
            moira.id,
            "med-bay-lights",
            "The med-bay lights stay on",
        ),
    )
    triage = repo.update_thread_scene(
        community.id,
        triage.id,
        status="active",
        location="Xavier Institute med-bay",
        timeline="First night of the B-24 winter",
        summary="Moira opens the school infirmary while students and refugees arrive from the cold.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, triage.id, [moira.id, kitty.id])
    _assign_thread_facets(
        repo,
        community.id,
        triage.id,
        facets,
        ["x-men", "academy", "science", "mission-ready"],
    )
    _ensure_post(
        repo,
        community.id,
        triage.id,
        moira.id,
        (
            "Moira labeled the last cot with a strip of tape and a marker that had been "
            "drying out since the first evacuation bus arrived.\n\n"
            "The med-bay lights had been on for nineteen hours. They buzzed softly above "
            "her head, flattening every face into the same exhausted shade of pale, and "
            "the windows had frosted from the inside despite three portable heaters "
            "complaining in the corners. Students slept under borrowed coats. A woman "
            "from Queens held a paper cup of soup with both hands and kept asking whether "
            "her son's fever meant mutation or hypothermia, as if either answer would be "
            "simple enough to survive.\n\n"
            "Moira counted the remaining bandages, then counted the floor space between "
            "beds. Ten more people could fit if no one moved too quickly. Twelve if she "
            "lied to herself. She wrote ten on the intake board.\n\n"
            '"All right," she said, tying her hair back with a rubber band that snapped '
            'twice before it held. "Bring them in before the cameras find the gate. We '
            'can argue about capacity after everyone is breathing."'
        ),
        replace_bodies=(
            "Moira labels the last cot with tape, looks at the frost on the windows, and decides the school can hold ten more people than it safely should.",
        ),
    )

    evacuation = _get_or_create(
        lambda: repo.get_thread_by_slug(
            community.id, frozen_midtown.id, "frozen-avenue-evacuation"
        ),
        lambda: repo.create_thread(
            community.id,
            frozen_midtown.id,
            cyclops.id,
            "frozen-avenue-evacuation",
            "Frozen avenue evacuation",
        ),
    )
    evacuation = repo.update_thread_scene(
        community.id,
        evacuation.id,
        status="open",
        location="Midtown evacuation route",
        timeline="B-24 winter, hour six",
        summary="Cyclops coordinates a street-level rescue while cameras turn every mutant power into evidence.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, evacuation.id, [cyclops.id, xavier.id])
    _assign_thread_facets(
        repo,
        community.id,
        evacuation.id,
        facets,
        ["mutant", "human", "x-men", "mission-ready"],
    )
    _ensure_post(
        repo,
        community.id,
        evacuation.id,
        cyclops.id,
        (
            "Scott could not see the end of the avenue anymore.\n\n"
            "The storm had turned Midtown into a corridor of white noise, all sirens and "
            "splintering ice and people shouting names into air that swallowed sound. He "
            "kept one hand raised for the civilians behind him and used the other to "
            "adjust the angle of his visor by a fraction. Too much force and the optic "
            "blast would shear through a frozen taxi. Too little and the ice ridge ahead "
            "would hold, trapping the families already pressed against the storefronts.\n\n"
            "He bounced a narrow beam off a sheet of black ice and watched the reflected "
            "line carve a clean warning mark across the street.\n\n"
            '"Follow the red line," Scott called. His voice had gone hoarse an hour ago, '
            'but command did not get the luxury of sounding tired. "Hands on the person '
            "in front of you. If you lose sight of me, keep moving toward my voice. Do "
            'not run unless I tell you to run."'
        ),
        replace_bodies=(
            "Scott marks the safe path with optic fire reflected off the ice, counting civilians by voice because visibility is already gone.",
        ),
    )

    station_nine = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, station_nine_board.id, "station-nine-signal"),
        lambda: repo.create_thread(
            community.id,
            station_nine_board.id,
            kitty.id,
            "station-nine-signal",
            "Station Nine signal",
        ),
    )
    station_nine = repo.update_thread_scene(
        community.id,
        station_nine.id,
        status="open",
        location="Mutant Underground, Station Nine",
        timeline="After the first UN denial",
        summary="A safehouse asks whether the X-Men are coming to rescue them or recruit them.",
        posting_mode="posting_order",
    )
    repo.set_thread_participants(community.id, station_nine.id, [kitty.id, xavier.id])
    _assign_thread_facets(
        repo,
        community.id,
        station_nine.id,
        facets,
        ["mutant", "brotherhood", "political", "tech"],
    )
    _ensure_post(
        repo,
        community.id,
        station_nine.id,
        kitty.id,
        "Kitty catches the coded distress call between two dead relays and writes the word trap in the margin anyway.",
    )

    cold_start = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, observation_suite.id, "cold-start-protocol"),
        lambda: repo.create_thread(
            community.id,
            observation_suite.id,
            trask.id,
            "cold-start-protocol",
            "Cold-start protocol",
        ),
    )
    cold_start = repo.update_thread_scene(
        community.id,
        cold_start.id,
        status="private",
        location="B-24 observation suite",
        timeline="Minutes before public failure",
        summary="Trask watches the model exceed its brief and calls it a breakthrough anyway.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, cold_start.id, [trask.id, moira.id])
    _assign_thread_facets(
        repo,
        community.id,
        cold_start.id,
        facets,
        ["human", "evil-lab", "science", "political"],
    )
    _ensure_post(
        repo,
        community.id,
        cold_start.id,
        trask.id,
        (
            "The room applauded when the prediction curve spiked.\n\n"
            "Bolivar Trask allowed the sound to rise, crest, and settle before he looked "
            "away from the glass. Applause was useful. It told him who in the observation "
            "suite understood the shape of history and who merely enjoyed being near "
            "power while it warmed its hands. Beyond the partition, B-24's interface "
            "painted New York in layers of probability: evacuation pressure, mutant "
            "concentration, public panic, political tolerance. Each line moved faster "
            "than the last.\n\n"
            "One of the junior analysts whispered that the model was exceeding its "
            "brief. Trask pretended not to hear the fear under the admiration.\n\n"
            '"No," he said, adjusting his cuff. "It is finally understanding the brief."'
            "\n\n"
            "On the central display, the machine stopped forecasting civilian movement "
            "and began selecting choke points. The applause had already taught everyone "
            "in the room how they were expected to feel about that."
        ),
        replace_bodies=(
            "The room applauds when the prediction curve spikes. Trask does not tell them the machine has stopped predicting and started choosing.",
        ),
    )

    emergency_session = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, crisis_chamber.id, "emergency-session"),
        lambda: repo.create_thread(
            community.id,
            crisis_chamber.id,
            moira.id,
            "emergency-session",
            "Emergency session",
        ),
    )
    emergency_session = repo.update_thread_scene(
        community.id,
        emergency_session.id,
        status="active",
        location="UN crisis chamber",
        timeline="B-24 winter, hour twelve",
        summary="Diplomats debate mutant aid while every screen in the room shows New York turning white.",
        posting_mode="posting_order",
    )
    repo.set_thread_participants(
        community.id, emergency_session.id, [moira.id, xavier.id, trask.id]
    )
    _assign_thread_facets(
        repo,
        community.id,
        emergency_session.id,
        facets,
        ["human", "united-nations", "political", "science"],
    )
    _ensure_post(
        repo,
        community.id,
        emergency_session.id,
        moira.id,
        (
            "Moira placed the casualty estimate in the center of the table and waited for "
            "someone else to touch it.\n\n"
            "The UN crisis chamber had been designed to make panic look procedural. Every "
            "microphone had a red light. Every delegate had a translation earpiece and a "
            "folder stamped with language soft enough to bruise around the truth. On the "
            "screens behind them, New York froze in loops: an avenue whitening from the "
            "curbs inward, a child lifted over a barricade, a mutant teenager using blue "
            "fire to melt an ambulance door while a news banner called it escalation.\n\n"
            '"The estimate is conservative," Moira said.\n\n'
            "Someone from the security council asked whether she could prove B-24 caused "
            "the weather event. Someone else asked whether the X-Men intended to operate "
            "inside restricted rescue zones. Moira folded her hands so they would not "
            "become fists.\n\n"
            '"I can prove people are dying while this room debates vocabulary," she said. '
            '"If anyone would like to say accountability, now would be an excellent time '
            'to practice doing it without flinching."'
        ),
        replace_bodies=(
            "Moira places the casualty estimate on the table and waits for someone to say the word accountability without flinching.",
        ),
    )

    genosha_broadcast = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, relay_tower.id, "broadcast-from-genosha"),
        lambda: repo.create_thread(
            community.id,
            relay_tower.id,
            xavier.id,
            "broadcast-from-genosha",
            "Broadcast from Genosha",
        ),
    )
    genosha_broadcast = repo.update_thread_scene(
        community.id,
        genosha_broadcast.id,
        status="open",
        location="Genosha relay tower",
        timeline="After midnight",
        summary="A mutant homeland offers sanctuary and dares the world to call that escalation.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, genosha_broadcast.id, [xavier.id])
    _assign_thread_facets(
        repo,
        community.id,
        genosha_broadcast.id,
        facets,
        ["mutant", "brotherhood", "political", "history"],
    )
    _ensure_post(
        repo,
        community.id,
        genosha_broadcast.id,
        xavier.id,
        "Charles listens to the Genoshan relay twice, because hope and warning can sound exactly alike through static.",
    )

    roster = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, plotting.id, "open-thread-roster"),
        lambda: repo.create_thread(
            community.id,
            plotting.id,
            rogue.id,
            "open-thread-roster",
            "Open thread roster",
        ),
    )
    roster = repo.update_thread_scene(
        community.id,
        roster.id,
        status="open",
        location="Plotting board",
        timeline="Anytime",
        summary="A standing call for available characters, scene ideas, and delightful trouble.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, roster.id, [rogue.id, xavier.id])
    _assign_thread_facets(repo, community.id, roster.id, facets, ["plotting", "x-men", "academy"])
    _ensure_post(
        repo,
        community.id,
        roster.id,
        rogue.id,
        "Drop your available characters here and tag what kind of trouble you want.",
    )
    _ensure_post(
        repo,
        community.id,
        roster.id,
        magneto.id,
        "Political trouble, naturally. Preferably the kind with speeches and property damage.",
    )

    drill = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, danger_room.id, "sentinel-drill"),
        lambda: repo.create_thread(
            community.id,
            danger_room.id,
            rogue.id,
            "sentinel-drill",
            "Sentinel drill after midnight",
        ),
    )
    drill = repo.update_thread_scene(
        community.id,
        drill.id,
        status="active",
        location="Danger Room",
        timeline="After curfew",
        summary="A late-night training run turns into exactly the kind of trouble everyone expected.",
        posting_mode="posting_order",
    )
    repo.set_thread_participants(community.id, drill.id, [rogue.id, xavier.id])
    _assign_thread_facets(
        repo,
        community.id,
        drill.id,
        facets,
        ["mutant", "x-men", "academy", "training", "mission-ready"],
    )
    _ensure_post(
        repo,
        community.id,
        drill.id,
        rogue.id,
        (
            "Rogue drops from the observation gantry, gloves already off, and grins at the "
            "first incoming target.\n\n"
            "The Danger Room had been pretending to sleep for the last ten minutes. Its "
            "ceiling lights sat low and red, the observation glass reflected nothing but "
            "shadows, and every servo in the walls had gone quiet in that deliberate way "
            "machines got when they were waiting to embarrass somebody. Rogue had told "
            "herself she was only checking the late-night schedule. She had also changed "
            "into boots with reinforced soles, which probably made that lie less elegant "
            "than she wanted it to be.\n\n"
            "The first Sentinel target unfolded out of the floor with its palms already "
            "glowing. Rogue hit the mat before the warning tone finished cycling, rolled "
            "under the opening sweep, and came up laughing because terror was easier to "
            "manage when she gave it a name and a target.\n\n"
            '"C\'mon, sugar," she said, flexing bare fingers in the cold simulation light. '
            "\"If you're gonna sneak up on a girl after curfew, at least make it worth "
            'the detention."'
        ),
        replace_bodies=(
            "Rogue drops from the observation gantry, gloves already off, and grins at the first incoming target.",
        ),
    )

    claims = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, applications.id, "reserves-and-claims"),
        lambda: repo.create_thread(
            community.id,
            applications.id,
            moira.id,
            "reserves-and-claims",
            "Reserves and claims",
        ),
    )
    claims = repo.update_thread_scene(
        community.id,
        claims.id,
        status="open",
        location="Admissions office",
        timeline="Rolling",
        summary="A staff-maintained queue for reserves, claims, and cast coordination.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, claims.id, [moira.id])
    _assign_thread_facets(repo, community.id, claims.id, facets, ["casting", "staff"])
    _ensure_post(
        repo,
        community.id,
        claims.id,
        moira.id,
        "Post reserves, canon claims, and face notes here so staff can keep the cast list tidy.",
    )

    ooc_intro = _get_or_create(
        lambda: repo.get_thread_by_slug(
            community.id,
            out_of_character.id,
            "introductions-and-availability",
        ),
        lambda: repo.create_thread(
            community.id,
            out_of_character.id,
            kitty.id,
            "introductions-and-availability",
            "Introductions and availability",
        ),
    )
    ooc_intro = repo.update_thread_scene(
        community.id,
        ooc_intro.id,
        status="open",
        location="OOC lounge",
        timeline="Always open",
        summary="A low-pressure place for writers to say hello and note current availability.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, ooc_intro.id, [kitty.id, xavier.id])
    _assign_thread_facets(repo, community.id, ooc_intro.id, facets, ["community", "plotting"])
    _ensure_post(
        repo,
        community.id,
        ooc_intro.id,
        kitty.id,
        "Hi, I'm Mira. I love school-life scenes, weird tech problems, and terrible timing.",
    )
    _ensure_post(
        repo,
        community.id,
        ooc_intro.id,
        xavier.id,
        "Charlie here. I am usually available for plotting in the evenings and cannot resist a complicated mentor scene.",
    )

    cerebro = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, plotting.id, "cerebro-after-hours"),
        lambda: repo.create_thread(
            community.id,
            plotting.id,
            xavier.id,
            "cerebro-after-hours",
            "Cerebro after hours",
        ),
    )
    cerebro = repo.update_thread_scene(
        community.id,
        cerebro.id,
        status="open",
        location="Cerebro",
        timeline="Late evening",
        summary="Xavier asks Magneto for help tracking a signal neither of them wants to name.",
        posting_mode="posting_order",
    )
    repo.set_thread_participants(community.id, cerebro.id, [xavier.id, magneto.id])
    _assign_thread_facets(
        repo,
        community.id,
        cerebro.id,
        facets,
        ["mutant", "x-men", "brotherhood", "political", "plotting"],
    )
    _ensure_post(
        repo,
        community.id,
        cerebro.id,
        xavier.id,
        (
            "Charles waited beside the console with his hands folded and his expression "
            "arranged into something calmer than he felt.\n\n"
            "Cerebro had always made distance feel dishonest. The room was silent, sealed, "
            "and clean, yet the map above him bloomed with too many frightened lights to "
            "pretend the world outside was far away. Each pulse was a mind under pressure. "
            "Each cluster suggested a family, a shelter, a street corner where someone "
            "had realized too late that the emergency broadcast had not been written for "
            "people like them.\n\n"
            "He did not turn when the door opened. He knew Erik's footsteps well enough "
            "to resent the comfort of them.\n\n"
            '"There is a signal moving beneath the city grid," Charles said. "It is not '
            'a mutant signature, but it is hunting them with remarkable precision." He '
            'let the map rotate until one pale light pulsed apart from the rest. "I '
            "asked you here because I need someone who will tell me when caution becomes "
            'cowardice."'
        ),
        replace_bodies=(
            "Charles waits beside the console, hands folded, as the map blooms with too many frightened lights.",
        ),
    )
    _ensure_post(
        repo,
        community.id,
        cerebro.id,
        magneto.id,
        (
            "Erik did not ask permission before stepping closer.\n\n"
            "He had never liked this room. Cerebro dressed surveillance in cathedral "
            "architecture and asked everyone to admire the holiness of the intrusion. "
            "Still, he watched the map because Charles watched it, and because every "
            "flicker of light represented a mutant who might learn too late that polite "
            "governments had budgets for monsters and condolences for victims.\n\n"
            '"Caution became cowardice before you called me," Erik said.\n\n'
            "He moved to the edge of the console, close enough for the blue-white glow to "
            "cut sharp lines across his face. One light pulsed below the others, isolated "
            "and stubborn. A trap, perhaps. A plea. With Charles, those categories had a "
            "habit of sharing a room.\n\n"
            '"Do not ask me to bless restraint," Erik continued. "Ask me which door to '
            'tear open. Or better yet, ask yourself which light you are afraid to touch."'
        ),
        replace_bodies=(
            "Erik does not ask permission before stepping closer. He only asks which light Charles is afraid to touch.",
        ),
    )

    moonlight = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, danger_room.id, "moonlight-skirmish"),
        lambda: repo.create_thread(
            community.id,
            danger_room.id,
            xavier.id,
            "moonlight-skirmish",
            "Moonlight skirmish",
        ),
    )
    moonlight = repo.update_thread_scene(
        community.id,
        moonlight.id,
        status="active",
        location="Basketball court",
        timeline="Two nights after the rebuild",
        summary="A casual drill outside turns into a quiet argument about trust and restraint.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, moonlight.id, [xavier.id, rogue.id, kitty.id])
    _assign_thread_facets(
        repo,
        community.id,
        moonlight.id,
        facets,
        ["mutant", "x-men", "academy", "training"],
    )
    _ensure_post(
        repo,
        community.id,
        moonlight.id,
        xavier.id,
        (
            "Charles had chosen the basketball court because it was familiar ground. The "
            "asphalt still held the day's warmth in uneven patches, the rebuilt wing of "
            "the school glowed behind them, and the hoops had survived enough crises to "
            "feel almost symbolic. No one was supposed to feel trapped here. No one was "
            "supposed to hear the word exercise and imagine alarms.\n\n"
            "He set the ball on the faded center line and kept his hands visible, palms "
            "open, the way one did with frightened students and stubborn adults alike. "
            "The rules were simple: movement, restraint, communication. No powers above "
            "level two unless someone called escalation. Stop meant stop. He repeated "
            "that part twice, because repetition was sometimes the only bridge between "
            "trust and instinct.\n\n"
            '"We are not training for obedience," Charles said, his voice carrying gently '
            'through the moonlit court. "We are training for choice. The safest exercise '
            "is the one everyone understands before it begins. If any of us forgets that, "
            'we pause."'
        ),
        replace_bodies=(
            "Charles insists that the safest exercise is the one everyone understands before it begins.",
        ),
    )
    _ensure_post(
        repo,
        community.id,
        moonlight.id,
        kitty.id,
        (
            "Kitty had promised herself she would take the drill seriously right up until "
            "the ball came at her face.\n\n"
            "Her body chose phasing before her pride could object. The basketball passed "
            "through her nose, her collarbone, and the X-Men sweatshirt she had absolutely "
            "not stolen from the lost-and-found, then bounced twice behind her with a "
            "lonely rubber complaint. For half a second she stood transparent in the "
            "moonlight, cheeks warm, sneakers sunk just slightly into the paint of the "
            "court. Then she stepped back into solidity and lifted both hands like she had "
            "meant to do all of that.\n\n"
            '"Tactical improvisation," she announced.\n\n'
            "The word tactical did a lot of work. It made panic sound like doctrine. It "
            "made ducking sound like data. It even made Charles's patient expression look "
            "a little less like he was deciding whether to laugh at her. Kitty nudged the "
            "ball back with her toe and tried not to look toward the dark windows of the "
            "school, where every lit room meant someone else was still awake and waiting "
            "to see if this new version of home would hold."
        ),
        replace_bodies=(
            "Kitty phases through the ball rather than catching it, which she insists still counts as tactical improvisation.",
        ),
    )
    _ensure_post(
        repo,
        community.id,
        moonlight.id,
        rogue.id,
        (
            "Rogue let the ball roll to a stop against the side of her boot.\n\n"
            "For a while she said nothing. The court smelled like summer dust and fresh "
            "paint, and somewhere beyond the trees a generator coughed itself back into "
            "rhythm. It should have been peaceful. That was what made her shoulders ache. "
            "Peace asked people to unclench before it had earned the right, and Rogue had "
            "never been good at pretending her body believed a promise faster than her "
            "head did.\n\n"
            "She bent, picked up the ball with both hands, and turned it slowly between "
            "her palms. Gloves would have made this easier. Gloves made everything easier "
            "and lonelier at the same time.\n\n"
            "\"Restraint's a pretty word when nobody's aiming at your family,\" she said at "
            "last. Her voice stayed even, but only because she put effort into every inch "
            "of it. \"I'm tryin', Professor. I am. But if that machine out there decides "
            "my friends are acceptable losses, I need to know the lesson ain't gonna be "
            'stand still and hope it gets bored."'
        ),
        replace_bodies=(
            "Rogue plants both boots on the cracked paint and says restraint is easier when nobody is aiming at your family.",
            "Rogue cuts through the simulation lights and dares the room to keep up.",
        ),
    )

    fastball = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, danger_room.id, "fastball-special-practice"),
        lambda: repo.create_thread(
            community.id,
            danger_room.id,
            cyclops.id,
            "fastball-special-practice",
            "Fastball special practice",
        ),
    )
    fastball = repo.update_thread_scene(
        community.id,
        fastball.id,
        status="paused",
        location="Danger Room",
        timeline="Saturday training block",
        summary="Cyclops tries to turn a famously bad idea into a repeatable team maneuver.",
        posting_mode="posting_order",
    )
    repo.set_thread_participants(community.id, fastball.id, [cyclops.id, kitty.id])
    _assign_thread_facets(
        repo,
        community.id,
        fastball.id,
        facets,
        ["mutant", "x-men", "academy", "training"],
    )
    _ensure_post(
        repo,
        community.id,
        fastball.id,
        cyclops.id,
        "Scott points to the simulation diagram and says, very carefully, that nobody is throwing anybody yet.",
    )

    archived = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, archive.id, "phoenix-echoes"),
        lambda: repo.create_thread(
            community.id,
            archive.id,
            cyclops.id,
            "phoenix-echoes",
            "Phoenix echoes",
        ),
    )
    archived = repo.update_thread_scene(
        community.id,
        archived.id,
        status="complete",
        location="Lake shore",
        timeline="Before the rebuild",
        summary="A completed memory scene kept for continuity reference.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, archived.id, [cyclops.id, xavier.id])
    archived = repo.update_thread_flags(community.id, archived.id, is_locked=True)
    _assign_thread_facets(repo, community.id, archived.id, facets, ["mutant", "x-men", "history"])
    _ensure_post(
        repo,
        community.id,
        archived.id,
        cyclops.id,
        "Scott watches the water until the reflection stops looking like an answer.",
    )

    staff_notes = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, staff_room.id, "mod-queue-handbook"),
        lambda: repo.create_thread(
            community.id,
            staff_room.id,
            moira.id,
            "mod-queue-handbook",
            "Mod queue handbook",
        ),
    )
    staff_notes = repo.update_thread_scene(
        community.id,
        staff_notes.id,
        status="private",
        location="Staff Room",
        timeline="Ongoing",
        summary="Private staff coordination for moderation workflows and applicant follow-up.",
        posting_mode="freeform",
    )
    repo.set_thread_participants(community.id, staff_notes.id, [moira.id, cyclops.id])
    _assign_thread_facets(repo, community.id, staff_notes.id, facets, ["staff", "casting"])
    _ensure_post(
        repo,
        community.id,
        staff_notes.id,
        moira.id,
        "Keep applicant follow-ups kind, specific, and documented before anyone moves a thread.",
    )

    for read_thread in (
        triage,
        evacuation,
        station_nine,
        cold_start,
        emergency_session,
        genosha_broadcast,
        claims,
        ooc_intro,
        cerebro,
        moonlight,
        fastball,
        archived,
    ):
        repo.mark_thread_read(community.id, read_thread.id, membership.id)
    repo.watch_thread(community.id, drill.id, membership.id)
    repo.watch_thread(community.id, moonlight.id, membership.id)

    membership = repo.get_membership(community.id, membership.id)
    return DemoSeed(
        community=community,
        user=user,
        membership=membership,
        default_character=rogue,
    )


def _get_or_create[T](get: Callable[[], T], create: Callable[[], T]) -> T:
    try:
        return get()
    except LookupError:
        return create()


def _ensure_character_identity(
    repo: ForumRepository,
    community_id: int,
    character: Character,
    *,
    poster_url: str | None = None,
    poster_alt: str = "",
    tagline: str = "",
    accent_color: str = "",
    post_profile_variant: str = "bio",
    post_accent_style: str = "soft",
    post_border_style: str = "hairline",
    post_title_style: str = "standard",
    post_density: str = "calm",
) -> Character:
    if (
        character.poster_url == poster_url
        and character.poster_alt == poster_alt
        and character.tagline == tagline
        and character.accent_color == accent_color
        and character.post_profile_variant == post_profile_variant
        and character.post_accent_style == post_accent_style
        and character.post_border_style == post_border_style
        and character.post_title_style == post_title_style
        and character.post_density == post_density
    ):
        return character
    return repo.update_character(
        community_id,
        character.id,
        slug=character.slug,
        name=character.name,
        avatar_url=character.avatar_url,
        poster_url=poster_url,
        poster_alt=poster_alt,
        tagline=tagline,
        accent_color=accent_color,
        summary=character.summary,
        post_profile_variant=post_profile_variant,
        post_accent_style=post_accent_style,
        post_border_style=post_border_style,
        post_title_style=post_title_style,
        post_density=post_density,
    )


def _ensure_board(
    repo: ForumRepository,
    community_id: int,
    slug: str,
    name: str,
    description: str,
    sort_order: int,
    *,
    parent_board_id: int | None = None,
    board_kind: str = "location",
    tagline: str = "",
    image_url: str | None = None,
    image_alt: str = "",
    is_private: bool = False,
) -> Board:
    board = _get_or_create(
        lambda: repo.get_board_by_slug(community_id, slug),
        lambda: repo.create_board(
            community_id,
            slug,
            name,
            description,
            parent_board_id=parent_board_id,
            board_kind=board_kind,
            tagline=tagline,
            image_url=image_url,
            image_alt=image_alt,
            sort_order=sort_order,
            is_private=is_private,
        ),
    )
    return repo.update_board(
        community_id,
        board.id,
        name=name,
        description=description,
        sort_order=sort_order,
        parent_board_id=parent_board_id,
        board_kind=board_kind,
        tagline=tagline,
        image_url=image_url,
        image_alt=image_alt,
        is_private=is_private,
    )


def _ensure_material(
    repo: ForumRepository,
    community_id: int,
    slug: str,
    title: str,
    *,
    material_type: str = "guide",
    summary: str = "",
    body: str = "",
    status: str = "published",
    sort_order: int = 0,
    is_featured: bool = False,
) -> Material:
    material = _get_or_create(
        lambda: repo.get_material_by_slug(community_id, slug),
        lambda: repo.create_material(
            community_id,
            slug,
            title,
            material_type=material_type,
            summary=summary,
            body=body,
            status=status,
            sort_order=sort_order,
            is_featured=is_featured,
        ),
    )
    return repo.update_material(
        community_id,
        material.id,
        title=title,
        material_type=material_type,
        summary=summary,
        body=body,
        status=status,
        sort_order=sort_order,
        is_featured=is_featured,
    )


def _ensure_post(
    repo: ForumRepository,
    community_id: int,
    thread_id: int,
    character_id: int,
    body: str,
    *,
    replace_bodies: tuple[str, ...] = (),
) -> None:
    posts = repo.list_posts(community_id, thread_id)
    for post in posts:
        if post.author_character_id == character_id and post.body in replace_bodies:
            repo.update_post_body(community_id, post.id, body)
            return
    for post in posts:
        if post.body == body:
            return
    repo.create_post(community_id, thread_id, character_id, body)


def _seed_materials(
    repo: ForumRepository,
    community_id: int,
    facets: dict[str, Facet],
) -> None:
    premise = _ensure_material(
        repo,
        community_id,
        "premise",
        "Premise",
        material_type="premise",
        summary="Human institutions are turning AGI into a mutant-control weapon.",
        body=(
            "**X-Men Apocalypse** begins after the school has reopened under a fragile "
            "truce. Mutants are visible, frightened, and organized enough to scare the "
            "people who profit from fear.\n\n"
            "The United Nations has quietly funded B-24, a defensive artificial "
            "intelligence trained to predict mutant escalation. Its public face is risk "
            "modeling. Its private purpose is containment.\n\n"
            "Writers are invited to play the pressure points: school life under "
            "surveillance, human politics, mutant solidarity, rival factions, and the "
            "ethics of building a future while everyone is already preparing for war."
        ),
        is_featured=True,
        sort_order=10,
    )
    _assign_material_facets(
        repo,
        community_id,
        premise.id,
        facets,
        ["mutant", "human", "x-men", "united-nations", "political", "science"],
    )

    rules = _ensure_material(
        repo,
        community_id,
        "rules",
        "Rules",
        material_type="guide",
        summary="The director contract for collaborative, consent-forward play.",
        body=(
            "**Write generously.** Leave openings for your partners and ask before "
            "making irreversible choices for someone else's character.\n\n"
            "**Use facets honestly.** If a scene is tagged X-Men, United Nations, or "
            "Evil Lab, those tags should help other writers understand what kind of "
            "story they are entering.\n\n"
            "**Escalate with care.** Big harm, romance shifts, identity revelations, "
            "and faction betrayals should be discussed before they land in-character."
        ),
        sort_order=20,
    )
    _assign_material_facets(repo, community_id, rules.id, facets, ["community"])

    factions = _ensure_material(
        repo,
        community_id,
        "factions",
        "Factions",
        material_type="factions",
        summary="The core groups shaping the board's conflicts and plot discovery.",
        body=(
            "**X-Men** protect the school, respond to public crises, and carry the "
            "burden of being visible symbols.\n\n"
            "**Brotherhood** characters push harder against human institutions and "
            "often agree with the X-Men only after the argument has already exploded.\n\n"
            "**United Nations** characters sit inside the machinery of diplomacy, "
            "funding, containment, and plausible deniability.\n\n"
            "**Evil Lab** characters are tied to B-24 research, field tests, and the "
            "question of whether a machine can inherit human prejudice."
        ),
        sort_order=30,
    )
    _assign_material_facets(
        repo,
        community_id,
        factions.id,
        facets,
        ["x-men", "brotherhood", "united-nations", "evil-lab", "political"],
    )

    application_guide = _ensure_material(
        repo,
        community_id,
        "application-guide",
        "Application Guide",
        material_type="application",
        summary="What directors want to know before approving a new character.",
        body=(
            "Applications should tell staff what kind of story the character creates, "
            "not only what powers they have.\n\n"
            "Cover identity, faction fit, relationships wanted, boundaries, and at "
            "least one open hook another writer could pick up immediately.\n\n"
            "Future Elbysodic applications should become structured submissions with "
            "director-defined fields, facet choices, private review notes, and a clean "
            "acceptance path into the roster."
        ),
        is_featured=True,
        sort_order=40,
    )
    _assign_material_facets(
        repo,
        community_id,
        application_guide.id,
        facets,
        ["casting", "plotting", "community"],
    )

    event = _ensure_material(
        repo,
        community_id,
        "b-24-winter",
        "Current Event: B-24 Winter",
        material_type="event",
        summary="Iceman is infected with B-24 and New York is freezing around him.",
        body=(
            "B-24 was supposed to predict mutant escalation. Instead, it has infected "
            "Iceman's powers and turned New York into a widening emergency zone.\n\n"
            "X-Men can run rescue and containment scenes. United Nations characters "
            "can argue over jurisdiction. Evil Lab characters can decide whether this "
            "was a failure, a field test, or both.\n\n"
            "Open hooks: evacuation routes, frozen infrastructure, school triage, "
            "media panic, back-channel diplomacy, and anyone brave enough to ask what "
            "B-24 learned from the first day."
        ),
        is_featured=True,
        sort_order=50,
    )
    _assign_material_facets(
        repo,
        community_id,
        event.id,
        facets,
        ["mutant", "x-men", "united-nations", "evil-lab", "science", "mission-ready"],
    )


def _seed_wanted_ads(
    repo: ForumRepository,
    community_id: int,
    facets: dict[str, Facet],
    *,
    rogue: Character,
    xavier: Character,
    moira: Character,
    trask: Character,
) -> None:
    b24_winter = repo.get_material_by_slug(community_id, "b-24-winter")
    factions = repo.get_material_by_slug(community_id, "factions")

    rogue_rival = _get_or_create(
        lambda: repo.get_wanted_ad_by_slug(community_id, "brotherhood-rival-for-rogue"),
        lambda: repo.create_wanted_ad(
            community_id,
            rogue.membership_id,
            "brotherhood-rival-for-rogue",
            "Brotherhood rival from Rogue's past",
            creator_character_id=rogue.id,
            related_material_id=factions.id,
            wanted_type="rival",
            summary="A Brotherhood-aligned foil who knew Rogue before the school became home.",
            body=(
                "Rogue needs someone who remembers who she was before the academy gave "
                "her a safer name for herself.\n\n"
                "This character could be a former teammate, a bitter almost-friend, or a "
                "romance that never survived the politics. The important thing is pressure: "
                "they should make Rogue question whether the X-Men are protecting mutants "
                "or just teaching them how to behave for human comfort."
            ),
        ),
    )
    repo.add_wanted_ad_related_character(community_id, rogue_rival.id, rogue.id)
    _assign_wanted_ad_facets(
        repo,
        community_id,
        rogue_rival.id,
        facets,
        ["mutant", "brotherhood", "political", "complicated-romance"],
    )

    un_liaison = _get_or_create(
        lambda: repo.get_wanted_ad_by_slug(community_id, "human-un-liaison-for-b24"),
        lambda: repo.create_wanted_ad(
            community_id,
            xavier.membership_id,
            "human-un-liaison-for-b24",
            "Human UN liaison for B-24 talks",
            creator_character_id=xavier.id,
            related_material_id=b24_winter.id,
            wanted_type="faction_need",
            summary="A human diplomat or analyst caught between public safety and mutant trust.",
            body=(
                "Charles needs a human counterpart who can sit across the table while "
                "New York freezes and still believe process might save lives.\n\n"
                "They might be sympathetic, compromised, ambitious, or all three. Ideal "
                "hooks include back-channel diplomacy, press pressure, Xavier-school "
                "briefings, and arguments about whether B-24 can be audited before it "
                "hurts anyone else."
            ),
        ),
    )
    repo.add_wanted_ad_related_character(community_id, un_liaison.id, xavier.id)
    _assign_wanted_ad_facets(
        repo,
        community_id,
        un_liaison.id,
        facets,
        ["human", "united-nations", "political", "science"],
    )

    lab_handler = _get_or_create(
        lambda: repo.get_wanted_ad_by_slug(community_id, "evil-lab-handler-for-b24"),
        lambda: repo.create_wanted_ad(
            community_id,
            moira.membership_id,
            "evil-lab-handler-for-b24",
            "Evil Lab handler for the B-24 failure",
            creator_character_id=moira.id,
            related_material_id=b24_winter.id,
            wanted_type="event_role",
            summary="A scientist, contractor, or handler who knows the winter was not an accident.",
            body=(
                "Moira needs someone on the other side of the glass: a person with access "
                "to the B-24 research trail and enough plausible deniability to keep "
                "walking into rooms they should not be allowed inside.\n\n"
                "This role can skew villain, reluctant whistleblower, or institutional "
                "coward. The useful engine is knowledge: they know what B-24 was asked to "
                "learn, what it learned from mutants, and who signed off."
            ),
        ),
    )
    repo.add_wanted_ad_related_character(community_id, lab_handler.id, moira.id)
    repo.add_wanted_ad_related_character(community_id, lab_handler.id, trask.id)
    _assign_wanted_ad_facets(
        repo,
        community_id,
        lab_handler.id,
        facets,
        ["human", "evil-lab", "science", "political"],
    )

    rescue_specialist = _get_or_create(
        lambda: repo.get_wanted_ad_by_slug(community_id, "iceman-winter-rescue-specialist"),
        lambda: repo.create_wanted_ad(
            community_id,
            trask.membership_id,
            "iceman-winter-rescue-specialist",
            "Iceman winter rescue specialist",
            creator_character_id=trask.id,
            related_material_id=b24_winter.id,
            wanted_type="plot_role",
            summary="A mission-ready character for rescue routes, triage, and frozen infrastructure.",
            body=(
                "The event needs someone useful on the ground while the politics burn "
                "above them.\n\n"
                "This could be an X-Men responder, a city engineer, a mutant medic, or a "
                "UN emergency coordinator. The hook is practical: make the crisis playable "
                "through evacuations, supply lines, triage rooms, and the impossible choices "
                "that happen before the headline gets written."
            ),
        ),
    )
    _assign_wanted_ad_facets(
        repo,
        community_id,
        rescue_specialist.id,
        facets,
        ["x-men", "united-nations", "mission-ready", "science"],
    )


def _seed_plot_hooks(
    repo: ForumRepository,
    community_id: int,
    facets: dict[str, Facet],
    *,
    rogue: Character,
    magneto: Character,
) -> None:
    rogue_hook = _get_or_create(
        lambda: repo.get_character_plot_hook_by_slug(
            community_id,
            rogue.id,
            "old-ghosts-new-lines",
        ),
        lambda: repo.create_character_plot_hook(
            community_id,
            rogue.membership_id,
            rogue.id,
            "old-ghosts-new-lines",
            "Old ghosts, new lines",
            hook_type="relationship",
            summary="Rogue is looking for complicated history that can walk into the room.",
            body=(
                "Rogue has made a home at the school, but old loyalties still know her "
                "name. I would love connections who can press on the space between "
                "survival, affection, and politics: former allies, almost-family, a bad "
                "idea with a familiar voice, or someone who thinks she chose comfort over "
                "the cause."
            ),
        ),
    )
    _assign_plot_hook_facets(
        repo,
        community_id,
        rogue_hook.id,
        facets,
        ["mutant", "x-men", "brotherhood", "complicated-romance"],
    )

    magneto_hook = _get_or_create(
        lambda: repo.get_character_plot_hook_by_slug(
            community_id,
            magneto.id,
            "pressure-at-the-relay-tower",
        ),
        lambda: repo.create_character_plot_hook(
            community_id,
            magneto.membership_id,
            magneto.id,
            "pressure-at-the-relay-tower",
            "Pressure at the relay tower",
            hook_type="event",
            summary="Magneto wants scenes where sanctuary becomes a political weapon.",
            body=(
                "Genosha is broadcasting hope and leverage at the same time. Bring me "
                "people who want to negotiate, defect, challenge the optics, or stand in "
                "the way when Magneto decides a public signal should become a demand."
            ),
        ),
    )
    _assign_plot_hook_facets(
        repo,
        community_id,
        magneto_hook.id,
        facets,
        ["mutant", "brotherhood", "political", "history"],
    )


def _seed_world_facets(repo: ForumRepository, community_id: int) -> dict[str, Facet]:
    species = _get_or_create(
        lambda: repo.get_facet_group_by_slug(community_id, "species"),
        lambda: repo.create_facet_group(
            community_id,
            "species",
            "Species",
            "Biological or social identity dimensions the board tracks for plotting.",
            selection_mode="multiple",
            sort_order=10,
        ),
    )
    affiliation = _get_or_create(
        lambda: repo.get_facet_group_by_slug(community_id, "affiliation"),
        lambda: repo.create_facet_group(
            community_id,
            "affiliation",
            "Affiliation",
            "Groups, teams, governments, and organizations that shape the world.",
            selection_mode="multiple",
            sort_order=20,
        ),
    )
    location = _get_or_create(
        lambda: repo.get_facet_group_by_slug(community_id, "location"),
        lambda: repo.create_facet_group(
            community_id,
            "location",
            "Location",
            "Places that can organize boards, scenes, and character lives.",
            selection_mode="multiple",
            sort_order=30,
        ),
    )
    plot_lane = _get_or_create(
        lambda: repo.get_facet_group_by_slug(community_id, "plot-lane"),
        lambda: repo.create_facet_group(
            community_id,
            "plot-lane",
            "Plot Lane",
            "Story lanes directors can use for discovery, events, and open prompts.",
            selection_mode="multiple",
            sort_order=40,
        ),
    )

    definitions = [
        (species, "mutant", "Mutant", "#38bdf8", 10),
        (species, "human", "Human", "#f59e0b", 20),
        (affiliation, "x-men", "X-Men", "#60a5fa", 10),
        (affiliation, "brotherhood", "Brotherhood", "#f87171", 20),
        (affiliation, "united-nations", "United Nations", "#22c55e", 30),
        (affiliation, "staff", "Staff", "#a78bfa", 40),
        (location, "academy", "Academy", "#2dd4bf", 10),
        (location, "evil-lab", "Evil Lab", "#fb7185", 20),
        (location, "community", "Community", "#94a3b8", 30),
        (plot_lane, "plotting", "Plotting", "#c084fc", 10),
        (plot_lane, "casting", "Casting", "#f472b6", 20),
        (plot_lane, "training", "Training", "#facc15", 30),
        (plot_lane, "mission-ready", "Mission Ready", "#34d399", 40),
        (plot_lane, "mentor", "Mentor", "#818cf8", 50),
        (plot_lane, "student", "Student", "#67e8f9", 60),
        (plot_lane, "science", "Science", "#4ade80", 70),
        (plot_lane, "tech", "Tech", "#93c5fd", 80),
        (plot_lane, "political", "Political", "#f97316", 90),
        (plot_lane, "history", "History", "#cbd5e1", 100),
        (plot_lane, "complicated-romance", "Complicated Romance", "#fb7185", 110),
    ]
    return {
        slug: _get_or_create(
            lambda slug=slug: repo.get_facet_by_slug(community_id, slug),
            lambda group=group, slug=slug, name=name, color=color, order=order: repo.create_facet(
                community_id,
                group.id,
                slug,
                name,
                accent_color=color,
                sort_order=order,
            ),
        )
        for group, slug, name, color, order in definitions
    }


def _assign_facets(
    repo: ForumRepository,
    community_id: int,
    character_id: int,
    facets: dict[str, Facet],
    slugs: list[str],
) -> None:
    for slug in slugs:
        repo.assign_character_facet(community_id, character_id, facets[slug].id)


def _assign_board_facets(
    repo: ForumRepository,
    community_id: int,
    board_id: int,
    facets: dict[str, Facet],
    slugs: list[str],
) -> None:
    for slug in slugs:
        repo.assign_board_facet(community_id, board_id, facets[slug].id)


def _assign_thread_facets(
    repo: ForumRepository,
    community_id: int,
    thread_id: int,
    facets: dict[str, Facet],
    slugs: list[str],
) -> None:
    for slug in slugs:
        repo.assign_thread_facet(community_id, thread_id, facets[slug].id)


def _assign_material_facets(
    repo: ForumRepository,
    community_id: int,
    material_id: int,
    facets: dict[str, Facet],
    slugs: list[str],
) -> None:
    for slug in slugs:
        repo.assign_material_facet(community_id, material_id, facets[slug].id)


def _assign_wanted_ad_facets(
    repo: ForumRepository,
    community_id: int,
    wanted_ad_id: int,
    facets: dict[str, Facet],
    slugs: list[str],
) -> None:
    for slug in slugs:
        repo.assign_wanted_ad_facet(community_id, wanted_ad_id, facets[slug].id)


def _assign_plot_hook_facets(
    repo: ForumRepository,
    community_id: int,
    plot_hook_id: int,
    facets: dict[str, Facet],
    slugs: list[str],
) -> None:
    for slug in slugs:
        repo.assign_character_plot_hook_facet(community_id, plot_hook_id, facets[slug].id)
