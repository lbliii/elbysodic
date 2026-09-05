# Program Blueprints

Program Blueprints are director-authored starter packets for creating a PBP
hub inside an Elbysodic studio network.

They are the composition contract for a program launch: premise, playable
places, starter faces, guide materials, current-event pressure, and wanted
hooks, and a safe theme token packet. A blueprint should feel like a small
pitch bible that a human director can review and a machine can hydrate into real
Elbysodic primitives.

## What They Are

A Program Blueprint is a structured import shape for:

- One community/program inside the studio network.
- The user's membership and initial role in that program.
- Starter roster faces for previewing character-aware workflows.
- Playable boards and desk lanes.
- World materials such as premise, current event, application guide, or rules.
- Wanted hooks that make the hub immediately playable.
- Safe theme tokens for program-specific atmosphere across light, dark, and
  system modes.

Blueprints should preserve PBP language. Prefer "face", "roster", "scene",
"wanted", "plotter", "current event", "guide", and "director" over generic CMS
language.

## What They Are Not

Blueprints are not live app state. After hydration, the source of truth is still
the database, repositories, services, and tenant boundary checks.

Blueprints are not themes. They may eventually refer to a theme or image pack,
but they should not become a CSS or layout format. Theme customization is
limited to approved tokens.

Blueprints are not a replacement for staff tools. A director can edit boards,
materials, wanted hooks, roles, and roster entries after import through normal
Elbysodic workflows.

Blueprints are not only seed data. The development seed uses them first because
that is the safest place to harden the contract, but the same shape should
later support import previews, templates, exports, and hosted onboarding.

## YAML Shape

YAML should be the human-friendly authoring surface. JSON can use the same
schema later for API clients, but the reviewable director packet should look
comfortable in YAML.

```yaml
elbysodic_blueprint: 1

program:
  slug: rl-small-town
  name: RL Small Town
  role:
    slug: member
    name: Member
    is_admin: false

theme:
  slug: founders-week
  name: "Founder's Week"
  typography:
    display: serif
    body: serif
    mono: mono
  radius: md
  density: calm
  texture: paper
  light:
    bg: "#fbf5e8"
    bg_subtle: "#eee3cf"
    surface: "#fffaf0"
    surface_elevated: "#f4ead7"
    border: "#c8b89a"
    text: "#2b2318"
    text_muted: "#75684f"
    accent: "#8d3f4a"
    accent_hover: "#6e2f38"
    accent_dim: "#c9878f"
    accent_secondary: "#4f7c5b"
    success: "#4f7c5b"
    warning: "#a06d2a"
    error: "#a64242"
  dark:
    bg: "#16130f"
    bg_subtle: "#211c16"
    surface: "#282219"
    surface_elevated: "#332b1f"
    border: "#675942"
    text: "#f6eddf"
    text_muted: "#c9b99e"
    accent: "#e38991"
    accent_hover: "#f0a7ad"
    accent_dim: "#7d4248"
    accent_secondary: "#91c49a"
    success: "#91c49a"
    warning: "#dbb168"
    error: "#ee8d8d"

appearance:
  post_style:
    profile_variant: poster
    accent_style: line
    border_style: hairline
    title_style: serif
    density: calm
  material_variants:
    premise: chapter
    event: noticeboard

characters:
  - slug: june-calloway
    name: June Calloway
    summary: "Florist, town council note-taker, and keeper of other people's secrets."
    tagline: "Everybody knows. Nobody says."

boards:
  - slug: main-street
    name: Main Street
    kind: location
    tagline: "One stoplight, twelve opinions, and a bakery that hears everything."
    description: "The town's public spine for errands, arguments, festivals, and reunions."
    media:
      url: "/elbysodic-static/seed-media/locations/smalltown-main-street.svg"
      alt: "Storefronts and civic lights along Main Street at dusk."
      treatment: poster
      focal_point: center
      overlay: medium

materials:
  - slug: premise
    title: "Premise: Founder's Week"
    type: premise
    summary: "A small-town ensemble where celebration keeps digging up history."
    body: |
      Founder's Week should be a cozy pressure cooker: parade planning,
      school reunions, family businesses, old property lines, summer visitors,
      and people who left town discovering the town kept a place for them anyway.

wanted:
  - slug: returning-sibling-with-the-missing-deed
    title: Returning sibling with the missing deed
    type: relationship
    related_material: premise
    summary: "A homecoming character tied to the disputed property lines."
    body: |
      This role gives the town an emotional fuse: someone who left, came back
      at the worst possible moment, and may have the document everyone else is
      arguing about.
```

The current Python contract is intentionally close to this shape:

- `ProgramBlueprint`
- `BlueprintCharacter`
- `BlueprintBoard`
- `BlueprintMaterial`
- `BlueprintWanted`
- `BlueprintTheme`
- `BlueprintThemeMode`
- `BlueprintTypography`
- `BlueprintAppearance`
- `BlueprintPostStyle`
- `BlueprintMaterialVariant`

The Python field names use repository-facing terms such as `board_kind`,
`material_type`, `wanted_type`, and `related_material_slug`. A future YAML parser
can map friendlier keys like `kind`, `type`, and `related_material` into those
typed objects before validation.

## Theme Boundary

Program themes change atmosphere through design tokens, not arbitrary CSS.
Use `docs/product/appearance-studio.md` for the broader product boundary around
theme tokens, ritual-surface variants, media slots, previews, and health
warnings.

Allowed theme controls:

- Light and dark color palettes.
- Display, body, and mono font stack keys from an allowlist.
- Radius preset.
- Density preset.
- Texture preset.

