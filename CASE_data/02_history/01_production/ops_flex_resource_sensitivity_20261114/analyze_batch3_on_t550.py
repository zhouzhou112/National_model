"""Small derived tables from immutable T550 outputs; no solver/model changes."""
from pathlib import Path
import argparse,json,time
import numpy as np
import pandas as pd
from metrics_flex import Inputs,service_deviations,price_arrays,sha,save,SERVICES
from accept_batch3_on_t550 import CASES,BASE
DATA=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/baseline_runtime/data_roots/neutral')
REFS={2030: {'REF': '20260914_base_v9_t48_m750_tol1e4_v3', 'OPS-Central': '20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3'}, 2040: {'REF': '20260919_base2040_v9_t44_m750_tol1e4_v1', 'OPS-Central': '20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1'}, 2060: {'REF': '20261012_base2060_v9a12_t48_m750_tol1e4_v1', 'OPS-Central': '20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2'}}
def table(out,name,data):data.to_csv(out/name,index=False,compression='gzip' if name.endswith('.gz') else None)
def load_reference(label,release):
 inp=Inputs(release);s=json.loads(inp.path('solve_report.json').read_text());m=s['solution_contract']['barrier_primal_dual_metrics']
 a=json.loads(inp.path('annual_summary.json').read_text());cost=pd.read_csv(inp.path('cost_components.csv'))
 return dict(label=label,P=float(m['primal_objective']),D=float(m['dual_objective']),annual=a,cost=cost,inputs=inp.checked)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('case',choices=CASES);a=ap.parse_args();started=time.time()
 inp=Inputs(CASES[a.case]);side=BASE/CASES[a.case]/'acceptance_resource_batch3_20261119'
 assert json.loads((side/'ACCEPTANCE_AND_ROWS_COMPLETE.json').read_text())['status']=='PASS'
 out=side/'analysis';out.mkdir(exist_ok=False)
 config=json.loads(inp.path('model_config_snapshot.json').read_text())['resolved_configuration'];year=int(config['planning_year']);assert year==int(a.case.rsplit('-',1)[-1]);annual=json.loads(inp.path('annual_summary.json').read_text());solve=json.loads(inp.path('solve_report.json').read_text())
 f=np.load(inp.path('flexible_load_dispatch.npz'),allow_pickle=False);p=f['province_codes'].astype(int);h=f['hour_index'].astype(int)
 assert len(p)==31 and np.array_equal(h,np.arange(8760));assert list(f['flexible_service_names'])==list(SERVICES)
 frac=float(config['flexible_load']['ev_v1g']['shiftable_energy_fraction']);delta=service_deviations(f,frac)
 closure=float(np.max(np.abs(delta.sum(axis=1)-(f['effective_total_load_gw']-f['baseline_total_load_gw']))));assert closure<=1e-6
 contract=f['flexible_service_capacity_gw'];a_csv=pd.read_csv(inp.path('annual_flexible_load_by_province.csv')).set_index('province_code').loc[p]
 np.testing.assert_allclose(contract,a_csv[[f'contracted_{s}_flexibility_gw' for s in SERVICES]],atol=1e-9,rtol=0)
 struct=json.loads(inp.path('resource_structure_audit.json').read_text());lookup={r['province_code']:r['values_gw'] for r in struct['province_upper_gw']};upper=np.asarray([lookup[int(x)] for x in p]);assert np.all(contract<=upper+1e-8)
 down=np.maximum(-delta,0).sum(axis=2);up=np.maximum(delta,0).sum(axis=2);rows=[]
 for i,prov in enumerate(p):
  for j,s in enumerate(SERVICES):rows.append(dict(province_code=int(prov),service=s,contract_gw=float(contract[i,j]),upper_gw=float(upper[i,j]),contract_share_of_upper=float(contract[i,j]/upper[i,j]) if upper[i,j]>0 else None,down_regulation_gwh=float(down[i,j]),up_regulation_gwh=float(up[i,j]),net_load_change_gwh=float(up[i,j]-down[i,j]),equivalent_down_hours=float(down[i,j]/contract[i,j]) if contract[i,j]>1e-10 else None))
 provincial=pd.DataFrame(rows);table(out,'services_by_province.csv',provincial)
 national=provincial.groupby('service',sort=False)[['contract_gw','upper_gw','down_regulation_gwh','up_regulation_gwh','net_load_change_gwh']].sum().reindex(SERVICES).reset_index();national['contract_share_of_upper']=national.contract_gw/national.upper_gw;national['equivalent_down_hours']=national.down_regulation_gwh/national.contract_gw.replace(0,np.nan);table(out,'services_national.csv',national)
 ad=side/'annual_rows/annual_row_duals.csv';energy,reserve,inertia,dates,price_meta=price_arrays(inp,ad,sha(ad),p,h,config)
 prices=pd.DataFrame(dict(province_code=np.repeat(p,8760),hour_index=np.tile(h,31),datetime_bj=np.tile(dates,31),energy_price_cny_per_mwh=energy.ravel(),reserve_component_cny_per_mwh=reserve.ravel(),inertia_component_cny_per_mwh=inertia.ravel(),load_marginal_price_cny_per_mwh=(energy+reserve+inertia).ravel()))
 table(out,'hourly_province_load_marginal_prices.csv.gz',prices)
 frames=[];keys=['baseline_total_load_gw','effective_total_load_gw','baseline_heating_gw','actual_heating_gw','baseline_cooling_gw','actual_cooling_gw','baseline_ev_gw','actual_ev_gw','ev_v2g_discharge_gw']
 arrays={k:f[k] for k in keys}
 for prov in [0,44,32,37,51,15]:
  ix=None if prov==0 else list(p).index(prov);row=dict(province_code=np.full(8760,prov),hour_index=h,datetime_bj=dates)
  for k,v in arrays.items():row[k]=v.sum(axis=0) if prov==0 else v[ix]
  for j,s in enumerate(SERVICES):row[s+'_net_load_deviation_gw']=delta[:,j,:].sum(axis=0) if prov==0 else delta[ix,j]
  row['actual_ev_net_load_gw']=row['actual_ev_gw']-row['ev_v2g_discharge_gw'];frames.append(pd.DataFrame(row))
 table(out,'hourly_dispatch_national_and_five_provinces.csv.gz',pd.concat(frames,ignore_index=True))
 vre=np.load(inp.path('vre_dispatch.npz'),allow_pickle=False);vg=vre['generation_gw'];va=vre['available_gw'];tech=vre['technologies'].astype(str)
 assert np.array_equal(vre['province_codes'],p);vrows=[]
 for i,prov in enumerate(p):
  for j,t in enumerate(tech):vrows.append(dict(province_code=int(prov),technology=t,generation_gwh=float(vg[i,j].sum()),available_gwh=float(va[i,j].sum()),curtailment_gwh=float((va[i,j]-vg[i,j]).sum())))
 vt=pd.DataFrame(vrows);table(out,'vre_generation_curtailment_by_province_technology.csv',vt)
 assert abs(vt.curtailment_gwh.sum()-annual['vre_curtailment_gwh'])<=1e-5
 generated=pd.read_csv(inp.path('annual_generation_by_province_technology.csv'));merged=generated.merge(vt[['province_code','technology','curtailment_gwh']],on=['province_code','technology'],how='left',validate='one_to_one');merged['curtailment_scope']=np.where(merged.technology.isin(tech),'VRE_AVAILABLE_MINUS_GENERATED','NOT_APPLICABLE_IN_THIS_VRE_CURTAILMENT_COLUMN');table(out,'generation_and_vre_curtailment_by_province_technology.csv',merged)
 th=np.load(inp.path('thermal_dispatch.npz'),allow_pickle=False);thermal=list(th['technologies'].astype(str));start=th['startup_capacity_gw'].sum(axis=2);stop=th['shutdown_capacity_gw'].sum(axis=2)
 manifest=pd.read_csv(inp.path('input_manifest.csv'));name='technology/thermal_nuclear_ruc_parameters.csv';parameter=DATA/name;assert len(manifest[manifest.logical_path==name])==1;assert sha(parameter)==manifest.loc[manifest.logical_path==name,'sha256'].iloc[0]
 ruc=pd.read_csv(parameter).set_index('technology').loc[thermal];caps=pd.read_csv(inp.path('thermal_nuclear_capacity.csv')).set_index(['province_code','technology']);trows=[]
 for i,prov in enumerate(p):
  for j,t in enumerate(thermal):
   cap=float(caps.loc[(prov,t),'capacity_gw']);trows.append(dict(province_code=int(prov),technology=t,capacity_gw=cap,startup_capacity_sum_gw=float(start[i,j]),shutdown_capacity_sum_gw=float(stop[i,j]),equivalent_full_capacity_starts=float(start[i,j]/cap) if cap>1e-10 else None,equivalent_full_capacity_shutdowns=float(stop[i,j]/cap) if cap>1e-10 else None,startup_cost_million_cny=float(start[i,j]*ruc.loc[t,'startup_yuan_per_mw']/1000),shutdown_cost_million_cny=float(stop[i,j]*ruc.loc[t,'shutdown_yuan_per_mw']/1000)))
 tt=pd.DataFrame(trows);table(out,'thermal_start_stop_by_province_technology.csv',tt)
 costs=pd.read_csv(inp.path('cost_components.csv'));costmap=costs.set_index('cost_component').value_million_cny_per_year
 reconstructed=float(tt.startup_cost_million_cny.sum()+tt.shutdown_cost_million_cny.sum());np.testing.assert_allclose(reconstructed,costmap['operating_startup_shutdown'],rtol=1e-7,atol=1e-6)
 st=np.load(inp.path('storage_dispatch.npz'),allow_pickle=False);srows=[];sc=st['charge_gw'];sd=st['discharge_gw'];se=st['energy_capacity_gwh']
 for i,prov in enumerate(p):
  for j,t in enumerate(st['technologies'].astype(str)):srows.append(dict(province_code=int(prov),technology=t,charge_gwh=float(sc[i,j].sum()),discharge_gwh=float(sd[i,j].sum()),energy_capacity_gwh=float(se[i,j]),equivalent_full_discharge_cycles=float(sd[i,j].sum()/se[i,j]) if se[i,j]>1e-10 else None))
 table(out,'storage_operation_by_province_technology.csv',pd.DataFrame(srows));np.testing.assert_allclose([sc.sum(),sd.sum()],[annual['storage_charge_gwh'],annual['storage_discharge_gwh']],atol=1e-5,rtol=1e-10)
 metrics=solve['solution_contract']['barrier_primal_dual_metrics'];P=float(metrics['primal_objective']);D=float(metrics['dual_objective']);comparisons=[];decomposition=[];sources={}
 for label,rel in REFS[year].items():
  ref=load_reference(label,rel);sources[label]=ref['inputs'];comparisons.append(dict(reference=label,case=a.case,point_saving_yi_cny=(ref['P']-P)/100,lower_saving_yi_cny=(ref['D']-P)/100,upper_saving_yi_cny=(ref['P']-D)/100,reference_P_million_cny=ref['P'],reference_D_million_cny=ref['D'],target_P_million_cny=P,target_D_million_cny=D,screening_B_million_cny=0.,vre_curtailment_difference_gwh=annual['vre_curtailment_gwh']-ref['annual']['vre_curtailment_gwh'],storage_charge_difference_gwh=annual['storage_charge_gwh']-ref['annual']['storage_charge_gwh']))
  refcost=ref['cost'].set_index('cost_component');both=costs.set_index('cost_component')
  for key in refcost.index.union(both.index):
   lhs=float(refcost.loc[key,'value_million_cny_per_year']) if key in refcost.index else 0.;rhs=float(both.loc[key,'value_million_cny_per_year']) if key in both.index else 0.
   direct=bool(both.loc[key,'included_directly_in_objective']) if key in both.index else bool(refcost.loc[key,'included_directly_in_objective']);decomposition.append(dict(reference=label,cost_component=key,reference_million_cny=lhs,target_million_cny=rhs,saving_million_cny=lhs-rhs,included_directly_in_objective=direct))
 decomposition_frame=pd.DataFrame(decomposition)
 for comparison in comparisons:
  selected=decomposition_frame[(decomposition_frame.reference==comparison['reference']) & decomposition_frame.included_directly_in_objective]
  np.testing.assert_allclose(selected.saving_million_cny.sum(),comparison['point_saving_yi_cny']*100,rtol=1e-7,atol=1e-4)
 table(out,'cost_comparisons.csv',pd.DataFrame(comparisons));table(out,'cost_saving_by_component.csv',decomposition_frame)
 summary=dict(status='PASS',case=a.case,planning_year=year,computed_on='T550',P_million_cny=P,D_million_cny=D,comparisons=comparisons,services=national.to_dict('records'),annual=annual,startup_shutdown_cost_million_cny=reconstructed,startup_capacity_sum_gw=float(start.sum()),shutdown_capacity_sum_gw=float(stop.sum()),service_decomposition_max_abs_gw=closure,actual_v2g_discharge_gwh=float(f['ev_v2g_discharge_gw'].sum()),price_metadata=price_meta,source_files=inp.checked,reference_source_files=sources,ruc_parameter_sha256=sha(parameter),seconds=time.time()-started,interpretation=['Engineering dual comparison intervals, not statistical confidence intervals or market settlement','Each OPS year uses its own accepted Base-frozen source, not another OPS year as upstream','Start/stop variables are continuous GW capacities; equivalent full-capacity cycles are not discrete unit start counts','Service down/up calculated against each contracted service pool baseline; V2G discharge is separately reported and not added again to net-service down regulation','Province code 0 in six-scope dispatch means synchronous national sum'])
 save(out/'analysis_summary.json',summary)
 files={str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in out.rglob('*') if p.is_file()};assert max(v['bytes'] for v in files.values())<=32*1024**2;save(out/'analysis_manifest.json',files)
 print(json.dumps(dict(case=a.case,status='PASS',files=len(files),bytes=sum(v['bytes'] for v in files.values()),seconds=time.time()-started)),flush=True)
if __name__=='__main__':main()
