"""Compare frozen running Base provenance to local portfolios; never optimize.

Reads only existing remote files and scheduler status over SSH. Writes a new
local evidence directory; no remote mutation or data-payload recomputation.
Input-manifest hashes describe recorded inputs, not a fresh full-store audit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
from datetime import datetime

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cispo_model.config import load_model_config


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def differences(left, right, prefix=''):
    if isinstance(left, dict) and isinstance(right, dict):
        return [row for key in sorted(left.keys() | right.keys())
                for row in differences(left.get(key), right.get(key), f'{prefix}.{key}'.strip('.'))]
    return [] if left == right else [dict(path=prefix, remote_base=left, local=right)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ssh-host', required=True)
    parser.add_argument('--release-root', required=True)
    parser.add_argument('--case-id', required=True)
    parser.add_argument('--job-id', required=True, type=int)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--local-result-dir', type=Path,
        help='Optional existing local case directory for recorded input-manifest comparison.')
    args = parser.parse_args()
    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)

    def read(command):
        return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
            args.ssh_host, command], check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=60).stdout

    release = args.release_root.rstrip('/')
    remote_output = f'{release}/outputs/{args.case_id}'
    scheduler = read(f'squeue -h -j {args.job_id} -o "%i %T %M %N"').decode().strip()
    (root/'scheduler.txt').write_text(scheduler+'\n', encoding='utf-8')
    for name in ('input_manifest.csv', 'model_config_snapshot.json', 'run_identity.json',
                 'final_stage_a_lp_identity.json'):
        (root/name).write_bytes(read('cat '+shlex.quote(f'{remote_output}/{name}')))
    hashes = read('cd '+shlex.quote(f'{release}/repo')+
        ' && sha256sum cispo_model/*.py config/optimization_2030.json '
        'config/scenarios/base.json config/formulation_profiles/annual_capacity_link_rows_8192_v1.json')
    (root/'remote_source_sha256.txt').write_bytes(hashes)
    sources = []
    for line in hashes.decode().splitlines():
        digest, path = line.split(maxsplit=1)
        local = ROOT/path
        sources.append(dict(path=path, remote_sha256=digest,
            local_sha256=sha(local) if local.is_file() else None,
            identical=local.is_file() and sha(local) == digest))
    frozen = json.loads((root/'model_config_snapshot.json').read_text(encoding='utf-8'))['resolved_configuration']
    base = load_model_config(
        formulation_path='config/formulation_profiles/annual_capacity_link_rows_8192_v1.json')
    # Numerics/profile identity can differ; all scientific coefficients remain checked.
    excluded = {'numerics', 'solver_profile'}
    scientific = lambda raw: {**{k:v for k,v in raw.items() if k not in excluded},
        'coefficient_zero_tolerance': raw['numerics']['coefficient_zero_tolerance']}
    base_diffs = differences(scientific(frozen), scientific(base.raw))
    case_diffs = {}
    for case in ('case1_thermal_v5', 'case2_ev_v5', 'case3_thermal_ev_v5'):
        config = load_model_config(scenario_path=f'config/scenarios/{case}.json',
            formulation_path='config/formulation_profiles/annual_capacity_link_rows_8192_v1.json')
        rows = differences(scientific(frozen), scientific(config.raw))
        unexpected = [row for row in rows if not row['path'].startswith(
            ('scenario.', 'flexible_load.', 'features.flexible_load'))]
        case_diffs[case] = dict(all_differences=rows, unexpected_base_differences=unexpected)
    core = {'monolithic.py', 'master.py', 'data.py', 'hydro.py', 'load_center.py',
        'annual_capacity_link_scaling.py', 'carbon_accounting.py', 'technology_registry.py',
        'timeblocks.py', 'wave_energy.py', 'price_basis.py'}
    core_match = core.issubset({Path(row['path']).name for row in sources}) and all(
        row['identical'] for row in sources if Path(row['path']).name in core)
    input_comparison = None
    if args.local_result_dir:
        remote_inputs = pd.read_csv(root/'input_manifest.csv').fillna('')
        local_inputs = pd.read_csv(args.local_result_dir/'input_manifest.csv').fillna('')
        for frame in (remote_inputs, local_inputs):
            frame['logical_path'] = frame.logical_path.str.replace('\\', '/', regex=False)
        config_kinds = {'configuration', 'scenario_configuration', 'solver_configuration', 'formulation_configuration'}
        left = remote_inputs[~remote_inputs.kind.isin(config_kinds)]
        right = local_inputs[~local_inputs.kind.isin(config_kinds)]
        joined = left.merge(right, on=['kind','logical_path'], how='outer',
            suffixes=('_remote','_local'), indicator=True, validate='one_to_one')
        joined['hash_identical'] = joined.sha256_remote.eq(joined.sha256_local)
        joined.to_csv(root/'recorded_input_comparison.csv', index=False)
        common = joined[joined['_merge'].eq('both')]
        input_comparison = dict(local_result=str(args.local_result_dir.resolve()),
            common_rows=len(common), identical_common_hashes=int(common.hash_identical.sum()),
            differing_common=common.loc[~common.hash_identical,
                ['kind','logical_path','sha256_remote','sha256_local']].to_dict('records'),
            base_only=joined.loc[joined['_merge'].eq('left_only'), ['kind','logical_path']].to_dict('records'),
            local_only=joined.loc[joined['_merge'].eq('right_only'), ['kind','logical_path']].to_dict('records'))
        # Read only the two known non-secret validation sidecars if they differ.
        for row in common.loc[~common.hash_identical].to_dict('records'):
            if row['kind'] == 'validation_sidecar' and row['logical_path'] in (
                'output_manifest.csv', 'smoke_test_report.json'):
                (root/('remote_'+row['logical_path'])).write_bytes(
                    read('cat '+shlex.quote(row['resolved_path_remote'])))
        input_comparison['status'] = ('IDENTICAL_RECORDED_INPUTS' if
            common.hash_identical.all() and len(common) == len(joined) else 'DIFFERENCES_RECORDED_FOR_REVIEW')
    report = dict(recorded_at=datetime.now().astimezone().isoformat(),
        git_head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        remote_release=release, job_status=scheduler, optimize_called=False,
        remote_mutation=False, source_comparison=sources,
        core_source_identity_pass=core_match, base_resolved_differences=base_diffs,
        portfolio_differences=case_diffs,
        recorded_input_comparison=input_comparison,
        status='PASS' if core_match and not base_diffs and not any(
            row['unexpected_base_differences'] for row in case_diffs.values()) else 'REVIEW_REQUIRED',
        limitations=['Source/config equality is not a newly constructed 8760h matrix comparison.',
            'Copied input manifests record hashes from launch; CF Zarr hashes cover metadata only.',
            'Changed validation/export/flex modules require separate regression evidence.'])
    (root/'base_identity_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_comparison','portfolio_differences')}, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
