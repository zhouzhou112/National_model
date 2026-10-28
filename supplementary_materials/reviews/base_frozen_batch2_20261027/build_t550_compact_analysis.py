"""T550-only descriptive analysis and bounded delivery; immutable source backups.

Usage: --backup-root PATH --output PATH (new directory).
All result computations stay on T550. No solving, source mutation, or monitoring.
"""
from pathlib import Path
import argparse,csv,hashlib,json,shutil,socket,datetime,tarfile

BASE={2030:'20260914_base_v9_t48_m750_tol1e4_v3',2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',2050:'20260930_base2050_v9_t48_m750_tol1e4_v1',2060:'20261012_base2060_v9a12_t48_m750_tol1e4_v1'}
B={2030:'20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3',2040:'20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1',2050:'20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1',2060:'20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2'}
OTHER=[('Case3',2030,'20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1'),('Case3',2040,'20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2'),('nocredit',2030,'20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1')]
SMALL=['annual_summary.json','annual_carbon_ccs.json','annual_capacity_by_technology.csv','annual_capacity_by_province_technology.csv','annual_generation_by_technology.csv','annual_generation_by_province_technology.csv','annual_flexible_load_by_province.csv','annual_resource_accounting_by_province.csv','annual_adequacy_by_province.csv','cost_components.csv','monthly_energy_by_technology.csv','storage_capacity.csv','thermal_nuclear_capacity.csv','transmission_capacity.csv','frozen_capacity_closure_audit.csv','frozen_capacity_closure_report.json','frozen_capacity_output_check.json','frozen_capacity_source_alignment.json','solve_report.json','solution_qc.json','preservation_report.json','result_manifest.json','run_identity.json','model_config_snapshot.json','output_catalog.csv','output_data_dictionary.csv']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
 return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def table(p,rows):
 if not rows:return
 keys=list(dict.fromkeys(k for row in rows for k in row));p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--backup-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
 assert socket.gethostname().split('.')[0]=='t550';assert not a.output.exists();a.output.mkdir(parents=True)
 evidence={};summaries=[];capacities=[];generation=[];costs=[];flex=[];summary_map={};copied=[];omitted=[]
 cases=[('Base',y,r) for y,r in BASE.items()]+[('B',y,r) for y,r in B.items()]+OTHER
 for case,year,release in cases:
  root=a.backup_root/release;out=root/'output_8760';backup=js(root/'backup_manifest.json');assert backup['status']=='COMPLETE'
  source_sha=sha(out/'result_manifest.json');assert source_sha==backup['source_result_manifest_sha256']
  entries={x['path']:x for x in js(out/'result_manifest.json')['files']};used={}
  def verify(name):
   p=out/name;assert name in entries and p.stat().st_size==entries[name]['bytes'] and sha(p)==entries[name]['sha256'],str(p)
   used[name]=dict(bytes=p.stat().st_size,sha256=entries[name]['sha256']);return p
  def rows(name):
   p=verify(name)
   with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
  solve=js(verify('solve_report.json'));metrics=solve['solution_contract'].get('barrier_primal_dual_metrics',{})
  row=dict(case=case,year=year,release=release,solver_status=solve['status'],iterations=solve['iteration_counts']['barrier'],solver_hours=solve['runtime_seconds']/3600,peak_process_tree_rss_gib=solve.get('runtime_memory',{}).get('peak_process_tree_rss_gib'),objective_million_cny=solve['objective_value_million_cny'],dual_objective_million_cny=metrics.get('dual_objective'),original_qc_status=solve.get('solution_qc_status'))
  annual=js(verify('annual_summary.json'));row['annual_summary']=annual
  side=root/'postprocess_20261027_mt/solution_qc_relative_v1.json'
  row['current_relative_v1_status']=js(side)['acceptance_profiles']['relative_v1']['status'] if side.exists() else 'SEE_EXISTING_ACCEPTANCE_RECORD'
  cr=rows('cost_components.csv');primary=[x for x in cr if x.get('included_in_primary_cost',x.get('included_directly_in_objective','')).lower()=='true']
  summed=sum(float(x['value_million_cny_per_year']) for x in primary)
  row['primary_cost_sum_million_cny']=summed;row['cost_sum_minus_objective_million_cny']=summed-row['objective_million_cny']
  assert abs(summed-row['objective_million_cny']) <= max(1e-3,1e-8*abs(row['objective_million_cny'])),release
  for name,target in [('annual_capacity_by_technology.csv',capacities),('annual_generation_by_technology.csv',generation),('cost_components.csv',costs)]:
   target.extend(dict(case=case,year=year,**x) for x in rows(name))
  if (out/'annual_flexible_load_by_province.csv').exists():
   fr=rows('annual_flexible_load_by_province.csv');keys=[k for k in fr[0] if k.startswith('contracted_') or k.startswith('firm_') or k in ['heating_shift_up_gwh','heating_shift_down_gwh','cooling_shift_up_gwh','cooling_shift_down_gwh','ev_mobility_v1g_relocated_gwh','ev_v2g_discharge_gwh','net_load_energy_change_gwh']]
   flex.append(dict(case=case,year=year,**{k:sum(float(x[k]) for x in fr) for k in keys}))
  summaries.append(row);summary_map[case,year]=row
  if case=='B' and year>=2040:
   for name in SMALL:
    p=verify(name) if name!='result_manifest.json' else out/name
    assert p.stat().st_size<=1024**2,name
    dest=a.output/'cases'/case/str(year)/release/'small_results'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    copied.append(dict(path=dest.relative_to(a.output).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
   for name in ['assessment_inputs.json','solution_qc_relative_v1.json','assessment_evidence.json']:
    p=side.parent/name;assert p.stat().st_size<=1024**2
    dest=a.output/'cases'/case/str(year)/release/'acceptance'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    copied.append(dict(path=dest.relative_to(a.output).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
   bm=a.output/'cases'/case/str(year)/release/'backup_manifest.json';shutil.copyfile(root/'backup_manifest.json',bm)
   omitted.extend(dict(case=case,year=year,path=x['path'],bytes=x['bytes'],reason='REMOTE_ONLY_BY_EXPLICIT_COMPACT_ALLOWLIST') for x in entries.values() if x['path'] not in SMALL)
  assert sha(out/'result_manifest.json')==source_sha
  for name,meta in used.items():assert sha(out/name)==meta['sha256']
  evidence[release]=dict(source_result_manifest_sha256=source_sha,backup_manifest_sha256=sha(root/'backup_manifest.json'),files=used,source_unchanged=True)
 comparisons=[]
 for year in B:
  base,other=summary_map['Base',year],summary_map['B',year];pb,px=base['objective_million_cny'],other['objective_million_cny'];db,dx=base['dual_objective_million_cny'],other['dual_objective_million_cny']
  comparisons.append(dict(year=year,base_objective_million_cny=pb,B_objective_million_cny=px,point_saving_million_cny=pb-px,lower_saving_million_cny=None if db is None else db-px,upper_saving_million_cny=None if dx is None else pb-dx,screening_bound_million_cny=0,comparison_status='ENGINEERING_BARRIER_INTERVAL_UNSCREENED_B',limitation='B uses Base plus documented static closure; interval is descriptive under author convention, not a proof of exact nested feasible sets.'))
 write(a.output/'analysis/run_summaries.json',summaries);table(a.output/'analysis/run_summary.csv',[{k:v for k,v in x.items() if k!='annual_summary'} for x in summaries]);table(a.output/'analysis/B_vs_Base_cost_interval.csv',comparisons)
 table(a.output/'analysis/national_capacity.csv',capacities);table(a.output/'analysis/national_generation.csv',generation);table(a.output/'analysis/cost_components.csv',costs);table(a.output/'analysis/flexible_contracts.csv',flex)
 write(a.output/'source_verification.json',evidence);write(a.output/'copied_files.json',copied);write(a.output/'remote_only_files.json',omitted)
 write(a.output/'analysis/execution.json',dict(host=socket.gethostname(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_sha256=sha(Path(__file__)),source_root=str(a.backup_root),cases=len(cases),no_source_writes=True,analysis_executed_on_t550=True))
 files=[dict(path=p.relative_to(a.output).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(a.output.rglob('*')) if p.is_file()]
 total=sum(x['bytes'] for x in files);assert total<12*1024**2,(total,'Delivery too large')
 assert max(x['bytes'] for x in files)<1024**2
 write(a.output/'delivery_manifest.json',dict(status='READY',total_bytes=total,files=files,max_file_bytes=1024**2,max_total_bytes=12*1024**2,source_computation='T550',includes_hourly_arrays=False,includes_original_models=False))
 bundle=a.output.with_suffix('.tar.gz');assert not bundle.exists()
 with tarfile.open(bundle,'w:gz') as tar:
  for p in sorted(a.output.rglob('*')):
   if p.is_file():tar.add(p,arcname=p.relative_to(a.output).as_posix())
 print(json.dumps(dict(status='READY',output=str(a.output),bundle=str(bundle),bundle_bytes=bundle.stat().st_size,bundle_sha256=sha(bundle),total_bytes=total,files=len(files),comparisons=comparisons)))
if __name__=='__main__':main()
