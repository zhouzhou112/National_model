"""One-shot immutable T550 collection, assessment and pricing of completed runs.

Usage: python postprocess.py case3_2040|B2030 collect|assess|price
Reuses the nocredit collector (every output file <=32 MiB), source SHA checks,
and existing scientific evaluators. Full pricing certificates stay on T550.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.util
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RELEASES = {
    'case3_2040': '20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2',
    'B2030': '20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3',
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('case', choices=RELEASES)
    p.add_argument('action', choices=['collect', 'assess', 'price'])
    p.add_argument('--cloud-collect', action='store_true', help='Read small files from cloud when T550 forwarding is unavailable')
    a = p.parse_args()
    if a.case == 'B2030' and a.action == 'price':
        p.error('Unscreened B needs no screening certificate')
    path = HERE.parent/'case3_2050_preparation_20261026/remote_work.py'
    spec = importlib.util.spec_from_file_location('nocredit_workflow', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    names = ['scripts/price_screened_candidates.py', 'scripts/assess_relative_v1.py',
             'cispo_model/vre_pricing.py', 'cispo_model/relative_acceptance.py']
    files = {n: base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    files['cispo_model/__init__.py'] = ''
    if a.action == 'collect':
        files = {}  # Collection needs no scientific evaluator deployment.
    tools = 'postprocess_tools_20261027_collection' if a.action == 'collect' else 'postprocess_tools_20261027_mt'
    common = m.COMMON.replace('postprocess_tools_20261026', tools)
    common = common.replace('postprocess_20261026', 'postprocess_20261027_mt')
    code = ('nocredit='+repr(RELEASES[a.case])+'\nbase2060='+repr(m.BASE2060)
            +'\ntool_files='+repr(files)+'\n'+common+m.ACTIONS[a.action])
    ssh, python = m.SSH, m.PYTHON
    if a.cloud_collect:
        if a.action != 'collect':
            p.error('--cloud-collect only permits small-file collection')
        helpers = m.COMMON[m.COMMON.index('def sha(p):'):m.COMMON.index('for rel in [nocredit,base2060]:')]
        cloudroot = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/'+RELEASES[a.case]+'/output_8760'
        code = 'from pathlib import Path\nimport json,base64,hashlib\nroot=Path('+repr(cloudroot)+')\n'+helpers+m.ACTIONS['collect']
        ssh, python = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20', 'paracloud-bscc-a8'], 'python3'
    compile(code, '<completed-postprocess>', 'exec')
    dest = HERE/a.case
    dest.mkdir(parents=True, exist_ok=True)
    receipt = dest/(a.action+'_receipt.json')
    if receipt.exists():
        raise FileExistsError('Review existing receipt before repeating: '+str(receipt))
    proc = subprocess.run(ssh+[python+' -'], input=code, text=True,
                          encoding='utf-8', capture_output=True, timeout=14400)
    (dest/(a.action+'.stderr.log')).write_text(proc.stderr, encoding='utf-8')
    if proc.returncode:
        raise RuntimeError(proc.stderr[-4000:]+proc.stdout[-1000:])
    result = json.loads(proc.stdout)
    if a.cloud_collect:
        plan = json.loads((HERE.parent/'cloud_backup_20261027/progress_initial.json').read_text())['backup_plan.json']
        assert result['result_manifest_sha256'] == plan['releases'][RELEASES[a.case]]['result_manifest_sha256']
        result['transport'] = 'cloud read-only fallback; identity equals verified T550 backup plan'
    if a.action in ['collect', 'assess']:
        for name, entry in result['files'].items():
            raw = base64.b64decode(entry.pop('base64'))
            assert len(raw) == entry['bytes']
            assert hashlib.sha256(raw).hexdigest() == entry['sha256']
            rel = Path(name)
            assert not rel.is_absolute() and '..' not in rel.parts
            target = dest/('output_8760' if a.action == 'collect' else 'assessment')/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                assert target.read_bytes() == raw
            else:
                target.write_bytes(raw)
    receipt.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(case=a.case, action=a.action, status=result.get('status'),
                         files=len(result.get('files', {})), receipt=str(receipt))))


if __name__ == '__main__':
    main()
