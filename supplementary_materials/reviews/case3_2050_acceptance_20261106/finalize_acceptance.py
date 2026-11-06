"""Evidence-bound 2026-11-06 acceptance and excluded-column diagnostics.
Runs on T550; reads immutable archives and existing finite audits, writes a NEW
sidecar directory. Never solves, edits archived QC, or schedules production.
"""
import argparse, copy, csv, hashlib, json, math, pathlib, re
import numpy as np

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def save(p,x):
 if p.exists():raise FileExistsError(p)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def row_check(row):
 if row['status']!='ORDER_AND_ROW_VERIFIED' or row['sense']!='=':raise ValueError('Row order/sense not verified')
 match=re.fullmatch(r'province_annual_external_sent_p(\d+)',row['name'])
 if not match:raise ValueError('Unreviewed row family; stop for author review')
 groups={}
 for t in row['terms']:groups.setdefault(t['variable'].split('[')[0],[]).append(t)
 expected={'province_annual_external_sent_gwh','flow_forward_gw','flow_reverse_ac_gw'}
 if not set(groups)<=expected or 'province_annual_external_sent_gwh' not in groups:raise ValueError('Unexpected annual row variables')
 account=groups['province_annual_external_sent_gwh']
 if len(account)!=1 or account[0]['coefficient']!=1:raise ValueError('Unexpected annual account coefficient')
 for k,terms in groups.items():
  if k!='province_annual_external_sent_gwh' and (len(terms)%8760 or any(t['coefficient']!=-1 for t in terms)):raise ValueError('Not an unscaled full-year flow sum')
 magnitude=float(row['row_magnitude']); residual=float(row['violation'])
 if not math.isfinite(magnitude) or magnitude<=0 or not math.isfinite(residual) or residual<0:raise ValueError('Invalid row values')
 limit=max(1e-3,1e-6*magnitude)
 return dict(name=row['name'],province_code=int(match[1]),family='province_annual_external_sent',unit='GWh',scope='8760 one-hour periods',row_magnitude_gwh=magnitude,residual_gwh=residual,relative_residual=residual/magnitude,tolerance_gwh=limit,ratio_to_tolerance=residual/limit,passed=residual<=limit,rule='AGENTS 2026-10-30 annual energy row: max(1e-3 GWh,1e-6*annual row energy)',equation='province_annual_external_sent_gwh = sum(outgoing forward GW and outgoing AC reverse GW)*1h',term_families={k:dict(count=len(v),coefficient_values=sorted(set(t['coefficient'] for t in v)),contribution=math.fsum(t['contribution'] for t in v)) for k,v in groups.items()})

def decide(profile,solve,family,cert):
 physical={k:v for k,v in profile['checks'].items() if k!='solver'}
 deferred=[k for k,v in physical.items() if v.get('passed') is None]
 physical_pass=all(v.get('passed') is True or (k=='reservoir_transition' and v.get('passed') is None and v.get('status')=='DEFERRED_BY_AUTHOR_20261012') for k,v in physical.items())
 metrics=solve['solution_contract']['barrier_primal_dual_metrics'];pinf=float(metrics['primal_infeasibility']);gap=float(metrics['relative_primal_dual_objective_gap']);ratio=float(cert['B_over_objective'])
 conditions=dict(physical_relative_checks=physical_pass,maximum_constraint_row_within_family_tolerance=family['passed'],own_BarPi_certificate=cert['scope']=='FULL_YEAR' and math.isfinite(ratio) and 0<=ratio<=1e-2,barrier_terminal_range_and_gap=solve['status']=='OPTIMAL' and math.isfinite(pinf) and 1e-2<pinf<=1e-1 and math.isfinite(gap) and 0<=gap<=1e-2)
 return conditions,deferred

