#!/usr/bin/env python3
"""Check bar text against the wallpaper strip across time and display crops."""
import importlib.util,json,pathlib,tomllib
import numpy as np
from PIL import ImageOps
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render',ROOT/'scripts/render.py')
render=importlib.util.module_from_spec(spec);spec.loader.exec_module(render)
c=tomllib.loads((ROOT/'theme/colors.toml').read_text())
def luminance(rgb):
    x=np.asarray(rgb,dtype=float)/255
    linear=np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
    return linear@np.array([.2126,.7152,.0722])
fg=luminance([int(c['foreground'][i:i+2],16) for i in (1,3,5)])
rows=[]
for t in range(render.DURATION):
    master=render.frame(t,1280,720)
    for label,size in [('landscape',(640,360)),('portrait',(360,640))]:
        crop=ImageOps.fit(master,size)
        bg=luminance(np.asarray(crop)[:20])
        ratio=(np.maximum(fg,bg)+.05)/(np.minimum(fg,bg)+.05)
        minimum=float(ratio.min());assert minimum>=4.5,(label,t,minimum)
        rows.append({'seconds':t,'crop':label,'minimum_bar_text_contrast':round(minimum,2)})
report={'minimum':min(r['minimum_bar_text_contrast'] for r in rows),'samples':rows,
        'note':'Computed from source frames and centre-fill crops; native bar colour selection is tested separately.'}
(ROOT/'qa/wallpaper-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Wallpaper bar-strip contrast:',report['minimum'])
