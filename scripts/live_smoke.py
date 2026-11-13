#!/usr/bin/env python3
"""Explicit live QA: clean workspace capture, short recording, and theme round trip.
Run only in the desktop session where temporary visual changes are acceptable.
"""
import json,os,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]; out=ROOT/'qa/local'
(out/'recordings').mkdir(parents=True,exist_ok=True)
def run(args,**kw): return subprocess.run(args,check=True,capture_output=True,text=True,**kw)
def lua(code): run(['hyprctl','eval',code])
monitors=json.loads(run(['hyprctl','-j','monitors']).stdout)
centre=next(m for m in monitors if m['name']=='DP-1')
focused=next(m for m in monitors if m['focused'])
env=dict(os.environ,OMARCHY_THEME_SYNC_FROM='basedcode-local-validation',OMARCHY_THEME_WAIT='1')
report={}; recording_started=False
try:
    lua('hl.dispatch(hl.dsp.focus({monitor="DP-1"})); hl.dispatch(hl.dsp.focus({workspace="name:basedcode-smoke"}))')
    time.sleep(1)
    run(['grim','-o','DP-1',str(out/'final-desktop.png')])
    status=subprocess.run(['omarchy','capture','screenrecording','--status'],capture_output=True,text=True)
    if status.returncode==1:
        recording_env=dict(env,OMARCHY_SCREENRECORD_DIR=str(out/'recordings'),OMARCHY_SCREENRECORD_DEBUG='true')
        # Background recorder children inherit stdout; a pipe can remain open
        # after the launcher exits. Use a file so communicate() cannot hang.
        with (out/'recording-launch.log').open('w') as log:
            subprocess.run(['omarchy','capture','screenrecording','--fullscreen','--resolution=1920x1080'],env=recording_env,timeout=30,check=True,stdout=log,stderr=log)
        recording_started=True
        time.sleep(6)
        with (out/'recording-stop.log').open('w') as log:
            subprocess.run(['omarchy','capture','screenrecording','--stop-recording'],env=recording_env,timeout=30,check=True,stdout=log,stderr=log)
        recording_started=False
        report['recording_command']='pass'
        report['recording_output']=(out/'recording-stop.log').read_text().strip()
    else:
        report['recording_command']='skipped: an existing recording or unavailable recorder was detected'
except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
    report['recording_command']='failed'
    report['recording_error']=str(error)
    report['recording_stderr']=str(error.stderr or '')
    report['recording_stdout']=str(error.stdout or '')
finally:
    if recording_started: subprocess.run(['omarchy','capture','screenrecording','--stop-recording'],env=env)
    lua('hl.dispatch(hl.dsp.focus({monitor="DP-1"})); hl.dispatch(hl.dsp.focus({workspace='+json.dumps(centre['activeWorkspace']['name'])+'}))')
    lua('hl.dispatch(hl.dsp.focus({monitor='+json.dumps(focused['name'])+'}))')
run(['omarchy','theme','set','basedcode-dark'],env=env,timeout=60)
assert (pathlib.Path.home()/'.local/state/omarchy/current/theme.name').read_text().strip()=='basedcode-dark'
run(['omarchy','theme','set','basedcode'],env=env,timeout=60)
run(['omarchy','theme','bg','set',str(pathlib.Path.home()/'.config/omarchy/themes/basedcode/backgrounds/01-basedcode-motion.mp4')],env=env)
time.sleep(2)
errors=run(['hyprctl','configerrors']).stdout.strip(); assert not errors,errors
report['live_theme_round_trip']='pass'
report['hyprland_errors']=errors
report['renderer']=json.loads(run(['owe','render-status']).stdout)
(out/'live-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
