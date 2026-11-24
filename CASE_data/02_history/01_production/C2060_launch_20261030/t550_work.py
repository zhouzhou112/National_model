"""Finite isolated C2060 R1 and engineering gates; preserve every directory.

prepare -> r1 -> gate --name screen_1h|unscreen_1h|gate_24h -> collect.
No production submission, watcher or modification of existing frozen sources.
"""
from pathlib import Path
import argparse, base64, hashlib, io, json, subprocess, tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REL=HERE.relative_to(ROOT).as_posix()
REMOTE='/home/zz2/National_model_server/C2060_launch_20261030_v1'
SOURCE='20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2'
PY='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
SCP=SSH[:-1];SCP[0]='scp'
PROFILE='config/solver_profiles/barrier_stagea_screened_agg0_lateentry_2060_v1_threads40.json'


def save(p,value):p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def remote(code,label,timeout=14400):
    header='from pathlib import Path\nimport json,hashlib,os,subprocess,sys,tarfile,time\nremote=Path('+repr(REMOTE)+')\nrepo=remote/"repo"\nwork=repo/'+repr(REL)+'\n'
    p=subprocess.run(SSH+[PY+' -'],input=header+code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    (HERE/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8');(HERE/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(p.stderr[-4000:]+p.stdout[-4000:])
    result=json.loads(p.stdout);save(HERE/(label+'.json'),result);return result


def main():
    global HERE, REMOTE
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['prepare','r1','gate','collect'])
    p.add_argument('--name',choices=['screen_1h','unscreen_1h','gate_24h'])
    p.add_argument('--attempt',type=int,default=1)
    a=p.parse_args()
    assert a.attempt>=1
    original_here=HERE
    if a.attempt>1:
        HERE=HERE/f'attempt_{a.attempt}';HERE.mkdir(exist_ok=True)
        REMOTE=REMOTE.removesuffix('_v1')+f'_v{a.attempt}'
    if a.phase=='prepare':
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        paths=subprocess.check_output(['git','ls-files','cispo_model','config','scripts','tests','AGENTS.md',REL,'supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py'],text=True).splitlines()
        archive=HERE/'t550_payload.tar.gz';assert not archive.exists()
        hashes={}
        with tarfile.open(archive,'w:gz') as tf:
            def add(name,raw):
                ti=tarfile.TarInfo('repo/'+name);ti.size=len(raw);tf.addfile(ti,io.BytesIO(raw));hashes[name]=hashlib.sha256(raw).hexdigest()
            for name in paths:add(name,subprocess.check_output(['git','show',commit+':'+name]))
            for target,source in [('acceptance_author_20261030.json',original_here.parent/'C2050_completed_20261029/acceptance_author_20261030.json'),('source_screen.csv',original_here.parent/'base_2060_screen_20261026/ready/source_screen.csv')]:add(REL+'/'+target,source.read_bytes())
            # Read-only fixtures needed by the existing production-contract tests.
            for name in ['supplementary_materials/reviews/base_2060_screen_20261026/ready/source_screen.csv',
                         'supplementary_materials/reviews/factor_pair_8760_20261005/cloud_payload/source_screen.csv',
                         'supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready2040_20261015/source_screen.csv',
                         'supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready2050_20261015/source_screen.csv']:
                add(name,(ROOT/name).read_bytes())
        expected=json.loads((original_here.parent/'case3_2050_preparation_20261026/expected_data_files.json').read_text())
        remote("assert not remote.exists()\nremote.mkdir()\nprint(json.dumps({'created':str(remote)}))",'create')
        subprocess.run(SCP+[str(archive),'national-model-server:'+REMOTE+'/payload.tar.gz'],check=True)
        result=remote('hashes='+repr(hashes)+'\nexpected='+repr(expected)+'\npayload_sha='+repr(sha(archive))+'\ncommit='+repr(commit)+'\n'+'''
assert hashlib.sha256((remote/'payload.tar.gz').read_bytes()).hexdigest()==payload_sha
with tarfile.open(remote/'payload.tar.gz') as tf:
 for item in tf.getmembers():assert item.isfile() and not Path(item.name).is_absolute() and '..' not in Path(item.name).parts
 tf.extractall(remote)
for name,h in hashes.items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==h,name
data=Path('/home/zz2/National_model_server/base_frozen_B_validation_20261026/data')
for name,row in expected.items():
 f=data/name;assert f.stat().st_size==row['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256'],name
(repo/'data').symlink_to(data,target_is_directory=True)
(work/'tested_source_lf_sha256.json').write_text(json.dumps(hashes,indent=2))
print(json.dumps(dict(status='PASS',commit=commit,files=len(hashes),data_files=len(expected),payload_sha256=payload_sha)))
''','prepare')
    elif a.phase in ['r1','gate']:
        if a.phase=='r1':
            source='/home/zz2/National_model_server/cloud_backup/'+SOURCE+'/output_8760'
            command=[PY,'scripts/prepare_continuation_state.py','--source',source,'--acceptance',REMOTE+'/repo/'+REL+'/acceptance_author_20261030.json','--planning-year','2060','--source-scenario','case3_thermal_ev_v5','--author-decision-label','ACCEPTED_RELATIVE_V1_20261030','--output',REMOTE+'/repo/'+REL+'/R1_v1']
            label='r1'
        else:
            assert a.name
            command=[PY,'supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py','--year','2060','--state',REMOTE+'/repo/'+REL+'/R1_v1/prepared_state/planning_state_candidate','--hours','24' if a.name=='gate_24h' else '1','--output',REMOTE+'/repo/'+REL+'/'+a.name,'--solver-profile',PROFILE,'--screen-csv',REMOTE+'/repo/'+REL+'/source_screen.csv','--same-scenario-continuation','--threads','8']
            if a.name=='unscreen_1h':command+=['--unscreened']
            label=a.name
        result=remote('command='+repr(command)+'\nlabel='+repr(label)+'\n'+'''
import psutil
assert psutil.virtual_memory().available/2**30>=90,'T550 gate available-memory threshold'
accept=json.loads((work/'acceptance_author_20261030.json').read_text());assert accept['status']=='PASS' and all(accept['conditions'].values())
env=os.environ.copy();env.update(CISPO_DATA_ROOT=str(repo/'data'),CISPO_CF_ROOT='/home/zz2/National_model_server/data/hourly_cf',CISPO_HYDRO_ROOT='/home/zz2/National_model_server/data/hydro_timeseries_20260719_sequential_sparse',CISPO_WAVE_ROOT='/home/zz2/National_model_server/data/wave_energy_20260727',CISPO_RAW_GRFR_ROOT='/home/zz2/National_model_server/data/grfr_raw_2019',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONUTF8='1',PYTHONPATH=str(repo))
start=time.monotonic()
with (work/(label+'.log')).open('x') as log:r=subprocess.run(command,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
result=dict(status='PASS' if r.returncode==0 else 'FAIL',exit_code=r.returncode,seconds=time.monotonic()-start,command=command,tail='\\n'.join((work/(label+'.log')).read_text().splitlines()[-20:]))
(work/(label+'_execution.json')).write_text(json.dumps(result,indent=2))
print(json.dumps(result))
''',label)
        if result['exit_code']!=0:raise RuntimeError(result['tail'])
    else:
        result=remote('''
import base64
files={}
for p in work.rglob('*'):
 if not p.is_file():continue
 state_cohorts='prepared_state' in p.parts and p.name=='capacity_cohorts.csv.gz' and p.stat().st_size<32*2**20
 if not state_cohorts and (p.suffix not in {'.json','.csv','.log'} or p.stat().st_size>1000000):continue
 if any(x in p.parts for x in ['model_archive','solution_snapshot','source_capsule']):continue
 raw=p.read_bytes();files[p.relative_to(work).as_posix()]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
print(json.dumps(dict(files=files)))
''','collect')
        for name,item in result['files'].items():
            raw=base64.b64decode(item.pop('base64'));assert hashlib.sha256(raw).hexdigest()==item['sha256']
            path=Path(name);assert not path.is_absolute() and '..' not in path.parts
            target=HERE/'t550_evidence'/path;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==raw
            else:target.write_bytes(raw)
        save(HERE/'collect.json',result)
    print(a.phase,result.get('status'),result.get('tail',''))


if __name__=='__main__':main()
