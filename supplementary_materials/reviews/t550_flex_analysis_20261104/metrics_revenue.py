"""T8 offline revenue/cost accounts with explicit unallocated common CO2 costs.
No solver imports. Inputs are SHA matched to the solved release manifest.
Shared CO2 transport/injection cost is allocated by provincial captured-source mass,
including fossil CCS, CHP CCS, BECCS and DAC, under the author-approved post-hoc rule.
"""
from pathlib import Path
import argparse, shutil, time, json
import numpy as np
import pandas as pd
from metrics_flex import Inputs,sha,save,price_arrays,BASE

def parameter(inputs,data_root,name):
    manifest=pd.read_csv(inputs.path('input_manifest.csv'))
    rows=manifest[manifest.logical_path==name]; assert len(rows)==1,name
    p=Path(data_root)/name; actual=sha(p);assert actual==rows.iloc[0].sha256,'parameter SHA mismatch: '+name
    inputs.checked['parameter:'+name]={'sha256':actual,'bytes':p.stat().st_size,'source':str(p)}
    return pd.read_csv(p)

def by_year(df,year):
    if 'year' in df:df=df[df.year==year]
    assert len(df)>0
    return df

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('case','release','annual-duals','annual-sha','out','data-root'):ap.add_argument('--'+n,required=True)
    a=ap.parse_args();start=time.time();out=Path(a.out);out.mkdir(parents=True,exist_ok=False);(out/'scripts').mkdir()
    for name in ['metrics_revenue.py','metrics_flex.py']:shutil.copy2(Path(__file__).parent/name,out/'scripts'/name)
    inp=Inputs(a.release);c=json.loads(inp.path('model_config_snapshot.json').read_text())['resolved_configuration'];year=int(c['planning_year'])
    def param(name):return parameter(inp,a.data_root,'technology/'+name+'.csv')
    ruc=param('thermal_nuclear_ruc_parameters').set_index('technology')
    om=param('thermal_nuclear_om_parameters').set_index('technology')
    sp=param('storage_technical_parameters').set_index('technology')
    capex=by_year(param('technology_capex_by_year'),year).set_index('technology')
    fuel=by_year(param('province_fuel_generation_cost_by_year'),year).set_index(['province_code','technology'])
    emissions=by_year(param('emission_factors_by_year'),year).set_index('technology')
    cc=param('ccs_cost_parameters').iloc[0]
    th_file=np.load(inp.path('thermal_dispatch.npz'),allow_pickle=False);st_file=np.load(inp.path('storage_dispatch.npz'),allow_pickle=False)
    th={k:th_file[k] for k in th_file.files};st={k:st_file[k] for k in st_file.files};th_file.close();st_file.close()
    p=th['province_codes'].astype(int);h=th['hour_index'].astype(int)
    assert np.array_equal(st['province_codes'],p) and np.array_equal(st['hour_index'],h)
    assert len(p)==31 and np.array_equal(h,np.arange(8760))
    for name in ['gross_generation_gw','net_generation_gw','online_capacity_gw','startup_capacity_gw','shutdown_capacity_gw','ramp_magnitude_gw']:
        assert th[name].shape==(31,len(th['technologies']),8760) and np.isfinite(th[name]).all(),name
    for name in ['reserve_up_gw','reserve_down_gw']:assert th[name].shape==(31,8760) and np.isfinite(th[name]).all(),name
    for name in ['charge_gw','discharge_gw','reserve_up_gw','reserve_down_gw']:assert st[name].shape==(31,len(st['technologies']),8760) and np.isfinite(st[name]).all(),name
    energy,_,_,dates,price_meta=price_arrays(inp,Path(a.annual_duals),a.annual_sha,p,h,c)
    annual_rows=pd.read_csv(a.annual_duals)
    annual_demand=annual_rows[annual_rows.row_family=='province_annual_effective_demand'].set_index('province_code').loc[p].pi_million_cny_per_gwh.to_numpy()
    annual_injection=annual_rows[annual_rows.row_family=='province_annual_non_spatial_injection'].set_index('province_code').loc[p].pi_million_cny_per_gwh.to_numpy()
    injection_energy=energy-1000*(annual_demand+annual_injection)[:,None]
    hd=pd.read_csv(inp.path('hourly_marginal_prices.csv.gz')).set_index(['province_code','hour_index']).reindex(pd.MultiIndex.from_product([p,h]))
    def dual(col):return hd[col].to_numpy().reshape(len(p),len(h))
    up=dual('up_reserve_pi_million_cny_per_gwh');down=dual('down_reserve_pi_million_cny_per_gwh');inertia=dual('inertia_pi_million_cny_per_gw_s')
    ann=pd.read_csv(inp.path('annual_constraint_shadow_prices.csv'))
    capacity=ann[ann.constraint=='capacity_margin'].copy();capacity.index=capacity.index_value.astype(int);assert len(capacity)==31
    carbon=ann[ann.constraint=='annual_net_carbon_limit'];assert len(carbon)==1
    carbon_price=float(carbon.iloc[0].tightening_scarcity_value)
    biomass=ann[ann.constraint=='annual_biomass_fuel_limit'].copy();biomass.index=biomass.index_value.astype(int)
    tc=pd.read_csv(inp.path('thermal_nuclear_capacity.csv')).set_index(['province_code','technology'])
    sc=pd.read_csv(inp.path('storage_capacity.csv')).set_index(['province_code','technology'])
    costs=pd.read_csv(inp.path('cost_components.csv')).set_index('cost_component').value_million_cny_per_year
    wacc=float(c['finance']['real_wacc_fraction']);life=c['finance']['default_lifetime_years']
    def crf(t):
        n=float(life[t]);return 1/n if wacc==0 else wacc*(1+wacc)**n/((1+wacc)**n-1)
    thtech=th['technologies'].astype(str); rt=ruc.reindex(thtech)
    thermal_up_by_tech=(rt.pmax_fraction.to_numpy()[None,:,None]*th['online_capacity_gw']-th['gross_generation_gw'])*(1-rt.ccs_power_loss_fraction.to_numpy()[None,:,None])
    thermal_down_by_tech=(th['gross_generation_gw']-rt.pmin_fraction.to_numpy()[None,:,None]*th['online_capacity_gw'])*(1-rt.ccs_power_loss_fraction.to_numpy()[None,:,None])
    net_residual=float(np.max(np.abs(th['net_generation_gw']-th['gross_generation_gw']*(1-rt.ccs_power_loss_fraction.to_numpy()[None,:,None]))))
    assert net_residual<=1e-8,'Net/gross power loss reconstruction mismatch'
    up_residual=float(np.max(np.abs(thermal_up_by_tech.sum(axis=1)-th['reserve_up_gw'])))
    down_residual=float(np.max(np.abs(thermal_down_by_tech.sum(axis=1)-th['reserve_down_gw'])))
    assert up_residual<=1e-8 and down_residual<=1e-8,'Thermal reserve reconstruction mismatch'
    rows=[]
    for pi,prov in enumerate(p):
      for k,t in enumerate(th['technologies'].astype(str)):
        gross=th['gross_generation_gw'][pi,k];net=th['net_generation_gw'][pi,k];cap=float(tc.loc[(prov,t),'capacity_gw'])
        fc=float(c['thermal']['nuclear_fuel_yuan_per_mwh']) if t=='nuclear' else fuel.loc[(prov,t),'fuel_cost_yuan_per_mwh']
        fc=0. if pd.isna(fc) else float(fc)
        factor=float(emissions.loc['coal' if t.startswith(('coal','cchp')) else 'gas','emission_factor_mtco2_per_gwh']) if t.startswith(('coal','cchp','gas','gchp')) else 0.
        capture=0.;ef=factor
        if t=='bioccs':
            ef=float(emissions.loc[t,'emission_factor_mtco2_per_gwh']);lc=emissions.loc[t].get('lifecycle_emission_factor_mtco2_per_gwh',0.);lc=0 if pd.isna(lc) else float(lc);capture=lc-ef
        elif t.endswith('ccs'):
            cf=float(emissions.loc['coal','ccs_capture_fraction']);capture=factor*cf;ef=factor*(1-cf)
        mass=float(gross.sum())*capture;em=float(gross.sum())*ef
        biomass_pj=float(gross.sum())*float(ruc.loc[t,'fuel_load_mj_per_kwh'])/1000 if t in ('bio','bioccs') else 0.
        row=dict(province_code=int(prov),technology=t,capacity_gw=cap,energy_capacity_gwh=None,generation_gwh=float(net.sum()),energy_revenue_million_cny=float(np.sum(injection_energy[pi]*net)/1000),capacity_revenue_million_cny=float(capacity.loc[prov,'gurobi_pi'])*float(c['security']['capacity_credit'][t])*cap,up_reserve_revenue_million_cny=float(np.sum(up[pi]*thermal_up_by_tech[pi,k])),down_reserve_revenue_million_cny=float(np.sum(down[pi]*thermal_down_by_tech[pi,k])),inertia_revenue_million_cny=float(np.sum(inertia[pi]*th['online_capacity_gw'][pi,k]*float(ruc.loc[t,'inertia_s']))),fuel_cost_million_cny=float(gross.sum())*fc/1000,variable_om_cost_million_cny=float(net.sum())*float(om.loc[t,'variable_om_yuan_per_mwh'])/1000,startup_shutdown_cost_million_cny=float(th['startup_capacity_gw'][pi,k].sum())*float(ruc.loc[t,'startup_yuan_per_mw'])/1000+float(th['shutdown_capacity_gw'][pi,k].sum())*float(ruc.loc[t,'shutdown_yuan_per_mw'])/1000,ramping_cost_million_cny=float(th['ramp_magnitude_gw'][pi,k].sum())*float(c['thermal']['ramping_cost_yuan_per_mwh'])/1000,annualized_investment_million_cny=cap*float(capex.loc[t,'capex_yuan_per_kw'])*crf(t),fixed_om_cost_million_cny=cap*float(capex.loc[t,'capex_yuan_per_kw'])*float(om.loc[t,'fixed_om_fraction_capex_per_year']),ccs_capture_cost_million_cny=mass*float(cc.capture_yuan_per_tco2),captured_mtco2=mass,emissions_mtco2=em,biomass_fuel_pj=biomass_pj,carbon_opportunity_cost_million_cny=em*carbon_price,biomass_opportunity_cost_million_cny=biomass_pj*float(biomass.loc[prov,'tightening_scarcity_value']),co2_transport_injection_cost_million_cny=None if t.endswith('ccs') else 0.,market_settleable_revenue_million_cny=None,market_scope_status='NOT_DEFINED_NO_MARKET_RULE_EVIDENCE')
        rows.append(row)
      for k,t in enumerate(st['technologies'].astype(str)):
        charge=st['charge_gw'][pi,k];discharge=st['discharge_gw'][pi,k];cap=float(sc.loc[(prov,t),'capacity_gw']);ec=float(sc.loc[(prov,t),'energy_capacity_gwh'])
        cost_basis=cap*float(capex.loc[t,'capex_yuan_per_kw'])
        if t=='phs' and c['storage_design']['phs_energy_capacity_mode']=='independent_power_energy_v1':
            design=c['storage_design'];cost_basis=cap*float(design['phs_power_capex_yuan_per_kw_by_planning_year'][str(year)])+ec*float(design['phs_energy_capex_yuan_per_kwh_by_planning_year'][str(year)])
        row=dict(province_code=int(prov),technology=t,capacity_gw=cap,energy_capacity_gwh=ec,generation_gwh=float((discharge-charge).sum()),energy_revenue_million_cny=float(np.sum(injection_energy[pi]*discharge-energy[pi]*charge)/1000),capacity_revenue_million_cny=float(capacity.loc[prov,'gurobi_pi'])*float(c['security']['capacity_credit'][t])*cap,up_reserve_revenue_million_cny=float(np.sum(up[pi]*st['reserve_up_gw'][pi,k])),down_reserve_revenue_million_cny=float(np.sum(down[pi]*st['reserve_down_gw'][pi,k])),inertia_revenue_million_cny=float(inertia[pi].sum())*cap*float(c['security']['non_synchronous_inertia_seconds'][t]),fuel_cost_million_cny=0.,variable_om_cost_million_cny=float((charge+discharge).sum())*float(sp.loc[t,'variable_om_yuan_per_mwh'])/1000,startup_shutdown_cost_million_cny=0.,ramping_cost_million_cny=0.,annualized_investment_million_cny=cost_basis*crf(t),fixed_om_cost_million_cny=cost_basis*float(sp.loc[t,'fixed_om_fraction_capex_per_year']),ccs_capture_cost_million_cny=0.,captured_mtco2=0.,emissions_mtco2=0.,biomass_fuel_pj=0.,carbon_opportunity_cost_million_cny=0.,biomass_opportunity_cost_million_cny=0.,co2_transport_injection_cost_million_cny=0.,market_settleable_revenue_million_cny=None,market_scope_status='NOT_DEFINED_NO_MARKET_RULE_EVIDENCE')
        rows.append(row)
    frame=pd.DataFrame(rows);thermal=~frame.technology.isin(['battery','phs']);storage=~thermal
    resource=pd.read_csv(inp.path('annual_resource_accounting_by_province.csv')).set_index('province_code').loc[p]
    by_province=frame.groupby('province_code')[['captured_mtco2','emissions_mtco2','biomass_fuel_pj']].sum().reindex(p)
    physical_checks={}
    for calc,reported in [('captured_mtco2','co2_captured_for_storage_mtco2'),('emissions_mtco2','emissions_before_dac_mtco2'),('biomass_fuel_pj','biomass_fuel_pj')]:
        residual=float(np.max(np.abs(by_province[calc]-resource[reported])))
        tol=max(1e-5,1e-6*float(np.abs(resource[reported]).max()))
        physical_checks[calc]={'max_abs_residual':residual,'tolerance':tol,'status':'PASS' if residual<=tol else 'FAIL'}
    assert all(x['status']=='PASS' for x in physical_checks.values()),physical_checks
    capture_numerical_residual=(float(resource.co2_captured_for_storage_mtco2.sum())-float(frame.captured_mtco2.sum()))*float(cc.capture_yuan_per_tco2)
    checks=[]
    mappings=[('operating_fuel','fuel_cost_million_cny',thermal),('operating_thermal_variable_om','variable_om_cost_million_cny',thermal),('operating_storage_variable_om','variable_om_cost_million_cny',storage),('operating_startup_shutdown','startup_shutdown_cost_million_cny',thermal),('operating_ramping','ramping_cost_million_cny',thermal),('thermal_nuclear_investment','annualized_investment_million_cny',thermal),('thermal_nuclear_fixed_om','fixed_om_cost_million_cny',thermal),('storage_investment','annualized_investment_million_cny',storage),('storage_fixed_om','fixed_om_cost_million_cny',storage),('ccs_capture','ccs_capture_cost_million_cny',thermal)]
    for key,col,mask in mappings:
        actual=float(frame.loc[mask,col].sum())+(capture_numerical_residual if key=='ccs_capture' else 0.);expected=float(costs[key]);err=actual-expected;tol=max(1e-6,abs(expected)*1e-8)
        checks.append(dict(component=key,reconstructed_million_cny=actual,exported_million_cny=expected,residual_million_cny=err,tolerance_million_cny=tol,status='PASS' if abs(err)<=tol else 'FAIL'))
    pd.DataFrame(checks).to_csv(out/'revenue_cost_reconciliation.csv',index=False)
    assert all(x['status']=='PASS' for x in checks),'Cost closure failed; see reconciliation'
    points=parameter(inp,a.data_root,'vre/optimization_points.csv')
    centers=points.groupby('province_code')[['lon','lat']].mean()
    flows=pd.read_csv(inp.path('co2_source_sink_flows.csv'))
    origins=centers.loc[flows.province_code]
    lon1=np.radians(origins.lon.to_numpy());lat1=np.radians(origins.lat.to_numpy());lon2=np.radians(flows.sink_lon.to_numpy());lat2=np.radians(flows.sink_lat.to_numpy())
    hav=np.sin((lat2-lat1)/2)**2+np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    distance=6371.0088*2*np.arcsin(np.sqrt(np.clip(hav,0,1)))
    flows['transport_injection_cost_million_cny']=flows.shipped_mtco2*(float(cc.storage_yuan_per_tco2)+float(cc.transport_yuan_per_tco2_km)*distance)
    provincial_cost=flows.groupby('province_code').transport_injection_cost_million_cny.sum().reindex(p,fill_value=0.)
    transport_sparse_residual=float(costs['co2_transport_injection'])-float(provincial_cost.sum())
    # Source export omits shipment entries <=1e-9 Mt; retain the exact objective residual explicitly.
    assert abs(transport_sparse_residual)<=max(1e-3,1e-6*abs(float(costs['co2_transport_injection']))),'Unexpected sparse CO2 cost residual'
    allocation=[]
    for prov in p:
        selected=frame[(frame.province_code==prov)&frame.technology.str.endswith('ccs')]
        dac=float(resource.loc[prov,'dac_removed_mtco2'])
        masses=[(row.technology,float(row.captured_mtco2)) for row in selected.itertuples()]+[('DAC',dac)]
        denominator=sum(mass for _,mass in masses);total=float(provincial_cost.loc[prov])
        assert denominator>=0 and (denominator>0 or abs(total)<=1e-8)
        for tech,mass in masses:
            amount=total*mass/denominator if denominator>0 else 0.
            allocation.append(dict(province_code=int(prov),technology=tech,captured_source_mtco2=mass,all_sources_captured_mtco2=denominator,province_co2_transport_injection_cost_million_cny=total,allocated_co2_cost_million_cny=amount,allocation_rule='AUTHOR_APPROVED_POSTHOC_CAPTURE_SHARE_ALL_PROVINCIAL_SOURCES'))
            if tech!='DAC':frame.loc[(frame.province_code==prov)&(frame.technology==tech),'co2_transport_injection_cost_million_cny']=amount
    allocation=pd.DataFrame(allocation)
    allocation_residual=float(np.max(np.abs(allocation.groupby('province_code').allocated_co2_cost_million_cny.sum().reindex(p)-provincial_cost)))
    assert allocation_residual<=1e-8,'All-source provincial cost allocation mismatch'
    allocation.to_csv(out/'co2_cost_allocation_by_province_source.csv',index=False)
    frame['province_co2_transport_injection_cost_million_cny']=frame.province_code.map(provincial_cost)
    revenues=['energy_revenue_million_cny','capacity_revenue_million_cny','up_reserve_revenue_million_cny','down_reserve_revenue_million_cny','inertia_revenue_million_cny']
    direct=['fuel_cost_million_cny','variable_om_cost_million_cny','startup_shutdown_cost_million_cny','ramping_cost_million_cny','annualized_investment_million_cny','fixed_om_cost_million_cny','ccs_capture_cost_million_cny']
    frame['all_related_dual_revenue_million_cny']=frame[revenues].sum(axis=1)
    frame['direct_cash_cost_million_cny']=frame[direct].sum(axis=1)
    frame['margin_before_shared_co2_cost_million_cny']=frame.all_related_dual_revenue_million_cny-frame.direct_cash_cost_million_cny-frame.carbon_opportunity_cost_million_cny-frame.biomass_opportunity_cost_million_cny
    complete=frame.co2_transport_injection_cost_million_cny.notna()
    common_total=float(costs['co2_transport_injection'])
    frame['net_revenue_upper_bound_million_cny']=frame.margin_before_shared_co2_cost_million_cny
    frame['net_revenue_lower_bound_million_cny']=frame.margin_before_shared_co2_cost_million_cny-np.where(frame.technology.str.endswith('ccs'),frame.province_co2_transport_injection_cost_million_cny,0.)
    frame['co2_allocation_bound_scope']=np.where(~frame.technology.str.endswith('ccs'),'No captured CO2; zero direct shipment cost','Individual bounds before allocation: 0 to province common CO2 cost; not jointly attainable')
    frame['net_economic_revenue_million_cny']=(frame.margin_before_shared_co2_cost_million_cny-frame.co2_transport_injection_cost_million_cny).where(complete)
    frame['required_capacity_compensation_cny_per_kw_year']=np.where(complete & (frame.capacity_gw>1e-9),np.maximum(0,-frame.net_economic_revenue_million_cny)/frame.capacity_gw,np.nan)
    frame['cost_account_status']=np.where(frame.technology.str.endswith('ccs'),'COMPLETE_WITH_AUTHOR_APPROVED_POSTHOC_CO2_ALLOCATION','DIRECT_TECHNOLOGY_ACCOUNT_COMPLETE')
    frame.to_csv(out/'firm_revenue_by_province_technology.csv',index=False)
    common=[dict(component='co2_transport_injection',cost_million_cny=float(costs['co2_transport_injection']),allocation='Provincial capture-share allocation includes all CCS and DAC sources; DAC detail retained separately',accounting_role='Actual objective cash cost'),dict(component='co2_transport_sparse_export_residual',cost_million_cny=transport_sparse_residual,allocation='Unallocated numerical remainder: source CSV omits flows <=1e-9 Mt',accounting_role='Reconstructed source CSV cost + this residual equals objective cost'),dict(component='ccs_capture_accounting_residual',cost_million_cny=capture_numerical_residual,allocation='Unallocated numerical remainder: annual captured variable minus dispatch-reconstructed captured mass',accounting_role='Technology capture costs + this residual equal objective capture cost')]
    pd.DataFrame(common).to_csv(out/'firm_revenue_common_costs.csv',index=False)
    save(out/'revenue_summary.json',dict(case=a.case,release=a.release,T8='PASS_POSTHOC_CO2_ALLOCATION',rows=len(frame),cost_checks=checks,co2_allocation_max_abs_residual_million_cny=allocation_residual,co2_transport_sparse_export_residual_million_cny=transport_sparse_residual,ccs_capture_accounting_residual_million_cny=capture_numerical_residual,physical_account_checks=physical_checks,net_generation_reconstruction_max_abs_gw=net_residual,producer_price_note='Thermal/discharge price=1000*(balance_pi-annual_injection_pi); charging price=1000*(balance_pi+annual_demand_pi)',thermal_up_reserve_reconstruction_max_abs_gw=up_residual,thermal_down_reserve_reconstruction_max_abs_gw=down_residual,inputs=inp.checked,price=price_meta,carbon_opportunity_cost_note='Shadow carbon price times net emissions, separate from objective cash costs; negative for BECCS removals',market_note='Actual settlement subset not defined because no jurisdiction/product rules supplied; no claim that all shadow revenue is payable',compensation_note='Economic proxy using all dual revenues and carbon/biomass opportunity costs; CCS uses author-approved post-hoc provincial capture-share cost allocation including DAC; not a settlement tariff',common_co2_cost_million_cny=float(costs['co2_transport_injection']),elapsed_seconds=time.time()-start,command=vars(a),solver_loaded=False))
    files={str(x.relative_to(out)):{'sha256':sha(x),'bytes':x.stat().st_size} for x in out.rglob('*') if x.is_file()}
    assert all(x['bytes']<=30_000_000 for x in files.values());save(out/'revenue_manifest.json',files)
    print(json.dumps({'case':a.case,'status':'PASS_POSTHOC_CO2_ALLOCATION','rows':len(frame),'cost_checks':'PASS','seconds':time.time()-start}),flush=True)
if __name__=='__main__':main()
