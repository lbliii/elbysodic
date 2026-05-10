# Image Dimensions

This map translates Midjourney-style aspect ratios into Elbysodic product
surfaces. It is design-system guidance and CSS-token vocabulary, not a new
Appearance Studio or Blueprint contract.

## Ratio Tokens

| Ratio | Token | Use |
| --- | --- | --- |
| `21:9` | `--elbysodic-ratio-billboard` | World gateways, board/location stages, program mastheads, cinematic place identity. |
| `16:9` | `--elbysodic-ratio-widescreen` | Mobile hero fallback, thread stage media, video-like scene context, broad previews. |
| `7:4` | `--elbysodic-ratio-editorial` | Board posters, location cards, high-context editorial tiles. |
| `4:3` | `--elbysodic-ratio-card` | Compact board cards, material/supporting media, balanced discovery grids. |
| `1:1` | `--elbysodic-ratio-square` | Avatars, icons, badges, small symbolic objects. |
| `4:5` | `--elbysodic-ratio-portrait` | Character cards, face-forward roster surfaces, portrait crops. |
| `2:3` | `--elbysodic-ratio-poster` | Character profile posters, casting posters, promotional face sheets. |
| `1:2` | `--elbysodic-ratio-tall` | Rare tall editorial panels, mobile-first art crops, narrow feature banners. |

## Surface Rules

- Board/location stage: use `21:9` on desktop and `16:9` on mobile. The image
  carries place identity and should feel panoramic.
- Thread cards: the board/place image should fill the full card rail on
  desktop, then collapse to a `16:7` banner on mobile.
- Board poster cards: use `7:4` by default. Use `4:3` only for compact
  navigation cards where the title and tagline need more vertical room.
- Character profile poster: use `2:3` or `4:5` depending on how much dossier
  text overlays the image. Avoid putting high-chroma image detail behind prose.
- Post profile rail: use poster-like ratios for identity, but keep the prose
  column visually calm.
- Wanted/casting hero: use `4:5` or `2:3` for face-forward casting; use `7:4`
  when the hook is about a group, place, faction, or relationship.
- Network/program hero: use `21:9` for the first viewport signal, with a
  readable text overlay and no card-framed hero copy.

## Generation Notes

- Generate larger than display size so `object-fit: cover` can crop without
  visible softness.
- Keep the subject away from the outer 10 percent on all sides for surfaces
  with overlays.
- Avoid dense text in generated images; product text should be real HTML.
- Preserve a quiet zone in the lower third for board and thread overlays.
- If one image must serve multiple surfaces, make it at `16:9` and crop
  outward to `21:9` or inward to `4:5` only after checking the focal point.

## Current Implementation

The CSS tokens live in `src/elbysodic/web/static/elbysodic-theme.css`.
Current wired surfaces:

- board stage: `21:9` desktop, `16:9` mobile
- board poster: `7:4`
- compact board poster: `4:3`
- thread card poster: full-height desktop rail, `16:7` mobile banner

Not-yet-wired surfaces should use this map before new ratios are introduced.
