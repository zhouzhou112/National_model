"""Launch wrapper: record actual annual contract bounds without scanning all LP columns."""
from pathlib import Path
from unittest.mock import patch
import argparse,hashlib,json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def runtime_contract_audit(config,data,artifacts,resource,reference):
    if artifacts.index['optimization_hours']!=8760:
        raise ValueError('Runtime resource audit is for the complete annual model')
    table=pd.read_csv(reference)
    labels={'base':('Base','Pathway'),'conservative':('Conservative','Constant'),'open':('Open','Full')}
    label,participation=labels[resource]
    wanted=table[(table.resource_scenario==label)&(table.participation_setting==participation)&(table.planning_year==config.planning_year)&(table.weather_year==config.weather_year)]
    if len(wanted)!=1:raise ValueError('Missing or ambiguous annual contract reference')
    wanted=wanted.iloc[0][['heating_ceiling_gw','cooling_ceiling_gw','smart_ceiling_gw','discharge_ceiling_gw']].to_numpy(dtype=float)
    artifacts.model.update()
    upper=np.asarray(artifacts.variables['flexible_service_capacity'].UB)
    if upper.shape!=(len(data.provinces),4) or not np.isfinite(upper).all() or (upper<0).any():raise ValueError('Invalid model service bounds')
    actual=upper.sum(axis=0);error=np.abs(actual-wanted)
    national=float(config.raw['flexible_load']['ev_v2g']['national_contracted_power_cap_gw_by_planning_year'][str(config.planning_year)])
    structural=artifacts.index['flexible_load_structural_audit']
    nonnegative_rows=int(structural['effective_load_nonnegative_constraint_rows_added'])
    expected_rows=({2050:139,2060:2249}.get(config.planning_year,0) if resource=='open' else 0)
    checks=dict(annual_upper_matches_reference=bool((error<=1e-6).all()),effective_load_row_count=nonnegative_rows==expected_rows)
    if resource=='open':checks['open_national_cap_nonbinding_by_bounds']=bool(national==1000 and national-actual[3]>0)
    return dict(status='PASS' if all(checks.values()) else 'FAIL',resource=resource,planning_year=config.planning_year,optimization_hours=8760,checks=checks,services=['heating','cooling','ev_v1g','ev_v2g'],actual_upper_sums_gw=actual.tolist(),reference_upper_sums_gw=wanted.tolist(),absolute_difference_gw=error.tolist(),tolerance_gw=1e-6,national_v2g_cap_gw=national,national_v2g_slack_lower_bound_gw=float(national-actual[3]),effective_load_nonnegative_rows=nonnegative_rows,reference_sha256=hashlib.sha256(Path(reference).read_bytes()).hexdigest(),province_upper_gw=[dict(province_code=int(p),values_gw=upper[i].tolist()) for i,p in enumerate(data.provinces.province_code)],method='Read only 31x4 MVar upper bounds and existing structural audit; no LP modification')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',choices=['base','conservative','open'],required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('runner_args',nargs=argparse.REMAINDER);a=p.parse_args()
    args=a.runner_args[1:] if a.runner_args[:1]==['--'] else a.runner_args
    if args.count('--output-dir')!=1:p.error('One explicit output directory required')
    out=Path(args[args.index('--output-dir')+1]).resolve()
    from scripts import run_cispo_2030_full_year as runner
    import cispo_model.monolithic as monolithic
    original=monolithic.build_full_year_monolithic;captured={}
    def capture(config,data,**kwargs):
        art=original(config,data,**kwargs);audit=runtime_contract_audit(config,data,art,a.resource,a.reference)
        (out/'resource_structure_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        captured.update(art=art,config=config,audit=audit)
        if audit['status']!='PASS':
            from cispo_model.solution_preservation import archive_model
            archive_model(art.model,out)
            raise RuntimeError('Annual resource structure gate failed; original model preserved')
        return art
    code=0
    with patch.object(sys,'argv',['runner']+args),patch.object(monolithic,'build_full_year_monolithic',capture):
        try:runner.main()
        except SystemExit as e:code=e.code
    if captured and (out/'solve_report.json').exists():
        solve=json.loads((out/'solve_report.json').read_text())
        if solve.get('status')=='OPTIMAL' and captured['art'].model.SolCount:
            actual=np.asarray(captured['art'].variables['flexible_service_capacity'].X)
            cap=captured['audit']['national_v2g_cap_gw'];slack=float(cap-actual[:,3].sum())
            report=dict(resource=a.resource,national_v2g_cap_gw=cap,contracted_v2g_gw=float(actual[:,3].sum()),slack_gw=slack,passed=slack>0 if a.resource=='open' else slack>=-1e-6,attribute='X')
            (out/'resource_v2g_slack_check.json').write_text(json.dumps(report,indent=2)+'\n')
            from cispo_model.result_summary import finalize_result_manifest
            finalize_result_manifest(out,captured['config'])
            if not report['passed']:code=2
    if code:raise SystemExit(code)

if __name__=='__main__':main()
