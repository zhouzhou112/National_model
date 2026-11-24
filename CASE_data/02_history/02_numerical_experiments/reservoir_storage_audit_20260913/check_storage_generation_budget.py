"""8760h isolated energy ceilings for the three corrected reservoirs.

Diagnostic LPs only: fixed installed power, current local inflow, cyclic water
balance and storage limit. No electric network, security or dispatch-value
objective. Their energy difference is NOT the national optimum's loss bound.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import gurobipy as gp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    table = pd.read_csv(HERE/'original_vs_v2/reservoirs_620.csv')
    selected = table[table.source_active_storage_m3 != table.selected_active_storage_m3]
    cfg = json.loads((HERE/'original_vs_v2/effective_config.json').read_text(encoding='utf-8'))
    h = cfg['hydro']
    conversion = h['reservoir_efficiency']*h['water_density_kg_per_m3']*h['gravity_m_per_s2']/1e9
    out = HERE/'isolated_energy_checks'
    out.mkdir(exist_ok=False)
    with np.load(HERE/'sources/old_4139552_reservoir_dispatch.npz') as old:
        upstream = old['upstream_release_m3s']
    with np.load(HERE/'original_vs_v2/hourly_water_evidence.npz') as source:
        inflow = source['local_after_cascade_m3s']
    results = []
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag', 0)
        env.start()
        for i, station in selected.iterrows():
            if np.any(upstream[i] != 0):
                raise ValueError('Diagnostic assumes these selected stations have no incoming cascade water')
            for scenario, storage in [('original',station.source_active_storage_m3),
                                      ('corrected',station.selected_active_storage_m3)]:
                model = gp.Model(env=env)
                model.Params.Method=2
                model.Params.Crossover=2
                model.Params.CrossoverBasis=1
                model.Params.NumericFocus=2
                model.Params.ScaleFlag=2
                model.Params.Threads=2
                model.Params.TimeLimit=60
                model.Params.FeasibilityTol=1e-6
                model.Params.OptimalityTol=1e-6
                model.Params.BarConvTol=1e-8
                model.Params.LogFile=str(out/f'{station.hydrochn_row_id}_{scenario}.log')
                local=inflow[i]/1000
                release_upper=np.minimum(local+storage/3.6e6,local.sum())*(1+1e-12)
                power_per_flow=conversion*station.head_m*1000
                turbine=model.addMVar(8760,lb=0,ub=np.minimum(release_upper,station.existing_capacity_gw/power_per_flow),name='turbine_1000m3s')
                spill=model.addMVar(8760,lb=0,ub=release_upper,name='spill_1000m3s')
                v=model.addMVar(8760,lb=0,ub=storage/1e6,name='active_storage_million_m3')
                model.addConstr(v[0]-v[-1] == 3.6*(local[0]-turbine[0]-spill[0]),name='cyclic')
                model.addConstr(v[1:]-v[:-1] == 3.6*(local[1:]-turbine[1:]-spill[1:]),name='water_balance')
                model.setObjective(power_per_flow*turbine.sum(),gp.GRB.MAXIMIZE)
                model.optimize()
                row=dict(hydrochn_row_id=station.hydrochn_row_id,plant_name_zh=station.plant_name_local_ght,
                         scenario=scenario,storage_m3=float(storage),status=int(model.Status),runtime=float(model.Runtime),
                         scope='ISOLATED_8760H_ENERGY_CEILING_NOT_SYSTEM_SOLVABILITY')
                if model.SolCount:
                    residual=v.X-np.roll(v.X,1)-3.6*(local-turbine.X-spill.X)
                    row.update(max_generation_gwh=float(model.ObjVal),max_water_residual_m3=float(np.abs(residual).max()*1e6),
                               bound_violation=float(model.BoundVio),spill_m3=float(spill.X.sum()*3.6e6),
                               storage_excursion_m3=float(np.ptp(v.X)*1e6))
                    np.savez_compressed(out/f'{station.hydrochn_row_id}_{scenario}.npz',
                                        volume_m3=v.X*1e6,turbine_m3s=turbine.X*1000,spill_m3s=spill.X*1000)
                results.append(row)
                model.dispose()
                print(json.dumps(row,ensure_ascii=False),flush=True)
    pd.DataFrame(results).to_csv(out/'results.csv',index=False)
    (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
