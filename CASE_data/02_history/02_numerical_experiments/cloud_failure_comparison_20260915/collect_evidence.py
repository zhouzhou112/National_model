"""Read-only cloud log snapshot; no Gurobi import, solve or server mutation.

Run with Python from any directory. Writes evidence/ beside this script.
"""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
PREFIX = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/'
CASES = {
    'base_old': PREFIX + '20260903_8760_stagea_final_2820fc3_v3/outputs/2030_base_8760_rows8192_stagea_final_t32_mem550_slurm32_no_softmem_2820fc3_v4',
    'thermal': PREFIX + '20260907_thermal_stagea_1e4_t44_ffd651a_v2/outputs/2030_case1_thermal_v5_8760_rows8192_t44_m700_tol1e4_ffd651a_v2',
    'base_v9': PREFIX + '20260914_base_v9_t48_m750_tol1e4_v3/output_8760',
}
FILES = ['gurobi.log', 'solve_report.json', 'solution_qc.json', 'preservation_report.json', 'barrier_checkpoint_error.json', 'build_report.json', 'model_config_snapshot.json', 'solver_parameters_before_optimize.json', 'model_archive/parameters.prm']

def main():
    dest = ROOT / 'evidence'
    dest.mkdir(exist_ok=True)
    remote = 'import os,json\n'
    remote += 'cases=' + repr(CASES) + '\nfiles=' + repr(FILES) + '\n'
    remote += '''result={}
for name,root in cases.items():
    result[name]={}
    for rel in files:
        p=os.path.join(root,rel)
        if os.path.isfile(p):
            with open(p) as f: result[name][rel]=f.read()
print(json.dumps(result))
'''
    proc = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'], input=remote, text=True, encoding='utf-8', capture_output=True, timeout=90)
    proc.check_returncode()
    payload = json.loads(proc.stdout)
    manifest = {'retrieved_at':datetime.datetime.now().astimezone().isoformat(), 'remote_roots':CASES, 'operation':'read-only SSH; no optimize or job mutation', 'files':{}}
    for name, files in payload.items():
        folder = dest / name
        folder.mkdir(exist_ok=True)
        for rel, content in files.items():
            path = folder / rel.replace('/', '__')
            path.write_text(content,encoding='utf-8')
            manifest['files'][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    cmd = "date '+%Y-%m-%d %H:%M:%S %Z'; squeue -u a8s001819 -o '%i|%j|%T|%M|%l|%N'; sacct -j 4479238,4533060,4614693 --format=JobID,State,ExitCode,Elapsed,Start,End,AllocCPUS,ReqMem,MaxRSS -P; sstat -j 4614693.batch --format=JobID,MaxRSS,AveRSS,MaxVMSize -P"
    scheduler = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8',cmd],capture_output=True,text=True,encoding='utf-8',timeout=45)
    scheduler.check_returncode()
    (dest/'scheduler.txt').write_text(scheduler.stdout,encoding='utf-8')
    manifest['scheduler_command']=cmd
    (ROOT/'source.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:list(v) for k,v in payload.items()},indent=2))

if __name__ == '__main__':
    main()
