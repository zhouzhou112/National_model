"""Compute two Base window budgets on verified T550 backups; return small JSON."""
from pathlib import Path
import base64,hashlib,json,subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCES={2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',2050:'20260930_base2050_v9_t48_m750_tol1e4_v1'}


def main():
    sources={y:dict(release=n,manifest_sha256=hashlib.sha256((HERE.parent/'base_frozen_followups_20261027/source_base'/n/'output_8760/result_manifest.json').read_bytes()).hexdigest()) for y,n in SOURCES.items()}
    files={name:base64.b64encode((ROOT/path).read_bytes()).decode() for name,path in {
        'carbon':'cispo_model/carbon_accounting.py','window':str((HERE/'window_carbon.py').relative_to(ROOT)),
        'emissions':'data/technology/emission_factors_by_year.csv'}.items()}
    code='sources='+repr(sources)+'\nfiles='+repr(files)+'\n'+r'''
from pathlib import Path
import base64,hashlib,json,types,sys,io
import numpy as np
import pandas as pd
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
package=types.ModuleType('cispo_model');package.__path__=[];sys.modules['cispo_model']=package
carbon=types.ModuleType('cispo_model.carbon_accounting');sys.modules[carbon.__name__]=carbon
exec(base64.b64decode(files['carbon']),carbon.__dict__)
scope={};exec(base64.b64decode(files['window']),scope)
emission_bytes=base64.b64decode(files['emissions']);table=pd.read_csv(io.BytesIO(emission_bytes))
result={}
for year,source in sources.items():
 root=Path('/home/zz2/National_model_server/cloud_backup')/source['release']/'output_8760'
 assert sha(root/'result_manifest.json')==source['manifest_sha256']
 entries={r['path']:r for r in json.loads((root/'result_manifest.json').read_text())['files']}
 names=['thermal_dispatch.npz','dac_capacity_capture.csv','annual_carbon_ccs.json','input_manifest.csv']
 hashes={}
 for name in names:
  p=root/name;h=sha(p);assert h==entries[name]['sha256'] and p.stat().st_size==entries[name]['bytes'];hashes[name]=h
 inputs=pd.read_csv(root/'input_manifest.csv')
 rec=inputs[inputs.logical_path=='technology/emission_factors_by_year.csv'];assert len(rec)==1
 assert hashlib.sha256(emission_bytes).hexdigest()==rec.iloc[0].sha256
 factors=table[table.year==year].set_index('technology')
 dac=pd.read_csv(root/'dac_capacity_capture.csv').capture_mtco2.sum()
 with np.load(root/'thermal_dispatch.npz',allow_pickle=False) as d:
  report=scope['account_window'](d['gross_generation_gw'],d['technologies'].tolist(),d['hour_index'],list(range(24)),factors,float(dac))
  assert len(set(d['province_codes'].tolist()))==31
 archived=json.loads((root/'annual_carbon_ccs.json').read_text())
 difference=report['annual_reconstructed_net_emissions_mt']-archived['annual_net_emissions_mtco2']
 assert abs(difference)<=1e-5,('Annual crosscheck',year,difference)
 report.update(status='PASS',year=year,source_release=source['release'],source_result_manifest_sha256=source['manifest_sha256'],
    source_files_sha256=hashes,emission_table_sha256=hashlib.sha256(emission_bytes).hexdigest(),
    model_carbon_code_sha256=hashlib.sha256(base64.b64decode(files['carbon'])).hexdigest(),
    accounting_code_sha256=hashlib.sha256(base64.b64decode(files['window'])).hexdigest(),
    annual_archive_net_emissions_mt=archived['annual_net_emissions_mtco2'],annual_reconstruction_difference_mt=difference,
    original_annual_carbon_limit_mt=archived['annual_carbon_limit_mtco2_per_year'],source_unchanged=sha(root/'result_manifest.json')==source['manifest_sha256'])
 result[year]=report
print(json.dumps(result))
'''
    command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -']
    p=subprocess.run(command,input=code,text=True,capture_output=True,timeout=600)
    (HERE/'window_collection.stderr.log').write_text(p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(p.stderr[-5000:])
    data=json.loads(p.stdout)
    for year,report in data.items():
        path=HERE/year/'window_carbon_budget.json';path.parent.mkdir(exist_ok=True)
        assert not path.exists();path.write_text(json.dumps(report,indent=2)+'\n')
        print(year,report['base_window_net_emissions_mt'],report['window_carbon_limit_mt'])


if __name__=='__main__':main()
