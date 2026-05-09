# Appearance Studio Roadmap

Status: partially superseded by production-readiness sequencing
Owner: Product/UI stewardship  
Created: 2026-05-01  
Last updated: 2026-05-09
Review by: 2026-06-06
Source: `ask stewards` consultation after comparing Avior and Lethe as
contemporary Jcink/PBP cultural references.  
Closure criteria: split into implementation issues or PR-sized plans covering
the theme editor, ritual-surface variants, validation, and import/export
support; archive this roadmap when those workstreams have owners or have been
superseded.

## 2026-05-09 Verification Update

The Appearance Studio product doc now exists, and Blueprint/theme parsing has
safe appearance payload coverage. The production-readiness roadmap defers
additional theme editor, health warning, and ritual-variant work until
auth/Railway smoke, storage persistence, privacy proof, and core browser QA are
stable enough that visual polish is not hiding data-contract risk.

## Purpose

Plan a feasible path for supporting the artistic range of contemporary PBP
boards without turning Elbysodic into a raw Jcink skin editor.

The product goal is aesthetic sovereignty with stable operations: Avior-like
accessible supernatural Americana and Lethe-like gothic folk-horror should be
able to feel genuinely different, while composer ergonomics, navigation,
permissions, mobile layout, and safe markup remain product-owned.

## Consulted Stewards

- Root constitution: `AGENTS.md`
- Product and architecture: `docs/AGENTS.md`
- Package and tooling: `src/elbysodic/AGENTS.md`
- Domain model: `src/elbysodic/domain/AGENTS.md`
- Service layer: `src/elbysodic/services/AGENTS.md`
- Storage and migrations: `src/elbysodic/db/AGENTS.md`
- Rendering and UI: `src/elbysodic/web/AGENTS.md`
- Blueprint contract: `src/elbysodic/blueprints/AGENTS.md`
- Tests: `tests/AGENTS.md`

## Feasibility Read

Confidence is high for safe art direction and medium for full Jcink-style
skin culture parity.

Evidence already in the codebase:

- `CommunityTheme` and `communities.default_theme_id` exist.
- Program Blueprints already carry safe theme tokens for light/dark palettes,
  typography keys, radius, density, and texture.
- `services/themes.py` converts tokens into CSS variables instead of raw CSS.
- `_layout.html` injects program theme variables into the shell.
- Studio already exposes post style vocabulary controls.
- Character records already carry avatar, poster, accent, and post style
  fields.
- Product docs already separate stable product grammar from community
  vocabulary and presentation.

The feasible version is a constrained Appearance Studio. The infeasible or
unsafe version is arbitrary CSS, arbitrary HTML templates, external font URLs,
or per-community JavaScript in ordinary director tools.

## Product Principles

1. Preserve the world as the default emotional surface.
2. Let communities change atmosphere, not safety contracts.
3. Keep operational surfaces predictable: composer, queues, notifications,
   permissions, staff actions, and navigation grammar remain product-owned.
4. Make ritual surfaces highly expressive: home/world gateway, guidebook
   material, board/location pages, thread postbit, character hub, wanted hooks,
   applications, claims, and event notices.
5. Prefer tokens, media, vocabulary, and approved presentation variants over
   raw selectors.
6. Provide previews and health warnings before publishing.
7. Keep every appearance primitive community-scoped and exportable later.

## Scope

### In Scope

- Community theme editor for existing safe tokens.
- Light, dark, and system mode preview.
- Allowed font stack keys, not arbitrary font imports.
- Radius, density, and texture presets.
- Community-level media slots where they map to product meaning.
- Presentation variants for PBP ritual surfaces.
- Postbit style vocabulary and character-level style choices.
- Facet/member-group colors and icons where they carry story grammar.
- Studio preview pages for directors.
- Accessibility/readability validation and soft health warnings.
- Blueprint import/export of approved tokens and variant choices.

### Out Of Scope For V1

- Raw CSS editor.
- Arbitrary HTML template editing.
- External font URLs.
- Per-community JavaScript.
- Full layout builders.
- Theme controls that change permissions, visibility, route ownership, or
  canonical workflow state.
- Per-community topbar realm structure.
- Unbounded marketplace skins.

## Workstreams

