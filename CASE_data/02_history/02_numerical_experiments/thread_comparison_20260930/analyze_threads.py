"""Read-only server evidence and offline 44/48-thread timing comparison.

Collect: python analyze_threads.py --collect --remote-base <cloud release parent>
Recompute cached evidence: python analyze_threads.py
Outputs: evidence/, manifest.json, comparison.json, windows.csv, iterations.csv.
No solver calls, job submissions, or remote writes. Python standard library only.
"""
from pathlib import Path
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
RELEASES = {
    'base2040_t44': '20260919_base2040_v9_t44_m750_tol1e4_v1',
    'base2030_t48': '20260914_base_v9_t48_m750_tol1e4_v3',
}
FILES = ['output_8760/gurobi.log', 'output_8760/solver_telemetry.jsonl',
         'output_8760/solve_report.json', 'output_8760/solution_qc.json',
         'output_8760/solver_parameters_before_optimize.json',
         'output_8760/run_scope.json', 'output_8760/model_config_snapshot.json',
         'runtime_slurm_job.txt', 'resource_usage.txt', 'batch_exit.json']
PAT = re.compile(r'^\s*(\d+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+(\d+)s\s*$', re.M)
WINDOWS = [(0,39),(10,39),(20,39),(50,97),(50,200),(100,200),
           (200,300),(300,348),(10,348),(0,348),(348,605),(0,605),
           (237,260),(260,277),(277,290),(290,306),(307,317),(317,327)]

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def collect(args):
    if not args.remote_base:
        raise ValueError('--collect requires --remote-base')
    remote = 'from pathlib import Path\nimport json,hashlib,subprocess\n'
    remote += 'base=Path('+repr(args.remote_base)+')\nreleases='+repr(RELEASES)+'\nfiles='+repr(FILES)+'\n'
    remote += '''records={}
for label, release in releases.items():
    for rel in files:
        path=base/release/rel
        if not path.is_file():
            continue
        if path.stat().st_size>12000000:
            raise RuntimeError('Unexpected evidence size: '+str(path))
        raw=path.read_bytes()
        records[label+'__'+rel.replace('/','__')]=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),text=raw.decode('utf-8'))
commands=[['squeue','-u','a8s001819'],['sacct','-j','4682935,4614693,4496031,4533060','--format=JobID,JobName,State,ExitCode,Start,End,Elapsed,ElapsedRaw,AllocCPUS,ReqMem,NodeList,MaxRSS','-P']]
scheduler=[]
for cmd in commands:
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,check=True)
    scheduler.append(dict(command=cmd,stdout=p.stdout,stderr=p.stderr))
print(json.dumps(dict(records=records,scheduler=scheduler)))
'''
    proc = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',
                           args.ssh_host,'python3 -'], input=remote,
                          capture_output=True,text=True,encoding='utf-8',timeout=90)
    if proc.returncode:
        raise RuntimeError('Read-only collection failed: '+proc.stderr[-3000:])
    payload = json.loads(proc.stdout)
    evidence = args.output_dir/'evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    manifest = {'collected_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),
                'source_state':'existing dirty working tree; no production changes', 'files':{}}
    for name, row in payload['records'].items():
        raw = row['text'].encode('utf-8')
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        (evidence/name).write_bytes(raw)
        manifest['files'][name] = {k:row[k] for k in ('path','sha256')}
    for label, name in [('oldbase2030_t44','base_t44_4496031.log'),('thermal2030_t44','thermal_t44_4533060.log')]:
        source = HERE.parent/'base_2040_continuation_20260919/evidence'/name
        raw = source.read_bytes()
        dest = label+'__gurobi.log'
        (evidence/dest).write_bytes(raw)
        manifest['files'][dest] = {'path':str(source.relative_to(HERE.parents[2])), 'sha256':hashlib.sha256(raw).hexdigest()}
    save_json(evidence/'scheduler.json', payload['scheduler'])
    manifest['files']['scheduler.json'] = {'sha256':hashlib.sha256((evidence/'scheduler.json').read_bytes()).hexdigest()}
    save_json(args.output_dir/'manifest.json',manifest)

