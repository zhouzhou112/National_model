"""Check retained continuation gates and source identities before freezing a release."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['case3_2040','C2050'],required=True);a=p.parse_args()
 year=2040 if a.case=='case3_2040' else 2050
 names=['case3_2040_screen_1h_02','case3_2040_unscreen_1h_02','case3_2040_24h_01'] if year==2040 else ['C2050_screen_1h_01','C2050_unscreen_1h_01','C2050_24h_01']
 checks={};evidence={};audits={}
 for name in names:
  out=HERE/name;g=json.loads((out/'continuation_gate.json').read_text());checks[name+'.runner']=g['runner_exit_code']==0;checks[name+'.parameter']=g['parameters']=='PASS';checks[name+'.tiny_headroom']=g['tiny_capacity_columns']==[]
  b=json.loads((out/'build_report.json').read_text());audit=b['numerical_robustness_audit'];audits[name]=audit
  allowed={'retrofit_upper_cleanup','hydro_capacity_headroom_cleanup','other_capacity_headroom_cleanup','capacity_rhs_cleanup'}
  checks[name+'.cleanup_whitelist']=set(audit)<=allowed
  for label in ('hydro_capacity_headroom_cleanup','retrofit_upper_cleanup'):
   items=audit.get(label,[]);items=[items] if isinstance(items,dict) else items
   checks[name+'.'+label]=all(x['cutoff_gw']==1e-5 and all(0<=v<=1e-5 for v in x['removed_gw']) for x in items)
  checks[name+'.capacity_rhs_cleanup']=all(x['cleaned_rhs']==0 and abs(x['original_rhs'])<1e-12 and x['reason']=='OPPOSITE_SIGN_CAPACITY_CANCELLATION_ROUNDOFF' for x in audit.get('capacity_rhs_cleanup',[]))
  checks[name+'.other_capacity_headroom_cleanup']=all(x['cutoff']==1e-5 and x['unit'] in ('GW','GWh') and x['closed_upper']==x['inherited_lower'] for x in audit.get('other_capacity_headroom_cleanup',[]))
  if g['hours']==24:
   checks['OPTIMAL']=g['status_code']==2;checks['M']=g['M']<=1e-3;checks['credit']=all(v<=1e-3 for v in g['credit'].values())
   checks['relative_v1_present']='relative_v1' in g['solution_qc.json']['acceptance_profiles']
   pres=g['preservation_report.json'];checks['preservation']=pres['status']=='COMPLETE' and not pres['errors'] and pres['original_model_archived'] and pres['stages']['raw_checkpoint']=='COMPLETE' and pres['stages']['candidate_selection']=='COMPLETE'
   checks['candidate_csv']=(out/'candidate_selection.csv').is_file()
  for file in ['continuation_gate.json','build_report.json','parameter_verification.json','input_manifest.csv','model_config_snapshot.json','model_archive/archive_manifest.json']:
   evidence[(out/file).relative_to(ROOT).as_posix()]=sha(out/file)
 identity=json.loads((HERE/(a.case+'_mps_identity.json')).read_text());checks['screen_only_new_bounds']=identity['status']=='PASS' and identity['different_segments']==['BOUNDS_VRE_NEW']
 r1=HERE/('R1_case3_2040_02' if year==2040 else 'R1_C2050_01');cleanup=json.loads((r1/'evidence/cleanup_gate.json').read_text());checks['R1']=cleanup['status']=='PASS'
 for file in (r1/'prepared_state').rglob('*'):
  if file.is_file():evidence[file.relative_to(ROOT).as_posix()]=sha(file)
 sourcepaths=['cispo_model/continuation_cleanup.py','cispo_model/factor_screen.py','scripts/run_cispo_2030_full_year.py',f'config/solver_profiles/barrier_stagea_screened_agg0_{year}_v1_threads48.json', 'config/optimization_numeric_dac_by_year_v9_a12.json','config/scenarios/case3_thermal_ev_v5.json',str((HERE/'continuation.sbatch').relative_to(ROOT)).replace('\\','/')]
 hashes={f:hashlib.sha256((ROOT/f).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for f in sourcepaths}
 report=dict(status='PASS' if all(checks.values()) else 'FAIL',case=a.case,year=year,checks=checks,tested_source_lf_sha256=hashes,evidence_sha256=evidence,cleanup_audits=audits,regression_log_sha256=sha(HERE/'regression.stderr.log'),gate_paths=names)
 (HERE/(a.case+'_final_gates.json')).write_text(json.dumps(report,indent=2)+'\n');print(report['status'],{k:v for k,v in checks.items() if not v})
 if report['status']!='PASS':raise SystemExit(2)
if __name__=='__main__':main()
