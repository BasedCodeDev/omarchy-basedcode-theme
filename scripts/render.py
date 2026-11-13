#!/usr/bin/env python3
"""Scene-matched purple field. No nodes, text or shader; no changes to the desktop."""
import argparse,json,math,pathlib,subprocess
import numpy as np
from PIL import Image,ImageOps
ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'src/design.json').read_text())['wallpaper']
DURATION=CFG['seconds']; FPS=CFG['fps']
def rgb(h):return np.array([int(h[i:i+2],16) for i in (1,3,5)],dtype=np.float32)

def field(t,w=1280,h=720):
    # CSS angles run clockwise from up. Project onto the full gradient line,
    # whose length is the sum of each axis's contribution to its endpoints.
    x,y=np.meshgrid(np.arange(w,dtype=np.float32)+.5,np.arange(h,dtype=np.float32)+.5)
    angle=math.radians(CFG['angle']);dx,dy=math.sin(angle),-math.cos(angle)
    pos=((x-w/2)*dx+(y-h/2)*dy)/(abs(w*dx)+abs(h*dy))+.5
    mix=np.clip((pos-CFG['start_stop'])/(CFG['end_stop']-CFG['start_stop']),0,1)[...,None]
    out=rgb(CFG['start'])*(1-mix)+rgb(CFG['end'])*mix
    p=2*math.pi*t/DURATION
    # Soft corner lights at t=0; their small offsets and opacity changes
    # form a periodic lighting pass, without moving or warping the base field.
    radius=math.hypot(w,h)
    bottom=np.clip(1-np.hypot(x-.018*w*math.sin(p),y-(h-.018*h*(1-math.cos(p))))/(radius*.34),0,1)
    top=np.clip(1-np.hypot(x-(w-.012*w*(1-math.cos(p))),y-.018*h*math.sin(p))/(radius*.22),0,1)
    for light,color,alpha in [(bottom,'#B87EFF',.16*.55*(1-.24*math.sin(p))), (top,'#FFFFFF',.12*.55*(1+.30*math.sin(p)))]:
        a=(light*alpha)[...,None];out=out*(1-a)+rgb(color)*a
    # Static sub-channel dither avoids banding without temporal shimmer.
    noise=np.random.default_rng(CFG['seed']).uniform(-.48,.48,(h,w,1))
    return np.clip(np.rint(out+noise),0,255).astype(np.uint8)

def frame(t,w=1920,h=1080):
    return Image.fromarray(field(t)).resize((w,h),Image.Resampling.BICUBIC)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--video',action='store_true');ap.add_argument('--width',type=int,default=CFG['width']);ap.add_argument('--height',type=int,default=CFG['height']);args=ap.parse_args()
    out=ROOT/'theme/backgrounds';out.mkdir(exist_ok=True);qa=ROOT/'qa';qa.mkdir(exist_ok=True)
    still=frame(0,CFG['still_width'],CFG['still_height']);still.save(out/'02-basedcode-still.png')
    frame(0,1280,720).save(qa/'wallpaper-review.png')
    ImageOps.fit(still,(608,1080)).save(qa/'portrait-review.png')
    sheet=Image.new('RGB',(1920,720))
    for i,t in enumerate((0,2,4,8,12,15)):sheet.paste(frame(t,640,360),((i%3)*640,(i//3)*360))
    sheet.save(qa/'motion-contact-sheet.png')
    if args.video:
        proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{args.width}x{args.height}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-threads','4',str(out/'01-basedcode-motion.mp4')],stdin=subprocess.PIPE)
        try:
            for i in range(FPS*DURATION):
                proc.stdin.write(frame(i/FPS,args.width,args.height).tobytes())
                if i%120==0:print(f'Rendered {i}/{FPS*DURATION}',flush=True)
            proc.stdin.close()
            if proc.wait():raise RuntimeError('Encoder failed')
        except BaseException:proc.kill();proc.wait();raise
    (qa/'render-inputs.json').write_text(json.dumps({'wordmark':False,'nodes':False,'still_size':[CFG['still_width'],CFG['still_height']],'video_size':[args.width,args.height],'fps':FPS,'seconds':DURATION,'seed':CFG['seed']},indent=2)+'\n')
    print('Purple field assets ready')
if __name__=='__main__':main()
