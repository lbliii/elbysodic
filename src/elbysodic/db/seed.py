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
                    "fully disappear from Lena's life."
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
    _seed_realm_interactions(repo, community.id, DEFAULT_REALM_INTERACTIONS)
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


def _seed_studio_network_programs(repo: ForumRepository, user: User) -> None:
    ensure_valid_program_blueprints(STUDIO_NETWORK_PROGRAMS)
    for program in STUDIO_NETWORK_PROGRAMS:
        community = _ensure_studio_program_community(repo, program)
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
        default_character: Character | None = None
        for index, character_seed in enumerate(program.characters):
            character = _get_or_create(
                lambda community=community, character_seed=character_seed: (
                    repo.get_character_by_slug(
                        community.id,
                        character_seed.slug,
                    )
                ),
                lambda community=community, membership=membership, character_seed=character_seed, index=index: (
                    repo.create_character(
                        community.id,
                        membership.id,
                        character_seed.slug,
                        character_seed.name,
                        summary=character_seed.summary,
                        tagline=character_seed.tagline,
                        make_default=index == 0,
                    )
                ),
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

        for index, board_seed in enumerate(program.boards, start=1):
            _ensure_board(
                repo,
                community.id,
                board_seed.slug,
                board_seed.name,
                board_seed.description,
                index * 10,
                board_kind=board_seed.board_kind,
                tagline=board_seed.tagline,
            )
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


def _ensure_studio_program_community(
    repo: ForumRepository,
    program: ProgramBlueprint,
) -> Community:
    try:
        community = repo.get_community_by_slug(program.slug)
    except LookupError:
        return repo.create_community(program.slug, program.name)
    if community.name == program.name and community.slug == program.slug:
        return community
    return repo.update_community_name_and_slug(community.id, slug=program.slug, name=program.name)


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
