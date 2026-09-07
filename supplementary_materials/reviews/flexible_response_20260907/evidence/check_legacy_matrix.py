import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
sys.path.insert(0,str(Path.cwd()/'tests'))
import numpy as np
import gurobipy as gp
from cispo_model.config import load_model_config
from cispo_model.flexible_load import attach_flexible_load
from test_flexible_portfolio import fixture,CASES
rows=[]
with patch.object(gp.Model,'optimize',side_effect=AssertionError('forbidden')),patch.object(gp.Model,'presolve',side_effect=AssertionError('forbidden')):
 for case in (*CASES,'base'):
  c=load_model_config(scenario_path=f'config/scenarios/{case}.json') if case!='base' else load_model_config()
  with gp.Model('unchanged') as m:
   m.Params.OutputFlag=0
   b=attach_flexible_load(m,c,fixture(),hours=24)
   m.setObjective(gp.quicksum(b.costs.values()));m.update()
   a=m.getA().tocsr();h=hashlib.sha256()
   for v in [a.data,a.indices,a.indptr,np.asarray(m.getAttr('RHS')),np.asarray(m.getAttr('LB')),np.asarray(m.getAttr('UB')),np.asarray(m.getAttr('Obj'))]:h.update(v.tobytes())
   h.update(json.dumps(m.getAttr('Sense')).encode())
   rows.append(dict(case=case,variables=m.NumVars,rows=m.NumConstrs,nnz=m.NumNZs,matrix_sha256=h.hexdigest(),fingerprint=int(m.Fingerprint)&0xffffffff))
Path(sys.argv[1]).write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
