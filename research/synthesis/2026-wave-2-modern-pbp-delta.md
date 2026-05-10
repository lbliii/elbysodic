# 2026 Wave 2 Modern PBP Delta

Status: public-source synthesis
Last updated: 2026-05-10
Confidence: medium

This wave tests the founder baseline from
`research/synthesis/2014-delta-agenda.md`: durable forum PBP as backbone, with
lite rapid-touch escape hatches for chatbox, IC text, AIM-like, phone-call, or
Discord-like exchanges.

Scope: public pages only. No private servers, private boards, private Discords,
outreach, or scraping. Jcink-hosted boards were partly inaccessible through the
browser, so this wave used public directories and public ads as proxies.

## Executive Read

The ecosystem is fragmented, not dead.

The strongest updated claim is:

> Modern roleplay has active communities and serious tools, but no obvious
> dominant platform owns the full PBP-native source-of-truth studio layer:
> durable scenes, face identity, rosters, claims, reserves, wanted hooks,
> applications, guidebooks, archives, privacy, rapid touchpoints, and
> director/staff operations in one coherent product.

The most relevant pattern is not "forums versus Discord." It is source of
truth versus touchpoint. Discord-era tools are strong at immediacy, presence,
identity proxying, and OOC coordination. Legacy PBP systems are stronger at
durable records, IC/OOC structure, character sheets, game archives, and
long-form pace. Modern RP communities appear to compose both, often with manual
workarounds.

## Source Map

| Source | Segment | Signal | Confidence |
| --- | --- | --- | --- |
| <https://rphub.co/> | FFXIV / MMO RP platform | Modern RP-native platform with characters, communities, events, art, forum, blog, roadmap, and in-game plugin | high |
| <https://rphub.co/blog/introducing-rphub-open> | RP platform builder | Self-hostable single-community version, portable characters, community-owned instances | medium-high |
| <https://rphub.co/blog/we-are-moving-away-from-discord> | RP platform builder | Feedback and product direction moved out of Discord because Discord loses trackable decisions and excludes privacy-averse users | high |
| <https://rphub.co/roadmap> | RP platform | Blocking, muting, forum, feedback hub, notifications, event integration, mod tools | high |
| <https://rphub.co/communities> | MMO RP discovery | Communities expose status, tags, content warnings, recruitment, events, members, gallery, guestbook | medium-high |
| <https://www.rprepository.com/> | Broad RP platform | Characters, forums, groups, chats, privacy around character ownership, broad style support | high |
| <https://www.rprepository.com/help/getting-started-guide> | Broad RP platform | Character profiles began as persistent story sheets; private groups can own forums/chats | high |
| <https://rpol.net/> | TTRPG/freeform PbP platform | Alias characters, sheets, portraits, dice, maps, private threads/text, groups, large active game corpus | high |
| <https://www.roleplayerguild.com/> | Forum PBP | Active public forum categories by writing intensity, interest checks, 1x1, tabletop, nation RP | high |
| <https://www.roleplayerguild.com/topics/4959-formatting-interest-checks-and-the-first-ooc-post> | Forum PBP guide | Interest-check/OOC/character-sheet tab conventions, IC/OOC separation, template labor | medium |
| <https://forum.rpg.net/index.php?forums%2Froleplay-by-post-play-forum.31%2F=> | TTRPG PbP forum | IC and OOC threads remain explicit active structure | medium-high |
| <https://rpggeek.com/wiki/page/One_Thing_Play_By_Forum> | TTRPG PbP guide | Recruitment, IC/OOC threads, randomizer, yearly initiatives, lurking as learning | medium |
| <https://jcinkdirectory.com/list.php> | Forum directory | Hundreds of active listed Jcink forums, many recent 2026 additions | medium |
| <https://rpings.tumblr.com/> | Jcink/Tumblr ad culture | Ads still use index, Discord, face claims, want ads, guidebook, activity rules, profile apps | medium |
| <https://roleplayindex.com/> | Ecosystem directory | Public index of forum, Discord, Tumblr, resource, and RP platform entrypoints | medium |
| <https://tupperbox.app/> | Discord identity tool | Character proxying, groups, dashboard, autoproxy, edits/deletes, logging | high |
| <https://tupperbox.app/guide/proxying> | Discord identity tool | Proxying, multiproxying, autoproxy, no true anonymity, query/audit paths | high |
| <https://tupperbox.app/guide/commands/proxy> | Discord identity tool | Proxy enable/disable can be scoped by server, category, channel, or thread | high |
| <https://tupperbox.app/guide/server-config> | Discord identity tool | Server logging and permissions are core moderation primitives | high |
| <https://pluralkit.me/> | Discord identity tool | Pseudo-account proxying for systems and also RP-style use cases | medium-high |
| <https://www.tumblr.com/chainsxwsmile/687908445767286784/tumblr-roleplay-etiquette-dos-and-donts> | Tumblr RP etiquette | Rules pages, about/dossier pages, mutuals-only, no reblogging uninvolved threads/headcanons | medium |
| <https://www.tumblr.com/rulesofroleplay> | Tumblr RP etiquette | Ghosting, notification unreliability, policies around dropped threads and boundaries | medium |
| <https://www.reddit.com/r/roleplaying/comments/1ak0gnw> | Reddit RP discourse | Ghosting is normalized enough to shape vetting and moving-to-Discord behavior | medium |
| <https://www.reddit.com/r/RoleplayPartnerSearch/comments/1reyvsl/looking_for_a_longterm_roleplayer_on_discord/> | Reddit partner search | Posts encode age, timezone, cadence, writing expectations, OOC, Discord/Chatzy, no-ghosting boundary | low-medium |

