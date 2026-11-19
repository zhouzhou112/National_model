"""Combine verified compact summaries on T550; no hourly arrays or solver calls."""
from pathlib import Path
import json,csv,hashlib,argparse
from metrics_flex import Inputs,sha,save

BASE=Path('/home/zz2/National_model_server/cloud_backup')
OUT=Path('/home/zz2/National_model_server/resource_comparison_20261119')
REF={2030:'20260914_base_v9_t48_m750_tol1e4_v3',2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',2050:'20260930_base2050_v9_t48_m750_tol1e4_v1',2060:'20261012_base2060_v9a12_t48_m750_tol1e4_v1'}
CENTRAL={2030:'20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3',2040:'20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1',2050:'20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1',2060:'20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2'}

def table(name,rows):
 with (OUT/name).open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)

def objective(release):
 inp=Inputs(release);s=json.loads(inp.path('solve_report.json').read_text());m=s['solution_contract']['barrier_primal_dual_metrics'];return float(m['primal_objective']),float(m['dual_objective']),inp.checked

def main():
 assert not OUT.exists();OUT.mkdir();rows=[];services=[];sources={};pairs=[]
 for year in (2030,2040,2050,2060):
  refP,refD,refsrc=objective(REF[year]);centralP,centralD,centralsrc=objective(CENTRAL[year]);sources[str(year)]={'REF':refsrc,'OPS-Central':centralsrc}
  results={}
  for resource in ('Open','Conservative'):
   if year==2050:
    release='20261115_'+('opsopen' if resource=='Open' else 'opscons')+'_2050_v9a12_t44_m750_tol1e4_v1';side='acceptance_resource_batch1_20261115'
   else:
    release=('20261115_opsopen_' if resource=='Open' else '20261117_opsconservative_')+str(year)+('_v9_' if year==2030 else '_v9a12_')+'t44_m750_tol1e4_v1';side='acceptance_resource_batch2_20261116' if resource=='Open' else 'acceptance_resource_batch3_20261119'
   root=BASE/release/side;analysis=json.loads((root/'analysis/analysis_summary.json').read_text());accept=json.loads((root/'acceptance_record.json').read_text());assert accept['status']==analysis['status']=='PASS'
   P,D,provenance=objective(release);assert P==analysis['P_million_cny'] and D==analysis['D_million_cny']
   r=dict(case='OPS-'+resource,year=year,P_million_cny=P,D_million_cny=D,ref_point_saving_yi_cny=(refP-P)/100,ref_lower_saving_yi_cny=(refD-P)/100,ref_upper_saving_yi_cny=(refP-D)/100,central_point_saving_yi_cny=(centralP-P)/100,central_lower_saving_yi_cny=(centralD-P)/100,central_upper_saving_yi_cny=(centralP-D)/100,acceptance='PASS',reused_prior_acceptance=year==2050 or resource=='Open');rows.append(r);results[resource]=r
   for service in analysis['services']:services.append(dict(case='OPS-'+resource,year=year,**service))
   sources[str(year)][resource]=dict(original_files=provenance,acceptance_sha256=sha(root/'acceptance_record.json'),analysis_sha256=sha(root/'analysis/analysis_summary.json'))
  op=results['Open'];co=results['Conservative'];pairs.append(dict(year=year,open_vs_conservative_point_yi_cny=(co['P_million_cny']-op['P_million_cny'])/100,lower_yi_cny=(co['D_million_cny']-op['P_million_cny'])/100,upper_yi_cny=(co['P_million_cny']-op['D_million_cny'])/100))
 table('OPS_resources_four_year_costs.csv',rows);table('OPS_resources_four_year_services.csv',services);table('Open_vs_Conservative_intervals.csv',pairs)
 save(OUT/'OPS_resources_four_year_summary.json',dict(status='PASS',computed_on='T550',rows=rows,services=services,pairs=pairs,source_identity=sources,interpretation='Cost intervals are engineering dual intervals, not statistical CI; no capacity investment response in OPS; do not interpret resource-scenario co-movement as a single-parameter causal effect'))
 save(OUT/'manifest.json',{p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in OUT.iterdir() if p.is_file()})
 print(json.dumps(dict(status='PASS',output=str(OUT),rows=len(rows))),flush=True)

def compare_late():
 assert OUT.exists() and not (OUT/'LATE_Open_vs_central.json').exists()
 previous=json.loads((OUT/'manifest.json').read_text())
 for n,r in previous.items():assert (OUT/n).stat().st_size==r['bytes'] and sha(OUT/n)==r['sha256']
 late=BASE/'20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1/acceptance_resource_late_20261119';a=json.loads((late/'acceptance_record.json').read_text());assert a['status']=='PASS'
 cref='20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2';cp=BASE/cref/'postprocess_20261027_mt/pricing/screen_pricing_certificate.json';assert sha(cp)=='b1ce3af43db2179aa4f1f901cc2beaaf1da50ebc2bbcf3cff43448368b959c15'
 certificate=json.loads(cp.read_text());C,D,provenance=objective(cref);assert certificate['identity']['semantic_manifest']['sha256']==provenance['result_manifest.json']['sha256']
 CB=float(certificate['B_million_cny']);P=a['P_million_cny'];T=a['D_million_cny'];B=a['screening_B_million_cny']
 comparison=dict(status='PASS',reference='LATE-Central2050',target='LATE-Open2050',reference_P_million_cny=C,reference_D_million_cny=D,reference_B_million_cny=CB,target_P_million_cny=P,target_D_million_cny=T,target_B_million_cny=B,point_saving_yi_cny=(C-P)/100,lower_saving_yi_cny=(D-CB-P)/100,upper_saving_yi_cny=(C-T+B)/100,formula='[D_reference-B_reference-P_target, P_reference-D_target+B_target]',reference_certificate_sha256=sha(cp),target_acceptance_sha256=sha(late/'acceptance_record.json'),source_identity=provenance,meaning='Same REF2040 upstream; own resource inputs and restricted sets differ, both certificate bounds retained')
 save(OUT/'LATE_Open_vs_central.json',comparison)
 save(OUT/'late_manifest.json',{'LATE_Open_vs_central.json':dict(bytes=(OUT/'LATE_Open_vs_central.json').stat().st_size,sha256=sha(OUT/'LATE_Open_vs_central.json'))})
 print(json.dumps(comparison),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['ops','late']);a=ap.parse_args()
 if a.phase=='ops':main()
 else:compare_late()
