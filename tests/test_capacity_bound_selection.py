"""Selected-column/state entry: scope, inheritance and disabled-path invariance."""
from pathlib import Path
from types import SimpleNamespace
import copy,json,tempfile,unittest
import numpy as np
import pandas as pd
from cispo_model.frozen_capacity import (read_capacity_selection,
    capture_selected_original_bounds,apply_capacity_selection,SELECTION_SCHEMA)

class BoundSelectionTest(unittest.TestCase):
    def fixture(self):
        class Model:
            def update(self):pass
        def var(name,lo,up):return SimpleNamespace(LB=np.array(lo,dtype=float),UB=np.array(up,dtype=float),VarName=np.array([f'{name}[{i}]' for i in range(len(lo))]))
        art=SimpleNamespace(model=Model(),variables={
            'vre_capacity':var('vre_capacity_gw',[1,2,0],[3,4,2]),
            'vre_new':var('vre_new_gw',[0,0,0],[2,2,2]),
            'spur_augmentation':var('spur_augmentation_gw',[0,0,0],[np.inf,np.inf,0]),
            'dispatch':var('dispatch',[0],[100]),
        },index={'vre_capacity_floor_gw':np.array([1.,2.,0.]),'vre_spur_floor_gw':np.array([.8,.4,0.]),'vre_max_cf':np.array([.5,.5,.5])})
        data=SimpleNamespace(vre_sites=pd.DataFrame({'grid_uid':['a','b','c'],'technology':['onwind','upv','dpv']}))
        records=[dict(grid_uid='a',technology='onwind',state='lower'),dict(grid_uid='b',technology='upv',state='upper'),dict(grid_uid='c',technology='dpv',state='free')]
        selected=dict(payload=dict(mode='vre_boundary_states',columns=records),evidence=dict(mode='vre_boundary_states',sha256='fixture'))
        return art,data,selected

    def test_disabled_path_does_not_access_model_or_config(self):
        cfg=SimpleNamespace(raw={'untouched':[1,2]});before=copy.deepcopy(cfg.raw)
        self.assertIsNone(read_capacity_selection(None,cfg,base_frozen=False))
        self.assertIsNone(apply_capacity_selection(None,None,None,None))
        capture_selected_original_bounds(None,None,None)
        self.assertEqual(before,cfg.raw)

    def test_stable_states_use_current_stock_and_minimal_spur(self):
        a,d,s=self.fixture();s['payload']['columns'].reverse()
        with tempfile.TemporaryDirectory() as tmp:
            r=apply_capacity_selection(a,d,s,tmp)
            np.testing.assert_array_equal(a.variables['vre_capacity'].LB,[1,4,0])
            np.testing.assert_array_equal(a.variables['vre_capacity'].UB,[1,4,2])
            np.testing.assert_array_equal(a.variables['vre_new'].LB,[0,2,0])
            np.testing.assert_array_equal(a.variables['vre_new'].UB,[0,2,2])
            np.testing.assert_allclose(a.variables['spur_augmentation'].LB,[0,1.6,0])
            np.testing.assert_array_equal(a.variables['dispatch'].UB,[100])
            self.assertEqual(r['changed_bound_columns'],6)
            text=(Path(tmp)/'capacity_bound_selection_audit.json').read_text()
            self.assertNotIn('Infinity',text)

    def test_bad_keys_or_out_of_bounds_stop_before_mutation(self):
        for bad in ['duplicate','out_of_bounds']:
            a,d,s=self.fixture();before={k:(v.LB.copy(),v.UB.copy()) for k,v in a.variables.items()}
            if bad=='duplicate':s['payload']['columns'][1]=dict(s['payload']['columns'][0])
            else:a.variables['vre_new'].UB[1]=1;before['vre_new']=(a.variables['vre_new'].LB.copy(),a.variables['vre_new'].UB.copy())
            with tempfile.TemporaryDirectory() as tmp,self.assertRaises(ValueError):apply_capacity_selection(a,d,s,tmp)
            for k,v in a.variables.items():
                np.testing.assert_array_equal(v.LB,before[k][0]);np.testing.assert_array_equal(v.UB,before[k][1])

    def test_already_fixed_columns_are_not_counted_as_bound_changes(self):
        a,d,s=self.fixture()
        for r in s['payload']['columns']:r['state']='free'
        s['payload']['columns'][2]['state']='lower'
        a.variables['vre_capacity'].UB[2]=0
        a.variables['vre_new'].UB[2]=0
        with tempfile.TemporaryDirectory() as tmp:
            result=apply_capacity_selection(a,d,s,tmp)
            self.assertEqual(result['selected_bound_columns'],3)
            self.assertEqual(result['changed_bound_columns'],0)

    def test_names_are_read_once_per_family_not_once_per_site(self):
        a,d,s=self.fixture();reads={}
        class CountedVariable:
            def __init__(self,key,source):
                self.key=key;self.LB=source.LB;self.UB=source.UB;self.names=source.VarName
            @property
            def VarName(self):
                reads[self.key]=reads.get(self.key,0)+1
                return self.names
        for key in ['vre_capacity','vre_new','spur_augmentation']:
            a.variables[key]=CountedVariable(key,a.variables[key])
        with tempfile.TemporaryDirectory() as tmp:apply_capacity_selection(a,d,s,tmp)
        self.assertEqual(reads,{'vre_capacity':1,'vre_new':1,'spur_augmentation':1})

    def test_D1_restores_only_exact_intra_bounds_and_expectations(self):
        mv=SimpleNamespace(LB=np.array([0.,0.]),UB=np.array([2.,3.]),VarName=np.array(['intra_new[0]','intra_new[1]']))
        art=SimpleNamespace(model=SimpleNamespace(update=lambda:None),variables={'intra_load_center_new':mv},index={})
        data=SimpleNamespace(intra_load_center_edges=pd.DataFrame({'intra_edge_id':['x','y']}))
        s=dict(payload=dict(mode='release_base_intra',columns=[dict(family='intra_load_center_new',stable_key=[x]) for x in ['y','x']]),evidence=dict(mode='release_base_intra',sha256='fixture'))
        capture_selected_original_bounds(art,data,s);mv.LB=mv.UB=np.array([1.,1.])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'frozen_capacity_expected.json';p.write_text(json.dumps(dict(intra_load_center_new=[1,1],intra_load_center_capacity=[1,1],vre_new=[4])))
            apply_capacity_selection(art,data,s,tmp)
            np.testing.assert_array_equal(mv.LB,[0,0]);np.testing.assert_array_equal(mv.UB,[2,3])
            self.assertEqual(json.loads(p.read_text()),{'vre_new':[4]})

    def test_D1_rejects_unreviewed_family_or_missing_link(self):
        for rows in [[dict(family='storage_new',stable_key=['x'])],[dict(family='intra_load_center_new',stable_key=['x'])]]:
            d=SimpleNamespace(intra_load_center_edges=pd.DataFrame({'intra_edge_id':['x','y']}))
            with self.assertRaises(ValueError):capture_selected_original_bounds(None,d,dict(payload=dict(mode='release_base_intra',columns=rows)))

    def test_selection_identity_and_year_are_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'selection.json';p.write_text(json.dumps(dict(schema_version=SELECTION_SCHEMA,planning_year=2050,mode='vre_boundary_states',columns=[dict(grid_uid='a',technology='onwind',state='lower')])))
            c=SimpleNamespace(raw={},planning_year=2050)
            r=read_capacity_selection(p,c,base_frozen=False)
            self.assertEqual(c.raw['capacity_bound_selection']['sha256'],r['evidence']['sha256'])
            with self.assertRaises(ValueError):read_capacity_selection(p,c,base_frozen=True)
            c.planning_year=2060
            with self.assertRaises(ValueError):read_capacity_selection(p,c,base_frozen=False)

if __name__=='__main__':unittest.main()
