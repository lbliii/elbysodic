# Product Strategy Spine

Status: product doctrine
Owner: Product and stewardship
Last updated: 2026-05-15

This document is the top-level product alignment spine for Elbysodic. It
distills the mission, research synthesis, architecture contracts, and active
roadmaps into one strategic shape. Use it when deciding whether a new plan,
feature, steward finding, or implementation path strengthens the product or
pulls it toward a generic forum, SaaS dashboard, or chat replacement.

Use `docs/product/experience-direction.md` for the current product-experience
synthesis: Jcink/forum PBP source-of-truth depth, Slack-like layered context,
Netflix/Apple TV-like editorial discovery, RPHub-level modern polish, and
technicolor futurism translated into Elbysodic's tenant, privacy, active-face,
and PBP vocabulary constraints.

## Thesis

Elbysodic is the operating system for pseudonymous collaborative story worlds.

It preserves the durable play-by-post source of truth while making the work
around play native: directors shape realms, writers carry faces and
obligations, and completed scenes can mature into reviewed continuity.

The forum remains the heart of play, but the product is larger than a forum.
The strategic product is a roleplay-native studio layer for creating, running,
discovering, writing in, and preserving living PBP realms.

The experience direction is not a literal collage of references. Forum/PBP
carries the cultural backbone, layered app patterns keep scene and obligation
context close, editorial discovery helps writers choose realms and wants, and
technicolor futurism gives Elbysodic a modern visual point of view. The product
rejects Discord replacement framing, passive streaming behavior, nostalgic
forum skinning, and generic SaaS chrome.

## Three Pillars

### 1. Realm Studio

Realm Studio is the director and staff product. It turns board-running labor
into first-class workflows instead of leaving directors to maintain scattered
threads, spreadsheets, templates, and private notes.

It owns:

- realm identity, launch posture, and public preview readiness
- scene hubs, boards, world materials, events, and guidebook material
- roster intake, applications, claims, reserves, wanted hooks, and casting
- Studio operations, review queues, launch checklists, and staff visibility
- safe Program Blueprints, theme tokens, media slots, and appearance controls
- exports, backups, and recovery paths that protect community archives

Realm Studio should feel like production support for a living writing room, not
generic admin.

### 2. Writer Network

Writer Network is the writer-facing product across realms. It helps a writer
understand where they are, which membership and face are active, what they owe,
what they are waiting on, and where the next playable opening lives.

It owns:

- global login with community-local membership identity
- active/default face and roster context inside each realm
- `needs reply`, `waiting`, `caught up`, watched, unread, and mentioned states
- Writer Desk, My Threads, notification lanes, and safe continuation paths
- wanted hooks, plotters, applications, reserves, and plotting-room handoffs
- public discovery through realm cards, wanted pressure, genre/mood lenses, and
  request-access or invitation posture

Writer Network is not a generic social network. It should help writers find the
right face, scene, wanted hook, and realm while preserving pseudonymity and
community control.

### 3. Continuity Graph

Continuity Graph is the compounding memory layer. It connects authored play to
the story objects it changes without turning private writing, staff notes, or
tentative plotting into public canon.

It will own:

- completed scene outcomes
- source-linked canon entries and citations
- affected faces, locations, events, factions, claims, reserves, wanted hooks,
  plot hooks, and world materials
- proposal, review, approval, revision, visibility, and notification workflows
- later automation that can suggest drafts only after manual provenance and
  privacy contracts are proven

Continuity Graph is intentionally deferred behind production trust, rendered
privacy, transaction, and source-link proof. The first slice should be manual
scene outcomes, not automatic canon publication. The backend readiness gate
lives in `docs/architecture/continuity-graph-readiness.md`.

## Strategic Sequencing

Sequence work by trust, then daily usefulness, then network effects:

1. Production trust: login, tenant routing, session posture, persistence,
   backup/restore, CSRF, rendered privacy, and transaction boundaries.
2. Realm opening: first realm setup, director launch room, invite-first access,
   first-face onboarding, and safe public preview.
3. Daily writing: active face, queue, notifications, drafts, preview, read
   state, wrong-face prevention, and mobile writing confidence.
4. Board-running backbone: applications, claims, reserves, wanted lifecycle,
   plotting handoffs, Studio operations, and staff-safe review.
5. Public discovery: service-owned NetworkHome/catalog read model, realm cards,
   public wanted pressure, and signed-out privacy proof.
6. Appearance and portability: safe visual control, media slots, exports,
   backups, restore drills, and alpha operations.
7. Continuity Graph: manual outcomes, source-linked canon proposals, review,
   public canon surfaces, and only later assisted drafting.

## Product Tests

Use these questions when reviewing plans or implementation:

- Does this strengthen Realm Studio, Writer Network, or Continuity Graph?
- Does it preserve global user, community-local membership, and local face
  boundaries?
- Does every public or shared surface have a tenant-safe source of truth?
- Does it use PBP language and workflows instead of generic forum/SaaS terms?
- Does it reduce director labor without taking away community standards or
  aesthetic control?
- Does it help a writer know where they are, who they are wearing, and what
  they owe next?
- Does it avoid exposing private, staff, application, plotting, or tentative
  canon material?
- Is the work sequenced after the trust gates it depends on?

## Not The Strategy

- A generic forum skin.
- A Discord replacement.
- A public self-serve community builder before invite-first trust is proven.
- A marketplace before public catalog privacy and realm opening are solid.
- AI-generated canon, moderation, or writing before provenance, consent, and
  review workflows exist.
- Global characters, global staff power, or role checks detached from
  `CommunityMembership`.
