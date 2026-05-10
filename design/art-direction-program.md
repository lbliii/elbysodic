# Art Direction Program

This note codifies how Elbysodic can help a community builder turn a board
premise into a coherent art direction without exposing raw CSS, arbitrary
templates, scripts, unsafe fonts, or layout controls.

This is design guidance, not a committed Blueprint, schema, service, route, or
database contract. Before implementing it in Program Blueprints, Appearance
Studio, seed data, CLI output, or storage, check in with a human and consult the
blueprint, services, web, docs, and tests stewards.

## Core Idea

Give each community a color score: a structured art-direction plan inspired by
Natalie Kalmus's "Color Consciousness." Kalmus analyzed each scene for mood,
character, color separation, harmony, emphasis, and restraint. Elbysodic can do
the same for PBP communities by mapping a director's premise into token roles,
surface intensity, media direction, and health warnings.

The score should help directors answer:

- What should this board feel like at first contact?
- Which surfaces get atmosphere, and which stay quiet for reading or staff work?
- Which colors carry identity, mood, action, and workflow state?
- Where is glass or translucency useful?
- What must remain stable so writers can read, post, and recognize their face?

## Builder Inputs

A community builder can ask for structured inputs instead of design jargon.

Required:

- `community_name`: public board name.
- `premise`: one to three sentences describing the world or play promise.
- `genre_lanes`: director-selected lanes such as supernatural small town,
  fandom academy, slice-of-life city, political intrigue, space opera, horror,
  romance, mystery, or survival.
- `reading_density`: `airy`, `balanced`, or `dense`.
- `tone`: three to five mood words.
- `safety_posture`: `soft`, `standard`, or `heightened`, describing how quiet
  staff, private, warning, and recovery surfaces should feel.

Optional:

- `era_or_technology`: contemporary, historical, near future, magical modern,
  retrofuture, post-collapse, or other director language.
- `media_direction`: photography, illustration, collage, map, dossier,
  poster, archive, field note, or symbolic.
- `avoid`: colors, visual tropes, media styles, or genre cliches the director
  does not want.
- `signature_motifs`: recurring symbols, materials, environments, factions,
  houses, species, claims, or event pressures.
- `community_examples`: existing boards, films, games, magazines, or objects
  used as taste references. Store as inspiration notes, not copied styles.

## Generated Score

The builder output should be explicit enough for preview, validation, and later
token hydration, but still safe enough for director editing.

```json
{
  "art_direction": {
    "name": "Technicolor Futurism",
    "summary": "Luminescent editorial sci-fi with calm prose rooms and sharp face identity.",
    "key": {
      "dark": "blue-black graphite",
      "light": "cool porcelain",
      "contrast_rule": "thread prose and staff notes use opaque key surfaces"
    },
    "identity_dye": {
      "family": "spectral magenta",
      "uses": ["community mark", "selected face", "primary ritual accents"]
    },
    "atmosphere_dye": {
      "family": "electric cyan",
      "uses": ["world gateway", "board hero", "media overlays"]
    },
    "state_dyes": {
      "needs_reply": "clean amber",
      "waiting": "muted violet",
      "caught_up": "mint signal",
      "watching": "peacock blue",
      "private": "smoke blue",
      "staff": "cool graphite",
      "warning": "sodium gold",
      "error": "signal coral"
    },
    "surface_intensity": {
      "world_gateway": "high",
      "board_location": "high",
      "thread": "low",
      "composer": "low",
      "character_hub": "medium_high",
      "wanted": "high",
      "studio": "low",
      "applications": "low",
      "staff_private": "lowest"
    },
    "materials": {
      "glass": ["topbar", "menus", "media_caption"],
      "solid": ["thread_body", "composer", "staff_notes", "application_review"],
      "texture": "scanline_subtle"
    },
    "restraint_rule": "Only one high-chroma dye may dominate a viewport; prose and staff surfaces return to key neutrals."
  }
}
```

Names and values above are illustrative. Implementation should use enumerated
keys and approved tokens, not arbitrary strings.

## Surface Intensity Budget

Surface intensity keeps art direction from overwhelming PBP work.

| Surface | Default Budget | Reason |
| --- | --- | --- |
| World gateway | High | sells community promise and atmosphere |
| Board/location | High | establishes playable place identity |
| Guidebook/material | Medium-high | supports canon prestige while preserving prose |
| Character hub | Medium-high | foregrounds face identity and plotter context |
| Wanted hooks | High | casting energy and desire are part of the job |
| Event notice | High | event pressure can be visually loud |
| Thread postbit | Medium | character identity matters, body prose stays calm |
| Thread body | Low | long-form reading is the prestige surface |
| Composer | Low | writing focus, preview parity, and active face clarity |
| Studio rooms | Low | production work needs precision and low noise |
| Applications/claims | Low | trust, review clarity, and privacy beat atmosphere |
| Staff/private/recovery | Lowest | safety and comprehension dominate |

## Validation And Warnings

Hard validation:

- Unknown token, surface, material, density, texture, or variant key.
- Raw CSS, HTML, script, external font URL, or arbitrary selector.
- Missing contrast target for text-bearing surfaces.
- Glass assigned behind thread prose, staff notes, composer body, or
  application review text.
- State dye missing for warning, error, private, or staff surfaces.

Soft warnings:

- More than one high-chroma dye dominates the same viewport.
- Low contrast between active face accent and the current postbit surface.
- Mood and state colors collide, such as warning and identity using the same
  hue family.
- Surface intensity is too high for reading-heavy or staff-heavy boards.
- Texture or glass appears on too many long-lived surfaces.
- Media direction lacks alt-text expectations or decorative-role guidance.

Warning copy should name the PBP surface:

```text
Thread body may be hard to read because glass was assigned behind prose.
Wanted hooks and warning notices both use amber; reserves may look like alerts.
The active face accent is too close to the postbit background.
```

## Programmatic Flow

1. Collect builder inputs in director language.
2. Classify genre lanes, tone, reading density, safety posture, and media
   direction.
3. Choose a key neutral system first.
4. Assign one identity dye and one atmosphere dye.
5. Reserve state dyes before decorative accents.
6. Apply surface intensity budgets.
7. Select safe material and texture presets.
8. Run contrast, role collision, glass-placement, and surface-budget checks.
9. Produce a director preview in PBP language.
10. Hydrate only approved tokens and variants through normal service and
    repository boundaries after the product contract exists.

## Director Preview Shape

Preview should sound like art direction, not a config dump:

```text
Your board reads as luminescent paranormal noir: graphite key surfaces,
electric cyan atmosphere on World and board heroes, magenta face identity, and
amber needs-reply pressure. Threads and applications stay opaque for reading.
Glass is reserved for menus and media captions.
```

## Implementation Notes For Later

- This likely belongs near Appearance Studio and Program Blueprints, but it
  should not be added to either public contract without an explicit review.
- Store community-local appearance decisions with `community_id`.
- Keep director choices as approved keys and token values, not raw CSS.
- Generate previews from read models that preserve membership, character,
  staff, and privacy boundaries.
- Tests should cover token validation, contrast warnings, surface intensity,
  rejected unsafe inputs, and rendered preview language.
