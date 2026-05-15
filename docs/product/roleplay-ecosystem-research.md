# Roleplay Ecosystem Research

Status: product research landscape
Owner: Product and UX stewardship
Last updated: 2026-05-10

This document maps the wider online roleplay ecosystem Elbysodic should learn
from: forum PBP writers, Discord roleplayers, Reddit partner-search writers,
Tumblr indie and group roleplayers, TTRPG PbP players, MMO/live-server
roleplayers, and OC/art-world roleplayers.

It is a working synthesis, not a finished market study. It uses public
community artifacts, rules pages, directories, and discussion threads as
evidence. The next research step is direct interviews with roleplayers and
directors across these cultures.

Use `docs/product/roleplay-research-outreach-leads.md` alongside this document
for public writers, bloggers, platform builders, and community operators who
could become research interview or alpha/beta feedback candidates.
Use `docs/product/experience-direction.md` for the promoted product-experience
synthesis that turns this research into current design and surface guidance.

## Founder Baseline And Delta To Research

Elbysodic's founder baseline is forum PBP as the backbone: durable boards,
threaded scenes, rosters, faces, claims, reserves, wanted hooks, applications,
guidebooks, skins, archives, staff rooms, director ritual, and side-channel
touchpoints like cboxes, Bravenet chat, AIM, IC texts, and phone-call style
rapid beats.

The product bar is not "Discord but branded" and not "old forum with a nicer
skin." The bar is a durable PBP source of truth with sanctioned escape hatches
for lite rapid touchpoints. Quick chat, IC text threads, voice-call
transcripts, chatbox banter, or Discord-like coordination can support play, but
they should not displace scene continuity, face identity, privacy boundaries,
or the community archive.

The design bar must also move forward from the 2014 memory. Elbysodic should
preserve the depth of forum PBP, but the default product should feel as current
as the strongest modern RP-native competitors. RPHub is the clearest public
signal so far: clean, media-aware, roleplayer-specific software can exist in
this category. Elbysodic should meet or exceed that level of polish while
expressing its own studio/backbone perspective.

The research question is the delta since roughly 2014:

- Which forum-PBP rituals still create trust, continuity, and culture?
- Which old rituals were workaround labor that a product should make native or
  remove?
- Which modern Discord/Tumblr/Reddit norms are now table stakes?
- Which modern norms are signs of platform absence, not product desire?
- Which rapid-touch workflows should Elbysodic support as first-class adjuncts,
  and which should remain integrations or social context outside the source of
  truth?
- Is the ecosystem truly missing a dedicated PBP platform, or are existing
  communities satisfied with fragmented tools for reasons Elbysodic must
  understand before challenging?

## Research Caveats

- Public rules and directory pages show what communities claim and enforce,
  not everything participants privately value.
- Reddit and Tumblr posts are anecdotal signals. Treat them as discovery
  material, not population-level proof.
- Many roleplayers move across platforms. Segment by behavior and need, not by
  assuming one person belongs to only one platform culture.
- Adult, ERP, fandom, original-character, tabletop, and live-server roleplay
  can have sharply different safety expectations. Elbysodic should support
  director-defined boundaries without flattening them.

## Landscape At A Glance

