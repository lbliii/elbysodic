# User Personas And User Panel

Status: product research guide
Owner: Product and UX stewardship
Last updated: 2026-05-10

This guide captures Elbysodic's working user model. It is not a substitute for
interviews, usability tests, analytics, or community feedback. Treat these
personas as product hypotheses grounded in the current mission, architecture,
privacy model, seeded QA personas, and active roadmap.

Use this guide when evaluating UX, flow, onboarding, navigation, writing
surfaces, Studio work, or product sequencing. Use
`docs/architecture/seed-personas.md` separately for browser QA identities.
Seed personas prove permission and route behavior; these personas represent
user intent, fear, expectation, and success.

## Research Basis

Current evidence:

- Elbysodic's root constitution and product mission.
- Wider roleplay ecosystem research in
  `docs/product/roleplay-ecosystem-research.md`.
- Modern PBP delta synthesis in
  `research/synthesis/2026-wave-2-modern-pbp-delta.md`.
- Simulated user panel synthesis in
  `research/synthesis/2026-05-10-simulated-user-panel.md`.
- Founder baseline and post-2014 delta questions in
  `research/synthesis/2014-delta-agenda.md`.
- Product guides for information hierarchy, navigation, control topology,
  appearance, paragraph rhythm, notices, and Program Blueprints.
- Architecture guides for tenant identity, security boundaries, rendered route
  privacy, and seed personas.
- Active plans for creator onboarding, wanted backstage, production readiness,
  Studio workflows, appearance, and public discovery.
- Seeded panel briefs and synthetic subagent critique across active writer,
  applicant, hook hunter, director, staff/safety, Discord migrant, and
  dedicated-platform/design-skeptic perspectives.

Validation gap:

- These personas still need real PBP community interviews, moderated task
  walkthroughs, and observation of directors running live boards.
- Until then, mark persona-driven claims as research assumptions when they
  justify roadmap priority or a large UX decision.

## V2 Research Updates

The second research wave sharpened these assumptions:

- The market is fragmented, not dead. Users may come from active forums,
  Discord servers, Reddit partner search, Tumblr RP, RPR/RPoL, RPHub, or
  private hybrid stacks.
- The central product tension is source of truth versus touchpoint. Elbysodic
  should preserve the durable PBP record while supporting quick coordination
  later.
- Active face and wrong-face prevention matter even more in a Discord/Tupperbox
  world where fast character proxying has trained users to expect quick
  identity switching.
- Discovery is trust work. Compatibility signals, boundaries, cadence, writing
  style, and anti-ghosting expectations are part of the job, not profile fluff.
- Directors need relief from manual board-running labor without losing
  community standards, aesthetic authority, or portability.
- Modern visual quality affects trust. If the product looks dated, users may
  read the primitives as old forum software even when the workflow is right.
- Archive/export confidence matters because many roleplay communities have
  survived platform churn, abandoned boards, private Discord sprawl, or lost
  history.

## Core Personas

### 1. The Active Scene Writer

Point of view: "I have scenes in motion and I need to know what I owe, what I
am waiting on, and which face I am wearing before I touch the composer."

Primary jobs:

- Enter a community and immediately understand current membership and active
  face.
- Find `needs reply`, `waiting`, `caught up`, watched, mentioned, and unread
  scenes.
- Distinguish the durable scene record from OOC or rapid-touch side chatter.
- Read the latest beat, understand cast and continuity, and reply as the right
  face.
- Keep long-form drafts, preview, safe markup, and character voice stable.
- Discover wanted hooks, plotter hooks, events, and facets relevant to the
  current roster.

Core journeys:

1. Community entry -> identity cluster -> Writer Desk -> next `needs reply`.
2. Scene card -> thread reader -> latest beat -> `Reply as <face>` -> preview
   -> post -> next unread or unreplied item.
3. Board/location -> atmosphere and open scenes -> join or watch -> queue.
4. Character hub -> face-specific queue, hooks, wanted ties, and recent posts.

Expectations:

