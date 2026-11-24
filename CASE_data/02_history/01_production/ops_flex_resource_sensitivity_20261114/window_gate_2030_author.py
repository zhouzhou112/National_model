"""Author-approved original B2030 carbon quota, only for its 24h engineering gates."""
from pathlib import Path
import hashlib,json,math
RULE='AUTHOR_2030_ORIGINAL_B_WINDOW_20261115'
SOURCE_SHA='af1e51f1c13d7bc41b997c1d4fafa8fee7efbffe40103d64b6bc5d79960dc342'
def apply_window_budget(art,budget_path,source_output,year,hours,output):
 p=Path(budget_path);budget=json.loads(p.read_text(encoding='utf-8'))
 if year!=2030 or hours!=24 or budget['year']!=2030 or budget['hour_indices']!=list(range(24)):
  raise ValueError('Author exception is only the exact 2030 first-24h gate')
 if budget.get('budget_rule')!=RULE or budget.get('author_approval')!='2030沿用原B窗口额度（推荐）':
  raise ValueError('Missing explicit author exception')
 source_sha=hashlib.sha256((Path(source_output)/'result_manifest.json').read_bytes()).hexdigest()
 if budget['status']!='PASS' or source_sha!=SOURCE_SHA or budget['source_result_manifest_sha256']!=source_sha:
  raise ValueError('B2030 source identity mismatch')
 annual=art.index['annual_carbon_limit_mtco2_per_year'];fraction=art.index['annual_flow_scaling_factor'];value=budget['window_carbon_limit_mt']
 if annual!=4000 or budget['original_annual_carbon_limit_mt']!=4000 or fraction!=24/8760:
  raise ValueError('Annual carbon limit or horizon changed')
 if not math.isfinite(value) or not math.isclose(value,4000*24/8760,rel_tol=0,abs_tol=1e-12):
  raise ValueError('Not the approved original B2030 quota')
 row=art.index['constraint_handles']['annual_net_carbon_limit']
 if row.Sense!='<' or not math.isclose(float(row.RHS),4000*24/8760,rel_tol=0,abs_tol=1e-12):
  raise ValueError('Original model carbon row changed')
 original=float(row.RHS);row.RHS=value;art.index['selected_horizon_carbon_limit_mtco2']=value;art.model.update()
 report=dict(status='PASS',year=year,hours=hours,budget_rule=RULE,source_result_manifest_sha256=source_sha,budget_payload_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),original_window_carbon_limit_mt=original,effective_window_carbon_limit_mt=value,original_annual_carbon_limit_mt=annual,production_annual_carbon_limit_unchanged=True,scope='TEST_ONLY_TRUNCATED_HORIZON',previous_failed_budget_mt=budget['previous_failed_budget_mt'])
 (Path(output)/'window_carbon_override.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report
