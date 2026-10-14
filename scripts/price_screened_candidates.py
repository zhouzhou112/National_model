"""Offline pricing of a screened output, no Gurobi dependency or optimization.

Usage: python scripts/price_screened_candidates.py --run-dir OUTPUT_ARCHIVE
       --output NEW_DIRECTORY [--re-solve-count 0|1]
Reads original MPS, raw BarPi, candidate_selection.csv, vre_capacity.csv and
solve_report.json. Writes screen_pricing_certificate.json, negative columns
and screen_sign_flip_sites.csv; source results are never modified.
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cispo_model.vre_pricing import (archive_paths,parse_vre_mps,read_table,
    site_prices,certificate,write_csv,sha256,verify_semantic_files)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--re-solve-count',type=int,choices=[0,1],default=0)
    a=p.parse_args();root=a.run_dir.resolve();out=a.output.resolve()
    if out.exists() or out.is_relative_to(root): p.error('Choose a new output outside the immutable run directory')
    out.mkdir(parents=True)
    mps,pi,identity=archive_paths(root)
    capacity=root/'vre_capacity.csv';selection=root/'candidate_selection.csv';solvepath=root/'solve_report.json'
    configpath=root/'model_config_snapshot.json'
    sources=[capacity,selection,solvepath,configpath]
    identity['semantic_manifest']=verify_semantic_files(root,[v.name for v in sources])
    before={str(v):sha256(v) for v in sources}
    solve=json.loads(solvepath.read_text(encoding='utf-8'))
    columns,stats=parse_vre_mps(mps,pi)
    config=json.loads(configpath.read_text(encoding='utf-8'))['resolved_configuration']
    prices=site_prices(columns,read_table(capacity),headroom_zero_gw=config['numerics'].get('capacity_headroom_zero_gw',1e-12))
    objective=solve['objective_value'] if 'objective_value' in solve else solve['objective_value_million_cny']
    result,flips=certificate(prices,read_table(selection),objective,re_solve_count=a.re_solve_count)
    result.update(identity=identity,input_sha256=before,parse=stats,solver_status=solve.get('status'),
                  scope='FULL_YEAR' if identity['source'].get('optimization_hours')==8760 else 'ENGINEERING_WINDOW_ONLY')
    fields=list(prices[0])+['original_new_ub_gw','improvement_bound_million_cny','base_rc_ratio']
    write_csv(out/'screen_sign_flip_sites.csv',flips,fields)
    write_csv(out/'negative_screened_columns.csv',result['negative_excluded_columns'],fields)
    write_csv(out/'vre_site_reduced_costs.csv',prices,list(prices[0]))
    assert before=={str(v):sha256(v) for v in sources}
    (out/'screen_pricing_certificate.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['B_million_cny','B_over_objective','near_optimality_decision','base_comparison_decision']}))


if __name__=='__main__':main()