- Actions name the face: `Reply as Rogue`, `Join as Rogue`, `Switch face`.
- `needs reply` and `waiting` match how writers think about obligations.
- Pace state is specific enough to explain whether a scene needs the writer,
  the cast, a director, a decision, or a pause.
- Staff and director controls do not dominate ordinary reading surfaces.
- Mobile still supports read latest, switch face, reply, and continue.
- The product feels current enough to trust for long writing sessions.

Anxieties:

- Posting as the wrong face.
- Losing a long draft or seeing preview differ from final render.
- Missing a reply, mention, watched update, or plotting-room handoff.
- OOC chatter, Discord, or side planning becoming the only place where story
  continuity is understandable.
- Facets, counters, badges, and controls drowning out story context.

UX questions:

- Can the writer always answer: where am I, who am I wearing, who is here, and
  what do I owe next?
- Is the active-face default obvious and reversible at the moment of posting?
- Does the composer preserve calm long-form writing flow?
- Does the page make the canonical source of truth clear when planning or
  rapid-touch context exists elsewhere?

### 2. The Invited Or New Face Applicant

Point of view: "I was invited or found the realm. I need to understand whether
this community is safe, active, current, and worth bringing a first face into."

Primary jobs:

- Understand premise, tone, rules, current event, scene hubs, and roster norms.
- Know whether this is an invite-only realm, public preview, request-access
  path, or director-provisioned account.
- Decide who can be played through wanted hooks, canon/OC policy, claims,
  reserves, facets, and application requirements.
- Draft or submit a first face without confusing account, membership, and
  character identity.
- Track application state, staff revision requests, claims, and reserves.
- Move from accepted face to first writing move.
- Evaluate fit before commitment: writing pace, post length, activity norms,
  boundaries, content posture, OOC expectations, and whether ghosting/off-ramps
  are handled humanely.

Core journeys:

1. Invite or request-access path -> realm preview -> guidebook/application
   guide -> wanted board -> start application.
2. Wanted-first path -> inspect hook -> prospective interest or reserve ->
   plotting room -> first scene.
3. Application -> first face draft -> claims/reserves -> submit -> staff review
   -> revise -> accepted face.
4. Accepted state -> default face -> character hub -> open scenes, wanted
   hooks, plotting, or queue.

Expectations:

- Onboarding says face, roster, claims, reserves, wanted, application, plotting,
  and scene.
- Primary actions are visible: `Start application`, `Reserve wanted`, `Submit
  application`, `Revise application`.
- Application status persists as a page state, not only a toast.
- Staff-only notes, applicant notes, and public movement states look distinct.
- Realm preview shows enough activity, tone, visual quality, and policy signal
  to judge whether the community is alive and well-run.
- Compatibility and boundary expectations are structured enough that the writer
  does not have to decode hidden Discord or Tumblr-era etiquette.

Anxieties:

- Accidentally exposing application or pitch notes.
- Not knowing whether a face is available, wanted, reserved, or blocked.
- Staff not seeing enough context, or everyone seeing too much.
- Getting accepted and not knowing where to start writing.
- Joining something that looks polished but has no durable archive, no staff
  clarity, or no real path into play.

UX questions:

- Can a no-face writer find the first-face path in under a minute?
- Does each applicant surface answer what is public, what staff sees, and what
  happens next?
- Do claims and reserves explain conflicts and expiry before commitment?
- Does the flow distinguish invited access from public application without
  making either feel like a generic signup funnel?

### 3. The Hook Hunter

Point of view: "I want a reason to write. I browse wanted hooks, plotters,
events, and facets until I can see a scene forming."

Primary jobs:

- Find playable openings by character, faction, event, relationship lane,
  location, or creator.
- Understand whether a wanted hook is open, reserved, in plotting, filled, or
  archived.
- Judge compatibility before raising a hand: cadence, writing length/style,
  tone, boundaries, OOC expectations, and desired commitment.
- Raise interest with an existing face or a prospective face.
- Move from interest to private plotting to a ready scene.
- Avoid public overcommitment before trust and availability are clear.

