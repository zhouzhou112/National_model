"""Finite, serial year-specific B gates. Stop immediately on a failed gate."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=HERE.parent/'base_frozen_B_20261026'
SOURCES={2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',2050:'20260930_base2050_v9_t48_m750_tol1e4_v1',2060:'20261012_base2060_v9a12_t48_m750_tol1e4_v1'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('year',type=int,choices=SOURCES)
    p.add_argument('--attempt',type=int,default=1);a=p.parse_args()
    work=HERE/str(a.year)
    if a.attempt!=1:work=work/('attempt_'+str(a.attempt))
    work.mkdir(exist_ok=True)
    source=HERE.parent/'base_frozen_followups_20261027/source_base'/SOURCES[a.year]
    closure=HERE/str(a.year)/'derived_static/closure.json'
    supplement=source/'frozen_capacity_B_20261027'
    assert json.loads((supplement/'supplement_manifest.json').read_text())['status']=='PASS'
    def run(name,command):
        with (work/(name+'.log')).open('x',encoding='utf-8') as log:
            proc=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        if proc.returncode:raise RuntimeError(name+' failed; retained '+str(work/(name+'.log')))
        print(name+' completed (exit 0; inspect result checks)',flush=True)
    for mode,hours,name in [('frozen',1,'frozen_1h'),('base-control',24,'base_control_24h'),('zero',24,'zero_24h'),('frozen',24,'frozen_24h')]:
        run(name,[sys.executable,str(OLD/'run_gate.py'),'--year',str(a.year),'--mode',mode,'--hours',str(hours),
                  '--source-release',str(source),'--supplement',str(supplement),'--closure',str(closure),'--output',str(work/name)])
        if name=='frozen_1h':
            diagnostic=work/'frozen_1h_fixed_capacity_conflicts.json'
            run('fixed_capacity_static_audit',[sys.executable,str(HERE.parent/'base_frozen_followups_20261027/diagnose_fixed_capacity_conflicts.py'),
                str(work/name),'--output',str(diagnostic)])
            if json.loads(diagnostic.read_text())['conflicts']:
                raise RuntimeError('Fixed-capacity static contradictions; stop before 24h. See '+str(diagnostic))
    for name,script in [('compare','compare_identity_gate.py'),('crosscheck','crosscheck_saved_solutions.py'),('assess','assess_revised_identity.py')]:
        run(name,[sys.executable,str(OLD/script),str(work)])
    import gurobipy as gp
    archive=work/'frozen_1h/model_archive/original.mps'
    if not archive.exists():archive=archive.with_suffix('.mps.gz')
    model=gp.read(str(archive))
    variables={v.VarName:v for v in model.getVars()}
    with (work/'frozen_1h/frozen_capacity_audit.csv').open() as stream:rows=list(csv.DictReader(stream))
    changes={r['variable']:r['after_gw'] for r in json.loads(closure.read_text())['rows']}
    fixed=all(variables[r['variable']].LB==variables[r['variable']].UB and abs(variables[r['variable']].LB-changes.get(r['variable'],float(r['frozen_value'])))<=1e-12 for r in rows)
    model.dispose()
    def read(p):return json.loads((work/p).read_text())
    checks={'mps_investment_fixed':fixed,'closure_audit':read('frozen_1h/frozen_capacity_closure_report.json')['status']=='PASS','identity_1':read('revised_identity_20261026/assessment.json')['status']=='PASS',
            'identity_2':read('frozen_24h/frozen_capacity_output_check.json')['status']=='PASS'}
    for name in ['frozen_1h','frozen_24h']:
        checks[name+'.source_alignment']=read(name+'/frozen_capacity_source_alignment.json')['status']=='PASS'
        checks[name+'.parameters']=read(name+'/parameter_verification.json')['status']=='PASS'
        checks[name+'.clip_gate']=not read(name+'/frozen_capacity_report.json')['clip_reporting_threshold_exceeded']
    for name in ['base_control_24h','zero_24h','frozen_24h']:
        checks[name+'.optimal']=read(name+'/solve_report.json')['status']=='OPTIMAL'
        checks[name+'.relative']=read(name+'/solution_qc.json')['acceptance_profiles']['relative_v1']['status']=='PASS'
        pres=read(name+'/preservation_report.json');checks[name+'.preservation']=pres['status']=='COMPLETE' and not pres['errors']
    paths=subprocess.check_output(['git','ls-files','cispo_model','config','scripts','tests'],cwd=ROOT,text=True).splitlines()+['cispo_model/frozen_closure.py','tests/test_frozen_closure.py']
    hashes={s:hashlib.sha256((ROOT/s).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for s in sorted(set(paths)) if (ROOT/s).is_file()}
    report=dict(status='PASS' if all(checks.values()) else 'FAIL',framework='B',planning_year=a.year,production_threads=48,
                source_base=SOURCES[a.year],checks=checks,tested_source_lf_sha256=hashes,investment_columns=len(rows),
                result_use='TEST_ONLY_TRUNCATED_HORIZON',source_collection_sha256=hashlib.sha256((HERE.parent/'base_frozen_followups_20261027/source_collection.json').read_bytes()).hexdigest())
    (work/'FINAL_GATES_PASSED.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],{k:v for k,v in checks.items() if not v})
    if report['status']!='PASS':raise SystemExit(2)


if __name__=='__main__':main()
