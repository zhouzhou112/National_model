"""Bind one completed year gate to regression, source/input hashes and authorization."""
from pathlib import Path
import argparse,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('year',type=int,choices=[2030,2040,2060]);a=ap.parse_args();work=HERE/'batch2'/str(a.year);target=work/'FINAL_YEAR_RELEASE_GATES.json';assert not target.exists()
 gates=load(work/'YEAR_GATES_PASSED.json');tests=load(HERE/'batch2/full_tests.json');local=load(HERE/'batch2/unchanged_local_archive_tests.json');inputs=load(HERE/'batch2/input_identity_recheck.json');install=load(HERE/'batch2/installation_receipt.json');info=install['years'][str(a.year)]
 assert gates['status']=='PASS' and gates['year']==a.year and gates['all_individual_gates_pass']
 assert tests['status']=='PASS' and tests['tests']==537 and len(tests['skips'])==2
 assert all(any(name in line for line in tests['skips']) for name in ['test_known_2050_cleanup_matches_independent_historical_audit','test_archived_2050_and_offline_source_immutable'])
 assert local['status']=='PASS' and local['tests']==2 and all(local['source_unchanged'].values())
 assert inputs['status']==install['status']=='PASS'
 assert sha(work/'window_carbon_budget.json')==info['budget_sha256']
 for path,wanted in tests['tested_source_lf_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==wanted,path
 auth=load(HERE/'batch2/AUTHORIZATION.json');assert auth['batch']==2 and auth['third_batch_authorized'] is False
 code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();template=load(HERE/'batch2/template_source.json')
 report=dict(status='PASS',year=a.year,batch=2,third_batch_authorized=False,source_commit=code,template_sha256=template['sha256'],closure_sha256=info['closure_sha256'],budget_sha256=info['budget_sha256'],source_result_manifest_sha256=info['source_result_manifest_sha256'],checks=dict(per_year_1h_24h_and_production_profile='PASS',neutrality_relative_objective_difference=gates['neutrality_relative_objective_difference'],monotonicity_relative_order_violations=gates['relative_order_violations'],objective_comparison_relative_tolerance=1e-7,full_regression_tests_covered=537,T550_passed=535,unchanged_local_archive_tests=2,immutable_input_SHA='PASS',original_frozen_source_and_closure_reused=True,threads=44),evidence_sha256={str(p.relative_to(HERE)):sha(p) for p in [work/'YEAR_GATES_PASSED.json',work/'window_carbon_budget.json',HERE/'batch2/full_tests.json',HERE/'batch2/unchanged_local_archive_tests.json',HERE/'batch2/input_identity_recheck.json',HERE/'batch2/installation_receipt.json',HERE/'batch2/AUTHORIZATION.json']})
 target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(year=a.year,status='PASS',checks=report['checks'])))
if __name__=='__main__':main()