Core journeys:

1. Wanted board -> filtered hook -> safe public context -> raise hand.
2. Compatibility scan -> existing face or prospective concept -> private note.
3. Hook owner response -> plotting room.
4. Plotting room -> ready for scene -> linked scene -> writer queue.
5. Character plotter -> relationship hook -> watch, message, or scene start.

Expectations:

- Hook status and next action use PBP language: raised hand, plotting, ready
  for scene, scene started, reserved, filled.
- Prospective interest does not pretend the writer already owns a face.
- Public wanted detail shows safe movement signals without private notes.
- Plotting stays object-bound, not a generic DM replacement.
- The product makes the next handoff obvious before people drift to Discord or
  lose the thread in private messages.

Anxieties:

- Private interest notes or room links leaking to unrelated members.
- Raising a hand and then losing the handoff in a generic inbox.
- Hooks staying visually open after they are socially no longer available.
- Being forced into a public commitment before the idea is ready.
- Matching with someone whose cadence, boundaries, or writing style was never
  made visible.

UX questions:

- Can each viewer tell what stage the hook is in without seeing data they
  should not see?
- Does the hook owner have a clear next action for each raised hand?
- Does the interested writer know where the conversation moved?
- Are compatibility signals visible without turning wanted hooks into a dating
  profile or public negotiation?

### 4. The Community Director

Point of view: "I am opening and running a realm. I need Elbysodic to make the
board-running material native without turning my community into a generic SaaS
workspace."

Primary jobs:

- Open a realm with premise, scene hubs, guidebook material, wanted hooks,
  intake, claims, reserves, appearance, invites, and launch checks.
- Keep play moving through application review, claims, reserves, wanted
  backstage, plotting rooms, events, and scene handoffs.
- Reduce manual forum labor without giving up director judgment or community
  standards.
- Protect private data, membership-scoped staff power, and character ownership.
- Shape atmosphere through safe theme tokens, media, vocabulary, and approved
  variants.
- Turn play into continuity through reviewed, source-linked canon work.
- Preserve portability, backups, and export confidence so the realm does not
  feel trapped on another fragile platform.

Core journeys:

1. Claim realm -> choose guided builder or Blueprint preview -> build scene
   hubs -> write director material -> configure intake and claims -> set
   appearance -> invite staff/writers -> launch.
2. Studio home -> "what needs a director" -> applications, claims, wanted
   backstage, boards/materials, operations health.
3. Wanted hook -> raised hand -> plotting room -> ready for scene -> scene
   started.
4. Appearance Studio -> preview health warnings -> publish safe atmosphere.

Expectations:

- Studio is a production room organized by board-running work, not database
  tables.
- Blueprint apply follows a reviewed diff, explicit collision mode,
  fingerprint, transaction rollback, tenant, ownership, and audit contract.
- Staff power is always capability-gated through community membership.
- Appearance controls preserve readability, composer stability, permissions,
  and mobile layout.
- Defaults are polished enough to launch without a custom skin, while still
  allowing the realm to feel culturally specific.
- Public discovery and rapid-touch features never undermine the realm's
  canonical source of truth.

Anxieties:

- Launching before the realm has enough structure, guidance, and safety.
- Private applications, wanted notes, plotting rooms, notifications, or counts
  leaking.
- Staff power following a global account into the wrong community.
- Director-edited boards/materials disappearing after deployment or restart.
- Customization pressure pulling toward unsafe raw CSS or templates.
- Looking dated next to modern RP-native tools and losing trust before writers
  experience the workflow.
- Being locked into a hosted platform without a credible export or recovery
  path.

UX questions:

- Can the director immediately see launch status and next required setup work?
- Does Studio surface the first actionable queue item without becoming noisy?
- Are staff controls available but outside the emotional path of play?
- Does every setup choice clarify whether it changes the source of truth,
  public presentation, or only social coordination?

### 5. The Staff Moderator

