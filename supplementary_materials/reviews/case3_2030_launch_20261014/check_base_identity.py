"""L3.1: build Base 1h from verified frozen sources and current checkout.

Writes a new evidence directory; never modifies either source tree or solves.
Usage: python check_base_identity.py --output <new-directory>
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    archived = ROOT / 'supplementary_materials/reviews/formal_launch_failure_20260914'
    release = '20260914_base_v9_t48_m750_tol1e4_v3'
    manifest = json.loads((archived / (release + '_manifest.json')).read_text())
    verified = []
    for item in manifest['files']:
        if not item['path'].startswith('repo/'):
            continue
        path = archived / release / item['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item['sha256']:
            raise RuntimeError('Frozen local source mismatch: ' + item['path'])
        verified.append({'path': item['path'], 'sha256': actual})
    (out / 'reference_source_verification.json').write_text(json.dumps(verified, indent=2))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
               CISPO_DATA_ROOT=str(ROOT / 'data'), CISPO_WAVE_ROOT=str(ROOT.parent / 'wave_energy'),
               OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PYTHONPATH=str(ROOT / 'output/portfolio_runtime_gurobi13'))
    records = []
    for name, repo in [('reference', archived / release / 'repo'), ('current', ROOT)]:
        output = out / name
        command = [sys.executable, '-B', str(repo / 'scripts/run_cispo_2030_full_year.py'),
                   '--config', str(repo / 'config/optimization_numeric_dac_by_year_v9.json'),
                   '--diagnostic-hours', '1', '--build-only', '--archive-original-model',
                   '--output-dir', str(output)]
        with (out / (name + '.stdout.log')).open('w', encoding='utf-8') as stdout, \
             (out / (name + '.stderr.log')).open('w', encoding='utf-8') as stderr:
            result = subprocess.run(command, cwd=repo, env=env, stdout=stdout, stderr=stderr)
        records.append({'name': name, 'command': command, 'returncode': result.returncode})
        (out / 'commands.json').write_text(json.dumps(records, indent=2))
        if result.returncode:
            raise RuntimeError(name + ' build failed; inspect retained logs')
        print(name + ' build completed', flush=True)
    sys.path.insert(0, str(ROOT))
    from cispo_model.factor_screen import mps_section_sha256
    segments = {}
    for name in ('reference', 'current'):
        matches = list((out / name).rglob('original.mps*'))
        if len(matches) != 1:
            raise RuntimeError('Expected one archive for ' + name)
        segments[name] = mps_section_sha256(matches[0])
    differences = [key for key in set().union(*[set(v) for v in segments.values()])
                   if segments['reference'].get(key) != segments['current'].get(key)]
    report = {'status': 'FAIL' if differences else 'PASS', 'different_segments': sorted(differences),
              'segments': segments, 'current_head': subprocess.check_output(
                  ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_manifest': str(archived / (release + '_manifest.json'))}
    (out / 'base_identity.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)
    if differences:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
