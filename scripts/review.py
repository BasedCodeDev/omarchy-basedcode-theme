#!/usr/bin/env python3
"""Design review sheet; schematic UI, clearly separated from live screenshots."""
import pathlib, subprocess, tomllib
from PIL import Image, ImageDraw, ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[1]
c=tomllib.loads((ROOT/'theme/colors.toml').read_text())
fontpath=subprocess.check_output(['fc-match','JetBrains Mono','-f','%{file}'],text=True).strip()
im=Image.new('RGB',(1920,1400),c['background']); d=ImageDraw.Draw(im)
def text(x,y,s,size=20,fill=c['foreground']):
    d.text((x,y),s,font=ImageFont.truetype(fontpath,size),fill=fill)
def card(box,title):
    d.rounded_rectangle(box,radius=12,fill=c['lighter_background'],outline=c['accent'],width=2)
    text(box[0]+24,box[1]+20,title,18,c['light_foreground'])
text(60,40,'BasedCode Light / Omarchy',36)
text(60,96,'Design review • v1.0 • schematic surfaces, not live screenshots',18,c['muted'])
wall=Image.open(ROOT/'theme/backgrounds/02-basedcode-light-still.png').resize((1120,630))
im.paste(wall,(60,154)); d=ImageDraw.Draw(im)
text(84,176,'Landscape / motion poster',18,c['muted'])
portrait=Image.open(ROOT/'qa/portrait-review.png').resize((354,630))
im.paste(portrait,(1220,154)); d=ImageDraw.Draw(im)
text(1610,168,'Palette',22)
for i,(name,key) in enumerate([('Canvas','background'),('Panel','lighter_background'),('Selection','selection'),('Purple','accent'),('Text','foreground'),('Muted','muted')]):
    y=220+i*84; d.rounded_rectangle((1610,y,1670,y+48),radius=6,fill=c[key]); text(1690,y,name,18); text(1690,y+25,c[key],16,c['muted'])
card((60,824,940,1340),'01 / Working surfaces')
d.rectangle((82,882,918,1318),fill=c['background'])
lines=[('// Real work. Clear hierarchy.','muted'),('function buildTheme(palette) {','blue'),('  const name = "BasedCode Light";','green'),('  return { name, version: 1 };','orange'),('}','foreground'),('','foreground'),('+ Added: readable selections','green'),('- Removed: low-contrast focus','red'),('! Warning: uncommitted changes','yellow')]
for i,(line,key) in enumerate(lines): text(106,910+i*37,line,20,c[key])
d.rectangle((106,1258,872,1295),fill=c['selection']); text(118,1264,'Selected text stays readable',19)
card((980,824,1860,1074),'02 / Menu and keyboard focus')
text(1008,890,'Terminal',24)
d.rounded_rectangle((1004,935,1836,991),radius=5,fill=c['selection'],outline=c['accent'],width=2)
text(1022,947,'Editor                     Enter',22)
text(1008,1013,'Files',22,c['light_foreground'])
card((980,1104,1860,1340),'03 / Notification and lock treatment')
text(1008,1170,'Build complete',25)
text(1008,1212,'Ready for the next iteration.',20,c['light_foreground'])
d.rounded_rectangle((1004,1260,1836,1316),radius=5,fill=c['background'],outline=c['accent'],width=2)
text(1022,1274,'Password',18,c['muted'])
im.save(ROOT/'qa/design-review.png')
print('Design sheet ready')
