"""Bounded numerical diagnostic of the actual national 8760h LP.

This writes a fresh diagnostic directory, never a production planning state.
--dry-run validates the configuration and records the resource requirements.
A time-limited run is NOT evidence of full-year optimality or numerical health.
Use a separately allocated high-memory compute node; never a login node.
"""
from pathlib import Path
import argparse
import copy
import json
import math
import os
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import psutil
from cispo_model.config import ModelConfig,load_model_config

_active_output_dir = None
RESOURCE_PROFILE = ROOT/'config/cloud_resource_profiles/a8_8760_stagea_default_v1.json'


def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    temporary.replace(path)


PARAMETERS = {
    'method': 'Method', 'threads': 'Threads', 'numeric_focus': 'NumericFocus',
    'scale_flag': 'ScaleFlag', 'presolve': 'Presolve',
    'barrier_convergence_tolerance': 'BarConvTol', 'crossover': 'Crossover',
    'crossover_basis': 'CrossoverBasis', 'solution_target': 'SolutionTarget',
    'feasibility_tolerance': 'FeasibilityTol', 'optimality_tolerance': 'OptimalityTol',
    'markowitz_tolerance': 'MarkowitzTol', 'time_limit_seconds': 'TimeLimit',
    'soft_mem_limit_gb': 'SoftMemLimit', 'dual_reductions': 'DualReductions',
    'inf_unbd_info': 'InfUnbdInfo',
}


def solver_parameter_snapshot(model, config):
    """Read back a safe allowlist, detecting ignored parameter assignments."""
    result={}
    for key,name in PARAMETERS.items():
        actual=getattr(model.Params,name)
        expected=config.raw['numerics'].get(key)
        if expected is not None and actual != expected:
            raise RuntimeError(f'Gurobi {name} mismatch: requested {expected}, active {actual}')
        if key == 'soft_mem_limit_gb' and expected is None and actual < 1e100:
            raise RuntimeError('Gurobi SoftMemLimit must be unlimited for the selected resource profile')
        result[name]=actual if math.isfinite(actual) else None
    for name in ['Aggregate','AggFill','BarOrder','BarCorrectors','BarHomogeneous',
                 'PreDual','PrePasses','PreSparsify','LPWarmStart','Seed','BarIterLimit']:
        result[name]=getattr(model.Params,name)
    return result


def diagnostic_exit_code(status, accepted):
    if status == 2 and accepted:
        return 0
    # Time/iteration/memory/interruption limits are inconclusive, not passes.
    return 3 if status in {7,8,9,10,11,16,17} else 2


def preserve_diagnostic_vectors(model, output_dir):
    """Query available Barrier vectors even when SolCount is zero; never accept them."""
    from cispo_model.solution_preservation import save_numeric_snapshot
    snapshot=save_numeric_snapshot(model,output_dir)
    # Keep the existing X filename without loading the entire vector into RAM.
    x=snapshot['attributes'].get('X')
    if x and x['finite']:
        shutil.copyfile(output_dir/'solution_snapshot'/x['path'],output_dir/'solution.npy')
    return snapshot


def export_physical_diagnostics(artifacts, data, config, output_dir):
    """A failed capacity/network QC must not suppress the hourly water QC."""
    from cispo_model.master import export_master_solution
    from cispo_model.solution_export import export_operational_solution
    result={}
    try:
        result['master']=export_master_solution(artifacts,data,output_dir,enforce_qc=True)
    except Exception as error:
        result['master_error']=f'{type(error).__name__}: {error}'
    try:
        operational=export_operational_solution(artifacts,data,config,output_dir,enforce_qc=True)
        result['operational_status']=operational.get('status')
    except Exception as error:
        result['operational_error']=f'{type(error).__name__}: {error}'
        qc_path=output_dir/'solution_qc.json'
        if qc_path.is_file():
            result['operational_status']=json.loads(qc_path.read_text(encoding='utf-8')).get('status')
    result['accepted']=bool('master' in result and result.get('operational_status')=='PASS'
        and 'operational_error' not in result)
    return result


