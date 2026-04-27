# Control Topology And Input Decisions

Elbysodic should stay dense enough for regular writers, but never make a
writer memorize hidden rules just to move a scene forward. This guide helps
agents decide when a control should be visible, collapsed, combined, inline,
iconic, or expanded into a deliberate editing surface.

Use `docs/product/navigation-menus.md` for navigation-specific decisions:
topbar realms, sidebar groups, route pathing, breadcrumbs, tabs, dropdowns, and
mobile drawer behavior.

The core tradeoff is:

- Recognition: visible, labeled controls lower memory load and help occasional
  users understand what can happen here.
- Minimalism: every visible control competes with the scene, face, hook, or
  world material the page exists to support.

Prefer compactness when the action remains discoverable, labeled, reversible,
and attached to the object it changes. Prefer visibility when hiding the
control would make the user ask, "What can I do next?"

## Placement Rhythm

Controls should appear where the user naturally becomes ready to use them, not
only where the data model happens to expose them.

Think of each page as a small journey:

1. **Orient**: where am I, what object am I looking at, and what face am I
   wearing?
2. **Read or compare**: what context do I need before acting?
3. **Act**: what is the next writing, interest, reply, or management move?
4. **Continue**: where should I go after finishing this object?

Use that journey to decide placement:

- Put orientation controls near the start: breadcrumbs, current lens, active
  face, current state, and object identity.
- Put creation and commitment controls at the moment of intent: `Reply as
  Rogue` near the scene and composer, interest actions on hook detail, reserve
  actions on wanted detail.
- Put skim/navigation controls where they support browsing: previous/next
  scene links belong in the transcript header, after scene context and before
  the first post, because writers often skim the setup before deciding whether
  to hop to a nearby scene.
- Put attention-continuation controls after completion: `Previous unreplied`
  and `Next unread` belong at the end of a thread, where the writer has
  finished reading and is deciding what needs attention next. These controls
  follow the visible community attention queue, not the current board's local
  scene order.
- Put inspection controls beside the thing they explain: post profile notes on
  the post identity, facet filters near result sets, material context beside
  canon or event content.
- Put management controls behind the object but out of the emotional path:
  scene management, staff controls, material studio, archive/close/move.

Do not collapse a control just because it is secondary. Collapse it when it is
secondary **and** not needed at the current step in the journey. Likewise, do
not surface a control just because it is common. Surface it when the visible
page state makes the action feel timely.

Recent thread-page decision: breadcrumbs should have breathing room at the top.
Previous/next scene navigation is useful for skimming and should stay visible,
but it belongs with the transcript header rather than the breadcrumb row:
after scene context and before the first post. Queue navigation is different:
`Previous unreplied` and `Next unread` are attention actions, so they belong
under the last post as small left/right navigation buttons that can jump across
boards when the next obligation lives elsewhere.

## Thread Reader Control Pattern

Thread detail pages have three different kinds of movement, and they should not
compete for the same slot:

- **Orientation** belongs at the top: breadcrumbs, scene title, current board,
  current event, state badges, and active face. Give this area breathing room.
- **Local skim navigation** belongs with the transcript header: previous/next
  thread controls help a writer compare neighboring scenes after reading the
  scene setup, but before committing to the first post.
- **Attention navigation** belongs after the last post: previous unreplied and
  next unread are not local geography. They are queue actions for the moment
  after the writer has finished reading.

When a control pair has a directional meaning, preserve its physical side even
when only one side exists. A lone `Next unread` still belongs on the right; a
lone `Previous unreplied` still belongs on the left.

Stage actions should separate commitment, reading, and state:

- The main commitment stays large and labeled: `Reply as <face>` or `Join as
  <face>`.
- Secondary reading movement can be labeled and compact: `Read latest`.
- Reversible state toggles can sit beside the labeled action as short icon
  buttons when the state also appears elsewhere, such as a `watching` badge.
  Keep the accessible label and tooltip explicit (`Watch thread`,
  `Unwatch thread`), even when the visual button is only a symbol.

## Research Anchors

Use these as the background doctrine, not as a second design system:

- Nielsen Norman Group, Jakob's Ten Usability Heuristics:
  visibility of system status, recognition rather than recall, consistency,
  error prevention, flexibility for expert users, and aesthetic/minimalist
  design.
  <https://media.nngroup.com/media/articles/attachments/Heuristic_Summary1_A4_compressed.pdf>
- Interaction Design Foundation, Progressive Disclosure: defer advanced or
  rarely used features so users meet complexity in a sequence instead of all at
  once.
  <https://www.interaction-design.org/literature/book/the-glossary-of-human-computer-interaction/progressive-disclosure>
- W3C WAI Forms Tutorial: form controls need clear labels, instructions, and
  programmatic relationships; hidden labels are acceptable only when the visual
  purpose remains clear.
  <https://www.w3.org/WAI/tutorials/forms/>
