from pathlib import Path
import hashlib,tarfile,subprocess,json
root=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3')
archive=root/'source.tar.gz'
actual=hashlib.sha256(archive.read_bytes()).hexdigest()
assert actual=='987a351effdfca79d4020568aea0957a04a0d20b7fe1a5a238911610fb8c9547'
with tarfile.open(str(archive),'r:gz') as tf:
 for member in tf.getmembers():
  assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts
 tf.extractall(str(root))
with (root/'upload_hash_check.log').open('w') as log:
 subprocess.check_call(['sha256sum','-c','release_files.sha256'],cwd=str(root),stdout=log)
subprocess.check_call(['bash','-n','formal_base.sbatch'],cwd=str(root))
script=r"""
set -euo pipefail
set -a
source /publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_2820fc3_v3/manifests/cloud_environment_paths.env
set +a
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
TASK_ROOT=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3
cd "$TASK_ROOT"
"$PYTHON" prepare_cloud_data_overlay.py --base-data "$CISPO_DATA_ROOT" --output-data "$TASK_ROOT/data_overlay" --overrides "$TASK_ROOT/data_overrides" > overlay_creation.log
export CISPO_DATA_ROOT="$TASK_ROOT/data_overlay"
export PYTHONPATH="$TASK_ROOT/repo${PYTHONPATH:+:$PYTHONPATH}"
cd "$TASK_ROOT/repo"
"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9.json --solver-config config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json --horizon full_year --preflight-only --output-dir "$TASK_ROOT/preflight" > "$TASK_ROOT/preflight.log" 2> "$TASK_ROOT/preflight.err"
cd "$TASK_ROOT"
"$PYTHON" compare_inputs.py --reference expected_input_manifest.csv --actual preflight/input_manifest.csv --output input_comparison.json
"""
p=subprocess.run(['bash'],input=script,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
print(json.dumps(dict(archive_sha256=actual,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2))
if p.returncode:
 err=root/'preflight.err'
 if err.is_file(): print(err.read_text()[-4000:])
raise SystemExit(p.returncode)