## What Changed Since The 2014 Baseline

### 1. Discord became the social runtime

Current public signal repeatedly points to Discord as the place people move for
1x1 writing, OOC coordination, server-based RP, and quick communication. Reddit
partner posts often use Reddit as discovery and Discord as the actual writing
or planning space. Tumblr and Jcink ads frequently include Discord links or
mention active Discord chat.

Product implication: Elbysodic does not need to become Discord, but it must
respect that modern writers expect fast coordination, pings, presence, and
low-friction side discussion.

Classification: `escape hatch` and `integration`, not `backbone`.

### 2. Character proxying became table stakes in chat contexts

Tupperbox and PluralKit-style proxying show a mature workaround for one user
speaking through multiple identities in fast chat. Important details:

- Writers need fast character selection without logging into separate accounts.
- Scoped proxy behavior matters by server, channel, category, or thread.
- Autoproxy and sticky/latch modes reduce repeated command friction.
- Moderators still need auditability; proxying is not true anonymity.
- Misconfiguration can cause wrong-identity anxiety.

Product implication: Elbysodic's active face model is correct, but chat-like
surfaces need a faster face-switching language than long-form composer flows.
Wrong-face prevention and visible current face should be treated as P0 trust
work.

Classification: `backbone` for face identity; `escape hatch` for live proxying.

### 3. Old forum rituals persist, but much of the labor is still manual

RPNation examples, Roleplayer Guild templates, Jcink ads, and forum directories
still show applications, reserves, roles, OOC threads, character sheets, face
claims, activity rules, tags, index/guidebook/want-ad links, and writing
standards. These rituals are not obsolete. They are still how communities
communicate seriousness, taste, availability, and trust.

The weak point is that many rituals are encoded as posts, templates, links, and
manual staff updates.

Product implication: Elbysodic should not erase applications, claims, reserves,
wanted hooks, guidebooks, plotters, or activity expectations. It should turn
them into native objects with state, permissions, reminders, and handoffs.

Classification: `backbone`.

### 4. Existing serious PbP platforms already prove some primitives

RPoL is especially important because it already exposes many hard PbP primitives:
unlimited game aliases, sheets, portraits, custom dice, maps, private threads,
private text, groups, and a large active corpus. RP Repository proves another
branch: character profile persistence, secret ownership, broad play-style
support, forums, chats, private messages, and groups.

