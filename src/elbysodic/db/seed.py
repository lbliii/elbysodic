"""Development seed data for the first playable forum slice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from elbysodic.db.repository import ForumRepository
from elbysodic.domain.models import Character, Community, CommunityMembership, Facet, User


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

    announcements = _get_or_create(
        lambda: repo.get_board_by_slug(community.id, "announcements"),
        lambda: repo.create_board(
            community.id,
            "announcements",
            "Announcements",
            "Site news, plot drops, and staff notes.",
            sort_order=10,
        ),
    )
    applications = _get_or_create(
        lambda: repo.get_board_by_slug(community.id, "applications"),
        lambda: repo.create_board(
            community.id,
            "applications",
            "Applications",
            "Character reserves, claims, and staff-side casting notes.",
            sort_order=15,
        ),
    )
    plotting = _get_or_create(
        lambda: repo.get_board_by_slug(community.id, "plotting"),
        lambda: repo.create_board(
            community.id,
            "plotting",
            "Plotting",
            "Find threads, plan arcs, and make delicious continuity trouble.",
            sort_order=20,
        ),
    )
    out_of_character = _get_or_create(
        lambda: repo.get_board_by_slug(community.id, "out-of-character"),
        lambda: repo.create_board(
            community.id,
            "out-of-character",
            "Out of Character",
            "Introductions, availability notes, and community chatter.",
            sort_order=25,
        ),
    )
    danger_room = _get_or_create(
        lambda: repo.get_board_by_slug(community.id, "danger-room"),
        lambda: repo.create_board(
            community.id,
            "danger-room",
            "Danger Room",
            "In-character training sequences, sparring, and tactical disasters.",
            sort_order=30,
        ),
    )
    archive = _get_or_create(
        lambda: repo.get_board_by_slug(community.id, "archive"),
        lambda: repo.create_board(
            community.id,
            "archive",
            "Archive",
            "Completed scenes and old event material.",
            sort_order=35,
        ),
    )
    staff_room = _get_or_create(
        lambda: repo.get_board_by_slug(community.id, "staff-room"),
        lambda: repo.create_board(
            community.id,
            "staff-room",
            "Staff Room",
            "Private staff coordination and moderation notes.",
            sort_order=40,
            is_private=True,
        ),
    )
    facets = _seed_world_facets(repo, community.id)
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
        repo, community.id, danger_room.id, facets, ["x-men", "academy", "training"]
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
        "Rogue drops from the observation gantry, gloves already off, and grins at the first incoming target.",
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
        "Charles waits beside the console, hands folded, as the map blooms with too many frightened lights.",
    )
    _ensure_post(
        repo,
        community.id,
        cerebro.id,
        magneto.id,
        "Erik does not ask permission before stepping closer. He only asks which light Charles is afraid to touch.",
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
        "Charles insists that the safest exercise is the one everyone understands before it begins.",
    )
    _ensure_post(
        repo,
        community.id,
        moonlight.id,
        kitty.id,
        "Kitty phases through the ball rather than catching it, which she insists still counts as tactical improvisation.",
    )
    _ensure_post(
        repo,
        community.id,
        moonlight.id,
        rogue.id,
        "Rogue plants both boots on the cracked paint and says restraint is easier when nobody is aiming at your family.",
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


def _ensure_post(
    repo: ForumRepository,
    community_id: int,
    thread_id: int,
    character_id: int,
    body: str,
) -> None:
    if any(post.body == body for post in repo.list_posts(community_id, thread_id)):
        return
    repo.create_post(community_id, thread_id, character_id, body)


def _seed_materials(
    repo: ForumRepository,
    community_id: int,
    facets: dict[str, Facet],
) -> None:
    premise = _get_or_create(
        lambda: repo.get_material_by_slug(community_id, "premise"),
        lambda: repo.create_material(
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
        ),
    )
    _assign_material_facets(
        repo,
        community_id,
        premise.id,
        facets,
        ["mutant", "human", "x-men", "united-nations", "political", "science"],
    )

    rules = _get_or_create(
        lambda: repo.get_material_by_slug(community_id, "rules"),
        lambda: repo.create_material(
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
        ),
    )
    _assign_material_facets(repo, community_id, rules.id, facets, ["community"])

    factions = _get_or_create(
        lambda: repo.get_material_by_slug(community_id, "factions"),
        lambda: repo.create_material(
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
        ),
    )
    _assign_material_facets(
        repo,
        community_id,
        factions.id,
        facets,
        ["x-men", "brotherhood", "united-nations", "evil-lab", "political"],
    )

    application_guide = _get_or_create(
        lambda: repo.get_material_by_slug(community_id, "application-guide"),
        lambda: repo.create_material(
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
        ),
    )
    _assign_material_facets(
        repo,
        community_id,
        application_guide.id,
        facets,
        ["casting", "plotting", "community"],
    )

    event = _get_or_create(
        lambda: repo.get_material_by_slug(community_id, "b-24-winter"),
        lambda: repo.create_material(
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
        ),
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
