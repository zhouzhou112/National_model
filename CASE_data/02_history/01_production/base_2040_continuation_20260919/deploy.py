"""Prepare one new release and validate it; explicitly separate prepare/submit/release."""
from pathlib import Path
import datetime
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REMOTE = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260919_base2040_v9_t44_m750_tol1e4_v1'
SOURCE = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3'
ENV_SOURCE = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_2820fc3_v3'
PROFILE = 'config/solver_profiles/barrier_checkpoint_full_year_cloud_2040_numeric_v1_threads44.json'
STATE = REMOTE+'/upstream_2030_bound_closed/planning_state_candidate'

def remote(code, label):
    compile(code, '<remote>', 'exec')
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20', 'paracloud-bscc-a8', 'python3 -'],
                       input=code, capture_output=True, text=True, encoding='utf-8', timeout=1800)
    (HERE/(label+'.stdout.log')).write_text(p.stdout, encoding='utf-8')
    (HERE/(label+'.stderr.log')).write_text(p.stderr, encoding='utf-8')
    print(p.stdout[-6500:])
    if p.returncode:
        print(p.stderr[-6500:])
    p.check_returncode()

HEADER = 'from pathlib import Path\nimport json,subprocess,hashlib,shutil,os,datetime,re\nroot=Path('+repr(REMOTE)+')\nsource=Path('+repr(SOURCE)+')\nenv_source=Path('+repr(ENV_SOURCE)+')\n'
ENV = '''set -euo pipefail
set -a
source "{env_source}/manifests/cloud_environment_paths.env"
set +a
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${{LD_LIBRARY_PATH:-}}"
export GRB_LICENSE_FILE="${{CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}}"
export http_proxy="${{CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
export CISPO_DATA_ROOT="{root}/data_overlay"
export PYTHONPATH="{root}/repo${{PYTHONPATH:+:$PYTHONPATH}}"
export UPSTREAM_STATE="{source}/output_8760/planning_state_candidate"
cd "{root}/repo"
'''

