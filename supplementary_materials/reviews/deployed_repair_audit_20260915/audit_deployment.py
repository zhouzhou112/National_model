"""Read-only SHA/config/input audit of already running Base V9 deployment.

No Gurobi import, solve or server mutation. Run from any directory.
Outputs audit.json and selected remote runtime records beside this script.
"""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RELEASE='20260914_base_v9_t48_m750_tol1e4_v3'
REMOTE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/'+RELEASE
MANIFEST=ROOT/'supplementary_materials/reviews/formal_launch_failure_20260914'/(RELEASE+'_manifest.json')

def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    entries=manifest['files']
    script='import os,json,hashlib,datetime\nroot='+repr(REMOTE)+'\nentries='+repr(entries)+'\n'
    script+='''results=[]
for item in entries:
    p=os.path.join(root,item['path'])
    actual=hashlib.sha256(open(p,'rb').read()).hexdigest() if os.path.isfile(p) else None
    results.append(dict(path=item['path'],expected=item['sha256'],actual=actual,match=actual==item['sha256']))
records={}
for rel in ['formal_base.sbatch','runtime_slurm_job.txt','preflight/input_manifest.csv','input_preflight/input_manifest.csv','output_8760/input_manifest.csv','output_8760/model_config_snapshot.json','output_8760/build_report.json','output_8760/solver_parameters_before_optimize.json']:
    p=os.path.join(root,rel)
    if os.path.isfile(p): records[rel]=open(p).read()
config=json.loads(records['output_8760/model_config_snapshot.json'])
resolved=config.get('resolved_configuration',config)
station=resolved.get('hydro',{}).get('station_parameters_file')
data_root=os.path.join(root,'data_overlay')
station_path=os.path.join(data_root,station)
station_sha=hashlib.sha256(open(station_path,'rb').read()).hexdigest()
print(json.dumps(dict(remote_files=results,records=records,station_file=station,data_root=data_root,actual_station_sha256=station_sha)))
'''
    proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=script,capture_output=True,text=True,encoding='utf-8',timeout=90)
    proc.check_returncode()
    result=json.loads(proc.stdout)
    records=result.pop('records')
    evidence=HERE/'evidence'
    evidence.mkdir(exist_ok=True)
    for rel,content in records.items():
        (evidence/rel.replace('/','__')).write_text(content,encoding='utf-8')
    local=[]
    for entry in entries:
        if entry['path'].startswith('repo/'):
            path=ROOT/entry['path'][5:]
        elif entry['path'].startswith('data_overrides/'):
            path=ROOT/'data'/entry['path'][15:]
        else:
            continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        local.append(dict(path=entry['path'],expected=entry['sha256'],actual=actual,match=actual==entry['sha256']))
    result.update(retrieved_at=datetime.datetime.now().astimezone().isoformat(),remote_root=REMOTE,local_files=local,
                  remote_checked=len(entries),remote_mismatches=[x for x in result['remote_files'] if not x['match']],
                  local_checked=len(local),local_mismatches=[x for x in local if not x['match']])
    frozen=ROOT/'supplementary_materials/reviews/numeric_doublecheck_20260913/source_snapshot'
    frozen_comparison=[]
    for old in sorted(frozen.rglob('*.py')):
        rel=old.relative_to(frozen)
        current=ROOT/rel
        frozen_comparison.append(dict(path=rel.as_posix(),same=current.exists() and hashlib.sha256(old.read_bytes()).digest()==hashlib.sha256(current.read_bytes()).digest()))
    result['v8_source_comparison']=frozen_comparison
    (HERE/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    config=json.loads(records['output_8760/model_config_snapshot.json'])
    resolved=config.get('resolved_configuration',config)
    print(json.dumps({k:v for k,v in result.items() if k not in ['remote_files','local_files']},ensure_ascii=False,indent=2))
    print('CONFIG_TOP_KEYS',list(resolved))
    for key in ['hydro','numerical_cleanup','numerical','formulation','intra_grid','annual_load_center_transmission','features','paths']:
        if key in resolved: print(key,json.dumps(resolved[key],ensure_ascii=False))
    print('RECORDS',list(records))

if __name__=='__main__':
    main()
