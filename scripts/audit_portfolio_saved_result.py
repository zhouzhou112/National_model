"""Rebuild a short diagnostic LP and replay archived vectors; never optimize.

Only <=168-hour portfolio evidence is supported to bound local memory. Exact
LP fingerprint/order/hash checks are mandatory. This cannot accept or repair
the source solution, and writes only to a new output directory.
"""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from datetime import datetime
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import gurobipy as gp
from cispo_model.config import ModelConfig
from cispo_model.data import load_model_data
from cispo_model.master import export_master_solution
from cispo_model.monolithic import build_full_year_monolithic
from cispo_model.offline_solution import read_legacy_checkpoint, offline_artifacts, audit_saved_primal
from cispo_model.solution_export import export_operational_solution
from cispo_model.solution_preservation import write_json
from cispo_model.flexible_portfolio import is_optional_portfolio
from cispo_model.io_contract import sha256_file, write_output_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output_dir.resolve()
    snapshot = json.loads((source/'model_config_snapshot.json').read_text(encoding='utf-8'))
    scope = json.loads((source/'run_scope.json').read_text(encoding='utf-8'))
    hours = int(scope['optimization_hours'])
    if not 1 <= hours <= 168:
        raise ValueError('Offline local replay is restricted to 1..168 hours')
    config = ModelConfig(path=Path(snapshot['source_path']), raw=snapshot['resolved_configuration'])
    config.validate()
    if not is_optional_portfolio(config.raw['flexible_load']):
        raise ValueError('Expected optional portfolio evidence')
    output.mkdir(parents=True, exist_ok=False)
    with ExitStack() as stack:
        for method in ('optimize', 'optimizeAsync', 'presolve', 'feasRelax', 'feasRelaxS'):
            if hasattr(gp.Model, method):
                stack.enter_context(patch.object(gp.Model, method,
                    side_effect=AssertionError(f'{method} forbidden during replay')))
        print('Loading inputs and reconstructing the original diagnostic LP; optimization forbidden.', flush=True)
        data = load_model_data(config)
        artifacts = build_full_year_monolithic(config, data, optimization_hours=hours,
            optimization_start_hour=int(scope.get('optimization_start_hour', 0)))
        stack.callback(artifacts.model.dispose)
        artifacts.model.update()
        registry = artifacts.index.get('annual_capacity_link_row_scaling')
        primal, dual = read_legacy_checkpoint(artifacts.model, source,
            expected_row_scaling_registry=registry)
        for vector in (primal, dual):
            if vector is not None:
                stack.callback(vector._mmap.close)
        print('Exact LP and saved-vector identity passed; exporting archived values.', flush=True)
        raw_qc = audit_saved_primal(artifacts.model, primal, row_scaling_registry=registry,
            violations_path=output/'raw_lp_violations.csv.gz')
        write_json(output/'raw_lp_qc.json', raw_qc)
        view = offline_artifacts(artifacts, primal, dual)
        export_master_solution(view, data, output, enforce_qc=False)
        qc = export_operational_solution(view, data, config, output, enforce_qc=False)
        report = dict(recorded_at=datetime.now().astimezone().isoformat(), source=str(source),
            source_snapshot_sha256=sha256_file(source/'model_config_snapshot.json'),
            source_checkpoint_manifest_sha256=sha256_file(source/'barrier_checkpoint/barrier_checkpoint_manifest.json'),
            status='OFFLINE_EXPORT_COMPLETE', scientifically_accepted=False,
            optimize_called=False, presolve_called=False, exact_lp_identity_pass=True,
            hours=hours, raw_lp_qc=raw_qc, semantic_qc_status=qc['status'],
            optional_portfolio_qc=qc.get('optional_portfolio_qc'),
            interpretation='Diagnostic replay only; no new optimum, no repaired vector, no planning state.')
        write_json(output/'offline_replay_report.json', report)
        write_output_catalog(output)
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
