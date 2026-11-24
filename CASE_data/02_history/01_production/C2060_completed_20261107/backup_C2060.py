"""One-shot T550 C2060 backup: plan|run --config JSON --engine PY.

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
    engine.configure(json.loads(a.config.read_text(encoding='utf-8')))
    {'plan': engine.plan, 'run': engine.run}[a.phase]()
