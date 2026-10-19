"""Finite continuation-year build/solve gate; each invocation preserves a new output.
Usage: --year 2040|2050 --state DIR --hours 1|24 [--unscreened] --output NEW
"""
import argparse, json, sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda x:x.tolist() if hasattr(x,'tolist') else str(x))+'\n',encoding='utf-8')

def parameters(config,data,model,year):
    from cispo_model.data import DATA_ROOT
    rows=[]
    def check(name,actual,expected):
        ok=bool(np.isfinite(np.asarray(actual)).all() and np.allclose(actual,expected,atol=1e-12,rtol=1e-12)) if isinstance(expected,(float,int)) else actual==expected
        ar=np.asarray(actual)
        value=actual if ar.ndim==0 else dict(min=float(ar.min()),max=float(ar.max()))
        rows.append(dict(parameter=name,actual=value,expected=expected,passed=ok))
    settings=config.raw['flexible_load'];service=data.flexible_load_v4
    h,c,v,b,cap,thermal,release,evcost,v2cost,infra,owner,deg,credits = ((.4,.3,.3,.15,60,35,40,35,40,30,120,110,(.5,.55,.45,.45)) if year==2040 else (.5,.4,.4,.2,120,30,30,30,30,20,100,80,(.45,.5,.4,.4)))
    check('v1g_fraction',settings['ev_v1g']['shiftable_energy_fraction'],v)
    check('v2g_fraction',settings['ev_v2g']['participation_fraction'],b)
    check('v2g_cap_gw',settings['ev_v2g']['national_contracted_power_cap_gw_by_planning_year'][str(year)],cap)
    check('legacy_bidirectional_activation',service.legacy_bidirectional_activation,False)
    for component,ret,duration in [('heating',.94,4),('cooling',.92,5)]:
        for key,val in [('retention_per_hour',ret),('positive_state_duration_hours',duration),('negative_state_duration_hours',duration)]:check(component+'.'+key,service.thermal_parameters[component][key],val)
        manifest=json.loads((DATA_ROOT/'load/flexible_load_envelope_v3.manifest.json').read_text())
        check(component+'.comfort_band',manifest[component+'_comfort_band_c'],1.)
        for key,val in [('enablement_cost_yuan_per_kw_year',thermal),('activation_cost_release_yuan_per_mwh',release),('activation_cost_precondition_yuan_per_mwh',0)]:check(component+'.'+key,service.service_costs[component][key],val)
    for component,vals in [('ev_v1g',(evcost,20,0,0)),('ev_v2g',(v2cost,owner,infra,deg))]:
        for key,val in zip(('enablement_cost_yuan_per_kw_year','activation_cost_yuan_per_mwh','infrastructure_cost_yuan_per_kw_year','degradation_cost_yuan_per_mwh'),vals):check(component+'.'+key,service.service_costs[component][key],val)
    for key in ('charge_efficiency','discharge_efficiency'):check(key,settings['ev_v2g'][key],.94)
    check('power_duration_hours',settings['ev_v2g']['power_duration_hours'],4.)
    check('maximum_power_to_daily_average_ratio',settings['ev_v1g']['maximum_power_to_daily_average_ratio'],2.)
    baseline=data.load_components_gw['ev'];daily=baseline.reshape(31,365,24).mean(axis=2).repeat(24,axis=1)
    check('actual_ev_charge_envelope_error',service.ev_availability['available_charge_power_gw']-np.maximum(v*baseline,2*v*daily),0.)
    check('actual_ev_inventory_error',service.ev_availability['fleet_energy_capacity_gwh']-.94*v*daily*24,0.)
    upstream=pd.read_csv(DATA_ROOT/'load/flexible_load_envelope_v3.csv.gz');upstream=upstream.loc[upstream.year==year]
    for component,fraction in [('heating',h),('cooling',c)]:
        for short,long in [('up','increase'),('down','reduction')]:
            values=upstream.pivot(index='province_code',columns='hour_index',values=f'{component}_{long}_limit_gw').reindex(data.provinces.province_code).to_numpy()
            check(component+'.participation_'+short+'_error',service.thermal_envelopes_gw[component+'_'+short]-fraction*values,0.)
    firm=settings['firm_capacity_credit']
    for component,val in zip(('heating','cooling','ev_v1g','ev_v2g'),credits):check('credit.'+component,firm['derating_fraction'][component],val)
    check('credit.duration',firm['required_event_duration_hours'],4.)
    check('credit.peak_reference',firm['peak_reference'],'four_hour_window_containing_immutable_full_year_province_baseline_peak_v1')
    variables=model.getVars()
    for prefix,val in [('heating_shift_up_gw_active[',0),('cooling_shift_up_gw_active[',0),('heating_shift_down_gw_active[',release/1000),('cooling_shift_down_gw_active[',release/1000),('ev_mobility_v1g_relocated_gw[',.02),('ev_mobility_discharge_gw[',(owner+deg)/1000)]:
        values=[x.Obj for x in variables if x.VarName.startswith(prefix)]
        if values:check('actual_objective.'+prefix,values,val)
        else:rows.append(dict(parameter='actual_objective.'+prefix,actual='ABSENT_IN_WINDOW',expected='support-dependent',passed=True))
    check('credit.variable_count',sum(x.VarName.startswith('firm_flexible_capacity_credit_gw[') for x in variables),124)
    return dict(status='PASS' if all(x['passed'] for x in rows) else 'FAIL',year=year,checks=rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--year',type=int,choices=[2040,2050],required=True);p.add_argument('--state',required=True,type=Path);p.add_argument('--hours',type=int,choices=[1,24],required=True);p.add_argument('--unscreened',action='store_true');p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    out=a.output.resolve()
    if out.exists():raise FileExistsError(out)
    profile=json.loads((ROOT/f'config/solver_profiles/barrier_stagea_screened_agg0_{a.year}_v1_threads48.json').read_text());profile['numerics']['threads']=8
    if a.unscreened:
        if a.hours!=1:raise ValueError('Unscreened diagnostic is build-only')
        profile['profile_id']='continuation_unscreened_build_only';profile['direct_nonbasic_scientific_acceptance']=False;profile.pop('candidate_screen')
    profilepath=out.parent/(out.name+'_profile.json');save(profilepath,profile)
    scenario_path=out.parent/(out.name+'_scenario.json');scenario_path.write_bytes((ROOT/'config/scenarios/case3_thermal_ev_v5.json').read_bytes().replace(b'\r\n',b'\n'))
    argv=['runner','--config',str(ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json'),'--scenario-config',str(scenario_path),'--solver-config',str(profilepath),'--planning-year',str(a.year),'--state-in',str(a.state.resolve()),'--allow-candidate-state-in','--diagnostic-hours',str(a.hours),'--archive-original-model','--output-dir',str(out)]
    if not a.unscreened:argv+=['--vre-screen-csv',str(ROOT/f'supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready{a.year}_20261015/source_screen.csv')]
    if a.year==2050:argv+=['--late-entry-base-state']
    if a.unscreened:argv+=['--engineering-barrier-checkpoint-only']
    argv+=['--build-only'] if a.hours==1 else ['--export-barrier-checkpoint']
    save(out.parent/(out.name+'_command.json'),argv)
    import cispo_model.monolithic as monolithic
    from scripts import run_cispo_2030_full_year as runner
    captured={};original=monolithic.build_full_year_monolithic
    def capture(config,data,**kw):
        art=original(config,data,**kw);captured.update(config=config,data=data,art=art);return art
    code=0
    with patch.object(sys,'argv',argv),patch.object(monolithic,'build_full_year_monolithic',capture):
        try:runner.main()
        except SystemExit as exc:code=exc.code;print('RUNNER_EXIT',repr(code),flush=True)
    if not captured:raise RuntimeError('Stopped before construction; retained logs')
    art=captured['art'];model=art.model;config=captured['config'];data=captured['data']
    result=dict(runner_exit_code=code,year=a.year,hours=a.hours,unscreened=a.unscreened,result_use='TEST_ONLY_TRUNCATED_HORIZON')
    pr=parameters(config,data,model,a.year);save(out/'parameter_verification.json',pr);result['parameters']=pr['status']
    keys=['vre_capacity','vre_new','hydro_capacity','hydro_new','storage_capacity','storage_new','thermal_capacity','thermal_new','thermal_retrofit_to_ccs','line_capacity','line_new','wave_capacity','wave_new','phs_energy_capacity','intra_load_center_capacity','intra_load_center_new','spur_augmentation','hydro_spur_augmentation','trunk_augmentation']
    tiny=[];inspected={}
    for key in keys:
        if key not in art.variables:continue
        mv=art.variables[key];lo=np.asarray(mv.LB);up=np.asarray(mv.UB);w=up-lo;mask=(w>0)&(w<1e-5)
        inspected[key]=int(lo.size)
        for pos in zip(*np.where(mask)):tiny.append(dict(key=key,variable=mv[pos].item().VarName,lower=float(lo[pos]),upper=float(up[pos]),width=float(w[pos])))
    result['capacity_columns_inspected']=inspected;result['tiny_capacity_columns']=tiny
    if a.hours==24:
        result['status_code']=int(model.Status)
        if model.SolCount:
            from flex_numerics_diagnostics import service_diagnostics
            variables={k:v for k,v in art.variables.items() if k.startswith(('heating_','cooling_','ev_','actual_','flexible_service_','firm_flexible_')) or k=='effective_load'}
            diag=service_diagnostics(config,data,SimpleNamespace(variables=variables),a.hours,0,out);result['M']=diag['maximum_service_residual_gw_gwh']
            values=np.load(out/'service_values.npz')
            from cispo_model.flexible_credit import audit_optional_credit
            result['credit']=audit_optional_credit(config.raw['flexible_load'],data,values['flexible_service_capacity'],values['ev_enrolled_service_fraction'],values['ev_bidirectional_service_fraction'],values['firm_flexible_capacity_credit'])
        for filename in ('solution_qc.json','preservation_report.json'):
            result[filename]=json.loads((out/filename).read_text()) if (out/filename).exists() else None
    save(out/'continuation_gate.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('solution_qc.json','preservation_report.json')},default=str),flush=True)
    if code or pr['status']!='PASS' or tiny or (a.hours==24 and (model.Status!=2 or result.get('M',float('inf'))>1e-3)):raise SystemExit(2)
if __name__=='__main__':main()