### 1. Appearance Contract

Document the public contract before widening implementation.

Deliverables:

- Add `docs/product/appearance-studio.md`.
- Define "ritual surfaces" and "operational surfaces".
- List allowed token families and explicitly disallowed controls.
- Describe preview and health-warning behavior.
- Cross-link from `docs/product/program-blueprints.md`,
  `docs/product/information-hierarchy.md`, and root `AGENTS.md` if the product
  doctrine changes.

Checks:

- `rg` for conflicting terms such as skin, theme, appearance, token, and
  custom.
- No claims that raw CSS or free-form templates are supported.

### 2. Theme Token Editor

Turn existing theme storage/rendering into a normal Studio workflow.

Deliverables:

- Studio route or room for editing the default community theme.
- Form controls for light/dark palettes, typography keys, radius, density, and
  texture.
- Server-side validation matching Program Blueprint validation.
- Service-layer method that persists through repository boundaries.
- Rendered preview before save or immediately after local edits.

Checks:

- Tenant-scoped repository tests for creating/updating/selecting default theme.
- Policy tests proving only world/studio managers can edit appearance.
- Rendered page tests proving theme variables appear only for the current
  community.

### 3. Theme Health

Add guardrails that keep expression readable.

Deliverables:

- Contrast/readability warnings for key pairs: text/background,
  muted/background, accent/background, accent/surface, warning/surface, and
  error/surface.
- Warnings, not hard blocks, unless a value is structurally invalid.
- Studio copy that names the affected surface in PBP language.
- Preview states for light, dark, and system.

Checks:

- Unit tests for contrast calculations and warning thresholds.
- Rendered Studio test for warnings.
- Browser QA for at least one light-heavy and one dark-heavy theme.

### 4. Ritual Surface Inventory

Audit screens and classify what directors can art-direct.

Initial classification:

- High expression: world gateway, guidebook/material pages, board/location
  hero, thread postbit, character hub, wanted detail, event notices,
  application guide, claims/casting pages.
- Medium expression: roster cards, thread cards, plotting room previews,
  discovery cards, sidebar labels.
- Low expression: composer controls, queue actions, notification inbox, Studio
  forms, permissions, staff review workflows, recovery pages.

Deliverables:

- Matrix in `docs/product/appearance-studio.md`.
- For each high-expression surface, identify token needs, media needs,
  component variants, and accessibility constraints.

Checks:

- Web/UI steward review against `information-hierarchy.md`,
  `control-topology.md`, `navigation-menus.md`, `paragraph-rhythm.md`, and
  `notices-admonitions.md`.

### 5. Presentation Variants

Expand expressiveness through approved component variants.

Candidate V1 variants:

- Guidebook material: dossier, chapter, noticeboard, archive.
- Board/location hero: map card, poster stage, directory listing, field note.
- Wanted hook: casting call, relationship ad, faction seat, event role.
- Character hub: profile dossier, poster profile, roster sheet, intimate
  journal.
- Event notice: seasonal pressure, danger bridge, festival banner, staff
  briefing.

Rules:

- Variants must preserve semantic content, labels, keyboard access, mobile
  layout, and safe prose rendering.
- Variants should be selected from Studio, not hand-authored through raw CSS.
- Components shared across surfaces should live under
  `src/elbysodic/web/pages/_components/`.

Checks:

- Rendered page tests for each new variant on representative surfaces.
- Browser QA for desktop and mobile.
- Markup tests remain green for post/canon/hook prose.

### 6. Community Media And Icons

Support visual identity without mixing it into layout code.

Deliverables:

- Define approved media slots: community mark, world hero image, location
  image, material cover, event banner, badge image, member-group/facet icon,
  character avatar/poster.
- Store metadata with alt text and ownership scope.
- Start with URL fields where existing surfaces already use URLs; defer file
  upload/storage policy if it widens scope too much.
- Add validation for missing alt text on director-managed media.

Checks:

- Tenant tests for media-bearing records.
- Rendered page tests for alt text and fallback behavior.

### 7. Program Blueprint Round Trip

Keep starter packets aligned with Studio.

Deliverables:

