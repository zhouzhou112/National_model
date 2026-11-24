"""Read-only terminal evidence for job4614693; never solves or changes jobs.

Run from any directory. Saves small reports/logs locally, not large vectors.
"""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
REMOTE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3'
FILES=['batch_exit.json','stderr.log','resource_usage.txt','runtime_slurm_job.txt',
       'output_8760/gurobi.log','output_8760/solve_report.json','output_8760/solution_qc.json',
       'output_8760/preservation_report.json','output_8760/run_summary.json',
       'output_8760/result_manifest.json','output_8760/model_archive/archive_manifest.json',
       'output_8760/barrier_checkpoint/barrier_checkpoint_manifest.json',
       'output_8760/planning_state_candidate/state_metadata.json',
       'output_8760/solver_parameters_before_optimize.json']

def main():
    remote='import os,json\nroot='+repr(REMOTE)+'\nfiles='+repr(FILES)+'\n'
    remote+='''records={}
for rel in files:
    p=os.path.join(root,rel)
    if os.path.isfile(p): records[rel]=open(p).read()
inventory=[]
for folder,dirs,names in os.walk(os.path.join(root,'output_8760')):
    for name in names:
        p=os.path.join(folder,name)
        inventory.append(dict(path=os.path.relpath(p,root),bytes=os.stat(p).st_size))
print(json.dumps(dict(records=records,inventory=inventory)))
'''
    proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=remote,text=True,encoding='utf-8',capture_output=True,timeout=90)
    proc.check_returncode()
    data=json.loads(proc.stdout)
    dest=HERE/'evidence'
    dest.mkdir(exist_ok=True)
    manifest={'retrieved_at':datetime.datetime.now().astimezone().isoformat(),'remote_root':REMOTE,'files':[]}
    for rel,content in data['records'].items():
        p=dest/rel.replace('/','__')
        p.write_text(content,encoding='utf-8')
        manifest['files'].append(dict(remote_path=rel,local_path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (HERE/'inventory.json').write_text(json.dumps(data['inventory'],indent=2),encoding='utf-8')
    command="date '+%Y-%m-%d %H:%M:%S %Z'; squeue -u a8s001819 -o '%i|%j|%T|%M|%l|%N'; sacct -j 4614693 --format=JobID,State,ExitCode,Elapsed,Start,End,AllocCPUS,ReqMem,MaxRSS,NodeList -P"
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8',command],text=True,encoding='utf-8',capture_output=True,timeout=45)
    p.check_returncode()
    (dest/'scheduler.txt').write_text(p.stdout,encoding='utf-8')
    manifest['scheduler_command']=command
    (HERE/'source.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    for rel in ['output_8760/solve_report.json','output_8760/solution_qc.json','output_8760/preservation_report.json','output_8760/barrier_checkpoint/barrier_checkpoint_manifest.json','output_8760/planning_state_candidate/state_metadata.json']:
        j=json.loads(data['records'][rel])
        print(rel,'KEYS',list(j))
        print(json.dumps({k:v for k,v in j.items() if k in ['status','status_code','runtime_seconds','solution_count','iteration_counts','solver_quality','errors','files','quality','classification','acceptance_status','checkpoint_status','qc_status','scientifically_accepted','candidate_only']},ensure_ascii=False))
        if 'hard_checks' in j:print('FAILED_CHECKS',[k for k,v in j['hard_checks'].items() if not v])

if __name__=='__main__':main()
