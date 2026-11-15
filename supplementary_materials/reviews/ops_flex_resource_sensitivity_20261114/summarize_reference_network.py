"""T550-only compact REF/central-OPS/network comparison, source-hash checked."""
from pathlib import Path
import argparse,json,sys
import pandas as pd
sys.path.insert(0,'/home/zz2/National_model_server/analysis_tools_resource_batch1_20261115')
from metrics_flex import Inputs,sha,SERVICES
REFS={'REF':'20260930_base2050_v9_t48_m750_tol1e4_v1',
 'OPS-Central':'20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1',
 'OPS-Open':'20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1',
 'OPS-Conservative':'20261115_opscons_2050_v9a12_agg0_t44_m750_tol1e4_v1',
 'D1-C5':'20261115_C5_intra_2050_v9a12_t44_m750_tol1e4_v1'}
# The resource release is not named with agg0, although its profile uses it.
REFS['OPS-Conservative']='20261115_opscons_2050_v9a12_t44_m750_tol1e4_v1'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline-annual-sha',required=True);a=ap.parse_args()
 base=Path('/home/zz2/National_model_server/cloud_backup');oldrows=Path('/home/zz2/National_model_server/analysis_tools_20261020/b2050/annual_row_duals.csv');assert sha(oldrows)==a.baseline_annual_sha
 identity=json.loads((oldrows.parent/'input_identity.json').read_text());order=json.loads((oldrows.parent/'row_order_verification.json').read_text());assert identity['status']==order['status']=='PASS'
 result={};tables=[]
 for name,rel in REFS.items():
  inp=Inputs(rel);s=json.loads(inp.path('solve_report.json').read_text());m=s['solution_contract']['barrier_primal_dual_metrics'];annual=json.loads(inp.path('annual_summary.json').read_text());network=pd.read_csv(inp.path('load_center_intra_transmission.csv'))
  r=dict(P_million_cny=m['primal_objective'],D_million_cny=m['dual_objective'],vre_curtailment_gwh=annual['vre_curtailment_gwh'],storage_charge_gwh=annual['storage_charge_gwh'],storage_discharge_gwh=annual['storage_discharge_gwh'],intra_new_sum_gw=float(network.new_capacity_gw.sum()),intra_capacity_sum_gw=float(network.capacity_gw.sum()))
  if name!='REF':
   f=pd.read_csv(inp.path('annual_flexible_load_by_province.csv'));r['contracted_gw']={service:float(f['contracted_'+service+'_flexibility_gw'].sum()) for service in SERVICES};r['v2g_discharge_gwh']=float(f.ev_v2g_discharge_gwh.sum())
  if name=='OPS-Central':
   checkpoint=json.loads(inp.path('barrier_checkpoint/barrier_checkpoint_manifest.json').read_text());assert checkpoint['vectors']['dual']['sha256']==identity['inputs']['barrier_checkpoint/dual_barpi.npy']['sha256'];path=oldrows
  elif name in ['OPS-Open','OPS-Conservative','D1-C5']:path=base/rel/'acceptance_resource_batch1_20261115/annual_rows/annual_row_duals.csv'
  else:path=None
  if path:
   d=pd.read_csv(path);z=d[d.row_family=='intra_load_center_annual_capacity'];assert len(z)==642 and (z.row_sense=='L').all();values=-1000*z.pi_million_cny_per_gwh
   r['intra_annual_capacity_value_cny_per_mwh']=dict(mean=float(values.mean()),median=float(values.median()),p95=float(values.quantile(.95)),minimum=float(values.min()),maximum=float(values.max()),rows=642,raw_sign_preserved=True);r['annual_row_duals_sha256']=sha(path)
  r['source_files']=inp.checked;result[name]=r;tables.append(dict(case=name,**{k:v for k,v in r.items() if isinstance(v,(float,int))}))
 remote=Path('/home/zz2/National_model_server/analysis_tools_resource_batch1_20261115/batch_summary');remote.mkdir(exist_ok=False)
 (remote/'reference_and_network_summary.json').write_text(json.dumps(result,indent=2)+'\n');pd.DataFrame(tables).to_csv(remote/'batch_comparison_summary.csv',index=False);print(json.dumps(result))
if __name__=='__main__':main()
