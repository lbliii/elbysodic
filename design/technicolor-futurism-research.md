# Technicolor Futurism Research Notes

These notes translate source-backed research into Elbysodic design-system
direction. They are not a full art-history survey. They exist so future agents
can make sharper product decisions when evolving tokens, components, and
Appearance Studio.

## Sources Consulted

- Natalie M. Kalmus, "Color Consciousness," Journal of the Society of
  Motion Picture Engineers 25, no. 2, August 1935, original research,
  DOI `10.5594/J05386`:
  https://journal.smpte.org/periodicals/Journal%20of%20the%20Society%20of%20Motion%20Picture%20Engineers/25/2/8/
- George Eastman Museum, Technicolor dye-transfer process:
  https://www.eastman.org/technicolor/technology/dye-transfer-printing
- George Eastman Museum, Color Control Department:
  https://www.eastman.org/technicolor/company/color-advisory-service
- George Eastman Museum reprint of Natalie M. Kalmus, "Color Consciousness":
  https://www.eastman.org/sites/default/files/technicolor/pdfs/ColorConsultants_ColorConsciousness.pdf
- NASA Science, visible light:
  https://science.nasa.gov/ems/09_visiblelight/
- Munsell Color, color notation:
  https://munsell.com/about-munsell-color/how-color-notation-works/
- National Gallery, complementary colors:
  https://www.nationalgallery.org.uk/paintings/glossary/complementary-colours
- Microsoft Learn, Acrylic material:
  https://learn.microsoft.com/en-us/windows/apps/design/style/acrylic
- Microsoft Learn, Mica material:
  https://learn.microsoft.com/en-au/windows/apps/design/style/mica
- Apple Human Interface Guidelines, materials:
  https://developer.apple.com/design/human-interface-guidelines/materials
- Britannica, Futurism:
  https://www.britannica.com/art/Futurism
- Guggenheim, Italian Futurism exhibition overview:
  https://exhibitions.guggenheim.org/futurism/

## Technicolor: What Matters For UI

Technicolor was a system before it was a vibe. The mature dye-transfer process
used separated color records and transferred cyan, yellow, and magenta dyes in
registered passes. The UI lesson is structural: build color as disciplined
layers with exact alignment, not as a decorative wash.

A useful historical nuance: Natalie M. Kalmus is often described in secondary
sources as a co-developer or pioneer of Technicolor, while museum and
institutional summaries usually credit the technical founding/invention to
Herbert T. Kalmus, Daniel Comstock, and W. Burton Wescott. For Elbysodic's
design purposes, Natalie Kalmus matters most as the author of "Color
Consciousness" and the leader of Technicolor's color-consulting discipline:
she turned the process into an aesthetic governance model.

Practical implications:

- Treat dark structure as the black key: type, rules, focus boundaries,
  on-media text, and surface edges need crisp value contrast.
- Treat saturated color as dye records: separate accent families with explicit
  jobs, not a general page atmosphere.
- Treat registration as layout discipline: sharp grids, consistent spacing,
  no fuzzy edge seams, and stable dimensions.
- Treat media and accents as printed layers over a controlled base.

Technicolor also had aesthetic governance. The Color Control Department and
Color Advisory Service treated color as planned composition tied to psychology,
character, emotion, costume, set, and mood. Natalie Kalmus's "Color
Consciousness" warns against both monotony and too much color. The product
translation is direct: Elbysodic should use color as narrative and workflow
grammar, not spectacle.

Practical implications:

- Every high-chroma token needs a semantic job.
- Atmospheric pages can carry more color than prose and staff-review rooms.
- Color should help distinguish face, scene, wanted, event, queue, private,
  staff, warning, and destructive states.
- A default palette should include quiet neutrals, not only luminous accents.

## Color Science: What To Control

Visible color is a narrow band of light humans can perceive; digital UI mixes
light additively, while Technicolor dye transfer is closer to subtractive
printing. Elbysodic lives on screens, so the goal is not literal film
simulation. The useful bridge is discipline around hue, value, and chroma.

Practical implications:

- Hue: choose the color family, such as cyan, magenta, amber, green, or red.
- Value: choose the lightness/darkness that makes hierarchy and text contrast
  work.
- Chroma: choose how vivid the color feels; reserve high chroma for meaningful
  signal.
