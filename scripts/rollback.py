#!/usr/bin/env python3
"""Restore current or pre-rename backups without confusing the two theme identities."""
import argparse,json,os,pathlib,shutil,subprocess
LEGACY={'basedcode':'basedcode-dark','basedcode-light':'basedcode'}
def resolve_record(record,backup):
    old=record['previous_theme']
    if record.get('schema_version',1)>=2:
        target=record.get('previous_theme_identity',old)
        installed=record.get('installed_theme')
    else:
        target=LEGACY.get(old,old)
        installed={'basedcode-backups':'basedcode','basedcode-light-backups':'basedcode-light'}.get(backup.parent.name)
    snapshot=backup/('previous-'+old)
    if not snapshot.exists():snapshot=None
    link=backup/'previous-theme-symlink.txt'
    if installed!=old or not link.exists():link=None
    return target,snapshot,link

def main():
    ap=argparse.ArgumentParser();ap.add_argument('backup',type=pathlib.Path);args=ap.parse_args()
    record=json.loads((args.backup/'rollback.json').read_text())
    name,previous,link=resolve_record(record,args.backup)
    target=pathlib.Path.home()/'.config/omarchy/themes'/name
    if previous is not None or link is not None:
        replaced=args.backup/('replaced-'+name)
        if replaced.exists():raise SystemExit('This backup has already restored a package.')
        if link is not None and not pathlib.Path(link.read_text()).exists():
            raise SystemExit('Saved theme symlink target is unavailable; restore the migration snapshot first.')
        if target.exists() or target.is_symlink():shutil.move(str(target),replaced)
        if previous is not None:shutil.copytree(previous,target)
        else:
            source=pathlib.Path(link.read_text())
            if not source.exists():raise SystemExit('Saved theme symlink target is unavailable; restore the migration snapshot first.')
            target.symlink_to(source)
    env=dict(os.environ,OMARCHY_THEME_SYNC_FROM='basedcode-rollback',OMARCHY_THEME_WAIT='1')
    subprocess.run(['omarchy','theme','set',name],env=env,check=True)
    subprocess.run(['omarchy','theme','bg','set',record['saved_background']],env=env,check=True)
    for key,value in record['desktop_settings'].items():subprocess.run(['gsettings','set','org.gnome.desktop.interface',key,value],check=True)
    print('Restored',name)
if __name__=='__main__':main()
