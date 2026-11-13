# Current theme validation

The current palette passes its automated contrast and generated-configuration checks.
Detailed current results are in `qa/validation.json`, `qa/app-validation.json`, and
`qa/nvim-highlights.json`. Foot and Ghostty validate; Hyprland and Neovim Lua parse.
Aether is tested in isolation without user plugins.

The public desktop preview is a real 2560×1440 capture of Neovim, btop, a terminal
listing and GNOME Files on a dedicated workspace. Both variants use the same
geometry and public sample files. btop's process list is hidden and networking
is restricted to loopback. The bar is temporarily shown for capture; the original
bar visibility, theme, wallpaper and workspaces are restored afterward.

GNOME Files uses native dark application styling and Yaru-purple icons. It is not
claimed to use the custom terminal background. Previews demonstrate the installed
applications, while other supported applications have generated-configuration coverage.

Wallpaper validation is in `qa/motion-validation.json`. The dark theme defaults to
an exact solid #1F241F PNG; its earlier animation is optional. The light theme uses
the softened purple animation and a matching still. No new performance benchmark
is claimed. Historical captures and benchmark results are excluded from current claims.

No real password authentication, suspend/resume, or privileged polkit action was
tested. User configuration, layouts, monitor scaling and fonts are preserved.
