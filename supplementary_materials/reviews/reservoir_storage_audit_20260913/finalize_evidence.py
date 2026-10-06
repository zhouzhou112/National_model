"""Freeze the storage review queue and exact local delivery sources/hashes.

Run once after all audit outputs exist. Writes only this evidence directory.
The overlay includes earlier uncommitted prerequisites; it is not a Git commit.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def main():
    table=pd.read_csv(HERE/'original_vs_v2/reservoirs_620.csv')
    corrected=table.source_active_storage_m3.ne(table.selected_active_storage_m3)
    table['review_priority']=np.select([corrected,
        table.affine_volume_pattern & table.source_storage_exceeds_10annual_budgets,
        table.source_storage_exceeds_10annual_budgets,
        table.affine_volume_pattern | table.source_storage_exceeds_annual_budget],[0,1,1,2],default=3)
    table['review_status']=np.select([corrected,
        table.affine_volume_pattern & table.source_storage_exceeds_10annual_budgets,
        table.source_storage_exceeds_10annual_budgets,
        table.affine_volume_pattern,
        table.source_storage_exceeds_annual_budget],
        ['CORRECTED_FROM_ENGINEERING_SOURCE','CHECK_ESTIMATED_STORAGE_AND_WATER_MATCH',
         'CHECK_STORAGE_WATER_INCONSISTENCY_NOT_AUTOMATIC_STORAGE_ERROR',
         'CHECK_ESTIMATED_STORAGE_SOURCE','CYCLIC_BOUND_REDUCIBLE_NOT_PHYSICAL_CERTIFICATION'],
        default='NO_SELECTED_FLAG_NOT_ENGINEERING_CERTIFICATION')
    table.sort_values(['review_priority','source_storage_to_safe_annual_water'],ascending=[True,False]).to_csv(
        HERE/'storage_review_queue.csv',index=False)
    package=json.loads((ROOT/'config/model_data_config.json').read_text(encoding='utf-8-sig'))
    inventory=Path(package['sources']['hydro_updated_inventory'])
    stage2=Path(package['sources']['hydro_stage2'])
    upstream=[inventory.parents[1]/'scripts/run_hydro_phs_pipeline.py',
              stage2.parents[1]/'scripts/stage2_pipeline.py',ROOT/'scripts/build_cispo_data_package.py']
    snapshots=HERE/'sources/generation_scripts';snapshots.mkdir(exist_ok=False)
    for p in upstream:shutil.copyfile(p,snapshots/p.name)
    changed=['cispo_model/config.py','scripts/audit_reservoir_storage.py',
        'config/hydro_storage_corrections_20260913_v2.csv','config/optimization_2030_storage_audited_v2.json',
        'CODEX_HANDOFF.md','MODEL_SERVER_STATUS.md','SERVER_RUNBOOK.md','cispo_full_lp_model_spec.md']
    prerequisites=['cispo_model/numerical_cleanup.py','cispo_model/monolithic.py','cispo_model/hydro.py',
        'cispo_model/master.py','cispo_model/data.py','cispo_model/io_contract.py','cispo_model/run_contract.py',
        'scripts/prepare_hydro_storage_corrections.py','config/optimization_2030_numeric_repaired.json',
        'config/hydro_storage_corrections_20260913.csv','tests/test_numerical_cleanup.py']
    files=[ROOT/p for p in changed+prerequisites]
    for sub in ['data/hydro/repaired_storage_audit_20260913_v2','data/hydro/repaired_20260913']:
        files.extend(sorted((ROOT/sub).glob('*')))
    with tarfile.open(HERE/'storage_audit_source_overlay.tar.gz','w:gz') as archive:
        for p in files:archive.add(p,arcname=p.relative_to(ROOT).as_posix())
    diff=subprocess.check_output(['git','diff','--',*changed,*prerequisites],cwd=ROOT)
    (HERE/'current_tracked_diff.patch').write_bytes(diff)
    record=dict(generated_at=datetime.now(timezone.utc).isoformat(),
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        git_commit_created=False,changed_this_review=changed,previous_uncommitted_prerequisites=prerequisites,
        audit_complete=True,physical_input_globally_certified=False,
        full_year_national_lp_built=False,full_year_national_lp_solved=False,
        short_horizon_performance_improvement_proven=False,
        independent_8760_station_energy_checks=6,
        validation=json.loads((HERE/'validation.json').read_text()),
        tests=json.loads((HERE/'unit_test_summary.json').read_text()),
        review_queue_counts=table.review_status.value_counts().to_dict(),
        source_files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha256(p)) for p in files],
        evidence=[dict(path=p.relative_to(HERE).as_posix(),bytes=p.stat().st_size,sha256=sha256(p))
                  for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json'],
        commands=[
            'python scripts/audit_reservoir_storage.py --output-dir supplementary_materials/reviews/reservoir_storage_audit_20260913/original_vs_v1',
            'python scripts/audit_reservoir_storage.py --config config/optimization_2030_storage_audited_v2.json --output-dir supplementary_materials/reviews/reservoir_storage_audit_20260913/original_vs_v2',
            'python supplementary_materials/reviews/reservoir_storage_audit_20260913/audit_old_storage_solution.py',
            'python supplementary_materials/reviews/reservoir_storage_audit_20260913/compare_storage_horizons.py',
            'python supplementary_materials/reviews/reservoir_storage_audit_20260913/check_storage_generation_budget.py',
            'python supplementary_materials/reviews/reservoir_storage_audit_20260913/run_storage_probe.py --case cleaned_nf2 --hours 24 --time-limit 180 --crossover 2 --tag _storage_v2'],
        runtime='Windows RL Python 3.10 with existing Gurobi 13.0.2 overlay and CISPO_WAVE_ROOT; PDF read/render uses bundled runtime',
        server_actions='Read-only SCP of old archived reservoir_dispatch.npz; no job submission or remote mutation')
    (HERE/'delivery_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:record[k] for k in ['git_head','audit_complete','tests','review_queue_counts']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