| Segment | Where They Gather | Cultural Center | Product Center |
| --- | --- | --- | --- |
| Legacy forum/PBP board roleplayers | Jcink, ProBoards, XenForo, Iwaku, RpNation, Roleplayer Guild, RPGnet, private boards | Long-form scenes, board identity, applications, claims, plotters, archives | Boards, threads, IC/OOC separation, rosters, guidebooks, BBCode, staff workflows |
| Discord text roleplayers | Private servers, fandom servers, hub servers, Tupperbox-style proxy use | Immediacy, social presence, channel-based scenes, low setup | Channels, roles, bots, character proxies, OOC chat, tickets, notifications |
| Reddit partner-search writers | r/roleplaying, r/RoleplayPartnerSearch, similar subs | Finding compatible 1x1 partners and moving to Discord | Prompts, preferences, boundaries, writing samples, vetting, DMs |
| Tumblr indie/group roleplayers | Muse blogs, RP mains, tags, communities, Discord hybrids | Aesthetic identity, mutuals, rules/about pages, asks, memes, boundaries | Blogs, pinned rules, bio/dossier pages, tags, reblogs, asks, sideblogs |
| TTRPG PbP players | RPGGeek, RPGnet, Myth-Weavers, RPoL, Discord/Avrae servers | Asynchronous campaigns, GM authority, dice, sheets, IC/OOC threads | Character sheets, dice, maps, private text, turn order, recruitment |
| MMO/live-server roleplayers | FFXIV, WoW, GTA/FiveM, RedM, private Discords | Immersion, events, IC/OOC boundary, shared world continuity | In-game scenes, event calendars, Discord coordination, reports, lore policy |
| OC/art-world roleplayers | DeviantArt groups, Toyhouse worlds, fandom wikis, private Discords | Character ownership, visual identity, group canon, activity checks | Character profiles, art galleries, worlds, applications, activity proof |
| Hybrid community operators | Jcink plus Discord, Tumblr main plus Discord, forum plus cbox | Keeping the old rituals while meeting writers where they already are | Org hub, chat space, guidebook, taken lists, apps, promotion, live support |

## Segment Notes

### Legacy Forum And PBP Board Roleplayers

What they value:

- A durable home for a community's world, scenes, canon, applications, wanted
  ads, claims, reserves, rosters, member groups, and archives.
- Long-form writing with stable URLs, formatting, preview, and time to think.
- Community aesthetic control: skins, postbits, face images, member-group
  colors, guidebook styling, and board atmosphere.
- Rituals that make the board feel governed and alive: applications, activity
  checks, event prompts, plotters, shipper pages, wanted ads, claims, reserves,
  awards, affiliates, and updates.
- IC/OOC separation. The thread is the scene; OOC and planning belong nearby
  but should not corrupt the transcript.

Pain points:

- Old forum stacks are powerful but brittle: mobile behavior, theme breakage,
  inaccessible skins, manual templates, and code-copying burden.
- Directors maintain too much by hand: claims, reserves, wanted status, event
  lists, application queues, activity checks, and member directories.
- Writers lose the daily thread loop inside scattered boards, manual trackers,
  Discord pings, and "where did I owe a reply?" uncertainty.
- Board history is valuable but hard to search, export, migrate, or preserve.
- Joining can feel like ritual overload: rules, claims, app template, Discord,
  taken list, reserves, plotting, and face setup live in separate places.

Elbysodic opportunity:

- Preserve board identity, long-form scenes, and archive trust while making
  board-running objects native instead of handcrafted forum posts.

### Discord Text Roleplayers

What they value:

- Low friction. Writers can join a server, read channels, chat OOC, and start
  planning quickly.
- Social presence: online members, quick replies, reactions, pings, OOC
  rapport, and fast staff support.
- Channel geography: a server can mirror locations, factions, DMs, staff
  rooms, applications, or scene categories.
- Character proxying through bots or conventions that let one account speak as
  several characters.
- Private tickets and mod channels for support, consent, application review,
  or reports.

Pain points:

- Discord is a social stream, not a durable writing archive. Scenes, lore, and
  decisions sink into channel history.
- Channel sprawl and notification fatigue make it hard to know what is active,
  owed, waiting, or canon.
- Character identity is often bolted on through bots, nicknames, roles, or
  manual formatting.
- Server governance can be opaque: staff decisions, rule changes, approvals,
  and handoffs may happen in DMs or tickets with little durable context.
- Discovery is fragmented across Disboard, Tumblr ads, Reddit posts, and word
  of mouth.

Elbysodic opportunity:

- Offer Discord's immediacy where it matters, but keep scenes, faces, wanted
  handoffs, applications, and canon in structured, recoverable objects.

### Reddit Partner-Search Writers

What they value:

- Fast discovery across a wide pool of potential 1x1 partners.
- Explicit preference matching: age, genre, fandom, pairing, length, tense,
  post frequency, boundaries, platform, samples, and dealbreakers.
