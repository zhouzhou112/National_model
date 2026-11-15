"""Install a fresh T550 gate runtime from reviewed sources and original input bytes."""
from pathlib import Path
import base64,json,subprocess,sys
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
archive=subprocess.check_output(['git','archive',commit,'cispo_model','scripts','config','tests'],cwd=REPO)
helpers=['resource_gate_batch2.py','resource_audit_batch2.py','window_gate.py','run_batch2_year_gates.py','contractable_total_national_source.csv']
files={str((HERE/n).relative_to(REPO)).replace('\\','/'):base64.b64encode((HERE/n).read_bytes()).decode() for n in helpers}
files['batch2/t550_sources.json']=base64.b64encode((HERE/'batch2/t550_sources.json').read_bytes()).decode()
files['batch2/cloud_source_file_sha256.json']=base64.b64encode((HERE/'batch2/cloud_source_file_sha256.json').read_bytes()).decode()
resume=sys.argv[1:]==['--resume-after-metadata-copy'];assert not sys.argv[1:] or resume
code='archive='+repr(base64.b64encode(archive).decode())+'\nfiles='+repr(files)+'\nsource_commit='+repr(commit)+'\nresume='+repr(resume)+'\n'+r'''
from pathlib import Path
import base64,hashlib,json,shutil,tarfile,io,subprocess,sys,csv,gzip,itertools,os
base=Path('/home/zz2/National_model_server');parent=base/'ops_flex_resource_sensitivity_20261114';runtime=parent/'runtime_batch2_20261115';repo=runtime/'repo'
if resume:assert runtime.exists() and not (runtime/'installation_receipt.json').exists() and not (runtime/'data_roots/2030/neutral').exists()
else:
 assert not runtime.exists();runtime.mkdir();shutil.copytree(parent/'validation_runtime_v7/repo',repo,symlinks=True)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(archive))) as tf:
 for member in tf.getmembers():assert (repo/member.name).resolve()==repo.resolve() or repo.resolve() in (repo/member.name).resolve().parents
 if resume:
  for member in tf.getmembers():
   if member.isfile():assert (repo/member.name).read_bytes()==tf.extractfile(member).read(),member.name
 else:tf.extractall(repo)
for name,raw in files.items():
 p=(runtime/name if name.startswith('batch2/') else repo/name);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==base64.b64decode(raw),name
 else:p.write_bytes(base64.b64decode(raw))
sources=json.loads((runtime/'batch2/t550_sources.json').read_text());cloud=json.loads((runtime/'batch2/cloud_source_file_sha256.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
shared=parent/'baseline_runtime';original2030=runtime/'data_roots/2030/original'
if not resume:original2030.parent.mkdir(parents=True);shutil.copytree(shared/'data_roots/neutral',original2030)
missing=[name for name,e in cloud['2030']['data_overlay'].items() if not (original2030/name).exists() or sha(original2030/name)!=e['sha256']]
listing=runtime/'original2030_metadata.files';listing.write_text(''.join(n+'\n' for n in missing))
if missing:
 subprocess.run(['rsync','-rt','--copy-links','--no-owner','--no-group','--protect-args','--files-from='+str(listing),'-e','ssh -F /home/zz2/.ssh/paracloud_backup_20261012/ssh_config','paracloud-backup:/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3/data_overlay/',str(original2030)+'/'],check=True)
def validate_base(root,year):
 for n,e in cloud[str(year)]['data_overlay'].items():
  p=root/n;assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],n
validate_base(original2030,2030)
roots2030={'original':str(original2030)}
for resource in ['neutral','conservative','open']:
 dest=original2030.parent/resource;shutil.copytree(original2030,dest);roots2030[resource]=str(dest)
 if resource!='neutral':
  bundle=shared/'inputs'/resource;a=json.loads((bundle/'BUILD_AUDIT.json').read_text())
  for n,e in a['files'].items():
   assert (bundle/n).stat().st_size==e['bytes'] and sha(bundle/n)==e['sha256'],n
   if n.startswith(('load/','flexibility/')):
    target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);assert not target.is_symlink();shutil.copy2(bundle/n,target);assert sha(target)==e['sha256']
 with gzip.open(original2030/'load/hourly_load_2025_2060.csv.gz','rt') as f,gzip.open(dest/'load/hourly_load_2025_2060.csv.gz','rt') as g:
  for x,y in itertools.zip_longest(csv.DictReader(f),csv.DictReader(g)):assert x and y and x['demand_gw']==y['demand_gw']
sys.path.insert(0,str(repo));import numpy as np;import pandas as pd
from cispo_model.carbon_accounting import resolve_beccs_carbon_factors
windowfile=repo/'supplementary_materials/reviews/base_frozen_batch2_20261027/window_carbon.py'
if not windowfile.exists():shutil.copy2(base/'base_frozen_batch2_20261027/repo/supplementary_materials/reviews/base_frozen_batch2_20261027/window_carbon.py',windowfile)
ns={};exec(windowfile.read_text(),ns)
report=dict(status='PASS',source_commit=source_commit,years={},source_data_not_regenerated=True,metadata_2030_copied_from_original_B_cloud=missing)
for year,meta in sources.items():
 y=int(year);info=dict(source=meta['source'],supplement=meta['source']+('/frozen_capacity_B_20261026' if y==2030 else '/frozen_capacity_B_20261027'),closure=meta.get('closure',{}).get('path'))
 if y==2030:info['data_roots']=roots2030
 else:
  validate_base(shared/'data_roots/neutral',y)
  info['data_roots']={r:str(shared/'data_roots'/r) for r in ['neutral','conservative','open']};info['data_roots']['original']=str(base/'base_frozen_batch2_20261027/repo/data');validate_base(Path(info['data_roots']['original']),y)
 for resource in ['conservative','open']:
  bundle=shared/'inputs'/resource;a=json.loads((bundle/'BUILD_AUDIT.json').read_text());d=Path(info['data_roots'][resource])
  for n,e in a['files'].items():
   assert sha(bundle/n)==e['sha256'],n
   if n.startswith(('load/','flexibility/')):assert sha(d/n)==e['sha256'],n
 if y>2030:
  info['budget']=meta['budget']['path'];assert sha(info['budget'])==meta['budget']['sha256'];assert sha(info['closure'])==meta['closure']['sha256']
 else:
  root=base/'cloud_backup/20260914_base_v9_t48_m750_tol1e4_v3/output_8760';mf=json.loads((root/'result_manifest.json').read_text());entries={e['path']:e for e in mf['files']};assert sha(root/'result_manifest.json')==meta['manifest_sha256']
  for n in ['thermal_dispatch.npz','dac_capacity_capture.csv','annual_carbon_ccs.json','input_manifest.csv']:assert sha(root/n)==entries[n]['sha256'],n
  emissions=Path(info['data_roots']['original'])/'technology/emission_factors_by_year.csv';im=pd.read_csv(root/'input_manifest.csv');assert sha(emissions)==im.loc[im.logical_path=='technology/emission_factors_by_year.csv','sha256'].iloc[0]
  factors=pd.read_csv(emissions);factors=factors[factors.year==y].set_index('technology');dac=pd.read_csv(root/'dac_capacity_capture.csv').capture_mtco2.sum()
  with np.load(root/'thermal_dispatch.npz',allow_pickle=False) as t:budget=ns['account_window'](t['gross_generation_gw'],t['technologies'].tolist(),t['hour_index'],list(range(24)),factors,float(dac))
  carbon=json.loads((root/'annual_carbon_ccs.json').read_text());delta=budget['annual_reconstructed_net_emissions_mt']-carbon['annual_net_emissions_mtco2'];assert abs(delta)<=1e-5
  budget.update(status='PASS',year=y,source_result_manifest_sha256=meta['manifest_sha256'],original_annual_carbon_limit_mt=carbon['annual_carbon_limit_mtco2_per_year'],annual_reconstruction_difference_mt=delta)
  target=runtime/'batch2/window_carbon_budget_2030.json';target.write_text(json.dumps(budget,indent=2)+'\n');info['budget']=str(target)
 info.update(source_result_manifest_sha256=meta['manifest_sha256'],production_input_files=len(cloud[year]['data_overlay']),budget_sha256=sha(info['budget']),closure_sha256=sha(info['closure']) if info['closure'] else None)
 report['years'][year]=info
subprocess.run(['git','add','cispo_model','scripts','config','tests'],cwd=repo,check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','-c','user.name=Validation Snapshot','-c','user.email=validation@local.invalid','commit','-m','Current reviewed source for second batch validation'],cwd=repo,check=True,stdout=subprocess.DEVNULL)
report['tested_source_lf_sha256']={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for d in ['cispo_model','scripts','config','tests'] for p in (repo/d).rglob('*') if p.is_file() and p.suffix in ['.py','.json'] and '__pycache__' not in p.parts}
(runtime/'installation_receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
'''
# Keep the generated remote program valid and reviewable before transmission.
compile(code,'<fresh-batch2-runtime>','exec')
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -'],input=code,text=True,encoding='utf-8',capture_output=True)
(HERE/'batch2/runtime_install.stdout.log').write_text(p.stdout,encoding='utf-8');(HERE/'batch2/runtime_install.stderr.log').write_text(p.stderr,encoding='utf-8')
if p.returncode:raise RuntimeError(p.stderr[-5000:]+p.stdout[-1000:])
result=json.loads(p.stdout);(HERE/'batch2/installation_receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],years=list(result['years']),copied_metadata=result['metadata_2030_copied_from_original_B_cloud'])))
