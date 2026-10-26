"""Prepare a state-free case3 2050 data/batch package; never submit a job.

Usage: python .../prepare_package.py local|cloud
Cloud mode creates a NEW preparation directory, not a frozen release. All
source data are SHA-checked, credentials are not read, R1/gates remain pending.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=HERE.parent/'case3_2040_C2050_launch_20261019'
PROFILE='config/solver_profiles/barrier_stagea_screened_agg0_case3_2050_v1_threads40.json'
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
SOURCE=BASE+'/20260914_base_v9_t48_m750_tol1e4_v3'
STAGING=BASE+'/_preparations/20261026_case3_2050_t40_v1'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','paracloud-bscc-a8']

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for b in iter(lambda:stream.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def write(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==raw,'Refuse different existing bytes '+str(p)
    else:p.write_bytes(raw)

def save(p,v):write(p,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())

def differences(a,b,prefix=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return sum((differences(a.get(k),b.get(k),prefix+'.'+k) for k in sorted(a.keys()|b.keys())),[])
    return [] if a==b else [dict(key=prefix.lstrip('.'),before=a,after=b)]

def local():
    original=json.loads((ROOT/'config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json').read_text())
    profile=copy.deepcopy(original)
    profile['profile_id']=Path(PROFILE).stem
    profile['numerics']['threads']=40
    screen_dir=HERE.parent/'case3_2030_launch_20261014/P4_ready2050_20261015'
    profile['candidate_screen']=json.loads((screen_dir/'candidate_screen_fragment.json').read_text())['candidate_screen']
    assert sha(screen_dir/'source_screen.csv')==profile['candidate_screen']['source_csv_sha256']
    diff=differences(original,profile)
    assert {r['key'] for r in diff}=={'profile_id','numerics.threads','candidate_screen.source_release',
        'candidate_screen.source_dual_sha256','candidate_screen.source_csv_sha256'}
    save(ROOT/PROFILE,profile)
    save(HERE/'profile_diff.json',dict(status='PASS',differences=diff,parent_sha256=sha(ROOT/'config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json'),profile_sha256=sha(ROOT/PROFILE)))
    batch=(OLD/'C2050_threads40.sbatch').read_text()
    batch=batch.replace('# Author 2026-10-20: C2050 40-thread retry; preserve original OOM release.',
                        '# Author 2026-10-26: framework A case3 2050; final gates and frozen release required.')
    batch=batch.replace('CISPO_EXTRA=()\nif [ "$CISPO_YEAR" = 2050 ]; then CISPO_EXTRA+=(--late-entry-base-state); fi\n','')
    batch=batch.replace('--allow-candidate-state-in "${CISPO_EXTRA[@]}"','--allow-candidate-state-in')
    batch=batch.replace('config/solver_profiles/barrier_stagea_screened_agg0_${CISPO_YEAR}_v1_threads40.json',PROFILE)
    batch=batch.replace('export GRB_LICENSE_FILE="${CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}"',
                        ': "${CISPO_CLOUD_LICENSE:?Final preflight must provide the validated license path}"\nexport GRB_LICENSE_FILE="$CISPO_CLOUD_LICENSE"')
    # Guard fails before any work on a preparation directory, even if manually submitted.
    batch=batch.replace('test ! -e output_8760',
        'test -f FINAL_GATES_PASSED.json\ntest -d upstream_state/planning_state_candidate\ntest ! -e output_8760')
    batch=batch.replace("root = Path(sys.argv[1])\n", "root = Path(sys.argv[1])\n"+
        "gates=json.loads((root/'FINAL_GATES_PASSED.json').read_text())\n"+
        "if gates.get('status') != 'PASS' or gates.get('planning_year') != 2050 or gates.get('framework') != 'A':\n"+
        "    raise RuntimeError('Framework A final gates are required')\n")
    assert '--late-entry-base-state' not in batch
    assert 'OMP_NUM_THREADS=40 OPENBLAS_NUM_THREADS=40 MKL_NUM_THREADS=40' in batch
    write(HERE/'case3_2050.sbatch',batch.encode())
    source=json.loads((OLD/'deployment_C2050/expected_data_files.json').read_text())
    expected={}
    for name,row in source.items():
        p=ROOT/'data'/name
        assert sha(p)==row['sha256'],'Input drift '+name
        expected[name]=dict(sha256=row['sha256'],bytes=p.stat().st_size,local_path='data/'+name)
    save(HERE/'expected_data_files.json',expected)
    additional=[k for k in expected if k.startswith('flexibility/participation_pathway_v2/') or k in
        ['thermal/existing_capacity_2025.csv','thermal/retirement_schedule.csv','hydro/grfr_monthly_p30_single_year_proxy_2019.nc']]
    launch=dict(status='PREPARED_WAITING_CASE3_2040',framework='A',scenario='case3_thermal_ev_v5',
        planning_year=2050,boundary_year=2040,solver_profile=PROFILE,upstream_job='5201318',
        upstream_state=None,screen_margin=.2,source_release=SOURCE,
        required_gates=['2040_terminal_backup_SHA','2040_certificate_B_over_obj_le_1e-2',
            '2040_extended_assessment','R1_state_audit','1h_screen_unscreen_MPS_segments',
            '24h_OPTIMAL_service_M_le_1e-3_credit_preservation','2050_parameter_approval','cloud_preflight'],
        resources=dict(cpus=64,memory='750G',billing=64,solver_threads=40,time_limit='UNLIMITED',
            minimum_available_memory_gib=700,no_requeue=True),
        authorization='Author 2026-10-26: submit and release only after all required gates pass',
        stage_b=False,background_monitor=False,submitted=False,
        release_name_template='YYYYMMDD_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1')
    save(HERE/'launch_config.draft.json',launch)
    payload=HERE/'preparation_payload.tar.gz'
    assert not payload.exists(),'Never overwrite a package'
    members={}
    with tarfile.open(payload,'w:gz') as tf:
        def add(name,p):
            raw=p.read_bytes();entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mode=0o640
            tf.addfile(entry,io.BytesIO(raw));members[name]=hashlib.sha256(raw).hexdigest()
        add('case3_2050.sbatch',HERE/'case3_2050.sbatch')
        add('launch_config.draft.json',HERE/'launch_config.draft.json')
        add('expected_data_files.json',HERE/'expected_data_files.json')
        add('source_screen.csv',screen_dir/'source_screen.csv')
        add('repo/'+PROFILE,ROOT/PROFILE)
        for name in additional:add('additional_data/'+name,ROOT/'data'/name)
    save(HERE/'package_identity.json',dict(status='PREPARED_NOT_FROZEN',sha256=sha(payload),bytes=payload.stat().st_size,
        files=members,input_files=len(expected),additional_files=additional,upstream_state_included=False,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()))
    print('Local preparation: profile, 58 verified data identities, batch and payload; no R1/state/solve.')

def cloud():
    identity=json.loads((HERE/'package_identity.json').read_text())
    assert sha(HERE/'preparation_payload.tar.gz')==identity['sha256']
    init='from pathlib import Path\np=Path('+repr(STAGING)+')\nassert not p.exists(), "Refuse existing preparation"\np.mkdir(parents=True)\n'
    subprocess.run(SSH+['python3 -'],input=init,text=True,check=True)
    subprocess.run(['scp','-o','BatchMode=yes',str(HERE/'preparation_payload.tar.gz'),
        'paracloud-bscc-a8:'+STAGING+'/preparation_payload.tar.gz'],check=True)
    code='root=Path('+repr(STAGING)+')\nsource=Path('+repr(SOURCE)+')\nidentity='+repr(identity)+'\n'+r'''
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
assert sha(root/'preparation_payload.tar.gz')==identity['sha256']
with tarfile.open(str(root/'preparation_payload.tar.gz')) as tf:
    for item in tf.getmembers():
        p=Path(item.name)
        assert item.isfile() and not p.is_absolute() and '..' not in p.parts and not (root/p).exists()
    tf.extractall(str(root))
for name,h in identity['files'].items():assert sha(root/name)==h,name
overlay=root/'data_overlay';overlay.mkdir()
for child in (source/'data_overlay').iterdir():
    if child.name not in {'flexibility','thermal','hydro'}:(overlay/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
flex=overlay/'flexibility';flex.mkdir()
for child in (source/'data_overlay/flexibility').iterdir():
    if child.name!='participation_pathway_v2':(flex/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
(flex/'participation_pathway_v2').symlink_to(root/'additional_data/flexibility/participation_pathway_v2',target_is_directory=True)
for family in ['thermal','hydro']:
    target=overlay/family;target.mkdir();extra=root/'additional_data'/family
    overrides={p.name:p for p in extra.iterdir()}
    for child in (source/'data_overlay'/family).iterdir():
        if child.name not in overrides:(target/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
    for name,p in overrides.items():(target/name).symlink_to(p)
expected=json.loads((root/'expected_data_files.json').read_text())
for name,v in expected.items():assert sha(overlay/name)==v['sha256'],name
subprocess.check_call(['bash','-n',str(root/'case3_2050.sbatch')])
assert not (root/'FINAL_GATES_PASSED.json').exists() and not (root/'upstream_state').exists()
result=dict(status='PREPARED_NOT_FROZEN_NOT_SUBMITTED',directory=str(root),input_files_verified=len(expected),
    payload_sha256=identity['sha256'],batch_syntax='PASS',framework='A',state='WAIT_CASE3_2040',credentials_read=False)
(root/'preparation_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
'''
    code='from pathlib import Path\nimport hashlib,json,tarfile,subprocess\n'+code
    p=subprocess.run(SSH+['python3 -'],input=code,text=True,capture_output=True,timeout=600)
    (HERE/'cloud_prepare.stderr.log').write_text(p.stderr)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    save(HERE/'cloud_preparation_receipt.json',json.loads(p.stdout));print(p.stdout)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['local','cloud'])
    a=p.parse_args();local() if a.mode=='local' else cloud()
