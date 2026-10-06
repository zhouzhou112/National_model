"""Recheck frozen evidence, actual LP extremes, and all annual water outputs.

Run with --mode evidence|matrix|inputs. Writes only beside this script;
does not solve or alter production inputs. Matrix inspection uses a saved LP.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
from collections import Counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.parent / 'numeric_resolution_20260913'
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def evidence():
    manifest = json.loads((PREVIOUS / 'delivery_manifest.json').read_text(encoding='utf-8'))
    records = []
    for key, base in [('source_files', ROOT), ('evidence', PREVIOUS)]:
        for entry in manifest[key]:
            p = base / entry['path']
            actual = digest(p) if p.exists() else None
            records.append(dict(group=key, path=entry['path'], expected=entry['sha256'], actual=actual,
                                passed=actual == entry['sha256']))
    # Verify the actual candidate input manifest, including the corrected table.
    for entry in pd.read_csv(PREVIOUS / 'full_year_input_check/input_manifest.csv').to_dict('records'):
        if entry['integrity_method'] == 'sha256_file' and pd.notna(entry['sha256']):
            p = Path(entry['resolved_path'])
            actual = digest(p) if p.is_file() else None
            records.append(dict(group='input_file', path=entry['logical_path'], expected=entry['sha256'], actual=actual,
                                passed=actual == entry['sha256']))
    report = dict(checked=len(records), failed=[r for r in records if not r['passed']], records=records)
    save('evidence_integrity.json', report)
    print(json.dumps({k: report[k] for k in ['checked', 'failed']}, ensure_ascii=False), flush=True)


def ranges(values):
    a = np.abs(np.asarray(values, dtype=float))
    a = a[(a > 0) & np.isfinite(a) & (a < 1e90)]
    return dict(min=float(a.min()), max=float(a.max()), span=float(a.max()/a.min())) if len(a) else None


def matrix(path, label=''):
    import gurobipy as gp
    from cispo_model.config import load_model_config
    from cispo_model.diagnostics import configure_gurobi
    cfg = load_model_config(path='config/optimization_2030_spill_tightened_v3.json')
    m = gp.read(str(path))
    configure_gurobi(m, cfg, HERE / f'matrix_presolve{label}.log')
    results = {}
    for name in ['raw', 'presolved']:
        model = m if name == 'raw' else m.presolve()
        vs, cs = model.getVars(), model.getConstrs()
        a = model.getA().tocsr()
        magnitude = np.abs(a.data)
        row_ids = np.repeat(np.arange(a.shape[0]), np.diff(a.indptr))
        row_min = np.full(a.shape[0], np.inf); row_max = np.zeros(a.shape[0])
        col_min = np.full(a.shape[1], np.inf); col_max = np.zeros(a.shape[1])
        np.minimum.at(row_min, row_ids, magnitude); np.maximum.at(row_max, row_ids, magnitude)
        np.minimum.at(col_min, a.indices, magnitude); np.maximum.at(col_max, a.indices, magnitude)
        obj = np.asarray(model.getAttr('Obj', vs)); rhs = np.asarray(model.getAttr('RHS', cs))
        lb = np.asarray(model.getAttr('LB', vs)); ub = np.asarray(model.getAttr('UB', vs))
        worst = np.argsort(col_max/col_min)[-15:][::-1]
        high_cols = []
        for i in worst:
            idx = np.flatnonzero(a.indices == i)
            lo, hi = idx[np.argmin(magnitude[idx])], idx[np.argmax(magnitude[idx])]
            high_cols.append(dict(variable=vs[i].VarName, minimum=float(col_min[i]), maximum=float(col_max[i]),
                                  span=float(col_max[i]/col_min[i]), small_row=cs[row_ids[lo]].ConstrName,
                                  large_row=cs[row_ids[hi]].ConstrName))
        extreme_entries = []
        for ix in [np.argsort(magnitude)[:10], np.argsort(magnitude)[-10:][::-1]]:
            extreme_entries.extend(dict(row=cs[row_ids[j]].ConstrName, variable=vs[a.indices[j]].VarName,
                                        coefficient=float(a.data[j])) for j in ix)
        small = np.flatnonzero(magnitude < 1e-4)
        report = dict(variables=len(vs), constraints=len(cs), nonzeros=a.nnz,
                      matrix=ranges(magnitude), objective=ranges(obj), rhs=ranges(rhs), bounds=ranges(np.r_[lb, ub]),
                      max_row_span=float(np.max(row_max/row_min)), max_column_span=float(np.max(col_max/col_min)),
                      column_spans_above_1e6=int((col_max/col_min > 1e6).sum()),
                      small_coefficient_count=len(small), small_coefficient_row_families=dict(Counter(cs[row_ids[j]].ConstrName.split('[')[0] for j in small)),
                      high_column_spans=high_cols, extreme_entries=extreme_entries,
                      small_bounds=[dict(variable=vs[i].VarName, attribute=k, value=float(v[i]))
                                    for k, v in [('LB',lb), ('UB',ub)]
                                    for i in np.flatnonzero((np.abs(v)>0)&(np.abs(v)<1e-6))[:30]],
                      objective_extremes=[dict(variable=vs[i].VarName, value=float(obj[i]))
                                          for i in np.argsort(np.abs(obj))[-10:][::-1]],
                      weak_objective_families=dict(Counter(vs[i].VarName.split('[')[0]
                            for i in np.flatnonzero((np.abs(obj)>0)&(np.abs(obj)<=1e-6)))),
                      empty_rows=int((np.diff(a.indptr)==0).sum()), empty_columns=int((col_max==0).sum()))
        results[name] = report
        print(name, json.dumps({k:report[k] for k in ['matrix','bounds','max_column_span','small_coefficient_count']}, ensure_ascii=False), flush=True)
        if name == 'presolved': model.dispose()
    m.dispose()
    save(f'matrix_audit{label}.json', dict(source=str(path), source_sha256=digest(path), results=results))


def inputs():
    from cispo_model.config import load_model_config
    from cispo_model.data import load_model_data
    from cispo_model.hydro import HydroProfileReader
    from cispo_model.timeblocks import TimeBlock
    from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3, independent_spill_upper_scaled
    from cispo_model.monolithic import _reservoir_release_upper_scaled
    cfg = load_model_config(path='config/optimization_2030_spill_tightened_v3.json')
    data = load_model_data(cfg)
    with HydroProfileReader(cfg,data) as reader:
        h = reader.read_linear_block(TimeBlock(0,0,8760))
    shape = h.reservoir_local_inflow_m3s.shape
    turbine=np.zeros(shape); spill=np.zeros(shape); volume=np.zeros(shape); seen=np.zeros(shape[0],int)
    for path in sorted((PREVIOUS/'annual_spill_v3').glob('component_*.npz')):
        with np.load(path) as saved:
            rows=saved['station_rows']; seen[rows]+=1
            turbine[rows]=saved['turbine_m3s']; spill[rows]=saved['spill_m3s']; volume[rows]=saved['storage_m3']
    if not np.all(seen==1): raise ValueError('Incomplete or duplicate annual coverage')
    q=h.reservoir_local_inflow_m3s
    inventory=cyclic_inventory_upper_m3(h)
    flow_scale=cfg.raw['hydro']['reservoir_flow_variable_scale_m3s']
    release=_reservoir_release_upper_scaled(h,flow_scale_m3s=flow_scale,preserve_exact_hourly_zeros=True)
    spill_bound, eligible=independent_spill_upper_scaled(h,release,flow_scale)
    v4_bound, _=independent_spill_upper_scaled(h,release,flow_scale,positive_bound_floor_m3s=1.)
    upstream=np.zeros(shape)
    for src,dst,w,lag,f in zip(h.cascade_edge_source_local_rows,h.cascade_edge_target_local_rows,
                              h.cascade_edge_target_weights,h.cascade_edge_lag_h,h.cascade_edge_transfer_fraction):
        transmitted=np.roll((turbine[src]+spill[src]).sum(axis=0),int(lag))*f
        for target,weight in zip(dst,w): upstream[target]+=float(weight)*transmitted
    residual=volume-np.roll(volume,1,axis=1)-3600*(q+upstream-turbine-spill)
    generation=turbine*h.reservoir_generation_conversion_gw_per_m3s[:,None]
    cap=data.hydro_stations.existing_capacity_gw.to_numpy(float)[h.reservoir_station_rows]
    qc=dict(stations=shape[0],hours=shape[1],station_hours=int(np.prod(shape)),
            all_finite=bool(all(np.isfinite(x).all() for x in [volume,turbine,spill,residual])),
            water_residual_m3=float(np.abs(residual).max()),
            turbine_lower_violation_m3s=float(np.maximum(-turbine,0).max()),
            turbine_upper_violation_m3s=float(np.maximum(turbine-release*flow_scale,0).max()),
            spill_upper_violation_m3s=float(np.maximum(spill-spill_bound*flow_scale,0).max()),
            spill_lower_violation_m3s=float(np.maximum(-spill,0).max()),
            storage_lower_violation_m3=float(np.maximum(-volume,0).max()),
            storage_upper_violation_m3=float(np.maximum(volume-inventory[:,None],0).max()),
            generation_upper_violation_gw=float(np.maximum(generation-cap[:,None],0).max()),
            isolated_spill_upper_violation_m3s=float(np.maximum(spill[eligible]-q[eligible],0).max()))
    qc['passed']=bool(qc['all_finite'] and qc['water_residual_m3']<=1
                     and qc['storage_lower_violation_m3']<=1 and qc['storage_upper_violation_m3']<=1
                     and max(qc[k] for k in qc if k.endswith('_m3s'))<=1e-3
                     and qc['generation_upper_violation_gw']<=1e-6)
    hydro=dict(qc=qc, local_rhs_million_m3=ranges(q*3600/1e6), inventory_bound_million_m3=ranges(inventory/1e6),
               source_storage_million_m3=ranges(h.reservoir_active_storage_m3/1e6),
               release_upper_scaled=ranges(release), spill_upper_scaled=ranges(spill_bound), eligible=int(eligible.sum()))
    hydro['v4_bound_check']=dict(spill_upper_scaled=ranges(v4_bound),
        positive_bounds_relaxed=int((v4_bound>spill_bound).sum()),
        tightened_vs_original_release=int((v4_bound<release).sum()),
        newly_zero_vs_original_release=int(((v4_bound==0)&(release>0)).sum()),
        v3_bounds_contained=bool(np.all(spill_bound<=v4_bound)),original_release_contains_v4=bool(np.all(v4_bound<=release)),
        zero_bounds_identical=bool(np.array_equal(spill_bound==0,v4_bound==0)),
        existing_v3_solutions_v4_spill_violation_m3s=float(np.maximum(spill-v4_bound*flow_scale,0).max()),
        v3_positive_bounds_below_1e_4=int(((spill_bound>0)&(spill_bound<1e-4)).sum()),
        v4_positive_bounds_below_1e_4=int(((v4_bound>0)&(v4_bound<1e-4)).sum()))
    sites=data.vre_sites
    tiny=[]
    for cutoff in [1e-6,1e-5,1e-4]:
        subset=sites[(sites.capacity_floor_gw>0)&(sites.capacity_floor_gw<cutoff)]
        result=dict(cutoff_gw=cutoff,sites=len(subset),floor_gw=float(subset.capacity_floor_gw.sum()),
                    nameplate_8760_energy_upper_gwh=float(subset.capacity_floor_gw.sum()*8760))
        energy=0.
        for source,group in subset.groupby('cf_source_technology'):
            for start in range(0,8760,168):
                cf=data.cf.read(source,group.cf_grid_id.to_numpy(np.int64),start,min(start+168,8760))
                energy+=float(np.where(cf>=1e-4,cf,0).sum(axis=0)@group.capacity_floor_gw.to_numpy(float))
        result['actual_cf_energy_upper_gwh']=energy
        tiny.append(result)
    sites.loc[(sites.capacity_floor_gw>0)&(sites.capacity_floor_gw<1e-4)].to_csv(HERE/'tiny_existing_vre.csv',index=False)
    field=cfg.raw['ccs_injection_field']
    sink=data.vre_points.loc[data.vre_points[field]>0,field]
    record=dict(hydro=hydro,tiny_existing_vre=tiny,ccs_sinks=dict(count=len(sink),annual_total_mtpa=float(sink.sum()),
                individual_range=ranges(sink),field=field),dac=data.dac.to_dict('records'))
    save('annual_input_audit.json',record)
    print(json.dumps(record,ensure_ascii=False,indent=2),flush=True)
    if not qc['passed']: raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['evidence','matrix','inputs'],required=True)
    p.add_argument('--mps',type=Path)
    p.add_argument('--label',default='')
    args=p.parse_args()
    if args.mode=='matrix':
        if not args.mps: p.error('--mps required for matrix inspection')
        matrix(args.mps,args.label)
    elif args.mode=='inputs': inputs()
    else: evidence()
