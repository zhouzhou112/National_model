"""T550-only install of a checksummed bundle into a NEW directory, then queue.

Usage: python install_flex_diagnostic_bundle.py --archive PATH --sha256 SHA
         --root NEW_DIRECTORY --server-root PATH --python PATH [--launch]
Does not alter any existing release or backup. Refuses existing destination.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile


def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b""):digest.update(block)
    return digest.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--server-root",required=True,type=Path)
    p.add_argument("--python",required=True,type=Path)
    p.add_argument("--launch",action="store_true")
    a=p.parse_args(); root=a.root.resolve(); base=a.server_root.resolve()
    if "cloud_backup" in root.parts or not root.is_relative_to(base/"probe_outputs"):
        raise ValueError("Destination must be a new probe_outputs directory")
    if sha(a.archive)!=a.sha256:raise ValueError("Bundle SHA mismatch; keep partial archive")
    root.mkdir(parents=True,exist_ok=False)
    with tarfile.open(a.archive) as tar:
        members=tar.getmembers()
        for member in members:
            if not member.isfile() or not (root/member.name).resolve().is_relative_to(root):
                raise ValueError("Unsafe bundle member")
        tar.extractall(root,members=members)
    manifest=json.loads((root/"bundle_manifest.json").read_text())
    for entry in manifest["files"]:
        if sha(root/entry["path"])!=entry["sha256"]:raise ValueError(entry["path"])
    env=os.environ.copy()
    env.update(CISPO_DATA_ROOT=str(root/"data"), CISPO_CF_ROOT=str(base/"data/hourly_cf"),
        CISPO_HYDRO_ROOT=str(base/"data/hydro_timeseries_20260719_sequential_sparse"),
        CISPO_RAW_GRFR_ROOT=str(base/"data/grfr_raw_2019"), CISPO_WAVE_ROOT=str(base/"data/wave_energy_20260727"),
        OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",PYTHONDONTWRITEBYTECODE="1")
    validation=dict(status="PASS",files=len(manifest["files"]),archive_sha256=a.sha256,
                    git_commit=manifest["git_commit"],root=str(root))
    subprocess.run([str(a.python),"-c","import numpy,pandas,psutil,gurobipy; print(gurobipy.gurobi.version())"],env=env,check=True)
    (root/"install_validation.json").write_text(json.dumps(validation,indent=2))
    if a.launch:
        cmd=["flock","--nonblock",str(base/"run_control/numerical_validation_solver.lock"),str(a.python),
             str(root/"repo/scripts/run_flex_server_series.py"),"--root",str(root),"--threads","16"]
        with (root/"queue_console.log").open("x") as log:
            proc=subprocess.Popen(cmd,cwd=root/"repo",env=env,stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        validation.update(launcher_pid=proc.pid,command=cmd)
        (root/"launch_receipt.json").write_text(json.dumps(validation,indent=2))
    print(json.dumps(validation))


if __name__=="__main__":main()
