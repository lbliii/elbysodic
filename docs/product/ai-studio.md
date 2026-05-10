# AI Studio

Status: product doctrine draft
Owner: Product, safety, and UX stewardship
Last updated: 2026-05-10

AI can turn play-by-post from director-heavy forum labor into a living studio
system. The opportunity is real: nightly moderation review, staff triage,
NPC-assisted scenes, stale-thread prompts, character art, face graphics,
summaries, continuity aids, and director tooling all map naturally onto the
structured writing artifacts Elbysodic is already building.

The boundary is equally important: AI must support writers, directors, and
staff without erasing consent, authorship, privacy, character agency, or canon
trust.

AI is not the current strategy lead. The product spine in
`docs/product/strategy-spine.md` puts production trust, Realm Studio, Writer
Network, and manual Continuity Graph provenance ahead of AI-assisted expansion.
Use this document only after the relevant non-AI workflow, privacy, and review
contracts exist.

## Product Thesis

PBP plus AI is strongest when Elbysodic owns the durable source of truth:
community, membership, face, scene, thread, wanted hook, application, claim,
reserve, guidebook, event, staff note, and canon state.

Generic chat tools can generate text. Elbysodic can give AI the product context
that matters:

- Which community is this?
- Which face is speaking?
- What is public, participant-only, staff-only, or private?
- Which thread is stale, waiting, blocked, or ready?
- What canon has been accepted?
- Which NPCs, settings, threats, or rituals are director-approved?
- What tone, content limits, and safety boundaries govern this realm?

That context is the advantage.

## Non-Negotiables

- AI is opt-in where it affects story, face identity, moderation outcomes,
  canon, or generated art.
- AI suggestions do not become canon until an authorized human accepts them.
- AI moderation is triage and evidence gathering by default, not final
  judgment.
- AI never posts as a writer's face without explicit action from that writer.
- AI-controlled NPCs, setting voices, and chaos prompts are visibly labeled.
- AI has the minimum context needed for the task; staff/private data stays out
  unless the flow explicitly requires staff-authorized review.
- AI outputs are editable, rejectable, and auditable.
- Directors can configure allowed AI modes inside Elbysodic's safety envelope,
  but cannot use AI settings to bypass privacy, consent, or authorship rules.

## Product Lanes

### 1. Moderation And Safety Review

Use cases:

- Nightly review of new public or staff-visible posts.
- User-triggered report analysis.
- Pattern detection across batched posts: harassment, slurs, grooming signals,
  boundary violations, metagaming accusations, IC/OOC bleed, age-policy risk,
  spam, or escalating conflict.
- Staff brief generation: relevant excerpts, involved faces, involved
  memberships, prior reports, thread context, policy sections, and recommended
  next step.

Product rule:

AI should act as a staff analyst, not a judge. It can rank, summarize, cite,
and suggest. Staff decide.

Required UX:

- Show what content was reviewed.
- Show why it was flagged.
- Link to exact posts or private reports visible to that staff member.
- Separate "AI concern" from "staff action."
- Let staff mark false positive, needs human review, action taken, or policy
  gap.

Avoid:

- Auto-bans, auto-warnings, auto-locks, or invisible moderation scores in V1.
- Training or tuning on private community content without explicit consent.
- Letting ordinary users see AI safety labels that would expose staff process
  or private reports.

### 2. Director-Controlled NPCs

Use cases:

- Director-approved NPCs that can be invoked in a post or scene.
- Scene-local NPC replies that move logistics, atmosphere, or minor conflict.
- Event actors, shopkeepers, witnesses, monsters, messengers, officials,
  rumors, weather, venue staff, or environmental reactions.
- "Ask the setting" style prompts for approved lore or atmosphere.

Product rule:

AI NPCs belong to the community and director policy, not to the model. They
need permissions, allowed scenes, tone, canon limits, and posting rules.

Required UX:

- `Invite NPC`, `Request setting beat`, or `Ask director NPC` actions should
  be explicit.
- Output previews before posting.
- Label generated NPC/setting content.
- Keep NPC posts tied to an actor record: director-authored, AI-assisted,
  staff-approved, or generated draft.
- Support "non-canon until accepted" for experimental beats.

Avoid:

- AI resolving major player consequences without consent.
- AI speaking for a player face.
- AI inventing canon, secrets, injuries, deaths, relationships, or private
  knowledge without director-approved scope.

#### Scene Setup: AI NPC Participation

When writers start a two-player or small-group scene, they may want the setting
to push back: dementor-like threats in a wizard-school community, clone troopers
or drones in a space-opera community, venue staff at a gala, town gossip,
weather, monsters, guards, witnesses, or other director-approved NPC forces.

This should be a scene-start setting, not a hidden model behavior.

Candidate controls:

- `Enable NPCs`: off by default unless the community/director sets a scene
  type where NPCs are expected.
- `NPC scope`: choose from director-approved NPCs, factions, setting forces, or
  a custom scene-local prompt.
- `NPC prompt`: what the NPC/setting force is allowed to do in this thread.
- `Frequency`: `by trigger`, `intercut`, or `ordered`.
- `Review mode`: `draft first`, `participant approval`, or `director/staff
  approval` depending on community settings.
- `Canon level`: `canon`, `pending canon`, `non-canon exercise`, or
  `atmosphere only`.

Frequency meanings:

- `by trigger`: NPC drafts are generated only when a participant uses an
  explicit action such as `Request NPC beat` or when a configured scene event
  occurs.
