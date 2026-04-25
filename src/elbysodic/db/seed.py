"""Development seed data for the first playable forum slice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from elbysodic.db.repository import ForumRepository
from elbysodic.domain.models import Character, Community, CommunityMembership, User


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
