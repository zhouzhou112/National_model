"""Read existing remote case reports over SSH; never build or solve a model.

The remote payload uses only the Python standard library and writes nothing.
Local output is a new JSON inventory with source hashes and reported QC, not
an independent recomputation of every historical primal vector.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shlex
import subprocess

REMOTE = r'''
import csv,hashlib,json,os,sys
from pathlib import Path
from datetime import datetime
roots=json.loads(sys.argv[1]); rows=[]; errors=[]; seen=set()
def read(path):
    if not path.is_file(): return {}
    try: return json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception as e:
        errors.append(dict(path=str(path),error=str(e))); return {}
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
for root in roots:
    root=Path(root)
    for current,dirs,files in os.walk(root):
        depth=len(Path(current).relative_to(root).parts)
        dirs[:]=[d for d in dirs if d not in ('repo','data','.git','visualizations','model_archive','solution_snapshot','barrier_checkpoint','__pycache__','venv') and depth<6]
        if 'solve_report.json' not in files or current in seen: continue
        seen.add(current); p=Path(current); solve=read(p/'solve_report.json'); scope=read(p/'run_scope.json')
        hours=solve.get('optimization_hours',scope.get('optimization_hours'))
        if hours is not None and int(hours)<168: continue
        qc=read(p/'solution_qc.json')
        qc_source='solution_qc.json'
        for candidate in ('solution_qc_stage_a_engineering.json','engineering_solution_qc.json','solution_qc_engineering.json','engineering_macro_analysis/solution_qc.json'):
            if not qc and (p/candidate).is_file(): qc=read(p/candidate);qc_source=candidate
        identity=read(p/'run_identity.json'); snapshot=read(p/'model_config_snapshot.json')
        raw=snapshot.get('resolved_configuration',{})
        water={k:v for k,v in qc.items() if any(s in k for s in ('reservoir','cascade','hydro'))}
        checks=qc.get('hard_checks',{})
        water_checks={k:v for k,v in checks.items() if any(s in k for s in ('reservoir','cascade','hydro'))}
        input_rows=[]
        if (p/'input_manifest.csv').is_file():
            with (p/'input_manifest.csv').open(encoding='utf-8-sig',newline='') as stream:
                for r in csv.DictReader(stream):
                    if r.get('kind')=='hydrology_timeseries' or r.get('logical_path','').replace('\\','/').endswith('hydro/hydro_stations.csv'):
                        input_rows.append({k:r.get(k) for k in ('kind','logical_path','sha256')})
        rows.append(dict(path=current,hours=hours,start_hour=solve.get('optimization_start_hour',scope.get('optimization_start_hour')),
            year=solve.get('planning_year',raw.get('planning_year')),scenario=solve.get('scenario_id',scope.get('scenario_id')),
            status=solve.get('status'),scientifically_accepted=solve.get('scientifically_accepted'),
            runtime_seconds=solve.get('runtime_seconds'),profile=solve.get('solver_profile_id'),
            solution_contract=solve.get('solution_contract'),solution_quality=solve.get('solution_quality'),
            model_statistics=solve.get('model_statistics'),qc_status=qc.get('status'),qc_source=qc_source,
            water_qc=water,water_hard_checks=water_checks,
            failed_hard_checks=[k for k,v in checks.items() if v is not True],
            numerics=raw.get('numerics'),hydro_settings=raw.get('hydro'),
            git_commit=(identity.get('implementation_bundle') or {}).get('git_commit'),
            hydro_input_hashes=input_rows,
            report_sha256={name:digest(p/name) for name in ('solve_report.json',qc_source,'raw_lp_qc.json','run_scope.json','result_manifest.json')},
            artifact_files=[n for n in files if any(s in n for s in ('qc','preserv','reservoir','terminal'))],
            raw_lp_qc=read(p/'raw_lp_qc.json')))
print(json.dumps(dict(recorded_at=datetime.now().astimezone().isoformat(),roots=roots,remote_write=False,
    optimize_called=False,cases=rows,errors=errors),ensure_ascii=False))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ssh-host',required=True)
    parser.add_argument('--root',action='append',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    command='python3 - '+shlex.quote(json.dumps(args.root))
    completed=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12',args.ssh_host,command],
        input=REMOTE.encode('utf-8'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,check=True)
    payload=json.loads(completed.stdout)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(host=args.ssh_host,cases=len(payload['cases']),errors=payload['errors'],output=str(args.output)),ensure_ascii=False))


if __name__=='__main__': main()
