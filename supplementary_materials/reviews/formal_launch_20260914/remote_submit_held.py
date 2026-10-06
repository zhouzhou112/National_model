from pathlib import Path
import subprocess,json,datetime
root=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v2')
assert json.loads((root/'input_comparison.json').read_text())['status']=='PASS'
assert json.loads((root/'preflight/preflight_report.json').read_text())['status']=='PASS'
assert not (root/'held_submission.json').exists()
args=['sbatch','--hold','--parsable','--export=ALL,SOURCE_RELEASE=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_2820fc3_v3','formal_base.sbatch']
p=subprocess.run(args,cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
record=dict(submitted_at_utc=datetime.datetime.utcnow().isoformat()+'Z',args=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
(root/'held_submission.json').write_text(json.dumps(record,indent=2))
if p.returncode: print(json.dumps(record,indent=2));raise SystemExit(p.returncode)
job=p.stdout.strip().split(';')[0]
assert job.isdigit()
record['job_id']=job
q=subprocess.run(['scontrol','show','job','-o',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
record['scontrol']=q.stdout
(root/'held_submission.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
