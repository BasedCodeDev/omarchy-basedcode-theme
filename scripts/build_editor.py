#!/usr/bin/env python3
"""Fix measured contrast problems in the stock VS Code template, retaining its tokens."""
import json, os, pathlib, shutil, subprocess, tempfile, tomllib
ROOT=pathlib.Path(__file__).resolve().parents[1]
c=tomllib.loads((ROOT/'theme/colors.toml').read_text())
with tempfile.TemporaryDirectory(prefix='basedcode-light-editor-') as temp:
    stage=pathlib.Path(temp)/'.local/state/omarchy/current/next-theme'
    stage.mkdir(parents=True)
    shutil.copy2(ROOT/'theme/colors.toml',stage/'colors.toml')
    subprocess.run(['/usr/share/omarchy/bin/omarchy-theme-set-templates'],env=dict(os.environ,HOME=temp,XDG_STATE_HOME=temp+'/.local/state',OMARCHY_PATH='/usr/share/omarchy'),check=True)
    theme=json.loads((stage/'vscode-theme.json').read_text())
theme['name']='BasedCode Light'
colors=theme['colors']
for key in ('focusBorder','list.focusOutline','settings.focusedRowBorder','menu.selectionBorder','menubar.selectionBorder'):
    colors[key]=c['accent']
for key in ('button.secondaryBackground','extensionButton.background'):
    colors[key]=c['selection']
for key in ('button.secondaryHoverBackground','extensionButton.hoverBackground'):
    colors[key]='#754382'
colors['button.hoverBackground']=c['bright_magenta']
colors['extensionButton.prominentHoverBackground']=c['bright_magenta']
colors['notebook.focusedCellBackground']=c['lighter_background']
for key in ('selection.background','editor.selectionBackground','terminal.selectionBackground','list.activeSelectionBackground','quickInputList.focusBackground'):
    colors[key]=c['selection']
(ROOT/'theme/vscode-theme.json').write_text(json.dumps(theme,indent=2)+'\n')
print('Built VS Code colour-only override: readable secondary buttons and solid focus indicators')
