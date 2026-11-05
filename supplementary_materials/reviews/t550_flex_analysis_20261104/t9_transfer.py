"""Finite serial T9 execution and per-case verified small-file return.

Usage: python t9_transfer.py CASE [CASE ...]. No background monitor or solver.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = ROOT.parent / 'claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'HostName=127.0.0.1', '-o', 'BindAddress=127.0.0.1', 'national-model-server']
PY = '/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
BASE = '/home/zz2/National_model_server'
CASES = {
    'base2030': '20260914_base_v9_t48_m750_tol1e4_v3',
    'base2040': '20260919_base2040_v9_t44_m750_tol1e4_v1',
    'base2050': '20260930_base2050_v9_t48_m750_tol1e4_v1',
    'base2060': '20261012_base2060_v9a12_t48_m750_tol1e4_v1',
    'case3_2030': '20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1',
    'case3_2040': '20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2',
    'c2050': '20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2',
    'nocredit_2030': '20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1',
    'b2030': '20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3',
    'b2040': '20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1',
    'b2050': '20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1',
    'b2060': '20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2',
}


def remote(code, timeout=900):
    r = subprocess.run(SSH + [PY + ' -'], input=code.encode(), capture_output=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace'))
    return r.stdout


def run(case, collect_only=False):
    script = (HERE / 't9_inertia.py').read_bytes()
    encoded = base64.b64encode(script).decode()
    out = BASE + '/analysis_tools_20261105_t9/' + case
    code = 'import base64,hashlib,json,os,subprocess\nfrom pathlib import Path\n'
    code += 'base=Path(' + repr(BASE + '/analysis_tools_20261105_t9') + ')\n'
    code += 'out=Path(' + repr(out) + ')\n'
    code += 'base.mkdir(exist_ok=True)\nscript=base/"t9_inertia.py"\nraw=base64.b64decode(' + repr(encoded) + ')\n'
    code += 'if script.exists():\n assert script.read_bytes()==raw,"script conflict"\nelse:\n script.write_bytes(raw)\n'
    code += 'assert not out.exists(),"case exists; inspect before rerun"\n'
    code += 'command=' + repr([PY, str(BASE + '/analysis_tools_20261105_t9/t9_inertia.py'), '--root', BASE + '/cloud_backup/' + CASES[case], '--out', out]) + '\n'
    code += 'log=base/' + repr(case + '.log') + '\n'
    code += 'with log.open("x") as f:\n r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1"))\n'
    code += 'print(log.read_text())\nassert r.returncode==0,"T9 failed"\n'
    if not collect_only:
        print(remote(code).decode(), flush=True)
    code = 'import hashlib,io,json,sys,tarfile\nfrom pathlib import Path\n'
    code += 'out=Path(' + repr(out) + ')\n'
    code += 'assert json.loads((out/"t9_summary.json").read_text())["status"]=="PASS"\n'
    code += 'files={p.name:p for p in out.iterdir() if p.is_file()}\n'
    code += 'files["scripts/t9_inertia.py"]=out.parent/"t9_inertia.py"\n'
    code += 'files[' + repr('logs/t9_' + case + '.log') + ']=out.parent/' + repr(case + '.log') + '\n'
    code += 'with tarfile.open(fileobj=sys.stdout.buffer,mode="w|") as tf:\n for name,p in files.items():\n  assert p.stat().st_size<=30000000\n  if name.endswith(".json"):name="metadata/"+name\n  tf.add(p,arcname=name,recursive=False)\n'
    data = remote(code)
    dest = DEST / case
    receipt = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        for member in tf:
            assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            raw = tf.extractfile(member).read()
            path = dest / member.name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                assert path.read_bytes() == raw, 'local conflict: ' + str(path)
            else:
                path.write_bytes(raw)
            receipt[member.name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    code = 'import hashlib,json\nfrom pathlib import Path\nroot=Path(' + repr(out) + ')\n'
    code += 'mapping=' + repr({name: (out + '/' + name.split('/')[-1] if name.startswith('metadata/') or '/' not in name else BASE + '/analysis_tools_20261105_t9/t9_inertia.py' if name.startswith('scripts/') else BASE + '/analysis_tools_20261105_t9/' + case + '.log') for name in receipt}) + '\n'
    code += 'print(json.dumps({name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in mapping.items()}))\n'
    hashes = json.loads(remote(code))
    for name, row in receipt.items():
        assert row['sha256'] == hashes[name], name
        row['verified'] = True
    total = sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())
    assert total <= 100_000_000, 'case return ceiling'
    result = dict(status='PASS', case=case, remote=out, files=receipt, new_bytes=sum(r['bytes'] for r in receipt.values()), case_total_bytes=total)
    (HERE / ('t9_receipt_' + case + '.json')).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(case=case, status='RETURNED_SHA_VERIFIED', files=len(receipt), bytes=result['new_bytes'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('cases', nargs='+', choices=list(CASES))
    p.add_argument('--collect-only', action='store_true', help='Resume verified delivery of completed existing T9; never rerun computation.')
    a = p.parse_args()
    for case in a.cases:
        run(case, collect_only=a.collect_only)
