"""Collect immutable acceptance documents from the verified T550 backup.
Run from any directory; no remote mutation; limits 2 MB/file and 10 MB total.
"""
import base64, hashlib, json, pathlib, subprocess
HERE=pathlib.Path(__file__).resolve().parent
RELEASE="20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2"
NAMES=["solution_qc.json","solve_report.json","preservation_report.json","result_manifest.json","run_identity.json","build_report.json","run_summary.json","annual_summary.json","model_config_snapshot.json","solver_parameters_before_optimize.json","run_scope.json","scenario_manifest.json","run_environment.json","preflight_report.json","annual_carbon_ccs.json","cost_components.csv","annual_capacity_by_technology.csv","annual_generation_by_technology.csv","annual_storage_operation_by_technology.csv","annual_flexible_load_by_province.csv","dual_export_status.json","model_archive/archive_manifest.json","model_archive/parameters.prm","barrier_checkpoint/barrier_checkpoint_manifest.json","planning_state_candidate/state_metadata.json","planning_state_candidate/state_transition_summary.csv","gurobi.log","solver_telemetry.jsonl"]
REMOTE="""
import pathlib,json,hashlib,base64
root=pathlib.Path('/home/zz2/National_model_server/cloud_backup')/release
manifest=json.loads((root/'backup_manifest.json').read_text())
assert manifest['status']=='COMPLETE' and manifest['source_unchanged_after_transfer']
files={}; total=0
for name in names:
 p=root/name
 assert p.is_file(),name
 assert p.stat().st_size<2000000,name
 data=p.read_bytes(); total+=len(data)
 assert total<10000000
 files[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'base64':base64.b64encode(data).decode()}
print(json.dumps({'files':files}))
"""
def main():
 names=['output_8760/'+x for x in NAMES]+['backup_manifest.json','batch_exit.json','resource_usage.txt','launch_config.json']
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -'],input='release='+repr(RELEASE)+'\nnames='+repr(names)+'\n'+REMOTE,text=True,encoding='utf-8',capture_output=True,timeout=120)
 p.check_returncode(); result=json.loads(p.stdout)
 dst=HERE/'claude_review_package'/'source'
 backup=json.loads(base64.b64decode(result['files']['backup_manifest.json']['base64']))
 entries={x['path']:x for x in backup['files']}
 for name,info in result['files'].items():
  data=base64.b64decode(info.pop('base64')); assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256']
  if name in entries:
   assert info['sha256']==entries[name]['sha256'] and info['bytes']==entries[name]['bytes'],name
   info['backup_manifest_check']='PASS'
  else: info['backup_manifest_check']='SELF_MANIFEST_SOURCE_SHA_VERIFIED'
  target=dst/name; target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists(): assert target.read_bytes()==data,name
  else: target.write_bytes(data)
 result.update(release=RELEASE,total_bytes=sum(v['bytes'] for v in result['files'].values()),file_count=len(result['files']),status='PASS')
 (HERE/'collection_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='files'}))
if __name__=='__main__': main()