- Low initial commitment. A writer can pitch, vet, and decline before creating
  a server or building a character.
- Directness: many posts foreground communication expectations and boundaries.

Pain points:

- Ghosting is a dominant recurring pain. Writers describe losing partners
  before planning, after moving to Discord, or mid-story.
- Compatibility is hard to verify from a prompt alone. Writing style,
  commitment level, and communication norms often mismatch.
- Search is noisy. Posts repeat the same metadata in prose and disappear into
  feed churn.
- No shared continuity. Once a match moves to Discord, Reddit no longer
  supports the story, archive, or obligation loop.
- Safety and age boundaries are mostly self-declared and hard to enforce.

Elbysodic opportunity:

- Treat partner discovery as structured compatibility and commitment-setting,
  then carry the match into a durable scene/plotting workflow instead of
  abandoning it to DMs.

### Tumblr Indie And Group Roleplayers

What they value:

- Muse identity and aesthetic presentation: pinned posts, rules pages,
  dossiers, graphics, icons, tags, headcanons, and blog themes.
- Consent and boundary rituals: mutuals-only, private/selective, do-not-reblog
  tags, rules-before-interaction expectations, content warnings, and block
  respect.
- Open-ended discovery through tags, starter calls, memes, asks, promos, and
  RP main blogs.
- The ability to be independent: one writer can run one muse, a multimuse, or
  a small network without joining a formal board.

Pain points:

- Etiquette is powerful but implicit. Newcomers must learn unwritten rules or
  risk blocks and social friction.
- Notifications and tags are unreliable as a workflow system.
- Threads, asks, headcanons, and rules can scatter across blog pages,
  sideblogs, dashboards, and Discord.
- Mutual status and reblog rules are meaningful but platform-native controls do
  not map cleanly to RP consent.
- Theme setup and accessibility vary widely.

Elbysodic opportunity:

- Make muse/face identity, boundaries, rules, and interaction preferences
  explicit product objects while preserving aesthetic control and selective
  interaction.

### TTRPG Play-By-Post Players

What they value:

- Asynchronous campaign play with a GM/DM, rules system, character sheets,
  dice, maps, IC/OOC threads, and private information.
- Clear recruitment status: open, full, apply, invite-only, seeking players,
  play in progress.
- Durable campaign records and the ability to lurk/read active games.
- Mechanical support where needed, but not at the expense of narrative flow.

Pain points:

- Tool fragmentation: sheets in one place, dice in another, maps elsewhere,
  OOC in Discord, scenes in forum threads.
- Pace management is hard: turn order, inactive players, private information,
  and GM workload can stall campaigns.
- Long threads become difficult to navigate without first-unread, summaries,
  issue/scene breaks, or state markers.
- Game/system requirements can make onboarding intimidating.

Elbysodic opportunity:

- Learn from PbP's explicit state, sheets, private text, and recruitment
  clarity, while staying focused on freeform PBP as the product center.

### MMO And Live-Server Roleplayers

What they value:

- Immersion and embodied character presence in a shared world.
- Strong IC/OOC boundaries, anti-metagaming norms, consent, and staff reports.
- Events, factions, venues, ranks, and community calendars.
- A sense that losing, conflict, or consequence can produce better story.

Pain points:

- The game client is not built for long-term story continuity, search, canon,
  applications, or writer obligations.
- Discord becomes the coordination layer, but not the archive.
- Staff must police metagaming, harassment, off-server conduct, and IC/OOC
  leakage across multiple platforms.
- Character role visibility can accidentally reveal information that should be
  covert or unknown in character.

Elbysodic opportunity:

- Build a story-first continuity layer that understands IC/OOC separation,
  events, factions, and private knowledge without relying on game-server hacks.

### OC And Art-World Roleplayers

What they value:

- Character ownership, design credit, galleries, profile pages, worlds,
  relationship links, and visual identity.
- Group canon with applications, activity checks, seasonal events, ranks,
  factions, prompts, and staff-approved plot consequences.
