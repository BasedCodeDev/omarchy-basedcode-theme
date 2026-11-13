#!/usr/bin/env python3
"""Install locally with a timestamped rollback record; --apply selects the theme."""
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
    home=pathlib.Path.home(); state=home/'.local/state/omarchy/current'
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup=home/'.local/state/omarchy/basedcode-backups'/stamp; backup.mkdir(parents=True)
    previous=(state/'theme.name').read_text().strip()
    original_background=(state/'background').resolve()
    background=backup/('previous-background'+original_background.suffix)
    if original_background.is_file(): shutil.copy2(original_background,background)
    protected=['.config/omarchy/shell.json','.config/hypr/bindings.lua','.config/hypr/monitors.lua','.config/hypr/looknfeel.lua']
    hashes={p:hashlib.sha256((home/p).read_bytes()).hexdigest() for p in protected if (home/p).exists()}
    desktop={}
    for key in ('gtk-theme','icon-theme','color-scheme'):
        desktop[key]=subprocess.check_output(['gsettings','get','org.gnome.desktop.interface',key],text=True).strip()
    record={'schema_version':2,'installed_theme':'basedcode','previous_theme_identity':previous,'previous_theme':previous,'previous_background':str(original_background),'saved_background':str(background),'protected_sha256':hashes,'desktop_settings':desktop}
    (backup/'rollback.json').write_text(json.dumps(record,indent=2)+'\n')
    target=home/'.config/omarchy/themes/basedcode'
    if target.exists() or target.is_symlink():
        if target.is_symlink():
            (backup/'previous-theme-symlink.txt').write_text(os.readlink(target)); target.unlink()
        else: shutil.move(str(target),backup/'previous-basedcode')
    shutil.copytree(ROOT/'theme',target)
    (ROOT/'qa/local').mkdir(parents=True,exist_ok=True)
    (ROOT/'qa/local/last-backup.txt').write_text(str(backup)+'\n')
    print('Installed:',target,'\nRollback record:',backup,flush=True)
    if args.apply:
        # Scope installation to this machine even if the user has theme mirroring enabled.
        env=dict(os.environ,OMARCHY_THEME_SYNC_FROM='basedcode-local-install',OMARCHY_THEME_WAIT='1')
        subprocess.run(['omarchy','theme','set','basedcode'],env=env,check=True)
    for p,h in hashes.items(): assert hashlib.sha256((home/p).read_bytes()).hexdigest()==h,p+' changed unexpectedly'
if __name__=='__main__': main()
