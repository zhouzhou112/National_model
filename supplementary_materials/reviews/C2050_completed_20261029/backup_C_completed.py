"""T550-only C2050 full backup with explicit launch metadata.

Usage: backup_C_completed.py plan|run --config CONFIG --engine ENGINE
Reuses the audited one-shot transfer engine and its global lock, resume,
30% reserve, per-file SHA, and final immutable-source checks.
"""
import argparse
import importlib.util
import json
import socket
from pathlib import Path

EXTRA = ['local_engineering_gates.json', 'local_threads40_gates.json',
         'startup_memory.json', 'startup_regression.log', 'release_receipt.json',
         'runtime_slurm_job.txt', 'upstream_state_sha256.json',
         'old_release_provenance.json', 'runtime_hash_check.log',
         'data_overlay_sha256.json', 'compute_node_smoke.json',
         'submission_attempt.json']

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['plan', 'run'])
    p.add_argument('--config', required=True, type=Path)
    p.add_argument('--engine', required=True, type=Path)
    a = p.parse_args()
    config = json.loads(a.config.read_text(encoding='utf-8'))
    assert config['execution_gate'] == 'AUTHORIZED_BY_USER_RETRY_20261029'
    assert socket.gethostname().split('.')[0] == 't550'
    spec = importlib.util.spec_from_file_location('backup_engine', a.engine)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    token = "'source_screen.csv','release_files.sha256','resource_usage.txt'"
    assert engine.INVENTORY.count(token) == 1
    engine.INVENTORY = engine.INVENTORY.replace(token, token + ',' + ','.join(repr(x) for x in EXTRA))
    engine.configure(config)
    {'plan': engine.plan, 'run': engine.run}[a.phase]()