- Consent around character use, godmodding, major injury/death, and canon
  impact.
- Creative output beyond text: art, comics, profile sheets, moodboards, and
  design trading.

Pain points:

- Character profile sites are not always good scene engines.
- Art/activity proofs create staff workload and anxiety.
- Canon updates and character state can scatter across comments, images,
  journals, Discord, and forum threads.
- Design ownership, AI/art theft, credit, and permission boundaries are
  culturally sensitive.

Elbysodic opportunity:

- Respect character-as-asset and character-as-voice at the same time: profiles,
  media, relationships, claims, canon state, and scenes should reinforce each
  other.

### Hybrid Community Operators

What they value:

- The board/forum as an authoritative hub and Discord/Tumblr/ads as social,
  support, and recruitment channels.
- Flexible play styles: forum threads, Discord scenes, cboxes, events, and
  sometimes both board and chat RP.
- Fast answers for newcomers without sacrificing the structured guidebook and
  application ritual.

Pain points:

- The "real" community state is split across too many places.
- Newcomers cannot tell which source is authoritative.
- Staff update the same fact repeatedly: taken canons, reserves, app status,
  wanted status, event state, rules, and Discord pins.
- Activity can look high in Discord but low on the board, or vice versa.

Elbysodic opportunity:

- Become the source of truth for story, identity, and workflow, while leaving
  room for Discord/Tumblr/social platforms as outreach and chat layers.

## Cross-Culture Values

These are the strongest throughlines across the ecosystem.

### 1. Character Identity Is Sacred

Roleplayers care deeply about who is speaking, who owns that character, what
the character knows, how the character is presented, and what boundaries apply
to the character.

Product implication:

- Elbysodic's face, roster, active-face, character hub, and public authorship
  model should remain the product center, not a profile add-on.

### 2. Consent And Boundaries Are Infrastructure

Across Tumblr etiquette, Discord rules, forum policies, and OC groups,
roleplayers repeatedly define boundaries: no godmodding, no metagaming, read
rules first, respect blocks, ask before joining, warn for content, do not
control another character, do not reblog/interrupt what is not yours.

Product implication:

- Boundaries should become visible state and workflow, not just prose buried in
  rules pages.

### 3. Continuity Is The Cultural Treasure

Threads, scenes, canons, character arcs, events, claims, reserves, and
relationship history are the emotional archive. Discord gives immediacy but
weak continuity; forums give continuity but often require manual labor.

Product implication:

- Elbysodic can win by combining durable scenes with lightweight, structured
  continuity helpers.

### 4. Discovery Is Broken But Essential

Every platform has a discovery workaround: interest checks, Tumblr tags, RP
mains, Disboard, Reddit prompts, partner requests, recruitment threads, ads,
affiliates, and directory pages.

Product implication:

- Wanted hooks, plotter hooks, facets, availability, writing style, genre,
  relationship lanes, and prospective interest should become a structured
  discovery graph.

### 5. Commitment Is Ambiguous

Roleplayers need to know who is actually available, interested, active, waiting,
slow, on hiatus, open, closed, full, reserved, or ready for scene. Most
platforms leave that to social guesswork.

Product implication:

- Statuses like `needs reply`, `waiting`, `caught up`, `watching`, `raised
  hand`, `in plotting`, `ready for scene`, `reserved`, and `filled` are not
  minor labels. They are trust tools.

### 6. Aesthetic Control Is Cultural Belonging

Jcink skins, Tumblr themes, character graphics, face claims, banners, member
groups, and icons are how communities express tone. But raw customization can
also destroy readability, accessibility, and safety.

Product implication:

- Appearance Studio should frame safe art direction as culture preservation,
  not mere theming.

### 7. OOC Community Makes IC Writing Possible

Writers want plotting, friendship, boundaries, staff help, support channels,
and vibe checks. The OOC layer is part of the writing engine, not unrelated
chat.

Product implication:

- Elbysodic should keep backstage, plotting rooms, application notes, and staff
  support object-bound and private where appropriate.

