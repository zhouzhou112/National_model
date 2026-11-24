"""Freeze current code and local input tables for a separate fixed-server probe."""
import csv
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name",default="experiment_v2",help="Fresh package basename; existing archives are never overwritten")
    args=parser.parse_args()
    if not args.name.replace('_','').replace('-','').isalnum():raise ValueError("Invalid package basename")
    archive=HERE/(args.name+".tar.gz")
    mf=HERE/(args.name+"_manifest.json")
    if archive.exists() or mf.exists():raise FileExistsError("Use a fresh package name")
    files={}
    for folder in ["cispo_model", "config"]:
        for p in (ROOT/folder).rglob("*"):
            if p.is_file() and p.suffix in {".py",".json",".csv",".yaml",".yml"}:
                files["repo/"+p.relative_to(ROOT).as_posix()]=p
    for p in HERE.glob("*.py"):
        files["repo/"+p.relative_to(ROOT).as_posix()]=p
    required=json.loads((ROOT/"config/model_input_files.json").read_text())["required_model_tables"]
    for rel in required:
        files["data/"+rel]=ROOT/"data"/rel
    # Include exact real inputs recorded by the production preflight, including
    # tables outside the minimum contract. Do not copy external weather chunks.
    with (HERE.parent/"formal_launch_20260914/local_preflight/input_manifest.csv").open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            p=Path(row["resolved_path"])
            if p.is_file() and (ROOT/"data") in p.parents:
                files["data/"+p.relative_to(ROOT/"data").as_posix()]=p
    for p in (ROOT/"data/hydro/repaired_storage_audit_20260913_v2").glob("*"):
        if p.is_file(): files["data/"+p.relative_to(ROOT/"data").as_posix()]=p
    source=ROOT.parent/"claude_workspace/evidence/rc_screen_2030/vre_site_reduced_costs.csv"
    files["source_screen.csv"]=source
    records=[dict(path=rel,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for rel,p in sorted(files.items())]
    manifest=dict(git_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                  working_tree_dirty=True,files=records)
    mf.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    with tarfile.open(archive,"x:gz",compresslevel=1) as tar:
        for rel,p in sorted(files.items()): tar.add(p,arcname=rel,recursive=False)
        tar.add(mf,arcname="experiment_manifest.json")
    print(json.dumps(dict(files=len(records),archive=str(archive),bytes=archive.stat().st_size)))


if __name__=="__main__":main()
