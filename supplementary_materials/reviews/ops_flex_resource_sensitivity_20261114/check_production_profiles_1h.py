"""Fresh 1h builds of the exact three production entry profiles; no optimize."""
from pathlib import Path
import json,subprocess
HERE=Path(__file__).resolve().parent
code=r'''
from pathlib import Path
import json,os,subprocess,time
root=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114');v=root/'validation_runtime_v7';repo=v/'repo';work=repo/'supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114'
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(repo),CISPO_CF_ROOT='/data/zz2/National_model/data/hourly_cf',CISPO_HYDRO_ROOT='/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse',CISPO_RAW_GRFR_ROOT='/data/zz2/National_model/data/grfr_raw_2019',CISPO_WAVE_ROOT='/data/zz2/National_model/data/wave_energy_20260727')
py='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
source='/home/zz2/National_model_server/base_frozen_batch2_20261027/repo/supplementary_materials/reviews/base_frozen_followups_20261027/source_base/20260930_base2050_v9_t48_m750_tol1e4_v1'
closure='/home/zz2/National_model_server/base_frozen_batch2_20261027/repo/supplementary_materials/reviews/base_frozen_batch2_20261027/2050/cloud_identity_v2/derived_static/closure.json'
results={}
for case,resource in [('ops_open','open'),('ops_conservative','conservative'),('D1','base')]:
 out=v/(case+'_production_core_1h');assert not out.exists()
 env['CISPO_DATA_ROOT']=str(root/'baseline_runtime/data_roots'/('neutral' if resource=='base' else resource))
 argv=[py,'scripts/run_cispo_2030_full_year.py','--config','config/optimization_numeric_dac_by_year_v9_a12.json','--solver-config','config/solver_profiles/barrier_stagea_base_frozen_agg0_v1_threads44.json','--scenario-config','config/scenarios/'+('case3_thermal_ev_v5' if resource=='base' else 'ops_'+resource+'_resource_v1')+'.json','--planning-year','2050','--diagnostic-hours','1','--build-only','--archive-original-model','--frozen-capacity-from',source+'/output_8760','--frozen-capacity-supplement',source+'/frozen_capacity_B_20261027','--frozen-capacity-closure',closure,'--output-dir',str(out)]
 if case=='D1':argv+=['--capacity-bound-selection',str(work/'D1_intra_selection.json')]
 start=time.monotonic()
 with (v/(out.name+'.stdout.log')).open('w') as f,(v/(out.name+'.stderr.log')).open('w') as g:p=subprocess.run(argv,cwd=repo,env=env,stdout=f,stderr=g)
 r=dict(exit_code=p.returncode,seconds=time.monotonic()-start,command=argv,stderr_tail=(v/(out.name+'.stderr.log')).read_text()[-2500:])
 for n in ['build_report.json','annual_capacity_link_row_scaling.json','frozen_capacity_report.json','run_identity.json']:
  if (out/n).exists():r[n]=json.loads((out/n).read_text())
 r['status']='PASS' if p.returncode==0 else 'STOP';results[case]=r
 (v/'production_profile_1h_receipts.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(dict(case=case,status=r['status'],seconds=r['seconds'],stderr=r['stderr_tail'])),flush=True)
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -'],input=code,text=True,encoding='utf-8',capture_output=True)
(HERE/'production_profile_transport.stdout.log').write_text(p.stdout,encoding='utf-8');(HERE/'production_profile_transport.stderr.log').write_text(p.stderr,encoding='utf-8');print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)