### 8. Safety And Pseudonymity Are Not Edge Cases

Roleplay spaces often involve identity exploration, mature themes, minors/adult
boundaries, fandom conflict, harassment risk, and parasocial intensity.

Product implication:

- Global account, community membership, public face, staff role, private notes,
  and cross-community identity must stay separated in policy and UI.

## Overlapping Pain Points

| Pain Point | Seen In | Product Interpretation |
| --- | --- | --- |
| Ghosting and unclear commitment | Reddit, Discord, Tumblr, 1x1 forums | Need lightweight availability, response expectations, pause/drop states, and low-shame exits. |
| Wrong identity or character confusion | Discord, forums, Tumblr, MMO RP | Active face and authorship must be visible before every commitment. |
| Lost scenes and weak archives | Discord, Tumblr, live RP | Durable scene objects, first-unread, summaries, exports, and search matter. |
| Manual board-running work | Jcink/forums, hybrids, OC groups | Claims, reserves, apps, wanted, events, and rosters should be native workflows. |
| Discovery noise | Reddit, Tumblr tags, Disboard, forums | Structured facets, wanted hooks, plotters, and compatibility filters. |
| Onboarding overwhelm | Forums, Tumblr, TTRPG PbP, OC groups | Guided first-face path and staged reading of rules, claims, reserves, and apps. |
| Hidden social rules | Tumblr, Discord, OC groups | Make boundaries, preferences, and interaction permissions explicit. |
| Channel/thread sprawl | Discord, forums, hybrids | Object-bound workrooms and stable navigation by user job. |
| Privacy side channels | Discord roles, notifications, forums, recovery pages | Counts, sidebars, search, denial pages, and notifications need privacy tests. |
| Aesthetic fragility | Jcink, Tumblr, OC groups | Safe tokens, media slots, variants, and health warnings. |
| Staff burnout | Directors, moderators, GMs | Studio should surface "what needs a director" and automate routine state. |
| Platform lock-in or collapse | Old forums, hosted boards, Discord-only play | Export, migration posture, and durable archives are trust features. |

## Renaissance Thesis

Elbysodic should not try to be a better Discord, a prettier Jcink, a Reddit
partner-search clone, or a TTRPG VTT. The unifying opportunity is:

> A roleplay-native studio where character identity, scene continuity,
> discovery, consent, community atmosphere, and board-running work are first
> class, while social chat and external platforms remain optional edges.

The renaissance bet is that roleplayers do not need another generic forum or
chat room. They need a product that understands the rituals they already built
by hand and removes the maintenance burden without flattening the culture.

## Product Bets To Unify Modern PBP

### 1. Make The Face Layer Universal

Deliver:

- Explicit active face in the shell.
- `Reply as <face>` and `Join as <face>` actions.
- Character hubs with recent posts, hooks, wanted ties, claims, applications,
  relationships, and queue context.
- Prospective face support for wanted interest before a character exists.

Why it unifies:

- Forums get proper character authorship, Discord gets character proxy clarity,
  Tumblr gets muse identity, OC groups get character ownership.

### 2. Turn Discovery Into Story Intent

Deliver:

- Wanted hooks, plotter hooks, relationship lanes, facets, event roles,
  availability, and prospective interest.
- Search/filter by genre, fandom/original, writing pace, length preference,
  content boundaries, roster needs, and open scene state.
- Public discovery that leads into private handoff instead of a dead ad.

Why it unifies:

- Reddit prompt matching, forum interest checks, Tumblr promos, and Discord
  hub ads all become structured pathways into play.

### 3. Build Backstage As The Missing Middle

Deliver:

- Object-bound plotting rooms attached to wanted hooks, scenes, applications,
  claims, events, or character relationships.
- Clear handoff states: raised hand, in plotting, ready for scene, scene
  started, waiting, paused, filled.
- Participant/owner/staff privacy by default.

Why it unifies:

- Discord gives planning energy; forums give archives. Backstage can give both
  without turning every interaction into a public thread or hidden DM.

