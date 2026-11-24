"""Freeze this completed local audit; verify evidence/package hashes, never submit jobs.

Run only after all probes have completed and the handoff documents are final.
Writes comparison.json/csv, source_snapshot, tracked_repair_changes.patch,
delivery_manifest.json and delivery_hash_check.json. Existing evidence is retained.
"""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def record(path):
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                sha256=digest(path))


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    if (HERE / 'delivery_manifest.json').exists():
        raise FileExistsError('Delivery is already frozen; create a new audit directory')
    comparison = []
    paths = sorted((HERE / 'probes').glob('*/result.json'))
    previous = HERE.parent / 'numeric_resolution_20260913/probes'
    paths += sorted(previous.glob('*_annual_bounds_spill/result.json'))
    for path in paths:
        value = read(path)
        raw = value['raw']
        comparison.append(dict(
            probe=path.parent.name, source=path.relative_to(ROOT).as_posix(),
            state=('REJECTED_TRIAL' if '_v7' in path.parent.name else
                   'FINAL' if '_final_v8' in path.parent.name else 'COMPARISON'),
            hours=value['optimization_hours'], start=value['optimization_start_hour'],
            coefficient_min=raw['coefficient_min_abs'], coefficient_max=raw['coefficient_max_abs'],
            matrix_span=raw['coefficient_max_abs'] / raw['coefficient_min_abs'],
            objective_min=raw['objective_coefficient_min_abs'],
            objective_max=raw['objective_coefficient_max_abs'],
            min_bound=raw.get('min_bound'), max_bound=raw.get('max_bound'),
            runtime_seconds=value.get('runtime'), barrier_iterations=value.get('barrier_iterations'),
            basis_revalidation=bool(value.get('basis_revalidation', {}).get('basis_reused')),
            kappa_estimate=value.get('kappa_estimate'), objective=value.get('objective'),
            raw_row_violation=value.get('raw_max_row_violation'),
            bound_violation=value.get('bound_violation'), dual_violation=value.get('dual_violation'),
            strict_acceptance=value.get('strict_acceptance'), status=value.get('status')))
    write('comparison.json', comparison)
    with (HERE / 'comparison.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparison[0]))
        writer.writeheader()
        writer.writerows(comparison)

    package = read(HERE / 'cloud_gate_manifest.json')
    stage = HERE / 'cloud_gate_20260913_v8'
    for item in package['files_manifest']:
        assert digest(stage / item['path']) == item['sha256'], item['path']
    archive = HERE / 'cloud_gate_20260913_v8.tar.gz'
    assert digest(archive) == package['archive_sha256']

    source_paths = list((ROOT / 'cispo_model').glob('*.py'))
    source_paths += [ROOT / p for p in [
        'CODEX_HANDOFF.md', 'MODEL_SERVER_STATUS.md', 'SERVER_RUNBOOK.md',
        'cispo_full_lp_model_spec.md', 'config/optimization_2030_numeric_final_v8.json',
        'scripts/probe_full_year_numerics.py', 'scripts/audit_reservoir_storage.py',
        'scripts/prepare_hydro_storage_corrections.py',
        'tests/test_numerical_cleanup.py', 'tests/test_reservoir_spill_reduction.py',
        'tests/test_numeric_simplification.py', 'tests/test_exact_zero_reservoir_bounds.py',
        'tests/test_hydro_station_model.py', 'tests/test_bound_tightening.py']]
    for path in source_paths:
        target = HERE / 'source_snapshot' / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    diff_paths = ['cispo_model', 'CODEX_HANDOFF.md', 'MODEL_SERVER_STATUS.md',
                  'SERVER_RUNBOOK.md', 'cispo_full_lp_model_spec.md']
    patch = subprocess.run(['git', 'diff', '--', *diff_paths], cwd=ROOT,
                           check=True, stdout=subprocess.PIPE).stdout
    (HERE / 'tracked_repair_changes.patch').write_bytes(patch)
    baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()

    water = read(HERE / 'annual_physical_qc_v8.json')
    regression = read(HERE / 'final_regression.json')
    assert water['passed'] and regression['successful'] and regression['tests'] == 50
    final = [row for row in comparison if row['state'] == 'FINAL']
    assert len(final) == 2 and all(row['strict_acceptance'] for row in final)
    evidence_paths = [p for p in sorted(HERE.rglob('*')) if p.is_file()
                      and '__pycache__' not in p.parts and p.suffix != '.pyc'
                      and p.name not in {'delivery_manifest.json', 'delivery_hash_check.json'}]
    input_paths = sorted((ROOT / 'data/hydro/repaired_storage_audit_20260913_v2').rglob('*'))
    manifest = dict(
        created_at=datetime.now(timezone.utc).isoformat(), git_baseline=baseline,
        git_changes_committed=False, candidate='config/optimization_2030_numeric_final_v8.json',
        scientific_case_id='base_2024_numeric_simplified_water_20260913_v8',
        initial_previous_hash_records_verified=689,
        regression=regression, annual_water_pass=water['passed'],
        national_8760_lp_built=False, national_8760_solve_pass=False,
        cloud_status='PREPARED_LOCALLY_NOT_UPLOADED_NOT_SUBMITTED',
        rejected_co2_row_scaling_retained_in_production=False,
        source_files=[record(p) for p in source_paths],
        corrected_input_files=[record(p) for p in input_paths if p.is_file()],
        reused_water_components=water['sources'],
        evidence_files=[record(p) for p in evidence_paths])
    write('delivery_manifest.json', manifest)
    checked = 0
    for section in ['source_files', 'corrected_input_files', 'reused_water_components', 'evidence_files']:
        for item in manifest[section]:
            path = Path(item['path'])
            if not path.is_absolute():
                path = ROOT / path
            assert digest(path) == item['sha256'], str(path)
            checked += 1
    check = dict(passed=True, checked_hash_records=checked, package_files_verified=package['files'],
                 manifest_sha256=digest(HERE / 'delivery_manifest.json'))
    write('delivery_hash_check.json', check)
    print(json.dumps(check, indent=2))


if __name__ == '__main__':
    main()
