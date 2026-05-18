"""Development seed data for the first playable forum slice."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from elbysodic.blueprints import (
    BlueprintBoard,
    BlueprintCharacter,
    BlueprintMaterial,
    BlueprintTheme,
    BlueprintThemeMode,
    BlueprintTypography,
    BlueprintWanted,
    ProgramBlueprint,
    blueprint_theme_tokens,
    ensure_valid_program_blueprints,
)
from elbysodic.db.repositories.discovery import DiscoveryTagInput
from elbysodic.db.repository import ForumRepository
from elbysodic.domain.models import (
    Board,
    Character,
    Community,
    CommunityMembership,
    Facet,
    Material,
    Role,
    User,
)


@dataclass(frozen=True, slots=True)
class DemoSeed:
    community: Community
    user: User
    membership: CommunityMembership
    default_character: Character | None


@dataclass(frozen=True, slots=True)
class InteractionOptionSeed:
    slug: str
    label: str
    description: str
    result_key: str = ""


@dataclass(frozen=True, slots=True)
class InteractionQuestionSeed:
    prompt: str
    help_text: str
    options: tuple[InteractionOptionSeed, ...]


@dataclass(frozen=True, slots=True)
class InteractionSeed:
    slug: str
    title: str
    interaction_type: str
    placement: str
    summary: str
    body: str
    result_mode: str
    questions: tuple[InteractionQuestionSeed, ...]


@dataclass(frozen=True, slots=True)
class ClaimTypeSeed:
    slug: str
    name: str
    claim_kind: str
    description: str
    is_required: bool = False
    is_exclusive: bool = False


@dataclass(frozen=True, slots=True)
class ApplicationFieldSeed:
    field_key: str
    label: str
    field_type: str
    help_text: str
    placeholder: str = ""
    options: tuple[str, ...] = ()
    maps_to_claim_type_slug: str | None = None
    is_required: bool = False


@dataclass(frozen=True, slots=True)
class CommunityMediaSeed:
    mark_url: str
    mark_alt: str
    hero_url: str
    hero_alt: str
    hero_treatment: str = "split"
    hero_focal_point: str = "center"
    hero_overlay: str = "medium"
    hero_height: str = "standard"


@dataclass(frozen=True, slots=True)
class BoardMediaSeed:
    image_url: str
    image_alt: str
    image_treatment: str = "poster"
    image_focal_point: str = "center"
    image_overlay: str = "medium"


@dataclass(frozen=True, slots=True)
class DiscoveryTagSeed:
    tag_type: str
    tag_key: str
    label: str
    search_text: str = ""
    sort_order: int = 0


@dataclass(frozen=True, slots=True)
class DiscoveryProfileSeed:
    premise_archetype: str
    play_engine: str
    lore_aperture: str
    access_model: str
    application_model: str
    age_rating: str
    content_rating: str
    activity_pace: str
    activity_expectation: str
    forum_adjunct: str
    roster_posture: str
    catalog_pitch: str
    onboarding_pitch: str
    tags: tuple[DiscoveryTagSeed, ...]
    staff_pick_label: str = ""
    featured_event_material_slug: str | None = None


@dataclass(frozen=True, slots=True)
class ClaimSeed:
    claim_type_slug: str
    character_slug: str
    value: str
    label: str
    status: str = "claimed"


@dataclass(frozen=True, slots=True)
class SeedPersona:
    key: str
    label: str
    email: str
    community_slug: str
    username: str
    character_slug: str
    purpose: str
    default_path: str = "/"


@dataclass(frozen=True, slots=True)
class SeedPersonaContext:
    persona: SeedPersona
    user: User
    community: Community
    membership: CommunityMembership
    role: Role
    character: Character | None


@dataclass(frozen=True, slots=True)
class OriginalPremiseWriterSeed:
    email: str
    username: str
    display_name: str


SEED_MEDIA_BASE = "/elbysodic-static/seed-media"
LOCATION_MEDIA_BASE = f"{SEED_MEDIA_BASE}/locations"
X_MEN_MEDIA = CommunityMediaSeed(
    mark_url=f"{SEED_MEDIA_BASE}/xmen-mark.svg",
    mark_alt="X-Men Apocalypse academy signal mark",
    hero_url=f"{SEED_MEDIA_BASE}/xmen-hero.svg",
    hero_alt="Snow-lit academy and B-24 signal lines",
)
STUDIO_PROGRAM_MEDIA: dict[str, CommunityMediaSeed] = {
    "hp-universe": CommunityMediaSeed(
        mark_url=f"{SEED_MEDIA_BASE}/hp-mark.svg",
        mark_alt="HP Universe glass staircase mark",
        hero_url=f"{SEED_MEDIA_BASE}/hp-hero.svg",
        hero_alt="Glass staircase rising through castle stacks",
        hero_treatment="poster",
        hero_focal_point="top",
    ),
    "jurassic-park-universe": CommunityMediaSeed(
        mark_url=f"{SEED_MEDIA_BASE}/jurassic-mark.svg",
        mark_alt="Jurassic Park Universe operations mark",
        hero_url=f"{SEED_MEDIA_BASE}/jurassic-hero.svg",
        hero_alt="Island operations fence and paddock monitors",
        hero_treatment="background",
        hero_focal_point="bottom",
        hero_overlay="heavy",
    ),
    "rl-nyc": CommunityMediaSeed(
        mark_url=f"{SEED_MEDIA_BASE}/nyc-mark.svg",
        mark_alt="RL NYC late train mark",
        hero_url=f"{SEED_MEDIA_BASE}/nyc-hero.svg",
        hero_alt="Night street windows above a subway platform",
        hero_treatment="background",
        hero_overlay="heavy",
        hero_height="compact",
    ),
    "rl-small-town": CommunityMediaSeed(
        mark_url=f"{SEED_MEDIA_BASE}/smalltown-mark.svg",
        mark_alt="RL Small Town founders week mark",
        hero_url=f"{SEED_MEDIA_BASE}/smalltown-hero.svg",
        hero_alt="Town square noticeboard and storefront lights",
        hero_treatment="poster",
        hero_focal_point="bottom",
    ),
    "harbor-society": CommunityMediaSeed(
        mark_url=f"{SEED_MEDIA_BASE}/smalltown-mark.svg",
        mark_alt="Harbor Society shoreline club mark",
        hero_url=f"{SEED_MEDIA_BASE}/smalltown-hero.svg",
        hero_alt="Coastal town square lights before a gala",
        hero_treatment="poster",
        hero_focal_point="bottom",
    ),
}
X_MEN_BOARD_MEDIA: dict[str, BoardMediaSeed] = {
    "xavier-institute": BoardMediaSeed(
        f"{LOCATION_MEDIA_BASE}/xmen-xavier-institute.svg",
        "Snowbound academy windows under B-24 signal arcs",
    ),
    "new-york-city": BoardMediaSeed(
        f"{LOCATION_MEDIA_BASE}/xmen-new-york-city.svg",
        "Frozen New York street with emergency lights",
    ),
    "mutant-underground": BoardMediaSeed(
        f"{LOCATION_MEDIA_BASE}/xmen-mutant-underground.svg",
        "Underground safehouse platform lit by mutant network signals",
    ),
    "trask-b24-facilities": BoardMediaSeed(
        f"{LOCATION_MEDIA_BASE}/xmen-trask-b24-facilities.svg",
        "Sterile B-24 server lab with containment monitors",
    ),
    "united-nations": BoardMediaSeed(
        f"{LOCATION_MEDIA_BASE}/xmen-united-nations.svg",
        "Emergency council chamber under blue crisis feeds",
    ),
    "genosha": BoardMediaSeed(
        f"{LOCATION_MEDIA_BASE}/xmen-genosha.svg",
        "Island relay tower broadcasting over a red horizon",
    ),
}
STUDIO_PROGRAM_BOARD_MEDIA: dict[str, dict[str, BoardMediaSeed]] = {
    "hp-universe": {
        "castle-corridors": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/hp-castle-corridors.svg",
            "Castle corridor with shifting stairs and portrait light",
        ),
        "restricted-stacks": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/hp-restricted-stacks.svg",
            "Restricted library stacks glowing behind locked rails",
        ),
        "hogsmeade-after-dark": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/hp-hogsmeade-after-dark.svg",
            "Hogsmeade lane with warm windows after dark",
        ),
    },
    "jurassic-park-universe": {
        "isla-nublar": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/jurassic-isla-nublar.svg",
            "Rainy island ridge with operations lights beyond the trees",
        ),
        "paddock-twelve": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/jurassic-paddock-twelve.svg",
            "Paddock fence warning lights during a storm",
        ),
        "control-room": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/jurassic-control-room.svg",
            "Control room monitors showing paddock alerts",
        ),
        "worker-village": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/jurassic-worker-village.svg",
            "Worker village bunks under rain and utility lights",
        ),
    },
    "rl-nyc": {
        "brooklyn": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/nyc-brooklyn.svg",
            "Brooklyn storefronts and apartment windows at night",
        ),
        "queens-night-market": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/nyc-queens-night-market.svg",
            "Queens night market stalls under wet string lights",
        ),
        "shift-work": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/nyc-shift-work.svg",
            "Late shift hospital and train lights after midnight",
        ),
    },
    "rl-small-town": {
        "main-street": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/smalltown-main-street.svg",
            "Main Street storefronts around the town noticeboard",
        ),
        "lake-road": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/smalltown-lake-road.svg",
            "Lake road cabins and dusk water beyond the trees",
        ),
        "town-hall": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/smalltown-town-hall.svg",
            "Town hall windows over meeting notices and steps",
        ),
        "county-fairgrounds": BoardMediaSeed(
            f"{LOCATION_MEDIA_BASE}/smalltown-county-fairgrounds.svg",
            "County fairgrounds with tents and founders week lights",
        ),
    },
}


DISCOVERY_PROFILE_SEEDS: dict[str, DiscoveryProfileSeed] = {
    "x-men-apocalypse": DiscoveryProfileSeed(
        premise_archetype="urban-supernatural-pressure-cooker",
        play_engine="event-driven",
        lore_aperture="canon-divergent",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/3/3",
        activity_pace="weekly",
        activity_expectation="scene replies, missions, and wanted hooks",
        forum_adjunct="forum-first",
        roster_posture="canons and original faces",
        catalog_pitch="A public mutant crisis realm with school life, factions, and B-24 pressure.",
        onboarding_pitch="Start with the crisis, a faction tie, a wanted hook, or a first face.",
        featured_event_material_slug="b-24-winter",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "urban-supernatural",
                "Urban supernatural pressure",
                "superhero crisis mutants factions current chapter",
                10,
            ),
            DiscoveryTagSeed("entry_path", "wanted", "Open wanted hooks", "wanted casting", 20),
            DiscoveryTagSeed("format", "forum-first", "Forum-first", sort_order=30),
        ),
    ),
    "hp-universe": DiscoveryProfileSeed(
        premise_archetype="original-canon-adjacent-au",
        play_engine="institution-driven",
        lore_aperture="canon-divergent",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/3/3",
        activity_pace="relaxed",
        activity_expectation="no word count, scene-driven school and village plots",
        forum_adjunct="forum-first",
        roster_posture="canons, staff, students, and original faces",
        catalog_pitch="A magic-school AU with institution politics, haunted corridors, and village pressure.",
        onboarding_pitch="Start with a corridor scene, current event, canon tie, or wanted hook.",
        featured_event_material_slug="current-event",
        tags=(
            DiscoveryTagSeed(
                "premise", "canon-adjacent-au", "Canon-adjacent AU", "magic school fantasy", 10
            ),
            DiscoveryTagSeed("genre", "magic-school", "Magic school", "magic fantasy castle", 20),
            DiscoveryTagSeed("pace", "relaxed", "Relaxed activity", sort_order=30),
        ),
    ),
    "jurassic-park-universe": DiscoveryProfileSeed(
        premise_archetype="strange-frontier",
        play_engine="survival-driven",
        lore_aperture="canon-divergent",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/3/3",
        activity_pace="weekly",
        activity_expectation="event pressure, operations scenes, and survival threads",
        forum_adjunct="forum-first",
        roster_posture="staff, scientists, handlers, and original faces",
        catalog_pitch="A storm-hit island operations realm where survival and containment keep colliding.",
        onboarding_pitch="Start with the current incident, an operations role, or a paddock thread.",
        featured_event_material_slug="current-event",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "strange-frontier",
                "Strange frontier",
                "survival sci-fi science island",
                10,
            ),
            DiscoveryTagSeed("pressure", "survival", "Survival pressure", "storm containment", 20),
            DiscoveryTagSeed("format", "forum-first", "Forum-first", sort_order=30),
        ),
    ),
    "rl-nyc": DiscoveryProfileSeed(
        premise_archetype="fame-and-industry-drama",
        play_engine="character-driven",
        lore_aperture="low-lore-real-life",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="21+",
        content_rating="2/2/2",
        activity_pace="relaxed",
        activity_expectation="slice-of-life scenes, work ties, and city events",
        forum_adjunct="forum-first",
        roster_posture="original faces and workplace connections",
        catalog_pitch="An urban real-life realm built around rent week, night shifts, and creative pressure.",
        onboarding_pitch="Start with a shift, roommate tie, wanted hook, or public event.",
        featured_event_material_slug="current-event",
        tags=(
            DiscoveryTagSeed(
                "premise", "fame-industry", "Fame and industry drama", "urban real life city", 10
            ),
            DiscoveryTagSeed(
                "tone", "city-social-web", "City social web", "workplace roommate", 20
            ),
            DiscoveryTagSeed("pace", "relaxed", "Relaxed activity", sort_order=30),
        ),
    ),
    "rl-small-town": DiscoveryProfileSeed(
        premise_archetype="small-town-social-web",
        play_engine="character-driven",
        lore_aperture="low-lore-real-life",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="21+",
        content_rating="2/2/2",
        activity_pace="relaxed",
        activity_expectation="no word count, family ties, local rituals, and slow-burn scenes",
        forum_adjunct="forum-first",
        roster_posture="original faces, families, and town roles",
        catalog_pitch="A small-town social web built around founders week, family ties, and public rituals.",
        onboarding_pitch="Start with the festival, a family tie, a workplace, or a wanted hook.",
        featured_event_material_slug="current-event",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "small-town-social-web",
                "Small-town social web",
                "small town found family slow burn",
                10,
            ),
            DiscoveryTagSeed(
                "tone", "coastal-status", "Coastal status town", "club gossip social ladder", 20
            ),
            DiscoveryTagSeed("pace", "relaxed", "Relaxed activity", sort_order=30),
        ),
    ),
    "harbor-society": DiscoveryProfileSeed(
        premise_archetype="small-town-social-web",
        play_engine="character-driven",
        lore_aperture="low-lore-real-life",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="21+",
        content_rating="2/2/2",
        activity_pace="relaxed",
        activity_expectation="no word count, weekly scenes, town events, and wanted ties",
        forum_adjunct="forum-first",
        roster_posture="original faces, families, civic roles, and local businesses",
        catalog_pitch="A coastal status town where club politics, family favors, and public rituals make every secret useful.",
        onboarding_pitch="The gala vote, family ties, town jobs, and quiet debts are already in motion.",
        featured_event_material_slug="founders-gala",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "small-town-social-web",
                "Small-town social web",
                "coastal town family gossip civic status",
                10,
            ),
            DiscoveryTagSeed(
                "tone", "coastal-status", "Coastal status town", "club gala old families", 20
            ),
            DiscoveryTagSeed(
                "entry_path", "wanted", "Open calls", "families workplaces rivals", 30
            ),
        ),
    ),
    "signal-creek": DiscoveryProfileSeed(
        premise_archetype="weird-town-mystery",
        play_engine="mystery-driven",
        lore_aperture="open-lore",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/2/3",
        activity_pace="weekly",
        activity_expectation="chapter prompts, encounter scenes, and character-led clues",
        forum_adjunct="forum-first",
        roster_posture="locals, researchers, officials, skeptics, believers, and strange-touched faces",
        catalog_pitch="A mountain town keeps recording impossible signals after a vanished-year mystery.",
        onboarding_pitch="The midnight signal gives newcomers a reason to ask questions before town memory closes ranks.",
        featured_event_material_slug="midnight-signal",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "weird-town-mystery",
                "Weird-town mystery",
                "haunted town signal rumors",
                10,
            ),
            DiscoveryTagSeed(
                "pressure", "current-chapter", "Current chapter", "meteor shower missing hiker", 20
            ),
            DiscoveryTagSeed("lore", "open-lore", "Open lore", "phenomena encounters", 30),
        ),
    ),
    "nocturne-row": DiscoveryProfileSeed(
        premise_archetype="urban-supernatural-pressure-cooker",
        play_engine="faction-driven",
        lore_aperture="open-lore",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="21+",
        content_rating="3/3/3",
        activity_pace="weekly",
        activity_expectation="faction scenes, treaty fallout, open calls, and mature city plots",
        forum_adjunct="forum-first",
        roster_posture="species, factions, hunters, humans, officials, and original faces",
        catalog_pitch="A visible-supernatural city where a treaty breach turns nightlife, law, and old covenants hostile.",
        onboarding_pitch="The treaty breach gives every faction, witness, and bystander a reason to move before daylight.",
        featured_event_material_slug="treaty-breach",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "urban-supernatural",
                "Urban supernatural pressure",
                "vampires witches hunters law city",
                10,
            ),
            DiscoveryTagSeed(
                "pressure", "faction-treaty", "Faction treaty crisis", "treaty breach council", 20
            ),
            DiscoveryTagSeed("content", "mature", "Mature themes", "21 plus 333", 30),
        ),
    ),
    "crownfall": DiscoveryProfileSeed(
        premise_archetype="court-and-faction-fantasy",
        play_engine="faction-driven",
        lore_aperture="original-lore",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/2/3",
        activity_pace="weekly",
        activity_expectation="court scenes, faction moves, border pressure, and event turns",
        forum_adjunct="forum-first",
        roster_posture="houses, factions, rank claims, magic roles, and original faces",
        catalog_pitch="A kingdom left without a clean heir, where houses, mages, merchants, rebels, and clergy turn legitimacy into a weapon.",
        onboarding_pitch="The broken coronation gives nobles, servants, soldiers, priests, and spies immediate reasons to choose badly.",
        featured_event_material_slug="broken-coronation",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "court-and-faction-fantasy",
                "Court and faction fantasy",
                "succession houses court politics fantasy",
                10,
            ),
            DiscoveryTagSeed(
                "pressure",
                "succession-crisis",
                "Succession crisis",
                "coronation omen border raid",
                20,
            ),
            DiscoveryTagSeed(
                "roster", "faction-claims", "Faction claims", "houses mages clergy rebels", 30
            ),
        ),
    ),
    "afterlight-accord": DiscoveryProfileSeed(
        premise_archetype="original-canon-adjacent-au",
        play_engine="canon-adjacent",
        lore_aperture="semi-open-lore",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/2/3",
        activity_pace="weekly",
        activity_expectation="accord politics, inherited duties, rebel pressure, and dangerous old loyalties",
        forum_adjunct="forum-first",
        roster_posture="heirs, exiles, monsters, archivists, rebels, officials, and original faces",
        catalog_pitch="A broken treaty town where inherited duties survived the war better than the people did.",
        onboarding_pitch="The failing Accord seal gives heirs, exiles, archivists, and fugitives a reason to come home.",
        featured_event_material_slug="accord-seal-fails",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "canon-adjacent-au",
                "Original canon-adjacent AU",
                "branch point archetypes heirs exiles",
                10,
            ),
            DiscoveryTagSeed("lore", "semi-open-lore", "Semi-open lore", "original lore roles", 20),
            DiscoveryTagSeed(
                "entry_path", "role-archetype", "Inherited roles", "heirs monsters archivists", 30
            ),
        ),
    ),
    "brightline": DiscoveryProfileSeed(
        premise_archetype="fame-and-industry-drama",
        play_engine="character-driven",
        lore_aperture="low-lore-real-life",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="21+",
        content_rating="2/2/2",
        activity_pace="relaxed",
        activity_expectation="industry scenes, scandals, public events, and career pressure",
        forum_adjunct="forum-first",
        roster_posture="performers, fixers, patrons, press, lawyers, assistants, and original faces",
        catalog_pitch="A spotlight city where studios, clubs, magazines, patrons, and gossip turn image into leverage.",
        onboarding_pitch="Awards night, contract leaks, old favors, and public apologies are ready to pull people together.",
        featured_event_material_slug="awards-night-sabotage",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "fame-industry",
                "Fame and industry drama",
                "spotlight city celebrity industry scandal",
                10,
            ),
            DiscoveryTagSeed(
                "tone", "public-image", "Public image pressure", "gossip press patrons", 20
            ),
            DiscoveryTagSeed("pace", "relaxed", "Relaxed activity", "career scenes slow burn", 30),
        ),
    ),
    "emberhouse": DiscoveryProfileSeed(
        premise_archetype="survival-trials",
        play_engine="institution-driven",
        lore_aperture="original-lore",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/2/3",
        activity_pace="weekly",
        activity_expectation="trial prompts, house politics, scarcity scenes, and consent-safe pressure",
        forum_adjunct="forum-first",
        roster_posture="houses, candidates, instructors, medics, sponsors, and original faces",
        catalog_pitch="A trial academy where rank, scarcity, sponsors, and adult agendas decide who gets protected.",
        onboarding_pitch="Trial selection has already gone wrong, and every house has someone to protect or blame.",
        featured_event_material_slug="tampered-selection",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "survival-trials",
                "Survival and trials",
                "academy trials clans scarcity rank",
                10,
            ),
            DiscoveryTagSeed(
                "pressure",
                "institution-pressure",
                "Institution pressure",
                "house system selection",
                20,
            ),
            DiscoveryTagSeed(
                "content", "consent-safe-trials", "Consent-safe trials", "safety guide", 30
            ),
        ),
    ),
    "gaslight-ward": DiscoveryProfileSeed(
        premise_archetype="occult-historical-pressure",
        play_engine="mystery-driven",
        lore_aperture="original-lore",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="21+",
        content_rating="3/2/3",
        activity_pace="weekly",
        activity_expectation="inquiry scenes, society pressure, class conflict, and occult consequences",
        forum_adjunct="forum-first",
        roster_posture="investigators, socialites, criminals, reformers, mediums, workers, and original faces",
        catalog_pitch="A period city where class, crime, etiquette, newspapers, police power, and occult bargains collide.",
        onboarding_pitch="The locked-room murder gives society, workers, reporters, police, and mediums a public reason to lie.",
        featured_event_material_slug="impossible-murder",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "occult-historical",
                "Occult historical pressure",
                "period city occult class crime",
                10,
            ),
            DiscoveryTagSeed(
                "pressure", "murder-inquiry", "Murder inquiry", "impossible murder season", 20
            ),
            DiscoveryTagSeed(
                "tone", "respectability", "Respectability pressure", "society etiquette", 30
            ),
        ),
    ),
    "wayfarer-station": DiscoveryProfileSeed(
        premise_archetype="strange-frontier",
        play_engine="survival-driven",
        lore_aperture="original-lore",
        access_model="public-preview",
        application_model="profile-app",
        age_rating="18+",
        content_rating="3/2/3",
        activity_pace="weekly",
        activity_expectation="station scenes, scarcity pressure, frontier law, and signal mysteries",
        forum_adjunct="forum-first",
        roster_posture="crew, smugglers, medics, engineers, envoys, archivists, and original faces",
        catalog_pitch="An isolated station at the edge of known space where law is fragile and one signal can change every bargain.",
        onboarding_pitch="The missing convoy has already tightened supplies, stirred old debts, and made the station listen.",
        featured_event_material_slug="missing-convoy",
        tags=(
            DiscoveryTagSeed(
                "premise",
                "strange-frontier",
                "Strange frontier",
                "space station frontier signal scarcity",
                10,
            ),
            DiscoveryTagSeed(
                "pressure", "scarcity", "Scarcity pressure", "supplies convoy station law", 20
            ),
            DiscoveryTagSeed("genre", "soft-sci-fi", "Soft sci-fi", "frontier station", 30),
        ),
    ),
}

ORIGINAL_PREMISE_SEED_SLUGS: tuple[str, ...] = (
    "harbor-society",
    "signal-creek",
    "nocturne-row",
    "crownfall",
    "afterlight-accord",
    "brightline",
    "emberhouse",
    "gaslight-ward",
    "wayfarer-station",
)

ORIGINAL_PREMISE_SEED_ARCHETYPES: dict[str, str] = {
    "harbor-society": "small-town-social-web",
    "signal-creek": "weird-town-mystery",
    "nocturne-row": "urban-supernatural-pressure-cooker",
    "crownfall": "court-and-faction-fantasy",
    "afterlight-accord": "original-canon-adjacent-au",
    "brightline": "fame-and-industry-drama",
    "emberhouse": "survival-trials",
    "gaslight-ward": "occult-historical-pressure",
    "wayfarer-station": "strange-frontier",
}

ORIGINAL_PREMISE_WRITER_SEEDS: tuple[OriginalPremiseWriterSeed, ...] = (
    OriginalPremiseWriterSeed("juniper.gray@example.com", "junipergray", "Juniper Gray"),
    OriginalPremiseWriterSeed("miles.north@example.com", "milesnorth", "Miles North"),
    OriginalPremiseWriterSeed("cass.marlow@example.com", "cassmarlow", "Cass Marlow"),
    OriginalPremiseWriterSeed("lena.wren@example.com", "lenawren", "Lena Wren"),
)


SEED_PERSONAS: tuple[SeedPersona, ...] = (
    SeedPersona(
        "xmen_writer",
        "X-Men writer",
        "writer@example.com",
        "x-men-apocalypse",
        "starlane",
        "rogue",
        "Ordinary writer with accepted faces, active-face queue, and scene posting.",
        "/my/threads",
    ),
    SeedPersona(
        "xmen_staff",
        "X-Men staff",
        "moira@example.com",
        "x-men-apocalypse",
        "moira",
        "moira-mactaggert",
        "Staff controls for Studio, applications, claims, and private production rooms.",
        "/studio",
    ),
    SeedPersona(
        "xmen_mod",
        "X-Men moderator",
        "alex@example.com",
        "x-men-apocalypse",
        "alex",
        "cyclops",
        "Thread lifecycle and moderation controls without changing the default writer.",
        "/studio/operations",
    ),
    SeedPersona(
        "xmen_partner",
        "X-Men plotting partner",
        "charlie@example.com",
        "x-men-apocalypse",
        "charlie",
        "charles-xavier",
        "Wanted, plotter, plotting-room, and notification counterparty checks.",
        "/plotting",
    ),
    SeedPersona(
        "xmen_applicant",
        "X-Men applicant",
        "mira@example.com",
        "x-men-apocalypse",
        "mira",
        "kitty-pryde",
        "Submitted application and writer-side revision workflow.",
        "/applications",
    ),
    SeedPersona(
        "xmen_outsider",
        "X-Men outsider",
        "simon@example.com",
        "x-men-apocalypse",
        "simon",
        "bolivar-trask",
        "Non-staff outsider for private-room, notification, and denial checks.",
        "/notifications",
    ),
    SeedPersona(
        "xmen_inactive",
        "X-Men inactive member",
        "inactive@example.com",
        "x-men-apocalypse",
        "sleepingstar",
        "sleeping-star",
        "Inactive membership for recovery and authorization denial checks.",
        "/members",
    ),
    SeedPersona(
        "hp_director",
        "HP director",
        "writer@example.com",
        "hp-universe",
        "starlane",
        "rowan-ash",
        "Same login as X-Men writer, but with director powers in another community.",
        "/studio",
    ),
    SeedPersona(
        "jp_director",
        "Jurassic Park director",
        "writer@example.com",
        "jurassic-park-universe",
        "starlane",
        "lena-marquez",
        "Director controls for a visually different action-survival community.",
        "/studio",
    ),
    SeedPersona(
        "nyc_writer",
        "NYC writer",
        "writer@example.com",
        "rl-nyc",
        "starlane",
        "lena-park",
        "Same login without staff power in a contemporary city community.",
        "/my/threads",
    ),
    SeedPersona(
        "smalltown_writer",
        "Small-town writer",
        "writer@example.com",
        "rl-small-town",
        "starlane",
        "june-calloway",
        "Same login in a low-stakes ensemble community.",
        "/my/threads",
    ),
    SeedPersona(
        "harbor_director",
        "Harbor Society director",
        "writer@example.com",
        "harbor-society",
        "starlane",
        "maris-vale",
        "Director view for a coastal town where gala season turns favors into leverage.",
        "/studio/discovery",
    ),
    SeedPersona(
        "signal_director",
        "Signal Creek director",
        "writer@example.com",
        "signal-creek",
        "starlane",
        "ira-bell",
        "Director view for a mountain town following a signal nobody can explain.",
        "/studio/discovery",
    ),
    SeedPersona(
        "nocturne_director",
        "Nocturne Row director",
        "writer@example.com",
        "nocturne-row",
        "starlane",
        "marcel-voss",
        "Director view for a city treaty fraying under public supernatural pressure.",
        "/studio/discovery",
    ),
    SeedPersona(
        "crownfall_director",
        "Crownfall director",
        "writer@example.com",
        "crownfall",
        "starlane",
        "seren-vale",
        "Director view for a court deciding who can survive the crown's empty chair.",
        "/studio/discovery",
    ),
    SeedPersona(
        "afterlight_director",
        "Afterlight Accord director",
        "writer@example.com",
        "afterlight-accord",
        "starlane",
        "orin-vale",
        "Director view for a broken accord where inherited duties outlive the old war.",
        "/studio/discovery",
    ),
    SeedPersona(
        "brightline_director",
        "Brightline director",
        "writer@example.com",
        "brightline",
        "starlane",
        "viv-marlowe",
        "Director view for awards week, contract leaks, and people selling a cleaner story.",
        "/studio/discovery",
    ),
    SeedPersona(
        "emberhouse_director",
        "Emberhouse director",
        "writer@example.com",
        "emberhouse",
        "starlane",
        "nara-vale",
        "Director view for a trial academy where rank boards decide who gets protected.",
        "/studio/discovery",
    ),
    SeedPersona(
        "gaslight_director",
        "Gaslight Ward director",
        "writer@example.com",
        "gaslight-ward",
        "starlane",
        "ada-vale",
        "Director view for a gaslit city hiding murder behind manners.",
        "/studio/discovery",
    ),
    SeedPersona(
        "wayfarer_director",
        "Wayfarer Station director",
        "writer@example.com",
        "wayfarer-station",
        "starlane",
        "mara-voss",
        "Director view for a frontier station rationing air, law, and trust.",
        "/studio/discovery",
    ),
)


def seed_persona_by_key(persona_key: str) -> SeedPersona:
    for persona in SEED_PERSONAS:
        if persona.key == persona_key:
            return persona
    raise LookupError(f"seed persona not found: {persona_key}")


def resolve_seed_persona(repo: ForumRepository, persona_key: str) -> SeedPersonaContext:
    persona = seed_persona_by_key(persona_key)
    community = repo.get_community_by_slug(persona.community_slug)
    user = repo.get_user_by_email(persona.email)
    membership = repo.get_membership_by_username(community.id, persona.username)
    if membership.user_id != user.id:
        raise LookupError(
            f"seed persona {persona.key} membership does not belong to {persona.email}"
        )
    role = repo.get_role(community.id, membership.role_id)
    character = None
    if persona.character_slug:
        character = repo.get_character_by_slug(community.id, persona.character_slug)
        if character.membership_id != membership.id:
            raise LookupError(
                f"seed persona {persona.key} character does not belong to @{persona.username}"
            )
    return SeedPersonaContext(
        persona=persona,
        user=user,
        community=community,
        membership=membership,
        role=role,
        character=character,
    )


STUDIO_NETWORK_PROGRAMS: tuple[ProgramBlueprint, ...] = (
    ProgramBlueprint(
        slug="hp-universe",
        name="HP Universe",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        theme=BlueprintTheme(
            slug="glass-staircase",
            name="Glass Staircase",
            typography=BlueprintTypography(display="serif", body="serif", mono="mono"),
            light=BlueprintThemeMode(
                bg="#f8f2df",
                bg_subtle="#eee3c7",
                surface="#fff9e8",
                surface_elevated="#fbefd3",
                border="#c9b57b",
                text="#2b2417",
                text_muted="#6f6041",
                accent="#7b4f9f",
                accent_hover="#5f397f",
                accent_dim="#b99ad1",
                accent_secondary="#2f7c72",
                success="#477b5e",
                warning="#9b6a1f",
                error="#a64242",
            ),
            dark=BlueprintThemeMode(
                bg="#14111d",
                bg_subtle="#1d172a",
                surface="#221b31",
                surface_elevated="#2b223e",
                border="#5b4c77",
                text="#f4ecd8",
                text_muted="#c5b691",
                accent="#c8a6ff",
                accent_hover="#dfc8ff",
                accent_dim="#6f5595",
                accent_secondary="#7ed0bd",
                success="#8ac59b",
                warning="#dfb55f",
                error="#ef8f8f",
            ),
            radius="md",
            density="calm",
            texture="paper",
        ),
        characters=(
            BlueprintCharacter(
                "rowan-ash",
                "Rowan Ash",
                "Seventh-year cursebreaker-in-training who keeps seeing tomorrow on the stairs.",
                "Ancient magic, modern consequences.",
            ),
            BlueprintCharacter(
                "celeste-binns",
                "Celeste Binns",
                "Archivist's daughter who knows which portraits are lying.",
                "The library remembers.",
            ),
            BlueprintCharacter(
                "imogen-vale",
                "Professor Imogen Vale",
                "Ancient Runes professor assigned to keep a broken castle from choosing sides.",
                "Every ward has a witness.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "castle-corridors",
                "Castle Corridors",
                "location",
                "Portraits gossip faster than owls and the stairs have started answering back.",
                "A shifting school artery for rumors, detentions, vanished students, and late-night discoveries.",
            ),
            BlueprintBoard(
                "restricted-stacks",
                "Restricted Stacks",
                "location",
                "Where old spells keep footnotes on the living.",
                "Library scenes, secret research, and faculty-supervised bad ideas.",
            ),
            BlueprintBoard(
                "hogsmeade-after-dark",
                "Hogsmeade After Dark",
                "location",
                "Butterbeer, back rooms, and the first place rumors become plans.",
                "Village scenes for weekends, family pressure, clandestine meetings, and inconvenient crushes.",
            ),
            BlueprintBoard(
                "owlery-plotter",
                "Owlery Plotter",
                "desk",
                "Lesson threads, secret societies, club nights, and cursed-object handoffs.",
                "A writer lane for school-year planning, mystery partners, and character connection calls.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: The Glass Staircase",
                "premise",
                "A Hogwarts mystery where the castle is showing students futures nobody has chosen yet.",
                (
                    "The Glass Staircase appeared after a summer renovation opened a sealed wing "
                    "beneath the astronomy tower. It reflects possible futures: exam failures, "
                    "family betrayals, romances that should not exist, and one student who does "
                    "not appear in any reflection at all.\n\n"
                    "The board is built for school drama with a supernatural engine: classroom "
                    "rivalries, club politics, forbidden research, faculty secrets, Ministry "
                    "oversight, and students deciding whether prophecy is a warning or a dare."
                ),
            ),
            BlueprintMaterial(
                "current-event",
                "Current Event: No Reflection",
                "event",
                "One student has gone missing, and every portrait remembers a different last sighting.",
                (
                    "The current plot opens the week after Juniper Quill walks into the Glass "
                    "Staircase and disappears from every mirror in the castle.\n\n"
                    "Open scene lanes include corridor searches, suspicious detentions, family "
                    "letters, Ministry interviews, faculty arguments, and students using "
                    "forbidden magic because the adults are moving too slowly."
                ),
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "guide",
                "Applications should bring a school-year role and at least one reason to touch the mystery.",
                (
                    "Useful concepts include students with family pressure, professors with old "
                    "research, Ministry observers, Hogsmeade locals, prefects, club leaders, and "
                    "characters who have seen something in the Staircase they badly want to undo."
                ),
            ),
        ),
        wanted=(
            BlueprintWanted(
                "ministry-observer-for-the-staircase",
                "Ministry observer for the Glass Staircase inquiry",
                "event_role",
                "A public-safety official who can make the investigation better or much worse.",
                (
                    "The school needs an outside adult with authority, suspicion, and enough "
                    "political pressure to treat teenagers like evidence. They can be sympathetic, "
                    "ambitious, compromised, or all three."
                ),
                related_material_slug="current-event",
            ),
            BlueprintWanted(
                "student-who-saw-their-own-expulsion",
                "Student who saw their own expulsion",
                "plot_role",
                "A character whose reflected future makes them desperate enough to break rules now.",
                (
                    "Bring a student whose glimpse of the future creates immediate playable "
                    "pressure: blackmail, secret alliances, bad research partners, or a frantic "
                    "attempt to change the timeline before anyone else finds out."
                ),
                related_material_slug="premise",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="jurassic-park-universe",
        name="Jurassic Park Universe",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        theme=BlueprintTheme(
            slug="isla-nublar-operations",
            name="Isla Nublar Operations",
            typography=BlueprintTypography(display="condensed", body="system", mono="mono"),
            light=BlueprintThemeMode(
                bg="#f2efe2",
                bg_subtle="#e1decf",
                surface="#fbf8ec",
                surface_elevated="#ece7d3",
                border="#9a8f70",
                text="#20261d",
                text_muted="#5f6658",
                accent="#2f7d4f",
                accent_hover="#1f5d39",
                accent_dim="#8ab891",
                accent_secondary="#b46f22",
                success="#3d7b4b",
                warning="#a36d1b",
                error="#a94432",
            ),
            dark=BlueprintThemeMode(
                bg="#0d1510",
                bg_subtle="#142018",
                surface="#1b271f",
                surface_elevated="#223429",
                border="#4a604d",
                text="#f2ead7",
                text_muted="#b9c0aa",
                accent="#6bbf7a",
                accent_hover="#91d99b",
                accent_dim="#2d6c43",
                accent_secondary="#f0a64d",
                success="#7bc986",
                warning="#e7b85a",
                error="#ff8468",
            ),
            radius="sm",
            density="compact",
            texture="grid",
        ),
        characters=(
            BlueprintCharacter(
                "lena-marquez",
                "Dr. Lena Marquez",
                "Behavioral paleobiologist who can tell when the fences are lying.",
                "The paddock is never quiet.",
            ),
            BlueprintCharacter(
                "caleb-ross",
                "Caleb Ross",
                "Field tech with a radio, a keyring, and increasingly bad odds.",
                "Check the gate twice.",
            ),
            BlueprintCharacter(
                "asha-bennett",
                "Asha Bennett",
                "Guest-experience director trying to keep the soft opening from becoming evidence.",
                "Smile for the investors.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "isla-nublar",
                "Isla Nublar",
                "location",
                "Rain, alarms, and something moving beyond the treeline before the park opens.",
                "The island stage for research stations, visitor roads, guest previews, and containment failures.",
            ),
            BlueprintBoard(
                "paddock-twelve",
                "Paddock Twelve",
                "location",
                "A new attraction with old blood in the soil.",
                "Restricted animal-care scenes, field repairs, strange behavior logs, and the first bad tracks.",
            ),
            BlueprintBoard(
                "control-room",
                "Control Room",
                "location",
                "Every warning light wants to be someone else's problem.",
                "Operations, security disputes, investor calls, and the screens nobody should ignore.",
            ),
            BlueprintBoard(
                "worker-village",
                "Worker Village",
                "location",
                "Bunks, cafeteria rumors, storm prep, and people who know the park after dark.",
                "Staff relationships, local labor friction, contraband, and off-shift secrets.",
            ),
            BlueprintBoard(
                "operations",
                "Operations",
                "desk",
                "Where incident scenes become tomorrow's sanitized report.",
                "Open expeditions, staff calls, rescue planning, and survival plotting.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Soft Opening",
                "premise",
                "Jurassic Park is preparing a private preview while the island starts keeping secrets.",
                (
                    "The public story is simple: a controlled investor preview before the grand "
                    "opening. The private reality is a half-finished island full of rushed systems, "
                    "underpaid staff, animals smarter than the reports suggest, and executives who "
                    "need the park to look inevitable.\n\n"
                    "This hub supports science drama, worker politics, corporate pressure, survival "
                    "set pieces, guest panic, and the creeping realization that containment is also "
                    "a story people tell themselves."
                ),
            ),
            BlueprintMaterial(
                "paddock-twelve-incident",
                "Current Event: Paddock Twelve",
                "event",
                "A juvenile raptor has vanished from a sealed paddock during a tropical storm.",
                (
                    "The first event begins with a clean status board, a missing animal, and three "
                    "hours before invited guests arrive.\n\n"
                    "Playable lanes include fence-line searches, staff coverups, guest containment, "
                    "animal behavior reads, storm-damaged roads, and the question everyone avoids: "
                    "did the animal escape, or was it moved?"
                ),
            ),
            BlueprintMaterial(
                "park-bible",
                "Park Bible",
                "guide",
                "The director frame for tone, staff roles, animal encounters, and escalation.",
                (
                    "Keep the park playable by balancing wonder with consequence. The best scenes "
                    "are not only chase scenes: they are bad calls made under pressure, people "
                    "protecting each other across job titles, and the moment a beautiful impossible "
                    "thing becomes dangerous because someone wanted it profitable."
                ),
            ),
        ),
        wanted=(
            BlueprintWanted(
                "corporate-cleaner-for-paddock-twelve",
                "Corporate cleaner for the Paddock Twelve incident",
                "faction_need",
                "A legal, PR, or security operator sent to make the timeline investor-safe.",
                (
                    "This character should create friction with scientists and field staff by "
                    "turning a living emergency into a liability problem. Bonus if they are not "
                    "wrong about every risk, just wrong about what matters most."
                ),
                related_material_slug="paddock-twelve-incident",
            ),
            BlueprintWanted(
                "guest-who-saw-the-track",
                "Preview guest who saw the track",
                "plot_role",
                "A civilian witness with just enough truth to make containment harder.",
                (
                    "A guest, investor's child, travel journalist, or VIP spouse saw evidence "
                    "before the official story was ready. They can become a rescue priority, a "
                    "blackmail risk, or the only person asking the right question."
                ),
                related_material_slug="paddock-twelve-incident",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="rl-nyc",
        name="RL NYC",
        role_slug="member",
        role_name="Member",
        is_admin=False,
        theme=BlueprintTheme(
            slug="rent-week",
            name="Rent Week",
            typography=BlueprintTypography(display="system", body="system", mono="mono"),
            light=BlueprintThemeMode(
                bg="#f4f3ee",
                bg_subtle="#e5e2da",
                surface="#ffffff",
                surface_elevated="#ece9e1",
                border="#bbb5aa",
                text="#202124",
                text_muted="#64615c",
                accent="#c04468",
                accent_hover="#93314d",
                accent_dim="#d895a9",
                accent_secondary="#277c92",
                success="#3c7a5a",
                warning="#a36d1b",
                error="#b13f4e",
            ),
            dark=BlueprintThemeMode(
                bg="#101114",
                bg_subtle="#181b21",
                surface="#20232a",
                surface_elevated="#292d36",
                border="#4d5360",
                text="#f3f0eb",
                text_muted="#b9b4aa",
                accent="#ff7aa2",
                accent_hover="#ff9cbb",
                accent_dim="#8d3c55",
                accent_secondary="#4cc9e2",
                success="#75c997",
                warning="#e7b75f",
                error="#ff7f8c",
            ),
            radius="sm",
            density="compact",
            texture="scanline",
        ),
        characters=(
            BlueprintCharacter(
                "lena-park",
                "Lena Park",
                "Night-shift producer trying to make rent, art, and a life in the same week.",
                "Everything is urgent after midnight.",
            ),
            BlueprintCharacter(
                "mateo-rivera",
                "Mateo Rivera",
                "Community organizer with too many group chats and not enough sleep.",
                "The city keeps receipts.",
            ),
            BlueprintCharacter(
                "tessa-chen",
                "Tessa Chen",
                "ER nurse with an ex in every borough and no patience for soft lies.",
                "Triage is a love language.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "brooklyn",
                "Brooklyn",
                "location",
                "Coffee, sirens, venues, stoops, and second chances nobody admits they need.",
                "Apartments, bars, studios, parks, and neighborhood threads for everyday drama.",
            ),
            BlueprintBoard(
                "queens-night-market",
                "Queens Night Market",
                "location",
                "Food stalls, missed trains, awkward dates, and old friends pretending not to stare.",
                "A high-crossover social hub for chance meetings, group scenes, and messy reunions.",
            ),
            BlueprintBoard(
                "shift-work",
                "Shift Work",
                "location",
                "Hospitals, kitchens, trains, offices, and the hours that make people honest.",
                "Workplace scenes for ambition, burnout, care, rivalry, and late-night confession.",
            ),
            BlueprintBoard(
                "group-chat",
                "Group Chat",
                "desk",
                "Roommates, exes, gigs, borough ties, and chance meetings that need one more nudge.",
                "A writer lane for grounded relationship planning, open socials, and slice-of-life threads.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Rent Week",
                "premise",
                "A grounded NYC ensemble where money, love, ambition, and friendship collide in public.",
                (
                    "Rent Week follows a loose network of friends, exes, coworkers, neighbors, "
                    "artists, nurses, organizers, bartenders, teachers, and commuters through "
                    "one very expensive city.\n\n"
                    "The drama engine is human-scale: housing pressure, creative ambition, family "
                    "obligations, mutual aid, bad timing, queer found family, work exhaustion, and "
                    "the way one subway delay can reroute three relationships."
                ),
            ),
            BlueprintMaterial(
                "current-event",
                "Current Event: The Building Meeting",
                "event",
                "A rent hike turns one apartment building into the center of everyone's week.",
                (
                    "A new landlord announces renovations, rent increases, and buyout offers in a "
                    "building where half the cast knows someone.\n\n"
                    "Open lanes include tenant meetings, legal-aid nights, hallway arguments, old "
                    "flames ending up on opposite sides, fundraising gigs, and the soft terror of "
                    "deciding whether to stay in a city that keeps asking for more."
                ),
            ),
            BlueprintMaterial(
                "city-guide",
                "City Guide",
                "guide",
                "Keep stakes human, local, and character-led.",
                (
                    "Use neighborhoods as emotional geography, not tourist scenery. A borough can "
                    "mean commute time, family history, community ties, rent math, ex proximity, "
                    "and where a character feels most like themselves."
                ),
            ),
        ),
        wanted=(
            BlueprintWanted(
                "ex-bandmate-with-the-old-lease",
                "Ex-bandmate with the old lease",
                "relationship",
                "A former creative partner whose name is still on a lease, a song, or both.",
                (
                    "This character brings unfinished business: a band that almost made it, a "
                    "friendship that turned into avoidance, and one practical reason they cannot "
                    "fully disappear from Lena's life.\n\n"
                    "Why this matters:\n"
                    "- Their name is still on a lease, a demo, a booking contact, or all three.\n"
                    "- Lena needs the person who still has keys, credits, and emotional leverage.\n"
                    "- The rent hike can turn old creative history into an immediate practical problem.\n\n"
                    "First scene invitations:\n"
                    "- A hallway confrontation after the building meeting.\n"
                    "- A late-night text about lease renewal paperwork neither of them can ignore.\n"
                    "- An open mic where someone plays the old song without warning.\n"
                    "- A subway platform after a gig, with the band group chat waking back up.\n\n"
                    "Relationship lanes:\n"
                    "- Exes who buried the breakup under band logistics.\n"
                    "- Best friends who imploded before the first good review.\n"
                    "- Former roommates still splitting an apartment, a couch, or a debt.\n"
                    "- Creative partners arguing over who gets to keep the song.\n\n"
                    "Negotiables:\n"
                    "- Romance is optional; friction, history, and tenderness are the point.\n"
                    "- The band genre, exact lease situation, and blame split are flexible.\n"
                    "- Player can bring a new face or tie an existing face into Lena's past."
                ),
                related_material_slug="premise",
            ),
            BlueprintWanted(
                "tenant-organizer-who-knows-everyone",
                "Tenant organizer who knows everyone",
                "event_role",
                "A connective character for the building meeting, mutual aid, and messy alliances.",
                (
                    "This role is ideal for someone who can pull many characters into play: group "
                    "texts, canvassing, legal-aid referrals, public pressure, and private favors "
                    "that complicate the clean version of the cause."
                ),
                related_material_slug="current-event",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="rl-small-town",
        name="RL Small Town",
        role_slug="member",
        role_name="Member",
        is_admin=False,
        theme=BlueprintTheme(
            slug="founders-week",
            name="Founder's Week",
            typography=BlueprintTypography(display="serif", body="serif", mono="mono"),
            light=BlueprintThemeMode(
                bg="#fbf5e8",
                bg_subtle="#eee3cf",
                surface="#fffaf0",
                surface_elevated="#f4ead7",
                border="#c8b89a",
                text="#2b2318",
                text_muted="#75684f",
                accent="#8d3f4a",
                accent_hover="#6e2f38",
                accent_dim="#c9878f",
                accent_secondary="#4f7c5b",
                success="#4f7c5b",
                warning="#a06d2a",
                error="#a64242",
            ),
            dark=BlueprintThemeMode(
                bg="#16130f",
                bg_subtle="#211c16",
                surface="#282219",
                surface_elevated="#332b1f",
                border="#675942",
                text="#f6eddf",
                text_muted="#c9b99e",
                accent="#e38991",
                accent_hover="#f0a7ad",
                accent_dim="#7d4248",
                accent_secondary="#91c49a",
                success="#91c49a",
                warning="#dbb168",
                error="#ee8d8d",
            ),
            radius="md",
            density="calm",
            texture="paper",
        ),
        characters=(
            BlueprintCharacter(
                "june-calloway",
                "June Calloway",
                "Florist, town council note-taker, and keeper of other people's secrets.",
                "Everybody knows. Nobody says.",
            ),
            BlueprintCharacter(
                "eli-brooks",
                "Eli Brooks",
                "Mechanic back home after ten years and one burned bridge too many.",
                "The road back is short.",
            ),
            BlueprintCharacter(
                "mara-whitlock",
                "Mara Whitlock",
                "Deputy mayor with perfect manners and a family name nailed to every building.",
                "Legacy is not the same as loyalty.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "main-street",
                "Main Street",
                "location",
                "One stoplight, twelve opinions, and a bakery that hears everything.",
                "The town's public spine for errands, arguments, festivals, and reunions.",
            ),
            BlueprintBoard(
                "lake-road",
                "Lake Road",
                "location",
                "Cabins, bonfires, old dares, and the place nobody goes alone after rain.",
                "A scenic pressure valve for secrets, romances, trespassing, and returning-home arcs.",
            ),
            BlueprintBoard(
                "town-hall",
                "Town Hall",
                "location",
                "Minutes, motions, grudges, and the polite version of a knife fight.",
                "Civic scenes for local politics, public disputes, permits, and family reputations.",
            ),
            BlueprintBoard(
                "county-fairgrounds",
                "County Fairgrounds",
                "location",
                "String lights, livestock pens, reunion smiles, and the annual art of pretending.",
                "Events, volunteer shifts, rivalry games, summer jobs, and festival mess.",
            ),
            BlueprintBoard(
                "porch-light",
                "Porch Light",
                "desk",
                "Family ties, local history, slow-burn scene calls, and who knows what about whom.",
                "A writer lane for cozy conflict, small-town entanglements, and relationship plotting.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Founder's Week",
                "premise",
                "A small-town ensemble where celebration keeps digging up history.",
                (
                    "Founder's Week should be a cozy pressure cooker: parade planning, school "
                    "reunions, family businesses, old property lines, summer visitors, and people "
                    "who left town discovering the town kept a place for them anyway.\n\n"
                    "The board's tension is not apocalypse. It is reputation, memory, inheritance, "
                    "returning home, staying put, and the cost of everyone knowing the wrong half "
                    "of the story."
                ),
            ),
            BlueprintMaterial(
                "current-event",
                "Current Event: The Time Capsule",
                "event",
                "A buried town time capsule contains a letter that makes three families nervous.",
                (
                    "During Founder's Week setup, volunteers open a damaged time capsule early and "
                    "find a sealed letter naming someone who allegedly sold land that was never "
                    "theirs to sell.\n\n"
                    "Playable lanes include council meetings, diner gossip, legal threats, family "
                    "confrontations, childhood friends choosing sides, and outsiders realizing the "
                    "town's nicest traditions have teeth."
                ),
            ),
            BlueprintMaterial(
                "town-guide",
                "Town Guide",
                "guide",
                "A grounded small-town sandbox where history is social weather.",
                (
                    "Every character should have at least two visible ties: a place they are known, "
                    "a person they avoid, a family story, a job everyone comments on, or a town "
                    "ritual they cannot escape. Keep the stakes intimate and let history do the work."
                ),
            ),
        ),
        wanted=(
            BlueprintWanted(
                "returning-sibling-with-the-missing-deed",
                "Returning sibling with the missing deed",
                "relationship",
                "A homecoming character tied to the time capsule letter and an unresolved family split.",
                (
                    "This role gives the town an emotional fuse: someone who left, came back at the "
                    "worst possible moment, and may have the document everyone else is arguing about."
                ),
                related_material_slug="current-event",
            ),
            BlueprintWanted(
                "founders-week-rival-chair",
                "Founder's Week rival chair",
                "event_role",
                "A civic antagonist, ex-friend, or perfectionist volunteer making the festival personal.",
                (
                    "The fair needs a human source of pressure: someone who can weaponize seating "
                    "charts, permits, sponsorships, family history, and a smile sharp enough to draw blood."
                ),
                related_material_slug="current-event",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="harbor-society",
        name="Harbor Society",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "maris-vale",
                "Maris Vale",
                "Fallen club darling returning with a charity ledger nobody wants opened.",
                "A smile is a weapon if the room taught you how.",
            ),
            BlueprintCharacter(
                "celia-fairbourne",
                "Celia Fairbourne",
                "Old-family gatekeeper who treats the Shoreline Club like civic infrastructure.",
                "Standards keep the town from sinking.",
            ),
            BlueprintCharacter(
                "august-reed",
                "August Reed",
                "Harbor Ledger reporter with a source in every committee and one burned friendship.",
                "Print the polite version first.",
            ),
            BlueprintCharacter(
                "talia-cross",
                "Talia Cross",
                "Marina hotel manager who knows which guests arrive under the wrong name.",
                "Check-in is only the first secret.",
            ),
            BlueprintCharacter(
                "grant-keller",
                "Grant Keller",
                "Golden-child football coach trying to keep school donors and old debts apart.",
                "Everybody loves a winner until the bill arrives.",
            ),
            BlueprintCharacter(
                "sloane-devereux",
                "Sloane Devereux",
                "Club membership chair whose guest list can raise money or end a marriage.",
                "Access is an art.",
            ),
            BlueprintCharacter(
                "nora-bell",
                "Nora Bell",
                "Diner owner and town memory keeper who hears confessions over pie.",
                "Coffee first, consequences after.",
            ),
            BlueprintCharacter(
                "owen-vale",
                "Owen Vale",
                "Deputy mayor balancing family loyalty, gala optics, and a missing donation trail.",
                "Public service is private damage control.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "shoreline-club",
                "Shoreline Club",
                "location",
                "White jackets, old money, new grudges, and a membership vote nobody can avoid.",
                "Club politics, social climbing, charitable pressure, private conversations, and public exits.",
                image_url="/elbysodic-static/seed-media/smalltown-hero.svg",
                image_alt="Coastal club terrace under warm evening light",
                image_treatment="background",
            ),
            BlueprintBoard(
                "main-street",
                "Main Street",
                "location",
                "Boutiques, gossip windows, campaign flyers, and errands that become alliances.",
                "Everyday town scenes for work ties, rivals, returns, and public reputation.",
                image_url="/elbysodic-static/seed-media/locations/smalltown-main-street.svg",
                image_alt="Small-town main street with string lights",
                image_treatment="background",
            ),
            BlueprintBoard(
                "marina-hotel",
                "Marina Hotel",
                "location",
                "Guest books, quiet bars, conference rooms, and people hiding in plain sight.",
                "Hotel, tourism, visiting family, investor, and illicit-meeting scenes.",
            ),
            BlueprintBoard(
                "town-hall",
                "Town Hall",
                "location",
                "Minutes, permits, donor plaques, and civic kindness with sharp edges.",
                "Council scenes, public hearings, campaign pressure, and old-family bargaining.",
                image_url="/elbysodic-static/seed-media/locations/smalltown-town-hall.svg",
                image_alt="Town hall with a festival banner",
                image_treatment="background",
            ),
            BlueprintBoard(
                "harbor-ledger",
                "Harbor Ledger",
                "location",
                "A weekly paper with a printer that overheats whenever the town gets interesting.",
                "Reporter scenes, anonymous tips, editorials, public scandals, and local history.",
            ),
            BlueprintBoard(
                "back-veranda",
                "Back Veranda",
                "desk",
                "Family ties, committee warfare, club votes, rivals, and slow-burn scene calls.",
                "Bring gala seating charts, grudges, favors, and the conversations people keep having off the record.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: The Shoreline Vote",
                "premise",
                "A coastal town where club access, civic ritual, and family history make every favor public.",
                (
                    "Harbor Society is built around a town that looks effortless because hundreds "
                    "of people keep performing it correctly: club memberships, school boosters, "
                    "hotel openings, marina permits, campaign breakfasts, and family names that "
                    "still decide who gets forgiven.\n\n"
                    "Everything worth keeping has witnesses: old families, new money, public "
                    "service, town jobs, returning-home grudges, and the kind of romance or "
                    "rivalry that has to survive being discussed at breakfast."
                ),
            ),
            BlueprintMaterial(
                "founders-gala",
                "Current Chapter: Founders Gala",
                "event",
                "A Shoreline Club membership vote collides with a charity-accounting scandal.",
                (
                    "The opening chapter begins three days before the Founders Gala. The club is "
                    "voting on a controversial new member while a reporter receives a ledger page "
                    "suggesting last year's charity auction quietly covered a private debt.\n\n"
                    "Playable lanes include committee sabotage, donor pressure, hotel guests with "
                    "old ties, school boosters picking sides, family damage control, and a gala "
                    "night where every table setting is a threat."
                ),
            ),
            BlueprintMaterial(
                "social-ladder",
                "Social Ladder",
                "guide",
                "Status in Harbor Society is public, practical, and never as stable as it looks.",
                (
                    "The town always has room for old families, club staff, hotel workers, teachers, "
                    "boosters, reporters, marina workers, seasonal returnees, local officials, "
                    "artists, donors, service workers, and people who married into the wrong story."
                ),
            ),
            BlueprintMaterial(
                "town-power-map",
                "Town Power Map",
                "factions",
                "Old families, club staff, civic office, donors, and working locals all trade leverage differently.",
                (
                    "Harbor Society is not divided into formal factions so much as public lanes of power. "
                    "Old families own memory and invitations. Club staff control access and overhear what "
                    "members pretend was private. Civic office turns permits, donations, and school-board "
                    "appointments into favors. Hotel and marina workers see who arrives under the wrong name. "
                    "Reporters and diner regulars decide which version becomes town history."
                ),
            ),
            BlueprintMaterial(
                "donor-circuit",
                "Donor Circuit",
                "guide",
                "Money, favors, and public service move through the same handful of rooms.",
                (
                    "A donation can be charity, apology, vote-buying, family pressure, or a way to keep a "
                    "name off the front page. Use sponsors, booster clubs, hotel investors, gala committees, "
                    "marina permits, school fundraisers, and paper deadlines when a scene needs social "
                    "pressure without leaving town."
                ),
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us where the town knows them, what they are hiding, and who can make it worse.",
                (
                    "A strong application names who benefits if they stay quiet and what they need "
                    "during Founders Gala week. No one starts alone: attach a family, job, rivalry, "
                    "debt, committee, or open request."
                ),
            ),
            BlueprintMaterial(
                "town-calendar",
                "Town Calendar",
                "guide",
                "Recurring rituals keep the social web moving after the gala.",
                (
                    "Use club lunches, marina markets, football boosters, school fundraisers, "
                    "paper deadlines, hotel soft openings, council hearings, and Sunday diner "
                    "crowds as low-friction scene starters."
                ),
            ),
        ),
        wanted=(
            BlueprintWanted(
                "rival-committee-chair",
                "Rival committee chair",
                "rival",
                "A polished antagonist for seating charts, donor calls, and old resentment.",
                "Someone should be able to make a gala centerpiece feel like a declaration of war.",
                related_material_slug="founders-gala",
            ),
            BlueprintWanted(
                "secret-donor-with-conditions",
                "Secret donor with conditions",
                "plot_role",
                "A benefactor whose money solves one public problem and creates three private ones.",
                "Ideal for a patron, ex-spouse, parent, hotel investor, or political operator.",
                related_material_slug="founders-gala",
            ),
            BlueprintWanted(
                "reporter-source-at-the-club",
                "Reporter source at the club",
                "connection",
                "A staffer, guest, or committee member feeding August just enough truth to hurt people.",
                "They know which rooms August cannot enter and which names he should never print.",
                related_material_slug="founders-gala",
            ),
            BlueprintWanted(
                "returning-ex-with-town-leverage",
                "Returning ex with town leverage",
                "relationship",
                "A former love or friend whose return turns old intimacy into public strategy.",
                "Slow-burn, betrayal, family history, and business pressure can all live here.",
                related_material_slug="premise",
            ),
            BlueprintWanted(
                "school-booster-with-receipts",
                "School booster with receipts",
                "event_role",
                "A connective local who knows how charity money, sports donors, and club votes overlap.",
                "Parents, teachers, coaches, donors, and town officials all have reasons to answer their calls.",
                related_material_slug="founders-gala",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="signal-creek",
        name="Signal Creek",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "ira-bell",
                "Ira Bell",
                "Observatory technician who heard the first impossible broadcast.",
                "Tune slowly.",
            ),
            BlueprintCharacter(
                "mae-kincaid",
                "Sheriff Mae Kincaid",
                "Skeptical sheriff trying to keep panic from becoming policy.",
                "Evidence before folklore.",
            ),
            BlueprintCharacter(
                "lena-ortiz",
                "Lena Ortiz",
                "Archivist whose family records disagree with town memory.",
                "The filing cabinet remembers better.",
            ),
            BlueprintCharacter(
                "cal-rivera",
                "Cal Rivera",
                "Teen witness who insists the missing hiker came back wrong.",
                "Nobody listens until the woods answer.",
            ),
            BlueprintCharacter(
                "vera-snow",
                "Vera Snow",
                "Occult shop owner with a practical approach to impossible things.",
                "Candles are tools, not decoration.",
            ),
            BlueprintCharacter(
                "sam-wyatt",
                "Sam Wyatt",
                "Returning sibling of a woman who vanished during the blank year.",
                "Grief keeps a map.",
            ),
            BlueprintCharacter(
                "dr-niko-page",
                "Dr. Niko Page",
                "Clinic doctor tracking shared symptoms after the meteor shower.",
                "Vitals do not lie, but patients do.",
            ),
            BlueprintCharacter(
                "hollis-vale",
                "Hollis Vale",
                "County emergency manager sent to make the story smaller.",
                "Containment starts with vocabulary.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "blackridge-observatory",
                "Blackridge Observatory",
                "location",
                "Receivers, static, meteor logs, and a signal that knows names.",
                "Research scenes, midnight calls, staff prompts, and technical clues.",
            ),
            BlueprintBoard(
                "creekside-diner",
                "Creekside Diner",
                "location",
                "Pie, bad coffee, rumor chains, and locals pretending they are not scared.",
                "Low-friction social scenes, gossip, family ties, and public reactions.",
            ),
            BlueprintBoard(
                "mirror-lake",
                "Mirror Lake",
                "location",
                "Still water, trailheads, missing-person flyers, and reflections that lag.",
                "Search scenes, witness confrontations, teen dares, and phenomena encounters.",
            ),
            BlueprintBoard(
                "sheriff-station",
                "Sheriff Station",
                "location",
                "Incident boards, volunteer maps, official denials, and exhausted deputies.",
                "Law, search parties, interviews, and town-safety pressure.",
            ),
            BlueprintBoard(
                "relay-site-seven",
                "Relay Site Seven",
                "location",
                "A fenced hilltop installation that should have been decommissioned in 1989.",
                "Trespass, government pressure, hidden records, and strange signal escalation.",
            ),
            BlueprintBoard(
                "static-room",
                "Static Room",
                "desk",
                "Rumors, encounters, clue calls, chapter prompts, and strange-touched plotting.",
                "Drop sightings, half-remembered dates, missing hours, and the rumors people swear they heard themselves.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: The Blank Year",
                "premise",
                "Signal Creek is a mountain town where an impossible broadcast keeps reopening an old disappearance.",
                (
                    "In 1998, Signal Creek lost a year. Records skip. Families remember different "
                    "weather. One woman vanished from a search party nobody agrees happened. Now "
                    "the observatory is receiving a repeating broadcast from that missing year, "
                    "and the voice on the tape sometimes answers questions asked in the room.\n\n"
                    "Daily life keeps going anyway: locals, researchers, skeptics, believers, "
                    "officials, teens, doctors, archivists, and people touched by phenomena all "
                    "have to decide what truth costs."
                ),
            ),
            BlueprintMaterial(
                "midnight-signal",
                "Current Chapter: Midnight Signal",
                "event",
                "During a meteor shower, the observatory receives a live broadcast from a hiker missing for twelve hours.",
                (
                    "The opening chapter begins when a missing hiker's voice cuts through the "
                    "observatory feed at 12:03 a.m. She describes town landmarks as they looked "
                    "twenty-eight years ago, then says someone is standing behind the listeners.\n\n"
                    "Playable lanes include search parties, clinic symptoms, sheriff interviews, "
                    "archive contradictions, occult experiments, teen witnesses, and county "
                    "officials trying to seal the wrong door."
                ),
            ),
            BlueprintMaterial(
                "public-rumors",
                "Public Rumors",
                "guide",
                "A rumor board for clues that any writer can pick up without staff permission.",
                "Use signal bursts, repeating numbers, missing trail markers, wrong reflections, lost hours, sleepwalking, and old photographs as open scene fuel.",
            ),
            BlueprintMaterial(
                "encounter-rules",
                "Encounter Rules",
                "guide",
                "The mystery should invite play without forcing outcomes or secret staff answers.",
                "Writers may introduce small phenomena in public scenes. Major answers, disappearances, identity changes, and town-wide consequences need staff coordination.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us who they know in town, what they believe, and why the signal will not leave them alone.",
                "Locals, returnees, researchers, first responders, skeptics, believers, officials, doctors, students, and people with wrong memories all have a place here.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "field-technician-at-relay-seven",
                "Field technician at Relay Site Seven",
                "event_role",
                "A practical operator who knows the old hardware should not be powered.",
                "This role connects the observatory, county officials, and trespass scenes.",
                related_material_slug="midnight-signal",
            ),
            BlueprintWanted(
                "cult-survivor-who-remembers-1998",
                "Cult survivor who remembers 1998",
                "plot_role",
                "A person with a dangerous partial memory of the blank year.",
                "They remember just enough to be useful and not enough to feel safe.",
                related_material_slug="premise",
            ),
            BlueprintWanted(
                "government-observer-with-a-soft-cover",
                "Government observer with a soft cover",
                "faction_need",
                "An outsider officially here for emergency logistics and unofficially here for the signal.",
                "Pressure, mistrust, records requests, and uneasy alliances will find them fast.",
                related_material_slug="midnight-signal",
            ),
            BlueprintWanted(
                "local-rival-for-the-archives",
                "Local rival for the archives",
                "rival",
                "Someone who thinks Lena is hiding the wrong family history.",
                "Family, professional, academic, and deeply personal grudges are all welcome.",
                related_material_slug="public-rumors",
            ),
            BlueprintWanted(
                "person-who-remembers-the-vanished-year",
                "Person who remembers the vanished year differently",
                "connection",
                "A character whose memories contradict everyone else's record.",
                "They are certain, frightened, and probably wrong in ways that matter.",
                related_material_slug="premise",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="nocturne-row",
        name="Nocturne Row",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "marcel-voss",
                "Marcel Voss",
                "Vampire negotiator trying to keep old houses from treating the treaty as theater.",
                "Peace is a performance until blood proves otherwise.",
            ),
            BlueprintCharacter(
                "eliana-crowe",
                "Eliana Crowe",
                "Witch barrister arguing supernatural cases in a courthouse built on older law.",
                "Contracts remember intent.",
            ),
            BlueprintCharacter(
                "ren-maddox",
                "Ren Maddox",
                "Werewolf organizer turning clinic access and housing rights into faction leverage.",
                "Care is political.",
            ),
            BlueprintCharacter(
                "jules-hart",
                "Jules Hart",
                "Hunter defector whose safehouse map is already out of date.",
                "Survival starts after betrayal.",
            ),
            BlueprintCharacter(
                "mara-quinn",
                "Mara Quinn",
                "Human journalist chasing the public attack before the city edits the footage.",
                "The first draft is evidence.",
            ),
            BlueprintCharacter(
                "dr-silas-wren",
                "Dr. Silas Wren",
                "Coroner who knows which bodies stop obeying biology.",
                "Death keeps paperwork.",
            ),
            BlueprintCharacter(
                "nyx-bell",
                "Nyx Bell",
                "Nightclub owner whose back rooms host deals the council cannot admit exist.",
                "Every door has a price.",
            ),
            BlueprintCharacter(
                "tamsin-vale",
                "Tamsin Vale",
                "Council heir inheriting a treaty nobody her age believes in.",
                "Legacy is not consent.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "emberline-district",
                "Emberline District",
                "location",
                "Neon, sirens, late-night deals, and monsters trying to look ordinary.",
                "Nightlife, witness scenes, faction meetings, and street-level consequences.",
            ),
            BlueprintBoard(
                "covenant-hall",
                "Covenant Hall",
                "location",
                "A council chamber where old families call survival tradition.",
                "Council politics, treaty disputes, species law, and public-facing rituals.",
            ),
            BlueprintBoard(
                "hunter-safehouse",
                "Hunter Safehouse",
                "location",
                "A basement clinic, weapons lockers, burned contacts, and no clean exits.",
                "Hunter, defector, rescue, protection, and moral-compromise scenes.",
            ),
            BlueprintBoard(
                "saint-brigid-hospital",
                "Saint Brigid Hospital",
                "location",
                "Blood bank rumors, impossible charts, frightened residents, and missing evidence.",
                "Medical pressure, coroner scenes, whistleblowers, and species secrecy.",
            ),
            BlueprintBoard(
                "press-room",
                "Press Room",
                "location",
                "Screens, police statements, edited footage, and reporters who know too much.",
                "Media pressure, leaks, public opinion, and human-side entry points.",
            ),
            BlueprintBoard(
                "night-market",
                "Night Market",
                "desk",
                "Faction ties, species claims, treaty fallout, mature plots, and city-wide calls.",
                "Bring the bargains, cover stories, witness problems, and debts nobody wants on the council floor.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Treaty City",
                "premise",
                "Nocturne Row is a city where supernatural visibility, law, nightlife, and old covenants are failing at once.",
                (
                    "The public knows enough to be afraid and not enough to be accurate. Vampires, "
                    "witches, werewolves, hunters, humans, officials, and old families have lived "
                    "under the Meridian Treaty for twelve years. It promised peace, registration, "
                    "limited disclosure, and emergency courts. It did not promise trust.\n\n"
                    "Play centers on faction pressure, mature city scenes, forbidden ties, public "
                    "image, legal compromise, species boundaries, and characters choosing whether "
                    "order is worth preserving."
                ),
            ),
            BlueprintMaterial(
                "treaty-breach",
                "Current Chapter: Treaty Breach",
                "event",
                "A public attack outside a nightclub leaves a council elder missing and every faction blaming the wrong witness.",
                (
                    "The first chapter begins after a phone video shows something inhuman outside "
                    "the Emberline District. The footage goes public, the elder responsible for "
                    "nightlife security disappears, and the council invokes emergency treaty powers.\n\n"
                    "Playable lanes include witness protection, blood-bank pressure, hunter "
                    "retaliation, witch-law arguments, nightlife coverups, press leaks, and faction "
                    "leaders trying to decide which truth can survive daylight."
                ),
            ),
            BlueprintMaterial(
                "species-limits",
                "Species Limits",
                "guide",
                "Species lore is playable pressure, not an encyclopedia contest.",
                "Keep powers legible, costs visible, and consent central. Major bloodline, curse, domination, resurrection, or city-wide magic claims need staff review.",
            ),
            BlueprintMaterial(
                "city-law",
                "City Law",
                "guide",
                "The Meridian Treaty creates public systems that characters can use, resist, or exploit.",
                "Use emergency courts, registration hearings, blood-bank rules, safehouse maps, and council warrants as scene starters.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us what the city thinks they are, who has a claim on them, and where their hard line is.",
                "The treaty breach, a public job, a private faction tie, an open request, or a relationship can all make politics personal.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "hostile-witness-from-emberline",
                "Hostile witness from Emberline",
                "event_role",
                "A human, hunter, or supernatural witness whose statement could start a faction war.",
                "Press, police, council messengers, and protection details will all want them first.",
                related_material_slug="treaty-breach",
            ),
            BlueprintWanted(
                "coven-rival-in-court",
                "Coven rival in court",
                "rival",
                "A legal or magical opponent who believes Eliana is saving the wrong treaty.",
                "Courtroom scenes, old debts, and public-private magical pressure fit naturally here.",
                related_material_slug="city-law",
            ),
            BlueprintWanted(
                "hunter-handler-left-behind",
                "Hunter handler left behind",
                "connection",
                "Someone from Jules's past who still thinks defection can be reversed.",
                "Trust, danger, found family, and ideology all get sharper when they walk back in.",
                related_material_slug="premise",
            ),
            BlueprintWanted(
                "blood-bank-whistleblower",
                "Blood-bank whistleblower",
                "plot_role",
                "A hospital worker with records that make both the council and hunters dangerous.",
                "Their records make hospital corridors feel as dangerous as council chambers.",
                related_material_slug="treaty-breach",
            ),
            BlueprintWanted(
                "forbidden-romance-across-the-treaty",
                "Forbidden romance across the treaty",
                "relationship",
                "A relationship hook that makes law, species, and public safety personal.",
                "Romance is optional; loyalty under public pressure is the point.",
                related_material_slug="premise",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="crownfall",
        name="Crownfall",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "seren-vale",
                "Seren Vale",
                "Disputed heir whose claim depends on an omen no one trusts.",
                "A crown is a question with soldiers.",
            ),
            BlueprintCharacter(
                "maelor-cairn",
                "Maelor Cairn",
                "Spymaster keeping three houses loyal by telling each one a different truth.",
                "Secrets are cheaper than armies.",
            ),
            BlueprintCharacter(
                "ivra-senn",
                "Ivra Senn",
                "Mage scholar with proof the coronation omen was not divine.",
                "Magic leaves a receipt.",
            ),
            BlueprintCharacter(
                "torren-ash",
                "Torren Ash",
                "Border commander whose troops are tired of dying for court poetry.",
                "Hold the line, then ask why.",
            ),
            BlueprintCharacter(
                "eluned-ro",
                "Eluned Ro",
                "Merchant diplomat turning grain ships into political pressure.",
                "Markets crown the patient.",
            ),
            BlueprintCharacter(
                "sava-morn",
                "Sava Morn",
                "Temple advocate deciding whether legitimacy belongs to blood or survival.",
                "Faith also keeps ledgers.",
            ),
            BlueprintCharacter(
                "kael-riven",
                "Kael Riven",
                "Hostage noble with two family names and one impossible escape route.",
                "Politeness is captivity.",
            ),
            BlueprintCharacter(
                "mira-thorne",
                "Mira Thorne",
                "Royal bastard courted by rebels, priests, and people who need a symbol.",
                "Every rumor wants a face.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "opal-court",
                "Opal Court",
                "location",
                "Silk, steel, succession law, and every smile counted by witnesses.",
                "Court scenes, petitions, noble pressure, ceremonies, and private bargains.",
            ),
            BlueprintBoard(
                "border-watch",
                "Border Watch",
                "location",
                "Mud roads, burned signal towers, and soldiers asking whose crown feeds them.",
                "Military scenes, raids, refugees, field medicine, and hard loyalties.",
            ),
            BlueprintBoard(
                "mage-archive",
                "Mage Archive",
                "location",
                "Sealed stacks, failed prophecies, and spell records that contradict the temple.",
                "Research, magic rules, scholar rivalries, and dangerous evidence.",
            ),
            BlueprintBoard(
                "market-docks",
                "Market Docks",
                "location",
                "Grain ships, bribes, sailors, foreign coins, and news before the court hears it.",
                "Trade, rumors, smuggling, diplomacy, and working-class pressure.",
            ),
            BlueprintBoard(
                "high-temple",
                "High Temple",
                "location",
                "Bells, oaths, disputed doctrine, and priests who know crowns are made.",
                "Faith, legitimacy, confession, reform, and public ritual scenes.",
            ),
            BlueprintBoard(
                "war-room",
                "War Room",
                "desk",
                "House claims, faction moves, missing loyalties, and succession plotting.",
                "Bring letters, orders, oaths, betrayals, border news, and the private reasons people choose a claimant.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: A Crown Without Witness",
                "premise",
                "A monarch dies before naming an heir, and every institution claims the right to finish the sentence.",
                "The capital is full of people who cannot wait for certainty: houses, mages, clergy, merchants, rebels, soldiers, hostages, and servants all have reasons to care who becomes legitimate, and none of them can win alone.",
            ),
            BlueprintMaterial(
                "broken-coronation",
                "Current Chapter: Broken Coronation",
                "event",
                "The coronation is interrupted by a magical omen and a border raid timed too well to be chance.",
                "The opening chapter starts when the crown flame turns black during Seren's public oath. Before the court can decide whether it means rejection, a border tower falls and the first survivor names a noble house as traitor. Playable lanes include court accusations, temple inquiry, mage evidence, hostage leverage, refugee arrivals, and merchants deciding which claimant gets grain.",
            ),
            BlueprintMaterial(
                "houses-and-factions",
                "Houses And Factions",
                "factions",
                "A quick guide to the houses, temple, mage archive, border command, merchant compact, and rebels.",
                "Use factions as scene engines, not homework. A face should know what their institution wants, what it fears, and what private tie might make them betray the clean faction line.",
            ),
            BlueprintMaterial(
                "magic-limits",
                "Magic Limits",
                "guide",
                "Magic is political evidence with cost, witnesses, and institutional control.",
                "Public magic leaves trace, prophecy is disputed, and major spellwork needs staff coordination. Keep magic useful in scenes without making power scale the point of play.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us who can command them in public and who could ruin them in private.",
                "Nobles, servants, soldiers, priests, mages, merchants, rebels, hostages, healers, spies, and foreign observers all have reasons to be near the broken coronation or border raid.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "secret-claimant-with-proof",
                "Secret claimant with proof",
                "plot_role",
                "A person whose blood, document, or magical trace could reorder the succession.",
                "Court, temple, archive, and rebels will all want to decide whether they are a person or a weapon.",
                related_material_slug="broken-coronation",
            ),
            BlueprintWanted(
                "oath-bound-guard",
                "Oath-bound guard",
                "connection",
                "A guard sworn to the old monarch and now pulled between rival claimants.",
                "Loyalty, protection, betrayal, and close court scenes all sit under the same oath.",
                related_material_slug="premise",
            ),
            BlueprintWanted(
                "foreign-ambassador",
                "Foreign ambassador with a grain fleet",
                "faction_need",
                "An envoy whose recognition can feed the city or starve the wrong claimant.",
                "Their diplomacy comes with trade threats, public recognition, and a fleet everyone needs.",
                related_material_slug="houses-and-factions",
            ),
            BlueprintWanted(
                "black-market-mage",
                "Black-market mage with omen residue",
                "event_role",
                "A spellworker who knows the coronation omen was altered.",
                "Archive doors, criminal contacts, and dangerous evidence open around them.",
                related_material_slug="broken-coronation",
            ),
            BlueprintWanted(
                "lost-sibling-at-the-border",
                "Lost sibling at the border",
                "relationship",
                "A personal tie caught in the raid that makes the succession crisis intimate.",
                "Soldiers, nobles, rebels, and refugees all understand a war differently when family is missing.",
                related_material_slug="broken-coronation",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="afterlight-accord",
        name="Afterlight Accord",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "orin-vale",
                "Orin Vale",
                "Heir of a vanished order whose role survived better than the order did.",
                "Inheritance is a locked door.",
            ),
            BlueprintCharacter(
                "maia-renn",
                "Maia Renn",
                "Exile captain hired to escort people the Accord would rather forget.",
                "The map is a promise until it burns.",
            ),
            BlueprintCharacter(
                "sel-archa",
                "Sel Archa",
                "Archivist tracking which old stories changed after the catastrophe.",
                "Version control for myth.",
            ),
            BlueprintCharacter(
                "kesh-morrow",
                "Kesh Morrow",
                "Converted monster trying to prove personhood before the council votes.",
                "Mercy is policy when it has witnesses.",
            ),
            BlueprintCharacter(
                "lira-sun",
                "Lira Sun",
                "Reformer who believes the old roles should be elected, not inherited.",
                "No more crowns made of memory.",
            ),
            BlueprintCharacter(
                "tovan-grey",
                "Tovan Grey",
                "Border runner moving people through transit gates that should be sealed.",
                "Every gate wants a toll.",
            ),
            BlueprintCharacter(
                "nesa-wild",
                "Nesa Wild",
                "Reluctant prophet whose visions quote endings that never happened.",
                "The future plagiarizes badly.",
            ),
            BlueprintCharacter(
                "vail-ix",
                "Vail IX",
                "Traitor to the old ending with one useful secret and no safe allies.",
                "Regret is not redemption yet.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "accord-town",
                "Accord Town",
                "location",
                "A treaty settlement built where old enemies were told to become neighbors.",
                "Public politics, uneasy daily life, council scenes, and faction contact.",
            ),
            BlueprintBoard(
                "old-academy",
                "Old Academy",
                "location",
                "Dormant halls, broken trials, and students inheriting duties nobody explained.",
                "Training, legacy pressure, old vows, and early threads for characters still learning what their names cost.",
            ),
            BlueprintBoard(
                "memory-archive",
                "Memory Archive",
                "location",
                "Records of the old ending, sealed branches, and stories that keep rewriting themselves.",
                "Research, archive disputes, lore reveals, and provenance questions.",
            ),
            BlueprintBoard(
                "rebel-safehouse",
                "Rebel Safehouse",
                "location",
                "Maps, false papers, stolen keys, and arguments about what freedom costs.",
                "Rebel scenes, rescue plans, fugitives, and moral compromise.",
            ),
            BlueprintBoard(
                "transit-gate",
                "Transit Gate",
                "location",
                "A damaged gate network that still opens for names it recognizes.",
                "Travel, border pressure, missing mentors, contraband, and strange arrivals.",
            ),
            BlueprintBoard(
                "branch-room",
                "Branch Room",
                "desk",
                "Inherited duties, branch records, accord pressure, and open calls.",
                "Bring old vows, missing mentors, sealed branches, broken gates, and the loyalties nobody can explain cleanly.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: The Old Ending Broke",
                "premise",
                "The Accord survived the catastrophe, but nobody agrees what victory was supposed to cost.",
                "People inherit duties, symbols, rivalries, powers, debts, and expectations from a world that no longer agrees on what happened. Some families call that honor. Some call it a sentence.",
            ),
            BlueprintMaterial(
                "accord-seal-fails",
                "Current Chapter: The Seal Fails",
                "event",
                "The Accord seal breaks during a remembrance ceremony and frees one prisoner history says died.",
                "The opening chapter brings public panic, council hearings, rebel movement, archive contradictions, and old names returning to circulation. Heirs, exiles, monsters, archivists, reformers, runners, officials, and people whose inherited story no longer fits all have reasons to be there.",
            ),
            BlueprintMaterial(
                "branch-point",
                "Branch Point",
                "guide",
                "The old ending failed at the moment victory became occupation.",
                "People remember the world through duties and consequences. Bring new names, new places, and obligations that belong to this setting.",
            ),
            BlueprintMaterial(
                "role-archetypes",
                "Inherited Roles",
                "guide",
                "Heirs, exiles, converted monsters, archivists, rebels, prophets, traitors, and border runners all have unfinished business.",
                "An inherited role is not a cage. Bring a pressure, a tie, and a reason the Accord makes their life harder now.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us what they inherited, who expects obedience, and what the old ending broke in them.",
                "Bring concepts rooted in this setting: original names, original places, and obligations that create new social, political, or emotional trouble.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "missing-mentor-from-the-old-ending",
                "Missing mentor from the old ending",
                "relationship",
                "A mentor figure whose return complicates the Accord's official history.",
                "Heirs, archivists, rebels, and anyone who built a life around a lie will have reasons to answer them.",
                related_material_slug="accord-seal-fails",
            ),
            BlueprintWanted(
                "oath-sibling-with-a-broken-role",
                "Oath sibling with a broken role",
                "connection",
                "Someone bound to a role that no longer matches what the world needs.",
                "They arrive with instant history, a private promise, and a public problem.",
                related_material_slug="role-archetypes",
            ),
            BlueprintWanted(
                "archive-thief",
                "Archive thief with a sealed branch",
                "plot_role",
                "A thief who stole the record of one possible ending.",
                "Archive scenes, rebel deals, transit-gate chases, and council pressure follow them naturally.",
                related_material_slug="accord-seal-fails",
            ),
            BlueprintWanted(
                "forbidden-envoy",
                "Forbidden envoy from beyond the gate",
                "faction_need",
                "An envoy whose existence proves the Accord map is incomplete.",
                "Diplomacy, suspicion, travel, and new history all arrive with their papers.",
                related_material_slug="branch-point",
            ),
            BlueprintWanted(
                "reformed-antagonist",
                "Reformed antagonist nobody wants pardoned",
                "rival",
                "A former enemy whose survival forces the community to define justice.",
                "Accountability, trust, and reform get harder when victims are still in the room.",
                related_material_slug="premise",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="brightline",
        name="Brightline",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "viv-marlowe",
                "Viv Marlowe",
                "Rising performer whose contract leak makes her useful to everyone but herself.",
                "Applause is leverage.",
            ),
            BlueprintCharacter(
                "rex-arden",
                "Rex Arden",
                "PR fixer who can bury a scandal if nobody asks what else goes underground.",
                "Optics first, truth second.",
            ),
            BlueprintCharacter(
                "dahlia-voss",
                "Dahlia Voss",
                "Old-money patron funding careers with conditions hidden in compliments.",
                "Taste is power with better lighting.",
            ),
            BlueprintCharacter(
                "kit-valentine",
                "Kit Valentine",
                "Gossip columnist whose sources keep becoming friends at the worst time.",
                "Print it before they deny it.",
            ),
            BlueprintCharacter(
                "milo-cade",
                "Milo Cade",
                "Producer trying to keep awards season from exposing how the deal was made.",
                "Every hit has paperwork.",
            ),
            BlueprintCharacter(
                "june-park",
                "June Park",
                "Venue owner who knows who can still sing after midnight and who cannot pay rent.",
                "Backstage tells the truth.",
            ),
            BlueprintCharacter(
                "lena-sable",
                "Lena Sable",
                "Fallen idol staging a comeback through one last dangerous favor.",
                "The spotlight remembers.",
            ),
            BlueprintCharacter(
                "ari-cho",
                "Ari Cho",
                "Assistant with receipts, calendar access, and no reason to stay loyal.",
                "Scheduling is surveillance.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "studio-lot",
                "Studio Lot",
                "location",
                "Soundstages, contracts, trailers, and people smiling through sabotage.",
                "Industry work scenes, auditions, producer pressure, and career bargaining.",
            ),
            BlueprintBoard(
                "blue-room",
                "Blue Room",
                "location",
                "A live club where careers begin, end, and get overheard from the bar.",
                "Performances, rivals, nightlife, found family, and late-night consequences.",
            ),
            BlueprintBoard(
                "gloss-office",
                "Gloss Office",
                "location",
                "Magazine deadlines, anonymous tips, photo selects, and legal threats.",
                "Press, gossip, image work, interviews, and source scenes.",
            ),
            BlueprintBoard(
                "charity-circuit",
                "Charity Circuit",
                "location",
                "Patrons, galas, photographers, old money, and favors dressed as generosity.",
                "Public image, fundraising, status, and social warfare.",
            ),
            BlueprintBoard(
                "courthouse-steps",
                "Courthouse Steps",
                "location",
                "Contract filings, defamation threats, paparazzi, and public statements.",
                "Legal pressure, scandal escalation, and career stakes.",
            ),
            BlueprintBoard(
                "green-room",
                "Green Room",
                "desk",
                "Career ties, scandal boards, open calls, rivals, patrons, and slow-burn plotting.",
                "Bring contract trouble, comeback plans, crisis favors, fake smiles, and the messages sent after midnight.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Image Has Teeth",
                "premise",
                "Brightline is a fame and industry drama where public image, creative work, and private compromise become leverage.",
                "Studios, clubs, magazines, patrons, lawyers, stylists, assistants, performers, producers, and gossip writers all move through the same city circuit. Careers turn on who gets seen, who gets protected, and who pays for the version of the story that sells.",
            ),
            BlueprintMaterial(
                "awards-night-sabotage",
                "Current Chapter: Awards Night Sabotage",
                "event",
                "An awards-night performance is sabotaged minutes before a leaked contract hits the press.",
                "The opening chapter starts with a failed spotlight, a missing backing track, and a contract leak that suggests a career-making deal was rigged. Playable lanes include backstage accusations, crisis PR, patron pressure, legal threats, magazine deadlines, and exes deciding whether to protect each other.",
            ),
            BlueprintMaterial(
                "career-ladder",
                "Career Ladder",
                "guide",
                "Fame is not only celebrity; it is access, labor, debt, patronage, and public narrative.",
                "Performers, stylists, assistants, venue workers, publicists, critics, photographers, lawyers, producers, patrons, influencers, crew, and people living near the spotlight all have something at stake.",
            ),
            BlueprintMaterial(
                "scandal-board",
                "Scandal Board",
                "guide",
                "Scandals should create playable pressure rather than punish writers for having messy faces.",
                "Use leaks, contracts, feuds, sponsorships, reviews, bad photos, public apologies, and private favors as scene starters. Consent and boundaries decide how far a scandal reaches.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us what the public thinks they are, what it costs to maintain, and who can help or hurt them.",
                "Tie them to awards week, the Blue Room, Gloss, court filings, the charity circuit, or a person whose favor is never free.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "rival-performer-with-the-same-song",
                "Rival performer with the same song",
                "rival",
                "A performer whose set list turns sabotage into personal history.",
                "Rivalry, romance, creative theft, and career comparison can all share the same stage.",
                related_material_slug="awards-night-sabotage",
            ),
            BlueprintWanted(
                "crisis-photographer",
                "Crisis photographer with the wrong image",
                "event_role",
                "A photographer who captured what PR needs buried.",
                "Press, legal, backstage, and public-image pressure all want the same contact sheet.",
                related_material_slug="awards-night-sabotage",
            ),
            BlueprintWanted(
                "patron-with-conditions",
                "Patron with conditions",
                "faction_need",
                "A benefactor whose money can open doors or own the room.",
                "Charity circuit favors, career debt, and status scenes follow their invitations.",
                related_material_slug="career-ladder",
            ),
            BlueprintWanted(
                "ex-manager-with-files",
                "Ex-manager with files",
                "connection",
                "A former manager, assistant, or handler holding documents nobody wants surfaced.",
                "Old trust, threats, legal leverage, and comeback plans all sit in their inbox.",
                related_material_slug="scandal-board",
            ),
            BlueprintWanted(
                "secret-spouse-or-contract-clause",
                "Secret spouse or contract clause",
                "relationship",
                "A relationship hook that makes public image and private loyalty collide.",
                "Romance is optional; the pressure is what the public version of the relationship costs.",
                related_material_slug="premise",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="emberhouse",
        name="Emberhouse",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "nara-vale",
                "Nara Vale",
                "Reluctant champion whose selection score should have been impossible.",
                "Win quietly or burn loudly.",
            ),
            BlueprintCharacter(
                "cassian-rook",
                "Cassian Rook",
                "Ambitious rival from a house that treats mercy like bad strategy.",
                "Second place is a warning.",
            ),
            BlueprintCharacter(
                "maeve-torr",
                "Maeve Torr",
                "Instructor trying to keep trials useful without letting sponsors turn them cruel.",
                "Pressure is not permission.",
            ),
            BlueprintCharacter(
                "ion-bell",
                "Ion Bell",
                "Medic who sees which injuries the academy calls character-building.",
                "Survival has aftercare.",
            ),
            BlueprintCharacter(
                "sena-quill",
                "Sena Quill",
                "House heir expected to win cleanly while everyone else cheats for her.",
                "Legacy is a crowded room.",
            ),
            BlueprintCharacter(
                "tavi-moss",
                "Tavi Moss",
                "Outsider scholarship student who knows scarcity before the academy simulates it.",
                "Resourcefulness is not romance.",
            ),
            BlueprintCharacter(
                "bram-hale",
                "Bram Hale",
                "Quartermaster whose supply ledgers can expose who tampered with selection.",
                "Nothing disappears. It gets requisitioned.",
            ),
            BlueprintCharacter(
                "elix-ward",
                "Elix Ward",
                "Council observer deciding whether the house system protects candidates or brands them.",
                "Oversight has teeth if anyone lets it bite.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "ember-hall",
                "Ember Hall",
                "location",
                "House banners, rank boards, sponsor balconies, and candidates learning who is watched.",
                "Dormitory and common-hall scenes for house politics, alliances, and public pressure.",
            ),
            BlueprintBoard(
                "trial-grounds",
                "Trial Grounds",
                "location",
                "Obstacle fields, signal flares, and rules everyone quotes before bending them.",
                "Trial prompts, team pressure, training scenes, and controlled danger.",
            ),
            BlueprintBoard(
                "council-chamber",
                "Council Chamber",
                "location",
                "Adults arguing about safety with candidates sitting outside the door.",
                "Policy, sponsors, appeals, rank disputes, and institutional stakes.",
            ),
            BlueprintBoard(
                "infirmary",
                "Infirmary",
                "location",
                "Clean sheets, hidden bruises, consent check-ins, and records sponsors cannot edit.",
                "Aftercare, medical scenes, injury fallout, and quiet truth-telling.",
            ),
            BlueprintBoard(
                "supply-depot",
                "Supply Depot",
                "location",
                "Ration tags, missing gear, locked crates, and someone always counting wrong.",
                "Scarcity scenes, quartermaster pressure, sabotage clues, and practical alliances.",
            ),
            BlueprintBoard(
                "trial-table",
                "Trial Table",
                "desk",
                "House ties, safety limits, rank claims, trial prompts, and open roles.",
                "Bring appeals, rivalries, aftercare needs, sponsor pressure, and the boundaries nobody gets to hand-wave.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Trial Season",
                "premise",
                "Emberhouse is a trial academy where rank, scarcity, loyalty, and adult agendas decide who gets protected.",
                "Candidates train inside a house system that claims trials build leadership. The real story is messier: sponsors, rank boards, scarce supplies, old house debts, safety limits, instructors with competing ethics, and candidates deciding what winning should cost.",
            ),
            BlueprintMaterial(
                "tampered-selection",
                "Current Chapter: Tampered Selection",
                "event",
                "The first trial roster is altered before dawn, moving three candidates into the wrong danger tier.",
                "Opening scenes can start in the house hall, supply depot, infirmary, council chamber, or trial grounds. The question is not only who cheated. It is who benefits when the academy calls the result tradition.",
            ),
            BlueprintMaterial(
                "house-guide",
                "House Guide",
                "factions",
                "The house system gives characters identity, rivals, resources, and expectations.",
                "Use houses as pressure lanes rather than sorting labels. Every house should offer allies, blind spots, and a reason a candidate might break rank.",
            ),
            BlueprintMaterial(
                "trial-rules",
                "Trial Rules And Safety",
                "guide",
                "Trials should create dramatic pressure while preserving writer consent and character agency.",
                "Major injuries, coercion, elimination, captivity, or public humiliation require coordination. The academy can be harsh without making writers fight for basic boundaries.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us who the house system says they are, what pressure follows them, and what boundary matters.",
                "Candidates, instructors, medics, quartermasters, house heirs, scholarship students, council observers, sponsors, and family outside the academy all have room here.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "secret-sponsor",
                "Secret sponsor with a hidden candidate",
                "faction_need",
                "A patron whose support explains why a candidate keeps surviving bad odds.",
                "House pressure, favoritism, and uncomfortable protection sit under every favor.",
                related_material_slug="tampered-selection",
            ),
            BlueprintWanted(
                "sibling-competitor",
                "Sibling competitor in another house",
                "relationship",
                "A family tie split across house loyalty and public ranking.",
                "Rivalry, protection, resentment, and impossible team scenes come with the name.",
                related_material_slug="house-guide",
            ),
            BlueprintWanted(
                "rule-enforcer",
                "Rule enforcer everyone underestimates",
                "event_role",
                "A staff or senior candidate responsible for making trial law visible.",
                "Cheating, appeals, and safety boundaries all get messier when they enter.",
                related_material_slug="trial-rules",
            ),
            BlueprintWanted(
                "injured-favorite",
                "Injured favorite with a missing supply tag",
                "plot_role",
                "A high-ranked candidate whose injury exposes the tampered selection.",
                "Attach this to infirmary, depot, and council scenes.",
                related_material_slug="tampered-selection",
            ),
            BlueprintWanted(
                "black-market-supplier",
                "Black-market supplier inside the depot",
                "connection",
                "Someone moving gear through the academy before scarcity becomes scandal.",
                "Bargains, favors, and practical moral compromise come wrapped in supply tags.",
                related_material_slug="premise",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="gaslight-ward",
        name="Gaslight Ward",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "ada-vale",
                "Ada Vale",
                "Investigator whose murder inquiry keeps crossing society drawing rooms.",
                "Ask softly. Listen for the lie.",
            ),
            BlueprintCharacter(
                "lucien-rowe",
                "Lucien Rowe",
                "Crime-family heir trying to make respectability pay better than fear.",
                "Bloodlines are balance sheets.",
            ),
            BlueprintCharacter(
                "mira-bell",
                "Mira Bell",
                "Medium with clients in every class and debts in every shadow.",
                "The dead are not discreet.",
            ),
            BlueprintCharacter(
                "edwin-frost",
                "Edwin Frost",
                "Newspaper editor who knows the city sells papers faster when it panics.",
                "Ink before alibi.",
            ),
            BlueprintCharacter(
                "celeste-ward",
                "Celeste Ward",
                "Society hostess whose season rooms hide reform money and occult favors.",
                "Manners are a locked drawer.",
            ),
            BlueprintCharacter(
                "jonas-pike",
                "Jonas Pike",
                "Factory organizer with a witness nobody important wants heard.",
                "Respectability rarely pays rent.",
            ),
            BlueprintCharacter(
                "thea-morne",
                "Thea Morne",
                "Stage performer whose patron vanished after the impossible murder.",
                "Curtain calls are evidence.",
            ),
            BlueprintCharacter(
                "dr-silas-gray",
                "Dr. Silas Gray",
                "Surgeon asked to sign a death certificate that anatomy refuses.",
                "The body objects.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "newspaper-office",
                "Newspaper Office",
                "location",
                "Hot type, anonymous letters, libel threats, and reporters who work past midnight.",
                "Press scenes, public panic, sources, editorials, and clue circulation.",
            ),
            BlueprintBoard(
                "police-court",
                "Police Court",
                "location",
                "Witness benches, corrupt clerks, public charges, and private bargains.",
                "Investigation, testimony, arrests, and institutional pressure.",
            ),
            BlueprintBoard(
                "season-rooms",
                "Season Rooms",
                "location",
                "Etiquette, introductions, whispers, and old debts under gaslight.",
                "Society scenes, class pressure, patronage, and public respectability.",
            ),
            BlueprintBoard(
                "dock-factory",
                "Docks And Factory",
                "location",
                "Fog, shift bells, union talk, smuggling, and people society only notices when useful.",
                "Worker scenes, crime pressure, witnesses, and reform politics.",
            ),
            BlueprintBoard(
                "occult-society",
                "Occult Society",
                "location",
                "Velvet curtains, sealed ledgers, borrowed names, and bargains older than the city.",
                "Mediums, occult debt, rituals, and hidden institutions.",
            ),
            BlueprintBoard(
                "ward-room",
                "Ward Room",
                "desk",
                "Inquiry leads, class ties, occult rules, open calls, and period-pressure plotting.",
                "Bring alibis, patrons, frightened witnesses, debts, invitations, and the secrets polite rooms keep warm.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Respectability And Rot",
                "premise",
                "Gaslight Ward is a period city where class, crime, reform, newspapers, etiquette, and occult societies collide.",
                "The city runs on public respectability and private bargains. Every institution has a front room and a cellar: society houses, newspapers, police courts, factories, theaters, hospitals, and occult circles all trade favors while pretending not to know one another.",
            ),
            BlueprintMaterial(
                "impossible-murder",
                "Current Chapter: Impossible Murder",
                "event",
                "A society-season debut is interrupted by a murder that happened in a locked room full of witnesses.",
                "Opening scenes can begin with witness statements, newspaper panic, society damage control, factory rumors, occult debts, medical contradictions, or police pressure. The mystery is playable because every class saw a different version of the room.",
            ),
            BlueprintMaterial(
                "city-institutions",
                "City Institutions",
                "guide",
                "The Ward is built from institutions that create scene pressure.",
                "Newspapers, police courts, factories, theaters, hospitals, season rooms, crime families, and occult societies all have public rules and private exceptions.",
            ),
            BlueprintMaterial(
                "occult-rules",
                "Occult Rules",
                "guide",
                "Occult power works through debt, witness, ritual, and consequence.",
                "Keep magic costly and social. Major possession, resurrection, mind control, or public supernatural proof requires staff coordination.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us what respectability demands of them and what bargain it cannot see.",
                "Investigators, socialites, workers, criminals, doctors, reporters, mediums, reformers, performers, servants, and people trapped between institutions all have a place.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "masked-patron",
                "Masked patron from the season rooms",
                "plot_role",
                "A patron tied to the impossible murder and the occult society ledger.",
                "Society scenes, blackmail, and class pressure follow their card across the room.",
                related_material_slug="impossible-murder",
            ),
            BlueprintWanted(
                "police-informant",
                "Police informant on the docks",
                "connection",
                "A witness who knows enough to be useful and frightened.",
                "Factory, crime, and police-court scenes all have reasons to protect or expose them.",
                related_material_slug="city-institutions",
            ),
            BlueprintWanted(
                "rival-medium",
                "Rival medium with the wrong ghost",
                "rival",
                "An occult rival whose testimony can ruin Mira or solve the case.",
                "Seances, fraud accusations, debt, and supernatural ambiguity sit on the same table.",
                related_material_slug="occult-rules",
            ),
            BlueprintWanted(
                "factory-witness",
                "Factory witness at the debut",
                "event_role",
                "A worker who should not have been in the locked room but saw the key moment.",
                "Class pressure, protection, press, and reform politics will all find them.",
                related_material_slug="impossible-murder",
            ),
            BlueprintWanted(
                "disgraced-fiance",
                "Disgraced fiance with a broken alibi",
                "relationship",
                "A social tie whose public fall makes the murder personal.",
                "Romance optional; reputation damage required.",
                related_material_slug="premise",
            ),
        ),
    ),
    ProgramBlueprint(
        slug="wayfarer-station",
        name="Wayfarer Station",
        role_slug="director",
        role_name="Director",
        is_admin=True,
        characters=(
            BlueprintCharacter(
                "mara-voss",
                "Mara Voss",
                "Station marshal enforcing laws nobody funded and everyone needs.",
                "Authority is a thin wall.",
            ),
            BlueprintCharacter(
                "jace-ren",
                "Jace Ren",
                "Smuggler with a cargo hold full of favors and one missing convoy marker.",
                "Every route has a ghost.",
            ),
            BlueprintCharacter(
                "sol-kade",
                "Sol Kade",
                "Engineer keeping life support honest while admin sells optimism.",
                "Bolts before speeches.",
            ),
            BlueprintCharacter(
                "nima-cho",
                "Nima Cho",
                "Medic triaging scarcity, radiation sickness, and people who lie about exposure.",
                "Vitals are negotiations.",
            ),
            BlueprintCharacter(
                "oren-hale",
                "Oren Hale",
                "Corporate envoy sent to audit losses before rescue costs money.",
                "Accountability travels first class.",
            ),
            BlueprintCharacter(
                "talia-ix",
                "Talia IX",
                "Archivist born station-side who knows which levels were erased from maps.",
                "Memory needs maintenance.",
            ),
            BlueprintCharacter(
                "vesper-lune",
                "Vesper Lune",
                "Performer whose market-deck stage hears every faction's private version.",
                "Songs travel farther than orders.",
            ),
            BlueprintCharacter(
                "rio-vale",
                "Rio Vale",
                "Quartermaster rationing air filters, medicine, and the truth.",
                "Supply is a language.",
            ),
        ),
        boards=(
            BlueprintBoard(
                "docking-ring",
                "Docking Ring",
                "location",
                "Airlocks, customs booths, missing convoy flags, and ships that arrive too quiet.",
                "Arrival scenes, smuggling, rescue pressure, and frontier law.",
            ),
            BlueprintBoard(
                "med-bay",
                "Med Bay",
                "location",
                "Crowded cots, exposure monitors, rationed medicine, and secrets under gloves.",
                "Medical pressure, triage, quarantine, and vulnerable alliances.",
            ),
            BlueprintBoard(
                "market-deck",
                "Market Deck",
                "location",
                "Stalls, performers, repair brokers, debt holders, and rumors traded by the cup.",
                "Social scenes, barter, found family, and public pressure.",
            ),
            BlueprintBoard(
                "admin-control",
                "Admin Control",
                "location",
                "Status boards, supply math, corporate calls, and people editing the crisis language.",
                "Authority, logistics, audits, public statements, and station politics.",
            ),
            BlueprintBoard(
                "archive-level",
                "Archive Level",
                "location",
                "Old maps, sealed memory banks, forbidden levels, and files that know the signal.",
                "Research, history, hidden routes, and strange-frontier mysteries.",
            ),
            BlueprintBoard(
                "chart-table",
                "Chart Table",
                "desk",
                "Station roles, scarcity ledgers, signal leads, open calls, and frontier plotting.",
                "Bring ration math, route rumors, debt contracts, missing people, and the messages nobody wants admin to hear.",
            ),
        ),
        materials=(
            BlueprintMaterial(
                "premise",
                "Premise: Edge Of The Chart",
                "premise",
                "Wayfarer Station survives at the edge of known space, where fragile law, limited supplies, and contested memory shape every bargain.",
                "The station is too remote to be comfortable and too useful to abandon. Crew, smugglers, medics, engineers, envoys, archivists, performers, quartermasters, station-born guides, and travelers all depend on systems that were never meant to hold this many secrets.",
            ),
            BlueprintMaterial(
                "missing-convoy",
                "Current Chapter: Missing Convoy",
                "event",
                "A supply convoy vanishes after transmitting an encrypted signal from outside the chart.",
                "The opening chapter brings docking delays, ration math, corporate audits, rescue arguments, archived maps, medical exposure risks, and one signal that may be a distress call or an invitation.",
            ),
            BlueprintMaterial(
                "station-law",
                "Station Law",
                "guide",
                "Law on Wayfarer is practical, fragile, and always under supply pressure.",
                "Customs, ration rules, quarantine orders, salvage claims, debt contracts, and marshal warrants create choices before they create answers.",
            ),
            BlueprintMaterial(
                "scarcity-ledger",
                "Scarcity Ledger",
                "guide",
                "Supplies are a story engine, not bookkeeping homework.",
                "Air filters, medicine, coolant, fuel, data access, berth space, and safe passage can all create relationships, favors, resentment, and public choices.",
            ),
            BlueprintMaterial(
                "application-guide",
                "Application Guide",
                "application",
                "Tell us what keeps them useful on the station, what they owe, and why the signal matters.",
                "Crew, smugglers, medics, engineers, corporate envoys, archivists, performers, quartermasters, station-born locals, debt holders, and convoy survivors all have room to move.",
            ),
        ),
        wanted=(
            BlueprintWanted(
                "debt-holder",
                "Debt holder with an air-filter contract",
                "faction_need",
                "Someone whose legal claim becomes dangerous when supplies run low.",
                "Station law, market-deck favors, and moral compromise all tighten when supplies run low.",
                related_material_slug="scarcity-ledger",
            ),
            BlueprintWanted(
                "corporate-auditor",
                "Corporate auditor who arrived before rescue",
                "event_role",
                "An envoy measuring losses while people still hope for survivors.",
                "Admin-control pressure, public anger, and accountability all follow their clipboard.",
                related_material_slug="missing-convoy",
            ),
            BlueprintWanted(
                "missing-pilot",
                "Missing pilot's partner on the docking ring",
                "relationship",
                "A personal tie to the convoy that turns logistics into grief.",
                "Rescue pressure, marshal scenes, and impossible choices get personal fast.",
                related_material_slug="missing-convoy",
            ),
            BlueprintWanted(
                "forbidden-level-witness",
                "Forbidden-level witness",
                "plot_role",
                "A station-born face who saw the signal route on a sealed archive map.",
                "Archive, market, admin, and signal trouble all lead back to what they saw.",
                related_material_slug="premise",
            ),
            BlueprintWanted(
                "alien-signal-translator",
                "Signal translator with an old war debt",
                "connection",
                "A specialist who can read part of the transmission but not safely alone.",
                "Research, trust, pressure, and frontier weirdness all need someone who can read the warning.",
                related_material_slug="missing-convoy",
            ),
        ),
    ),
)


DEFAULT_REALM_INTERACTIONS: tuple[InteractionSeed, ...] = (
    InteractionSeed(
        slug="pressure-lane-finder",
        title="Pressure Lane Finder",
        interaction_type="quiz",
        placement="application",
        summary="A quick lens for choosing where a new face feels most playable.",
        body=(
            "Use this as a soft nudge before applying. It is not binding; it helps writers "
            "and directors see whether the concept wants school politics, field work, "
            "Brotherhood pressure, or civilian fallout."
        ),
        result_mode="weighted",
        questions=(
            InteractionQuestionSeed(
                "When the world turns against mutants, where does your face first move?",
                "Pick the pressure that feels most useful for your opening threads.",
                (
                    InteractionOptionSeed(
                        "school",
                        "Toward the school",
                        "Found family, mentorship, student pressure, and safer walls.",
                        "x-men",
                    ),
                    InteractionOptionSeed(
                        "field",
                        "Into the field",
                        "Rescue work, hard choices, and fast-moving mission fallout.",
                        "mission-ready",
                    ),
                    InteractionOptionSeed(
                        "brotherhood",
                        "Toward sharper politics",
                        "Radicalization, protection through force, and ideological heat.",
                        "brotherhood",
                    ),
                    InteractionOptionSeed(
                        "civilian",
                        "Into the civilian blast radius",
                        "Families, public panic, and the cost of being known.",
                        "political",
                    ),
                ),
            ),
        ),
    ),
)


STUDIO_REALM_INTERACTIONS: dict[str, tuple[InteractionSeed, ...]] = {
    "hp-universe": (
        InteractionSeed(
            slug="house-pressure-sorting",
            title="House Pressure Sorting",
            interaction_type="quiz",
            placement="application",
            summary="A sorting-style prompt for the kind of school-year trouble your face courts.",
            body=(
                "This is less about choosing a canon house and more about the narrative pressure "
                "your character brings to the castle."
            ),
            result_mode="weighted",
            questions=(
                InteractionQuestionSeed(
                    "What would get your face into trouble before breakfast?",
                    "Choose the hook that sounds most fun to write.",
                    (
                        InteractionOptionSeed(
                            "bravery",
                            "Running toward a cursed door",
                            "Instinct, loyalty, and courage with poor timing.",
                            "gryffindor",
                        ),
                        InteractionOptionSeed(
                            "ambition",
                            "Making a private bargain",
                            "Reputation, leverage, and secrets kept too well.",
                            "slytherin",
                        ),
                        InteractionOptionSeed(
                            "curiosity",
                            "Reading the forbidden marginalia",
                            "Research, pattern-hunting, and consequences with footnotes.",
                            "ravenclaw",
                        ),
                        InteractionOptionSeed(
                            "loyalty",
                            "Covering for a friend",
                            "Care, stubbornness, and community pressure.",
                            "hufflepuff",
                        ),
                    ),
                ),
            ),
        ),
    ),
    "jurassic-park-universe": (
        InteractionSeed(
            slug="incident-role-poll",
            title="Incident Role Poll",
            interaction_type="poll",
            placement="general",
            summary="Vote on what kind of opening incident the island should spotlight next.",
            body=(
                "Directors can use this as a temperature check before staging the next island beat."
            ),
            result_mode="aggregate",
            questions=(
                InteractionQuestionSeed(
                    "Which incident lane should get the next event spotlight?",
                    "Pick the kind of pressure you would most like to write into.",
                    (
                        InteractionOptionSeed(
                            "supply-run",
                            "A supply run goes quiet",
                            "Radio silence, mud, and something moving near the crates.",
                        ),
                        InteractionOptionSeed(
                            "guest-tour",
                            "A guest tour loses power",
                            "Public-facing panic where everyone has a camera.",
                        ),
                        InteractionOptionSeed(
                            "lab-breach",
                            "A lab breach asks for volunteers",
                            "Contained science trouble that may not stay contained.",
                        ),
                    ),
                ),
            ),
        ),
    ),
    "rl-nyc": (
        InteractionSeed(
            slug="borough-energy-survey",
            title="Borough Energy Survey",
            interaction_type="survey",
            placement="application",
            summary="A quick vibe check for where a new NYC character creates pressure.",
            body="A small director aid for connecting applicants to neighborhoods and social circles.",
            result_mode="confirmation",
            questions=(
                InteractionQuestionSeed(
                    "What kind of city pressure should find your face first?",
                    "Choose the lane that would make the first three threads easy.",
                    (
                        InteractionOptionSeed(
                            "creative",
                            "Creative scene chaos",
                            "Openings, auditions, collabs, rivals, and late-night favors.",
                        ),
                        InteractionOptionSeed(
                            "work",
                            "Work-life collision",
                            "Ambition, burnout, bosses, shifts, side hustles, and rent.",
                        ),
                        InteractionOptionSeed(
                            "neighborhood",
                            "Neighborhood history",
                            "Families, regulars, grudges, and everyone knowing your business.",
                        ),
                    ),
                ),
            ),
        ),
    ),
    "rl-small-town": (
        InteractionSeed(
            slug="founders-week-vote",
            title="Founder's Week Vote",
            interaction_type="poll",
            placement="general",
            summary="Choose the next public pressure point for the time capsule event.",
            body="A simple civic vote directors can turn into the next town-wide prompt.",
            result_mode="aggregate",
            questions=(
                InteractionQuestionSeed(
                    "Where should the time capsule letter cause trouble next?",
                    "Pick the public stage that sounds most combustible.",
                    (
                        InteractionOptionSeed(
                            "diner",
                            "The diner breakfast rush",
                            "Gossip, receipts, and three tables pretending not to listen.",
                        ),
                        InteractionOptionSeed(
                            "council",
                            "The town council meeting",
                            "Minutes, motions, microphones, and long memories.",
                        ),
                        InteractionOptionSeed(
                            "festival",
                            "The Founder's Week parade",
                            "Floats, sponsors, old grudges, and everyone outside.",
                        ),
                    ),
                ),
            ),
        ),
    ),
}


DEFAULT_CLAIM_TYPES: tuple[ClaimTypeSeed, ...] = (
    ClaimTypeSeed(
        "face",
        "Face Claim",
        "face",
        "Public actor, model, or visual reference used by a face.",
        is_required=True,
        is_exclusive=True,
    ),
    ClaimTypeSeed(
        "faction",
        "Faction Claim",
        "faction",
        "The character's primary political or story allegiance.",
        is_required=True,
    ),
    ClaimTypeSeed(
        "power",
        "Power Claim",
        "ability",
        "The mutation, ability lane, or signature capability directors should track.",
    ),
)


DEFAULT_APPLICATION_FIELDS: tuple[ApplicationFieldSeed, ...] = (
    ApplicationFieldSeed(
        "face_claim",
        "Face claim",
        "text",
        "The public visual reference you want directors to reserve.",
        placeholder="Example: Ian McKellen",
        maps_to_claim_type_slug="face",
        is_required=True,
    ),
    ApplicationFieldSeed(
        "faction_claim",
        "Primary faction",
        "select",
        "Choose the story lane that should shape staff review and plotting defaults.",
        options=("X-Men", "Brotherhood", "United Nations", "Evil Lab", "Civilian"),
        maps_to_claim_type_slug="faction",
        is_required=True,
    ),
    ApplicationFieldSeed(
        "power_claim",
        "Power or role claim",
        "text",
        "A concise mutation, ability, or production role directors should avoid duplicating.",
        placeholder="Metal manipulation, evacuation medic, UN analyst",
        maps_to_claim_type_slug="power",
    ),
)


DEFAULT_CLAIMS: tuple[ClaimSeed, ...] = (
    ClaimSeed("face", "magneto", "magneto-visual", "Magneto visual reference"),
    ClaimSeed("face", "rogue", "rogue-visual", "Rogue visual reference"),
    ClaimSeed("face", "storm", "storm-visual", "Storm visual reference"),
    ClaimSeed("faction", "magneto", "brotherhood", "Brotherhood"),
    ClaimSeed("faction", "rogue", "x-men", "X-Men"),
    ClaimSeed("faction", "storm", "x-men", "X-Men", status="available"),
)


STUDIO_CLAIM_TYPES: dict[str, tuple[ClaimTypeSeed, ...]] = {
    "hp-universe": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed("house", "House Claim", "faction", "School house or social lane.", True),
        ClaimTypeSeed(
            "year", "Year Claim", "rank", "Student year, graduate status, or faculty role."
        ),
    ),
    "jurassic-park-universe": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "department",
            "Department Claim",
            "occupation",
            "Park, lab, security, or guest-facing department.",
            True,
        ),
        ClaimTypeSeed(
            "clearance",
            "Clearance Claim",
            "access",
            "What this face is allowed to know before things go wrong.",
        ),
    ),
    "rl-nyc": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "occupation",
            "Occupation Claim",
            "occupation",
            "Work, art, nightlife, or survival lane.",
        ),
        ClaimTypeSeed("borough", "Borough Claim", "location", "Primary neighborhood pressure."),
    ),
    "rl-small-town": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "family", "Family Claim", "relationship", "Local family, newcomer tie, or town lineage."
        ),
        ClaimTypeSeed(
            "business", "Business Claim", "occupation", "Shop, service, civic office, or workplace."
        ),
    ),
    "harbor-society": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "family",
            "Family Claim",
            "relationship",
            "Old family, newcomer tie, or married-in pressure.",
        ),
        ClaimTypeSeed(
            "club_role",
            "Club Role Claim",
            "access",
            "Member, staff, guest, donor, or applicant posture.",
        ),
        ClaimTypeSeed(
            "business",
            "Business Claim",
            "occupation",
            "Public workplace, civic office, or service lane.",
        ),
    ),
    "signal-creek": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "town_tie",
            "Town Tie Claim",
            "relationship",
            "Local, returnee, outsider, official, or researcher lane.",
        ),
        ClaimTypeSeed(
            "belief",
            "Belief Claim",
            "faction",
            "Skeptic, believer, touched, coverup, or undecided posture.",
        ),
        ClaimTypeSeed(
            "phenomenon",
            "Phenomenon Claim",
            "power",
            "Optional strange effect, symptom, or memory anomaly.",
        ),
    ),
    "nocturne-row": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "species",
            "Species Claim",
            "species",
            "Human, vampire, witch, werewolf, hunter, or other approved lane.",
        ),
        ClaimTypeSeed(
            "faction",
            "Faction Claim",
            "faction",
            "Council, coven, pack, hunter cell, press, hospital, or unaffiliated.",
        ),
        ClaimTypeSeed(
            "boundary",
            "Boundary Claim",
            "content",
            "Power, consent, or mature-content boundary directors should honor.",
        ),
    ),
    "crownfall": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "house",
            "House Claim",
            "faction",
            "Noble house, temple, archive, border, merchant, or rebel tie.",
        ),
        ClaimTypeSeed(
            "rank",
            "Rank Claim",
            "rank",
            "Public office, military rank, court role, or social station.",
        ),
        ClaimTypeSeed(
            "magic",
            "Magic Claim",
            "power",
            "Optional magical discipline, omen tie, or anti-magic posture.",
        ),
    ),
    "afterlight-accord": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "role_archetype",
            "Inherited Role Claim",
            "role",
            "Heir, exile, monster, archivist, reformer, runner, prophet, or traitor lane.",
        ),
        ClaimTypeSeed(
            "faction",
            "Faction Claim",
            "faction",
            "Accord council, academy, archive, rebels, gate runners, or unaffiliated.",
        ),
        ClaimTypeSeed(
            "branch_wound",
            "Branch Wound Claim",
            "relationship",
            "The old-ending pressure this face carries into play.",
        ),
    ),
    "brightline": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "career",
            "Career Claim",
            "occupation",
            "Performer, fixer, patron, press, producer, venue, legal, or crew lane.",
        ),
        ClaimTypeSeed(
            "image", "Image Claim", "reputation", "How the public thinks they know this face."
        ),
        ClaimTypeSeed(
            "industry_tie",
            "Industry Tie Claim",
            "relationship",
            "Studio, club, magazine, charity, court, or patron connection.",
        ),
    ),
    "emberhouse": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed("house", "House Claim", "faction", "Academy house, clan, or sponsor lane."),
        ClaimTypeSeed(
            "rank", "Rank Claim", "rank", "Candidate rank, instructor role, or council authority."
        ),
        ClaimTypeSeed(
            "trial_boundary",
            "Trial Boundary Claim",
            "content",
            "Safety, consent, or pressure limit directors should honor.",
        ),
    ),
    "gaslight-ward": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "class_posture",
            "Class Posture Claim",
            "class",
            "Society, worker, criminal, professional, or liminal status.",
        ),
        ClaimTypeSeed(
            "institution",
            "Institution Claim",
            "faction",
            "Newspaper, police court, factory, society, hospital, or occult tie.",
        ),
        ClaimTypeSeed(
            "secret_bargain",
            "Secret Bargain Claim",
            "relationship",
            "Occult debt, patronage, blackmail, or private obligation.",
        ),
    ),
    "wayfarer-station": (
        ClaimTypeSeed(
            "face",
            "Face Claim",
            "face",
            "Public visual reference.",
            is_required=True,
            is_exclusive=True,
        ),
        ClaimTypeSeed(
            "station_role",
            "Station Role Claim",
            "occupation",
            "Crew, smuggler, medic, engineer, envoy, archivist, performer, or quartermaster.",
        ),
        ClaimTypeSeed(
            "scarcity",
            "Scarcity Claim",
            "resource",
            "Supply, access, debt, route, or exposure pressure.",
        ),
        ClaimTypeSeed(
            "signal_tie",
            "Signal Tie Claim",
            "mystery",
            "How this face touches the missing convoy or encrypted signal.",
        ),
    ),
}


STUDIO_APPLICATION_FIELDS: dict[str, tuple[ApplicationFieldSeed, ...]] = {
    "hp-universe": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "house_claim",
            "House or lane",
            "select",
            "The school pressure lane that best fits your concept.",
            options=("Gryffindor", "Slytherin", "Ravenclaw", "Hufflepuff", "Faculty", "Hogsmeade"),
            maps_to_claim_type_slug="house",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "year_claim",
            "Year or role",
            "text",
            "Student year, graduate status, faculty role, or adult tie.",
            placeholder="Seventh year, professor, shopkeeper",
            maps_to_claim_type_slug="year",
        ),
    ),
    "jurassic-park-universe": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "department_claim",
            "Department",
            "select",
            "Where this character creates immediate island pressure.",
            options=(
                "Paleobiology",
                "Security",
                "Guest Services",
                "Operations",
                "Executive",
                "Visitor",
            ),
            maps_to_claim_type_slug="department",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "clearance_claim",
            "Clearance",
            "text",
            "What they are allowed to know before the incident escalates.",
            placeholder="Guest-only, paddock access, lab access",
            maps_to_claim_type_slug="clearance",
        ),
    ),
    "rl-nyc": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "occupation_claim",
            "Occupation",
            "text",
            "The work or creative lane people know them by.",
            placeholder="Bartender, stylist, gallery assistant",
            maps_to_claim_type_slug="occupation",
        ),
        ApplicationFieldSeed(
            "borough_claim",
            "Borough",
            "select",
            "Where their day-to-day story tends to orbit.",
            options=(
                "Manhattan",
                "Brooklyn",
                "Queens",
                "The Bronx",
                "Staten Island",
                "Jersey-adjacent",
            ),
            maps_to_claim_type_slug="borough",
        ),
    ),
    "rl-small-town": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "family_claim",
            "Family or local tie",
            "text",
            "A lineage, newcomer tie, or relationship pressure the town recognizes.",
            placeholder="The Vale family, returning cousin, new arrival",
            maps_to_claim_type_slug="family",
        ),
        ApplicationFieldSeed(
            "business_claim",
            "Business or civic role",
            "text",
            "A workplace, shop, church committee, volunteer role, or office.",
            placeholder="Diner owner, council aide, mechanic",
            maps_to_claim_type_slug="business",
        ),
    ),
    "harbor-society": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "family_claim",
            "Family or town tie",
            "text",
            "Where the town places this face socially.",
            placeholder="Old family, married-in, newcomer, returnee",
            maps_to_claim_type_slug="family",
        ),
        ApplicationFieldSeed(
            "club_role_claim",
            "Club posture",
            "select",
            "How they touch the Shoreline Club and Founders Gala.",
            options=("Member", "Staff", "Guest", "Donor", "Applicant", "Critic"),
            maps_to_claim_type_slug="club_role",
        ),
    ),
    "signal-creek": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "town_tie_claim",
            "Town tie",
            "select",
            "How this face enters the mystery.",
            options=("Local", "Returnee", "Researcher", "Official", "Skeptic", "Believer"),
            maps_to_claim_type_slug="town_tie",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "belief_claim",
            "Belief posture",
            "text",
            "What they think is happening before the signal proves otherwise.",
            maps_to_claim_type_slug="belief",
        ),
    ),
    "nocturne-row": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "species_claim",
            "Species or human lane",
            "select",
            "The public roster lane directors should review.",
            options=("Human", "Vampire", "Witch", "Werewolf", "Hunter", "Other approved"),
            maps_to_claim_type_slug="species",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "faction_claim",
            "Faction pressure",
            "text",
            "Council, coven, pack, hunter cell, press, hospital, or unaffiliated pressure.",
            maps_to_claim_type_slug="faction",
        ),
    ),
    "crownfall": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "house_claim",
            "House or faction",
            "text",
            "The institution that creates immediate pressure for this face.",
            maps_to_claim_type_slug="house",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "rank_claim",
            "Rank or role",
            "text",
            "Their public role in the succession crisis.",
            maps_to_claim_type_slug="rank",
        ),
    ),
    "afterlight-accord": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "role_archetype_claim",
            "Inherited role",
            "select",
            "The duty, reputation, or old promise this face carries.",
            options=(
                "Heir",
                "Exile",
                "Converted monster",
                "Archivist",
                "Reformer",
                "Runner",
                "Prophet",
                "Traitor",
            ),
            maps_to_claim_type_slug="role_archetype",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "faction_claim",
            "Faction pressure",
            "text",
            "Accord, academy, archive, rebel, gate, or unaffiliated pressure.",
            maps_to_claim_type_slug="faction",
        ),
    ),
    "brightline": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "career_claim",
            "Career lane",
            "text",
            "How the industry knows this face.",
            placeholder="Performer, publicist, producer, critic, lawyer, assistant",
            maps_to_claim_type_slug="career",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "image_claim",
            "Public image",
            "text",
            "The story people think they know about this face.",
            maps_to_claim_type_slug="image",
        ),
    ),
    "emberhouse": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "house_claim",
            "House or sponsor lane",
            "text",
            "Where the academy places this face before the trial starts.",
            maps_to_claim_type_slug="house",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "trial_boundary_claim",
            "Trial boundary",
            "text",
            "A safety, consent, or pressure note directors should honor.",
            maps_to_claim_type_slug="trial_boundary",
        ),
    ),
    "gaslight-ward": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "class_posture_claim",
            "Class posture",
            "select",
            "The public respectability lane this face moves through.",
            options=("Society", "Worker", "Criminal", "Professional", "Occult", "Liminal"),
            maps_to_claim_type_slug="class_posture",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "institution_claim",
            "Institution tie",
            "text",
            "Newspaper, court, factory, society, hospital, occult, or theater pressure.",
            maps_to_claim_type_slug="institution",
        ),
    ),
    "wayfarer-station": (
        ApplicationFieldSeed(
            "face_claim",
            "Face claim",
            "text",
            "The visual reference you want directors to reserve.",
            maps_to_claim_type_slug="face",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "station_role_claim",
            "Station role",
            "text",
            "The work, access, or public lane that makes this face necessary.",
            placeholder="Marshal, smuggler, engineer, medic, envoy, archivist",
            maps_to_claim_type_slug="station_role",
            is_required=True,
        ),
        ApplicationFieldSeed(
            "scarcity_claim",
            "Scarcity pressure",
            "text",
            "The supply, access, debt, route, or exposure issue touching this face.",
            maps_to_claim_type_slug="scarcity",
        ),
    ),
}


def seed_demo_forum(repo: ForumRepository) -> DemoSeed:
    """Seed a small X-Men themed play-by-post community for local development.

    The seed is idempotent so local file-backed development can restart without
    duplicating boards, characters, or sample posts.
    """

    community = _ensure_community_media_defaults(
        repo,
        repo.seed_default_community("X-Men Apocalypse"),
        X_MEN_MEDIA,
    )
    community = repo.update_community_launch_status(community.id, "public-preview")
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
    _seed_studio_network_programs(repo, user)
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
    inactive_user = _get_or_create(
        lambda: repo.get_user_by_email("inactive@example.com"),
        lambda: repo.create_user("inactive@example.com", "dev-password-hash"),
    )
    inactive_membership = _get_or_create(
        lambda: repo.get_membership_for_user(community.id, inactive_user.id),
        lambda: repo.create_membership(
            community.id,
            inactive_user.id,
            member_role.id,
            "sleepingstar",
            "Sleeping Star",
        ),
    )
    repo.connection.execute(
        """
        UPDATE community_memberships
        SET is_active = 0
        WHERE community_id = ? AND id = ?
        """,
        (community.id, inactive_membership.id),
    )
    repo.connection.commit()

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
    sleeping_star = _get_or_create(
        lambda: repo.get_character_by_slug(community.id, "sleeping-star"),
        lambda: repo.create_character(
            community.id,
            inactive_membership.id,
            "sleeping-star",
            "Sleeping Star",
            summary="Inactive QA face used to prove dormant memberships cannot act.",
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
    sleeping_star = repo.update_character_application_status(
        community.id,
        sleeping_star.id,
        "accepted",
    )

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
    sleeping_star = _ensure_character_identity(
        repo,
        community.id,
        sleeping_star,
        tagline="Dormant by design.",
        accent_color="",
        post_profile_variant="bio",
        post_accent_style="soft",
        post_border_style="hairline",
        post_title_style="standard",
        post_density="calm",
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
    inactive_membership = repo.get_membership(community.id, inactive_membership.id)
    if inactive_membership.default_character_id is None:
        repo.set_default_character(community.id, inactive_membership.id, sleeping_star.id)

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
    for board in (
        xavier_institute,
        new_york,
        mutant_underground,
        b24_facilities,
        united_nations,
        genosha,
    ):
        _ensure_board_media_default(repo, community.id, board, X_MEN_BOARD_MEDIA[board.slug])
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
    _seed_discovery_profile(
        repo,
        community.id,
        DISCOVERY_PROFILE_SEEDS.get("x-men-apocalypse"),
    )
    _seed_realm_interactions(repo, community.id, DEFAULT_REALM_INTERACTIONS)
    _seed_intake_claims(
        repo,
        community.id,
        claim_types=DEFAULT_CLAIM_TYPES,
        application_fields=DEFAULT_APPLICATION_FIELDS,
    )
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
    _seed_character_claims(repo, community.id, DEFAULT_CLAIMS)

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


def _seed_studio_network_programs(repo: ForumRepository, user: User) -> None:
    ensure_valid_program_blueprints(STUDIO_NETWORK_PROGRAMS)
    for program in STUDIO_NETWORK_PROGRAMS:
        community = _ensure_studio_program_community(repo, program)
        media_seed = STUDIO_PROGRAM_MEDIA.get(program.slug)
        if media_seed is not None:
            community = _ensure_community_media_defaults(repo, community, media_seed)
        if program.theme is not None:
            repo.upsert_default_theme(
                community.id,
                slug=program.theme.slug,
                name=program.theme.name,
                tokens_json=json.dumps(
                    blueprint_theme_tokens(program.theme),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
        role = _get_or_create(
            lambda program=program, community=community: repo.get_role_by_slug(
                community.id,
                program.role_slug,
            ),
            lambda program=program, community=community: repo.create_role(
                community.id,
                program.role_slug,
                program.role_name,
                is_admin=program.is_admin,
            ),
        )
        membership = _get_or_create(
            lambda community=community: repo.get_membership_for_user(community.id, user.id),
            lambda community=community, role=role: repo.create_membership(
                community.id,
                user.id,
                role.id,
                "starlane",
                "Lane",
            ),
        )
        original_writer_memberships = (
            _seed_original_premise_writer_memberships(repo, community, membership)
            if program.slug in ORIGINAL_PREMISE_SEED_SLUGS
            else {}
        )
        preferred_defaults: dict[int, int] = {}
        default_character: Character | None = None
        for index, character_seed in enumerate(program.characters):
            character_membership = _original_premise_character_membership(
                character_seed.slug,
                index,
                membership,
                original_writer_memberships,
            )
            character = _get_or_create(
                lambda community=community, character_seed=character_seed: (
                    repo.get_character_by_slug(
                        community.id,
                        character_seed.slug,
                    )
                ),
                lambda community=community, character_membership=character_membership, character_seed=character_seed: (
                    repo.create_character(
                        community.id,
                        character_membership.id,
                        character_seed.slug,
                        character_seed.name,
                        summary=character_seed.summary,
                        tagline=character_seed.tagline,
                    )
                ),
            )
            preferred_defaults.setdefault(character_membership.id, character.id)
            character = repo.transfer_character_membership(
                community.id,
                character.id,
                character_membership.id,
                make_default=index == 0,
            )
            character = _ensure_character_identity(
                repo,
                community.id,
                character,
                tagline=character_seed.tagline,
            )
            if index == 0:
                default_character = character

        membership = repo.get_membership(community.id, membership.id)
        if membership.default_character_id is None and default_character is not None:
            repo.set_default_character(community.id, membership.id, default_character.id)
        for membership_id, character_id in preferred_defaults.items():
            assigned_membership = repo.get_membership(community.id, membership_id)
            if assigned_membership.default_character_id is None:
                repo.set_default_character(community.id, membership_id, character_id)

        for index, board_seed in enumerate(program.boards, start=1):
            board = _ensure_board(
                repo,
                community.id,
                board_seed.slug,
                board_seed.name,
                board_seed.description,
                index * 10,
                board_kind=board_seed.board_kind,
                tagline=board_seed.tagline,
                image_url=board_seed.image_url or None,
                image_alt=board_seed.image_alt,
                image_treatment=board_seed.image_treatment,
                image_focal_point=board_seed.image_focal_point,
                image_overlay=board_seed.image_overlay,
            )
            media_seed = STUDIO_PROGRAM_BOARD_MEDIA.get(program.slug, {}).get(board_seed.slug)
            if media_seed is not None:
                _ensure_board_media_default(repo, community.id, board, media_seed)
        materials_by_slug: dict[str, Material] = {}
        for index, material_seed in enumerate(program.materials, start=1):
            material = _ensure_material(
                repo,
                community.id,
                material_seed.slug,
                material_seed.title,
                material_type=material_seed.material_type,
                summary=material_seed.summary,
                body=material_seed.body,
                sort_order=index * 10,
                is_featured=index == 1,
            )
            materials_by_slug[material_seed.slug] = material
        for wanted_seed in program.wanted:
            related_material_id = None
            if wanted_seed.related_material_slug:
                related_material_id = materials_by_slug[wanted_seed.related_material_slug].id
            _get_or_create(
                lambda community=community, wanted_seed=wanted_seed: repo.get_wanted_ad_by_slug(
                    community.id,
                    wanted_seed.slug,
                ),
                lambda community=community, membership=membership, default_character=default_character, wanted_seed=wanted_seed, related_material_id=related_material_id: (
                    repo.create_wanted_ad(
                        community.id,
                        membership.id,
                        wanted_seed.slug,
                        wanted_seed.title,
                        creator_character_id=(
                            default_character.id if default_character is not None else None
                        ),
                        related_material_id=related_material_id,
                        wanted_type=wanted_seed.wanted_type,
                        summary=wanted_seed.summary,
                        body=wanted_seed.body,
                    )
                ),
            )
        _seed_realm_interactions(
            repo,
            community.id,
            STUDIO_REALM_INTERACTIONS.get(program.slug, ()),
        )
        _seed_intake_claims(
            repo,
            community.id,
            claim_types=STUDIO_CLAIM_TYPES.get(program.slug, ()),
            application_fields=STUDIO_APPLICATION_FIELDS.get(program.slug, ()),
        )
        _seed_discovery_profile(repo, community.id, DISCOVERY_PROFILE_SEEDS.get(program.slug))
        if program.slug in ORIGINAL_PREMISE_SEED_SLUGS:
            _seed_original_premise_depth(repo, community, program, membership)


def _seed_original_premise_writer_memberships(
    repo: ForumRepository,
    community: Community,
    director_membership: CommunityMembership,
) -> dict[str, CommunityMembership]:
    member_role = _get_or_create(
        lambda: repo.get_role_by_slug(community.id, "member"),
        lambda: repo.create_role(community.id, "member", "Member"),
    )
    memberships: dict[str, CommunityMembership] = {"director": director_membership}
    for writer_seed in ORIGINAL_PREMISE_WRITER_SEEDS:
        writer = _get_or_create(
            lambda writer_seed=writer_seed: repo.get_user_by_email(writer_seed.email),
            lambda writer_seed=writer_seed: repo.create_user(
                writer_seed.email,
                "dev-password-hash",
            ),
        )
        memberships[writer_seed.username] = _get_or_create(
            lambda community=community, writer=writer: repo.get_membership_for_user(
                community.id,
                writer.id,
            ),
            lambda community=community, writer=writer, writer_seed=writer_seed: (
                repo.create_membership(
                    community.id,
                    writer.id,
                    member_role.id,
                    writer_seed.username,
                    writer_seed.display_name,
                )
            ),
        )
    return memberships


def _original_premise_character_membership(
    _character_slug: str,
    index: int,
    director_membership: CommunityMembership,
    writer_memberships: dict[str, CommunityMembership],
) -> CommunityMembership:
    if not writer_memberships or index == 0:
        return director_membership
    writer_keys = tuple(writer.username for writer in ORIGINAL_PREMISE_WRITER_SEEDS)
    writer_key = writer_keys[(index - 1) % len(writer_keys)]
    return writer_memberships[writer_key]


def _ensure_studio_program_community(
    repo: ForumRepository,
    program: ProgramBlueprint,
) -> Community:
    try:
        community = repo.get_community_by_slug(program.slug)
    except LookupError:
        community = repo.create_community(program.slug, program.name)
    else:
        if community.name != program.name or community.slug != program.slug:
            community = repo.update_community_name_and_slug(
                community.id,
                slug=program.slug,
                name=program.name,
            )
    if community.launch_status != "public-preview":
        community = repo.update_community_launch_status(community.id, "public-preview")
    return community


def _ensure_community_media_defaults(
    repo: ForumRepository,
    community: Community,
    media_seed: CommunityMediaSeed,
) -> Community:
    mark_url = community.community_mark_url or media_seed.mark_url
    mark_alt = community.community_mark_alt
    if community.community_mark_url is None:
        mark_alt = media_seed.mark_alt
    hero_url = community.world_hero_image_url or media_seed.hero_url
    hero_alt = community.world_hero_image_alt
    if community.world_hero_image_url is None:
        hero_alt = media_seed.hero_alt
    hero_treatment = community.world_hero_treatment
    hero_focal_point = community.world_hero_focal_point
    hero_overlay = community.world_hero_overlay
    hero_height = community.world_hero_height
    if community.world_hero_image_url is None:
        hero_treatment = media_seed.hero_treatment
        hero_focal_point = media_seed.hero_focal_point
        hero_overlay = media_seed.hero_overlay
        hero_height = media_seed.hero_height
    if (
        mark_url == community.community_mark_url
        and mark_alt == community.community_mark_alt
        and hero_url == community.world_hero_image_url
        and hero_alt == community.world_hero_image_alt
        and hero_treatment == community.world_hero_treatment
        and hero_focal_point == community.world_hero_focal_point
        and hero_overlay == community.world_hero_overlay
        and hero_height == community.world_hero_height
    ):
        return community
    return repo.update_community_media(
        community.id,
        community_mark_url=mark_url,
        community_mark_alt=mark_alt,
        world_hero_image_url=hero_url,
        world_hero_image_alt=hero_alt,
        world_hero_treatment=hero_treatment,
        world_hero_focal_point=hero_focal_point,
        world_hero_overlay=hero_overlay,
        world_hero_height=hero_height,
    )


def _seed_original_premise_depth(
    repo: ForumRepository,
    community: Community,
    program: ProgramBlueprint,
    membership: CommunityMembership,
) -> None:
    characters = [
        repo.get_character_by_slug(community.id, character_seed.slug)
        for character_seed in program.characters[:4]
    ]
    boards = [
        repo.get_board_by_slug(community.id, board_seed.slug)
        for board_seed in program.boards
        if board_seed.board_kind in {"location", "community"}
    ][:3]
    if len(characters) < 3 or len(boards) < 2:
        return

    opening = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, boards[0].id, "opening-pressure"),
        lambda: repo.create_thread(
            community.id,
            boards[0].id,
            characters[0].id,
            "opening-pressure",
            "Opening pressure",
            summary=(
                f"{characters[0].name} pulls the first public thread into "
                f"{community.name}'s current premise."
            ),
            location=boards[0].name,
            timeline="Current chapter",
        ),
    )
    repo.set_thread_participants(
        community.id,
        opening.id,
        [characters[0].id, characters[1].id, characters[2].id],
    )
    _ensure_post(
        repo,
        community.id,
        opening.id,
        characters[0].id,
        (
            f"{characters[0].name} arrived at {boards[0].name} with the public "
            f"pressure of {community.name} already waiting in the room."
        ),
    )
    _ensure_post(
        repo,
        community.id,
        opening.id,
        characters[1].id,
        (
            f"{characters[1].name} answered with a practical offer, a private "
            "reservation, and one question that could turn into a scene."
        ),
    )

    followup = _get_or_create(
        lambda: repo.get_thread_by_slug(community.id, boards[1].id, "wanted-thread-start"),
        lambda: repo.create_thread(
            community.id,
            boards[1].id,
            characters[1].id,
            "wanted-thread-start",
            f"{boards[1].name} first-scene ask",
            summary=(
                f"A public ask at {boards[1].name} pulls {characters[2].name} "
                f"and {characters[3].name} toward {community.name}'s current chapter."
            ),
            location=boards[1].name,
            timeline="Current chapter",
        ),
    )
    repo.set_thread_participants(
        community.id,
        followup.id,
        [characters[1].id, characters[2].id, characters[3].id],
    )
    _ensure_post(
        repo,
        community.id,
        followup.id,
        characters[1].id,
        (
            f"{characters[1].name} left a note at {boards[1].name}: a clear "
            "opening for rivals, allies, witnesses, or relatives to answer."
        ),
    )
    _ensure_post(
        repo,
        community.id,
        followup.id,
        characters[2].id,
        (
            f"{characters[2].name} took the hook seriously enough to make it "
            "someone else's problem before the next scene could settle."
        ),
    )
    repo.watch_thread(community.id, followup.id, membership.id)
    repo.mark_thread_read(community.id, opening.id, membership.id)

    _seed_original_premise_character_claims(repo, community.id, program)


def _seed_original_premise_character_claims(
    repo: ForumRepository,
    community_id: int,
    program: ProgramBlueprint,
) -> None:
    claim_types = STUDIO_CLAIM_TYPES.get(program.slug, ())[:2]
    if not claim_types:
        return
    claims: list[ClaimSeed] = []
    for character_seed in program.characters[:3]:
        claims.extend(
            ClaimSeed(
                claim_type_seed.slug,
                character_seed.slug,
                f"{character_seed.slug}-{claim_type_seed.claim_kind}",
                f"{character_seed.name} {claim_type_seed.name}",
            )
            for claim_type_seed in claim_types
        )
    _seed_character_claims(repo, community_id, tuple(claims))


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
    image_treatment: str = "poster",
    image_focal_point: str = "center",
    image_overlay: str = "medium",
    is_private: bool = False,
) -> Board:
    try:
        return repo.get_board_by_slug(community_id, slug)
    except LookupError:
        return repo.create_board(
            community_id,
            slug,
            name,
            description,
            parent_board_id=parent_board_id,
            board_kind=board_kind,
            tagline=tagline,
            image_url=image_url,
            image_alt=image_alt,
            image_treatment=image_treatment,
            image_focal_point=image_focal_point,
            image_overlay=image_overlay,
            sort_order=sort_order,
            is_private=is_private,
        )


def _ensure_board_media_default(
    repo: ForumRepository,
    community_id: int,
    board: Board,
    media_seed: BoardMediaSeed,
) -> Board:
    if board.image_url is not None:
        return board
    return repo.update_board(
        community_id,
        board.id,
        name=board.name,
        description=board.description,
        sort_order=board.sort_order,
        parent_board_id=board.parent_board_id,
        board_kind=board.board_kind,
        sidebar_section=board.sidebar_section,
        tagline=board.tagline,
        image_url=media_seed.image_url,
        image_alt=media_seed.image_alt,
        image_treatment=media_seed.image_treatment,
        image_focal_point=media_seed.image_focal_point,
        image_overlay=media_seed.image_overlay,
        is_private=board.is_private,
        navigation_order=board.navigation_order,
        show_in_navigation=board.show_in_navigation,
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
    try:
        return repo.get_material_by_slug(community_id, slug)
    except LookupError:
        return repo.create_material(
            community_id,
            slug,
            title,
            material_type=material_type,
            summary=summary,
            body=body,
            status=status,
            sort_order=sort_order,
            is_featured=is_featured,
        )


def _seed_discovery_profile(
    repo: ForumRepository,
    community_id: int,
    seed: DiscoveryProfileSeed | None,
) -> None:
    if seed is None:
        return
    featured_event_material_id = None
    if seed.featured_event_material_slug is not None:
        try:
            featured_event_material_id = repo.get_material_by_slug(
                community_id,
                seed.featured_event_material_slug,
            ).id
        except LookupError:
            featured_event_material_id = None
    repo.upsert_discovery_profile(
        community_id,
        premise_archetype=seed.premise_archetype,
        play_engine=seed.play_engine,
        lore_aperture=seed.lore_aperture,
        access_model=seed.access_model,
        application_model=seed.application_model,
        age_rating=seed.age_rating,
        content_rating=seed.content_rating,
        activity_pace=seed.activity_pace,
        activity_expectation=seed.activity_expectation,
        forum_adjunct=seed.forum_adjunct,
        roster_posture=seed.roster_posture,
        catalog_pitch=seed.catalog_pitch,
        onboarding_pitch=seed.onboarding_pitch,
        staff_pick_label=seed.staff_pick_label,
        featured_event_material_id=featured_event_material_id,
    )
    repo.replace_discovery_tags(
        community_id,
        tuple(
            DiscoveryTagInput(
                tag.tag_type,
                tag.tag_key,
                tag.label,
                search_text=tag.search_text,
                sort_order=tag.sort_order,
            )
            for tag in seed.tags
        ),
    )


def _seed_realm_interactions(
    repo: ForumRepository,
    community_id: int,
    interactions: tuple[InteractionSeed, ...],
) -> None:
    for interaction_index, interaction_seed in enumerate(interactions, start=1):
        interaction = _get_or_create(
            lambda community_id=community_id, interaction_seed=interaction_seed: (
                repo.get_realm_interaction_by_slug(
                    community_id,
                    interaction_seed.slug,
                )
            ),
            lambda community_id=community_id, interaction_seed=interaction_seed, interaction_index=interaction_index: (
                repo.create_realm_interaction(
                    community_id,
                    interaction_seed.slug,
                    interaction_seed.title,
                    interaction_type=interaction_seed.interaction_type,
                    placement=interaction_seed.placement,
                    summary=interaction_seed.summary,
                    body=interaction_seed.body,
                    result_mode=interaction_seed.result_mode,
                    sort_order=interaction_index * 10,
                )
            ),
        )
        if repo.list_realm_interaction_questions(community_id, interaction.id):
            continue
        for question_index, question_seed in enumerate(interaction_seed.questions, start=1):
            question = repo.create_realm_interaction_question(
                community_id,
                interaction.id,
                question_seed.prompt,
                help_text=question_seed.help_text,
                sort_order=question_index * 10,
            )
            for option_index, option_seed in enumerate(question_seed.options, start=1):
                repo.create_realm_interaction_option(
                    community_id,
                    question.id,
                    option_seed.slug,
                    option_seed.label,
                    description=option_seed.description,
                    result_key=option_seed.result_key,
                    sort_order=option_index * 10,
                )


def _seed_intake_claims(
    repo: ForumRepository,
    community_id: int,
    *,
    claim_types: tuple[ClaimTypeSeed, ...],
    application_fields: tuple[ApplicationFieldSeed, ...],
) -> None:
    claim_types_by_slug = {}
    for index, claim_type_seed in enumerate(claim_types, start=1):
        claim_type = _get_or_create(
            lambda community_id=community_id, claim_type_seed=claim_type_seed: (
                repo.get_claim_type_by_slug(community_id, claim_type_seed.slug)
            ),
            lambda community_id=community_id, claim_type_seed=claim_type_seed, index=index: (
                repo.create_claim_type(
                    community_id,
                    claim_type_seed.slug,
                    claim_type_seed.name,
                    claim_kind=claim_type_seed.claim_kind,
                    description=claim_type_seed.description,
                    is_required=claim_type_seed.is_required,
                    is_exclusive=claim_type_seed.is_exclusive,
                    sort_order=index * 10,
                )
            ),
        )
        claim_types_by_slug[claim_type.slug] = repo.update_claim_type(
            community_id,
            claim_type.id,
            name=claim_type_seed.name,
            claim_kind=claim_type_seed.claim_kind,
            description=claim_type_seed.description,
            is_required=claim_type_seed.is_required,
            is_exclusive=claim_type_seed.is_exclusive,
            sort_order=index * 10,
        )

    for index, field_seed in enumerate(application_fields, start=1):
        mapped_claim_type_id = None
        if field_seed.maps_to_claim_type_slug is not None:
            mapped_claim_type_id = claim_types_by_slug[field_seed.maps_to_claim_type_slug].id
        options_json = json.dumps(list(field_seed.options), separators=(",", ":"))
        field = _get_or_create(
            lambda community_id=community_id, field_seed=field_seed: (
                repo.get_application_template_field_by_key(
                    community_id,
                    field_seed.field_key,
                )
            ),
            lambda community_id=community_id, field_seed=field_seed, mapped_claim_type_id=mapped_claim_type_id, options_json=options_json, index=index: (
                repo.create_application_template_field(
                    community_id,
                    field_seed.field_key,
                    field_seed.label,
                    field_type=field_seed.field_type,
                    help_text=field_seed.help_text,
                    placeholder=field_seed.placeholder,
                    options_json=options_json,
                    maps_to_claim_type_id=mapped_claim_type_id,
                    is_required=field_seed.is_required,
                    sort_order=index * 10,
                )
            ),
        )
        repo.update_application_template_field(
            community_id,
            field.id,
            label=field_seed.label,
            field_type=field_seed.field_type,
            help_text=field_seed.help_text,
            placeholder=field_seed.placeholder,
            options_json=options_json,
            maps_to_claim_type_id=mapped_claim_type_id,
            is_required=field_seed.is_required,
            sort_order=index * 10,
        )


def _seed_character_claims(
    repo: ForumRepository,
    community_id: int,
    claims: tuple[ClaimSeed, ...],
) -> None:
    for claim_seed in claims:
        claim_type = repo.get_claim_type_by_slug(community_id, claim_seed.claim_type_slug)
        character = repo.get_character_by_slug(community_id, claim_seed.character_slug)
        existing = [
            claim
            for claim in repo.list_character_claims(
                community_id,
                status=None,
                claim_type_id=claim_type.id,
            )
            if claim.value == claim_seed.value
        ]
        if existing:
            continue
        repo.create_character_claim(
            community_id,
            claim_type.id,
            claim_seed.value,
            claim_seed.label,
            character_id=character.id,
            status=claim_seed.status,
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
