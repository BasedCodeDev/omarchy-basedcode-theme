#!/usr/bin/env python3
"""Exercise the installed Omarchy generator with an isolated subprocess home."""
import configparser, hashlib, json, os, pathlib, re, shutil, subprocess, tempfile, tomllib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def luminance(h):
    cs=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    cs=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in cs]
    return sum(v*w for v,w in zip(cs,(.2126,.7152,.0722)))
def contrast(a,b):
    hi,lo=sorted((luminance(a),luminance(b)),reverse=True)
    return (hi+.05)/(lo+.05)
def main():
    c=tomllib.loads((ROOT/'theme/colors.toml').read_text())
    for k,v in c.items():
        assert k=='mode' or re.fullmatch(r'#[0-9a-fA-F]{6}',v),(k,v)
    official=tomllib.loads(pathlib.Path('/usr/share/omarchy/themes/catppuccin/colors.toml').read_text())
    assert set(official)<=set(c)
    checks=[]
    def check(label,fg,bg,minimum=4.5):
        ratio=contrast(fg,bg); checks.append({'name':label,'foreground':fg,'background':bg,'ratio':round(ratio,2),'minimum':minimum})
        assert ratio>=minimum,f'{label}: {ratio:.2f} < {minimum}'
    for key in ('foreground','light_foreground','muted','dark_foreground','red','green','yellow','blue','cyan','magenta','orange','brown','bright_red','bright_green','bright_yellow','bright_blue','bright_cyan','bright_magenta'):
        check('code '+key,c[key],c['background'])
    for bg in ('background','lighter_background','selection'):
        check(bg+' text',c['foreground'],c[bg])
        check(bg+' focus',c['accent'],c[bg],3)
    check('panel secondary',c['light_foreground'],c['lighter_background'])
    check('panel muted',c['muted'],c['lighter_background'])
    check('lock placeholder',c['muted'],c['background'])
    for bg in ('dark_background','darker_background'):
        for fg in ('foreground','light_foreground','muted'):
            check(bg+' '+fg,c[fg],c[bg])
    with tempfile.TemporaryDirectory(prefix='basedcode-validation-') as temp:
        isolated=pathlib.Path(temp)
        stage=isolated/'.local/state/omarchy/current/next-theme'
        stage.mkdir(parents=True)
        for f in (ROOT/'theme').glob('*'):
            if f.is_file(): shutil.copy2(f,stage/f.name)
        env=dict(os.environ, HOME=temp, XDG_CONFIG_HOME=str(isolated/'.config'),XDG_STATE_HOME=str(isolated/'.local/state'),OMARCHY_PATH='/usr/share/omarchy')
        result=subprocess.run(['/usr/share/omarchy/bin/omarchy-theme-set-templates'],env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        generated=[]
        for file in sorted(stage.iterdir()):
            if not file.is_file(): continue
            if file.suffix=='.png':
                assert file.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),file.name
                continue
            text=file.read_text()
            assert '{{' not in text,file.name
            if file.suffix=='.toml': tomllib.loads(text)
            if file.suffix=='.json': json.loads(text)
            if file.name=='foot.ini':
                parser=configparser.ConfigParser(); parser.read_string(text)
                assert parser['colors-dark']['foreground'].upper()==c['foreground'][1:]
            generated.append(file.name)
        shell=tomllib.loads((stage/'shell.toml').read_text())
        assert shell['bar']['active']==c['accent']
        assert shell['lock']['placeholder']==c['muted']
        assert shell['menu']['selected-text']==c['selection_foreground']
        assert shell['menu']['selected-background']==c['selection']
        assert shell['font']['base-size']==12
        for name in ('launcher','menu','notifications','popups','tooltip','polkit','lock'):
            section=shell[name]; check(name+' text',section['text'],section['background'])
            check(name+' border',section['border'],section['background'],3)
        editor=json.loads((stage/'vscode-theme.json').read_text())
        assert editor['type']==c['mode']
        vc=editor['colors']
        for label,fg,bg in [('primary button','button.foreground','button.background'),('secondary button','button.secondaryForeground','button.secondaryBackground'),('secondary hover','button.secondaryForeground','button.secondaryHoverBackground'),('extension button','extensionButton.foreground','extensionButton.background'),('editor selection','editor.selectionForeground','editor.selectionBackground'),('terminal selection','terminal.selectionForeground','terminal.selectionBackground')]:
            check(label,vc[fg],vc[bg])
        check('editor keyboard focus',vc['focusBorder'],c['background'],3)
        def composite(fg,bg):
            alpha=int(fg[7:9],16)/255 if len(fg)==9 else 1
            return '#'+''.join(f'{round(int(fg[i:i+2],16)*alpha+int(bg[i:i+2],16)*(1-alpha)):02x}' for i in (1,3,5))
        for key in ('diffEditor.insertedTextBackground','diffEditor.removedTextBackground','editor.findMatchBackground'):
            check(key,c['foreground'],composite(vc[key],c['background']))
        controls=shell['controls']
        for state in ('normal','hover-cursor','focus','selected'):
            fill=controls[state+'-color']+f"{round(controls[state+'-fill-alpha']*255):02x}"
            bg=composite(fill,c['lighter_background'])
            check('control '+state+' text',c['foreground'],bg)
            check('control '+state+' border',controls[state+'-border'],bg,3)
        for label,fg,bg in [('primary hover','button.foreground','button.hoverBackground'),('extension hover','extensionButton.foreground','extensionButton.hoverBackground'),('prominent hover','extensionButton.prominentForeground','extensionButton.prominentHoverBackground')]:
            check(label,vc[fg],vc[bg])
        destination=ROOT/'build/generated'
        if destination.exists(): shutil.rmtree(destination)
        shutil.copytree(stage,destination)
    media=ROOT/'theme/backgrounds/01-basedcode-motion.mp4'
    video=None
    if media.exists():
        video=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(media)],text=True))
        video['format']['filename']=str(media.relative_to(ROOT))
        streams=video['streams']; assert len(streams)==1 and streams[0]['codec_name']=='h264'
        assert streams[0]['pix_fmt']=='yuv420p'
        assert streams[0]['r_frame_rate']=='30/1'
        assert (streams[0]['width'],streams[0]['height']) in ((3840,2160),(2560,1440),(1920,1080))
        assert abs(float(video['format']['duration'])-16)<.05
    report={'omarchy':subprocess.check_output(['omarchy','version'],text=True).strip(),'generated_files':generated,'contrast_checks':checks,'video':video}
    (ROOT/'qa/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS: {len(checks)} contrast checks; {len(generated)} generated/config files; video={bool(video)}')
    for row in sorted(checks,key=lambda x:x['ratio'])[:6]: print(row['name'],row['ratio'])
if __name__=='__main__': main()
