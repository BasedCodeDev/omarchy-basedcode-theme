# BasedCode Light design

The approved direction extends the purple field from the supplied nodes.html background
into charcoal windows with light text, sampled from the supplied scene’s top bar. The name identifies the brighter
sibling of the Carbon theme; this is deliberately a native dark-mode application palette.

| Role | Colour |
|---|---|
| Working surface | `#1F241F` |
| Shell panels | `#272D27` |
| Side surfaces | `#191D19` |
| Deep background | `#141814` |
| Primary text | `#FFFFFF` |
| Muted text | `#C1A7CE` |
| Focus and active borders | `#D7A4E2` |
| Selection | White on `#663674` |

Muted red, green, ochre, blue and cyan distinguish syntax, diagnostics and diffs.
These functional colours are checked for contrast against the working surface.

The wallpaper uses a 285-degree gradient from #895395 to #30203E, matching the
warmer, brighter right side and soft plum left side of the supplied streaming scene.
The screenshot was used as a visual colour reference; its text and graphics are not bundled.
Soft corner illumination shifts gently over a periodic 16-second loop. The animation is
1080p/30fps; the matching still is 4K. Purple accents retain the approved mockup C palette; window surfaces match the scene’s top bar.

Shell panels, launcher, menu, notifications, controls, tooltips, popups, polkit and
lock preview share the same hierarchy. Omarchy generates terminal and editor integrations
from colors.toml. The VS Code colour override preserves native syntax mapping.
Generic applications use the native Adwaita-dark fallback; custom purple surfaces require
application theme support. User fonts, geometry, transparency and layout overrides remain
in effect. Lock styling does not alter authentication.