- GOV.UK Design System form components: radios for one choice, checkboxes for
  several choices or toggles, selects as a last resort, and textareas for
  longer open text.
  <https://design-system.service.gov.uk/components/radios/>
  <https://design-system.service.gov.uk/components/checkboxes/>
  <https://design-system.service.gov.uk/components/select/>
  <https://design-system.service.gov.uk/components/textarea/>
- Atlassian Inline Edit: inline edit is a view mode that switches into editing
  in place on the same page.
  <https://atlassian.design/components/inline-edit>
- Material Design component guidance: menus are temporary choice surfaces,
  text fields must be identifiable/findable/legible, and sliders fit subjective
  ranges or intensity settings.
  <https://m1.material.io/components/menus.html>
  <https://m1.material.io/components/text-fields.html>
  <https://m1.material.io/components/sliders.html>

## Control Density Test

Before adding or condensing controls, answer these questions:

1. What is the primary story object on this surface: scene, face, plot hook,
   wanted hook, material, application, claim, reserve, or room?
2. What is the next likely action for the current viewer and active face?
3. Is the action frequent, rare, staff-only, destructive, reversible, or
   high-commitment?
4. Does the user need to compare choices before acting?
5. Does the control affect one small field, one whole object, or a workflow
   state visible to other writers?
6. Can the active face safely choose a default, or does the user need to pick
   a character, membership, or prospective concept explicitly?
7. Would hiding this control force recall, or merely reduce noise?
8. Can the compact version still be labeled for screen readers, keyboard
   reachable, and understandable on mobile?
9. Where in the journey does this action become useful: orienting, reading,
   acting, or continuing?

If the answers are unclear, keep the control visible and labeled until usage
patterns tell us what can safely collapse.

## Decision Matrix

| Pattern | Use When | Avoid When | Elbysodic Examples |
| --- | --- | --- | --- |
| Visible primary button | The page has one obvious next action, especially writing or commitment. | There are several equal actions or the action is rare/staff-only. | `Reply as Rogue`, `Start plotting room`, `Publish plot hook`, `Submit application`. |
| Visible secondary button or link | The action is common but not the main reason the page exists. | It is rare, dangerous, or only useful after other context is open. | `Watch thread`, `View related material`, `Edit hook` for the owner. |
| Icon plus text | The action is domain-specific, important, or not universally recognized. | The text repeats many times in a dense row and the icon is familiar. | `New plot hook`, `Reserve wanted`, `Mark caught up`. |
| Icon-only button | The action is repeated, low-risk, conventional, and has a stable tooltip/ARIA label. | The icon would carry product-specific meaning or irreversible work. | Search, close, expand/collapse, edit pencil in a repeated owner toolbar. |
| Overflow menu | Actions are rare, related, and secondary to the object. | The action is the next expected move or must be compared with nearby choices. | Archive, duplicate, move, close, request revision, staff moderation. |
| Disclosure panel | Optional complexity belongs near the object but should not interrupt reading. | The hidden content is required to complete the main task or continue the flow. | Facets, related material, advanced discovery filters, profile notes, material studio controls. |
| Inline edit, explicit pencil | A small set of owner-only fields can be edited in context, but editing mode should be deliberate. | The field is the primary text artifact or the action has social/workflow impact. | Plot hook status, room summary, character tagline, material metadata. |
| Click-to-edit immediately | A single short field is obviously editable, low-risk, and has clear save/cancel behavior. | The text is also a navigation link, is long-form, or edits affect public workflow state. | Hook title in an owner studio area, compact room label, draft title. |
| Full edit page or form | The object has several fields, validation, body text, permissions, or preview needs. | Only one small reversible property is changing. | Character profile edit, wanted hook edit, material edit, application forms. |
| Segmented control | A small, flat set of mutually exclusive modes changes the local view. | The choices navigate to separate stable routes. | `Open / Plotting / Closed` local hook filters. |
| Route tabs | Closely related routes are durable views of the same object or workspace. | The user is only filtering one list or jumping within a page. | Future character profile sections, director tool subsections. |
| Radio group | The user must choose exactly one option from a short, visible set. | Multiple choices are allowed, or the list is too long to scan. | Hook type, application type, visibility choice. |
| Checkbox group | The user can choose multiple options, or a setting is independently on/off. | Exactly one choice is allowed. | Facet selection, notification options, content warnings. |
| Select | Space is tight and the user is choosing one item from a known longer list. | The choices teach the user what the question means, or the list is short. | Time zone, status in an admin table, compact staff filter. |
| Combobox/autocomplete | The user must find an item from a large roster, faction list, material list, or facet vocabulary. | The list is short enough to show directly. | Character picker, related material picker, director facet lookup. |
| Text input | The answer is short, named, or structured. | The user needs prose, pitch, or long-form context. | Slug, title, prospective character name. |
| Textarea | The answer is prose, pitch, summary, or body copy. | A constrained choice would reduce uncertainty. | Plot hook body, wanted pitch, application response, post composer. |
| Slider or stepper | The value is a range, intensity, ordering, or numeric adjustment. | The exact value is important and easier to type. | Future theme intensity, reading density, maybe scene priority. |

