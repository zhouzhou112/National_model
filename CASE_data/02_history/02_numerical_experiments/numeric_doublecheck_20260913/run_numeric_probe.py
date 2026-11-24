"""v2 storage-only delta on the v1 cleanup candidate; bounded integration solve.

python run_probe.py --case physical_nf2 --hours 24 --time-limit 180
Cases: physical_nf1, rows_nf1, physical_nf2, capped_nf2, cleaned_nf2.
Only isolated numeric-repair evidence is written; default source data unchanged.
"""
from pathlib import Path
import argparse
import copy
import json
import sys
import time
import hashlib
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
import gurobipy as gp
from cispo_model.config import ModelConfig, load_model_config
from cispo_model.data import load_model_data
from cispo_model.monolithic import build_full_year_monolithic
from cispo_model.diagnostics import configure_gurobi, model_statistics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', required=True, choices=['physical_nf1','rows_nf1','physical_nf2','capped_nf2','cleaned_nf2'])
    p.add_argument('--hours', type=int, default=24)
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--time-limit', type=int, default=180)
    p.add_argument('--crossover', type=int, default=0)
    p.add_argument('--tag', default='')
    p.add_argument('--spill-reduction', action='store_true')
    p.add_argument('--spill-positive-bound-floor', type=float, default=0.0)
    p.add_argument('--config', type=str)
    p.add_argument('--cf-cutoff', type=float, default=1e-4)
    p.add_argument('--reuse-identical-mps', type=Path)
    p.add_argument('--annual-water-bounds', action='store_true')
    p.add_argument('--markowitz',type=float,default=0.01)
    a = p.parse_args()
    if not 1 <= a.hours <= 744 or not 1 <= a.time_limit <= 1800:
        p.error('Local probe limited to 744h / 1800 solver seconds')
    out=Path(__file__).parent/'probes'/f'{a.case}_{a.hours}h_s{a.start}_cross{a.crossover}{a.tag}'
    out.mkdir(parents=True, exist_ok=False)
    cfg=load_model_config(path=a.config or ('config/optimization_2030_storage_audited_v2.json' if a.case=='cleaned_nf2' else None),
        formulation_path='config/formulation_profiles/annual_capacity_link_rows_8192_v1.json' if a.case=='rows_nf1' else None)
    raw=copy.deepcopy(cfg.raw)
    raw['hydro']['limit_independent_spill_to_inflow']=a.spill_reduction
    raw['hydro']['independent_spill_positive_bound_floor_m3s']=a.spill_positive_bound_floor
    raw['numerics']['markowitz_tolerance']=a.markowitz
    raw['numerics'].update(method=2,threads=8,numeric_focus=1 if a.case.endswith('nf1') else 2,
        crossover=a.crossover,solution_target=0 if a.crossover else 1,barrier_convergence_tolerance=1e-8,
        feasibility_tolerance=1e-6,optimality_tolerance=1e-6,aggregate=1,
        dual_reductions=1,inf_unbd_info=0,time_limit_seconds=a.time_limit,soft_mem_limit_gb=8)
    if a.crossover:
        raw['numerics']['crossover_basis']=1
    if a.case in ['capped_nf2','cleaned_nf2']:
        raw['hydro']['reduce_cyclic_inventory_range']=True
    if a.case=='cleaned_nf2':
        raw['numerics']['coefficient_zero_tolerance']=a.cf_cutoff
        raw['hydro']['local_inflow_cleanup_m3s']=0.01
    cfg=ModelConfig(cfg.path,raw,formulation_path=cfg.formulation_path);cfg.validate()
    (out/'executed_probe_source.py').write_bytes(Path(__file__).read_bytes())
    (out/'configuration.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
    start=time.perf_counter(); data=load_model_data(cfg)
    if a.annual_water_bounds:
        from cispo_model.hydro import HydroProfileReader
        from cispo_model.timeblocks import TimeBlock
        import cispo_model.monolithic as mm
        with HydroProfileReader(cfg,data) as reader:
            annual=reader.read_linear_block(TimeBlock(0,0,8760))
        annual_inventory=mm.cyclic_inventory_upper_m3(annual)
        annual_release=mm._reservoir_release_upper_scaled(annual,flow_scale_m3s=cfg.raw['hydro']['reservoir_flow_variable_scale_m3s'],preserve_exact_hourly_zeros=True)
        mm.cyclic_inventory_upper_m3=lambda block: annual_inventory.copy()
        mm._reservoir_release_upper_scaled=lambda block,**kwargs: annual_release[:,a.start:a.start+a.hours].copy()
        del annual
    art=build_full_year_monolithic(cfg,data,compute_max_cf=True,optimization_hours=a.hours,optimization_start_hour=a.start)
    model=art.model;configure_gurobi(model,cfg,out/'gurobi.log');model.update()
    report={'build_seconds':time.perf_counter()-start,'compute_max_cf':True,'annual_water_bounds':a.annual_water_bounds,'independent_spill_reduction':a.spill_reduction,
            'optimization_hours':a.hours,'optimization_start_hour':a.start,
            'spill_positive_bound_floor_m3s':a.spill_positive_bound_floor,
            'raw':model_statistics(model)}
    report['capacity_floor_cleanup']=art.index.get('vre_capacity_floor_cleanup')
    report['raw'].update(min_bound=model.MinBound,max_bound=model.MaxBound)
    all_vars=model.getVars();all_rows=model.getConstrs()
    small_bounds=[]
    for attribute in ['LB','UB']:
        values=np.asarray(model.getAttr(attribute,all_vars))
        for i in np.flatnonzero((np.abs(values)>0)&(np.abs(values)<1e-6))[:30]:
            small_bounds.append(dict(name=all_vars[i].VarName,attribute=attribute,value=float(values[i])))
    report['small_bounds_examples']=small_bounds
    rhs_all=np.asarray(model.getAttr('RHS',all_rows))
    report['small_rhs_examples']=[dict(name=all_rows[i].ConstrName,value=float(rhs_all[i]))
        for i in np.flatnonzero((np.abs(rhs_all)>0)&(np.abs(rhs_all)<1e-5))[:30]]
    presolved=model.presolve();report['presolved']=model_statistics(presolved);presolved.dispose()
    (out/'build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    model.write((out/'raw_model.mps').resolve().as_posix())
    if a.reuse_identical_mps:
        current_hash=hashlib.sha256((out/'raw_model.mps').read_bytes()).hexdigest()
        reference_hash=hashlib.sha256(a.reuse_identical_mps.read_bytes()).hexdigest()
        basis=a.reuse_identical_mps.parent/'terminal.bas'
        matched=current_hash==reference_hash and basis.is_file()
        report['basis_revalidation']={'identical_mps':current_hash==reference_hash,
            'sha256':current_hash,'reference_mps':str(a.reuse_identical_mps),'basis_reused':matched,
            'interpretation':'Only a byte-identical previously cold-solved LP may reuse its basis; current physical QC is rerun. This is not a new cold Barrier solve.'}
        if matched:
            model.read(str(basis.resolve()));model.Params.Method=1
    model.optimize()
    try:
        model.write((out/'terminal.bas').resolve().as_posix())
    except Exception as error:
        report['basis_archive_error']=repr(error)
    report.update(status=model.Status,solution_count=model.SolCount,runtime=model.Runtime,barrier_iterations=model.BarIterCount)
    if model.SolCount:
        try:
            report['kappa_estimate']=model.Kappa
        except gp.GurobiError:
            pass
        report.update(objective=model.ObjVal,constraint_violation=model.ConstrVio,bound_violation=model.BoundVio,
                      dual_violation=model.DualVio)
        vs=model.getVars();cs=model.getConstrs();x=np.asarray(model.getAttr('X',vs));matrix=model.getA()
        activity=matrix@x;rhs=np.asarray(model.getAttr('RHS',cs));sense=np.asarray(model.getAttr('Sense',cs))
        residual=activity-rhs;viol=np.where(sense=='=',np.abs(residual),np.where(sense=='<',np.maximum(residual,0),np.maximum(-residual,0)))
        worst=np.argsort(viol)[-10:][::-1]
        report['worst_rows']=[dict(name=cs[i].ConstrName,violation=float(viol[i])) for i in worst]
        report['raw_max_row_violation']=float(viol.max(initial=0))
        np.save(out/'solution.npy',x)
        # Reuse publication-facing physical checks, even for nonbasic output.
        from cispo_model.master import export_master_solution
        from cispo_model.solution_export import export_operational_solution
        try:
            master_qc=export_master_solution(art,data,out/'physical_export',enforce_qc=False)
            op_qc=export_operational_solution(art,data,cfg,out/'physical_export',enforce_qc=False)
            report['physical_export_qc']={'master':master_qc,'operational_status':op_qc.get('status'),
                'hard_checks':op_qc.get('hard_checks')}
            master_pass=all(master_qc[k]<=1e-5 for k in [
                'maximum_center_balance_residual_gwh','maximum_province_net_exchange_residual_gwh',
                'maximum_intra_capacity_violation_gwh','maximum_vre_annual_availability_violation_gwh',
                'maximum_ror_annual_availability_violation_gwh'])
            master_pass=master_pass and master_qc['bidirectional_active_edge_count']==0 and master_qc['dpv_spur_augmentation_max_gw']<=1e-8
            report['physical_export_qc']['master_status']='PASS' if master_pass else 'HARD_FAIL'
            report['strict_acceptance']=bool(model.Status==2 and master_pass and op_qc.get('status')=='PASS'
                and report['raw_max_row_violation']<=1e-5 and model.BoundVio<=1e-5 and model.DualVio<=1e-5)
        except Exception as error:
            report['physical_export_error']=repr(error)
        # Small probe MPS supports independent inspection; no annual model is written.
        try:
            model.write((out/'model.mps').resolve().as_posix())
        except Exception as error:
            report['archive_error']=repr(error)
    (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True);model.dispose()


if __name__=='__main__':
    main()