### 4. Make Commitment Gentle But Visible

Deliver:

- Writer availability, slow/hiatus/paused states, drop/close etiquette,
  waiting/needs-reply accuracy, and low-shame handoff messages.
- Reminder and queue tools that reduce guilt instead of increasing pressure.

Why it unifies:

- Ghosting is not solved by punishment. It is reduced by expectation-setting,
  status visibility, and humane exits.

### 5. Replace Manual Board Admin With Studio Workflows

Deliver:

- Director launch checklist.
- Native claims, reserves, applications, events, guidebook material, wanted
  outcomes, activity health, and operations status.
- Studio organized by jobs: open realm, review apps, move casting, maintain
  world, keep queues healthy.

Why it unifies:

- Directors from forum, Discord, and OC groups all carry administrative burden.
  Elbysodic can make that labor visible, structured, and less exhausting.

### 6. Preserve The Archive And Make It Portable

Deliver:

- Stable scene URLs, export posture, backup guidance, migration path,
  first-unread, caught-up state, summaries, canon links, and private-safe
  recovery.

Why it unifies:

- The emotional archive is why old boards mattered and why Discord-only play
  feels fragile.

### 7. Let Communities Look Like Themselves Safely

Deliver:

- Appearance Studio with tokens, media slots, presentation variants, alt text,
  contrast warnings, and no raw CSS/script requirement.
- Character and board media that carry meaning without breaking controls.

Why it unifies:

- Jcink/Tumblr/OC cultures need aesthetic identity; modern product quality
  needs accessibility and safety.

### 8. Support Platform Bridges Without Becoming Dependent

Deliver later, after core flows:

- Discord notification or digest integration.
- Import helpers for board/thread archives, wanted lists, claims, or character
  profiles.
- Shareable public wanted/realm pages for Tumblr/Reddit promotion.
- Export packages that directors can actually understand.

Why it unifies:

- Communities will not abandon every existing social surface. Elbysodic should
  become the source of truth, not demand cultural isolation.

## What Elbysodic Should Not Do

- Do not become a generic community SaaS with "projects", "members", "tasks",
  and "tags" replacing faces, scenes, rosters, claims, reserves, wanted, and
  plotting.
- Do not make Discord the canonical archive. Discord can be a bridge, not the
  source of truth.
- Do not assume all roleplayers want the same pace, literacy norm, genre, age
  boundary, content policy, or application strictness.
- Do not treat safety as only moderation. Authorship clarity, private notes,
  consent, side-channel privacy, and pseudonymity are also safety.
- Do not over-automate social nuance. Some handoffs should make expectations
  visible without forcing writers into punitive metrics.
- Do not expose raw CSS, scripts, or arbitrary templates as the price of
  aesthetic freedom.

## Research Questions To Validate Next

### Interviews

- What platform did you start roleplaying on, and what do you miss from it?
- Where does your current RP actually happen: thread, channel, DM, doc, game,
  or all of the above?
- What makes you trust a new community enough to apply or post?
- What do you currently track manually?
- What causes you to drop, pause, ghost, or leave?
- What do you wish staff/directors understood about your writing flow?
- What does a good application or first-face onboarding feel like?
- What makes a wanted ad or prompt actually convert into a scene?
- What information must stay private for you to feel safe?
- What would make you migrate a community away from your current setup?

### Usability Tests

- Newcomer finds a realm, reads enough to decide, and starts a first face.
- Writer returns after two weeks and finds what they owe.
- Hook hunter moves from wanted detail to private plotting to ready-for-scene.
- Director opens a realm and gets to "safe to invite writers".
- Staff reviewer handles an application revision without leaking notes.
- Safety-boundary tester switches communities and confirms staff/face state.

### Competitive Audits

- Jcink sandbox board: applications, claims, reserves, skin, Discord handoff.
- Discord-only RP server: channel taxonomy, Tupperbox setup, staff tickets,
  activity rules.
