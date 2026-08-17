#!/usr/bin/env python3
"""Fail closed unless a Barrier checkpoint is complete and reusable.

This lightweight gate is intended for serial campaign orchestration.  It does
not replace exact-LP validation before deferred crossover; it prevents a
forensic, incomplete recovery manifest from being used to authorize the next
long-horizon engineering run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "cispo_barrier_primal_dual_checkpoint_v1"
ELIGIBLE_STATUSES = {
    "ACCEPTED_PRIMARY_BARRIER_SOLUTION",
    "ENGINEERING_BARRIER_CHECKPOINT_ONLY",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_checkpoint_manifest(manifest_path: str | Path) -> dict[str, Any]:
    """Return a machine-readable, fail-closed campaign eligibility report."""
    path = Path(manifest_path)
    reasons: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        return {
            "schema_version": "cispo_checkpoint_campaign_gate_v1",
            "eligible": False,
            "manifest_path": str(path),
            "reasons": [f"manifest_unreadable:{type(error).__name__}"],
        }
    if not isinstance(manifest, dict):
        return {
            "schema_version": "cispo_checkpoint_campaign_gate_v1",
            "eligible": False,
            "manifest_path": str(path),
            "reasons": ["manifest_not_object"],
        }

    if manifest.get("schema_version") != SCHEMA_VERSION:
        reasons.append("schema_version")
    if manifest.get("deferred_crossover_eligible") is not True:
        reasons.append("deferred_crossover_eligible")
    checkpoint_status = manifest.get("checkpoint_status")
    if checkpoint_status not in ELIGIBLE_STATUSES:
        reasons.append("checkpoint_status")
    if checkpoint_status == "ENGINEERING_BARRIER_CHECKPOINT_ONLY" and (
        manifest.get("scientifically_accepted") is not False
    ):
        reasons.append("engineering_scientific_identity")
    if checkpoint_status == "ACCEPTED_PRIMARY_BARRIER_SOLUTION" and (
        manifest.get("scientifically_accepted") is not True
    ):
        reasons.append("accepted_scientific_identity")

    evidence = manifest.get("solver_evidence")
    if not isinstance(evidence, dict):
        reasons.append("solver_evidence")
    else:
        if evidence.get("status_code") != 2:
            reasons.append("solver_status_code")
        if evidence.get("barrier_status_code") != 2:
            reasons.append("barrier_status_code")

    vector_evidence: dict[str, Any] = {}
    vectors = manifest.get("vectors")
    if not isinstance(vectors, dict):
        reasons.append("vectors")
    else:
        for role in ("primal", "dual"):
            metadata = vectors.get(role)
            role_report: dict[str, Any] = {"valid": False}
            vector_evidence[role] = role_report
            if not isinstance(metadata, dict):
                reasons.append(f"{role}_metadata")
                continue
            relative = metadata.get("path")
            if not isinstance(relative, str) or Path(relative).name != relative:
                reasons.append(f"{role}_path")
                continue
            vector_path = path.parent / relative
            try:
                entries = int(metadata.get("entries", 0))
                expected_bytes = int(metadata.get("bytes", 0))
            except (TypeError, ValueError):
                entries = expected_bytes = 0
            expected_sha = metadata.get("sha256")
            if entries <= 0:
                reasons.append(f"{role}_entries")
            if expected_bytes <= 0:
                reasons.append(f"{role}_bytes")
            if not isinstance(expected_sha, str) or len(expected_sha) != 64:
                reasons.append(f"{role}_sha256_metadata")
            if not vector_path.is_file():
                reasons.append(f"{role}_file")
                continue
            actual_bytes = vector_path.stat().st_size
            actual_sha = _sha256(vector_path)
            if actual_bytes != expected_bytes:
                reasons.append(f"{role}_size_mismatch")
            if actual_sha != expected_sha:
                reasons.append(f"{role}_sha256_mismatch")
            role_report.update(
                valid=(
                    entries > 0
                    and actual_bytes == expected_bytes
                    and actual_sha == expected_sha
                ),
                entries=entries,
                bytes=actual_bytes,
                sha256=actual_sha,
            )

    return {
        "schema_version": "cispo_checkpoint_campaign_gate_v1",
        "eligible": not reasons,
        "manifest_path": str(path),
        "checkpoint_status": checkpoint_status,
        "deferred_crossover_eligible": manifest.get("deferred_crossover_eligible"),
        "reasons": reasons,
        "vectors": vector_evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = check_checkpoint_manifest(args.manifest)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
