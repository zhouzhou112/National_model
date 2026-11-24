"""One finite full backup of terminal OPS-Open 2030/2040/2060 outputs on T550."""
from pathlib import Path
import argparse,importlib.util,json,socket
RELEASES={'20261115_opsopen_2030_v9_t44_m750_tol1e4_v1',
          '20261115_opsopen_2040_v9a12_t44_m750_tol1e4_v1',
          '20261115_opsopen_2060_v9a12_t44_m750_tol1e4_v1'}
EXTRA=['FINAL_GATES_PASSED.json','compute_node_smoke.json','startup_resources.json',
       'data_copy_verification.json','license_path_preflight.json','runtime_slurm_job.txt',
       'runtime_hash_check.log','submission.json','release_receipt.json','source_code_sha256.json',
       'resource_contract_reference.csv','engineering_gate_window_carbon_budget.json','frozen_closure.json']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','run']);p.add_argument('--config',required=True);p.add_argument('--engine',required=True);a=p.parse_args()
 assert socket.gethostname().split('.')[0]=='t550'
 spec=importlib.util.spec_from_file_location('backup_engine',a.engine);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 token="'source_screen.csv','release_files.sha256','resource_usage.txt'";assert m.INVENTORY.count(token)==1
 m.INVENTORY=m.INVENTORY.replace(token,token+','+','.join(repr(n) for n in EXTRA))
 cfg=json.loads(Path(a.config).read_text(encoding='utf-8'));assert set(cfg['releases'])==RELEASES and len(cfg['releases'])==3;m.configure(cfg);assert m.MIN_FREE_FRACTION==.05
 {'plan':m.plan,'run':m.run}[a.phase]()
