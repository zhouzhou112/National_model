"""One-shot T550 Case3 2060 backup: plan|run --config JSON --engine PY.

Reuse the checked transfer engine, locks, resume and SHA verification.
The explicit metadata list supplements all output_8760 files.
"""
import argparse
import importlib.util
import json
import socket
from pathlib import Path

EXTRA = ['FINAL_GATES_PASSED.json', 'compute_node_smoke.json',
         'startup_resources.json', 'released_submission.json',
         'data_copy_verification.json', 'license_path_preflight.json',
         'runtime_slurm_job.txt', 'runtime_hash_check.log',
         'submission_attempt.json', 'release_attempt.json',
         'sbatch_provenance.json', 'upstream_acceptance.json',
         'upstream_pricing_receipt.json']

def apply_author_space_override(engine, config):
    """Author's 2026-11-14 exception is restricted to this one operation."""
    if not config.get('author_space_override_20261114', False):
        return
    assert config['operation'] == '20261114_case3_2060_completed'
    assert config['releases'] == ['20261106_case3_2060_v9a12_screen0p2_agg0_t44_m750_tol1e4_v1']
    assert config['destination'] == '/home/zz2/National_model_server/cloud_backup'
    assert config['author_instruction'] == '直接保存别管门槛'
    # Keep the engine's free-space-versus-payload check, but no reserve percentage.
    # Locks, resumable transfer, all tiers and SHA verification remain unchanged.
    engine.MIN_FREE_FRACTION = 0.0

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['plan', 'run'])
    p.add_argument('--config', required=True, type=Path)
    p.add_argument('--engine', required=True, type=Path)
    a = p.parse_args()
    assert socket.gethostname().split('.')[0] == 't550'
    spec = importlib.util.spec_from_file_location('full_backup', a.engine)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    token = "'source_screen.csv','release_files.sha256','resource_usage.txt'"
    assert engine.INVENTORY.count(token) == 1
    engine.INVENTORY = engine.INVENTORY.replace(
        token, token + ',' + ','.join(repr(x) for x in EXTRA))
    config = json.loads(a.config.read_text(encoding='utf-8'))
    engine.configure(config)
    apply_author_space_override(engine, config)
    {'plan': engine.plan, 'run': engine.run}[a.phase]()
