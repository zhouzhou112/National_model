"""Archive this repair's source overlay and hash retained evidence; no solve."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import subprocess
import tarfile

OUT=Path(__file__).parent
ROOT=OUT.parents[2]
FILES=['cispo_full_lp_model_spec.md','cispo_model/config.py','cispo_model/data.py','cispo_model/hydro.py',
       'cispo_model/io_contract.py','cispo_model/master.py','cispo_model/monolithic.py',
       'cispo_model/numerical_cleanup.py','cispo_model/run_contract.py',
       'config/optimization_2030_numeric_repaired.json','config/hydro_storage_corrections_20260913.csv',
       'scripts/prepare_hydro_storage_corrections.py','tests/test_numerical_cleanup.py']


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    archive=OUT/'repair_source_overlay.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name in FILES:tar.add(ROOT/name,arcname=name)
        tar.add(ROOT/'data/hydro/repaired_20260913',arcname='data/hydro/repaired_20260913')
    selected=[ROOT/name for name in FILES]
    selected+=list((ROOT/'data/hydro/repaired_20260913').glob('*'))
    selected+=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
               and p.name!='delivery_manifest.json']
    rows=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
          for p in sorted(set(selected)) if p.is_file()]
    accepted={}
    for hours in (24,168):
        suffix='final900' if hours==168 else 'final'
        p=OUT/'probes'/f'cleaned_nf2_{hours}h_s0_cross2_fullcf_{suffix}/result.json'
        accepted[str(hours)]=json.loads(p.read_text(encoding='utf-8')).get('strict_acceptance',False) if p.is_file() else False
    report={'generated_at':datetime.now().astimezone().isoformat(),
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'uncommitted':True,'final_local_strict_acceptance':accepted,
            'full_year_validated':False,'cloud_solver_jobs_submitted':0,
            'raw_hydro_source_preserved':True,'source_overlay':archive.relative_to(ROOT).as_posix(),
            'files':rows}
    (OUT/'delivery_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
