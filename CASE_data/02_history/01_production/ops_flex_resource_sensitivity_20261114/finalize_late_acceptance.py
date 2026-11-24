"""Evidence-only conditional acceptance of the restricted LATE-Open solution."""
from pathlib import Path
import copy,json,math
import numpy as np
from prepare_late_acceptance import BASE,RELEASE,SIDE,sha,save
from annual_row_acceptance import row_check

def decide(physical_pass,row_pass,own_certificate,pinf,gap,ratio):
 return dict(physical_relative_checks=bool(physical_pass),maximum_row_within_family_tolerance=bool(row_pass),own_directional_certificate=bool(own_certificate) and math.isfinite(ratio) and 0<=ratio<=1e-2,terminal_pinf_author_range=math.isfinite(pinf) and 1e-2<=pinf<=1e-1,relative_primal_dual_gap=math.isfinite(gap) and 0<=gap<=1e-2)

def main():
 b=BASE/RELEASE;root=b/'output_8760';out=b/SIDE
 assert json.loads((out/'PREPARATION_COMPLETE.json').read_text())['status']=='PASS'
 baseline=json.loads((out/'solution_qc_relative_v1_baseline.json').read_text());solve=json.loads((root/'solve_report.json').read_text());row=json.loads((out/'row_audit_full.json').read_text());price=json.loads((out/'pricing/directional_pricing_report.json').read_text());cert=price['certificate'];metrics=solve['solution_contract']['barrier_primal_dual_metrics']
 assert solve['status']=='OPTIMAL' and row['index']==solve['solution_quality_locations']['maximum_constraint_violation']['index']
 assert row['source_result_manifest_sha256']==sha(root/'result_manifest.json')
 assert price['source_sha256']['solve_report.json']==sha(root/'solve_report.json')
 assert price['identity']['mps_sha256']==row['source_files']['model_archive/original.mps.gz']['sha256']
 assert price['selection_sha256']==sha(b/'capacity_selection.json')
 family=row_check(row)
 actual=solve.get('solution_quality',{}).get('maximum_constraint_violation')
 if actual is None:actual=json.loads((root/'solution_qc.json').read_text())['solver_quality']['maximum_constraint_violation']
 agreement=abs(float(row['violation'])-float(actual));assert agreement<=max(1e-8,abs(float(actual))*1e-5)
 physical={k:v for k,v in baseline['acceptance_profiles']['relative_v1']['checks'].items() if k!='solver'}
 physical_pass=all(v.get('passed') is True or (k=='reservoir_transition' and v.get('status')=='DEFERRED_BY_AUTHOR_20261012') for k,v in physical.items())
 P=float(metrics['primal_objective']);D=float(metrics['dual_objective']);B=float(cert['B_million_cny']);ratio=float(cert['B_over_objective']);assert math.isfinite(B) and B>=0 and math.isclose(B/P,ratio,rel_tol=1e-12,abs_tol=1e-15)
 assert math.isclose(float(cert['objective_million_cny']),P,rel_tol=1e-12)
 conditions=decide(physical_pass,family['passed'],price['scope']=='FIXED_SOLUTION_CERTIFICATE',float(metrics['primal_infeasibility']),float(metrics['relative_primal_dual_objective_gap']),ratio)
 conditions['annual_resource_structure']=json.loads((root/'resource_structure_audit.json').read_text())['status']=='PASS'
 conditions['original_preservation']=json.loads((root/'preservation_report.json').read_text())['status']=='COMPLETE'
 central=BASE/'20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2/output_8760/solve_report.json';centralP=float(json.loads(central.read_text())['objective_value_million_cny'])
 conditions['objective_not_above_central_LATE']=P<=centralP
 accepted=all(conditions.values());status='PASS' if accepted else 'STOP_AUTHOR_CONDITION_NOT_MET'
 compact={k:v for k,v in row.items() if k not in ['terms','annual_capacity_link_row_scaling']};compact.update(family_assessment=family,term_count=len(row['terms']),full_row_audit_sha256=sha(out/'row_audit_full.json'),full_row_audit_remote_path=str(out/'row_audit_full.json'))
 save(out/'row_audit_summary.json',compact)
 import csv
 with (out/'pricing/boundary_directional_prices.csv').open(newline='') as f:prices=list(csv.DictReader(f))
 distributions={}
 for state,key in [('lower','increase_rc_ratio'),('upper','decrease_rc_ratio')]:
  values=np.array([float(r[key]) for r in prices if r['state']==state],dtype=float)
  distributions[state]=dict(count=len(values),negative=int(np.sum(values<0)),quantiles=dict(zip(['min','p01','p05','p50','p95','p99','max'],[float(x) for x in np.quantile(values,[0,.01,.05,.5,.95,.99,1])]))) if len(values) else dict(count=0)
 record=dict(status=status,case='LATE-Open-2050',planning_year=2050,release=RELEASE,checks=conditions,P_million_cny=P,D_million_cny=D,primal_dual_gap_million_cny=P-D,screening_B_million_cny=B,B_over_objective=ratio,B_to_original_gap=B/(P-D),barrier_primal_infeasibility=metrics['primal_infeasibility'],barrier_primal_infeasibility_disclosure_only=accepted,row=family,maximum_violation_reconstruction_difference=agreement,certificate=cert,directional_rc_ratio_distributions=distributions,strict_source_status=json.loads((root/'solution_qc.json').read_text())['status'],evidence_sha256={n:sha(out/n) for n in ['backup_verification.json','solution_qc_relative_v1_baseline.json','row_audit_full.json','pricing/directional_pricing_report.json']},central_LATE_objective_million_cny=centralP,central_LATE_point_saving_yi_cny=(centralP-P)/100,automatic_resolve=False,comparison_resolve_requires_author=ratio>1e-4,author_adoption='PENDING_AUTHOR_REVIEW',late_2060_authorized=False,source_archives_modified=False)
 save(out/'acceptance_record.json',record)
 revised=copy.deepcopy(baseline);rp=revised['acceptance_profiles']['relative_v1'];rp['baseline_status']=rp['status'];rp['baseline_solver_check']=copy.deepcopy(rp['checks']['solver']);rp['conditional_evidence_sha256']=sha(out/'acceptance_record.json')
 if accepted:rp['checks']['solver'].update(passed=True,classification='CONDITIONAL_DISCLOSURE_AUTHOR_20261106',conditions=conditions);rp['status']='PASS'
 save(out/'solution_qc_relative_v1.json',revised)
 save(out/'ACCEPTANCE_AND_ROWS_COMPLETE.json',dict(status=status,case='LATE-Open-2050',source_unchanged=True))
 print(json.dumps(dict(status=status,B=B,B_over_objective=ratio,row=family,checks=conditions)),flush=True)
 if not accepted:raise SystemExit(2)

if __name__=='__main__':main()
