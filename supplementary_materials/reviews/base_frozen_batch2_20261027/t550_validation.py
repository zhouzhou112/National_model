"""Finite isolated T550 validation, preserving every run and returning small evidence."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REMOTE='/home/zz2/National_model_server/base_frozen_batch2_20261027'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
SCP=['scp','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1']
PY='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
REL='supplementary_materials/reviews/base_frozen_batch2_20261027'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def remote(code):
    p=subprocess.run(SSH+['python3 -'],input='remote='+repr(REMOTE)+'\n'+code,text=True,capture_output=True,timeout=600)
    if p.returncode:raise RuntimeError(p.stdout[-2000:]+p.stderr[-4000:])
    return json.loads(p.stdout)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['prepare','run','collect']);parser.add_argument('--year',type=int,choices=[2040,2050]);a=parser.parse_args()
    if a.phase=='prepare':
        payload=HERE/'t550_validation_payload.tar.gz';assert not payload.exists()
        paths=subprocess.check_output(['git','ls-files','cispo_model','config','scripts','tests','AGENTS.md'],text=True,cwd=ROOT).splitlines()
        paths+=subprocess.check_output(['git','ls-files',REL],text=True,cwd=ROOT).splitlines()
        for name in ['compare_identity_gate.py','crosscheck_saved_solutions.py','assess_revised_identity.py']:
            paths.append('supplementary_materials/reviews/base_frozen_B_20261026/'+name)
        paths+=['supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py','supplementary_materials/reviews/base_frozen_followups_20261027/diagnose_fixed_capacity_conflicts.py','supplementary_materials/reviews/base_frozen_followups_20261027/source_collection.json']
        source=ROOT/'supplementary_materials/reviews/base_frozen_followups_20261027/source_base'
        for p in source.rglob('*'):
            if p.is_file():paths.append(p.relative_to(ROOT).as_posix())
        for y in [2040,2050]:
            paths += [REL+f'/{y}/window_carbon_budget.json',f'supplementary_materials/reviews/base_frozen_closure_20261027/{y}/derived_static/closure.json']
        hashes={};sys.path.insert(0,str(ROOT))
        from cispo_model.factor_screen import mps_section_sha256
        from audit_window_models import rhs
        original={}
        for y in [2040,2050]:
            old=HERE.parent/'base_frozen_closure_20261027'/str(y)
            p=old/'base_control_24h/model_archive/original.mps'
            values=rhs(p);values.pop('annual_net_carbon_limit')
            original[y]=dict(sections=mps_section_sha256(p),rhs_except_carbon_sha256=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest(),onehour_sha256=digest(old/'frozen_1h/model_archive/original.mps'))
        expected=json.loads((HERE.parent/'case3_2050_preparation_20261026/expected_data_files.json').read_text())
        tested=json.loads((HERE.parent/'base_frozen_closure_20261027/2060/attempt_2/FINAL_GATES_PASSED.json').read_text())['tested_source_lf_sha256']
        with tarfile.open(payload,'w:gz') as tf:
            def add(name,b):
                ti=tarfile.TarInfo('repo/'+name);ti.size=len(b);tf.addfile(ti,io.BytesIO(b));hashes[name]=hashlib.sha256(b).hexdigest()
            for p in sorted(set(paths)):
                b=(ROOT/p).read_bytes()
                if p.endswith(('.py','.md','.sbatch')):b=b.replace(b'\r\n',b'\n')
                add(p,b)
            add(REL+'/tested_sources.json',json.dumps(tested).encode())
            add(REL+'/original_model_comparison.json',json.dumps(original).encode())
        remote("from pathlib import Path\nimport json\np=Path(remote);assert not p.exists();p.mkdir()\nprint(json.dumps({'created':str(p)}))")
        subprocess.run(SCP+[str(payload),'national-model-server:'+REMOTE+'/payload.tar.gz'],check=True)
        result=remote('expected='+repr(expected)+'\nhashes='+repr(hashes)+'\npayload_sha='+repr(digest(payload))+'\n'+r'''
from pathlib import Path
import hashlib,json,tarfile
r=Path(remote);assert hashlib.sha256((r/'payload.tar.gz').read_bytes()).hexdigest()==payload_sha
with tarfile.open(r/'payload.tar.gz') as tf:
 for item in tf.getmembers():assert item.isfile() and not Path(item.name).is_absolute() and '..' not in Path(item.name).parts
 tf.extractall(r)
for name,h in hashes.items():assert hashlib.sha256((r/'repo'/name).read_bytes()).hexdigest()==h,name
data=Path('/home/zz2/National_model_server/base_frozen_B_validation_20261026/data')
for name,row in expected.items():
 p=data/name;assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],name
(r/'repo/data').symlink_to(data,target_is_directory=True)
print(json.dumps(dict(status='PASS',files=len(hashes),data_files=len(expected),data_root=str(data),payload_sha256=payload_sha)))
''')
        save(HERE/'t550_setup.json',result);print(result)
    elif a.phase=='run':
        assert a.year
        script=f'''from pathlib import Path
import os,subprocess,json,time
root=Path({REMOTE!r});repo=root/'repo';here=repo/{REL!r}
env=os.environ.copy();env.update(CISPO_DATA_ROOT=str(repo/'data'),CISPO_CF_ROOT='/home/zz2/National_model_server/data/hourly_cf',CISPO_HYDRO_ROOT='/home/zz2/National_model_server/data/hydro_timeseries_20260719_sequential_sparse',CISPO_WAVE_ROOT='/home/zz2/National_model_server/data/wave_energy_20260727',CISPO_RAW_GRFR_ROOT='/home/zz2/National_model_server/data/grfr_raw_2019',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8',PYTHONPATH=str(repo))
start=time.monotonic()
with (here/'B{a.year}_gates.log').open('x') as log:
 p=subprocess.run([{PY!r},str(here/'run_year_gates.py'),'{a.year}'],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
result=dict(year={a.year},exit_code=p.returncode,runtime_seconds=time.monotonic()-start)
(here/'B{a.year}_execution.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
print('\\n'.join((here/'B{a.year}_gates.log').read_text().splitlines()[-15:]),flush=True)
raise SystemExit(p.returncode)
'''
        p=subprocess.run(SSH+['python3 -'],input=script,text=True,capture_output=True,timeout=14400)
        (HERE/f'B{a.year}_t550_execution.log').write_text(p.stdout+p.stderr,encoding='utf-8')
        print(p.stdout,p.stderr);raise SystemExit(p.returncode)
    else:
        assert a.year
        # Gather only small receipts, command/profile files and compact model audit.
        code='year='+str(a.year)+'\n'+r'''
from pathlib import Path
import json,hashlib,sys,tarfile
root=Path(remote)/'repo';here=root/'supplementary_materials/reviews/base_frozen_batch2_20261027';work=here/str(year)
sys.path[:0]=[str(root),str(here)]
from audit_window_models import rhs
from cispo_model.factor_screen import mps_section_sha256
original=json.loads((here/'original_model_comparison.json').read_text())[str(year)]
target=work/'base_control_24h/model_archive/original.mps';sections=mps_section_sha256(target)
values=rhs(target);actual=values.pop('annual_net_carbon_limit')
changed=[k for k in sections if sections[k]!=original['sections'][k]]
other_same=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()==original['rhs_except_carbon_sha256']
one_same=hashlib.sha256((work/'frozen_1h/model_archive/original.mps').read_bytes()).hexdigest()==original['onehour_sha256']
expected=json.loads((work/'window_carbon_budget.json').read_text())['window_carbon_limit_mt']
audit=dict(status='PASS' if changed==['RHS'] and other_same and one_same and abs(actual-expected)<1e-12 else 'FAIL',changed_sections=changed,other_rhs_identical=other_same,one_hour_model_identical=one_same,effective_window_carbon_limit_mt=actual)
(work/'window_model_audit.json').write_text(json.dumps(audit,indent=2))
assert audit['status']=='PASS',audit
paths=[]
for p in work.rglob('*'):
 if p.is_file() and p.suffix in {'.json','.csv','.log'} and p.stat().st_size<500000 and 'model_archive' not in p.parts and 'solution_snapshot' not in p.parts:paths.append(p)
archive=here/('B'+str(year)+'_small_evidence.tar.gz');assert not archive.exists()
with tarfile.open(archive,'w:gz') as tf:
 for p in paths:tf.add(p,arcname=p.relative_to(work).as_posix())
print(json.dumps(dict(status='PASS',files=len(paths),archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),audit=audit)))
'''
        # audit imports pandas/numpy through factor_screen, use the existing environment.
        p=subprocess.run(SSH+[PY+' -'],input='remote='+repr(REMOTE)+'\n'+code,text=True,capture_output=True,timeout=600)
        if p.returncode:raise RuntimeError(p.stdout+p.stderr)
        receipt=json.loads(p.stdout);archive=HERE/f'B{a.year}_small_evidence.tar.gz'
        subprocess.run(SCP+['national-model-server:'+receipt['archive'],str(archive)],check=True)
        assert digest(archive)==receipt['sha256']
        target=HERE/str(a.year)/'t550_v1';target.mkdir(exist_ok=False)
        with tarfile.open(archive) as tf:
            for item in tf.getmembers():assert item.isfile() and not Path(item.name).is_absolute() and '..' not in Path(item.name).parts
            tf.extractall(target)
        save(HERE/f'B{a.year}_collection.json',receipt);print(receipt)


if __name__=='__main__':main()
