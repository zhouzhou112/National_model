"""Small solved LP proves state bounds and directional spur certificate."""
from pathlib import Path
from types import SimpleNamespace
import tempfile,unittest
import numpy as np
import pandas as pd
try:
    import gurobipy as gp
except ImportError:
    gp=None
from cispo_model.frozen_capacity import apply_capacity_selection
from cispo_model.vre_pricing import parse_vre_mps,directional_site_prices,directional_certificate
from cispo_model.factor_screen import mps_section_sha256

@unittest.skipIf(gp is None,'Gurobi environment required')
class SelectedLPSmallCase(unittest.TestCase):
    def test_disabled_MPS_identity_and_upper_release_bound(self):
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.start()
            with gp.Model('small_pair',env=env) as model,tempfile.TemporaryDirectory() as tmp:
                model.Params.Method=0
                cap=model.addMVar(1,lb=1,ub=3,name='vre_capacity_gw')
                new=model.addMVar(1,lb=0,ub=2,name='vre_new_gw')
                spur=model.addMVar(1,lb=0,name='spur_augmentation_gw')
                model.addConstr(cap-new==1,name='vre_capacity_accounting')
                model.addConstr(spur-.5*cap>=-.4,name='spur_capacity_non_dpv')
                model.setObjective(2*cap.sum()+3*new.sum()+4*spur.sum())
                model.update();p=Path(tmp)
                art=SimpleNamespace(model=model,variables=dict(vre_capacity=cap,vre_new=new,spur_augmentation=spur),index=dict(vre_capacity_floor_gw=np.array([1.]),vre_spur_floor_gw=np.array([.4]),vre_max_cf=np.array([.5])))
                data=SimpleNamespace(vre_sites=pd.DataFrame(dict(grid_uid=['G1'],technology=['onwind'])))
                model.write(str(p/'before.mps'))
                apply_capacity_selection(art,data,None,p)
                model.write(str(p/'disabled.mps'))
                self.assertEqual((p/'before.mps').read_bytes(),(p/'disabled.mps').read_bytes())
                model.optimize();self.assertEqual(model.Status,gp.GRB.OPTIMAL);free_objective=model.ObjVal
                selection=[dict(grid_uid='G1',technology='onwind',state='upper')]
                apply_capacity_selection(art,data,dict(payload=dict(mode='vre_boundary_states',columns=selection),evidence=dict(mode='vre_boundary_states',sha256='fixture')),p)
                model.write(str(p/'fixed.mps'))
                old=mps_section_sha256(p/'before.mps');fixed=mps_section_sha256(p/'fixed.mps')
                self.assertEqual({k:v for k,v in old.items() if not k.startswith('BOUNDS')},{k:v for k,v in fixed.items() if not k.startswith('BOUNDS')})
                model.optimize();self.assertEqual(model.Status,gp.GRB.OPTIMAL)
                fixed_objective=model.ObjVal;np.save(p/'pi.npy',model.Pi)
                columns,_=parse_vre_mps(p/'fixed.mps',p/'pi.npy',include_spur=True)
                prices=directional_site_prices(columns,[dict(grid_uid='G1',technology='onwind',capacity_floor_gw=1,capacity_upper_gw=3)],selection,require_fixed=True)
                cert=directional_certificate(prices,fixed_objective)
                self.assertAlmostEqual(fixed_objective-free_objective,14.,places=8)
                self.assertGreaterEqual(cert['B_million_cny']+1e-9,fixed_objective-free_objective)
                self.assertAlmostEqual(cert['B_million_cny'],14.,places=8)

if __name__=='__main__':unittest.main()
