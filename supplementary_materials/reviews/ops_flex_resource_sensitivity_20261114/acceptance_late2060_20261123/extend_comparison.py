"""Read-only compact certificate diagnostics and C2060 comparison on T550."""
from pathlib import Path
import json,csv,math
from prepare_acceptance import BASE,RELEASE,SIDE,sha,save
from metrics_flex import Inputs

def main():
 side=BASE/RELEASE/SIDE;a=json.loads((side/'acceptance_record.json').read_text());assert a['status']=='PASS'
 out=side/'comparisons';assert not out.exists();out.mkdir()
 with (side/'pricing/boundary_directional_prices.csv').open(newline='') as f:prices=list(csv.DictReader(f))
 negative=zero=positive=0;groups={}
 for r in prices:
  if r['state']=='free':continue
  rc=float(r['increase_rc_ratio' if r['state']=='lower' else 'decrease_rc_ratio']);bound=float(r['improvement_bound_million_cny'])
  if rc<0:
   negative+=1
   if float(r['capacity_upper_gw'])==float(r['capacity_floor_gw']):zero+=1
  if bound>0:
   positive+=1;key=(int(r['province_code']),r['technology'],r['state']);g=groups.setdefault(key,dict(province_code=key[0],technology=key[1],state=key[2],positive_improvement_groups=0,B_million_cny=0.));g['positive_improvement_groups']+=1;g['B_million_cny']+=bound
 assert positive==a['certificate']['negative_fixed_sites'] and math.isclose(sum(g['B_million_cny'] for g in groups.values()),a['screening_B_million_cny'],rel_tol=1e-12)
 with (out/'directional_B_by_province_technology.csv').open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=['province_code','technology','state','positive_improvement_groups','B_million_cny']);wr.writeheader();wr.writerows(sorted(groups.values(),key=lambda r:-r['B_million_cny']))
 save(out/'directional_B_summary.json',dict(status='PASS',negative_direction_groups=negative,negative_direction_zero_original_range=zero,positive_improvement_groups=positive,B_million_cny=a['screening_B_million_cny'],province_codes=sorted(set(k[0] for k in groups)),province_count=len(set(k[0] for k in groups)),source_prices_sha256=sha(side/'pricing/boundary_directional_prices.csv')))
 ref='20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1';inp=Inputs(ref);solve=json.loads(inp.path('solve_report.json').read_text());m=solve['solution_contract']['barrier_primal_dual_metrics'];cp=BASE/ref/'postprocess_20261108/pricing/screen_pricing_certificate.json'
 assert sha(cp)=='72ee281b247fb4ecdcd5bcbce3493b33b5c16f0a0e23c2ce934a9efa7ac39233'
 cert=json.loads(cp.read_text());assert cert['identity']['semantic_manifest']['sha256']==inp.checked['result_manifest.json']['sha256']
 refP=float(m['primal_objective']);refD=float(m['dual_objective']);refB=float(cert['B_million_cny']);P=a['P_million_cny'];D=a['D_million_cny'];B=a['screening_B_million_cny']
 result=dict(status='PASS',reference='LATE-Central2060',target='LATE-Open2060',reference_P_million_cny=refP,reference_D_million_cny=refD,reference_B_million_cny=refB,target_P_million_cny=P,target_D_million_cny=D,target_B_million_cny=B,point_saving_yi_cny=(refP-P)/100,lower_saving_yi_cny=(refD-refB-P)/100,upper_saving_yi_cny=(refP-D+B)/100,formula='[D_reference-B_reference-P_target, P_reference-D_target+B_target]',reference_certificate_sha256=sha(cp),target_acceptance_sha256=sha(side/'acceptance_record.json'),source_identity=inp.checked,interpretation='Engineering intervals conditional on each inherited state; not a certificate for the whole intertemporal pathway; resource inputs and inherited states differ')
 save(out/'LATE_Open_vs_central.json',result)
 save(out/'manifest.json',{p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in out.iterdir() if p.is_file()})
 print(json.dumps(dict(status='PASS',negative_direction_groups=negative,zero_range_negative_groups=zero,positive_improvement_groups=positive,province_count=len(set(k[0] for k in groups)),central_comparison=result)),flush=True)

if __name__=='__main__':main()
