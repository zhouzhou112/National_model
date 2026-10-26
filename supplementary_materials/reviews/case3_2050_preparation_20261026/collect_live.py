"""One-shot read-only snapshot of the two protected running jobs."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess

HERE=Path(__file__).resolve().parent
CODE=r'''
from pathlib import Path
import subprocess,json,re,hashlib,datetime
result={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobs':{}}
for job in ['5201318','5207165']:
    record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
    fields=dict(re.findall(r'(?:^|\s)([A-Za-z][A-Za-z0-9_]*)=(\S+)',record))
    root=Path(fields['WorkDir']);log=root/'output_8760/gurobi.log';raw=log.read_bytes()
    rows=[]
    for line in raw.decode('utf-8',errors='replace').splitlines():
        if re.match(r'^\s*\d+\s+[-+0-9.e]+\s+[-+0-9.e]+\s+[-+0-9.e]+\s+[-+0-9.e]+\s+[-+0-9.e]+\s+\d+s\s*$',line):rows.append(line.strip())
    result['jobs'][job]=dict(slurm={k:fields.get(k) for k in ['JobState','RunTime','NodeList','AllocTRES','TimeLimit','WorkDir','ExitCode','Restarts']},
        last_barrier_rows=rows[-3:],gurobi_log_sha256=hashlib.sha256(raw).hexdigest(),
        stderr_bytes={p.name:p.stat().st_size for p in [root/'stderr.log',root/('slurm-'+job+'.err')] if p.exists()},
        terminal_output_present=(root/'output_8760/solve_report.json').exists())
result['accounting']=subprocess.check_output(['sacct','-X','-j','5201318,5207165','--format=JobID,State,ExitCode,Elapsed','--parsable2'],universal_newlines=True)
print(json.dumps(result))
'''

def main():
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','paracloud-bscc-a8','python3 -'],
        input=CODE,capture_output=True,text=True,encoding='utf-8',timeout=60)
    if p.returncode:raise RuntimeError(p.stderr)
    result=json.loads(p.stdout)
    path=HERE/('live_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
