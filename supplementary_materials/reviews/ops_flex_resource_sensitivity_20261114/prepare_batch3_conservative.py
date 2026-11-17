"""Prepare and verify the three author-authorized conservative cases; no Slurm actions."""
from pathlib import Path
import argparse, hashlib, json, subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / 'batch3_conservative_20261117'
REMOTE = '/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/conservative_gates_20261117'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2', '-o', 'HostName=127.0.0.1', '-o', 'BindAddress=127.0.0.1', 'national-model-server']

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def payload():
    tested = json.loads((HERE/'batch2/full_tests.json').read_text())
    assert tested['status'] == 'PASS'
    for n, h in tested['tested_source_lf_sha256'].items():
        assert hashlib.sha256((REPO/n).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == h, n
    bundle = REPO.parent/'claude_workspace/inputs/flex_resource_scenarios_v1_20261114/conservative'
    audit = json.loads((bundle/'BUILD_AUDIT.json').read_text(encoding='utf-8'))
    expected = json.loads((HERE/'batch2/input_identity_recheck.json').read_text())['local']['conservative']
    assert sha(bundle/'BUILD_AUDIT.json') == expected
    for n, e in audit['files'].items():
        assert (bundle/n).stat().st_size == e['bytes'] and sha(bundle/n) == e['sha256'], n
    years = {}
    for y in (2030, 2040, 2060):
        p = HERE/'batch2'/str(y)
        if y == 2030:
            p /= 'author_window_v2'
        g = json.loads((p/'YEAR_GATES_PASSED.json').read_text())
        r = g['records']['conservative_24h']
        assert g['status'] == 'PASS' and g['all_individual_gates_pass']
        assert r['returncode'] == 0 and r['relative_v1'] == 'PASS' and r['preservation'] == 'COMPLETE'
        assert r['frozen_capacity_output_check.json']['status'] == 'PASS'
        assert r['parameter_verification.json']['status'] == 'PASS'
        if y == 2030:
            assert abs(r['window_carbon_override.json']['effective_window_carbon_limit_mt'] - 10.95890410958904) < 1e-12
        years[str(y)] = dict(source_identity=g['source_identity'], command=r['command'], gate_path=str(p.relative_to(HERE)), gate_sha256=sha(p/'YEAR_GATES_PASSED.json'), gate_lf_sha256=hashlib.sha256((p/'YEAR_GATES_PASSED.json').read_bytes().replace(b'\r\n',b'\n')).hexdigest(), remote_gate_parent=str(Path(r['command'][r['command'].index('--output')+1]).parent).replace('\\','/'), neutrality=g['neutrality_relative_objective_difference'], monotonicity=g['relative_order_violations'])
    return dict(years=years, tested=tested['tested_source_lf_sha256'], audit_sha256=expected, files=audit['files'], cloud_sources=json.loads((HERE/'batch2/cloud_source_file_sha256.json').read_text()), helpers={n:sha(HERE/n) for n in ['resource_gate_batch2.py','resource_audit_batch2.py','resource_gate_2030_author.py','window_gate.py','window_gate_2030_author.py','contractable_total_national_source.csv']})

WORKER = r'''
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
work=Path(sys.argv[1]); data=json.loads((work/'inputs.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
records={}
for year,meta in data['years'].items():
 start=time.time();info=meta['source_identity'];old=meta['command'];helper=Path(old[1]);repo=helper.parents[3];hp=helper.parent
 for n,h in data['tested'].items():assert hashlib.sha256((repo/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,n
 for n in [helper.name,'resource_audit_batch2.py','contractable_total_national_source.csv']:
  assert sha(hp/n)==data['helpers'][n],n
 prior=Path(meta['remote_gate_parent'])/'YEAR_GATES_PASSED.json';assert hashlib.sha256(prior.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==meta['gate_lf_sha256']
 assert sha(Path(info['source'])/'output_8760/result_manifest.json')==info['source_result_manifest_sha256']
 assert sha(info['budget'])==info['budget_sha256']
 if info['closure']:assert sha(info['closure'])==info['closure_sha256']
 root=Path(info['data_roots']['conservative'])
 bundle=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/baseline_runtime/inputs/conservative')
 assert sha(bundle/'BUILD_AUDIT.json')==data['audit_sha256']
 for n,e in data['files'].items():
  assert (bundle/n).stat().st_size==e['bytes'] and sha(bundle/n)==e['sha256'],n
  if n.startswith(('load/','flexibility/')):assert (root/n).stat().st_size==e['bytes'] and sha(root/n)==e['sha256'],n
 for n,e in data['cloud_sources'][year]['data_overlay'].items():
  if n in data['files'] and n.startswith(('load/','flexibility/')):continue
  assert (root/n).stat().st_size==e['bytes'] and sha(root/n)==e['sha256'],n
 for n,e in data['cloud_sources'][year]['frozen_source'].items():
  q=Path(info['source']).parent/n
  assert q.stat().st_size==e['bytes'] and sha(q)==e['sha256'],n
 out=work/year/'conservative_production_1h';out.parent.mkdir(exist_ok=False)
 args=[sys.executable,str(helper),'--year',year,'--mode','frozen','--resource','conservative','--hours','1','--production-profile','--source-release',info['source'],'--supplement',info['supplement'],'--output',str(out)]
 if info['closure']:args+=['--closure',info['closure']]
 env=dict(os.environ,PYTHONPATH=str(repo),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',CISPO_DATA_ROOT=str(root),CISPO_CF_ROOT='/data/zz2/National_model/data/hourly_cf',CISPO_HYDRO_ROOT='/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse',CISPO_RAW_GRFR_ROOT='/data/zz2/National_model/data/grfr_raw_2019',CISPO_WAVE_ROOT='/data/zz2/National_model/data/wave_energy_20260727')
 with (out.parent/'stdout.log').open('x') as f,(out.parent/'stderr.log').open('x') as g:p=subprocess.run(args,cwd=repo,env=env,stdout=f,stderr=g)
 r=dict(year=int(year),command=args,exit_code=p.returncode,seconds=time.time()-start,reused_24h_sha256=meta['gate_sha256'],remote_24h_raw_sha256=sha(prior),source_and_input_recheck='PASS',tested_sources_unchanged=True)
 for n in ['identity_gate_probe.json','parameter_verification.json','build_report.json','run_identity.json']:
  if (out/n).exists():r[n]=json.loads((out/n).read_text())
 probe=r.get('identity_gate_probe.json',{})
 r['status']='PASS' if p.returncode==0 and probe.get('all_investment_families_fixed') is True and r.get('parameter_verification.json',{}).get('status')=='PASS' else 'STOP'
 save(out.parent/'receipt.json',r);records[year]=r;save(work/'results.json',records)
 print(json.dumps(dict(year=year,status=r['status'],seconds=r['seconds'])),flush=True)
save(work/'COMPLETE.json',dict(status='PASS' if all(r['status']=='PASS' for r in records.values()) else 'STOP',years=list(records)))
'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','start','status']);a=ap.parse_args()
    OUT.mkdir(exist_ok=True)
    if a.phase=='prepare':
        data=payload();save(OUT/'inputs.json',data)
        save(OUT/'AUTHORIZATION.json',dict(date='2026-11-17',batch=3,cases=['ops_conservative_2030','ops_conservative_2040','ops_conservative_2060'],late_open_2060_authorized=False,maximum_cloud_jobs=4,threads=44,source='Explicit author chat: second-batch OPS-Open adopted; conservative years released early after individual gates',window_carbon_2030_mt=10.95890410958904))
        (OUT/'t550_worker.py').write_text(WORKER,encoding='utf-8')
        compile(WORKER,'<batch3-worker>','exec')
        print(json.dumps(dict(status='PREPARED',years=list(data['years']),model_changes=False,local_input_sha='PASS')))
        return
    if a.phase=='start':
        code='data='+repr(json.loads((OUT/'inputs.json').read_text()))+'\nworker='+repr(WORKER)+'\nwork='+repr(REMOTE)+'\n'+r'''
from pathlib import Path
import json,subprocess
work=Path(work);assert not work.exists(),'Inspect previous processes/results before restart'
free=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert free>24*2**30,'Insufficient available memory for bounded serial builds'
work.mkdir();(work/'inputs.json').write_text(json.dumps(data,indent=2)+'\n');(work/'worker.py').write_text(worker)
with (work/'worker.stdout.log').open('x') as f,(work/'worker.stderr.log').open('x') as g:
 p=subprocess.Popen(['/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python',str(work/'worker.py'),str(work)],stdin=subprocess.DEVNULL,stdout=f,stderr=g,start_new_session=True)
r=dict(pid=p.pid,work=str(work),available_gib=free/2**30,finite=True);(work/'execution.json').write_text(json.dumps(r)+'\n');print(json.dumps(r))
'''
    else:
        code='work='+repr(REMOTE)+'\n'+r'''
from pathlib import Path
import json
w=Path(work);r={}
for n in ['execution.json','results.json','COMPLETE.json']:
 if (w/n).exists():r[n]=json.loads((w/n).read_text())
for n in ['worker.stdout.log','worker.stderr.log']:
 if (w/n).exists():r[n]=(w/n).read_text()[-4000:]
if 'execution.json' in r:r['process_exists']=Path('/proc/'+str(r['execution.json']['pid'])).exists()
print(json.dumps(r))
'''
    p=subprocess.run(SSH+['python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=180)
    (OUT/(a.phase+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(p.stderr[-3000:]+p.stdout[-1000:])
    r=json.loads(p.stdout);save(OUT/(a.phase+'.json'),r)
    print(json.dumps({k:v for k,v in r.items() if k!='results.json'}))
    if 'results.json' in r:print(json.dumps({k:dict(status=v['status'],seconds=v['seconds']) for k,v in r['results.json'].items()}))

if __name__=='__main__':main()
