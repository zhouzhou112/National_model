"""Prepare a new R1 continuation-state capsule; no solver or archive mutation.

Input: --source OUTPUT --acceptance JSON --planning-year YEAR --output NEW_DIR.
Outputs: prepared_state/, source_capsule/ and evidence/ with cohort audits/SHA.
Retains retrofit-linked groups, zeros negative new-build tails, closes tiny
VRE/hydro headroom and shared biomass bounds using non-CCS new builds only.
All deletion ratio/quantity gates from the author 6b/6c rules remain active.
"""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,math,shutil,sys,io,struct
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from cispo_model.continuation_cleanup import assess
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
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True,help='Immutable source output with candidate state and semantic exports')
    parser.add_argument('--acceptance',type=Path,required=True,help='Separate author acceptance with source SHA identities')
    parser.add_argument('--planning-year',type=int,required=True,choices=[2040,2050,2060])
    parser.add_argument('--source-scenario',default='base')
    parser.add_argument('--author-decision-label',default='ACCEPTED_RELATIVE_V1_20261012',
        help='Exact separately recorded author adoption label; future acceptance dates must be explicit')
    parser.add_argument('--config',type=Path,default=ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reproduce-gzip-header-from',type=Path,help='Optional historical gzip header for byte-exact regression; never changes cohort values')
    args=parser.parse_args()
    source=args.source.resolve();acceptance=args.acceptance.resolve()
    assert not args.output.exists(),'Never overwrite a derivative or failed run'
    assert not args.output.resolve().is_relative_to(source),'Output must be outside immutable source'
    args.output.mkdir(parents=True);evidence_dir=args.output/'evidence';evidence_dir.mkdir()
    accepted=json.loads(acceptance.read_text(encoding='utf-8'))
    accepted_hashes=accepted['source_evidence']['source_sha256']
    assert sha(source/'result_manifest.json')==accepted_hashes['result_manifest.json']
    manifest=json.loads((source/'result_manifest.json').read_text(encoding='utf-8'))
    source_hashes={item['path']:item['sha256'] for item in manifest['files']}
    source_hashes.update(accepted_hashes)
    metadata_source=json.loads((source/'planning_state_candidate/state_metadata.json').read_text(encoding='utf-8'))
    source_year=int(metadata_source['planning_year']);planning_year=args.planning_year
    assert source_year+10==planning_year,'R1 requires the preceding ten-year planning state'
    assert args.author_decision_label.startswith('ACCEPTED_')
    assert accepted['author_decision']==args.author_decision_label
    gate,cohorts,delete,negative=assess(source,planning_year=planning_year,source_year=source_year)
    save(evidence_dir/'cleanup_gate.json',gate)
    pd.DataFrame(gate['by_technology']).to_csv(evidence_dir/'deletion_by_technology.csv',index=False)
    pd.DataFrame(gate['retrofit_protected_groups']).to_csv(evidence_dir/'retrofit_protected_groups.csv',index=False)
    assert gate['status']=='PASS','R1 quantity/ratio gate failed; source unchanged, see evidence'
    for name,digest in gate['source_sha256'].items():
        assert digest==source_hashes[name], 'Source evidence SHA mismatch: '+name
    # A compact, explicitly derived capsule preserves original bytes while its
    # own manifest enumerates only copied state dependencies. Original full
    # output manifest remains separate and SHA-linked; never edit evidence.
    capsule=args.output/'source_capsule'
    if not capsule.exists():
        capsule.mkdir()
        for name in ['solution_qc.json','solve_report.json','run_identity.json',
                     'planning_state_candidate/state_metadata.json',
                     'planning_state_candidate/capacity_cohorts.csv.gz',
                     'planning_state_candidate/state_transition_summary.csv']:
            old=source/name;new=capsule/name;new.parent.mkdir(exist_ok=True)
            assert sha(old)==source_hashes[name], 'State dependency SHA mismatch: '+name
            shutil.copy2(old,new)
        shutil.copy2(source/'result_manifest.json',capsule/'original_result_manifest.json')
        save(capsule/'result_manifest.json',dict(manifest_purpose='BYTE_IDENTICAL_STATE_DEPENDENCY_CAPSULE',
            source_manifest_sha256=sha(source/'result_manifest.json'),files=[dict(path=p.relative_to(capsule).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(capsule.rglob('*')) if p.is_file()]))
    original=PlanningState.load(capsule/'planning_state_candidate',expected_boundary_year=source_year,
        expected_scenario_id=args.source_scenario,allow_unaccepted_candidate=True)
    pd.testing.assert_frame_equal(cohorts,original.cohorts,check_dtype=False)
    target=args.output/'prepared_state'
    cfg=load_model_config(args.config).for_planning_year(planning_year)
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
        before=original.active_adjustment(family,ids,planning_year=planning_year,unit='GW')
        inherited=working.active_adjustment(family,ids,planning_year=planning_year,unit='GW')
        floor=base+inherited
        if family=='vre':floor[(floor>0)&(floor<1e-5)]=0
        if (floor < -1e-9).any():raise RuntimeError('Negative inherited floor beyond authorized cleanup: '+family)
        bad=np.where(floor>upper)[0]
        for i in bad:
            needed=float(floor[i]-upper[i])
            if needed>=1e-5:raise RuntimeError('New bound-close excess >=1e-5 GW: '+ids[i])
            selected=clean.asset_class.eq(family)&clean.asset_id.eq(ids[i])&clean.build_year.le(planning_year)&clean.retire_year.gt(planning_year)
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
        after=working.active_adjustment(family,ids,planning_year=planning_year,unit='GW')
        effective=base+after
        if family=='vre':effective[(effective>0)&(effective<1e-5)]=0
        if (effective>upper+1e-12).any():raise RuntimeError('Bound-close residual exceeds tolerance')
        bound_tables[family]=pd.DataFrame(dict(asset_id=ids,exogenous_floor_gw=base,upper_gw=upper,
            original_inherited_gw=before,original_headroom_gw=upper-base-before,
            after_deletion_inherited_gw=inherited,after_deletion_excess_gw=np.maximum(floor-upper,0),
            prepared_inherited_gw=after,prepared_headroom_gw=upper-effective))
    shared_closures=[]
    thermal=data.thermal_floor.set_index(['province_code','technology'])
    all_thermal_ids=sorted(set(clean.loc[clean.asset_class.eq('thermal'),'asset_id']) |
        {stable_asset_id(p,t) for p,t in thermal.index})
    for bound in data.biomass_capacity_bounds.itertuples(index=False):
        province=int(bound.province_code);upper=float(bound.capacity_upper_gw)
        ids=[stable_asset_id(province,t) for t in ['bio','bioccs']]
        positions=[all_thermal_ids.index(i) for i in ids]
        def inherited_pair():
            return working.active_adjustment('thermal',all_thermal_ids,planning_year=planning_year,unit='GW')[positions]
        exo=np.array([float(thermal.loc[(province,t),'capacity_floor_gw']) for t in ['bio','bioccs']])
        before=exo+inherited_pair();excess=float(before.sum()-upper)
        if excess<=0:continue
        if excess>=1e-5:raise RuntimeError('Shared biomass excess outside R1 bound-close: '+str(province))
        snapshot=clean.copy(deep=True)
        allowed=clean.asset_class.eq('thermal')&clean.asset_id.eq(ids[0])&clean.technology.eq('bio')&clean.action.eq('new_build')&clean.unit.eq('GW')&clean.build_year.le(planning_year)&clean.retire_year.gt(planning_year)&clean.capacity_delta.gt(0)
        left=excess+max(0,upper-math.nextafter(upper,-math.inf));changes=[]
        for index in clean.loc[allowed].sort_values('build_year',kind='stable').index:
            if left<=0:break
            old=float(clean.at[index,'capacity_delta']);new=max(0.,math.nextafter(old-min(old,left),-math.inf))
            clean.at[index,'capacity_delta']=new;left-=old-new
            row=dict(asset_class='thermal',asset_id=ids[0],technology='bio',build_year=int(clean.at[index,'build_year']),before_gw=old,after_gw=new,reduction_gw=old-new,original_excess_gw=excess,reason='AUTHOR_R1_NON_CCS_NEW_BUILD_SHARED_BOUND_CLOSE')
            touched.append(row);changes.append(row)
        after=exo+inherited_pair()
        if not (left<1e-12 and after.sum()<=upper+1e-12 and after[0]>=0):
            raise RuntimeError('Insufficient non-CCS new builds for shared bound closure')
        assert after[1]==before[1]
        pd.testing.assert_frame_equal(snapshot.loc[~allowed],clean.loc[~allowed],check_exact=True)
        shared_closures.append(dict(province_code=province,shared_upper_gw=upper,before_floor_gw=before.tolist(),after_floor_gw=after.tolist(),initial_excess_gw=excess,total_reduction_gw=math.fsum(r['reduction_gw'] for r in changes),retrofit_pairs_unchanged=True,ccs_capacity_unchanged=True,affected_rows=changes))
    save(evidence_dir/'shared_biomass_bound_closure.json',shared_closures)
    target.mkdir();state=target/'planning_state_candidate';state.mkdir()
    for name in ['solution_qc.json','solve_report.json','run_identity.json']:
        shutil.copy2(source/name,target/name)
    shutil.copy2(source/'result_manifest.json',target/'original_result_manifest.json')
    shutil.copy2(acceptance,target/'acceptance_relative_v1.json')
    # Preserve the exact original text of every untouched cohort (especially
    # retrofit pairs). A pandas float CSV round trip can change a last bit.
    with gzip.open(source/'planning_state_candidate/capacity_cohorts.csv.gz','rt',encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle);fields=reader.fieldnames;records=list(reader)
    retained=[]
    for index,record in enumerate(records):
        if bool(delete.iloc[index]):continue
        if float(clean.at[index,'capacity_delta'])!=float(cohorts.at[index,'capacity_delta']):
            record['capacity_delta']=repr(float(clean.at[index,'capacity_delta']))
        retained.append(record)
    text=io.StringIO(newline='')
    writer=csv.DictWriter(text,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(retained)
    mtime=0
    if args.reproduce_gzip_header_from:
        with args.reproduce_gzip_header_from.open('rb') as handle:header=handle.read(10)
        assert header[:3]==b'\x1f\x8b\x08'
        mtime=struct.unpack('<I',header[4:8])[0]
    with (state/'capacity_cohorts.csv.gz').open('wb') as handle:
        with gzip.GzipFile(filename='capacity_cohorts.csv',mode='wb',fileobj=handle,mtime=mtime) as compressed:
            compressed.write(text.getvalue().encode('utf-8'))
            # Match gzip.open(..., 'wt') used by the historical writer:
            # TextIOWrapper flushes Z_SYNC_FLUSH before the gzip footer.
            compressed.flush()
    active=clean[clean.build_year.le(source_year)&clean.retire_year.gt(source_year)]
    summary=active.groupby(['asset_class','technology','unit','action'],dropna=False).agg(cohort_rows=('asset_id','size'),capacity_delta=('capacity_delta','sum')).reset_index()
    summary.insert(0,'active_planning_year',source_year);summary.to_csv(state/'state_transition_summary.csv',index=False)
    metadata=dict(original.metadata);metadata.pop('candidate_use_acknowledged',None)
    closure=dict(rule='OLDEST_POSITIVE_NEW_BUILD_FIRST_NEXTAFTER',threshold_gw=1e-5,affected_rows=touched,
        total_reduction_gw=math.fsum(r['reduction_gw'] for r in touched))
    closure['shared_biomass_upper']=shared_closures
    metadata.update(cohort_rows=len(clean),capacity_cohorts_sha256=sha(state/'capacity_cohorts.csv.gz'),
        state_transition_summary_sha256=sha(state/'state_transition_summary.csv'),
        continuation_cleanup=dict(gate,applied=True,state_changed=True),continuation_bound_closure=closure,
        acceptance_relative_v1_sha256=sha(acceptance),source_capacity_state_policy='AUTHOR_R1_CLEANED_BOUND_CLOSED_DERIVATIVE')
    save(state/'state_metadata.json',metadata)
    save(target/'bound_closure_audit.json',closure)
    for family,frame in bound_tables.items():frame.to_csv(evidence_dir/('state_bounds_'+family+'.csv'),index=False)
    audit=dict(source_capacity_cohorts_sha256=sha(source/'planning_state_candidate/capacity_cohorts.csv.gz'),
        source_state_metadata_sha256=sha(source/'planning_state_candidate/state_metadata.json'),
        acceptance_sha256=sha(acceptance),cohort_distribution=distribution,cleanup_gate=gate,bound_closure=closure,
        headroom={f:dict(original=bins(t.original_headroom_gw),prepared=bins(t.prepared_headroom_gw),
            after_deletion_overshoots=int(t.after_deletion_excess_gw.gt(0).sum())) for f,t in bound_tables.items()})
    save(evidence_dir/'state_structure_audit.json',audit)
    save(target/'result_manifest.json',dict(manifest_purpose='AUTHOR_R1_DERIVED_STATE_INTEGRITY',
        source_manifest_sha256=sha(source/'result_manifest.json'),files=[dict(path=p.relative_to(target).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(target.rglob('*')) if p.is_file()]))
    loaded=PlanningState.load(state,expected_boundary_year=source_year,expected_scenario_id=args.source_scenario,allow_unaccepted_candidate=True)
    assert len(loaded.cohorts)==len(clean)
    untouched=~delete&~negative
    for r in touched:untouched &= ~(cohorts.asset_class.eq(r['asset_class'])&cohorts.asset_id.eq(r['asset_id'])&cohorts.build_year.eq(r['build_year']))
    pd.testing.assert_frame_equal(cohorts.loc[untouched].reset_index(drop=True),clean.loc[untouched[~delete]].reset_index(drop=True),check_dtype=False)
    print(json.dumps(dict(status='PREPARED',cohort_rows=len(clean),bound_closed_rows=len(touched),bound_closed_gw=closure['total_reduction_gw'],source_unchanged=sha(source/'planning_state_candidate/capacity_cohorts.csv.gz')==gate['source_sha256']['planning_state_candidate/capacity_cohorts.csv.gz'])))

if __name__=='__main__':main()