def distributions(prices,selection,expected_count=6195):
 lookup={(r['grid_uid'],r['technology']):r for r in prices};keys=[(r['grid_uid'],r['technology']) for r in selection]
 if len(lookup)!=len(prices) or len(keys)!=len(set(keys)) or set(keys)!=set(lookup):raise ValueError('Selection/prices identity mismatch')
 excluded=[]
 for s in selection:
  if s['screened_out'].lower()!='true':continue
  r=lookup[(s['grid_uid'],s['technology'])];now=float(r['rc_ratio']);base=float(s['rc_ratio']);head=float(s['original_new_ub_gw'])
  if not all(math.isfinite(v) for v in [now,base,head]) or head<0:raise ValueError('Invalid price/headroom')
  excluded.append(dict(grid_uid=s['grid_uid'],technology=s['technology'],province_code=r['province_code'],original_new_ub_gw=head,base_rc_ratio=base,current_rc_ratio=now,delta_rc_ratio=now-base,improvement_bound_million_cny=head*max(-float(r['rc_build']),0)))
 if len(excluded)!=expected_count:raise ValueError(f'Excluded count drift: {len(excluded)} != {expected_count}')
 ratios=np.array([r['current_rc_ratio'] for r in excluded]);delta=np.array([r['delta_rc_ratio'] for r in excluded])
 summary=dict(excluded_columns=len(excluded),excluded_headroom_gw=math.fsum(r['original_new_ub_gw'] for r in excluded),minimum_rc_ratio=float(ratios.min()),negative_count=int((ratios<0).sum()),below_0p1_count=int((ratios<0.1).sum()),below_0p1_fraction=float((ratios<0.1).mean()),current_quantiles={str(q):float(np.quantile(ratios,q)) for q in [0,.05,.25,.5,.75,.95,1]},delta_definition='current Case3 2050 rc_ratio minus original Base screening rc_ratio, equal weight per excluded column',delta_median=float(np.median(delta)),delta_p05=float(np.quantile(delta,.05)),quantile_method='numpy default linear',B_recomputed_million_cny=math.fsum(r['improvement_bound_million_cny'] for r in excluded))
 return summary,excluded

