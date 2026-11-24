"""One read-only B2030 v3 snapshot; no polling, watcher or job mutation.

Usage: python collect_v3_performance.py --label startup_01
Writes a new JSON receipt and per-iteration CSV locally. Final metrics require
terminal Slurm state, resource_usage.txt and solve_report.json; missing != zero.
"""
import argparse
import csv
import json
from pathlib import Path
import deploy_pilot_v3 as deployment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not args.label.replace('_','').isalnum():
        parser.error('label must contain letters, numbers or underscores')
    result = deployment.remote(r'''
from datetime import datetime, timezone
receipt=json.loads((root/'released_submission.json').read_text())
job=receipt['job_id']; assert job.isdigit() and job not in {'5201318','5207165','5276670'}
result=dict(observed_at=datetime.now(timezone.utc).isoformat(),job_id=job,release=str(root),iterations=[])
for key,cmd in [
 ('scontrol',['scontrol','show','job','-o',job]),
 ('sacct',['sacct','-j',job,'--parsable2','--noheader','--format=JobID,JobName,State,ExitCode,Elapsed,AllocTRES,MaxRSS,Start,End']),
 ('sstat',['sstat','-j',job+'.batch','--parsable2','--noheader','--format=JobID,MaxRSS,AveRSS,MaxVMSize'])]:
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 result[key]=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
for name in ['compute_node_smoke.json','startup_resources.json','batch_exit.json','v2_identity_reuse.json','license_path_preflight.json','output_8760/solve_report.json']:
 p=root/name
 if p.exists():result[name]=json.loads(p.read_text())
for name in ['resource_usage.txt','stdout.log','stderr.log','slurm-'+job+'.err']:
 p=root/name
 if p.exists():
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-10000));tail=f.read().decode('utf-8',errors='replace')
  result[name]=dict(bytes=p.stat().st_size,tail=tail)
telemetry=root/'output_8760/solver_telemetry.jsonl'
if telemetry.exists():
 last=None
 with telemetry.open() as stream:
  for line in stream:
   try:r=json.loads(line)
   except ValueError:continue  # possibly a partial live final line
   if r.get('event')!='solver_progress' or r.get('phase')!='barrier':continue
   i=r.get('iteration');t=r.get('runtime_seconds')
   if i is None or t is None or (last and i<=last['iteration']):continue
   row=dict(iteration=i,runtime_seconds=t,iteration_seconds=(t-last['runtime_seconds']) if last and i==last['iteration']+1 else None)
   result['iterations'].append(row);last=row
result['completed_barrier_iterations_observed']=result['iterations'][-1]['iteration'] if result['iterations'] else None
result['final_metrics_available']='output_8760/solve_report.json' in result and 'batch_exit.json' in result
print(json.dumps(result))
''', args.label)
    deployment.save(deployment.EVIDENCE/(args.label+'.json'), result)
    with (deployment.EVIDENCE/(args.label+'_iterations.csv')).open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['iteration','runtime_seconds','iteration_seconds'])
        writer.writeheader();writer.writerows(result['iterations'])
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
