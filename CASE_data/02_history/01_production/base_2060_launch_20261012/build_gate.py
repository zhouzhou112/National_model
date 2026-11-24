"""One-hour build-only identity and numerical audit, never optimize.

Explicit code root supports comparison with frozen 2050 code. Outputs arrays,
MPS section hashes, complete tiny-bound tables, and row/column-family coefficient
statistics. Data and state come from recorded environment/arguments.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys,time
from collections import Counter
import numpy as np
import pandas as pd
from scipy import sparse

def save(p,obj):p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--code-root',type=Path,default=Path(__file__).resolve().parents[3])
    p.add_argument('--year',type=int,required=True);p.add_argument('--state-in',type=Path,required=True)
    p.add_argument('--a12',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.code_root.resolve();sys.path.insert(0,str(root))
    from cispo_model.config import load_model_config
    from cispo_model.data import load_model_data,DATA_ROOT
    from cispo_model.planning_state import PlanningState
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.diagnostics import model_statistics
    from cispo_model.run_contract import analysis_case_identity
    from cispo_model.io_contract import write_run_provenance
    import gurobipy as gp
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    cfg=load_model_config(root/('config/optimization_numeric_dac_by_year_v9_a12.json' if a.a12 else 'config/optimization_numeric_dac_by_year_v9.json')).for_planning_year(a.year)
    state=PlanningState.load(a.state_in,expected_boundary_year=cfg.boundary_year,expected_scenario_id='base',allow_unaccepted_candidate=True)
    data=load_model_data(cfg,planning_state=state)
    write_run_provenance(out,cfg,data_root=DATA_ROOT,planning_state=data.planning_state)
    started=time.monotonic();art=build_full_year_monolithic(cfg,data,compute_max_cf=True,optimization_hours=1)
    m=art.model;m.update();lo=np.array(m.getAttr('LB'));up=np.array(m.getAttr('UB'))
    names=np.array(m.getAttr('VarName'));rows=np.array(m.getAttr('ConstrName'))
    families=np.array([n.split('[')[0] for n in names])
    # Capacity decisions include total/new/built/retrofit/connectivity stocks;
    # dispatch, reserve and storage charge/discharge are operational power.
    capacity=np.array([n.endswith(('_gw','_gwh')) and any(s in n for s in ['capacity','new','retrofit','expansion','spur','trunk']) for n in families])
    tiny=(up-lo>0)&(up-lo<1e-5)
    smallbounds=((abs(lo)>0)&(abs(lo)<1e-6))|((abs(up)>0)&(abs(up)<1e-6))
    for label,mask in [('tiny_intervals',tiny),('small_bounds',smallbounds)]:
        pd.DataFrame(dict(variable=names[mask],family=families[mask],lb=lo[mask],ub=up[mask],
            width=up[mask]-lo[mask],gw_capacity=capacity[mask])).to_csv(out/(label+'.csv'),index=False)
    mat=m.getA();coo=mat.tocoo();ab=abs(coo.data)
    extremes=[]
    for label,index in [('minimum',int(ab.argmin())),('maximum',int(ab.argmax()))]:
        extremes.append(dict(kind=label,row=str(rows[coo.row[index]]),column=str(names[coo.col[index]]),value=float(coo.data[index])))
    for axis,index,labels in [('row',coo.row,rows),('column',coo.col,names)]:
        def family(name):return re.sub(r'_\d+(?:_\d+)*$','',str(name).split('[')[0])
        frame=pd.DataFrame(dict(family=np.array([family(n) for n in labels])[index],absolute_coefficient=ab))
        frame.groupby('family').absolute_coefficient.agg(['size','min','max']).to_csv(out/(axis+'_coefficient_families.csv'))
    sparse.save_npz(out/'matrix.npz',mat)
    np.savez(out/'lp_arrays.npz',lower=lo,upper=up,rhs=m.getAttr('RHS'),objective=m.getAttr('Obj'),
        senses=m.getAttr('Sense'),row_names=rows,variable_names=names)
    m.write(str(out/'model.mps'))
    hashes={};section=None
    with (out/'model.mps').open('rb') as stream:
        for line in stream:
            if not line[:1].isspace():
                section=line.split()[0].decode();hashes.setdefault(section,hashlib.sha256())
            hashes[section].update(line)
    report=dict(year=a.year,optimization_hours=1,optimize_called=False,build_seconds=time.monotonic()-started,
        code_root=str(root),state_root=str(state.root),gurobi_version=gp.gurobi.version(),
        statistics=model_statistics(m),tiny_nonzero_rhs_rows=[dict(row=str(r),rhs=float(v)) for r,v in zip(rows,m.getAttr('RHS')) if 0<abs(v)<1e-12],mps_sections_sha256={s:h.hexdigest() for s,h in hashes.items()},
        scientific_identity=analysis_case_identity(cfg),tiny_gw_capacity_intervals=int((tiny&capacity).sum()),
        tiny_gw_capacity_by_family=dict(Counter(families[tiny&capacity])),
        small_nonzero_bounds_by_family=dict(Counter(families[smallbounds])),
        coefficient_extremes=extremes,coefficient_span=float(ab.max()/ab.min()),
        numerical_robustness_audit=art.index.get('numerical_robustness_audit',{}),
        annual_budget_note='One-hour annual flow budgets scale by 1/8760 and are separately disclosed; not GW capacity stocks',
        status='PASS' if not (tiny&capacity).any() and ab.max()/ab.min()<=1e9 else 'STOP_AUTHOR_REVIEW_REQUIRED')
    save(out/'build_report.json',report)
    for key in ['thermal_retrofit_survivor_upper_gw','hydro_capacity_floor_gw','hydro_capacity_upper_gw']:
        if key in art.index:np.save(out/(key+'.npy'),art.index[key])
    print(json.dumps({k:report[k] for k in ['status','statistics','tiny_gw_capacity_intervals','tiny_gw_capacity_by_family','coefficient_extremes','coefficient_span']}))
    m.dispose()

if __name__=='__main__':main()
