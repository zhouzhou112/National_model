"""Freeze the authorized repaired Base source/input overlay in a new archive.

Run locally after regression tests and local_preflight; refuses existing roots.
No upload, submission or deletion is performed by this script.
"""
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAME = '20260914_base_v9_t48_m750_tol1e4_v3'


def main():
    stage = HERE / NAME
    stage.mkdir(exist_ok=False)
    for folder, patterns in [('cispo_model', ['*.py']), ('config', ['*.json','*.csv','*.yaml','*.yml'])]:
        for pattern in patterns:
            for src in sorted((ROOT/folder).rglob(pattern)):
                dst = stage/'repo'/src.relative_to(ROOT)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    for name in ['run_cispo_2030_full_year.py','run_cispo_planning_sequence.py','probe_full_year_numerics.py']:
        dst = stage/'repo/scripts'/name
        dst.parent.mkdir(exist_ok=True)
        shutil.copy2(ROOT/'scripts'/name, dst)
    test_path = stage/'repo/tests/test_numeric_repaired_formal_launch.py'
    test_path.parent.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'tests/test_numeric_repaired_formal_launch.py', test_path)
    corrected = 'hydro/repaired_storage_audit_20260913_v2'
    shutil.copytree(ROOT/'data'/corrected, stage/'data_overrides'/corrected)
    for name in ['formal_base.sbatch','compare_inputs.py']:
        shutil.copy2(HERE/name, stage/name)
    shutil.copy2(HERE.parent/'tolerance_1e4_readiness_20260913/prepare_cloud_data_overlay.py', stage/'prepare_cloud_data_overlay.py')
    shutil.copy2(HERE.parent/'formal_launch_20260914/local_preflight/input_manifest.csv', stage/'expected_input_manifest.csv')
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    metadata = dict(git_base_commit=commit, working_tree_dirty=True,
                    source_identity='Exact packaged file SHA256; not a clean Git commit',
                    scientific_configuration_sha256='937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0',
                    authorization='Author requested full 2030 solve without solver/job wall limit on 2026-09-14')
    (stage/'source_identity.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    entries = [dict(path=p.relative_to(stage).as_posix(), bytes=p.stat().st_size,
                    sha256=hashlib.sha256(p.read_bytes()).hexdigest())
               for p in sorted(stage.rglob('*')) if p.is_file()]
    (stage/'release_files.sha256').write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in entries), encoding='utf-8', newline='\n')
    archive = HERE/(NAME+'.tar.gz')
    with tarfile.open(archive, 'x:gz') as tar:
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                tar.add(path, arcname=path.relative_to(stage).as_posix())
    manifest = dict(metadata, archive=archive.name, archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                    archive_bytes=archive.stat().st_size, file_count=len(entries), files=entries)
    (HERE/(NAME+'_manifest.json')).write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'}, indent=2))


if __name__ == '__main__':
    main()