def analyze(args):
    evidence=args.output_dir/'evidence'
    manifest=json.loads((args.output_dir/'manifest.json').read_text(encoding='utf-8'))
    for name, meta in manifest['files'].items():
        assert hashlib.sha256((evidence/name).read_bytes()).hexdigest()==meta['sha256'],name
    summary={}
    windows=[]
    iterations=[]
    patterns={
        'threads':r'Thread count:.*using up to (\d+) threads',
        'numeric_focus':r'NumericFocus\s+(\d+)',
        'bar_conv_tol':r'^BarConvTol\s+([-+\d.eE]+)',
        'cpu_model':r'CPU model: (.*)',
        'presolve_seconds':r'Presolve time: ([\d.]+)s',
        'ordering_seconds':r'Ordering time: ([\d.]+)s',
        'factor_nz':r'Factor NZ\s*:\s*(\S+)',
        'factor_ops':r'Factor Ops\s*:\s*(\S+)',
        'raw_size':r'Optimize a model with (.*)',
        'presolved_size':r'Presolved: (.*)',
        'terminal':r'Barrier solved model in (.*)',
    }
    for path in sorted(evidence.glob('*gurobi.log')):
        label=path.name.split('__')[0]
        log=path.read_text(encoding='utf-8')
        rows={int(m[1]):dict(iteration=int(m[1]),primal=float(m[2]),dual=float(m[3]),
              pinf=float(m[4]),dinf=float(m[5]),compl=float(m[6]),seconds=int(m[7])) for m in PAT.finditer(log)}
        assert rows and sorted(rows)==list(range(max(rows)+1)),label
        assert all(rows[i]['seconds']>=rows[i-1]['seconds'] for i in range(1,max(rows)+1))
        telemetry={}
        tp=evidence/(label+'__output_8760__solver_telemetry.jsonl')
        if tp.exists():
            for line in tp.read_text(encoding='utf-8').splitlines():
                event=json.loads(line)
                if event.get('phase')=='barrier' and 'iteration' in event:
                    telemetry[int(event['iteration'])]=event
        stats={key:(m.group(1) if (m:=re.search(pattern,log,re.M)) else None) for key,pattern in patterns.items()}
        stats.update(last_iteration=max(rows),first_log_seconds=rows[0]['seconds'],last_log_seconds=rows[max(rows)]['seconds'],telemetry_count=len(telemetry))
        report_path=evidence/(label+'__output_8760__solve_report.json')
        if report_path.exists():
            report=json.loads(report_path.read_text(encoding='utf-8'))
            assert report['iteration_counts']['barrier']==max(rows)
            stats.update(solver_runtime_seconds=report['runtime_seconds'],
                         solver_status=report['status'],qc_status=report['solution_qc_status'],
                         scientifically_accepted=report['scientifically_accepted'],
                         solver_parameters=report['solver_parameters'])
        for a,b in sorted(set(WINDOWS+[(0,max(rows))])):
            if a not in rows or b not in rows: continue
            diffs=[rows[i]['seconds']-rows[i-1]['seconds'] for i in range(a+1,b+1)]
            row=dict(case=label,start=a,end=b,steps=b-a,
                     mean_minutes=statistics.mean(diffs)/60,median_minutes=statistics.median(diffs)/60,
                     min_minutes=min(diffs)/60,max_minutes=max(diffs)/60,work_per_step=None,telemetry_mean_minutes=None)
            if a in telemetry and b in telemetry:
                row['work_per_step']=(telemetry[b]['work_units']-telemetry[a]['work_units'])/(b-a)
                row['telemetry_mean_minutes']=(telemetry[b]['runtime_seconds']-telemetry[a]['runtime_seconds'])/(b-a)/60
                # Callback timings and printed log timings can differ; keep both distinct.
            windows.append(row)
        for i,row in rows.items():
            iterations.append(dict(case=label,**row,delta_seconds=row['seconds']-rows[i-1]['seconds'] if i else None))
        summary[label]=stats
    window_map={(x['case'],x['start'],x['end']):x for x in windows}
    comparisons=[]
    for a,b in [(10,39),(50,97),(50,200),(200,300),(300,348),(10,348)]:
        x=window_map['base2040_t44',a,b];y=window_map['base2030_t48',a,b]
        comparisons.append(dict(start=a,end=b,t44_time_increase_percent=(x['mean_minutes']/y['mean_minutes']-1)*100,
                                t44_work_increase_percent=(x['work_per_step']/y['work_per_step']-1)*100))
    x=summary['base2040_t44'];y=summary['base2030_t48']
    total=x['last_log_seconds']-y['last_log_seconds']
    setup=x['first_log_seconds']-y['first_log_seconds']
    extra=round(window_map['base2040_t44',348,605]['mean_minutes']*60*257)
    decomposition=dict(total_log_runtime_difference_seconds=total,pre_iteration0_difference_seconds=setup,
                       common_iteration0_to348_difference_seconds=total-setup-extra,
                       additional_2040_iteration348_to605_seconds=extra,
                       additional_iterations_share_percent=extra/total*100,
                       caveat='Descriptive time accounting, not a causal attribution to model/year/thread count.')
    parameters_x=x['solver_parameters'];parameters_y=y['solver_parameters']
    parameter_differences={k:[parameters_y.get(k),parameters_x.get(k)] for k in parameters_x.keys()|parameters_y.keys() if parameters_y.get(k)!=parameters_x.get(k)}
    assert parameter_differences=={'threads':[48,44]},parameter_differences
    save_json(args.output_dir/'comparison.json',dict(summary=summary,windows=windows,comparisons=comparisons,
              decomposition=decomposition,solver_parameter_differences=parameter_differences,
              validation='evidence SHA256, contiguous iterations, monotonic log times, terminal counts and solver-parameter diff PASS'))
    for name, records in [('windows.csv',windows),('iterations.csv',iterations)]:
        with (args.output_dir/name).open('w',encoding='utf-8-sig',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(records[0]))
            writer.writeheader(); writer.writerows(records)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    for row in windows:
        if (row['start'],row['end']) in [(10,39),(50,97),(50,200),(200,300),(300,348),(10,348),(348,605)]:
            print(row)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collect',action='store_true')
    parser.add_argument('--remote-base')
    parser.add_argument('--ssh-host',default='paracloud-bscc-a8')
    parser.add_argument('--output-dir',type=Path,default=HERE)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    if args.collect: collect(args)
    analyze(args)

if __name__=='__main__':
    main()
