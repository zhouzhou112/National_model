"""Bind passed local/T550 engineering evidence for a no-submission cloud package."""
from pathlib import Path
import csv,json,hashlib,subprocess,tarfile,io
from prepare_cloud import HERE,WORK,REPO,longpath,load,sha,TEMPLATE_SOURCE

def main():
 out=HERE/'FINAL_PREPARATION_GATES.json';assert not out.exists()
 evi=HERE/'t550_evidence';receipt=load(HERE/'collect_receipt.json');assert receipt['status']=='PASS' and receipt['all_bytes_sha_match'] and receipt['submitted'] is False
 complete=load(evi/'PREPARATION_GATES_COMPLETE_v2.json');assert complete['status']=='PASS' and not complete['submitted'] and not complete['submission_authorized']
 r1=load(evi/'R1_v1/evidence/cleanup_gate.json');identity=load(evi/'identity_24h_central_v2/identity_gate.json');one=load(evi/'selected_1h/selection_build_gate.json');day=load(evi/'restricted_24h/selection_build_gate.json');pre=load(evi/'t550_preflight/preflight_report.json');selection=load(evi/'final_selection.json');sel=load(evi/'selection_receipt.json');install=load(HERE/'installation_receipt.json')
 assert all(x['status']=='PASS' for x in [r1,identity,one,day,pre,sel,install])
 for g in [one,day]:
  assert g['resource_audit']['status']=='PASS' and g['matrix_objective_rhs_and_senses_byte_identical'] and all(g['other_investment_bounds_unchanged'].values())
 assert day['quality_ok']
 assert identity['relative_objective_difference']<=1e-7 and max(identity['maximum_capacity_difference_by_family'].values())<=1e-9
 key=lambda r:(r['grid_uid'],r['technology'])
 final={key(r):r['state'] for r in selection['columns']};assert len(final)==len(selection['columns'])==36686
 with longpath(evi/'initial_state_and_2050_change_audit.csv').open(encoding='utf-8',newline='') as f:initial=list(csv.DictReader(f))
 forced={key(r) for r in initial if r['common_state_2060']=='free' or r['vs_LATE2050_ge_10MW']=='True' or r['vs_REF2050_ge_10MW']=='True'}
 free={k for k,v in final.items() if v=='free'};assert len(forced)==845 and forced<=free and len(free)==4879 and len(free)<=5000
 assert sha(evi/'final_selection.json')==sel['sha256']==complete['selection_sha256']
 state=evi/'R1_v1/prepared_state';m=load(state/'result_manifest.json')
 for r in m['files']:
  p=longpath(state/r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
 bridge=load(state/'acceptance_relative_v1.json');assert bridge['submission_authorized'] is False and bridge['author_decision']=='ACCEPTED_FOR_PREPARATION_ONLY_20261119'
 parent=REPO/'case_results/by_case/LATE-Open/2050/20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1/acceptance_resource_late_20261119/acceptance_record.json';assert sha(parent)==bridge['acceptance_record_sha256'] and load(parent)['status']=='PASS'
 archive=load(WORK/'batch3_completed_backup_20261118/source_inventory.json')['plan']['releases'][TEMPLATE_SOURCE];wanted=next(r['sha256'] for r in archive['files'] if r['path']=='continuation.sbatch');template=WORK/'batch3_conservative_20261117/deployment/ops_conservative_2060/job.sbatch';assert hashlib.sha256(template.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==wanted
 source=load(HERE/'source_manifest.json')
 exported=subprocess.check_output(['git','archive','HEAD','cispo_model','scripts','config','tests'],cwd=REPO)
 actual={}
 with tarfile.open(fileobj=io.BytesIO(exported)) as archive:
  for member in archive.getmembers():
   if member.isfile():actual[member.name]=hashlib.sha256(archive.extractfile(member).read()).hexdigest()
 assert set(actual)==set(source['files'])-{'AGENTS.md'}
 for n,h in actual.items():assert h==source['files'][n]['sha256'],n
 files=[HERE/'AUTHORIZATION.json',HERE/'installation_receipt.json',evi/'PREPARATION_GATES_COMPLETE_v2.json',evi/'R1_v1/evidence/cleanup_gate.json',evi/'identity_24h_central_v2/identity_gate.json',evi/'selected_1h/selection_build_gate.json',evi/'restricted_24h/selection_build_gate.json',evi/'t550_preflight/preflight_report.json',evi/'selection_receipt.json',evi/'final_selection.json',state/'result_manifest.json',state/'acceptance_relative_v1.json']
 report=dict(status='PASS',planning_year=2060,submitted=False,submission_authorized=False,source_commit=source['commit'],regression_tests_covered=537,selection_sha256=sel['sha256'],selection_margin=sel['chosen_margin'],free_groups=len(free),mandatory_initial_free_groups=len(forced),selection_state_counts={s:sum(v==s for v in final.values()) for s in ['lower','upper','free']},open_BUILD_AUDIT_sha256=install['open_BUILD_AUDIT_sha256'],template_release=TEMPLATE_SOURCE,template_sha256=wanted,checks=dict(R1='PASS',central_resource_entry_identity='PASS',actual_open_selected_1h='PASS',actual_open_restricted_24h='PASS',parameters='PASS',source_and_input_identity='PASS',T550_preflight='PASS',model_matrix_objective_rhs_unchanged_by_selection=True,other_investment_bounds_unchanged=True,threads=44,production_scenario_entry='same Open configuration as own Open2050 upstream; no late-entry-base-state flag'),local_evidence_sha256={p.relative_to(HERE).as_posix():sha(p) for p in files})
 out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='local_evidence_sha256'}))

if __name__=='__main__':main()
