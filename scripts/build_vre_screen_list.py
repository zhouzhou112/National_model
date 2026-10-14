"""Build a year-specific screen from immutable Base original MPS/raw BarPi.

Usage: --run-dir BASE_OUTPUT --source-release RELEASE_ID --margin 0.2
       --output NEW_DIRECTORY
No optimization/Gurobi. Stable grid_uid x technology keys are preserved.
The JSON records SHA identities and the profile fields to use in a NEW release.
"""
import argparse
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cispo_model.vre_pricing import archive_paths,parse_vre_mps,read_table,site_prices,sha256,finite,write_csv,verify_semantic_files


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--source-release',required=True)
    p.add_argument('--margin',type=float,default=.2)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference-screen',type=Path,help='Optional independently archived Base screen for full-archive self-check')
    a=p.parse_args();root=a.run_dir.resolve();out=a.output.resolve()
    if out.exists() or out.is_relative_to(root):p.error('Use a new output outside the immutable Base archive')
    if finite(a.margin)<0:p.error('margin must be nonnegative')
    out.mkdir(parents=True)
    mps,pi,identity=archive_paths(root)
    paths=[root/'vre_capacity.csv',root/'model_config_snapshot.json']
    identity['semantic_manifest']=verify_semantic_files(root,[v.name for v in paths])
    hashes={str(x):sha256(x) for x in paths}
    config=json.loads(paths[1].read_text(encoding='utf-8'))['resolved_configuration']
    columns,stats=parse_vre_mps(mps,pi)
    prices=site_prices(columns,read_table(paths[0]),headroom_zero_gw=config['numerics'].get('capacity_headroom_zero_gw',1e-12))
    for row in prices:
        row['headroom_gw']=row['archived_capacity_upper_gw']-row['capacity_floor_gw']
        row['screened_out_at_margin']=row['headroom_gw']>0 and row['rc_ratio']>=a.margin
    target=out/'source_screen.csv';write_csv(target,prices,list(prices[0]))
    result=dict(identity=identity,input_sha256=hashes,parse=stats,sites=len(prices),
        candidate_screen=dict(enabled=True,margin=a.margin,source_release=a.source_release,
            source_dual_sha256=identity['barpi_sha256'],source_csv_sha256=sha256(target)),
        excluded_sites=sum(v['screened_out_at_margin'] for v in prices),
        scope='FULL_YEAR' if identity['source'].get('optimization_hours')==8760 else 'ENGINEERING_WINDOW_ONLY',
        alignment='grid_uid x technology; application must perform an exact one-to-one join')
    if a.reference_screen:
        if identity['source'].get('scenario_id')!='base':
            raise ValueError('Base self-check requires a Base source archive')
        reference=read_table(a.reference_screen)
        lookup={(v['grid_uid'],v['technology']):v for v in reference}
        if set(lookup)!={(v['grid_uid'],v['technology']) for v in prices}:
            raise ValueError('Reference screen identities differ')
        errors=[];terms=[];selected=0
        for v in prices:
            old=lookup[(v['grid_uid'],v['technology'])]
            errors.append(abs(v['rc_build']-finite(old['rc_build'])))
            if not math.isclose(v['rc_build'],finite(old['rc_build']),abs_tol=1e-8,rel_tol=1e-10):
                raise ValueError('Base reduced cost differs from independent source screen')
            if finite(old['rc_ratio'])>=a.margin and v['headroom_gw']>0:
                selected+=1;terms.append(v['headroom_gw']*max(-v['rc_build'],0.))
        result['base_archive_self_check']=dict(reference_sha256=sha256(a.reference_screen),
            maximum_rc_difference=max(errors),selected_columns=selected,
            B_million_cny=math.fsum(terms),passed=math.fsum(terms)<=1e-8,
            definition='Original preselected Base columns; independent full-MPS repricing, no original bound change')
    assert hashes=={str(x):sha256(x) for x in paths}
    (out/'screen_identity.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(sites=result['sites'],excluded_sites=result['excluded_sites'],output=str(out))))


if __name__=='__main__':main()
