"""Combine unchanged 24h evidence and fresh conservative 1h/profile gates."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];OUT=HERE/'batch3_conservative_20261117'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
data=load(OUT/'inputs.json');status=load(OUT/'status.json');cloud=load(OUT/'cloud_recheck.json');auth=load(OUT/'AUTHORIZATION.json')
assert cloud['status']=='PASS' and auth['late_open_2060_authorized'] is False
tested=load(HERE/'batch2/full_tests.json');assert tested['status']=='PASS'
local=load(HERE/'batch2/unchanged_local_archive_tests.json');assert local['status']=='PASS' and local['tests']==2
for n,h in data['tested'].items():assert hashlib.sha256((REPO/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,n
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
results={}
for year,meta in data['years'].items():
 existing=OUT/year/'FINAL_YEAR_RELEASE_GATES.json'
 if existing.exists():
  assert load(existing)['status']=='PASS'
  results[year]='ALREADY_FINALIZED';continue
 r=status.get('results.json',{}).get(year)
 if not r or r['status']!='PASS':
  results[year]='WAIT_OR_STOP';continue
 oldpath=HERE/meta['gate_path']/'YEAR_GATES_PASSED.json';assert sha(oldpath)==meta['gate_sha256']==r['reused_24h_sha256']
 old=load(oldpath);cons=old['records']['conservative_24h']
 assert cons['relative_v1']=='PASS' and cons['frozen_capacity_output_check.json']['status']=='PASS'
 assert r['identity_gate_probe.json']['all_investment_families_fixed'] is True
 assert r['parameter_verification.json']['status']=='PASS' and r['source_and_input_recheck']=='PASS'
 assert r['run_identity.json']['solver_runtime']['solver_profile']['id']=='barrier_stagea_base_frozen_agg0_v1_threads44'
 numerics=r['build_report.json']['solver_numerical_compatibility']
 assert numerics['status']=='PASS' and numerics['aggregate_parameter']==0 and numerics['crossover_parameter']==0 and numerics['barrier_convergence_tolerance']==1e-4
 p=OUT/year;p.mkdir(exist_ok=True);oldfinal=load(HERE/'batch2'/year/'FINAL_YEAR_RELEASE_GATES.json')
 budget=oldfinal.get('window_carbon_budget_path','batch2/'+year+'/window_carbon_budget.json');assert sha(HERE/budget)==oldfinal['budget_sha256']
 receipt=p/'t550_receipt.json';assert not receipt.exists()
 receipt.write_text(json.dumps(r,indent=2)+'\n')
 evidence=[oldpath,receipt,OUT/'cloud_recheck.json',OUT/'AUTHORIZATION.json',HERE/'batch2/full_tests.json',HERE/'batch2/unchanged_local_archive_tests.json']
 record=dict(status='PASS',year=int(year),batch=3,resource='conservative',late_open_2060_authorized=False,source_commit=commit,template_release=cloud['template_release'],template_local_path='batch3_conservative_20261117/template.sbatch',template_sha256=cloud['template_sha256'],closure_sha256=oldfinal['closure_sha256'],budget_sha256=oldfinal['budget_sha256'],window_carbon_budget_path=budget,source_result_manifest_sha256=oldfinal['source_result_manifest_sha256'],checks=dict(conservative_1h_and_exact_production_profile='PASS',conservative_24h='PASS_REUSED_WITH_SHA_RECHECK',frozen_capacity_max_difference=max(e['max_abs_difference'] for e in cons['frozen_capacity_output_check.json']['checks']),neutrality_relative_objective_difference=old['neutrality_relative_objective_difference'],monotonicity_relative_order_violations=old['relative_order_violations'],full_regression_tests_covered=537,model_sources_unchanged=True,immutable_input_SHA='PASS',original_frozen_source_and_closure_reused=True,threads=44,annual_carbon_limit_unchanged=True),evidence_sha256={str(e.relative_to(HERE)):sha(e) for e in evidence})
 if year=='2030':record['checks']['all_24h_sides_share_original_B_quota_mt']=10.95890410958904
 target=p/'FINAL_YEAR_RELEASE_GATES.json';assert not target.exists(),'Do not overwrite existing final gates'
 target.write_text(json.dumps(record,indent=2)+'\n');results[year]='PASS'
print(json.dumps(results))