- Complementary and split-complementary relationships can create energy, but
  they need quiet value control or they become visual noise.

Suggested palette model:

- 70 percent key neutrals and content layers.
- 20 percent low-to-medium chroma support colors.
- 10 percent high-chroma dye-record accents.

This is a design heuristic, not a hard token contract.

## Futurism: What To Keep And What To Refuse

Historic Futurism carries useful formal cues and serious ideological baggage.
Elbysodic should borrow only the formal language that serves the product:
modernity, speed, directional energy, technological confidence, layered motion,
and typographic force. It should refuse militarism, aggression, contempt for
the past, and dehumanizing machine worship.

Practical implications:

- Use forward motion through composition: directional rules, staggered grids,
  active-state vectors, progressive reveal, and confident asymmetry.
- Keep motion restrained and useful: orientation, transition, relationship, or
  focus.
- Let the writing archive matter. Elbysodic is continuity-native, so futurism
  cannot mean erasing the past.
- Make technology feel like a studio instrument for writers, not an industrial
  machine that swallows character voice.

## Glass Eleganza: What It Means Here

Glass eleganza is a component-material direction, not a mandate for frosted
cards everywhere. The useful modern guidance from platform design systems is
that materials create hierarchy, separate foreground from background, preserve
context, and require strong legibility. Microsoft recommends acrylic mainly
for transient surfaces and warns against seams, noise, and overuse. Mica is
more appropriate as a subtle base layer. Apple similarly frames materials as
semantic hierarchy and emphasizes legibility over apparent color.

Practical implications:

- Use glass for transient or context-linked surfaces: menus, popovers,
  dropdowns, command overlays, preview scrims, topbar/sidebar treatment, and
  media captions.
- Use opaque or near-opaque surfaces for long-lived reading, writing, staff,
  and form surfaces.
- Avoid nested glass cards, edge-to-edge acrylic strips, glass behind prose,
  and accent-colored text on translucent backgrounds.
- Every glass treatment needs a solid fallback for high contrast, reduced
  transparency, low-power, unsupported browsers, and print/export contexts.
- Add texture/noise only when it improves separation; it should never compete
  with body text.

## Component Design Translation

| Component Area | Technicolor Rule | Futurism Rule | Glass Rule |
| --- | --- | --- | --- |
| App shell | black key establishes crisp frame | persistent studio cockpit, not SaaS chrome | subtle Mica-like base only |
| Topbar/sidebar | low-chroma structure with one active dye accent | directional active states | restrained translucent layer if readable |
| Menus/popovers | dye accent marks selected action | fast, clear transition | best fit for acrylic/glass |
| Place/board hero | high-chroma identity allowed | cinematic momentum into scenes | glass captions only over media |
| Thread/postbit | face accent as controlled dye record | motion almost none | no glass behind prose |
| Wanted hooks | color supports desire, urgency, role | editorial casting energy | media overlay glass acceptable |
| Studio rooms | mostly black-key and neutral layers | precise production hierarchy | avoid glass except transient controls |
| Applications/claims | color clarifies state and review path | sharp editorial queue | opaque surfaces for trust |
| Notices | warning/error/success chroma is explicit | urgent vector or rule allowed | only if contrast survives |

## Palette Exploration Brief

Explore a default palette that moves beyond the current warm paper, rose, moss,
and gold without discarding readability:

- deep blue-black or graphite key
- cool porcelain light canvas
- electric cyan for focus and link energy
- spectral magenta or rose-violet for identity and selection
- clean amber or chartreuse-yellow for highlights and warnings
- emerald or mint signal for safe progress
- vermilion/coral for destructive or urgent pressure

Do not ship a palette because it looks futuristic in isolation. Test it across:

- world gateway
- board/location page
- thread page and composer
- character hub
- wanted hooks and backstage
- Studio production rooms
- applications, claims, and reserves
- staff/private notices
- light, dark, and system modes
- mobile first viewport and long-scroll reading

## Open Questions

- Should Elbysodic keep one default technicolor-futurist theme, or define a
  small set of launchable theme presets?
- Which component should become the first glass-eleganza proof: menu, topbar,
  media caption, wanted card, or board hero?
- Should Appearance Studio expose "luminosity" and "material" presets, or keep
  them internal until the default design stabilizes?
- What browser QA artifact should become the standard visual proof for palette
  changes?
