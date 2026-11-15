"""Finite validation in a new T550 copy, never overwrite previous runs."""
from pathlib import Path
import base64,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
REMOTE='/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -']
updates={n:base64.b64encode((REPO/n).read_bytes()).decode() for n in ['scripts/run_cispo_2030_full_year.py','tests/test_resource_factor_probe.py']}
code='root='+repr(REMOTE)+'\nupdates='+repr(updates)+'\n'+r'''
from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess,time
root=Path(root);old=root/'validation_runtime_v6';new=root/'validation_runtime_v7'
assert not new.exists();new.mkdir()
shutil.copytree(old/'repo',new/'repo',symlinks=True)
shutil.copytree(old/'late_upstream',new/'late_upstream')
repo=new/'repo';work=repo/'supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114'
for n,b in updates.items():(repo/n).write_bytes(base64.b64decode(b))
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(repo),CISPO_DATA_ROOT=str(root/'baseline_runtime/data_roots/neutral'),CISPO_CF_ROOT='/data/zz2/National_model/data/hourly_cf',CISPO_HYDRO_ROOT='/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse',CISPO_RAW_GRFR_ROOT='/data/zz2/National_model/data/grfr_raw_2019',CISPO_WAVE_ROOT='/data/zz2/National_model/data/wave_energy_20260727')
py='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
subprocess.run(['git','add','scripts/run_cispo_2030_full_year.py','tests/test_resource_factor_probe.py'],cwd=repo,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','-c','user.name=Validation Snapshot','-c','user.email=validation@local.invalid','commit','-m','Validate resource profile physical row contract'],cwd=repo,check=True,stdout=subprocess.DEVNULL)
def run(name,argv,data='neutral'):
 env['CISPO_DATA_ROOT']=str(root/'baseline_runtime/data_roots'/data)
 start=time.monotonic()
 with (new/(name+'.stdout.log')).open('w') as out,(new/(name+'.stderr.log')).open('w') as err:
  p=subprocess.run(argv,cwd=repo,env=env,stdout=out,stderr=err)
 r=dict(exit_code=p.returncode,seconds=time.monotonic()-start,command=argv,stderr_tail=(new/(name+'.stderr.log')).read_text()[-5500:])
 (new/(name+'_result.json')).write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({name:r}),flush=True)
 return r
suite=run('unittest',[py,'-m','unittest','discover','-s','tests','-v'])
suite['tested_source_lf_sha256']={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for d in ['cispo_model','scripts','config','tests'] for p in (repo/d).rglob('*') if p.is_file() and p.suffix in ['.py','.json'] and '__pycache__' not in p.parts}
(new/'unittest_result.json').write_text(json.dumps(suite,indent=2)+'\n')
assert suite['exit_code']==0
late=run('late_selected_1h',[py,str(work/'late_selected_build.py'),'--state',str(new/'late_upstream/planning_state_candidate'),'--selection',str(work/'LATE_Open_2050_fixed_selection.json'),'--output',str(new/'late_open_selected_1h')],'open')
source='/home/zz2/National_model_server/base_frozen_batch2_20261027/repo/supplementary_materials/reviews/base_frozen_followups_20261027/source_base/20260930_base2050_v9_t48_m750_tol1e4_v1'
closure='/home/zz2/National_model_server/base_frozen_batch2_20261027/repo/supplementary_materials/reviews/base_frozen_batch2_20261027/2050/cloud_identity_v2/derived_static/closure.json'
for case,resource in [('ops_open','open'),('ops_conservative','conservative'),('D1','base')]:
 argv=[py,'scripts/run_resource_sensitivity_case.py','--resource',resource,'--reference',str(work/'contractable_total_national_source.csv'),'--','--config','config/optimization_numeric_dac_by_year_v9_a12.json','--solver-config','config/solver_profiles/barrier_stagea_base_frozen_agg0_v1_threads44.json','--scenario-config','config/scenarios/'+('case3_thermal_ev_v5' if resource=='base' else 'ops_'+resource+'_resource_v1')+'.json','--planning-year','2050','--diagnostic-hours','1','--build-only','--archive-original-model','--frozen-capacity-from',source+'/output_8760','--frozen-capacity-supplement',source+'/frozen_capacity_B_20261027','--frozen-capacity-closure',closure,'--output-dir',str(new/(case+'_production_profile_1h'))]
 if case=='D1':argv+=['--capacity-bound-selection',str(work/'D1_intra_selection.json')]
 run(case,argv,'neutral' if resource=='base' else resource)
'''
p=subprocess.run(SSH,input=code,text=True,encoding='utf-8',capture_output=True)
(HERE/'validation_v7_transport.stdout.log').write_text(p.stdout,encoding='utf-8')
(HERE/'validation_v7_transport.stderr.log').write_text(p.stderr,encoding='utf-8')
print(p.stdout[-9000:]);print(p.stderr[-2000:]);raise SystemExit(p.returncode)
