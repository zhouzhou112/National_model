"""Read audit job status/log tails with squeue/sacct; never changes any job."""
from pathlib import Path
import datetime
import json
import subprocess

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'submission_receipt.json').read_text())
code='from pathlib import Path\nimport datetime,json,subprocess\nroot=Path('+repr(r['root'])+')\njobs='+repr(r['jobs'])+'\n'
code+='''
result={'at':datetime.datetime.now().astimezone().isoformat(),'logs':{},'results':{}}
ids=','.join(jobs.values())
for name,args in [('queue',['squeue','-j',ids,'-o','%.18i %.12T %.12M %.30R']),('accounting',['sacct','-j',ids,'--format=JobID,State,Elapsed,ExitCode,AllocCPUS,ReqMem,MaxRSS,NodeList','--parsable2'])]:
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    result[name]={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
for year,job in jobs.items():
    for suffix in ['out','err']:
        p=root/('tiny_bound_{}-{}.{}'.format(year,job,suffix))
        if p.exists():
            with p.open('rb') as f:
                f.seek(max(0,p.stat().st_size-4500));result['logs'][p.name]=f.read().decode('utf-8')
    folder=root/('result_'+year)
    if folder.exists():
        result['results'][year]={p.name:p.stat().st_size for p in folder.iterdir() if p.is_file() and p.suffix!='.scratch'}
print(json.dumps(result))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','paracloud-bscc-a8','python3 -'],input=code,capture_output=True,text=True,encoding='utf-8',timeout=90)
p.check_returncode();x=json.loads(p.stdout)
tag=datetime.datetime.fromisoformat(x['at']).astimezone(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
(HERE/('status_'+tag+'.json')).write_text(json.dumps(x,indent=2),encoding='utf-8')
def compact_log(name,content):
    done=next((line[9:] for line in content.splitlines() if line.startswith('COMPLETE ')),None)
    if done:
        summary=json.loads(done)
        return {k:summary[k] for k in ['year','totals','elapsed_seconds','validations']}
    return '\n'.join(content.splitlines()[-2:]) if name.endswith('.out') else content

print(json.dumps(dict(at=x['at'],queue=x['queue']['stdout'],
                     latest_logs={k:compact_log(k,v) for k,v in x['logs'].items()},
                     results=x['results']),indent=2))