def main():
    mode = sys.argv[1]
    if mode == 'prepare':
        files = {'repo/'+PROFILE: (REPO/PROFILE).read_text(),
                 'base_2040.sbatch': (HERE/'base_2040.sbatch').read_text(),
                 'validate_2040.py': (HERE/'validate_2040.py').read_text()}
        code = HEADER + 'files='+repr(files)+'\n'+r'''
assert not root.exists(), 'Refuse to overwrite an existing release'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'], cwd=str(source))
root.mkdir()
shutil.copytree(source/'repo',root/'repo',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
(root/'data_overlay').symlink_to(source/'data_overlay',target_is_directory=True)
for rel, content in files.items():
    path=root/rel
    assert not path.exists(), rel
    path.write_text(content)
identity=dict(created_at=datetime.datetime.now().astimezone().isoformat(), predecessor_job='4614693',
              predecessor_release=str(source), predecessor_state=str(source/'output_8760/planning_state_candidate'),
              authorization='User requested continuation into 2040 and return to 44 solver threads on 2026-09-19',
              state_acceptance='UNACCEPTED_CANDIDATE_RETAIN_UPSTREAM_QC', planning_year=2040,
              automatic_successor=False, production_model_code_changed=False)
(root/'source_identity.json').write_text(json.dumps(identity,indent=2)+'\n')
manifest=[]
for path in sorted(root.rglob('*')):
    if path.is_file() and not path.is_symlink():
        manifest.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+str(path.relative_to(root)))
(root/'release_files.sha256').write_text('\n'.join(manifest)+'\n')
subprocess.check_call(['bash','-n','base_2040.sbatch'],cwd=str(root))
print(json.dumps(identity,indent=2))
'''
        remote(code, 'prepare')
    elif mode == 'amend-validator':
        code = HEADER + 'content='+repr((HERE/'validate_2040.py').read_text())+'\n'+r'''
assert not (root/'held_submission.json').exists()
path=root/'validate_2040.py'
before=hashlib.sha256(path.read_bytes()).hexdigest()
history=root/'preparation_history'
history.mkdir(exist_ok=True)
shutil.copy2(path,history/('validate_2040_'+before+'.py'))
path.write_text(content)
after=hashlib.sha256(path.read_bytes()).hexdigest()
manifest=root/'release_files.sha256'
lines=manifest.read_text().splitlines()
lines=[after+'  validate_2040.py' if line.endswith('  validate_2040.py') else line for line in lines]
manifest.write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(before=before,after=after,reason='Preparation-only validation helper fix; model and execution profile unchanged')))
'''
        remote(code, mode)
    elif mode == 'close-state':
        bash = ENV.format(root=REMOTE, source=SOURCE, env_source=ENV_SOURCE)
        bash += '"$PYTHON" "'+REMOTE+'/prepare_bound_closed_state.py"\n'
        code = HEADER+'(root/"prepare_bound_closed_state.py").write_text('+repr((HERE/'prepare_bound_closed_state.py').read_text())+')\n'
        code += 'p=subprocess.run(["bash"],input='+repr(bash)+',universal_newlines=True)\nassert p.returncode==0\n'
        code += r'''
manifest=root/'release_files.sha256'
lines=manifest.read_text().splitlines()
for path in sorted((root/'upstream_2030_bound_closed').rglob('*'))+[root/'prepare_bound_closed_state.py']:
    if path.is_file(): lines.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+str(path.relative_to(root)))
manifest.write_text('\n'.join(lines)+'\n')
'''
        remote(code, mode)
    elif mode == 'audit':
        bash = ENV.format(root=REMOTE, source=SOURCE, env_source=ENV_SOURCE)
        bash += '"$PYTHON" "'+REMOTE+'/audit_state_bounds.py"\n'
        code = HEADER+'(root/"audit_state_bounds.py").write_text('+repr((HERE/'audit_state_bounds.py').read_text())+')\n'
        code += 'p=subprocess.run(["bash"],input='+repr(bash)+',universal_newlines=True)\nraise SystemExit(p.returncode)\n'
        remote(code, mode)
    elif mode in ('preflight','validate'):
        bash = ENV.format(root=REMOTE, source=SOURCE, env_source=ENV_SOURCE)
        bash += 'export UPSTREAM_STATE="'+STATE+'"\n'
        if mode == 'preflight':
            bash += '"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9.json --solver-config '+PROFILE+' --planning-year 2040 --horizon full_year --state-in "$UPSTREAM_STATE" --allow-candidate-state-in --engineering-barrier-checkpoint-only --preflight-only --output-dir "'+REMOTE+'/preflight_bound_closed" > "'+REMOTE+'/preflight_bound_closed.log" 2> "'+REMOTE+'/preflight_bound_closed.err"\n'
        else:
            bash += '"$PYTHON" "'+REMOTE+'/validate_2040.py" > "'+REMOTE+'/validation_2040.log" 2> "'+REMOTE+'/validation_2040.err"\n'
        code = HEADER+'script='+repr(bash)+'\n'+'''
p=subprocess.run(['bash'],input=script,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
print(json.dumps(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)))
'''
        name = 'preflight_bound_closed/preflight_report.json' if mode=='preflight' else 'validation_2040.json'
        code += 'path=root/'+repr(name)+'\nif path.exists(): print(path.read_text())\n'
        code += 'raise SystemExit(p.returncode)\n'
        remote(code, mode)
    elif mode == 'submit':
        code = HEADER+'''
assert json.loads((root/'preflight_bound_closed/preflight_report.json').read_text())['status']=='PASS'
assert json.loads((root/'validation_2040.json').read_text())['status']=='PASS'
assert not (root/'held_submission.json').exists()
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
exports='ALL,SOURCE_RELEASE='+str(env_source)+',UPSTREAM_STATE='+str(root/'upstream_2030_bound_closed/planning_state_candidate')
test=subprocess.run(['sbatch','--test-only','--export='+exports,'base_2040.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
(root/'submission_test.json').write_text(json.dumps(dict(returncode=test.returncode,stdout=test.stdout,stderr=test.stderr),indent=2))
assert test.returncode==0, test.stderr
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'base_2040.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
record=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,submitted_at=datetime.datetime.now().astimezone().isoformat())
(root/'held_submission.json').write_text(json.dumps(record,indent=2))
assert p.returncode==0, record
job=p.stdout.strip().split(';')[0]
assert job.isdigit()
record['job_id']=job
record['scontrol']=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
(root/'held_submission.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
'''
        remote(code, mode)
    elif mode == 'release':
        code = HEADER+'''
assert not (root/'release_job.json').exists()
job=json.loads((root/'held_submission.json').read_text())['job_id']
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
assert 'Reason=JobHeldUser' in record and 'TimeLimit=UNLIMITED' in record, record
req=re.search(r'\\bReqTRES=(\\S+)',record).group(1)
tres=dict(x.split('=',1) for x in req.split(','))
assert tres['cpu']=='64' and tres['billing']=='64' and tres['mem']=='750G', tres
subprocess.check_call(['scontrol','release',job])
after=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
result=dict(job_id=job,released_at=datetime.datetime.now().astimezone().isoformat(),scontrol=after)
(root/'release_job.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
'''
        remote(code, mode)
    elif mode == 'status':
        code = HEADER+'''
job=json.loads((root/'held_submission.json').read_text())['job_id']
result={'job_id':job,'scontrol':subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)}
for rel in ['compute_node_smoke.json','continuation_contract_check.json','batch_exit.json','stderr.log','startup_regression.log','stdout.log','output_8760/run_scope.json','output_8760/gurobi.log']:
    p=root/rel
    if p.is_file(): result[rel]=p.read_text()[-4500:]
print(json.dumps(result,indent=2))
'''
        remote(code, mode+'_'+datetime.datetime.now().strftime('%H%M%S'))
    else:
        raise SystemExit('Unknown mode')

if __name__ == '__main__':
    main()