Allowed appearance controls:

- Post style defaults from the same approved vocabulary Studio exposes:
  profile variant, accent style, border style, title style, and density.
- Guidebook material presentation variants keyed by material type, such as
  `chapter`, `dossier`, `noticeboard`, and `archive`.
- Board media slots for playable hubs:
  `media.url`, `media.alt`, `media.treatment`, `media.focal_point`, and
  `media.overlay`. These map to the same safe Studio board media controls:
  poster/background/compact/text treatment, center/top/bottom/left/right focal
  point, and light/medium/heavy overlay.

Disallowed theme controls:

- Raw CSS selectors.
- Script tags or JavaScript.
- External font URLs.
- Layout rules that can break app structure.
- Per-component overrides outside approved token names.
- Raw HTML templates or template overrides.

The goal is for Jurassic Park, HP, RL NYC, and RL Small Town to feel like
different rooms in one studio network while sharing Elbysodic's operational
grammar.

## Shared PBP Vocabulary

Blueprint validation uses the same material and wanted-hook vocabulary as the
rendered app labels:

- Material types: `premise`, `guide`, `factions`, `application`, and `event`.
- Wanted hook types: `canon`, `connection`, `event_role`, `faction_need`,
  `plot_role`, `relationship`, and `rival`.

## Validation Rules

Blueprint validation should fail before hydration when:

- A required slug, name, title, summary, type, or role field is blank.
- A blueprint has no starter faces.
- A blueprint has no playable boards.
- A blueprint has no director materials.
- Program, character, board, material, or wanted slugs are duplicated.
- Unsupported keys appear in the top-level packet, program, role, roster face,
  board, media, material, wanted, theme, or appearance sections.
- A board uses an unknown `board_kind`.
- A director material uses an unknown material type.
- A wanted hook uses an unknown wanted-hook type.
- A board media URL is present without alt text, or alt text is present without
  a URL.
- A board media treatment, focal point, or overlay is outside the Studio
  allowlist.
- A board media URL uses an unsafe scheme such as `javascript:` or `data:`.
- A wanted hook references a material slug that does not exist in the same
  blueprint.
- A theme color is not a 6-digit hex color.
- A theme font, radius, density, or texture preset is outside the allowlist.
- An appearance post style or material variant is outside the allowlist.
- An appearance payload includes raw CSS, script, HTML, template, or external
  font keys.

Errors should be written for humans first, because directors need to fix these
files. Avoid raw database exceptions or stack traces in import preview flows.

## Hydration Rules

Hydration should always go through repository/service boundaries. It should not
write ad hoc SQL from a page handler or importer.

Studio apply hydrates only the director's current realm. The Blueprint program
slug must match that realm before a transaction begins; Studio does not create
or select a different community. Identical face, board, material, wanted, or
theme slugs in another community are irrelevant to planning and apply.

Every mode is explicit:

- `create_only` creates missing faces, boards, materials, wanted hooks, and
  themes, but stops on live content collisions. The current realm name and
  matched Blueprint role must already agree with the packet.
- `skip_existing` creates missing rows and preserves every matched live row.
- `explicit_update` replaces reviewed current-realm rows. It may update only
  faces and wanted hooks owned by the importing membership, and it refuses to
  change the importing director's own capability grant.
- `dry_run` repeats validation and diff planning without entering a write
  transaction.

Starter faces and wanted hooks are owned by the importing membership. The first
starter face becomes that membership's default only when no default exists.
Board media passes the same safe URL, alt-text, treatment, focal-point, and
overlay validation as preview. Theme values remain allowlisted tokens. Material
appearance variants are stored on each material as `chapter`, `dossier`,
`noticeboard`, or `archive` rather than becoming raw layout input.

Non-dry-run apply reserves a fingerprint-and-mode idempotency key, hydrates all
accepted rows, records the staff audit event, and completes the command inside
one repository transaction. A repeated accepted command is rejected with a
stable result. A late failure rolls back hydrated rows and the command
reservation; the failed attempt is then recorded without exposing exception or
Blueprint source content.

The reviewed fingerprint covers the packet, planned actions, and current values
of every matched realm row the packet can affect. Apply recalculates that state
after entering the write transaction and rejects the packet when a director has
edited any reviewed row since preview. In `skip_existing` mode, a face owned by
another writer remains untouched and is never selected as the importing
director's default face or as the author of a newly created wanted hook.

## Import Flow

Studio intake implements a reviewed two-step flow:

1. Paste YAML and preview it. Parsing, validation, current-realm matching, and
   the typed create/update/skip/blocked diff are read-only.
2. Choose a collision mode and apply that exact fingerprint. The service
   re-runs preview and permission checks inside the write transaction, then
   commits hydration and audit together.

The preview summarizes the packet in director language, such as “1 program, 3
starter faces, 5 scene hubs, 3 materials, 2 wanted hooks,” then names each
planned action. A mismatched realm slug renders a blocked row and no Apply
control. Stale previews, unsupported modes, ordinary members, unsafe appearance
input, and live collisions rejected by the selected mode do not hydrate rows.

After a successful apply, Studio renders the accepted mode and committed state
instead of offering the same Apply control again. Directors preview again for a
later reviewed change. The source of truth after apply is the normal
community-scoped repository state, not the YAML packet or rendered diff.

File upload, background import jobs, public Blueprint marketplaces, and
unreviewed realm generation remain out of scope.

The implemented hydration design snapshot and its closure proof live in
`plans/archive/2026/program-blueprint-hydration-2026-05-02.md`. GitHub is the
live work DAG; see `docs/plan/issue-lifecycle.md`.