Point of view: "I am trusted to keep the board safe and moving. I need precise
tools that do not leak staff state or make ordinary writers feel watched."

Primary jobs:

- Review applications, claims, reserves, reports, and private production rooms.
- Moderate thread lifecycle: pin, lock, move, archive, recover, or close.
- Help directors maintain queues and handoffs.
- See enough private context to act, but only inside this community and role.
- Leave clear state for writers without exposing staff-only reasoning.
- Resolve source-of-truth confusion when Discord, private messages, or rapid
  touchpoints create off-platform commitments.

Core journeys:

1. Staff Studio or operations lane -> pending work -> review detail -> action
   -> visible writer state.
2. Thread lifecycle issue -> staff controls -> confirmation -> updated state.
3. Application revision -> staff note -> applicant-visible request -> resubmit.

Expectations:

- Staff actions are capability-scoped and auditable.
- Dangerous actions use explicit confirmation and clear aftermath.
- Staff-only context does not appear in public catalog, search, sidebars,
  notifications, recovery pages, or mobile drawers.
- Writer-facing state is plain enough to reduce anxiety.
- Proxy-like or rapid identity features remain auditable enough for staff to
  resolve harm without exposing pseudonymous boundaries publicly.

Anxieties:

- Accidentally exposing private notes while trying to help.
- Acting with staff power in the wrong community.
- Hidden controls making urgent moderation work slow.
- Staff workflow copy sounding punitive or generic.
- Having to reconstruct what happened from screenshots, Discord logs, and
  scattered side channels instead of a reliable community record.

UX questions:

- Does the surface show the minimum private context needed for this staff job?
- Is the public aftermath clear without revealing private reasoning?
- Are staff actions visually behind story surfaces but easy to reach from
  Studio?
- Does the tool preserve enough provenance to act without making every writer
  feel surveilled?

### 6. The Safety-Boundary Writer

Point of view: "I use pseudonymous writing spaces because identity boundaries
matter. I will leave if global account, membership, face, staff, or private
state blur."

Primary jobs:

- Know which global account, community membership, and face are active.
- Keep membership identity, staff power, private rooms, applications, and
  notifications scoped to one community.
- Write or apply without revealing cross-community identity.
- Recover from denied/private routes without confirmation leaks.
- Understand whether character proxying, rapid-touch exchanges, or generated
  summaries are public, private, audited, or canon.

Core journeys:

1. Switch community -> identity cluster -> local membership and active face.
2. Public/private route attempt -> safe recovery -> no private title leak.
3. Notification -> target object -> only authorized detail.
4. Same global account with different roles -> no staff bleed.

Expectations:

- Public surfaces never reveal active face, unread counts, private queue,
  draft material, staff notes, private room names, or private application state.
- Counts, badges, sidebars, mobile drawers, and recovery pages obey the same
  privacy contract as detail pages.
- Character authorship and membership ownership are distinct in UI and policy.
- Public catalog pages disclose mature/content posture and community standards
  without exposing private applicant, staff, or member activity.

Anxieties:

- Cross-community identity leakage.
- Wrong-face posting.
- Notification or count side channels exposing private objects.
- Theme or client-side state smuggling private information into the DOM.
- Discord-style proxy habits making it unclear who can see the real account,
  membership, or author behind a face.

UX questions:

- Can a user always tell which identity layer is being used?
- Do outsider and same-user-different-community states render safely?
- Are private object titles absent from denial and recovery pages?
- Is every audience boundary visible before the user commits text, identity,
  or application details?

### 7. The Returning Regular

Point of view: "I have been away. I need to regain continuity without rereading
everything or feeling punished for absence."

Primary jobs:

- See what changed since last visit.
- Recover current obligations and waiting states.
- Re-enter scenes, plotting rooms, and events with context.
- Decide whether to reply, watch, mark caught up, or step away.
- Understand whether a stalled thread needs the writer, another participant,
  a director decision, or a graceful exit.

Core journeys:

