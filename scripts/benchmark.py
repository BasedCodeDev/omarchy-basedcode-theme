#!/usr/bin/env python3
"""Five-minute observational samples. GPU totals include other desktop apps."""
import json,os,pathlib,statistics,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/local'; OUT.mkdir(parents=True,exist_ok=True)
media=pathlib.Path.home()/'.local/state/omarchy/current/theme/backgrounds'
def proc_sample():
    result={}
    for path in pathlib.Path('/proc').glob('[0-9]*/stat'):
        try:
            stat=path.read_text(); name=stat.split('(',1)[1].rsplit(')',1)[0]
            if name not in ('owe-render','owed','qs','quickshell'): continue
            fields=stat.rsplit(')',1)[1].split()
            result[path.parent.name+':'+fields[19]]={'name':name,'ticks':int(fields[11])+int(fields[12]),'rss_mib':int(fields[21])*os.sysconf('SC_PAGE_SIZE')/1048576}
        except (OSError,ValueError,IndexError): pass
    return result
def gpu_sample():
    result=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,utilization.decoder,memory.used,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True)
    try: return [float(v.strip()) for v in result.stdout.splitlines()[0].split(',')]
    except (ValueError,IndexError): return None
all_results={}
def display_state():
    monitors=json.loads(subprocess.check_output(['hyprctl','-j','monitors'],text=True))
    return [{k:m[k] for k in ('name','width','height','scale','transform','refreshRate')} for m in monitors]
initial_displays=display_state()
def still_our_theme():
    return (pathlib.Path.home()/'.local/state/omarchy/current/theme.name').read_text().strip()=='basedcode'
try:
    for label,filename in [('still','02-basedcode-still.png'),('motion','01-basedcode-motion.mp4')]:
        subprocess.run(['omarchy','theme','bg','set',str(media/filename)],check=True)
        time.sleep(5)
        previous=proc_sample(); start=time.monotonic(); samples=[]
        for i in range(60):
            if not still_our_theme(): raise RuntimeError('Theme changed during benchmark; leaving the new selection untouched')
            before=time.monotonic(); time.sleep(5); now=proc_sample(); elapsed=time.monotonic()-before
            cpu=sum(max(0,v['ticks']-previous[k]['ticks']) for k,v in now.items() if k in previous)/os.sysconf('SC_CLK_TCK')/elapsed*100
            samples.append({'seconds':round(time.monotonic()-start,2),'process_cpu_percent_one_core':cpu,'process_rss_mib':sum(v['rss_mib'] for v in now.values()),'gpu':gpu_sample()})
            progress={'mode':label,'samples':len(samples),'target_samples':60}
            (OUT/'benchmark-progress.json').write_text(json.dumps(progress)+'\n')
            previous=now
            if (i+1)%12==0: print(f'{label}: {i+1}/60 samples',flush=True)
        all_results[label]={'seconds':time.monotonic()-start,'samples':samples,
            'display_state':display_state(),
            'mean_process_cpu_percent_one_core':statistics.mean(x['process_cpu_percent_one_core'] for x in samples),
            'mean_process_rss_mib':statistics.mean(x['process_rss_mib'] for x in samples)}
        (OUT/'benchmark.json').write_text(json.dumps(all_results,indent=2)+'\n')
finally:
    if still_our_theme(): subprocess.run(['omarchy','theme','bg','set',str(media/'01-basedcode-motion.mp4')],check=False)
print('Observational benchmark complete; animated background restored',flush=True)
summary={'note':'Observational samples; other desktop applications contribute to GPU totals.',
         'displays_unchanged':all(v['display_state']==initial_displays for v in all_results.values()),'modes':{}}
for label,result in all_results.items():
    samples=result['samples']; gpu=[s['gpu'] for s in samples if s['gpu'] is not None]
    summary['modes'][label]={'seconds':round(result['seconds'],1),'samples':len(samples),
        'cpu_percent_one_core':round(result['mean_process_cpu_percent_one_core'],2),
        'rss_mib':round(result['mean_process_rss_mib'],2),
        'gpu_means':dict(zip(('utilization_percent','decoder_percent','memory_mib','power_w'),
                            [round(statistics.mean(v[i] for v in gpu),2) for i in range(4)])) if gpu else None}
(ROOT/'qa/performance-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