Product implication: Elbysodic should not assume it is inventing PBP tooling.
It is choosing a narrower, more opinionated product center: roleplay-native
community studio and writing continuity, probably closer to a premium modern
Jcink/RPR/RPoL hybrid than a greenfield category.

Classification: competitive/adjacent `backbone` evidence.

### 5. Discovery is everywhere, but trust is weak

Reddit partner search shows high upfront filtering: age, timezone, writing
length, tense/person, genres, OOC expectations, platform, response cadence,
writing samples, "more than hello" tests, and anti-ghosting language. This is
not just preference. It is self-defense against mismatch, low-effort replies,
and abandonment.

Product implication: Elbysodic discovery should surface compatibility and
commitment expectations before people move into a plotter, private room, or
scene. "Raise interest" should include enough structured signal to reduce
low-fit handoffs without forcing a full application.

Classification: `backbone` for wanted/discovery; `social convention` for
personal vetting rituals.

### 6. Boundary language is more explicit and more culturally loaded

Tumblr etiquette stresses rules pages, dossiers/about pages, mutuals-only,
selective interaction, content warnings, not reblogging uninvolved threads, and
respecting headcanons. RPHub's public SFW/NSFW moderation discussion shows that
platform-level policy, public-page discoverability, external links, mature
themes, and safety disclosure are genuinely hard, not copywriting details.

Product implication: Elbysodic needs explicit visibility and audience controls
for rules, boundaries, mature themes, content warnings, applications, and
private notes. It also needs product standards for what cannot be advertised
publicly even if communities want to configure it.

Classification: `backbone` for consent/privacy; `reject` for unsafe public
advertising and raw community self-rule that exposes the platform.

### 7. The "single community install" model is externally validated

RPHub's rphub/open post is a strong independent signal: self-hosted or
single-community instances solve community autonomy, content-rule control,
longevity, portability, and operator trust. It also validates Elbysodic's MVP
shape: one community per install, but with architecture ready for tenant-aware
future growth.

Product implication: Elbysodic should lean into "your realm, your archive, your
standards" while preserving exportability and avoiding lock-in fear.

Classification: `backbone`.

## Product Bets Strengthened

### -1. AI can make PBP newly viable

The founder thesis that PBP plus AI is "gold" is plausible and strategically
important. Traditional forums placed a large operating burden on directors:
moderation review, activity checks, stale threads, NPC support, summaries,
application review, wanted matching, graphics, and continuity work. AI can
reduce that burden if Elbysodic gives it structured PBP context and strict
human-in-the-loop boundaries.

The strongest AI opportunities:

- nightly or report-triggered moderation briefs for staff
- director-controlled NPC and setting drafts
- stale-thread/inertia prevention prompts
- generated face graphics, posters, banners, and character sheets
- scene recaps and continuity proposals
- wanted-hook and application review assistance

The product risk is equally large: AI that silently judges, posts as a player,
mutates canon, exposes private context, or floods scenes with generic prose
would break the trust that PBP communities rely on.

Product implication: AI should become a Studio layer, not a novelty feature.
Use `docs/product/ai-studio.md` before designing or implementing AI-assisted
moderation, NPCs, stale-thread prompts, generated media, recaps, continuity, or
writer/director assistants.

Classification: `backbone` product opportunity with strict safety envelope.

### 0. RPHub raises the competitive design bar

RPHub is the strongest modern competitor signal in this wave because it is not
only RP-native; it looks current. Its public surfaces are clean, image-rich,
fast to understand, and visibly designed around characters, communities,
events, galleries, a forum, a roadmap, and the Glance plugin. The lesson is not
to copy RPHub's dark purple visual language. The lesson is that RP-native
software no longer gets permission to look dated just because old forum tools
were powerful.

Product implication: Elbysodic's default experience must feel contemporary
before a director touches Appearance Studio. Forum backbone cannot mean forum
nostalgia. The brand should communicate a premium studio layer for writers and
directors: calm, legible, atmospheric, media-aware, mobile-conscious, and
operationally precise.

Classification: `backbone` design requirement.

### A. Forum backbone is still right

The forum backbone should remain canonical:

