# Circle Terminals Token Map

Status: accepted direction
Created: 2026-05-10
Applies to: `src/elbysodic/web/static/elbysodic-theme.css`

Circle Terminals gives the default product theme a simple grammar:

```text
o --   opening post
o -    reply beat
o ---  continuing scene
```

In the app, those marks translate into structure, identity, and continuity
rather than decoration. The default theme should feel like a black-key studio
system with controlled cyan, magenta, amber, and green dye records.

## Token Audit

The current theme already has the right token families:

- Key structure: `--elbysodic-key-dark*`, `--elbysodic-key-light*`,
  `--chirpui-bg`, `--chirpui-bg-subtle`, `--chirpui-surface`,
  `--chirpui-surface-alt`, `--chirpui-surface-elevated`.
- Editorial containment: `--chirpui-border`,
  `--chirpui-border-subtle`, `--elbysodic-editorial-rule`.
- Identity and action: `--elbysodic-identity-dye`,
  `--elbysodic-identity-dye-hover`, `--elbysodic-identity-dye-dim`,
  `--chirpui-accent`, `--chirpui-primary`.
- Atmosphere and focus: `--elbysodic-atmosphere-dye`,
  `--chirpui-accent-secondary`, `--chirpui-focus-ring`.
- State language: `--elbysodic-state-needs-reply`,
  `--elbysodic-state-waiting`, `--elbysodic-state-caught-up`,
  `--elbysodic-state-watching`, `--elbysodic-state-private`,
  `--elbysodic-state-staff`, `--elbysodic-state-error`.
- Media and elevated ritual surfaces: `--elbysodic-glass-bg`,
  `--elbysodic-glass-border`, `--elbysodic-on-media-*`.

The adjustment is not a new token system. The work is to make these existing
tokens behave like the Circle Terminals mark: compact, legible, saturated only
where a roleplayer expects signal.

## Target Roles

| Product Role | Token | Direction |
| --- | --- | --- |
| Black key | `--elbysodic-key-dark*` | Move slightly closer to ink-black studio structure while keeping surface steps readable. |
| Porcelain key | `--elbysodic-key-light*` | Keep light mode luminous and editorial, not beige or generic white SaaS. |
| Face/reply identity | `--elbysodic-identity-dye` | Use magenta as the primary active/selected/identity signal. |
| World/thread atmosphere | `--elbysodic-atmosphere-dye` | Use cyan for focus, exploration, network atmosphere, and opening-thread signal. |
| Continuing scene | `--elbysodic-state-needs-reply` | Use amber for continuity pressure, warning, and needs-reply states. |
| Caught up | `--elbysodic-state-caught-up` | Use green only for calm success/safe state, never as general decoration. |
| Waiting | `--elbysodic-state-waiting` | Keep waiting as a cooler violet/blue transition state distinct from error or success. |
| Staff/private | `--elbysodic-state-staff`, `--elbysodic-state-private` | Keep backstage material low chroma and legible. |
| Error/destructive | `--elbysodic-state-error` | Reserve coral/red for errors and destructive outcomes. |
| Focus | `--chirpui-focus-ring` | Prefer cyan focus so keyboard movement reads as an aperture/thread signal. |

## Accepted Adjustments

- Dark mode should deepen the key blacks and calm card borders so the dye
  records feel precise instead of neon.
- Light mode should become a luminous porcelain/ink treatment. It should retain
  high-contrast text and avoid cream, sand, or monochrome blue.
- Magenta remains the primary Chirp accent because it best maps to face and
  reply identity.
- Cyan remains secondary, focus, network, and atmosphere.
- Amber becomes the continuity pressure color and should be more golden than
  brown in both modes.
- Green is a fourth Circle Terminals record only for safe/caught-up state.
- Staff and private state should use desaturated blue-gray tokens.
- Glass tokens are acceptable for shell/global/platform ritual surfaces only;
  prose, composer, applications, and staff/private review text stay on calm
  opaque surfaces.

## Proof

This map is grounded in the existing token families in
`elbysodic-theme.css`. Phase 1 is documentation-only and does not change app
behavior.
