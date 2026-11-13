#!/usr/bin/env python3
"""Restore a recorded theme/background and desktop appearance settings."""
import argparse,json,os,pathlib,shutil,subprocess
ap=argparse.ArgumentParser(); ap.add_argument('backup',type=pathlib.Path); args=ap.parse_args()
record=json.loads((args.backup/'rollback.json').read_text())
target=pathlib.Path.home()/'.config/omarchy/themes/basedcode-light'
previous=args.backup/'previous-basedcode-light'
previous_link=args.backup/'previous-theme-symlink.txt'
if record['previous_theme']=='basedcode-light' and (previous.exists() or previous_link.exists()):
    replaced=args.backup/'replaced-basedcode-light'
    if replaced.exists(): raise SystemExit('This backup has already restored an older BasedCode Light package.')
    if target.exists() or target.is_symlink(): shutil.move(str(target),replaced)
    if previous.exists(): shutil.copytree(previous,target)
    else: target.symlink_to(previous_link.read_text())
env=dict(os.environ,OMARCHY_THEME_SYNC_FROM='basedcode-light-local-rollback',OMARCHY_THEME_WAIT='1')
subprocess.run(['omarchy','theme','set',record['previous_theme']],env=env,check=True)
subprocess.run(['omarchy','theme','bg','set',record['saved_background']],env=env,check=True)
for k,v in record['desktop_settings'].items():
    subprocess.run(['gsettings','set','org.gnome.desktop.interface',k,v],check=True)
print('Restored',record['previous_theme'])