1. Login -> Writer Desk -> missed mentions and watched updates.
2. Thread -> first unread -> cast and last beat -> reply or mark caught up.
3. Plotting room -> summary/state -> ready for scene or waiting.
4. Character hub -> recent posts and active hooks -> choose a re-entry point.

Expectations:

- First-unread and latest links work reliably.
- Queue language is forgiving: needs reply, waiting, caught up, watching.
- Context is close to action without turning every page into a recap wall.
- Paused, stale, complete, and exited states are humane and do not read as
  public shame.

Anxieties:

- Missing a social commitment.
- Being unable to tell whether a thread is active, paused, complete, or stale.
- Marking something caught up and losing a useful reminder.
- Returning to a community where important continuity moved to Discord and the
  canonical thread no longer explains what happened.

UX questions:

- Does the return path make continuity legible in one or two screens?
- Are caught-up and watched states reversible and understandable?
- Can a writer continue from the end of one thread into the next obligation?
- Are stale or paused states framed as continuity support rather than blame?

## Jobs-To-Be-Done Summary

| Job | Primary Personas | Product Promise |
| --- | --- | --- |
| Know who I am here | Active Writer, New Face, Safety Writer | Community membership and active face are always explicit. |
| Find what needs me | Active Writer, Returning Regular, Director | Desk and Studio surface obligations in PBP language. |
| Reply without breaking flow | Active Writer, Returning Regular | Composer, preview, draft, and face context stay stable. |
| Bring in a face | New Face, Director, Staff | Applications, claims, reserves, and first-face onboarding are clear and private. |
| Find playable hooks | Hook Hunter, Active Writer | Wanted, plotter, facets, and events lead to actual scenes. |
| Move interest into play | Hook Hunter, Director, Staff | Backstage handoffs are object-bound and privacy-safe. |
| Run the board | Director, Staff | Studio is organized around production work, not generic admin. |
| Preserve identity boundaries | Safety Writer, all personas | Tenant, membership, character, and staff boundaries hold across every surface. |
| Shape atmosphere safely | Director, Active Writer | Appearance creates mood without breaking readability or workflow. |
| Return after absence | Returning Regular, Active Writer | Read state and queue continuation restore continuity. |
| Verify fit before commitment | New Face, Hook Hunter, Reddit lens | Cadence, boundaries, writing style, and availability are visible enough to reduce mismatch. |
| Trust the archive | Director, Returning Regular, Safety Writer | Scenes, materials, plotting handoffs, and exports preserve the community record. |
| Separate source of truth from touchpoints | Director, Staff, Active Writer | Discord, chatbox, or rapid-touch context supports play without replacing canonical state. |
| Trust that this is modern software | Director, New Face, all personas | Defaults feel polished, mobile-conscious, and RP-native before customization. |

## Core User Journeys

### Daily Writing Loop

Trigger: a writer visits a community with scenes in motion.

1. Land in the community shell and confirm membership plus active face.
2. Scan Writer Desk for `needs reply`, `waiting`, watched, mentioned, and
   unread items.
3. Open the most relevant scene.
4. Read scene identity, cast, current state, and latest beat.
5. Reply as the active face, switch face deliberately, or mark caught up.
6. Continue to next unread or unreplied item.

Success signals:

- The writer never wonders which face will post.
- The next action is visible at the moment of intent.
- The writer can leave and resume without losing draft or queue context.

Failure modes:

- Generic `Submit` controls, hidden face state, broken preview parity, noisy
  cards, or inaccurate queue states.

### First Face Onboarding

Trigger: an invited or accepted writer has no playable face yet.

1. Enter through invite, request-access, or director-provisioned account.
2. Read premise, rules, application guidance, claims/reserves, and wanted
   openings.
3. Start a first face or express prospective wanted interest.
4. Draft application details and claim/reserve needs.
5. Submit, revise, or wait for staff review.
6. On acceptance, set default face and move to character hub, open scenes,
   wanted hooks, plotting, or queue.

Success signals:

- The writer understands account vs membership vs face.
- Claims/reserves are clear before commitment.
- Accepted state leads directly into writing.

