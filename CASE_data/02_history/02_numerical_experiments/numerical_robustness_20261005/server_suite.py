"""Fixed-server serial probes. Run beneath flock; no cloud submission or credentials.

Each new solve requires >=90GiB available RAM and no other visible solver.
Records gate decisions and subprocess exit codes. Individual output roots cannot
be overwritten. This script is deliberately finite, not a monitoring service.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import time
import psutil

root=Path(sys.argv[1]).resolve()
env=os.environ.copy();base=Path('/home/zz2/National_model_server')
env.update(CISPO_DATA_ROOT=str(root/'data'),CISPO_CF_ROOT=str(base/'data/hourly_cf'),
    CISPO_HYDRO_ROOT=str(base/'data/hydro_timeseries_20260719_sequential_sparse'),
    CISPO_WAVE_ROOT=str(base/'data/wave_energy_20260727'),PYTHONDONTWRITEBYTECODE='1',
    OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='12')
probe=root/'repo/supplementary_materials/reviews/numerical_robustness_20261005/run_probe.py'
cases=[('A_off744',['--variant','off','--year','2040','--state-in',str(root/'upstream_2030_bound_closed/planning_state_candidate')]),
       ('A_on744',['--variant','A','--year','2040','--state-in',str(root/'upstream_2030_bound_closed/planning_state_candidate')]),
       ('B_off744',['--variant','off']),('B_on744',['--variant','B']),
       ('C_off744_factor',['--variant','off','--factor']),('C_on744_factor',['--variant','C','--factor'])]
records=[]
for name,args in cases:
    if (root/name/'result.json').exists():
        records.append(dict(name=name,already_complete=True));continue
    others=[]
    for proc in psutil.process_iter(['pid','name','cmdline']):
        try:
            command=proc.info['cmdline'] or []
            if proc.pid==os.getpid() or not command:continue
            if any(any(marker in arg for marker in ['run_cispo','run_probe.py','benchmark_storage_diagnostic','gurobi_cl','run_screen_probe']) for arg in command):
                others.append({'pid':proc.pid,'executable':proc.info['name'],'script':next((Path(arg).name for arg in command if arg.endswith('.py')),None)})
        except (psutil.AccessDenied,psutil.NoSuchProcess):pass
    gate=dict(case=name,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        available_memory_bytes=psutil.virtual_memory().available,other_solvers=others)
    (root/(name+'.gate.json')).write_text(json.dumps(gate,indent=2))
    if gate['available_memory_bytes']<90*2**30 or others:
        records.append(dict(name=name,status='GATE_BLOCKED',gate=gate));break
    with (root/(name+'.console.log')).open('w') as log:
        completed=subprocess.run(['/usr/bin/time','-v',sys.executable,str(probe),'--hours','744','--start','2880',
            '--threads','12',*args,'--output',str(root/name)],cwd=root/'repo',env=env,stdout=log,stderr=subprocess.STDOUT)
    record=dict(name=name,returncode=completed.returncode)
    if (root/name/'result.json').exists():record['result']=json.loads((root/name/'result.json').read_text())
    records.append(record);(root/'suite_status.json').write_text(json.dumps(records,indent=2))
    if completed.returncode:break
(root/'suite_status.json').write_text(json.dumps(records,indent=2))
