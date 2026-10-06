"""Record the final local candidate, exact evidence and unresolved full-year gate."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    paths=['cispo_model/numerical_cleanup.py','cispo_model/monolithic.py','cispo_model/config.py',
        'config/optimization_2030_spill_tightened_v3.json','scripts/probe_full_year_numerics.py',
        'tests/test_reservoir_spill_reduction.py','CODEX_HANDOFF.md','MODEL_SERVER_STATUS.md',
        'SERVER_RUNBOOK.md','cispo_full_lp_model_spec.md']
    patch=subprocess.check_output(['git','diff','--',*paths],cwd=ROOT)
    (HERE/'tracked_diff_including_previous_work.patch').write_bytes(patch)
    trials={}
    for hours in [24,168]:
        d=json.loads((HERE/f'probes/cleaned_nf2_{hours}h_s0_cross2_annual_bounds_spill/result.json').read_text())
        trials[str(hours)]={k:d[k] for k in ['status','runtime','barrier_iterations','objective',
            'raw_max_row_violation','bound_violation','dual_violation','strict_acceptance']}
    record=dict(generated_at=datetime.now(timezone.utc).isoformat(),
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),git_commit_created=False,
        local_candidate='config/optimization_2030_spill_tightened_v3.json',
        physical_input_table='data/hydro/repaired_storage_audit_20260913_v2/hydro_stations.csv',
        changes_this_turn=paths,nationwide_8760_lp_built=False,nationwide_8760_lp_solved=False,
        nationwide_numerical_problem_certified_resolved=False,cloud_gate_submitted=False,
        cloud_scope_confirmation='REQUESTED_PENDING',
        annual_water=json.loads((HERE/'annual_spill_v3/summary.json').read_text()),
        annual_physical_qc=json.loads((HERE/'annual_physical_qc.json').read_text()),
        bound_reduction=json.loads((HERE/'annual_spill_v3/bound_reduction.json').read_text()),
        integrated_tests=trials,regression_tests=json.loads((HERE/'regression_tests.json').read_text()),
        source_files=[dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=digest(ROOT/p)) for p in paths],
        evidence=[dict(path=p.relative_to(HERE).as_posix(),bytes=p.stat().st_size,sha256=digest(p))
            for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json'
            and '__pycache__' not in p.parts],
        commands=[
            'python probe_annual_water.py --units water_scaled --output-dir annual_water --time-limit 60',
            'python probe_annual_water.py --units water_scaled --spill-reduction --output-dir annual_spill_v3 --time-limit 300',
            'python validate_annual_water.py',
            'python run_numeric_probe.py --case cleaned_nf2 --hours 24 --time-limit 180 --crossover 2 --annual-water-bounds --spill-reduction --tag _annual_bounds_spill',
            'python run_numeric_probe.py --case cleaned_nf2 --hours 168 --time-limit 1200 --crossover 2 --annual-water-bounds --spill-reduction --tag _annual_bounds_spill',
            'python scripts/probe_full_year_numerics.py --output-dir NEW_DIR --validate-inputs-only'],
        limitations=['Water diagnostics fix existing capacities and exclude national electricity/carbon/security constraints',
            'Integrated 24/168h tests retain annual water bounds but not full-year electricity constraints',
            'Concurrent local diagnostics invalidate simple wall-clock speedup claims',
            'No cloud deployment or job submission; old release and Thermal status queried read-only'])
    (HERE/'delivery_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:record[k] for k in ['git_head','nationwide_numerical_problem_certified_resolved','regression_tests','bound_reduction']},indent=2))


if __name__=='__main__':main()
