"""Finite R1, reference scoring and engineering gates. No Slurm commands."""
from pathlib import Path
import json,os,subprocess,sys,time,hashlib,traceback

ROOT=Path(__file__).resolve().parent
REPO=ROOT/'repo'
WORK=REPO/'supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114'
SOURCE=Path('/home/zz2/National_model_server/cloud_backup/20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1/output_8760')
REFERENCE=Path('/home/zz2/National_model_server/cloud_backup/20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1/output_8760')
PY=sys.executable
STATE=ROOT/'R1_v1/prepared_state/planning_state_candidate'
RECORDS={}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):(ROOT/name).write_text(json.dumps(value,indent=2)+'\n')
def environment(resource):
 info=json.loads((ROOT/'installation_receipt.json').read_text())
 return dict(os.environ,PYTHONPATH=str(REPO),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CISPO_DATA_ROOT=info['open_data_root' if resource=='open' else 'neutral_data_root'],CISPO_CF_ROOT='/data/zz2/National_model/data/hourly_cf',CISPO_HYDRO_ROOT='/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse',CISPO_RAW_GRFR_ROOT='/data/zz2/National_model/data/grfr_raw_2019',CISPO_WAVE_ROOT='/data/zz2/National_model/data/wave_energy_20260727')

def start(label,args,resource='neutral'):
 assert not (ROOT/(label+'.stdout.log')).exists()
 mem=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))/1024**2
 assert mem>=90,'Existing T550 engineering-build startup threshold requires 90GiB available'
 f=(ROOT/(label+'.stdout.log')).open('x');g=(ROOT/(label+'.stderr.log')).open('x');p=subprocess.Popen([PY]+[str(x) for x in args],cwd=REPO,env=environment(resource),stdout=f,stderr=g)
 RECORDS[label]=dict(pid=p.pid,command=[PY]+[str(x) for x in args],resource=resource,available_memory_gib=mem,status='RUNNING',started_at=time.time());save('execution_results.json',RECORDS)
 return p,f,g

def finish(label,task):
 p,f,g=task;rc=p.wait();f.close();g.close();RECORDS[label].update(returncode=rc,status='PASS' if rc==0 else 'STOP',seconds=time.time()-RECORDS[label]['started_at']);save('execution_results.json',RECORDS);print(json.dumps(dict(phase=label,**RECORDS[label])),flush=True)
 return rc==0

def main():
 assert not (ROOT/'R1_v1').exists() and not (ROOT/'execution_results.json').exists()
 assert json.loads((ROOT/'author_preparation_acceptance.json').read_text())['submission_authorized'] is False
 task=start('r1',['scripts/prepare_continuation_state.py','--source',SOURCE,'--acceptance',ROOT/'author_preparation_acceptance.json','--planning-year','2060','--source-scenario','case3_thermal_ev_v5','--author-decision-label','ACCEPTED_FOR_PREPARATION_ONLY_20261119','--output',ROOT/'R1_v1'])
 if not finish('r1',task):raise RuntimeError('R1 failed; no further gates or reference scoring started')
 assert json.loads((ROOT/'R1_v1/evidence/cleanup_gate.json').read_text())['status']=='PASS'
 pricing=start('reference_pricing',['scripts/price_capacity_bound_selection.py','--run-dir',REFERENCE,'--selection-json',ROOT/'initial_selection.json','--output',ROOT/'reference_pricing_2060','--reference-only','--target-free-sites','5000'])
 identity=start('identity_24h',[WORK/'identity_gate_2060.py','--state',STATE,'--output',ROOT/'identity_24h'])
 ok_identity=finish('identity_24h',identity);ok_pricing=finish('reference_pricing',pricing)
 if not ok_identity or not ok_pricing:raise RuntimeError('Identity gate or reference scoring failed; preserve all outputs')
 proposal=ROOT/'reference_pricing_2060/proposed_selection.json';report=json.loads((ROOT/'reference_pricing_2060/directional_pricing_report.json').read_text());assert report['status']=='PROPOSAL_READY_REQUIRES_GATES'
 initial=json.loads((ROOT/'initial_selection.json').read_text());chosen=json.loads(proposal.read_text());forced={(r['grid_uid'],r['technology']) for r in initial['columns'] if r['state']=='free'};free={(r['grid_uid'],r['technology']) for r in chosen['columns'] if r['state']=='free'};assert forced<=free and len(free)<=5000 and chosen['planning_year']==2060
 final=ROOT/'final_selection.json';assert not final.exists();final.write_bytes(proposal.read_bytes());save('selection_receipt.json',dict(status='PASS',initial_free=845,final_free=len(free),forced_preserved=True,chosen_margin=report['chosen_margin'],sha256=sha(final),source='Reference scores only; own solution certificate still required after a future authorized production solve'))
 one=start('selected_1h',[WORK/'selected_build_2060.py','--state',STATE,'--selection',final,'--output',ROOT/'selected_1h'],'open')
 if not finish('selected_1h',one):raise RuntimeError('Selected 1h gate failed')
 assert json.loads((ROOT/'selected_1h/selection_build_gate.json').read_text())['status']=='PASS'
 day=start('restricted_24h',[WORK/'restricted_gate24_2060.py','--state',STATE,'--selection',final,'--output',ROOT/'restricted_24h'],'open')
 if not finish('restricted_24h',day):raise RuntimeError('Restricted 24h gate failed')
 assert json.loads((ROOT/'restricted_24h/selection_build_gate.json').read_text())['status']=='PASS'
 preflight=start('t550_preflight',['scripts/run_cispo_2030_full_year.py','--config','config/optimization_numeric_dac_by_year_v9_a12.json','--scenario-config','config/scenarios/ops_open_resource_v1.json','--solver-config','config/solver_profiles/barrier_stagea_resource_restricted_agg0_v1_threads44.json','--planning-year','2060','--horizon','full_year','--state-in',STATE,'--allow-candidate-state-in','--capacity-bound-selection',final,'--preflight-only','--output-dir',ROOT/'t550_preflight'],'open')
 if not finish('t550_preflight',preflight):raise RuntimeError('T550 preflight failed')
 assert json.loads((ROOT/'t550_preflight/preflight_report.json').read_text())['status']=='PASS'
 save('PREPARATION_GATES_COMPLETE.json',dict(status='PASS',submission_authorized=False,submitted=False,planning_year=2060,source_commit=json.loads((ROOT/'installation_receipt.json').read_text())['source_commit'],selection_sha256=sha(final),free_groups=len(free),records=RECORDS))

if __name__=='__main__':
 try:main()
 except Exception as e:
  save('STOP.json',dict(status='STOP',error=repr(e),records=RECORDS,submitted=False));traceback.print_exc();raise
