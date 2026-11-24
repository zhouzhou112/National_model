"""One finite local 24h gate through the production runner, with post-run audits.

Usage: python run_engineering_gate.py --case base|zero|case3|nocredit --output NEW
Captures the built objects without altering construction; retains all raw exports.
"""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', choices=['base','zero','case3','nocredit'],required=True)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); output=a.output.resolve()
    if output.exists(): raise FileExistsError(output)
    profile=output.parent/(output.name+'_profile.json')
    scenario=ROOT/'config/scenarios'/('case3_thermal_ev_v5_nocredit.json' if a.case=='nocredit' else 'case3_thermal_ev_v5.json')
    argv=['run_cispo_2030_full_year.py','--config',str(ROOT/'config/optimization_numeric_dac_by_year_v9.json'),
          '--diagnostic-hours','24','--archive-original-model','--output-dir',str(output)]
    if a.case=='zero':
        d=json.loads(scenario.read_text(encoding='utf-8'))
        d['overrides']['flexible_load']['response_contract']={
            'version':'proportional_enrollment_response_v1',
            'maximum_enrollment_fraction':dict.fromkeys(['heating','cooling','ev_v1g','ev_v2g'],0.),
            'v2g_infrastructure_fraction':0.}
        scenario=output.parent/(output.name+'_scenario.json'); save(scenario,d)
    if a.case!='base': argv+=['--scenario-config',str(scenario)]
    if a.case in ('case3','nocredit'):
        d=json.loads((ROOT/'config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json').read_text())
        d['numerics']['threads']=8;save(profile,d)
        argv+=['--solver-config',str(profile),'--vre-screen-csv',str(ROOT/'supplementary_materials/reviews/factor_pair_8760_20261005/cloud_payload/source_screen.csv'), '--export-barrier-checkpoint']
    save(output.parent/(output.name+'_command.json'),argv)
    import cispo_model.monolithic as monolithic
    from scripts import run_cispo_2030_full_year as runner
    original=monolithic.build_full_year_monolithic
    captured={}
    def capture(config,data,**kw):
        art=original(config,data,**kw)
        captured.update(config=config,data=data,art=art)
        return art
    exit_code=0
    with patch.object(sys,'argv',argv), patch.object(monolithic,'build_full_year_monolithic',capture):
        try: runner.main()
        except SystemExit as exc: exit_code=exc.code
    if not captured: raise RuntimeError('Runner stopped before build; inspect retained logs')
    art=captured['art']; model=art.model; config=captured['config'];data=captured['data']
    result={'case':a.case,'runner_exit_code':exit_code,'status_code':int(model.Status),
            'objective':float(model.ObjVal) if model.SolCount else None,'hours':24,'result_use':'TEST_ONLY_TRUNCATED_HORIZON'}
    if model.SolCount and a.case!='base':
        from flex_numerics_diagnostics import service_diagnostics
        keys={k:v for k,v in art.variables.items() if k.startswith(('heating_','cooling_','ev_','actual_','flexible_service_','firm_flexible_')) or k=='effective_load'}
        diag=service_diagnostics(config,data,SimpleNamespace(variables=keys),24,0,output)
        result['M']=diag['maximum_service_residual_gw_gwh']
        values=np.load(output/'service_values.npz')
        decisions=[k for k in values.files if not k.startswith(('actual_','effective_'))
                   and not k.endswith(('_upper','_ub'))]
        result['maximum_flex_decision_abs']=max(float(np.abs(values[k]).max(initial=0)) for k in decisions)
        if 'firm_flexible_capacity_credit' in values.files:
            from cispo_model.flexible_credit import audit_optional_credit
            result['credit']=audit_optional_credit(config.raw['flexible_load'],data,
                values['flexible_service_capacity'],values['ev_enrolled_service_fraction'],
                values['ev_bidirectional_service_fraction'],values['firm_flexible_capacity_credit'])
        else:
            result['credit']={'credit_variables_absent':True}
    for filename in ('preservation_report.json','solution_qc.json'):
        path=output/filename
        result[filename]=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
    save(output/'engineering_gate.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('preservation_report.json','solution_qc.json')}),flush=True)
    if model.Status!=2: raise SystemExit(2)


if __name__=='__main__':main()
