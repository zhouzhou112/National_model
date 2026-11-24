"""Read-only chunked integrity check of saved vectors; does not load an LP."""
from pathlib import Path
import json
import subprocess

HERE=Path(__file__).resolve().parent
REMOTE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3'
PYTHON='/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310/bin/python'

def main():
    script='root='+repr(REMOTE)+'\n'
    script+='''import os,json,hashlib,numpy as np
folder=os.path.join(root,'output_8760/barrier_checkpoint')
manifest=json.load(open(os.path.join(folder,'barrier_checkpoint_manifest.json')))
results={}
for kind,entry in manifest['vectors'].items():
    p=os.path.join(folder,entry['path'])
    h=hashlib.sha256()
    with open(p,'rb') as f:
        while True:
            block=f.read(8*1024*1024)
            if not block:break
            h.update(block)
    values=np.load(p,mmap_mode='r',allow_pickle=False)
    finite=all(np.isfinite(values[start:start+1000000]).all() for start in range(0,len(values),1000000))
    results[kind]=dict(entries=int(values.size),shape=list(values.shape),dtype=str(values.dtype),bytes=os.stat(p).st_size,sha256=h.hexdigest(),hash_match=h.hexdigest()==entry['sha256'],all_finite=bool(finite),shape_match=values.shape==(entry['entries'],))
    del values
results['source_sha256']={}
for rel in ['repo/scripts/run_cispo_2030_full_year.py','repo/cispo_model/solution_export.py']:
    results['source_sha256'][rel]=hashlib.sha256(open(os.path.join(root,rel),'rb').read()).hexdigest()
qcpath=os.path.join(root,'output_8760/load_center_network_qc.csv')
results['load_center_network_qc_csv']=open(qcpath).read()
print(json.dumps(results))
'''
    proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8',PYTHON+' -'],input=script,text=True,encoding='utf-8',capture_output=True,timeout=120)
    proc.check_returncode()
    result=json.loads(proc.stdout)
    (HERE/'checkpoint_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for kind in ['primal','dual']:
        assert result[kind]['hash_match'] and result[kind]['all_finite'] and result[kind]['shape_match'],kind
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
