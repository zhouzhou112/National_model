"""Bounded 8760h water-block diagnostics, preserving every cascade edge.

Usage: python probe_annual_water.py --units water_scaled --output-dir NEW_DIR
Splits only disconnected hydraulic components; batches independent stations.
This is not a national electricity-system solve. The objective is generation
weighted by 1 + provincial hourly load / provincial peak, with existing power.
All hours, storage bounds, delays and transfer fractions come from production.
"""
from pathlib import Path
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import gurobipy as gp
import numpy as np
from scipy import sparse
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock
from cispo_model.monolithic import _reservoir_release_upper_scaled
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3, independent_spill_upper_scaled


def components(h):
    n=len(h.reservoir_station_rows)
    parent=list(range(n))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    for src,dst in zip(h.cascade_edge_source_local_rows,h.cascade_edge_target_local_rows):
        rows=list(src)+list(dst)
        for row in rows[1:]: parent[find(int(row))]=find(int(rows[0]))
    groups={}
    for i in range(n): groups.setdefault(find(i),[]).append(i)
    coupled=[g for g in groups.values() if len(g)>1]
    singles=[g[0] for g in groups.values() if len(g)==1]
    return coupled+[singles[i:i+16] for i in range(0,len(singles),16)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--units',choices=['water_scaled','energy_gw_gwh'],required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--time-limit',type=float,default=60)
    p.add_argument('--spill-reduction',action='store_true')
    p.add_argument('--spill-positive-bound-floor',type=float,default=0.)
    p.add_argument('--group-id',type=int)
    p.add_argument('--group-ids',type=int,nargs='+')
    p.add_argument('--config',default='config/optimization_2030_storage_audited_v2.json')
    p.add_argument('--presolve-only',action='store_true')
    args=p.parse_args()
    if not 0 < args.time_limit <= 600: p.error('Per component limit must be <= 600 seconds')
    out=args.output_dir;out.mkdir(parents=True,exist_ok=False)
    cfg=load_model_config(path=args.config)
    data=load_model_data(cfg)
    with HydroProfileReader(cfg,data) as reader: h=reader.read_linear_block(TimeBlock(0,0,8760))
    (out/'configuration.json').write_text(json.dumps(cfg.raw,indent=2))
    (out/'executed_probe_source.py').write_bytes(Path(__file__).read_bytes())
    storage=cyclic_inventory_upper_m3(h)/1e6
    release=_reservoir_release_upper_scaled(h,flow_scale_m3s=1000,preserve_exact_hourly_zeros=True)
    spill=release
    if args.spill_reduction:
        spill,eligible=independent_spill_upper_scaled(h,release,1000,positive_bound_floor_m3s=args.spill_positive_bound_floor)
        (out/'bound_reduction.json').write_text(json.dumps(dict(eligible_stations=int(eligible.sum()),
            changed_spill_bounds=int((spill<release).sum()),new_zero_bounds=int(((spill==0)&(release>0)).sum())),indent=2))
    power=h.reservoir_generation_conversion_gw_per_m3s*1000
    volume_energy=power/3.6
    capacity=data.hydro_stations.existing_capacity_gw.to_numpy(float)[h.reservoir_station_rows]
    turbine=np.minimum(release,capacity[:,None]/power[:,None])
    groups=components(h)
    (out/'scope.json').write_text(json.dumps(dict(hours=8760,stations=len(storage),groups=groups,
        units=args.units,spill_reduction=args.spill_reduction,objective='generation weighted by 1+load/peak',
        fixed_capacity='existing',national_electricity_constraints=False),indent=2))
    records=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',1);env.setParam('LogToConsole',0);env.start()
        for group_id,selected in enumerate(groups):
            if args.group_id is not None and group_id != args.group_id: continue
            if args.group_ids is not None and group_id not in args.group_ids: continue
            started=time.perf_counter()
            print('Building component',group_id,'stations',len(selected),flush=True)
            ids=np.asarray(selected,int);count=len(ids);hours=8760;size=count*hours
            index={int(i):j for j,i in enumerate(ids)}
            energy=args.units=='energy_gw_gwh'
            ff=power[ids] if energy else np.ones(count)
            vf=volume_energy[ids] if energy else np.ones(count)
            ub=np.r_[(turbine[ids]*ff[:,None]).ravel(),(spill[ids]*ff[:,None]).ravel(),
                     np.repeat(storage[ids]*vf,hours)]
            # Build in original water units, then apply the exact row/column
            # substitution. Physical residuals are reconstructed independently.
            k=np.arange(size);prev=(k//hours)*hours+(k-1)%hours
            row=[k,k,k,k];col=[k,k+size,k+2*size,prev+2*size]
            val=[np.full(size,3.6),np.full(size,3.6),np.ones(size),-np.ones(size)]
            for src,dst,weights,lag,transfer in zip(h.cascade_edge_source_local_rows,
                    h.cascade_edge_target_local_rows,h.cascade_edge_target_weights,
                    h.cascade_edge_lag_h,h.cascade_edge_transfer_fraction):
                for target,weight in zip(dst,weights):
                    if int(target) not in index: continue
                    for source in src:
                        if int(source) not in index: raise ValueError('Cascade was split')
                        rr=index[int(target)]*hours+np.arange(hours)
                        cc=index[int(source)]*hours+(np.arange(hours)-int(lag))%hours
                        vv=-3.6*float(weight)*np.asarray(transfer)
                        row.extend([rr,rr]);col.extend([cc,cc+size]);val.extend([vv,vv])
            water=sparse.coo_matrix((np.concatenate(val),(np.concatenate(row),np.concatenate(col))),shape=(size,3*size)).tocsr()
            factor=np.r_[np.repeat(ff,hours),np.repeat(ff,hours),np.repeat(vf,hours)]
            row_factor=np.repeat(vf,hours)
            matrix=water.multiply(row_factor[:,None]).multiply(1/factor).tocsr()
            rhs=(3.6*h.reservoir_local_inflow_m3s[ids]/1000).ravel()
            local_load=data.load_gw[h.reservoir_province_positions[ids]]
            price=1+local_load/local_load.max(axis=1)[:,None]
            objective=np.r_[(price*power[ids,None]/ff[:,None]).ravel(),np.zeros(2*size)]
            m=gp.Model(env=env)
            m.Params.Method=2;m.Params.Crossover=2;m.Params.CrossoverBasis=1
            m.Params.NumericFocus=2;m.Params.ScaleFlag=2;m.Params.Threads=4
            m.Params.SoftMemLimit=5;m.Params.TimeLimit=args.time_limit
            m.Params.BarConvTol=1e-8;m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6
            m.Params.LogFile=str(out/f'component_{group_id:03d}.log')
            x=m.addMVar(3*size,lb=0,ub=ub,obj=objective,name='water_coordinate')
            m.addMConstr(matrix,x,'=',rhs*row_factor,name='water_balance')
            m.ModelSense=gp.GRB.MAXIMIZE;m.update()
            rec=dict(group_id=group_id,station_rows=ids.tolist(),station_count=count,units=args.units,
                matrix_min=m.MinCoeff,matrix_max=m.MaxCoeff,bound_min=m.MinBound,bound_max=m.MaxBound,
                rhs_min=m.MinRHS,rhs_max=m.MaxRHS)
            if args.presolve_only:
                pre=m.presolve()
                rec.update(raw_variables=m.NumVars,raw_rows=m.NumConstrs,raw_nonzeros=m.NumNZs,
                    presolved_variables=pre.NumVars,presolved_rows=pre.NumConstrs,presolved_nonzeros=pre.NumNZs,
                    presolved_matrix_min=pre.MinCoeff,presolved_matrix_max=pre.MaxCoeff,
                    presolved_objective_min=pre.MinObjCoeff,presolved_objective_max=pre.MaxObjCoeff)
                records.append(rec);pre.dispose();m.dispose()
                (out/'presolve_results.json').write_text(json.dumps(records,indent=2));print(json.dumps(rec),flush=True)
                continue
            m.optimize()
            rec.update(status=m.Status,solutions=m.SolCount,runtime=m.Runtime,barrier_iterations=m.BarIterCount)
            if m.SolCount:
                native=x.X;physical=native/factor
                residual=(water@physical-rhs)*1e6
                physical_ub=ub/factor
                excess=np.maximum(physical-physical_ub,0)
                lower=np.maximum(-physical,0)
                rec.update(objective=m.ObjVal,raw_row_violation=m.ConstrVio,bound_violation=m.BoundVio,
                    dual_violation=m.DualVio,water_residual_m3=float(np.abs(residual).max()),
                    storage_violation_m3=float(max(excess[2*size:].max(),lower[2*size:].max())*1e6),
                    generation_gwh=float((physical[:size].reshape(count,hours)*power[ids,None]).sum()))
                rec['pass']=bool(m.Status==2 and rec['water_residual_m3']<=1 and rec['storage_violation_m3']<=1)
                try: rec['kappa']=m.Kappa
                except gp.GurobiError: pass
                np.savez_compressed(out/f'component_{group_id:03d}.npz',station_rows=ids,
                    turbine_m3s=physical[:size].reshape(count,hours)*1000,
                    spill_m3s=physical[size:2*size].reshape(count,hours)*1000,
                    storage_m3=physical[2*size:].reshape(count,hours)*1e6)
            else: rec['pass']=False
            rec['elapsed_seconds']=time.perf_counter()-started
            records.append(rec)
            (out/'results.json').write_text(json.dumps(records,indent=2))
            print(json.dumps(rec),flush=True)
            m.dispose()
    if args.presolve_only:return
    summary=dict(stations=sum(r['station_count'] for r in records),hours=8760,
        groups=len(records),all_pass=all(r['pass'] for r in records),
        failed_groups=[r['group_id'] for r in records if not r['pass']],
        runtime_seconds=sum(r['runtime'] for r in records),
        maximum_water_residual_m3=max((r['water_residual_m3'] for r in records if 'water_residual_m3' in r),default=None),
        components_without_solution=[r['group_id'] for r in records if not r['solutions']],
        national_electricity_lp_solved=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)


if __name__=='__main__': main()
