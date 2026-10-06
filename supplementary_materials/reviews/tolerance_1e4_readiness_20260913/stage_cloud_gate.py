"""Package the reviewed source/input overlay locally; no upload or submission."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    stage=HERE/'cloud_gate_20260913_v9_t44_cross0_tol1e4'
    stage.mkdir(exist_ok=False)
    for folder,patterns in [('cispo_model',['*.py']),('config',['*.json','*.csv','*.yaml','*.yml'])]:
        for pattern in patterns:
            for src in sorted((ROOT/folder).rglob(pattern)):
                dst=stage/'repo'/src.relative_to(ROOT)
                dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    for name in ['probe_full_year_numerics.py','run_cispo_2030_full_year.py','run_cispo_planning_sequence.py']:
        dst=stage/'repo/scripts'/name;dst.parent.mkdir(exist_ok=True)
        shutil.copy2(ROOT/'scripts'/name,dst)
    corrected='hydro/repaired_storage_audit_20260913_v2'
    shutil.copytree(ROOT/'data'/corrected,stage/'data_overrides'/corrected)
    for name in ['prepare_cloud_data_overlay.py','cloud_preflight.sbatch']:
        shutil.copy2(HERE/name,stage/name)
    entries=[]
    for path in sorted(stage.rglob('*')):
        if path.is_file():
            entries.append(dict(path=path.relative_to(stage).as_posix(),bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (stage/'release_files.sha256').write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in entries),encoding='utf-8',newline='\n')
    archive=HERE/'cloud_gate_20260913_v9_t44_cross0_tol1e4.tar.gz'
    with tarfile.open(archive,'w:gz') as tf:
        for path in sorted(stage.rglob('*')):
            if path.is_file():tf.add(path,arcname=path.relative_to(stage).as_posix())
    record=dict(status='PREPARED_LOCALLY_NOT_SUBMITTED',files=len(entries),
        archive_bytes=archive.stat().st_size,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        source_release='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_2820fc3_v3',
        resources=dict(partition='amd_a8_768',cpus=64,memory_gib=700,job_wall_hours=2,
            gurobi_threads=44,gurobi_soft_memory_gb=None,solver_seconds=900,barrier_convergence_tolerance=1e-4,crossover=0,solution_target=1),files_manifest=entries)
    (HERE/'cloud_gate_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='files_manifest'},indent=2))


if __name__=='__main__':main()
