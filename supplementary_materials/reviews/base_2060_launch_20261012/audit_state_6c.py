"""Read-only comprehensive capacity-floor and retrofit audit after 6c build stop.

Reproduces the builder's GW stock guards without constructing or relaxing an LP.
Reports source versus derivative, active retrofit provenance and input SHA.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parents[2]))
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data,DATA_ROOT
from cispo_model.planning_state import PlanningState,stable_asset_id
from cispo_model.master import THERMAL_TECHS,STORAGE_TECHS
from prepare_state_6b import bins

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-in',type=Path,default=HERE/'upstream_2050_prepared_6c/planning_state_candidate')
    parser.add_argument('--output-dir',type=Path,default=HERE/'revision_6c')
    args=parser.parse_args();out=args.output_dir
    cfg=load_model_config(HERE.parents[2]/'config/optimization_numeric_dac_by_year_v9_a12.json').for_planning_year(2060)
    paths={k:HERE/v/'planning_state_candidate' for k,v in [('original','upstream_2050_source_capsule'),('prepared','upstream_2050_prepared_6c')]}
    paths['prepared']=args.state_in
    states={k:PlanningState.load(v,expected_boundary_year=2050,expected_scenario_id='base',allow_unaccepted_candidate=True) for k,v in paths.items()}
    data=load_model_data(cfg,planning_state=states['original']);provinces=data.province_codes.tolist()
    table=data.thermal_floor.pivot(index='province_code',columns='technology',values='capacity_floor_gw').reindex(index=provinces,columns=THERMAL_TECHS[:-1],fill_value=0.)
    nuclear=data.nuclear_floor.set_index('province_code').capacity_floor_gw.reindex(provinces).fillna(0.)
    base=np.column_stack([table.to_numpy(float),nuclear.to_numpy(float)])
    ids=[stable_asset_id(p,t) for p in provinces for t in THERMAL_TECHS]
    floors={k:base+s.active_adjustment('thermal',ids,planning_year=2060,unit='GW').reshape(base.shape) for k,s in states.items()}
    guards=[];biomass=[];cohort_evidence=[]
    for stage,state in states.items():
        f=floors[stage]
        guards.append(dict(stage=stage,family='thermal',negative_count=int((f<-1e-9).sum()),minimum_gw=float(f.min())))
        upper=data.nuclear_upper.set_index('province_code').capacity_upper_gw.reindex(provinces).to_numpy(float)
        delta=f[:,THERMAL_TECHS.index('nuclear')]-upper
        guards.append(dict(stage=stage,family='nuclear',over_upper_count=int((delta>1e-9).sum()),maximum_excess_gw=float(max(0,delta.max()))))
        upper=data.biomass_capacity_bounds.set_index('province_code').capacity_upper_gw.reindex(provinces).to_numpy(float)
        pair=f[:,THERMAL_TECHS.index('bio')]+f[:,THERMAL_TECHS.index('bioccs')]
        for i,p in enumerate(provinces):
            biomass.append(dict(stage=stage,province_code=p,bio_floor_gw=float(f[i,THERMAL_TECHS.index('bio')]),
                bioccs_floor_gw=float(f[i,THERMAL_TECHS.index('bioccs')]),shared_upper_gw=float(upper[i]),
                shared_floor_gw=float(pair[i]),excess_gw=float(max(0,pair[i]-upper[i])),fails=bool(pair[i]>upper[i]+1e-9)))
            if pair[i]>upper[i]+1e-9:
                c=state.cohorts
                c=c[c.asset_class.eq('thermal')&c.province_code.eq(p)&c.technology.isin(['bio','bioccs'])&c.build_year.le(2060)&c.retire_year.gt(2060)]
                for row in c.to_dict('records'):cohort_evidence.append(dict(stage=stage,**row))
        for family,asset_ids,exo,ub in [
            ('vre',[stable_asset_id(r.grid_uid,r.technology) for r in data.vre_sites.itertuples(index=False)],data.vre_sites.capacity_floor_gw.to_numpy(float),data.vre_sites.capacity_upper_gw.to_numpy(float)),
            ('hydro',data.hydro_stations.hydrochn_row_id.astype(str).tolist(),data.hydro_stations.existing_capacity_gw.to_numpy(float),data.hydro_stations.capacity_potential_gw.to_numpy(float))]:
            floor=exo+state.active_adjustment(family,asset_ids,planning_year=2060,unit='GW')
            if family=='vre':floor[(floor>0)&(floor<1e-5)]=0
            guards.append(dict(stage=stage,family=family,negative_count=int((floor<-1e-9).sum()),over_upper_count=int((floor>ub+1e-9).sum()),maximum_excess_gw=float(np.maximum(floor-ub,0).max()),headroom_bins=bins(ub-floor)))
        storage_ids=[stable_asset_id(p,t) for p in provinces for t in STORAGE_TECHS]
        exo=np.zeros((len(provinces),len(STORAGE_TECHS)));ub=np.full(exo.shape,np.inf)
        for j,t in enumerate(STORAGE_TECHS):
            bounds=(data.battery_bounds if t=='battery' else data.storage_bounds).set_index('province_code').reindex(provinces)
            exo[:,j]=bounds.capacity_floor_gw.to_numpy(float)
            if t=='phs':ub[:,j]=bounds.capacity_upper_gw.to_numpy(float)
        floor=exo+state.active_adjustment('storage',storage_ids,planning_year=2060,unit='GW').reshape(exo.shape)
        guards.append(dict(stage=stage,family='storage',negative_count=int((floor<-1e-9).sum()),over_upper_count=int((floor>ub+1e-9).sum()),maximum_excess_gw=float(np.maximum(floor-ub,0).max())))
        if data.wave is not None:
            wave=data.wave.sites;wave_ids=[stable_asset_id(v,'wave') for v in wave.grid_uid]
            floor=state.active_adjustment('wave',wave_ids,planning_year=2060,unit='GW')
            ub=wave.capacity_upper_gw.to_numpy(float)
            guards.append(dict(stage=stage,family='wave',negative_count=int((floor<-1e-9).sum()),over_upper_count=int((floor>ub+1e-9).sum()),maximum_excess_gw=float(np.maximum(floor-ub,0).max())))
    # Include original counterparts even where only the derivative fails.
    failed_provinces={r['province_code'] for r in biomass if r['fails']}
    cohort_evidence=[]
    for stage,state in states.items():
        c=state.cohorts
        selected=c[c.asset_class.eq('thermal')&c.province_code.isin(failed_provinces)&c.technology.isin(['bio','bioccs'])&c.build_year.le(2060)&c.retire_year.gt(2060)]
        for row in selected.to_dict('records'):cohort_evidence.append(dict(stage=stage,**row))
    # 2060 is the final planning year: retrofit survivor upper equals the
    # source technology's nonnegative 2060 floor before A2 cleanup.
    retrofit=[]
    pairs=[('coal','coalccs'),('cchp','cchpccs'),('gas','gasccs'),('gchp','gchpccs'),('bio','bioccs')]
    for source,target in pairs:
        values=np.maximum(floors['prepared'][:,THERMAL_TECHS.index(source)],0)
        for p,v in zip(provinces,values):retrofit.append(dict(province_code=p,source=source,target=target,original_upper_gw=float(v),a2_upper_gw=float(0 if 0<v<1e-5 else v)))
    c=states['original'].cohorts
    active=c[c.action.eq('retrofit_out')&c.build_year.le(2060)&c.retire_year.gt(2060)]
    protected=json.loads((out/'cleanup_gate.json').read_text())['retrofit_protected_groups']
    for r in protected:
        select=(c.asset_class.eq(r['asset_class'])&c.technology.eq(r['technology'])&c.asset_id.eq(r['asset_id']))
        surviving=c[select&c.build_year.le(2060)&c.retire_year.gt(2060)]
        r.update(new_build_active_2060_gw=math.fsum(surviving.loc[surviving.action.eq('new_build'),'capacity_delta']),
            active_retrofit_out_gw=math.fsum(surviving.loc[surviving.action.eq('retrofit_out'),'capacity_delta']))
    pd.DataFrame(protected).to_csv(out/'retrofit_protected_groups_detailed.csv',index=False)
    pd.DataFrame(biomass).to_csv(out/'biomass_shared_bound_audit.csv',index=False)
    pd.DataFrame(cohort_evidence).to_csv(out/'biomass_shared_bound_cohorts.csv',index=False)
    pd.DataFrame(retrofit).to_csv(out/'retrofit_upper_audit.csv',index=False)
    before=c[c.action.isin(['retrofit_in','retrofit_out'])].reset_index(drop=True)
    after=states['prepared'].cohorts;after=after[after.action.isin(['retrofit_in','retrofit_out'])].reset_index(drop=True)
    pd.testing.assert_frame_equal(before,after,check_exact=True)
    result=dict(status='STOP_AUTHOR_REVIEW_REQUIRED',trigger='Inherited biomass plus BECCS capacity exceeds shared upper',
        guard_tolerance_gw=1e-9,capacity_guards=guards,biomass_failures=[r for r in biomass if r['fails']],
        retrofit_pairs_unchanged=True,active_retrofit_out_rows=len(active),active_zero_retrofit_out_rows=int(active.capacity_delta.eq(0).sum()),
        protected_candidate_groups=len(protected),protected_positive_groups=sum(r['new_build_gw']>0 for r in protected),
        protected_new_build_all_cohorts_gw=math.fsum(r['new_build_gw'] for r in protected),protected_new_build_active_2060_gw=math.fsum(r['new_build_active_2060_gw'] for r in protected),
        retrofit_upper_bins={s:bins([r['a2_upper_gw'] for r in retrofit if r['source']==s]) for s,t in pairs},
        state_sha256={k:hashlib.sha256((p/'capacity_cohorts.csv.gz').read_bytes()).hexdigest() for k,p in paths.items()},no_optimization=True,no_submission=True)
    (out/'capacity_accounting_stop.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['capacity_guards','retrofit_upper_bins']},indent=2))
if __name__=='__main__':main()
