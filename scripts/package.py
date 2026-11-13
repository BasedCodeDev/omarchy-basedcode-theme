#!/usr/bin/env python3
"""Build reproducible archives from explicit public inputs; never include local QA."""
import gzip,hashlib,json,pathlib,shutil,subprocess,tarfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
# Keep the repository root directly installable by Omarchy. Edit theme/ and
# regenerate these tracked copies with this script; Git deduplicates their blobs.
for source in (ROOT/'theme').iterdir():
    if source.is_dir(): shutil.copytree(source,ROOT/source.name,dirs_exist_ok=True)
    else: shutil.copy2(source,ROOT/source.name)
DIST=ROOT/'dist'; DIST.mkdir(exist_ok=True)
release=ROOT/'build/release/basedcode-light'
if release.exists(): shutil.rmtree(release)
shutil.copytree(ROOT/'theme',release)
runtime_readme='''# BasedCode Light for Omarchy\n\nCharcoal BasedCode theme with purple accents and light text and native dark application mode; tested on Omarchy 4.5.0-3.\n\nExtract this basedcode-light directory into ~/.config/omarchy/themes/ (back up an existing copy first), then run:\n\n    omarchy theme set basedcode-light\n\nRequires Yaru-purple icons. JetBrainsMono Nerd Font is recommended. Animation uses Omarchy native video wallpaper support.\n\nChoose the matching still or animation through the background picker, or run:\n\n    omarchy theme bg set ~/.config/omarchy/themes/basedcode-light/backgrounds/02-basedcode-light-still.png\n    omarchy theme bg set ~/.config/omarchy/themes/basedcode-light/backgrounds/01-basedcode-light-motion.mp4\n\nSwitch back through the theme picker. Before installation, record your existing theme and wallpaper if you need exact restoration.\n\nSource archive contains the renderer, scripts, full documentation and validation results. No fonts or icon files are bundled. BasedCode brand rights are separate from the implementation licence.\n'''
(release/'README.md').write_text(runtime_readme)
for name in ('LICENSE','BRAND-RIGHTS.md','THIRD-PARTY-NOTICES.md'):
    shutil.copy2(ROOT/name,release/name)
shutil.copy2(ROOT/'docs/VALIDATION.md',release/'VALIDATION.md')
manifest={str(p.relative_to(release)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(release.rglob('*')) if p.is_file()}
(release/'manifest.sha256').write_text(''.join(f'{h}  {name}\n' for name,h in manifest.items()))
def archive(filename,files):
    with (DIST/filename).open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as tar:
        for source,name in files:
            assert source.is_file() and not source.is_symlink()
            info=tar.gettarinfo(str(source),arcname=name); info.uid=info.gid=0; info.uname=info.gname=''; info.mtime=0; info.mode=0o644
            with source.open('rb') as f: tar.addfile(info,f)
archive('basedcode-light-1.0.0.tar.gz',[(p,'basedcode-light/'+str(p.relative_to(release))) for p in sorted(release.rglob('*')) if p.is_file()])
public=[]
for folder in ('src','scripts','theme','docs','qa'):
    for p in sorted((ROOT/folder).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and not (folder=='qa' and 'local' in p.relative_to(ROOT).parts): public.append(p)
public += [ROOT/n for n in ('README.md','LICENSE','BRAND-RIGHTS.md','THIRD-PARTY-NOTICES.md','requirements.txt','.gitignore')]
archive('basedcode-light-1.0.0-source.tar.gz',[(p,'omarchy-basedcode-light/'+str(p.relative_to(ROOT))) for p in sorted(public)])
(DIST/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(DIST.glob('*.tar.gz'))))
print('Built runtime and source archives in',DIST)
