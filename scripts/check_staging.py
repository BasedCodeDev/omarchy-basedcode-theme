#!/usr/bin/env python3
"""Test Git-installed staging, native switching and remembered still choice offline."""
import hashlib,json,os,pathlib,shutil,subprocess,tempfile,tomllib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='basedcode-light-staging-') as tmp:
    isolated=pathlib.Path(tmp)
    target=isolated/'.config/omarchy/themes/basedcode-light'
    if '--repository-root' in sys.argv:
        # Exercise exactly the tracked installable repository, excluding local QA.
        files=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z']).decode().split('\0')
        for name in filter(None,files):
            dest=target/name; dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,dest)
    else:
        shutil.copytree(ROOT/'theme',target)
    (target/'.git').mkdir()  # Native staging uses this to identify a cloned theme.
    env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_STATE_HOME=tmp+'/.local/state',XDG_CACHE_HOME=tmp+'/.cache',XDG_RUNTIME_DIR=tmp,OMARCHY_PATH='/usr/share/omarchy',OMARCHY_THEME_HEADLESS='1')
    def select(name):
        result=subprocess.run(['omarchy','theme','set',name],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        return result.stderr
    stderr=select('basedcode-light')
    current=isolated/'.local/state/omarchy/current'
    assert (current/'background').resolve().name=='01-basedcode-light-motion.mp4'
    assert (current/'theme/vscode-theme.json').read_bytes()==(target/'vscode-theme.json').read_bytes()
    assert tomllib.loads((current/'theme/shell.toml').read_text())['bar']['active']=='#D7A4E2'
    assert (current/'theme/neovim.lua').exists()
    assert (current/'theme/foot.ini').exists()
    (current/'background').unlink()
    (current/'background').symlink_to(current/'theme/backgrounds/02-basedcode-light-still.png')
    # Use a copy of the installed dark sibling in this isolated home.
    dark=pathlib.Path.home()/'.config/omarchy/themes/basedcode'
    shutil.copytree(dark,isolated/'.config/omarchy/themes/basedcode')
    select('basedcode')
    assert (current/'theme.name').read_text().strip()=='basedcode'
    select('basedcode-light')
    assert (current/'background').resolve().name=='02-basedcode-light-still.png'
    assert (current/'background').exists()
    assert (current/'theme/colors.toml').read_bytes()==(ROOT/'theme/colors.toml').read_bytes()
    report={'git_staging':'pass','native_generated_terminal_and_neovim':'pass','vscode_override_preserved':'pass','theme_round_trip':'pass','remembered_still_choice':'pass','staging_stderr':stderr.strip()}
    (ROOT/'qa/staging-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
