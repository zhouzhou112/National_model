"""Offline terminal audit: python analyze.py. Reads frozen JSON/logs only.
Writes summary.json; verifies source SHA and complete Barrier iterations.
No SSH, model modifications, solver calls or job submissions.
"""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json

HERE=Path(__file__).resolve().parent

def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))

def main():
    scheduler=read('scheduler.json'); terminal=read('terminal_scheduler.json')
    for evidence in [scheduler, terminal]:
        for rel, expected in evidence['source_sha256'].items():
            assert hashlib.sha256((HERE/rel.replace('/','__')).read_bytes()).hexdigest()==expected, rel
    spec=importlib.util.spec_from_file_location('eta',HERE.parent.parent/'convergence_eta_20261004/estimate.py')
    eta=importlib.util.module_from_spec(spec);spec.loader.exec_module(eta)
    rows=eta.parse(HERE/'output_8760__gurobi.log')
    assert [r['iteration'] for r in rows]==list(range(rows[-1]['iteration']+1))
    report=read('output_8760__solve_report.json');qc=read('output_8760__solution_qc.json')
    preservation=read('output_8760__preservation_report.json');dual=read('dual_export_status.json')
    previous=read('../status_20261011T144319Z/summary.json')
    assert report['status']=='OPTIMAL' and rows[-1]['iteration']==report['iteration_counts']['barrier']==716
    assert preservation['status']=='COMPLETE' and not preservation['errors']
    assert all(v=='COMPLETE' for v in preservation['stages'].values())
    lines=terminal['accounting_terminal'].splitlines(); headers=lines[0].split('|')
    job=next(dict(zip(headers,line.split('|'))) for line in lines[1:] if line.split('|')[0]=='4844528')
    assert job['State']=='COMPLETED' and job['ExitCode']=='0:0'
    beijing=dt.timezone(dt.timedelta(hours=8));uk=dt.timezone(dt.timedelta(hours=1))
    end=dt.datetime.fromisoformat(job['End']).replace(tzinfo=beijing)
    closure=abs(qc['objective_component_residual_million_cny'])/max(abs(report['objective_value_million_cny']),1e-30)
    opposing=qc['interprovincial_directionality_assessment']['observed']['opposing_share_of_gross_flow']
    metrics=['pinf','dinf','compl','absolute_objective_difference']
    result=dict(collected_at_server=scheduler['collected_at'],collected_at_uk=dt.datetime.fromisoformat(scheduler['collected_at']).astimezone(uk).isoformat(),
        slurm=job,completed_at_uk=end.astimezone(uk).isoformat(),completed_at_beijing=end.isoformat(),
        source_sha256_verified=True,verified_source_files=sum(len(x['source_sha256']) for x in [scheduler,terminal]),
        iteration_count=len(rows),last_log=rows[-1],previous_log=previous['last_log'],
        reduction_percent_since_682={m:100*(1-rows[-1][m]/previous['last_log'][m]) for m in metrics},
        solver_status=report['status'],solver_runtime_seconds=report['runtime_seconds'],solver_runtime_days=report['runtime_seconds']/86400,
        objective_value_million_cny=report['objective_value_million_cny'],solution_quality=report['solution_quality'],
        terminal_barrier_callback=preservation['solver_contract']['barrier_primal_dual_metrics'],
        preservation_status=preservation['status'],preservation_errors=preservation['errors'],preservation_stages=preservation['stages'],
        original_qc_status=qc['status'],original_failed_hard_checks=[k for k,v in qc['hard_checks'].items() if not v],
        original_acceptance_policy=qc['solver_contract']['acceptance_policy'],
        original_scientifically_accepted=qc['scientifically_accepted'],author_decision=preservation['author_decision'],
        relative_v1_review=dict(formal_profile_present_in_archived_qc='acceptance_profile' in qc,full_reassessment_complete=False,
            power_balance_pass_by_minimum_floor=qc['maximum_power_balance_residual_gw']<=0.001,
            maximum_power_balance_residual_gw=qc['maximum_power_balance_residual_gw'],
            objective_closure_relative=closure,objective_closure_pass=closure<=1e-7,
            opposing_share_of_gross_flow=opposing,opposing_threshold=1e-4,opposing_pass_under_archived_gross_flow_definition=opposing<=1e-4,
            opposing_energy_gwh=qc['total_bidirectional_minimum_flow_gwh'],excess_loss_gwh=qc['interprovincial_directionality_assessment']['observed']['excess_loss_gwh'],
            reservoir_max_residual_m3=qc['maximum_reservoir_transition_residual_m3'],reservoir_pass=None,
            reservoir_missing_evidence='station-level residuals and active storage denominators',
            overall='NOT_PASSED_PENDING_FULL_REASSESSMENT'),
        dual_export_available=dual['available'],dual_attribute=dual['dual_attribute'],dual_hourly_rows=dual['hourly_rows'],dual_annual_rows=dual['annual_rows'],
        maximum_power_balance_residual_kw=qc['maximum_power_balance_residual_gw']*1e6,
        annual_net_emissions_mtco2=qc['annual_net_emissions_mtco2'],carbon_limit_mtco2=qc['carbon_limit_mtco2'],
        stderr_bytes={n:(HERE/n).stat().st_size for n in ['stderr.log','slurm-4844528.err']},
        output_catalog_json_exists='output_catalog.json' not in terminal['missing_files'],
        note='squeue invalid job ID and sstat no live step are consistent with completed accounting; no source artifacts changed')
    (HERE/'summary.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