Failure modes:

- Generic signup flow, hidden application status, unclear claim conflicts, or
  no practical next step after acceptance.

### Wanted Backstage Handoff

Trigger: a writer is interested in a wanted hook or plotter connection.

1. Browse wanted hooks by facet, event, creator, relationship lane, or status.
2. Inspect safe public context, availability, cadence, boundary, and
   commitment signals.
3. Raise interest with an existing face or prospective concept.
4. Hook owner or staff reviews private note and starts a plotting room.
5. Participants move the room to ready for scene.
6. A scene is created or linked; queues and notifications update.

Success signals:

- Each viewer sees the right stage and next action.
- Private notes and room links stay scoped to participants, hook owner, and
  casting-capable staff.
- The handoff feels like plot movement, not inbox maintenance.
- The hook does not require a Discord side quest to understand whether the idea
  is compatible.

Failure modes:

- Public note leaks, hidden room links, duplicated start-room actions, or stale
  hook status.
- The product captures interest but loses the next step, pushing the actual
  decision into DMs where the community record cannot see it.

### Realm Opening

Trigger: a director is creating the first real community.

1. Claim realm identity, slug, director membership, and launch status.
2. Choose Guided Realm Builder or Program Blueprint preview.
3. Create scene hubs and public/private board structure.
4. Write director material: premise, rules, application guide, event prompt.
5. Configure intake, claims, reserves, and first-face posture.
6. Set safe appearance and media.
7. Invite staff and writers.
8. Pass launch checklist and open the realm.

Success signals:

- Studio names what remains before launch.
- The realm is playable before writers arrive.
- Public preview does not leak staff/private material.
- The default public face feels current enough that directors do not need to
  skin the product before inviting writers.
- Backup/export posture is understandable before real writer data accumulates.

Failure modes:

- Launch before first-face path, unsafe Blueprint apply, raw theme controls, or
  manual SQL becoming the production workflow.
- A visually dated or generic public surface undercuts trust in the product
  before the director can prove the community's writing quality.

### Staff Review And Recovery

Trigger: private board-running work needs staff or director action.

1. Staff enters Studio or an object-local management surface.
2. Reads only the private context needed for the task.
3. Acts with community-scoped capability.
4. Writer-facing state updates without leaking internal notes.
5. Denied, inactive, outsider, and cross-tenant routes recover safely.

Success signals:

- Staff has enough context and clear action labels.
- Ordinary writers see only the safe result.
- Recovery pages reveal no private titles or notes.

Failure modes:

- Staff data in sidebars, notifications, public catalog, denial pages, or
  mobile drawers.

### Source-Of-Truth Check

Trigger: a flow introduces Discord-like coordination, chatbox behavior,
external links, generated summaries, rapid-touch scenes, or imported context.

1. Identify the canonical object: scene, plotting room, wanted hook,
   application, material, claim, reserve, event, or external reference.
2. Identify the audience: public, community, participant, owner, staff,
   director, private draft, or external.
3. Identify the consequence: canon, pending canon, non-canon, OOC,
   atmosphere, or unsupported side context.
4. Show what Elbysodic owns and what remains an external touchpoint.
5. Provide the next action inside the canonical object where possible.

Success signals:

- Users know where the durable record lives.
- Side chatter can enrich play without becoming the only source of truth.
- Staff and directors can audit commitments without exposing private context.

Failure modes:

- Important decisions exist only in Discord screenshots, DMs, hidden notes, or
  generated summaries that are not tied to source objects.

## Cross-Persona Expectations

- PBP vocabulary is product infrastructure: face, roster, scene, thread,
  plotter, wanted, claims, reserves, needs reply, waiting, caught up, watching,
  backstage, Studio, and director.
- Community, membership, and face state are always explicit before authorship
  or workflow commitment.
- Writer flow is text-first: readable prose, long-form composer, preview
  parity, local drafts, and stable layout.
- Privacy is visible, not merely enforced: users should understand what is
  public, participant-only, owner-only, staff-only, or private.
