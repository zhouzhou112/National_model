"""Publish release eligibility only after all scoped 2030 exception gates pass."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=HERE/'batch2/2030/author_window_v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def main():
 target=HERE/'batch2/2030/FINAL_YEAR_RELEASE_GATES.json';assert not target.exists()
 gate=load(OUT/'YEAR_GATES_PASSED.json');install=load(OUT/'installation_receipt.json');tests=load(HERE/'batch2/full_tests.json');local=load(HERE/'batch2/unchanged_local_archive_tests.json');info=install['years']['2030'];budget=load(OUT/'window_carbon_budget.json')
 assert gate['status']=='PASS' and gate['year']==2030 and gate['all_individual_gates_pass']
 assert tests['status']=='PASS' and tests['tests']==537 and len(tests['skips'])==2 and local['status']=='PASS' and local['tests']==2
 assert load(OUT/'execution_receipt.json')['scope_tests']=='3 PASS'
 assert budget['budget_rule']=='AUTHOR_2030_ORIGINAL_B_WINDOW_20261115' and budget['author_approval']=='2030沿用原B窗口额度（推荐）'
 assert sha(OUT/'window_carbon_budget.json')==info['budget_sha256']
 for name in ['original_B_24h','neutral_24h','open_24h','conservative_24h','zero_24h']:
  r=gate['records'][name]['window_carbon_override.json'];assert r['budget_rule']==budget['budget_rule'] and r['effective_window_carbon_limit_mt']==budget['window_carbon_limit_mt'] and r['original_annual_carbon_limit_mt']==4000
 for p,h in tests['tested_source_lf_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,p
 assert load(HERE/'batch2/input_identity_recheck.json')['status']=='PASS'
 template=load(OUT/'template_source.json');path=HERE/'batch2/deployment/ops_open_2060/job.sbatch';assert hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==template['sha256']
 report=dict(status='PASS',year=2030,batch=2,third_batch_authorized=False,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),template_sha256=template['sha256'],template_local_path='batch2/deployment/ops_open_2060/job.sbatch',template_release='20261115_opsopen_2060_v9a12_t44_m750_tol1e4_v1',closure_sha256=None,budget_sha256=info['budget_sha256'],window_carbon_budget_path='batch2/2030/author_window_v2/window_carbon_budget.json',source_result_manifest_sha256=info['source_result_manifest_sha256'],checks=dict(per_year_1h_24h_and_production_profile='PASS',neutrality_relative_objective_difference=gate['neutrality_relative_objective_difference'],monotonicity_relative_order_violations=gate['relative_order_violations'],full_regression_tests_covered=537,scoped_author_exception_tests=3,immutable_input_SHA='PASS',annual_carbon_limit_unchanged_mt=4000,all_24h_sides_share_original_B_quota_mt=budget['window_carbon_limit_mt'],threads=44),evidence_sha256={str(p.relative_to(HERE)):sha(p) for p in [OUT/'YEAR_GATES_PASSED.json',OUT/'window_carbon_budget.json',OUT/'installation_receipt.json',OUT/'execution_receipt.json',HERE/'batch2/full_tests.json',HERE/'batch2/AUTHORIZATION.json']})
 target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(year=2030,status='PASS',checks=report['checks'])))
if __name__=='__main__':main()
