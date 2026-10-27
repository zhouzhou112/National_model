"""Source-bound closure changes only authorized capacities and preserves audit."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import gurobipy as gp
import pandas as pd

from cispo_model.frozen_closure import build_payload, apply_static_closure


class FrozenClosureTests(unittest.TestCase):
    def setup_case(self):
        m=gp.Model();m.Params.OutputFlag=0
        spur=m.addVar(lb=1,ub=1,obj=10,name='spur_augmentation_gw[0]')
        trunk=m.addVar(lb=2,ub=2,obj=20,name='trunk_augmentation_gw[0]')
        bio=m.addVar(lb=1,ub=1,obj=30,name='thermal_new_gw[0,8]')
        cap=m.addVar(lb=0,obj=5,name='thermal_capacity_gw[0,8]')
        ccs=m.addVar(lb=1,ub=1,name='thermal_capacity_gw[0,9]')
        storage=m.addVar(lb=4,ub=4,name='storage_new_gw[0]')
        m.addConstr(cap-bio==2,name='thermal_non_ccs_capacity_accounting_bio[0]')
        m.addConstr(spur>=1.0002,name='spur_capacity_non_dpv[0]')
        m.addConstr(trunk>=2.003,name='trunk_capacity_0')
        m.addConstr(cap+ccs<=3.999,name='biomass_beccs_shared_capacity_upper_s4_34[0]')
        m.update()
        names=[spur.VarName,trunk.VarName,bio.VarName]
        frame=pd.DataFrame([dict(variable=n,family=f,stable_key=json.dumps(k),base_value=v,
            frozen_value=v,original_lb=0,original_ub=10) for n,f,k,v in zip(names,
            ['spur_augmentation','trunk_augmentation','thermal_new'],[['a','upv'],['sub'],['11','bio']],[1,2,1])])
        conflicts=[dict(row=n) for n in ['spur_capacity_non_dpv[0]','trunk_capacity_0','biomass_beccs_shared_capacity_upper_s4_34[0]']]
        p=build_payload(m,frame,conflicts,'source-sha',2040)
        return m,frame,p

    def test_minimum_changes_cost_and_unchanged_source(self):
        m,frame,p=self.setup_case()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);frame.to_csv(root/'frozen_capacity_audit.csv',index=False)
            original=(root/'frozen_capacity_audit.csv').read_bytes()
            path=root/'input.json';path.write_text(json.dumps(p))
            result=apply_static_closure(SimpleNamespace(model=m,index={}),root,path,'source-sha',2040)
            self.assertEqual(result['status'],'PASS')
            self.assertEqual((root/'frozen_capacity_audit.csv').read_bytes(),original)
            self.assertAlmostEqual(m.getVarByName('spur_augmentation_gw[0]').LB,1.0002)
            self.assertAlmostEqual(m.getVarByName('trunk_augmentation_gw[0]').LB,2.003)
            self.assertAlmostEqual(m.getVarByName('thermal_new_gw[0,8]').LB,.999)
            self.assertEqual(m.getVarByName('thermal_capacity_gw[0,9]').LB,1)
            self.assertEqual(m.getVarByName('storage_new_gw[0]').LB,4)
            self.assertAlmostEqual(result['annual_cost_delta_million_cny'],.002+.06-.035)
            self.assertTrue(all(abs(x['post_closure_gap_gw'])<1e-12 for x in result['rows']))
        m.dispose()

    def test_wrong_source_row_target_or_amount_fails_before_mutation(self):
        for kind in ['source','year','row','target','amount']:
            m,frame,p=self.setup_case()
            if kind=='source':p['source_result_manifest_sha256']='other'
            elif kind=='year':p['planning_year']=2050
            elif kind=='row':p['rows'][0]['row']='power_balance_0'
            elif kind=='target':p['rows'][0]['variable']='storage_new_gw[0]'
            else:p['rows'][0]['after_gw']+=.001
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);frame.to_csv(root/'frozen_capacity_audit.csv',index=False)
                path=root/'input.json';path.write_text(json.dumps(p))
                with self.assertRaises(ValueError):
                    apply_static_closure(SimpleNamespace(model=m,index={}),root,path,'source-sha',2040)
                self.assertEqual(m.getVarByName('spur_augmentation_gw[0]').LB,1)
            m.dispose()

    def test_ccs_target_and_duplicate_row_rejected(self):
        m,frame,p=self.setup_case()
        with self.assertRaises(ValueError):build_payload(m,frame,[p['rows'][0]]*2,'source-sha',2040)
        frame.loc[frame.family=='thermal_new','stable_key']=json.dumps(['11','bioccs'])
        with self.assertRaises(ValueError):build_payload(m,frame,[p['rows'][-1]],'source-sha',2040)
        m.dispose()


if __name__=='__main__':unittest.main()