- Navigation has one job per surface: topbar for community modes, sidebar for
  local contents, breadcrumbs for lineage, local rails for in-object movement,
  and actions where intent forms.
- Studio is production work, not a generic admin table.
- Appearance may change atmosphere, but not permissions, visibility, required
  controls, contrast, or composer stability.
- Public discovery and onboarding must not obscure the practical path to first
  face and first scene.
- Every flow that references Discord, chatbox, imported context, AI, or other
  side touchpoints must say what Elbysodic treats as canonical.
- Compatibility signals belong close to discovery and wanted handoffs:
  cadence, writing style, boundaries, content posture, commitment, and OOC
  expectations.
- Default visual quality is part of trust. A dated public face can make users
  discount correct PBP primitives.
- Portability and recovery are user-facing trust promises, not only operator
  concerns.

## User Panel

The user panel is a reusable product-review device. It complements stewards;
it does not replace them.

Stewards protect contracts, architecture, tests, and domain boundaries. The
user panel represents user motives, trust, comprehension, and flow. If they
disagree, synthesize both: a panel finding should be accepted only when it can
be implemented within steward constraints or when a human explicitly chooses to
change the contract.

### Panelists

Use the smallest panel that matches the change:

- Active Scene Writer: daily writing, queues, composer, scene reading,
  character hubs, mobile catch-up, source-of-truth clarity.
- Invited/New Face Applicant: invitations, request access, first-face
  onboarding, applications, claims, reserves, fit evaluation.
- Hook Hunter: wanted hooks, plotter hooks, discovery, prospective interest,
  compatibility signals, backstage handoffs.
- Community Director: realm setup, Studio, boards, guidebook, events,
  appearance, launch checklist, portability, modern default quality.
- Staff Moderator: application review, claims/reserves, moderation, private
  workrooms, recovery states, provenance.
- Safety-Boundary Writer: pseudonymity, active face, cross-community identity,
  rendered privacy, notification/count side channels.
- Returning Regular: first-unread, caught-up, watched threads, continuity after
  absence, stale/paused state.

Add the rapid-touch lens when a flow introduces chatbox, IC text, AIM-like,
phone-call, live-chat, or Discord-like affordances:

- Rapid-Touch Writer: quick IC exchanges, small scene beats, OOC coordination,
  pings, and social presence that should support the forum-PBP backbone without
  fragmenting continuity, authorship, consent, or archive trust.

Add the AI scene lens when a flow introduces generated NPCs, setting beats,
stale-thread prompts, or AI-assisted continuity:

- AI-Assisted Scene Writer: opt-in NPC or setting participation that adds
  motion without taking over player agency, speaking for player faces, leaking
  private context, or turning non-canon suggestions into canon silently.

Add ecosystem lenses from
`docs/product/roleplay-ecosystem-research.md` when the product question is about
reaching, migrating, or unifying roleplayers from other platforms:

- Discord Migrant: immediacy, OOC social presence, channel geography,
  character proxying, scoped identity, notifications, and archive weakness.
- Reddit 1x1 Seeker: partner discovery, compatibility signals, direct
  boundaries, ghosting, writing samples, and Discord migration.
- Tumblr Indie Muse: rules/about pages, selective interaction, mutuals-only
  norms, tags, asks, aesthetics, and consent etiquette.
- TTRPG PbP GM/Player: recruitment, IC/OOC threads, sheets, dice, private
  information, turn clarity, and campaign pace.
- OC/Art Group Member: character ownership, galleries, activity checks, group
  canon, consent around major plot effects, and design credit.
- Hybrid Community Operator: forum/Jcink plus Discord/Tumblr workflows,
  duplicated updates, source-of-truth confusion, and newcomer support.
- Dedicated Platform Regular: RPR, RPoL, RPHub, or similar users who expect
  persistent profiles, aliases/faces, private groups, chats/forums, events,
  portability, moderation controls, and a product that feels actively
  maintained.
