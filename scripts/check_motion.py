#!/usr/bin/env python3
"""Check periodic continuity and decode first/last compressed frames for seam comparison."""
import importlib.util,json,pathlib,subprocess
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render',ROOT/'scripts/render.py')
render=importlib.util.module_from_spec(spec); spec.loader.exec_module(render)
a=np.asarray(render.frame(0,640,360),dtype=np.float32)
b=np.asarray(render.frame(render.DURATION,640,360),dtype=np.float32)
c=np.asarray(render.frame(2,640,360),dtype=np.float32)
period=float(np.abs(a-b).max()); change=float(np.abs(a-c).mean())
assert period<=1,period
assert change>.01,change  # Approved subtle lighting, not the rejected moving ribbons.
media=ROOT/'theme/backgrounds/01-basedcode-light-motion.mp4'
last=render.FPS*render.DURATION-1
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(media),'-vf',f"select='eq(n,0)+eq(n,1)+eq(n,{last-1})+eq(n,{last})',scale=640:360",'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
frames=np.frombuffer(raw,dtype=np.uint8).reshape(4,360,640,3).astype(np.float32)
seam=float(np.abs(frames[-1]-frames[0]).mean())
adjacent=max(float(np.abs(frames[1]-frames[0]).mean()),float(np.abs(frames[-1]-frames[-2]).mean()))
assert seam<max(adjacent*2,1), (seam,adjacent)
report={'periodic_max_channel_delta':period,'two_second_mean_channel_delta':change,'encoded_seam_mean_delta':seam,'encoded_adjacent_mean_delta':adjacent}
(ROOT/'qa/motion-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