def main():
    global _active_output_dir
    resource=json.loads(RESOURCE_PROFILE.read_text(encoding='utf-8'))
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',default='config/optimization_numeric_dac_by_year_v9.json')
    p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--time-limit',type=int,default=900)
    p.add_argument('--bar-conv-tol',type=float,choices=[1e-8,1e-6,1e-4],default=1e-4)
    p.add_argument('--threads',type=int,default=resource['gurobi']['threads'])
    p.add_argument('--soft-mem-limit-gb',type=float,default=resource['gurobi']['soft_mem_limit_gb'])
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--validate-inputs-only',action='store_true')
    a=p.parse_args()
    if (not 1<=a.time_limit<=1800 or not 1<=a.threads<=64
            or (a.soft_mem_limit_gb is not None and not 1<=a.soft_mem_limit_gb<=650)):
        p.error('Diagnostic limits: 1800 solver seconds, 64 threads, optional soft memory cap <=650 GB')
    cfg=load_model_config(path=a.config)
    if cfg.hours!=8760 or cfg.raw['time_boundary']!='cyclic_year' or cfg.planning_year!=2030:
        p.error('This gate requires the actual 2030/8760h cyclic model')
    raw=copy.deepcopy(cfg.raw)
    # Restore the selected Stage A contract; the source v9 configuration also
    # records local Crossover=2 QC experiments and is not a cloud solver profile.
    raw['numerics'].update(threads=a.threads,time_limit_seconds=a.time_limit,
        soft_mem_limit_gb=a.soft_mem_limit_gb,barrier_convergence_tolerance=a.bar_conv_tol,
        crossover=resource['gurobi']['crossover'],solution_target=1)
    cfg=ModelConfig(cfg.path,raw,formulation_path=cfg.formulation_path);cfg.validate()
    out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    _active_output_dir=out
    available=psutil.virtual_memory().available
    plan=dict(config=str(cfg.path),hours=8760,solver_time_limit_seconds=a.time_limit,
        threads=a.threads,soft_mem_limit_gb=a.soft_mem_limit_gb,
        barrier_convergence_tolerance=a.bar_conv_tol,
        crossover=raw['numerics']['crossover'],solution_target=raw['numerics']['solution_target'],
        resource_profile=str(RESOURCE_PROFILE),
        slurm_cpus_per_task=resource['slurm']['cpus_per_task'],
        slurm_memory_gib=resource['slurm']['memory_gib'],
        minimum_available_memory_gib=128,available_memory_gib=available/2**30,
        dry_run=a.dry_run,validate_inputs_only=a.validate_inputs_only,
        production_state_will_be_written=False,
        interpretation='A bounded precheck can expose failures; only OPTIMAL plus full QC certifies a solution')
    write(out/'plan.json',plan);write(out/'effective_config.json',raw)
    if a.dry_run:
        print(json.dumps(plan));return
    from cispo_model.data import DATA_ROOT,load_model_data
    from cispo_model.io_contract import write_run_provenance
    if a.validate_inputs_only:
        data=load_model_data(cfg)
        write_run_provenance(out,cfg,data_root=DATA_ROOT,planning_state=data.planning_state)
        write(out/'input_validation.json',dict(status='PASS',lp_built=False,
            hydro_stations=len(data.hydro_stations),load_shape=list(data.load_gw.shape)))
        return
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Full national probe requires a dedicated Slurm allocation')
    if available<128*2**30:
        raise RuntimeError('Insufficient free memory for national LP build')
    if int(os.environ.get('SLURM_CPUS_PER_TASK','0'))<max(a.threads,resource['slurm']['cpus_per_task']):
        raise RuntimeError('Slurm CPU allocation is below the selected resource profile')
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.diagnostics import configure_gurobi,model_statistics
    import gurobipy as gp
    started=time.perf_counter()
    write(out/'terminal.json',dict(state='RUNNING',phase='load_and_build',full_year_accepted=False))
    data=load_model_data(cfg)
    # The production manifest is produced before building, so a killed build
    # still leaves the exact input lineage alongside the resolved config.
    write_run_provenance(out,cfg,data_root=DATA_ROOT,planning_state=data.planning_state)
    art=build_full_year_monolithic(cfg,data,compute_max_cf=True)
    m=art.model;configure_gurobi(m,cfg,out/'gurobi.log');m.update()
    report=dict(scope='NATIONAL_8760_NUMERICAL_DIAGNOSTIC',build_seconds=time.perf_counter()-started,
        raw=model_statistics(m),reservoir_bounds=art.index['reservoir_flow_bound_audit'])
    report['raw'].update(min_bound=m.MinBound,max_bound=m.MaxBound)
    write(out/'build.json',report)
    # Preserve the original LP before any solve can fail. Do not hold an extra
    # presolved model in memory; optimize() records presolve/factor data in its log.
    report['gurobi_version']=list(gp.gurobi.version())
    report['solver_parameters']=solver_parameter_snapshot(m,cfg)
    write(out/'solver_parameters.json',report['solver_parameters'])
    m.write((out/'raw_model.mps').as_posix())
    report['raw_model_bytes']=(out/'raw_model.mps').stat().st_size
    report['presolve_and_factor_statistics']='gurobi.log from the actual optimize() call'
    write(out/'build.json',report)
    write(out/'terminal.json',dict(state='RUNNING',phase='optimize',full_year_accepted=False))
    last=[-1]
    with (out/'barrier_progress.jsonl').open('w',encoding='utf-8') as stream:
        def callback(model,where):
            if where==gp.GRB.Callback.BARRIER:
                iteration=int(model.cbGet(gp.GRB.Callback.BARRIER_ITRCNT))
                if iteration==last[0]:return
                last[0]=iteration
                record=dict(iteration=iteration,runtime=model.cbGet(gp.GRB.Callback.RUNTIME),
                    primal=model.cbGet(gp.GRB.Callback.BARRIER_PRIMOBJ),dual=model.cbGet(gp.GRB.Callback.BARRIER_DUALOBJ),
                    primal_infeasibility=model.cbGet(gp.GRB.Callback.BARRIER_PRIMINF),
                    dual_infeasibility=model.cbGet(gp.GRB.Callback.BARRIER_DUALINF),
                    complementarity=model.cbGet(gp.GRB.Callback.BARRIER_COMPL))
                primal,dual=record['primal'],record['dual']
                record['relative_primal_dual_gap']=(abs(primal-dual)/max(1.,abs(primal),abs(dual))
                    if math.isfinite(primal) and math.isfinite(dual) else None)
                stream.write(json.dumps(record)+'\n');stream.flush()
        m.optimize(callback)
    report.update(status=m.Status,solutions=m.SolCount,runtime=m.Runtime,barrier_iterations=m.BarIterCount,
        full_year_accepted=False)
    write(out/'result.json',report)
    try:
        report['solution_snapshot']=preserve_diagnostic_vectors(m,out)
    except Exception as error:
        report['solution_snapshot_error']=f'{type(error).__name__}: {error}'
    write(out/'result.json',report)
    if m.SolCount:
        try:
            report.update(objective=m.ObjVal,constraint_violation=m.ConstrVio,bound_violation=m.BoundVio,
                dual_violation=m.DualVio)
        except (gp.GurobiError, AttributeError) as error:
            report['solution_read_error']=str(error)
        write(out/'result.json',report)
    if m.Status==gp.GRB.INFEASIBLE:
        m.Params.TimeLimit=120;m.computeIIS();m.write(str(out/'iis.ilp'))
    if m.Status==gp.GRB.OPTIMAL:
        try:
            report['physical_qc']=export_physical_diagnostics(art,data,cfg,out/'physical_export')
            report['full_year_accepted']=bool(report['physical_qc']['accepted'] and m.ConstrVio<=1e-5
                and m.BoundVio<=1e-5 and m.DualVio<=1e-5)
        except Exception as error:
            report['physical_qc_error']=f'{type(error).__name__}: {error}'
        write(out/'result.json',report)
    exit_code=diagnostic_exit_code(m.Status,report['full_year_accepted'])
    write(out/'terminal.json',dict(state='COMPLETE',exit_code=exit_code,solver_status=m.Status,
        full_year_accepted=report['full_year_accepted']))
    print(json.dumps({k:report[k] for k in ['status','solutions','runtime','full_year_accepted']}),flush=True)
    m.dispose()
    raise SystemExit(exit_code)


if __name__=='__main__':
    # Keep a terminal record on ordinary Python failures as well as solver exits.
    # A hard OS kill may only leave the last RUNNING phase; never infer success.
    try:
        main()
    except Exception as error:
        if _active_output_dir is not None:
            write(_active_output_dir/'terminal.json',dict(state='ERROR',full_year_accepted=False,
                error=f'{type(error).__name__}: {error}'))
        raise