def readcsv(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--release-root',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);ap.add_argument('--frozen-source',type=pathlib.Path,required=True);a=ap.parse_args()
 b=a.release_root;root=b/'output_8760';side=b/'postprocess_20261106';rowpath=b/'acceptance_20261106/archived_constraint_audit.json';pricing=side/'pricing'
 if a.output.exists() or a.output.resolve().is_relative_to(root.resolve()):raise ValueError('New independent sidecar required')
 backup=json.loads((b/'backup_manifest.json').read_text());assert backup['status']=='COMPLETE' and backup['source_unchanged_after_transfer']
 row=json.loads(rowpath.read_text());cert=json.loads((pricing/'screen_pricing_certificate.json').read_text());assess=json.loads((side/'solution_qc_relative_v1.json').read_text());solve=json.loads((root/'solve_report.json').read_text());checkpoint=json.loads((root/'barrier_checkpoint/barrier_checkpoint_manifest.json').read_text())
 result_sha=sha(root/'result_manifest.json');assert result_sha==backup['source_result_manifest_sha256']==row['source_result_manifest_sha256']
 assert cert['identity']['barpi_sha256']==checkpoint['vectors']['dual']['sha256']
 assert cert['identity']['mps_sha256']==row['source_files']['model_archive/original.mps.gz']['sha256']
 assert cert['identity']['checkpoint_manifest_sha256']==row['source_files']['barrier_checkpoint/barrier_checkpoint_manifest.json']['sha256']
 for n,record in row['source_files'].items():
  if n!='model_archive/original.mps.gz':assert sha(root/n)==record['sha256'],n
 assert cert['input_sha256'][str(root/'solve_report.json')]==sha(root/'solve_report.json')
 assert assess['source_sha256'][str(root/'solve_report.json')]==sha(root/'solve_report.json')
 assert row['index']==solve['solution_quality_locations']['maximum_constraint_violation']['index']==53400865
 agreement=abs(row['violation']-solve['solution_quality']['maximum_constraint_violation']);assert agreement<1e-7
 frozen=json.loads(a.frozen_source.read_text());repo_hashes=json.loads((b/'cloud_source_repo_sha256.json').read_text())
 # SHA must occur in the immutable release's source manifest, regardless of its JSON layout.
 for n,record in frozen.items():assert record['sha256'] in json.dumps(repo_hashes),n
 family=row_check(row);profile=assess['acceptance_profiles']['relative_v1'];conditions,deferred=decide(profile,solve,family,cert)
 dist,columns=distributions(readcsv(pricing/'vre_site_reduced_costs.csv'),readcsv(root/'candidate_selection.csv'))
 assert math.isclose(dist['B_recomputed_million_cny'],cert['B_million_cny'],rel_tol=1e-12,abs_tol=1e-8)
 metrics=solve['solution_contract']['barrier_primal_dual_metrics'];gap=float(metrics['absolute_primal_dual_objective_gap']);assert gap>0
 accepted=all(conditions.values())
 evidence_paths=[rowpath,pricing/'screen_pricing_certificate.json',side/'solution_qc_relative_v1.json',side/'assessment_evidence.json',b/'backup_manifest.json',a.frozen_source]
 decision=dict(status='PASS' if accepted else 'STOP_AUTHOR_CONDITION_NOT_MET',author_decision='ACCEPTED_RELATIVE_V1_20261106' if accepted else 'NOT_ADOPTED_CONDITIONS_UNMET',conditions=conditions,row=family,reconstruction_difference=agreement,physical_deferred=deferred,barrier_primal_infeasibility=metrics['primal_infeasibility'],barrier_primal_infeasibility_disclosure_only=accepted,certificate={k:cert[k] for k in ['B_million_cny','B_over_objective','excluded_columns','near_optimality_decision','scope']},comparison=dict(original_P_minus_D_million_cny=gap,original_gap_yi_cny=gap/100,B_to_original_gap=cert['B_million_cny']/gap,automatic_resolve=False,author_decision_required=cert['B_over_objective']>1e-4,legacy_certificate_label=cert['base_comparison_decision'],rule='AGENTS 2026-11-06 supersedes automatic comparison re-solve'),rc_ratio_distribution=dist,case3_2060_margin=0.3 if cert['B_over_objective']>5e-4 else 0.2,source_evidence=dict(source_sha256={'result_manifest.json':result_sha,**{n:r['sha256'] for n,r in row['source_files'].items()}}),evidence_sha256={str(p):sha(p) for p in evidence_paths},source_archives_modified=False)
 a.output.mkdir(parents=True)
 save(a.output/'acceptance_author_20261106.json',decision);save(a.output/'excluded_rc_ratio_distribution.json',dist)
 with (a.output/'excluded_rc_ratio_columns.csv').open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(columns[0]));wr.writeheader();wr.writerows(columns)
 revised=copy.deepcopy(assess);rp=revised['acceptance_profiles']['relative_v1'];rp['baseline_status']=rp['status'];rp['baseline_solver_check']=copy.deepcopy(rp['checks']['solver']);rp['author_decision_reference']='AGENTS.md 2026-11-06';rp['conditional_evidence_sha256']=sha(a.output/'acceptance_author_20261106.json')
 if accepted:
  rp['checks']['solver'].update(passed=True,classification='CONDITIONAL_DISCLOSURE_AUTHOR_20261106',primal_infeasibility_disclosure_only=True,conditions=conditions);rp['status']='PASS'
 save(a.output/'solution_qc_relative_v1_author_20261106.json',revised)
 print(json.dumps(dict(status=decision['status'],row=family,certificate=decision['certificate'],comparison=decision['comparison'],distribution=dist,case3_2060_margin=decision['case3_2060_margin']),ensure_ascii=False))
if __name__=='__main__':main()
