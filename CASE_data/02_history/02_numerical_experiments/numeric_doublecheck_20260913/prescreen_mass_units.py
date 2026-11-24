"""Inspect consistent CO2 balance row units; no source mutation or solve."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import gurobipy as gp
from cispo_model.config import load_model_config
from cispo_model.diagnostics import configure_gurobi,model_statistics


def main():
    out=Path(__file__).resolve().parent
    p=out/'probes/cleaned_nf2_24h_s0_cross2_annual_bounds_no_dac_v6/model.mps'
    m=gp.read(str(p));cfg=load_model_config(path='config/optimization_2030_numeric_simplified_no_dac_v6.json')
    configure_gurobi(m,cfg,out/'mass_row_scale_presolve_fixed.log')
    records={}
    for name,scale in [('before',1.),('carbon_10kt_rows',100.)]:
        if scale!=1:
            prefixes=('annual_net_carbon_limit','co2_source_balance_p','co2_sink_injection_capacity',
                      'annual_captured_p','annual_emissions_accounting','dac_selected_horizon_capacity')
            rows=[r for r in m.getConstrs() if r.ConstrName.startswith(prefixes)]
            for r in rows:
                a=m.getRow(r)
                for i in range(a.size()):m.chgCoeff(r,a.getVar(i),a.getCoeff(i)*scale)
                r.RHS*=scale
            m.update()
        pre=m.presolve();records[name]={'raw':model_statistics(m),'presolved':model_statistics(pre)};pre.dispose()
        if scale!=1:m.write(str(out/'mass_rows_scaled_24.mps'))
    (out/'mass_row_scale_prescreen.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(records,indent=2))
    m.dispose()


if __name__=='__main__':main()