- `intercut`: Elbysodic suggests an NPC beat after a configurable number of
  player posts or when the scene appears stalled.
- `ordered`: the NPC has a visible turn slot in the scene order.

Required guardrails:

- The thread header shows that AI NPCs are enabled.
- Participants can see the NPC scope before posting.
- Generated NPC beats preview before publication unless the community has a
  stricter director-approved automation mode for specific scene types.
- The model cannot introduce major irreversible consequences outside the scene
  scope.
- The model cannot speak as player-owned faces.
- The scene can pause, disable, or revise NPC settings.
- If a scene uses fandom concepts, the community supplies the fictional
  context; Elbysodic should store it as community/scene prompt material rather
  than platform-owned lore.

### 3. Inertia Prevention

Use cases:

- Detect scenes that are stale, waiting, circular, or missing an inciting
  action.
- Suggest next beats to the involved writers or director.
- Offer a "chaos prompt" that personifies the setting or introduces a small
  complication.
- Generate recap plus possible continuation hooks.
- Nudge the right actor: writer, cast, director, staff, or hook owner.

Product rule:

The chaos bot should enrich the canvas, not punish slowness or hijack agency.
It is a spark generator and director assistant, not a mandatory intervention.

Required UX:

- Staleness states should be visible: waiting on cast, waiting on decision,
  needs director, paused, stale, complete, or gracefully exited.
- Chaos prompts should be opt-in per community and per eligible scene type.
- Writers should be able to dismiss, snooze, request another prompt, or ask a
  director to review.
- Director settings should control tone, intensity, allowed stakes, and whether
  prompts can appear to writers directly.

Avoid:

- Shaming writers for slow replies.
- Auto-posting chaos into active scenes.
- Generating surprise danger, intimacy, injury, death, or rule-breaking content
  without consent and scope.

### 4. Creative Generation

Use cases:

- Face graphics, character posters, moodboards, banners, badges, location
  images, event art, wanted graphics, and guidebook visuals.
- Character-sheet drafting: appearance, voice notes, hooks, boundaries, wanted
  ties, relationship seeds, and application drafts.
- Director material drafting: premise, event copy, claims guide, reserves
  copy, application prompts, faction blurbs, and NPC seeds.

Product rule:

AI generation should reduce blank-page friction while preserving community
standards, credit norms, safety, and director control.

Required UX:

- Generated media should have source/provenance metadata.
- Communities should be able to require review before generated assets appear
  publicly.
- Character images should distinguish generated face graphics from face claims
  based on real people, actors, artists, or commissioned work.
- Prompts and outputs should obey the community's public/mature-content rules.
- Users should be able to regenerate, edit, discard, or mark as inspiration
  rather than final.

Avoid:

- Deepfake-like use of real people without clear policy.
- Style imitation controls that create artist-credit conflict.
- Public generated media that bypasses community moderation.
- Treating AI-generated appearance as identity proof.

### 5. Continuity And Studio Assistance

Use cases:

- Thread recaps and "what happened since I left?"
- Continuity extraction for director review.
- Canon proposal drafts from completed scenes.
- Claim/reserve conflict summaries.
- Wanted-hook matching and compatibility notes.
- Application review assistance.
- "What does this writer owe next?" queue explanation.

Product rule:

Continuity AI should draft, summarize, and point. Canon changes still require
human acceptance.

Required UX:

- Cite the scenes, posts, hooks, or materials used.
- Mark summaries as generated.
- Let directors accept, edit, or reject canon proposals.
- Keep public summaries separate from staff/private summaries.

Avoid:

- Silent canon mutation.
- Summaries that reveal private threads to unauthorized viewers.
- Using generated summaries as the only archive.

## Permission Model

AI features should be permissioned through `CommunityMembership` and community
roles, not global user status.

Candidate capabilities:

- `ai.view_suggestions`
- `ai.request_scene_prompt`
- `ai.request_npc_draft`
- `ai.publish_npc_post`
- `ai.review_moderation_flags`
- `ai.configure_realm_ai`
- `ai.generate_public_media`
- `ai.approve_generated_media`
- `ai.accept_canon_summary`

All AI work that touches community content must remain community-scoped.

## Audit And Provenance

Store enough metadata for trust:

- requester membership
- affected community
- affected face, scene, thread, hook, application, or material
- AI feature lane
- input scope summary
- output state: draft, dismissed, accepted, edited, published, flagged
- accepting/publishing membership
- created and accepted timestamps

Do not store raw prompts with private content unless the storage and privacy
contract explicitly allows it. Prefer structured references to source objects.

## Product Sequencing

Good early candidates:

1. Staff moderation brief for user reports.
2. Thread recap for authorized participants.
3. Director-only stale-thread suggestions.
4. Wanted-hook compatibility suggestions.
5. Generated character/profile drafting in private draft state.

Higher-risk later candidates:

1. AI NPC posting into live scenes.
2. Public chaos prompts.
3. Automatic moderation action.
4. Public generated media pipelines.
5. Cross-community learning or recommendation.

## Review Questions

Before adding an AI feature, ask:

1. Who requested the AI action?
2. Which community, membership, face, scene, or staff object scopes the action?
3. What private or staff-only data is included?
4. Is the output draft, suggestion, private note, public post, or canon?
5. Who can accept, publish, dismiss, or audit it?
6. What consent is required from participants?
7. What failure would break trust: wrong face, privacy leak, canon mutation,
   moderation harm, or generated-media misuse?
8. Can the feature work as human-in-the-loop first?