## Inline Editing Rules

Inline editing is useful when it removes travel, not when it hides structure.

Use an explicit edit pencil that reveals editable fields when:

- The object has several fields, but only a few are likely to change often.
- The field is public, owner-only, or staff-only and should not invite casual
  accidental edits.
- The user benefits from reading the current value before deciding to edit.
- The page needs a calm reading mode most of the time.

Use immediate click-to-edit when:

- The field is a short title, label, status note, or ordering value.
- The editable text is not also a link.
- The save/cancel model is visible, keyboard accessible, and forgiving.
- Blur-save is safe, or there is an explicit save action near the field.
- The page shows immediate system status after save or validation failure.

Do not use inline edit for:

- Long-form posts, canon bodies, applications, or plot hook bodies that need
  preview and draft protection.
- Actions with social consequences, such as accepting an application,
  reserving a wanted, closing a room, or archiving a public object.
- Cross-object edits where the user must understand relationships before
  committing.

## Disclosure Rules

Collapse details when the content is useful but not always needed:

- Staff/director controls on reading surfaces.
- Facet assignment and related-material wiring after the object is created.
- Advanced filters after the default active-face result is useful.
- Audit/revision details when the current state is enough.

Keep details visible when they answer "what can I do next?":

- Reply/join/interest actions.
- Active-face defaults.
- Current workflow state.
- Continuation actions at the end of a finished reading flow.
- Empty states that teach the next useful action.
- Validation errors and required form instructions.

If a disclosure contains only one action and that action is the point of the
page, the disclosure is probably wrong.

## Icon Rules

Icons save space only when the meaning is already known or repeated enough to
be learned safely. They do not replace product language.

- Use icon-only controls for shell utilities, repeated row actions, and
  universal operations such as close, search, edit, delete, expand, collapse,
  previous, next, and more.
- Pair icons with text for PBP-specific verbs: plot, reserve, claim, watch,
  join, caught up, needs reply, waiting, application, face, and roster.
- Every icon-only control needs an accessible name and a hover/focus tooltip.
- Avoid icon-only destructive actions unless they live inside a labeled
  overflow menu or confirm step.
- Keep icons visually secondary to character identity, prose, and world
  material.

## Form Control Rules

Labels are part of the control, not decoration.

- Every input, textarea, select, checkbox group, and radio group needs a label
  or legend. Placeholder text is not a substitute.
- Put labels above text fields and textareas unless the shared component
  already provides an accessible floating label.
- Use fieldsets and legends for related radios and checkboxes.
- Write hint text only when it changes behavior: `Select all that apply`,
  `Optional`, `Visible to staff and the wanted creator`, or accepted formats.
- Prefer radios over selects for short meaningful lists because visible options
  reduce memory and comparison cost.
- Prefer checkboxes over multi-selects for multiple choices.
- Break up one vague textarea into smaller structured fields when a writer
  would otherwise wonder what kind of answer is expected.

## Elbysodic Defaults

Use these defaults unless a surface has a stronger local reason:

- Story-moving actions stay visible and text-labeled.
- Active-face actions should read as `as <face>` when that reduces choice
  pressure safely.
- Skim navigation can stay visible near the reading surface: previous/next
  thread controls help writers browse nearby scenes after they have enough
  scene context to decide. Prefer placing these controls in the transcript
  header when the local titles are short and bounded.
- State toggles can become compact icon buttons when the state is visible
  elsewhere and the button keeps a clear accessible label, such as watching a
  thread from the scene stage. Pair these with a nearby labeled action when
  possible: `[○] [Read latest]`, not a mystery icon floating alone.
- Attention navigation belongs after the transcript: `Previous unreplied` and
  `Next unread` are for moving across things that need attention after the
  reader has finished the current scene. Treat this as community-queue
  navigation, not same-board browsing.
- Owner and staff actions can collapse behind `Edit`, `Manage`, or an overflow
  when the page is primarily for reading or writing.
- Plotter and wanted pages should expose interest/room actions clearly; archive,
  close, duplicate, and move belong behind management controls.
- Character hubs should show the plotter path first, then tracker context, then
  lower-frequency management.
- Dense desks can use more compact controls than atmospheric world surfaces,
  but the current obligation must remain obvious.
- If a compact control is new to Elbysodic vocabulary, introduce it with text
  first. Collapse to an icon or disclosure only after the pattern is repeated.

## Review Checklist

When reviewing a new UI pass, scan for:

- The primary action is visible and labeled.
- Rare or staff-only actions do not dominate the story surface.
- No icon-only control carries unfamiliar PBP meaning.
- Hidden controls are not required to complete the page's main task.
- Inline edit has obvious focus, save, cancel, validation, and status behavior.
- Controls are keyboard reachable and have accessible names.
- Mobile layout does not turn controls into unlabeled fragments.
- The page still feels like a calm writing room, not a settings console.