- Extend Blueprint docs only for approved tokens and variant keys.
- Preserve the "not a CSS/theme engine" boundary.
- Add preview of appearance payload in Studio intake.
- Later: export an existing community appearance packet once the editor is
  stable.

Checks:

- `tests/test_program_blueprints.py` for valid/invalid theme and variant
  payloads.
- Hydration tests only after the apply flow exists.

## Suggested Milestones

### Milestone 1: Contract And Audit

Goal: decide the boundaries and surface matrix before new controls ship.

Tasks:

- Write `docs/product/appearance-studio.md`.
- Classify ritual vs operational surfaces.
- Add "Appearance Studio" to the existing steward backlog as a concrete follow
  up or cross-link this plan from the backlog rollup.

Exit criteria:

- Stewards can point to one doc when deciding whether a proposed appearance
  control belongs in V1.

### Milestone 2: Theme Editor MVP

Goal: directors can edit the existing safe theme tokens from Studio.

Tasks:

- Add service/repository route for default theme updates.
- Build Studio form and preview.
- Add tenant/policy/rendered tests.

Exit criteria:

- A community can change light/dark palette, font keys, radius, density, and
  texture without raw CSS.

### Milestone 3: Health Warnings

Goal: directors can see when a board's atmosphere is hurting readability.

Tasks:

- Implement contrast checks.
- Show warnings in the theme editor.
- Add preview states for key surfaces.

Exit criteria:

- Invalid colors fail; risky palettes save with clear warnings.

### Milestone 4: First Ritual Variants

Goal: ship visible artistic range where PBP culture most expects it.

Recommended first slice:

- Thread postbit variants, because post identity is central to Jcink culture
  and the app already has post style primitives.
- Guidebook/material variants, because Avior and Lethe both use guide surfaces
  as cultural front doors.

Exit criteria:

- Two communities can share the same workflows while looking meaningfully
  different on post and guidebook surfaces.

### Milestone 5: Blueprint Alignment

Goal: starter packets can carry the same safe appearance decisions.

Tasks:

- Add variant keys to blueprint validation only after Studio keys settle.
- Show appearance summary in dry-run intake.
- Defer hydration until the broader Program Blueprint apply plan is active.

Exit criteria:

- Appearance payloads are reviewable in director language and cannot smuggle
  raw CSS, JS, or layout rules.

## Testing Strategy

- Domain: typed fields remain explicit and community-scoped.
- Storage: theme and appearance settings cannot cross communities.
- Services: only permitted staff/directors can mutate appearance.
- Rendering: current community receives its own CSS variables and variants.
- Accessibility: contrast warnings, alt text, keyboard access, and mobile
  wrapping on representative pages.
- Browser QA: world gateway, guidebook material, board page, thread, character
  profile, wanted detail, Studio editor, and mobile thread reading.

Use the normal project checks before merging implementation slices:

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest -q --tb=short
uv run ty check src/elbysodic/ tests/
uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"
```

## Risks

- Raw customization pressure: roleplayers will expect skin freedom because
  Jcink normalized it. Product copy needs to explain the safer model without
  sounding dismissive.
- Accessibility drift: custom palettes can make prose hard to read. Add
  warnings early.
- Variant sprawl: every board aesthetic can become a one-off. Promote only
  repeated PBP meanings into shared variants.
- Theme/data leakage: appearance settings must remain tenant-scoped.
- Operational instability: do not let appearance controls resize composer,
  hide core actions, or change workflow labels into unreadable novelty.
- Import boundary creep: Program Blueprints must not become a skin format.

## Not Now

- Marketplace themes.
- Raw skin import from Jcink.
- Admin-authored CSS selectors.
- Theme-specific route templates.
- Per-character custom CSS.
- External fonts or script embeds.
- User-uploaded asset pipeline, unless a separate storage/security plan exists.

## Next Checks

1. Draft `docs/product/appearance-studio.md` from this roadmap.
2. Inspect current Studio routes and decide whether the theme editor belongs in
   the main Studio page or a dedicated `/studio/appearance` route.
3. Inventory existing CSS variables and identify missing token names for
   guidebook, postbit, wanted, and event surfaces.
4. Choose the first two demo aesthetics to validate range. Recommended:
   accessible small-town mystery and gothic folk-horror.
5. Build the Theme Editor MVP before adding new variant families.
