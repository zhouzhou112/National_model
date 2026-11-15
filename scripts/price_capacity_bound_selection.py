"""Read-only two-direction pricing of explicit VRE boundary-state selections.

Reference mode proposes a free set; it never claims a solution certificate or
submits a re-solve. All outputs go to a fresh sidecar outside the source run.
"""
from pathlib import Path
import argparse,copy,gzip,json,math,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cispo_model.vre_pricing import (archive_paths,parse_vre_mps,read_table,site_prices,
    directional_site_prices,directional_certificate,write_csv,verify_semantic_files,sha256,SITE_COLUMN)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir',type=Path,required=True)
    ap.add_argument('--selection-json',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--reference-only',action='store_true')
    ap.add_argument('--target-free-sites',type=int,default=5000)
    ap.add_argument('--parse-cache',type=Path,help='Reuse only a SHA-verified cap/new/spur parse from the same original MPS and BarPi')
    a=ap.parse_args();root=a.run_dir.resolve();out=a.output.resolve()
    if out.exists() or out.is_relative_to(root):ap.error('Fresh sidecar outside immutable run required')
    selection=json.loads(a.selection_json.read_text(encoding='utf-8'))
    if selection['schema_version']!='capacity_bound_selection_v1' or selection['mode']!='vre_boundary_states':ap.error('VRE boundary-state selection required')
    config=json.loads((root/'model_config_snapshot.json').read_text())['resolved_configuration']
    if selection['planning_year']!=config['planning_year']:ap.error('Source/selection year mismatch')
    names=['vre_capacity.csv','solve_report.json','model_config_snapshot.json']
    if not a.reference_only:names.append('capacity_bound_selection_audit.json')
    semantic=verify_semantic_files(root,names)
    before={n:sha256(root/n) for n in names}
    mps,pi,identity=archive_paths(root);stats_before={str(p):(p.stat().st_size,p.stat().st_mtime_ns) for p in [mps,pi]}
    out.mkdir(parents=True)
    if a.parse_cache:
        cache=a.parse_cache.resolve();record=json.loads((cache/'parse_cache_manifest.json').read_text())
        if record['schema_version']!='vre_spur_parse_cache_v1' or record['mps_sha256']!=identity['mps_sha256'] or record['barpi_sha256']!=identity['barpi_sha256']:
            ap.error('Parse cache source identity mismatch')
        if sha256(cache/'parsed_columns.json.gz')!=record['columns_sha256']:ap.error('Parse cache SHA mismatch')
        with gzip.open(cache/'parsed_columns.json.gz','rt') as f:columns=json.load(f)
        for d in columns.values():
            d['lb']=float(d['lb']);d['ub']=float(d['ub'])
        parse=record['parse']
    else:
        columns,parse=parse_vre_mps(mps,pi,include_spur=True)
        encoded={n:dict(d,lb=d['lb'] if math.isfinite(d['lb']) else str(d['lb']),ub=d['ub'] if math.isfinite(d['ub']) else str(d['ub'])) for n,d in columns.items()}
        with gzip.open(out/'parsed_columns.json.gz','wt') as f:json.dump(encoded,f,separators=(',',':'),allow_nan=False)
        record=dict(schema_version='vre_spur_parse_cache_v1',mps_sha256=identity['mps_sha256'],barpi_sha256=identity['barpi_sha256'],columns_sha256=sha256(out/'parsed_columns.json.gz'),parse=parse)
        (out/'parse_cache_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    capacity=read_table(root/'vre_capacity.csv');effective=copy.deepcopy(capacity)
    if a.reference_only:
        site_prices({n:v for n,v in columns.items() if SITE_COLUMN.fullmatch(n)},capacity,
                    headroom_zero_gw=config['numerics'].get('capacity_headroom_zero_gw',1e-12))
        for i,r in enumerate(effective):
            r['capacity_floor_gw']=columns[f'vre_capacity_gw[{i}]']['lb']
            r['capacity_upper_gw']=columns[f'vre_capacity_gw[{i}]']['ub']
    else:
        audit=json.loads((root/'capacity_bound_selection_audit.json').read_text())
        if audit['sha256']!=sha256(a.selection_json):ap.error('Archived selection SHA mismatch')
        originals={tuple(r['stable_key']):r for r in audit['rows'] if r['family']=='vre_capacity'}
        states={(r['grid_uid'],r['technology']):r['state'] for r in selection['columns']}
        for i,r in enumerate(effective):
            key=(r['grid_uid'],r['technology'])
            if states[key]=='free':
                r['capacity_floor_gw']=columns[f'vre_capacity_gw[{i}]']['lb'];r['capacity_upper_gw']=columns[f'vre_capacity_gw[{i}]']['ub']
            else:
                o=originals[key];lo=float(o['original_lb']);up=float(o['original_ub'])
                physical_lo=float(r['capacity_floor_gw']);physical_up=float(r['capacity_upper_gw'])
                cutoff=config['numerics'].get('capacity_headroom_zero_gw',1e-12)
                expected_up=physical_lo if abs(physical_up-physical_lo)<=cutoff else physical_up
                if not math.isclose(lo,physical_lo,abs_tol=1e-9,rel_tol=1e-10) or not math.isclose(up,expected_up,abs_tol=1e-9,rel_tol=1e-10):ap.error('Original bound audit/semantic export mismatch')
                r['capacity_floor_gw']=lo;r['capacity_upper_gw']=up
    prices=directional_site_prices(columns,effective,selection['columns'],require_fixed=not a.reference_only)
    result=dict(scope='REFERENCE_SCORES_ONLY' if a.reference_only else 'FIXED_SOLUTION_CERTIFICATE',source=str(root),identity=identity,semantic=semantic,source_sha256=before,selection_sha256=sha256(a.selection_json),parse=parse)
    if a.reference_only:
        base_free={ (r['grid_uid'],r['technology']) for r in prices if r['state']=='free'}
        candidates=[r for r in prices if r['state']!='free' and r['capacity_upper_gw']>r['capacity_floor_gw']]
        thresholds=[.2,.1,.05,.02,.01,.005,.001,0.]
        trials=[];chosen=None
        for threshold in thresholds:
            additional={ (r['grid_uid'],r['technology']) for r in candidates if r['increase_rc_ratio' if r['state']=='lower' else 'decrease_rc_ratio']<=threshold}
            total=len(base_free|additional);trials.append(dict(margin=threshold,base_free=len(base_free),added=len(additional),total_free=total))
            if chosen is None and total<=a.target_free_sites:chosen=(threshold,additional)
        result.update(target_free_sites=a.target_free_sites,threshold_trials=trials,
                      status='PROPOSAL_READY_REQUIRES_GATES' if chosen else 'STOP_AUTHOR_REVIEW_FREE_SET_SIZE')
        if chosen:
            threshold,additional=chosen;proposed=copy.deepcopy(selection)
            for r in proposed['columns']:
                if (r['grid_uid'],r['technology']) in additional:r['state']='free'
            proposed['source_references']['directional_reference']=dict(result_manifest_sha256=semantic['sha256'],barpi_sha256=identity['barpi_sha256'],mps_sha256=identity['mps_sha256'],margin=threshold,method='adverse/near-entry-or-exit directional ratio; retain spur inequality analytically')
            result.update(chosen_margin=threshold,free_sites=len(base_free|additional),added_sites=len(additional))
    else:
        solve=json.loads((root/'solve_report.json').read_text());objective=solve.get('objective_value_million_cny',solve.get('objective_value'))
        result['certificate']=directional_certificate(prices,objective)
        result['status']='CERTIFICATE_COMPUTED_NO_AUTOMATIC_RESOLVE'
    assert before=={n:sha256(root/n) for n in names}
    assert all((p.stat().st_size,p.stat().st_mtime_ns)==stats_before[str(p)] for p in [mps,pi])
    fields=sorted(set().union(*(r.keys() for r in prices)))
    write_csv(out/'boundary_directional_prices.csv',prices,fields)
    if a.reference_only and chosen:
        (out/'proposed_selection.json').write_text(json.dumps(proposed,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        result['proposed_selection_sha256']=sha256(out/'proposed_selection.json')
    (out/'directional_pricing_report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['identity','parse','source_sha256','semantic','certificate']}))

if __name__=='__main__':main()
