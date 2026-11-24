"""Verify and extract this isolated experiment; existing server data untouched."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

p=argparse.ArgumentParser();p.add_argument("root",type=Path);p.add_argument("--archive",default="experiment_v2.tar.gz");a=p.parse_args()
r=a.root.resolve(strict=True)
with tarfile.open(r/a.archive) as tf:
    for m in tf.getmembers():
        if not m.isfile() or not (r/(m.name)).resolve().is_relative_to(r):
            raise ValueError("Unsafe archive entry")
        if (r/m.name).exists():raise FileExistsError(r/m.name)
    tf.extractall(r)
manifest=json.loads((r/"experiment_manifest.json").read_text())
for e in manifest["files"]:
    q=r/e["path"]
    if hashlib.sha256(q.read_bytes()).hexdigest()!=e["sha256"]:raise ValueError(e["path"])
(r/"install_validation.json").write_text(json.dumps(dict(files=len(manifest["files"]),status="PASS")))
print("verified",len(manifest["files"]))
