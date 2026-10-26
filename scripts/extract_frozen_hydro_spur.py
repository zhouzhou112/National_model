"""Extract the author-authorized missing hydro spur table without solving.

Reads an immutable Base output, verifies archived identities, prefers saved X,
and validates the entire MPS column order plus VRE against its semantic table.
Writes a new sidecar directory only; never alters the source archive.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

import numpy as np


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verified_file(root, record):
    path = (root / record["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Manifest path escapes source directory")
    if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
        raise ValueError(f"Source identity mismatch: {path}")
    return path


def extract_columns(path, vector, expected_count, expected_digest):
    """Stream Gurobi's original linear MPS; memory is bounded by two families."""
    targets = {"vre_new_gw": {}, "hydro_spur_augmentation_gw": {}}
    pattern = re.compile(rb"(vre_new_gw|hydro_spur_augmentation_gw)\[(\d+)\]$")
    digest = hashlib.sha256()
    digest.update(b"cispo_raw_lp_variable_order_v1\0")
    digest.update(expected_count.to_bytes(8, "big"))
    section = None
    previous = None
    count = 0
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        for line in stream:
            if not line.strip() or line.startswith(b"*"):
                continue
            if not line[:1].isspace():
                section = line.split()[0]
                if section in {b"RHS", b"RANGES", b"BOUNDS", b"ENDATA"}:
                    break
                continue
            if section != b"COLUMNS":
                continue
            name = line.split(None, 1)[0]
            if b"'MARKER'" in line:
                raise ValueError("Integer MPS markers are not allowed in Base LP")
            if name == previous:
                continue
            if count >= len(vector):
                raise ValueError("MPS has more columns than the saved vector")
            digest.update(count.to_bytes(8, "big"))
            digest.update(len(name).to_bytes(8, "big"))
            digest.update(name)
            digest.update(b"\0")
            match = pattern.fullmatch(name)
            if match:
                family = targets[match[1].decode("ascii")]
                position = int(match[2])
                if position in family:
                    raise ValueError("Duplicate target column")
                value = float(vector[count])
                if not np.isfinite(value):
                    raise ValueError("Nonfinite target value")
                family[position] = (count, value)
            previous = name
            count += 1
    if count != expected_count or digest.hexdigest() != expected_digest:
        raise ValueError("Original MPS column order does not match saved vector")
    return targets


def extract(source: Path, output: Path):
    source, output = source.resolve(), output.resolve()
    if output == source or output.is_relative_to(source):
        raise ValueError("Supplement must be outside immutable output_8760")
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": "frozen_hydro_spur_supplement_v1", "status": "IN_PROGRESS",
              "source_directory": str(source), "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        result_path = source / "result_manifest.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        records = {r["path"]: r for r in result["files"]}
        report["result_manifest_sha256"] = sha256(result_path)
        tables = {}
        for name in ("vre_capacity.csv", "hydro_capacity.csv"):
            path = verified_file(source, records[name])
            with path.open(encoding="utf-8-sig", newline="") as f:
                tables[name] = list(csv.DictReader(f))
        checkpoint_path = verified_file(source, records["barrier_checkpoint/barrier_checkpoint_manifest.json"])
        checkpoint = json.loads(checkpoint_path.read_text())
        archive_path = verified_file(source, records["model_archive/archive_manifest.json"])
        archive = json.loads(archive_path.read_text())
        ordering = checkpoint["lp_ordering"]
        if archive["gurobi_fingerprint"] != ordering["gurobi_fingerprint"]:
            raise ValueError("Checkpoint/archive fingerprint mismatch")
        mps_record = next(r for r in archive["files"] if r["path"] in {"original.mps.gz", "original.mps"})
        mps = verified_file(source / "model_archive", mps_record)
        snapshot_path = source / "solution_snapshot/snapshot_manifest.json"
        snapshot = None
        if snapshot_path.exists():
            verified_file(source, records["solution_snapshot/snapshot_manifest.json"])
            snapshot = json.loads(snapshot_path.read_text())
        if snapshot and "X" in snapshot.get("attributes", {}):
            record = snapshot["attributes"]["X"]
            vector_path = verified_file(snapshot_path.parent, record)
            if snapshot["gurobi_fingerprint"] != archive["gurobi_fingerprint"]:
                raise ValueError("X snapshot/archive fingerprint mismatch")
            if snapshot["variable_order_digest"]["sha256"] != ordering["variable_order_digest"]["sha256"]:
                raise ValueError("X snapshot column order mismatch")
            attribute = "X"
        else:
            if (source / "solution_snapshot/X.npy").exists():
                raise ValueError("Unmanifested X exists; cannot silently fall back to BarX")
            record = checkpoint["vectors"]["primal"]
            if record["attribute"] != "BarX":
                raise ValueError("Unsupported fallback attribute")
            vector_path = verified_file(checkpoint_path.parent, record)
            attribute = "BarX"
        vector = np.load(vector_path, mmap_mode="r", allow_pickle=False)
        if vector.shape != (ordering["variables"],) or vector.dtype != np.dtype("float64"):
            raise ValueError("Saved vector dimension/dtype mismatch")
        report.update(vector_attribute=attribute, vector_sha256=record["sha256"],
                      vector_path=str(vector_path), mps_sha256=mps_record["sha256"],
                      variable_order_sha256=ordering["variable_order_digest"]["sha256"],
                      fallback_reason="X not preserved" if attribute == "BarX" else None)
        targets = extract_columns(mps, vector, ordering["variables"], ordering["variable_order_digest"]["sha256"])
        vre = tables["vre_capacity.csv"]
        hydro = tables["hydro_capacity.csv"]
        for family, rows in (("vre_new_gw", vre), ("hydro_spur_augmentation_gw", hydro)):
            if set(targets[family]) != set(range(len(rows))):
                raise ValueError(f"Missing/extra target indices: {family}")
        if len({(r['grid_uid'], r['technology']) for r in vre}) != len(vre):
            raise ValueError("Duplicate VRE stable keys")
        if len({r['hydrochn_row_id'] for r in hydro}) != len(hydro):
            raise ValueError("Duplicate hydro station IDs")
        delta = np.array([abs(targets['vre_new_gw'][i][1] - float(row['new_capacity_gw'])) for i, row in enumerate(vre)])
        report['vre_crosscheck'] = {'entries': len(vre), 'max_abs_difference_gw': float(delta.max()),
                                  'tolerance_gw': 1e-9, 'passed': bool(np.isfinite(delta).all() and (delta <= 1e-9).all())}
        if not report['vre_crosscheck']['passed']:
            raise ValueError("VRE vector/table identity gate failed")
        table = output / "hydro_spur_capacity.csv"
        with table.open('x', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hydrochn_row_id', 'original_column_index', 'hydro_spur_augmentation_gw'])
            for i, row in enumerate(hydro):
                writer.writerow([row['hydrochn_row_id'], *targets['hydro_spur_augmentation_gw'][i]])
        report.update(status='PASS', table={'path':table.name, 'bytes':table.stat().st_size, 'sha256':sha256(table)},
                      source_table_sha256={name:records[name]['sha256'] for name in tables})
    except Exception as error:
        report.update(status='FAIL', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        (output / 'supplement_manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(extract(args.source, args.output), indent=2))
