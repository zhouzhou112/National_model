"""Author-scoped Case3 2060 thread trial and exact C2060 screening gates."""
import copy,csv,hashlib,importlib.util,json,pathlib,tempfile,unittest
from types import SimpleNamespace
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Case32060ProfileTests(unittest.TestCase):
 def setUp(self):
  from cispo_model.config import load_model_config
  from cispo_model.factor_screen import CASE3_2060_44_PROFILE_ID
  self.cfg=load_model_config(ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json',scenario_path=ROOT/'config/scenarios/case3_thermal_ev_v5.json',solver_path=ROOT/f'config/solver_profiles/{CASE3_2060_44_PROFILE_ID}.json').for_planning_year(2060)
  self.args=SimpleNamespace(state_in='accepted_Case3_2050_R1',late_entry_base_state=False,archive_original_model=True,vre_screen_csv=ROOT/'supplementary_materials/reviews/base_2060_screen_20261026/ready/source_screen.csv')
 def test_registered_profile_and_exact_settings(self):
  from cispo_model.factor_screen import validate_production_screen_contract,CASE3_2060_44_PROFILE_ID
  from scripts.run_cispo_2030_full_year import DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS
  self.assertIn(CASE3_2060_44_PROFILE_ID,DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS)
  validate_production_screen_contract(self.cfg,self.args)
  c=json.loads((ROOT/'config/solver_profiles/barrier_stagea_screened_agg0_lateentry_2060_v1_threads40.json').read_text());a=json.loads(self.cfg.solver_path.read_text())
  self.assertEqual(a['candidate_screen'],c['candidate_screen']);self.assertEqual(a['numerics'],dict(c['numerics'],threads=44))
  self.assertEqual({k for k in a if a[k]!=c[k]},{'profile_id','description','numerics'})
 def test_wrong_year_state_or_scenario_rejected(self):
  from cispo_model.factor_screen import validate_production_screen_contract
  with self.assertRaisesRegex(ValueError,'same-scenario'):validate_production_screen_contract(self.cfg.for_planning_year(2050),self.args)
  for key,val in [('state_in',None),('late_entry_base_state',True)]:
   args=SimpleNamespace(**vars(self.args));setattr(args,key,val)
   with self.assertRaisesRegex(ValueError,'same-scenario'):validate_production_screen_contract(self.cfg,args)
 def test_margin_source_and_threads_cannot_drift(self):
  from cispo_model.factor_screen import validate_production_screen_contract
  for key,val in [('margin',.3),('source_release','wrong_year')]:
   cfg=copy.deepcopy(self.cfg);cfg.raw['candidate_screen'][key]=val
   with self.assertRaises(ValueError):validate_production_screen_contract(cfg,self.args)
  cfg=copy.deepcopy(self.cfg);cfg.raw['numerics']['threads']=48
  with self.assertRaises(ValueError):validate_production_screen_contract(cfg,self.args)
 def test_exclusion_gate_detects_site_addback(self):
  path=ROOT/'supplementary_materials/reviews/case3_2060_launch_20261106/screen_identity.py';spec=importlib.util.spec_from_file_location('screen_id',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/'a.csv';b=pathlib.Path(d)/'b.csv'
   content='grid_uid,technology,screened_out\na,onwind,true\nb,pv,false\n';a.write_text(content);b.write_text(content)
   self.assertEqual(m.compare(a,b)['status'],'PASS');b.write_text(content.replace('onwind,true','onwind,false'))
   r=m.compare(a,b);self.assertEqual(r['status'],'FAIL');self.assertEqual(r['case3_only'],[('a','onwind')])
if __name__=='__main__':unittest.main()
