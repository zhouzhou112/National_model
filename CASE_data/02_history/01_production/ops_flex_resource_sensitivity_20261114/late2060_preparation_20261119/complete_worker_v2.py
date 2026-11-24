"""Continue only after the corrected central-resource identity gate passes."""
from pathlib import Path
import json,traceback
import prepare_worker as shared

ROOT=shared.ROOT
REPO=shared.REPO
WORK=shared.WORK
STATE=shared.STATE

def save(name,value):
 if name=='execution_results.json':name='execution_results_v2.json'
 (ROOT/name).write_text(json.dumps(value,indent=2)+'\n')

def main():
 previous=json.loads((ROOT/'execution_results.json').read_text())
 assert previous['r1']['status']==previous['reference_pricing']['status']=='PASS'
 assert json.loads((ROOT/'identity_v2_result.json').read_text())['status']=='PASS'
 assert json.loads((ROOT/'identity_24h_central_v2/identity_gate.json').read_text())['status']=='PASS'
 assert json.loads((ROOT/'R1_v1/evidence/cleanup_gate.json').read_text())['status']=='PASS'
 assert not (ROOT/'execution_results_v2.json').exists()
 shared.save=save;shared.RECORDS={}
 report=json.loads((ROOT/'reference_pricing_2060/directional_pricing_report.json').read_text());assert report['status']=='PROPOSAL_READY_REQUIRES_GATES'
 proposal=ROOT/'reference_pricing_2060/proposed_selection.json';initial=json.loads((ROOT/'initial_selection.json').read_text());chosen=json.loads(proposal.read_text())
 forced={(r['grid_uid'],r['technology']) for r in initial['columns'] if r['state']=='free'};free={(r['grid_uid'],r['technology']) for r in chosen['columns'] if r['state']=='free'}
 assert len(forced)==845 and forced<=free and len(free)<=5000 and chosen['planning_year']==2060
 final=ROOT/'final_selection.json';assert not final.exists();final.write_bytes(proposal.read_bytes())
 save('selection_receipt.json',dict(status='PASS',initial_free=845,final_free=len(free),forced_preserved=True,chosen_margin=report['chosen_margin'],sha256=shared.sha(final),source='Central LATE2060 reference scores only; future own solution certificate still required'))
 for label,helper,hours in [('selected_1h','selected_build_2060.py',1),('restricted_24h','restricted_gate24_2060.py',24)]:
  task=shared.start(label,[WORK/helper,'--state',STATE,'--selection',final,'--output',ROOT/label],'open')
  if not shared.finish(label,task):raise RuntimeError(label+' failed')
  assert json.loads((ROOT/label/'selection_build_gate.json').read_text())['status']=='PASS'
 task=shared.start('t550_preflight',['scripts/run_cispo_2030_full_year.py','--config','config/optimization_numeric_dac_by_year_v9_a12.json','--scenario-config','config/scenarios/ops_open_resource_v1.json','--solver-config','config/solver_profiles/barrier_stagea_resource_restricted_agg0_v1_threads44.json','--planning-year','2060','--horizon','full_year','--state-in',STATE,'--allow-candidate-state-in','--capacity-bound-selection',final,'--preflight-only','--output-dir',ROOT/'t550_preflight'],'open')
 if not shared.finish('t550_preflight',task):raise RuntimeError('T550 preflight failed')
 assert json.loads((ROOT/'t550_preflight/preflight_report.json').read_text())['status']=='PASS'
 save('PREPARATION_GATES_COMPLETE_v2.json',dict(status='PASS',submission_authorized=False,submitted=False,planning_year=2060,source_commit=json.loads((ROOT/'installation_receipt.json').read_text())['source_commit'],selection_sha256=shared.sha(final),free_groups=len(free),identity_gate='identity_24h_central_v2/identity_gate.json',identity_reference_scope='Central-resource generic entry identity; actual Open2060 tested separately with own Open2050 R1 state',records=shared.RECORDS))

if __name__=='__main__':
 try:main()
 except Exception as e:
  save('STOP_v2.json',dict(status='STOP',error=repr(e),records=shared.RECORDS,submitted=False));traceback.print_exc();raise
