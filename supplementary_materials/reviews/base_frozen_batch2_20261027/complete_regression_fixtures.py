"""Restore missing review test fixtures in the isolated T550 validation copy only."""
from pathlib import Path
import base64, hashlib, json, subprocess, sys, zlib
from t550_validation import SSH, REMOTE, PY, REL

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
paths=['supplementary_materials/reviews/base_2060_launch_20261012/audit_cleanup_6b.py',
       'supplementary_materials/reviews/numerical_robustness_20261005/compare_probes.py',
       'supplementary_materials/reviews/factor_pair_8760_20261005/cloud_payload/source_screen.csv']
for prefix in ['cloud_runs/scripts','supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready2040_20261015','supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready2050_20261015']:
    paths+=subprocess.check_output(['git','ls-files',prefix],cwd=ROOT,text=True).splitlines()
payload={}
for name in sorted(set(paths)):
    p=ROOT/name
    if p.is_file() and p.stat().st_size<5*1024**2:
        payload[name]=base64.b64encode(p.read_bytes().replace(b'\r\n',b'\n')).decode()
blob=base64.b64encode(zlib.compress(json.dumps(payload).encode())).decode()
code=f'''
from pathlib import Path
import base64,json,zlib,subprocess,os
root=Path({REMOTE!r})/'repo';here=root/{REL!r}
payload=json.loads(zlib.decompress(base64.b64decode({blob!r})))
for name,value in payload.items():
 p=root/name;raw=base64.b64decode(value)
 if p.exists():assert p.read_bytes().replace(b'\\r\\n',b'\\n')==raw,name
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
if not (root/'.git').exists():
 subprocess.check_call(['git','init','--quiet'],cwd=root)
 subprocess.check_call(['git','add','cispo_model','scripts','config','tests','AGENTS.md'],cwd=root)
 subprocess.check_call(['git','-c','user.name=Codex validation','-c','user.email=codex-validation@local','commit','-qm','Isolated validation source snapshot'],cwd=root)
env=os.environ.copy();env.update(CISPO_DATA_ROOT=str(root/'data'),CISPO_CF_ROOT='/home/zz2/National_model_server/data/hourly_cf',CISPO_HYDRO_ROOT='/home/zz2/National_model_server/data/hydro_timeseries_20260719_sequential_sparse',CISPO_WAVE_ROOT='/home/zz2/National_model_server/data/wave_energy_20260727',CISPO_RAW_GRFR_ROOT='/home/zz2/National_model_server/data/grfr_raw_2019',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONPATH=str(root))
with (here/'full_regression_v2.log').open('x') as log:
 p=subprocess.run([{PY!r},'-m','unittest','discover','-s','tests','-q'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(exit_code=p.returncode,fixtures=len(payload),tail=(here/'full_regression_v2.log').read_text()[-12000:])))
raise SystemExit(p.returncode)
'''
if __name__=='__main__':
    p=subprocess.run(SSH+['python3 -'],input=code,text=True,capture_output=True,timeout=1200)
    (HERE/'t550_regression_v2_receipt.log').write_text(p.stdout+p.stderr,encoding='utf-8')
    print(p.stdout,p.stderr);sys.exit(p.returncode)
