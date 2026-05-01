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
    related_material: current-event
    summary: "A homecoming character tied to the time capsule letter."
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

## Validation Rules

Blueprint validation should fail before hydration when:

- A required slug, name, title, summary, type, or role field is blank.
- A blueprint has no starter faces.
- A blueprint has no playable boards.
- A blueprint has no director materials.
- Program, character, board, material, or wanted slugs are duplicated.
- A board uses an unknown `board_kind`.
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

Hydration should be idempotent where practical:

- Existing programs are looked up by slug.
- Existing roles, starter faces, boards, materials, and wanted hooks are looked
  up by slug inside the program community.
- Theme tokens are stored as the community's default theme.
- Materials and boards can be updated from the blueprint so seed and preview
  content can improve over time.
- Wanted hooks are created if missing. A later edit workflow can decide how
  aggressive updates should be for already-edited wanted ads.

Hydration should keep tenant scope explicit. Every created object belongs to
one community, and every character or wanted hook has an intentional membership
owner.

## Import Flow

Studio intake now supports the first dry-run milestone. The complete flow is:

1. Upload or paste a YAML Program Blueprint.
2. Parse into typed blueprint objects.
3. Validate and show a dry-run preview.
4. Apply through a service-layer hydrator.

The dry-run preview should summarize the resulting program in director language:
"1 program, 3 starter faces, 5 scene hubs, 3 materials, 2 wanted hooks."

Do not make file import the first user-facing milestone. The first milestone is
the shared contract: seed data and future YAML imports should describe the same
kind of PBP hub. The current Studio preview intentionally stops before step 4:
it validates and summarizes the packet, but does not create or update database
state.

## Hydration Gate

Keep apply disabled until the hydrator has an explicit service-layer plan for:

- duplicate handling for existing program, role, face, board, material, wanted,
  and theme slugs
- ownership defaults for starter faces and director-authored wanted hooks
- rollback behavior when a later object fails after earlier objects validate
- tenant tests that prove every created object stays in the selected community
- a dry-run diff that names create, update, and skipped objects before mutation

Until those pieces exist, Studio intake should keep saying that preview is a
hydration gate, not a launch button.
