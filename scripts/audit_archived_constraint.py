"""Stream an archived continuous MPS row against its original BarX checkpoint.

No solve or source mutation. Run on the backup host; only the row audit JSON
needs to be retrieved. Both row and variable order digests must match the
checkpoint before the numerical result is considered verified.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


def digest_start(kind, count):
    h = hashlib.sha256()
    h.update(f"cispo_raw_lp_{kind}_order_v1\0".encode("ascii"))
    h.update(count.to_bytes(8, "big"))
    return h


def digest_item(h, index, name, sense=""):
    encoded = name.encode("utf-8")
    h.update(index.to_bytes(8, "big"))
    h.update(len(encoded).to_bytes(8, "big"))
    h.update(encoded)
    h.update(sense.encode("ascii") + b"\0")


def audit_stream(lines, primal, ordering, target_index):
    """MPS free/fixed whitespace tokens, continuous columns, one RHS vector."""
    counts = dict(variable=ordering["variables"], constraint=ordering["constraints"])
    hashes = {k: digest_start(k, n) for k, n in counts.items()}
    section = None
    row_index = col_index = -1
    col_name = target_name = sense = None
    rhs = 0.0
    rhs_set = None
    terms = []
    sections = {"NAME", "OBJSENSE", "OBJNAME", "ROWS", "COLUMNS", "RHS", "RANGES", "BOUNDS", "ENDATA"}
    for line in lines:
        if not line.strip() or line.startswith("*"):
            continue
        if not line[0].isspace():
            head = line.split()[0]
            if head in sections:
                section = head
                if head == "COLUMNS":
                    if target_name is None:
                        raise ValueError("Target row index absent")
                    print(f"Located row {target_index}: {target_name} ({sense})", file=sys.stderr, flush=True)
                if head == "ENDATA":
                    break
                continue
        if section == "ROWS":
            row_type, name = line.split()
            if row_type == "N":
                continue
            mapped = {"E": "=", "L": "<", "G": ">"}[row_type]
            row_index += 1
            digest_item(hashes["constraint"], row_index, name, mapped)
            if row_index == target_index:
                target_name, sense = name, mapped
        elif section == "COLUMNS":
            name, rest = line.split(None, 1)
            if "'MARKER'" in rest:
                raise ValueError("Integer MPS is unsupported")
            if name != col_name:
                col_index += 1
                col_name = name
                digest_item(hashes["variable"], col_index, name)
            if target_name in rest:
                parts = rest.split()
                if len(parts) not in (2, 4):
                    raise ValueError("Malformed COLUMNS entry")
                for row, coefficient in zip(parts[::2], parts[1::2]):
                    if row == target_name:
                        a = float(coefficient.replace("D", "E"))
                        x = float(primal[col_index])
                        if not math.isfinite(a) or not math.isfinite(x):
                            raise ValueError("Nonfinite target row data")
                        terms.append(dict(variable=name, index=col_index, coefficient=a, barx=x, contribution=a*x))
        elif section == "RHS":
            parts = line.split()
            if rhs_set is not None and parts[0] != rhs_set:
                raise ValueError("Multiple RHS vectors unsupported")
            rhs_set = parts[0]
            for row, value in zip(parts[1::2], parts[2::2]):
                if row == target_name:
                    rhs += float(value.replace("D", "E"))
        elif section == "RANGES":
            raise ValueError("Ranged rows unsupported")
    actual_counts = dict(variable=col_index+1, constraint=row_index+1)
    if actual_counts != counts or len(primal) != counts["variable"]:
        raise ValueError(f"Ordering count mismatch: {actual_counts}, expected {counts}")
    digests = {k: h.hexdigest() for k, h in hashes.items()}
    for kind, value in digests.items():
        if value != ordering[f"{kind}_order_digest"]["sha256"]:
            raise ValueError(f"{kind} ordering digest mismatch")
    lhs = math.fsum(t["contribution"] for t in terms)
    residual = lhs-rhs
    violation = abs(residual) if sense == "=" else max(0.0, residual if sense == "<" else -residual)
    positive = math.fsum(t["contribution"] for t in terms if t["contribution"] > 0)
    negative = -math.fsum(t["contribution"] for t in terms if t["contribution"] < 0)
    scale = max(abs(rhs), positive, negative)
    return dict(status="ORDER_AND_ROW_VERIFIED", index=target_index, name=target_name,
                sense=sense, lhs=lhs, rhs=rhs, signed_residual=residual,
                violation=violation, positive_lhs_sum=positive, negative_lhs_sum=negative,
                row_magnitude=scale, relative_violation=violation/scale if scale else None,
                counts=actual_counts, ordering_sha256=digests, terms=terms,
                scientific_acceptance="NOT_ASSESSED_REQUIRES_FAMILY_UNIT_AND_TOLERANCE")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True, help="Immutable output_8760 backup")
    p.add_argument("--row-index", type=int, required=True)
    p.add_argument("--audit-json", type=Path, required=True)
    args = p.parse_args()
    if args.audit_json.exists():
        raise FileExistsError(args.audit_json)
    root = args.output_dir
    manifest_path = root/"result_manifest.json"
    manifest_sha = sha(manifest_path)
    entries = {e["path"]: e for e in json.loads(manifest_path.read_text())["files"]}
    names = ["model_archive/original.mps.gz", "barrier_checkpoint/primal_barx.npy",
             "barrier_checkpoint/barrier_checkpoint_manifest.json", "solve_report.json"]
    sources = {}
    stats = {}
    for name in names:
        path = root/name
        observed = dict(bytes=path.stat().st_size, sha256=sha(path))
        assert observed == {k: entries[name][k] for k in ("bytes", "sha256")}, name
        sources[name] = observed
        stats[name] = (path.stat().st_size, path.stat().st_mtime_ns)
    checkpoint = json.loads((root/names[2]).read_text())
    primal = np.load(root/names[1], mmap_mode="r", allow_pickle=False)
    with gzip.open(root/names[0], "rt", encoding="utf-8") as f:
        result = audit_stream(f, primal, checkpoint["lp_ordering"], args.row_index)
    for name, before in stats.items():
        path = root/name
        assert (path.stat().st_size, path.stat().st_mtime_ns) == before, name
    assert sha(manifest_path) == manifest_sha
    result.update(source_result_manifest_sha256=manifest_sha, source_files=sources,
                  source_unchanged_stat_and_manifest=True,
                  annual_capacity_link_row_scaling=checkpoint.get("annual_capacity_link_row_scaling"))
    args.audit_json.parent.mkdir(parents=True, exist_ok=True)
    args.audit_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
    print(json.dumps({k: result[k] for k in ("status", "name", "violation", "row_magnitude", "relative_violation")}))


if __name__ == "__main__":
    main()