- Reddit partner-search flow: prompt structure, vetting, Discord migration.
- Tumblr indie muse: rules/about, mutuals-only, tags, memes, boundaries.
- TTRPG PbP campaign: recruitment, IC/OOC threads, sheets, dice, private info.
- OC/art RP group: applications, activity checks, character ownership, events.

## Implications For The Existing User Panel

The current panel should expand beyond internal Elbysodic roles. Add or
explicitly invoke these ecosystem lenses when evaluating major product bets:

- Discord Migrant: values immediacy, OOC social presence, channel geography,
  and character proxy ease; fears archive loss and channel sprawl.
- Reddit 1x1 Seeker: values compatibility, direct boundaries, low-commitment
  discovery, and reliable communication; fears ghosting and mismatched effort.
- Tumblr Indie Muse: values rules/about pages, aesthetic identity, selective
  interaction, and consent rituals; fears implicit etiquette traps and
  notification failure.
- TTRPG PbP GM/Player: values recruitment status, sheets, dice, private info,
  and turn clarity; fears stalled games and tool fragmentation.
- OC/Art Group Member: values character ownership, media, activity proof,
  group canon, and consent around major plot effects; fears art theft and
  staff burden.

These lenses should complement, not replace, the current Active Scene Writer,
New Face Applicant, Hook Hunter, Community Director, Staff Moderator,
Safety-Boundary Writer, and Returning Regular panelists.

## Sources

- Roleplayer Guild homepage and forum taxonomy:
  <https://www.roleplayerguild.com/>
- RpNation homepage and forum taxonomy:
  <https://www.rpnation.com/>
- Iwaku Roleplay 101 and terms:
  <https://www.iwakuroleplay.com/help/roleplay/>
  <https://www.iwakuroleplay.com/help/terms>
- RolePlay onLine homepage:
  <https://rpol.net/>
- RP Repository homepage:
  <https://www.rprepository.com/>
- RPGGeek Play By Forum guides:
  <https://rpggeek.com/wiki/page/Play_By_Forum>
  <https://rpggeek.com/wiki/page/One_Thing_Play_By_Forum>
- RPGnet Roleplay-By-Post forum:
  <https://forum.rpg.net/index.php?forums%2Froleplay-by-post-play-forum.31%2F=>
- Storytellers' Circle forum pages:
  <https://storytellerscircle.com/>
  <https://storytellerscircle.com/forums/>
- Tumblr roleplay etiquette and community pages:
  <https://www.tumblr.com/chainsxwsmile/687908445767286784/tumblr-roleplay-etiquette-dos-and-donts>
  <https://rulesofroleplay.tumblr.com/faq>
  <https://www.tumblr.com/communities/browse/roleplay>
- Tumblr/Jcink/Discord hybrid examples:
  <https://www.tumblr.com/denouementrpg>
  <https://www.tumblr.com/bluehourrp>
- Reddit roleplay discussion and partner-search examples:
  <https://www.reddit.com/r/roleplaying/comments/1ak0gnw>
  <https://www.reddit.com/r/RoleplayPartnerSearch/comments/16o8xoo>
  <https://www.reddit.com/r/RoleplayPartnerSearch/comments/13wfbqd>
- Discord/live RP rules and bot-adjacent references:
  <https://providence-rp.com/rules/>
  <https://garnet-roleplay.gitbook.io/guide/rules/core-principles-and-server-etiquette/remaining-in-character-ic>
  <https://docs.medievaldiscord.com/ooc-mechanics/out-of-character-and-in-character-roles>
  <https://elysiumrp.fandom.com/wiki/About_Elysium>
  <https://rpmm.wikidot.com/general-information>
- DISBOARD play-by-post tag:
  <https://disboard.org/servers/tag/play-by-post>
- DeviantArt and Toyhouse OC/art roleplay references:
  <https://www.deviantart.com/viralremix/art/So-You-Want-to-Join-an-RP-Group-299443345>
  <https://www.deviantart.com/domain-of-the-wolf/journal/Group-Rules-425665757>
  <https://www.deviantartsupport.com/kb/en/article/does-deviantart-allow-role-play>
  <https://toyhou.se/>
