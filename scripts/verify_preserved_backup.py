"""Check a preserved result manifest with streaming SHA256; no solver required.

The report is written outside result-dir so the historical archive stays intact.
Use --allow-subset only for a deliberately incomplete local analysis cache.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(root, subset=False):
    root = Path(root).resolve()
    manifest = json.loads((root / "result_manifest.json").read_text(encoding="utf-8-sig"))
    rows, errors, missing = [], [], []
    for record in manifest["files"]:
        path = (root / record["path"]).resolve()
        if root not in path.parents:
            raise ValueError("Manifest path outside result root")
        if not path.is_file():
            missing.append(record["path"])
            if not subset:
                errors.append({"path": record["path"], "reason": "missing"})
            continue
        actual = {"path": record["path"], "bytes": path.stat().st_size, "sha256": sha256(path)}
        actual["pass"] = actual["bytes"] == record["bytes"] and actual["sha256"] == record["sha256"]
        rows.append(actual)
        if not actual["pass"]:
            errors.append(actual)
    return {"generated_at": datetime.now().astimezone().isoformat(), "result_dir": str(root),
            "status": "FAIL" if errors else ("SUBSET_PASS" if subset else "PASS"),
            "manifest_sha256": sha256(root / "result_manifest.json"),
            "manifest_count": len(manifest["files"]), "checked_count": len(rows),
            "checked_bytes": sum(r["bytes"] for r in rows), "missing": missing,
            "errors": errors, "files": rows,
            "scientific_acceptance": manifest.get("scientifically_accepted", False),
            "note": "Byte integrity only; no scientific acceptance and no re-optimization."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--allow-subset", action="store_true")
    args = parser.parse_args()
    if args.result_dir.resolve() in args.report.resolve().parents:
        parser.error("Report must be outside the immutable result directory")
    report = verify(args.result_dir, args.allow_subset)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"files", "missing", "errors"}}, ensure_ascii=False))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