- boards and scene hubs
- scenes/threads
- IC/OOC separation
- faces and rosters
- guidebooks and director material
- applications
- claims and reserves
- wanted hooks and plotters
- activity/commitment state
- archives and export
- staff/director workflows

### B. Rapid touchpoints need their own state model

Do not treat quick exchanges as generic comments. Classify them by story
consequence:

- `canon micro-scene`
- `non-canon banter`
- `IC text`
- `IC call transcript`
- `OOC plotting`
- `status/presence`
- `external Discord reference`

Each type needs a visible relationship to face, participants, privacy, and
archive behavior.

### C. "Needs reply" is not enough; pace state should be richer

PBP advice sources keep returning to momentum. Elbysodic should eventually
model:

- needs writer
- needs director/staff
- waiting on cast
- waiting on decision
- waiting on roll/system
- ready for scene
- paused
- stale
- complete
- gracefully exited

### D. Discovery should be compatibility-first

Partner search and wanted hooks should capture:

- age/audience policy where relevant
- writing length/style
- pace/cadence
- timezone or usual free windows
- genre/fandom/facet
- boundaries and content posture
- desired commitment
- sample or recent post link where appropriate
- OOC preference
- open/filled/reserved/plotting status

### E. Elbysodic needs privacy as visible UX

Users should understand whether something is public, community-only,
members-only, participant-only, staff-only, owner-only, private draft, or
external. This matters for Tumblr-style boundaries, RPHub-style public policy,
and Tupperbox-style proxy auditability.

## Product Risks Updated

### Existing platforms may cover more than expected

RPoL, RPR, RPHub, and Roleplayer Guild each own part of the space. Elbysodic's
position must be crisp: not "we are the only PBP tool," but "we are the
PBP-native studio layer for running a community as a durable writing world."

RPHub also sets a visual expectation risk. If Elbysodic ships with dated
forum-era defaults, even correct PBP primitives may read as old software rather
than a modern roleplay studio.

### Discord replacement framing is a trap

RPHub explicitly moved feedback out of Discord because Discord is poor at
trackable product discussion, but still keeps Discord as hangout context. That
is the right distinction. Elbysodic should replace Discord only where Discord is
misused as the system of record.

### Public safety policy will be a product-defining stance

RPHub's SFW discussion shows a hard platform truth: allowing communities to set
their own rules does not remove platform responsibility for public pages,
search indexes, linked pages, moderation load, or legal/payment/host risk.
Elbysodic should provide knobs inside an opinionated policy envelope.

### Private community health is invisible from public pages

Public directories can prove activity and vocabulary, but not retention,
private Discord culture, moderation trust, director burnout, or why communities
choose one tool over another. Interviews are required.

## Updated Research Gaps

- Direct interviews with current Jcink/forum directors.
- Walkthroughs of private or semi-private Discord RP servers with consent.
- Interviews with Discord-first writers who never used forum PBP.
- RPR/RPoL user interviews: what works, what feels old, what they would never
  give up.
- RPHub operator/user interviews if available: portability, SFW policy, Glance,
  community instances, and "moving away from Discord."
- Tumblr indie writer interviews: what would a non-Tumblr product have to do to
  preserve selective interaction and aesthetic identity?
- Reddit partner-search interviews: what signals actually predict a good match?

## Near-Term Elbysodic Decisions To Consider

1. Keep the MVP centered on one community per install and make that feel like a
   deliberate strength, not a limitation.
2. Treat rapid-touch as a planned surface with strict story-state and privacy
   rules, not as an unstructured chat add-on.
3. Prioritize active face and wrong-face prevention across both long-form and
   quick-touch posting.
4. Make applications, claims, reserves, wanted hooks, guidebook, and plotters
   native before investing in broad public discovery.
5. Build a compatibility/interests layer for wanted hooks before a generic
   partner-search marketplace.
6. Draft platform policy early for public pages, mature themes, external links,
   privacy, and what community customization cannot override.
7. Add export/portability language to product posture; lock-in anxiety is real.
8. Position Elbysodic as the canonical archive/studio layer, not as a
   replacement for every social touchpoint.