- Modern Design Skeptic: users who may like the thesis but will discount the
  product if the first public surfaces feel dated, generic, inaccessible, or
  visually less credible than modern RP-native competitors.

### When To Consult

Consult the panel for:

- New or changed onboarding, writer desk, composer, thread, board, character,
  wanted, plotting, application, claim, reserve, Studio, Appearance Studio, or
  public discovery flows.
- Any route or surface where active face, membership, staff role, private
  notes, notifications, queues, or recovery state affects comprehension.
- Product prioritization, roadmap sequencing, or UX reviews where user value is
  the main question.
- Major copy or navigation changes that could drift into generic forum/SaaS
  language.

Use all panelists for broad roadmap or whole-product reviews. Use two to four
panelists for focused UX changes.

### Subagent Prompt

When delegation is available and a user asks for user-panel review, spawn
independent panelist agents. Give each panelist one persona and this task:

```text
Act as the <panelist> for Elbysodic. Read AGENTS.md, the closest scoped
AGENTS.md, docs/product/user-personas-panel.md, and the files or screenshots
being evaluated. Advocate only from this user's point of view. Return findings
in User Panel Signal Format. Do not edit files.
```

For ecosystem panelists, also read
`docs/product/roleplay-ecosystem-research.md` and evaluate whether the flow
honors that platform culture's values while moving users toward Elbysodic's
source-of-truth model.

The implementing agent owns synthesis and decides accepted, deferred, duplicate,
or not-now findings.

### User Panel Signal Format

Use this format:

- Panelist:
- Flow:
- Severity: P0/P1/P2/P3
- User Job:
- Evidence:
- User Impact:
- Expected Experience:
- Recommended Change:
- Required Proof:
- Collateral:
- Confidence:

Severity guidance:

- P0: Trust-breaking privacy, wrong-face, data-loss, or unsafe public exposure.
- P1: Blocks a core journey such as first face, reply, application, wanted
  handoff, or director launch.
- P2: Causes repeated confusion, extra work, hidden next action, or vocabulary
  drift in a frequent flow.
- P3: Polish, clarity, or nice-to-have improvement that does not block the job.

### Synthesis Checklist

Before accepting a panel finding, answer:

1. Which user job is harmed?
2. Which persona or personas are affected?
3. Is this a daily core loop, onboarding loop, trust boundary, or edge case?
4. Does the recommended change preserve tenant, membership, character, staff,
   and privacy boundaries?
5. What proof is required: rendered test, service test, browser QA, copy check,
   accessibility check, screenshot, docs update, or no collateral?
6. Does the finding create conflict with a steward invariant?
7. Is this PR-sized, or should it become roadmap/not-now work?

### Evaluation Questions

Use these questions during product and UX reviews:

- Can the user identify community, membership, active face, object, state, and
  next action without reading hidden rules?
- Does the surface use PBP language instead of generic forum, SaaS, CRM, or CMS
  terms?
- Is the primary story object still the foreground, or did controls and counts
  take over?
- Does each actor see the correct state: anonymous, no-face member, ordinary
  member, owner, interested writer, room participant, staff, director,
  inactive member, outsider, and same-user-different-community viewer?
- Are private notes, staff context, draft material, application details,
  plotting-room links, unread counts, and notification targets safe from side
  channels?
- Does the journey continue after the action, especially after reply,
  application acceptance, wanted interest, scene creation, or caught-up state?
- Does mobile preserve the same essential identity, action, and privacy cues?
- Does Appearance Studio or community customization support atmosphere without
  breaking readability, contrast, labels, focus, or required controls?
- Does the flow make the canonical source of truth clear when Discord,
  chatbox, imported context, rapid-touch, or generated content is involved?
- Does discovery expose enough compatibility signal to reduce ghosting,
  mismatch, and low-fit handoffs?
- Would a user familiar with RPHub, RPR, RPoL, Tupperbox, or modern Discord RP
  read this as actively maintained roleplay software?
- Does the product communicate backup, export, or archive trust when a director
  or returning writer needs it?
