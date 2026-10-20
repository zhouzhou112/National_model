"""Run the existing relative_v1 CLI on verified T550 data and return exact bytes.

No source-result changes, solver calls, or repeated data transfers. Assessment
sidecars live outside output_8760. Existing identical inputs/tools can be reused;
conflicting bytes are refused. All statuses, including failures, are returned.
"""
from pathlib import Path
import base64
import hashlib
import json
import subprocess
from collect_evidence import RELEASES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
       "-o", "HostName=127.0.0.1", "-o", "BindAddress=127.0.0.1",
       "national-model-server"]
REMOTE = r'''
from pathlib import Path
import base64, hashlib, json, subprocess, sys, datetime
tools=Path('/home/zz2/National_model_server/acceptance_tools_20261020_completed')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def write_new_or_equal(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data, 'Refuse conflicting bytes: '+str(path)
    else:path.write_bytes(data)
for name,content in tool_files.items():
    write_new_or_equal(tools/name,base64.b64decode(content))
sys.path.insert(0,str(tools))
from cispo_model.relative_acceptance import archived_inputs, VERSION
base=Path('/home/zz2/National_model_server/cloud_backup')
op=base/'_operations/20261020_base2060_case3_2030'
status=json.loads((op/'transfer_status.json').read_text())
plan=json.loads((op/'backup_plan.json').read_text())
result={}
for key,release in releases.items():
    assert all(any(s['release']==release and s['tier']==tier and s['status']=='VERIFIED'
                   for s in status['stages']) for tier in ['T1','T2'])
    source=base/release/'output_8760'
    target=base/release/'acceptance_relative_v1_20261020_completed'
    target.mkdir(exist_ok=True)
    assert json.loads((source/'preservation_report.json').read_text())['status']=='COMPLETE'
    entries={r['path']:r for r in json.loads((source/'result_manifest.json').read_text())['files']}
    names=list(collection[key]['files'])
    names += ['hourly_province_balance.csv.gz','reservoir_dispatch.npz']
    hashes={name:sha(source/name) for name in names}
    for name,digest in hashes.items():
        if name in entries:
            assert digest==entries[name]['sha256'],name
            assert (source/name).stat().st_size==entries[name]['bytes'],name
        if name in collection[key]['files']:
            assert digest==collection[key]['files'][name]['sha256'],name
    inputs=target/'assessment_inputs.json'
    if not inputs.exists():
        inputs.write_bytes((json.dumps(archived_inputs(source),indent=2,allow_nan=False)+'\n').encode())
    output=target/'solution_qc_relative_v1.json'
    if not output.exists():
        run=subprocess.run([sys.executable,str(tools/'scripts/assess_relative_v1.py'),
            str(source),'--inputs',str(inputs),'--output',str(output)],
            capture_output=True,text=True)
        assert run.returncode in [0,2] and output.exists(),run.stdout+run.stderr
    assessment=json.loads(output.read_text())
    assert assessment['source_sha256']=={
        str(source/'solution_qc.json'):hashes['solution_qc.json'],
        str(source/'solve_report.json'):hashes['solve_report.json'],
        str(inputs):sha(inputs)}
    assert assessment['acceptance_profiles']['relative_v1']['version']==VERSION
    assert hashes=={name:sha(source/name) for name in names},'Source bytes changed'
    evidence=dict(
        generated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_sha256=hashes,archive=str(source),sidecar=str(target),
        source_unchanged=True,
        source_result_manifest_sha256=hashes['result_manifest.json'],
        cloud_collection_matches=True,manifest_verified=[n for n in hashes if n in entries],
        evaluator_version=VERSION,tool_sha256={n:sha(tools/n) for n in tool_files},
        git_commit=git_commit,
        backup_verified_tiers_at_assessment=['T1','T2'],
        backup_operation=str(op),backup_plan_result_identity=plan['releases'][release]['result_manifest_sha256'])
    assert evidence['source_result_manifest_sha256']==evidence['backup_plan_result_identity']
    evidence_path=target/'evidence_manifest.json'
    if not evidence_path.exists():
        evidence_path.write_bytes((json.dumps(evidence,indent=2)+'\n').encode())
    else:
        existing=json.loads(evidence_path.read_text())
        assert existing['source_sha256']==hashes and existing['tool_sha256']==evidence['tool_sha256']
    payload={}
    for path in [inputs,output,evidence_path]:
        raw=path.read_bytes()
        payload[path.name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
            base64=base64.b64encode(raw).decode())
    result[key]=dict(status=assessment['acceptance_profiles']['relative_v1']['status'],
        sidecar=str(target),files=payload)
print(json.dumps(result))
'''


def main():
    files = {name: base64.b64encode((ROOT / name).read_bytes()).decode()
             for name in ["cispo_model/relative_acceptance.py", "scripts/assess_relative_v1.py"]}
    files["cispo_model/__init__.py"] = ""
    collection = json.loads((HERE / "collection_manifest.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    code = ("tool_files=" + repr(files) + "\nreleases=" + repr(RELEASES)
            + "\ncollection=" + repr(collection) + "\ngit_commit=" + repr(commit) + "\n" + REMOTE)
    process = subprocess.run(
        SSH + ["/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -"],
        input=code, capture_output=True, text=True, encoding="utf-8", timeout=600)
    (HERE / "assessment.stderr.log").write_text(process.stderr, encoding="utf-8")
    process.check_returncode()
    result = json.loads(process.stdout)
    for key, entry in result.items():
        directory = HERE / "assessments" / key
        directory.mkdir(parents=True, exist_ok=True)
        for name, item in entry["files"].items():
            raw = base64.b64decode(item.pop("base64"))
            assert len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"]
            path = directory / name
            if path.exists():
                assert path.read_bytes() == raw, path
            else:
                path.write_bytes(raw)
    (HERE / "assessment_byte_verification.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({key: item["status"] for key, item in result.items()}))


if __name__ == "__main__":
    main()
