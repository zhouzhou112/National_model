"""Author-authorized C2050 retry: fresh release, 40 solver threads, unchanged LP.

Run prepare, preflight, submit, release, status sequentially. Each mutation refuses
blind repetition. Reads the old release only; never changes other jobs.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
from deploy_continuation import BASE, ENV_SOURCE, HOST, REPO, HERE, environment, remote, save, sha

NAME = "20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1"
OLD = BASE + "/20261020_lateentry_2050_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1"
ROOT = BASE + "/" + NAME
EVIDENCE = HERE / "deployment_C2050_t40"
PROFILE = "config/solver_profiles/barrier_stagea_screened_agg0_2050_v1_threads40.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "preflight", "submit", "release", "status"))
    args = parser.parse_args()
    EVIDENCE.mkdir(exist_ok=True)
    if args.mode == "prepare":
        gates = json.loads((EVIDENCE / "gates.json").read_text(encoding="utf-8"))
        assert gates["status"] == "PASS"
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
        for path, expected in gates["tested_source_lf_sha256"].items():
            blob = subprocess.check_output(["git", "show", commit + ":" + path], cwd=REPO)
            assert hashlib.sha256(blob).hexdigest() == expected, path
        archive = subprocess.check_output(["git", "archive", commit, "cispo_model", "config", "scripts", "tests", "AGENTS.md"], cwd=REPO)
        batch_path = (HERE.relative_to(REPO) / "C2050_threads40.sbatch").as_posix()
        batch = subprocess.check_output(["git", "show", commit + ":" + batch_path], cwd=REPO)
        assert batch == (HERE / "C2050_threads40.sbatch").read_bytes().replace(b"\r\n", b"\n")
        launch = dict(release=NAME, source_commit=commit, scenario="case3_thermal_ev_v5",
                      planning_year=2050, boundary_year=2040, framework="C_Late-entry",
                      state_input="upstream_state/planning_state_candidate", solver_profile=PROFILE,
                      screening_margin=.2, upstream_release=OLD, previous_failed_job="5201262",
                      authorization="Author 2026-10-20: start C2050 with 40 solver threads",
                      automatic_successor=False, stage_b=False,
                      resources=dict(cpus=64, memory="750G", billing=64, time_limit="UNLIMITED",
                                     requeue=False, solver_threads=40, minimum_available_memory_gib=700),
                      gates_sha256=sha(EVIDENCE / "gates.json"))
        save(EVIDENCE / "launch_config.json", launch)
        payload = EVIDENCE / "release_payload.tar.gz"
        hashes = {}
        with tarfile.open(fileobj=io.BytesIO(archive)) as source, tarfile.open(payload, "w:gz") as target:
            def add(name, data):
                member = tarfile.TarInfo(name)
                member.size, member.mode = len(data), 0o640
                target.addfile(member, io.BytesIO(data))
            for member in source.getmembers():
                if member.isfile():
                    data = source.extractfile(member).read()
                    add("repo/" + member.name, data)
                    hashes[member.name] = hashlib.sha256(data).hexdigest()
            add("continuation.sbatch", batch)
            add("launch_config.json", (EVIDENCE / "launch_config.json").read_bytes())
            add("local_threads40_gates.json", (EVIDENCE / "gates.json").read_bytes())
        remote("assert not root.exists()\nroot.mkdir()\nprint(json.dumps({'created':str(root)}))",
               ROOT, EVIDENCE, "create")
        subprocess.run(["scp", "-o", "BatchMode=yes", str(payload), HOST + ":" + ROOT + "/release_payload.tar.gz"], check=True)
        result = remote("old=Path(" + repr(OLD) + ")\nexpected_repo=" + repr(hashes) +
                        "\ncommit=" + repr(commit) + "\npayload_sha=" + repr(sha(payload)) +
                        "\nprofile_path=" + repr(PROFILE) + "\n" + r'''
import shutil
assert hashlib.sha256((root/'release_payload.tar.gz').read_bytes()).hexdigest()==payload_sha
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(old))
old_manifest_sha=hashlib.sha256((old/'release_files.sha256').read_bytes()).hexdigest()
with tarfile.open(str(root/'release_payload.tar.gz')) as tf:
    for item in tf.getmembers():
        p=Path(item.name)
        assert item.isfile() and not p.is_absolute() and '..' not in p.parts
        assert not (root/p).exists()
    tf.extractall(str(root))
for path,h in expected_repo.items():
    assert hashlib.sha256((root/'repo'/path).read_bytes()).hexdigest()==h,path
shutil.copytree(str(old/'upstream_state'),str(root/'upstream_state'))
for name in ['source_screen.csv','local_engineering_gates.json']:
    shutil.copy2(str(old/name),str(root/name))
overlay=root/'data_overlay';overlay.mkdir()
for child in (old/'data_overlay').iterdir():
    (overlay/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
expected=json.loads((old/'data_overlay_sha256.json').read_text())
assert len(expected)==58
for path,h in expected.items():
    assert hashlib.sha256((overlay/path).read_bytes()).hexdigest()==h,path
state_hashes={}
for p in sorted((root/'upstream_state').rglob('*')):
    if p.is_file():
        rel=str(p.relative_to(root/'upstream_state'))
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        assert h==hashlib.sha256((old/'upstream_state'/rel).read_bytes()).hexdigest(),rel
        state_hashes[rel]=h
profile=json.loads((root/'repo'/profile_path).read_text())
assert hashlib.sha256((root/'source_screen.csv').read_bytes()).hexdigest()==profile['candidate_screen']['source_csv_sha256']
assert profile['numerics']['threads']==40 and profile['numerics']['aggregate']==0
(root/'cloud_source_repo_sha256.json').write_text(json.dumps(dict(source_commit=commit,files=expected_repo),indent=2)+'\n')
(root/'data_overlay_sha256.json').write_text(json.dumps(expected,indent=2)+'\n')
(root/'upstream_state_sha256.json').write_text(json.dumps(state_hashes,indent=2)+'\n')
(root/'old_release_provenance.json').write_text(json.dumps(dict(release=str(old),manifest_sha256=old_manifest_sha,verified=True),indent=2)+'\n')
subprocess.check_call(['bash','-n','continuation.sbatch'],cwd=str(root))
paths=[p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and 'data_overlay' not in p.relative_to(root).parts]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(paths)))
assert hashlib.sha256((old/'release_files.sha256').read_bytes()).hexdigest()==old_manifest_sha
print(json.dumps(dict(status='FROZEN',release=str(root),source_commit=commit,repo_files=len(expected_repo),data_files=len(expected),state_files=state_hashes,source_manifest_sha256=hashlib.sha256((root/'cloud_source_repo_sha256.json').read_bytes()).hexdigest(),release_manifest_sha256=hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest())))
''', ROOT, EVIDENCE, "freeze")
        save(EVIDENCE / "frozen_release.json", result)
    elif args.mode == "preflight":
        script = environment(ROOT) + f'''"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9_a12.json --scenario-config config/scenarios/case3_thermal_ev_v5.json --solver-config {PROFILE} --planning-year 2050 --state-in "{ROOT}/upstream_state/planning_state_candidate" --allow-candidate-state-in --late-entry-base-state --vre-screen-csv "{ROOT}/source_screen.csv" --horizon full_year --allow-nonbasic-planning-state --preflight-only --output-dir "{ROOT}/preflight" > "{ROOT}/preflight.log" 2>&1
'''
        result = remote("script=" + repr(script) + "\nold=Path(" + repr(OLD) + ")\n" + r'''
assert not (root/'preflight').exists(),'Do not retry a failed preflight in place'
p=subprocess.run(['bash'],input=script,universal_newlines=True)
if p.returncode:
    print((root/'preflight.log').read_text()[-4500:]);raise SystemExit(p.returncode)
report=json.loads((root/'preflight/preflight_report.json').read_text())
assert report['status']=='PASS'
import csv
def rows(path):
    with path.open(encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))
new=rows(root/'preflight/input_manifest.csv')
prior=rows(old/'preflight_v2/input_manifest.csv')
required=[x for x in new if x['required']=='True']
old_required=[x for x in prior if x['required']=='True']
assert len(required)==len(old_required)==79
config_kinds={'configuration','technology_parameter_registry','scenario_configuration','solver_configuration','input_contract'}
assert sum(x['kind'] not in config_kinds for x in required)==74
# Matching paths after removing release identity: solver profile is the sole
# intentionally changed input; every data/state/scenario/config SHA is exact.
def key(row):
    path=row['resolved_path']
    for prefix in (str(root),str(old)):
        if path.startswith(prefix):return path[len(prefix):]
    return path
by_key={key(x):x for x in old_required}
matched=0
for row in required:
    if 'threads40.json' in row['resolved_path']:
        assert row['sha256']==hashlib.sha256((root/'repo'/json.loads((root/'launch_config.json').read_text())['solver_profile']).read_bytes()).hexdigest()
        continue
    k=key(row)
    assert k in by_key and row['sha256']==by_key[k]['sha256'],k
    matched+=1
print(json.dumps(dict(status='PASS',required_count=len(required),unchanged_required_sha_count=matched,report=report)))
''', ROOT, EVIDENCE, "preflight")
        save(EVIDENCE / "cloud_preflight.json", result)
    elif args.mode == "submit":
        result = remote("exports=" + repr("ALL,SOURCE_RELEASE=" + ENV_SOURCE) + "\n" + r'''
assert json.loads((root/'preflight/preflight_report.json').read_text())['status']=='PASS'
assert not (root/'submission_attempt.json').exists()
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
test=subprocess.run(['sbatch','--test-only','--export='+exports,'continuation.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
assert test.returncode==0,test.stderr
(root/'submission_attempt.json').write_text(json.dumps(dict(test_stdout=test.stdout,test_stderr=test.stderr)))
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'continuation.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
receipt=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2))
assert p.returncode==0,receipt
job=p.stdout.strip().split(';')[0];assert job.isdigit()
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
receipt.update(job_id=job,scontrol=record,released=False)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2))
tres=dict(x.split('=',1) for x in re.search(r'\bReqTRES=(\S+)',record).group(1).split(','))
assert tres['cpu']=='64' and tres['mem'] in ['750G','768000M'] and tres['billing']=='64'
assert 'JobState=PENDING' in record and 'Reason=JobHeldUser' in record and 'TimeLimit=UNLIMITED' in record and 'Requeue=0' in record
receipt['resource_check']='PASS'
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
''', ROOT, EVIDENCE, "submit")
        save(EVIDENCE / "held_submission.json", result)
    elif args.mode == "release":
        assert json.loads((EVIDENCE / "cloud_preflight.json").read_text())["status"] == "PASS"
        result = remote(r'''
receipt=json.loads((root/'held_submission.json').read_text())
assert receipt['resource_check']=='PASS' and not (root/'release_receipt.json').exists()
job=receipt['job_id']
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
assert 'Reason=JobHeldUser' in record and 'JobState=PENDING' in record
subprocess.check_call(['scontrol','release',job])
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
result=dict(job_id=job,release=str(root),released=True,scontrol=record)
(root/'release_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
''', ROOT, EVIDENCE, "release")
        save(EVIDENCE / "release_receipt.json", result)
    else:
        result = remote(r'''
job=json.loads((root/'held_submission.json').read_text())['job_id']
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
result=dict(job_id=job,scontrol=record)
for name in ['compute_node_smoke.json','startup_regression.log','batch_exit.json','stderr.log','stdout.log']:
    path=root/name
    if path.exists():
        if path.suffix=='.json':result[name]=json.loads(path.read_text())
        else:
            with path.open('rb') as stream:
                stream.seek(max(0,path.stat().st_size-5000))
                result[name]=stream.read().decode('utf-8',errors='replace')
print(json.dumps(result))
''', ROOT, EVIDENCE, "status")
        save(EVIDENCE / "startup_status.json", result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
