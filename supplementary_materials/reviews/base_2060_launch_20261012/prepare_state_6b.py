"""Prepare an immutable 2050->2060 derivative under author task section 6b.

Run with the project Python/data environment. Inputs are SHA-verified original
2050 candidate and formal acceptance; output is upstream_2050_prepared. Refuses
overwrite. All source files and non-new-build/non-GW cohorts remain unchanged.
"""
from pathlib import Path
import hashlib,json,math,shutil,sys
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from audit_cleanup_6b import assess
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.planning_state import PlanningState,stable_asset_id

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def bins(values):
    a=np.asarray(values,float); edges=[0,1e-6,1e-5,1e-4,1e-3,float('inf')]
    return [dict(lower_gw=l,upper_gw=None if math.isinf(u) else u,count=int(((a>l)&(a<=u)).sum()),
                 sum_gw=float(a[(a>l)&(a<=u)].sum())) for l,u in zip(edges[:-1],edges[1:])]

def main():
    source=HERE.parent/'base_acceptance_relative_v1_20261012/evidence/2050'
    acceptance=HERE.parent/'base_acceptance_relative_v1_20261012/assessments/2050/acceptance_relative_v1.json'
    accepted=json.loads(acceptance.read_text())
    assert accepted['author_decision']=='ACCEPTED_RELATIVE_V1_20261012'
    gate,cohorts,delete,negative=assess(source)
    assert gate['status']=='PASS'
    # A compact, explicitly derived capsule preserves original bytes while its
    # own manifest enumerates only copied state dependencies. Original full
    # output manifest remains separate and SHA-linked; never edit evidence.
    capsule=HERE/'upstream_2050_source_capsule'
    if not capsule.exists():
        capsule.mkdir()
        for name in ['solution_qc.json','solve_report.json','run_identity.json',
                     'planning_state_candidate/state_metadata.json',
                     'planning_state_candidate/capacity_cohorts.csv.gz',
                     'planning_state_candidate/state_transition_summary.csv']:
            old=source/name;new=capsule/name;new.parent.mkdir(exist_ok=True)
            assert sha(old)==accepted['source_evidence']['source_sha256'].get(name,sha(old))
            shutil.copy2(old,new)
        shutil.copy2(source/'result_manifest.json',capsule/'original_result_manifest.json')
        save(capsule/'result_manifest.json',dict(manifest_purpose='BYTE_IDENTICAL_STATE_DEPENDENCY_CAPSULE',
            source_manifest_sha256=sha(source/'result_manifest.json'),files=[dict(path=p.relative_to(capsule).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(capsule.rglob('*')) if p.is_file()]))
    original=PlanningState.load(capsule/'planning_state_candidate',expected_boundary_year=2050,
        expected_scenario_id='base',allow_unaccepted_candidate=True)
    pd.testing.assert_frame_equal(cohorts,original.cohorts,check_dtype=False)
    target=HERE/'upstream_2050_prepared';assert not target.exists(),'Never overwrite prepared state'
    cfg=load_model_config(ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json').for_planning_year(2060)
    data=load_model_data(cfg,planning_state=original)
    clean=cohorts.loc[~delete].copy();clean.loc[negative[~delete],'capacity_delta']=0.0
    working=PlanningState(None,dict(original.metadata),clean)
    groups=cohorts[cohorts.unit.eq('GW')].groupby(['asset_class','technology','action','asset_id'],dropna=False).capacity_delta.agg(math.fsum)
    distribution=[dict(asset_class=a,technology=t,action=action,bins=bins(v),
        nonpositive_assets=int(v.le(0).sum()),nonpositive_sum_gw=float(v[v.le(0)].sum()))
        for (a,t,action),v in groups.groupby(level=[0,1,2])]
    touched=[];bound_tables={}
    for family,ids,base,upper in [
        ('vre',[stable_asset_id(r.grid_uid,r.technology) for r in data.vre_sites.itertuples(index=False)],
         data.vre_sites.capacity_floor_gw.to_numpy(float),data.vre_sites.capacity_upper_gw.to_numpy(float)),
        ('hydro',data.hydro_stations.hydrochn_row_id.astype(str).tolist(),
         data.hydro_stations.existing_capacity_gw.to_numpy(float),data.hydro_stations.capacity_potential_gw.to_numpy(float))]:
        before=original.active_adjustment(family,ids,planning_year=2060,unit='GW')
        inherited=working.active_adjustment(family,ids,planning_year=2060,unit='GW')
        floor=base+inherited
        if family=='vre':floor[(floor>0)&(floor<1e-5)]=0
        if (floor < -1e-9).any():raise RuntimeError('Negative inherited floor beyond authorized cleanup: '+family)
        bad=np.where(floor>upper)[0]
        for i in bad:
            needed=float(floor[i]-upper[i])
            if needed>=1e-5:raise RuntimeError('New bound-close excess >=1e-5 GW: '+ids[i])
            selected=clean.asset_class.eq(family)&clean.asset_id.eq(ids[i])&clean.build_year.le(2060)&clean.retire_year.gt(2060)
            allowed=selected&clean.unit.eq('GW')&clean.action.eq('new_build')&clean.capacity_delta.gt(0)
            left=needed+max(0,float(upper[i]-math.nextafter(upper[i],-math.inf)))
            for index in clean.loc[allowed].sort_values('build_year',kind='stable').index:
                if left<=0:break
                old=float(clean.at[index,'capacity_delta'])
                new=max(0.,math.nextafter(old-min(old,left),-math.inf))
                clean.at[index,'capacity_delta']=new;left-=old-new
                touched.append(dict(asset_class=family,asset_id=ids[i],build_year=int(clean.at[index,'build_year']),
                    before_gw=old,after_gw=new,reduction_gw=old-new,original_excess_gw=needed))
            if left>1e-12:raise RuntimeError('Insufficient positive new cohorts for closure')
        after=working.active_adjustment(family,ids,planning_year=2060,unit='GW')
        effective=base+after
        if family=='vre':effective[(effective>0)&(effective<1e-5)]=0
        if (effective>upper+1e-12).any():raise RuntimeError('Bound-close residual exceeds tolerance')
        bound_tables[family]=pd.DataFrame(dict(asset_id=ids,exogenous_floor_gw=base,upper_gw=upper,
            original_inherited_gw=before,original_headroom_gw=upper-base-before,
            after_deletion_inherited_gw=inherited,after_deletion_excess_gw=np.maximum(floor-upper,0),
            prepared_inherited_gw=after,prepared_headroom_gw=upper-effective))
    target.mkdir();state=target/'planning_state_candidate';state.mkdir()
    for name in ['solution_qc.json','solve_report.json','run_identity.json']:
        shutil.copy2(source/name,target/name)
    shutil.copy2(source/'result_manifest.json',target/'original_result_manifest.json')
    shutil.copy2(acceptance,target/'acceptance_relative_v1.json')
    clean.to_csv(state/'capacity_cohorts.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    active=clean[clean.build_year.le(2050)&clean.retire_year.gt(2050)]
    summary=active.groupby(['asset_class','technology','unit','action'],dropna=False).agg(cohort_rows=('asset_id','size'),capacity_delta=('capacity_delta','sum')).reset_index()
    summary.insert(0,'active_planning_year',2050);summary.to_csv(state/'state_transition_summary.csv',index=False)
    metadata=dict(original.metadata);metadata.pop('candidate_use_acknowledged',None)
    closure=dict(rule='OLDEST_POSITIVE_NEW_BUILD_FIRST_NEXTAFTER',threshold_gw=1e-5,affected_rows=touched,
        total_reduction_gw=math.fsum(r['reduction_gw'] for r in touched))
    metadata.update(cohort_rows=len(clean),capacity_cohorts_sha256=sha(state/'capacity_cohorts.csv.gz'),
        state_transition_summary_sha256=sha(state/'state_transition_summary.csv'),
        continuation_cleanup=gate,continuation_bound_closure=closure,
        acceptance_relative_v1_sha256=sha(acceptance),source_capacity_state_policy='AUTHOR_6B_CLEANED_BOUND_CLOSED_DERIVATIVE')
    save(state/'state_metadata.json',metadata)
    save(target/'bound_closure_audit.json',closure)
    for family,frame in bound_tables.items():frame.to_csv(HERE/('state_bounds_'+family+'.csv'),index=False)
    audit=dict(source_capacity_cohorts_sha256=sha(source/'planning_state_candidate/capacity_cohorts.csv.gz'),
        source_state_metadata_sha256=sha(source/'planning_state_candidate/state_metadata.json'),
        acceptance_sha256=sha(acceptance),cohort_distribution=distribution,cleanup_gate=gate,bound_closure=closure,
        headroom={f:dict(original=bins(t.original_headroom_gw),prepared=bins(t.prepared_headroom_gw),
            after_deletion_overshoots=int(t.after_deletion_excess_gw.gt(0).sum())) for f,t in bound_tables.items()})
    save(HERE/'revision_6b/state_structure_audit.json',audit)
    save(target/'result_manifest.json',dict(manifest_purpose='AUTHOR_6B_DERIVED_STATE_INTEGRITY',
        source_manifest_sha256=sha(source/'result_manifest.json'),files=[dict(path=p.relative_to(target).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(target.rglob('*')) if p.is_file()]))
    loaded=PlanningState.load(state,expected_boundary_year=2050,expected_scenario_id='base',allow_unaccepted_candidate=True)
    assert len(loaded.cohorts)==len(clean)
    untouched=~delete&~negative
    for r in touched:untouched &= ~(cohorts.asset_class.eq(r['asset_class'])&cohorts.asset_id.eq(r['asset_id'])&cohorts.build_year.eq(r['build_year']))
    pd.testing.assert_frame_equal(cohorts.loc[untouched].reset_index(drop=True),clean.loc[untouched[~delete]].reset_index(drop=True),check_dtype=False)
    print(json.dumps(dict(status='PREPARED',cohort_rows=len(clean),bound_closed_rows=len(touched),bound_closed_gw=closure['total_reduction_gw'],source_unchanged=sha(source/'planning_state_candidate/capacity_cohorts.csv.gz')==gate['source_sha256']['planning_state_candidate/capacity_cohorts.csv.gz'])))

if __name__=='__main__':main()
