"""Reproduce the preliminary 2030 comparison and 2040 readiness review.

Consumes SHA-verified small result files collected by collect_comparison_20261019.py.
No optimization, state mutation, scientific adoption, or scheduler action.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from cispo_model.continuation_cleanup import assess

ROOT=Path(__file__).parent/'comparison_20261019'
def read(label,name): return json.loads((ROOT/label/name).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    gate,_,_,_=assess(ROOT/'case3',planning_year=2040,source_year=2030)
    gatepath=ROOT/'r1_cleanup_precheck.json'
    if gatepath.exists():
        assert json.loads(gatepath.read_text())==gate
    else:
        gatepath.write_text(json.dumps(gate,indent=2)+'\n')
    verify={}
    for label in ('base','case3'):
        manifest={v['path']:v['sha256'] for v in read(label,'result_manifest.json')['files']}
        checks={}
        for collection in [ROOT/(label+'_collection.json'), ROOT/(label+'_r1_collection.json')]:
            if not collection.exists():continue
            for name,meta in json.loads(collection.read_text())['files'].items():
                if not meta.get('verified'):continue
                digest=sha(ROOT/label/name)
                assert digest==meta['sha256'],name
                if name in manifest: assert digest==manifest[name],name
                checks[name]={'sha256':digest,'matches_remote':True,'in_result_manifest':name in manifest}
        verify[label]=checks
    summaries={v:read(v,'annual_summary.json') for v in ('base','case3')}
    solve={v:read(v,'solve_report.json') for v in summaries}
    for v in summaries:
        assert summaries[v]['planning_year']==2030 and summaries[v]['optimization_hours']==8760
        assert solve[v]['status']=='OPTIMAL'
    assert abs(summaries['base']['period_baseline_load_gwh']-summaries['case3']['period_baseline_load_gwh'])<1e-6
    rows=[]
    def add(metric,unit,b,c):rows.append(dict(metric=metric,unit=unit,base=b,case3=c,delta_case3_minus_base=c-b))
    for key,unit,factor in [('objective_million_cny_per_year','100million_CNY/year',.01),
        ('period_effective_peak_load_gw','GW',1),('period_vre_curtailment_gwh','TWh',.001),
        ('period_storage_discharge_gwh','TWh',.001),('period_load_gwh','TWh',.001)]:
        add(key,unit,*[summaries[v][key]*factor for v in summaries])
    frames={v:pd.read_csv(ROOT/v/'annual_capacity_by_technology.csv').set_index('technology') for v in summaries}
    for t in frames['base'].index:
        add('capacity_'+t,'GW',*[frames[v].loc[t,'capacity'] for v in summaries])
    for v in summaries:
        storage=pd.read_csv(ROOT/v/'storage_capacity.csv')
        frames[v]=storage.groupby('technology').energy_capacity_gwh.sum()
    for t in frames['base'].index:add('storage_energy_'+t,'GWh',*[frames[v][t] for v in summaries])
    add('annual_net_emissions','MtCO2',*[read(v,'annual_carbon_ccs.json')['annual_net_emissions_mtco2'] for v in summaries])
    pd.DataFrame(rows).to_csv(ROOT/'comparison_metrics.csv',index=False)
    costs={v:pd.read_csv(ROOT/v/'cost_components.csv').set_index('cost_component').value_million_cny_per_year for v in summaries}
    costdiff=pd.concat(costs,axis=1).fillna(0)
    costdiff['delta_case3_minus_base']=costdiff.case3-costdiff.base
    costdiff.to_csv(ROOT/'cost_component_comparison.csv')
    metrics={v:solve[v]['solution_contract']['barrier_primal_dual_metrics'] for v in summaries}
    pb,px=[summaries[v]['objective_million_cny_per_year'] for v in summaries]
    db,dx=[metrics[v]['dual_objective'] for v in summaries]
    flex=pd.read_csv(ROOT/'case3/annual_flexible_load_by_province.csv')
    fields=[k for k in flex.columns if k.startswith(('contracted_','firm_'))]+['ev_mobility_v1g_relocated_gwh','ev_mobility_discharge_gwh']
    flexsum={k:float(flex[k].sum()) for k in fields}
    qc={v:read(v,'solution_qc.json') for v in summaries}
    result=dict(status='PRELIMINARY_COMPARISON_2040_NOT_READY',source_verification=verify,
        point_saving_100million_cny=(pb-px)/100,point_saving_percent=(pb-px)/pb*100,
        saving_interval_100million_cny=dict(lower=(db-px)/100,upper_without_B=(pb-dx)/100,
            upper_formula='upper_without_B + B_million_cny/100',B_status='PENDING_ORIGINAL_ARCHIVE_TRANSFER_AND_PRICING'),
        re_solve_threshold_B_million_cny=px*1e-4,flexible_load_totals=flexsum,
        qc={v:dict(status=json.loads((ROOT/(v+'_relative_extended.json')).read_text())['acceptance_profiles']['relative_v1']['status'],
            strict_failures=[k for k,val in qc[v]['hard_checks'].items() if not val],
            barrier_metrics=metrics[v]) for v in summaries},
        readiness=dict(relative_v1_extended='PASS',preservation=read('case3','preservation_report.json').get('status'),
            R1_quantity_precheck=gate['status'],pricing_certificate='PENDING',author_adoption='PENDING',
            R1_prepared_state='NOT_CREATED',gates_2040='NOT_RUN',release_2040='NOT_CREATED',job_2040='NOT_SUBMITTED'),
        scope='8760h, 31 provinces; capacity GW, energy GWh; annual system cost; no planning extrapolation from short windows')
    (ROOT/'comparison_summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','point_saving_100million_cny','point_saving_percent','saving_interval_100million_cny','readiness']}))

if __name__=='__main__':main()
