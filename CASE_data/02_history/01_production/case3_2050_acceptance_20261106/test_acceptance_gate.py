"""Fail-closed tests for the author evidence gate, no solver calls."""
import copy,unittest
from finalize_acceptance import decide,distributions,row_check
class EvidenceGateTest(unittest.TestCase):
 def setUp(self):
  self.profile={'checks':{'power_balance':{'passed':True},'reservoir_transition':{'passed':None,'status':'DEFERRED_BY_AUTHOR_20261012'},'solver':{'passed':False}}}
  self.solve={'status':'OPTIMAL','solution_contract':{'barrier_primal_dual_metrics':{'primal_infeasibility':.055,'relative_primal_dual_objective_gap':.0008}}}
  self.cert={'scope':'FULL_YEAR','B_over_objective':.001}
 def test_accept_only_with_all_conditions(self):
  c,d=decide(self.profile,self.solve,{'passed':True},self.cert);self.assertTrue(all(c.values()));self.assertEqual(d,['reservoir_transition'])
 def test_physical_failure_and_unknown_deferred_block(self):
  for value in [False,None]:
   self.profile['checks']['power_balance']['passed']=value
   self.assertFalse(all(decide(self.profile,self.solve,{'passed':True},self.cert)[0].values()))
 def test_large_or_nonfinite_pinf_and_certificate_block(self):
  for x in [.100001,float('nan')]:
   self.solve['solution_contract']['barrier_primal_dual_metrics']['primal_infeasibility']=x
   self.assertFalse(all(decide(self.profile,self.solve,{'passed':True},self.cert)[0].values()))
  self.setUp();self.cert['B_over_objective']=.010001
  self.assertFalse(all(decide(self.profile,self.solve,{'passed':True},self.cert)[0].values()))
 def test_row_must_be_verified_family(self):
  with self.assertRaises(ValueError):row_check({'status':'ORDER_AND_ROW_VERIFIED','sense':'=','name':'other_p13'})
 def test_annual_tolerance_uses_energy_scale(self):
  row={'status':'ORDER_AND_ROW_VERIFIED','sense':'=','name':'province_annual_external_sent_p13','terms':[{'variable':'province_annual_external_sent_gwh[2]','coefficient':1,'contribution':200000}]+[{'variable':f'flow_forward_gw[0,{i}]','coefficient':-1,'contribution':-200000/8760} for i in range(8760)],'row_magnitude':200000,'violation':.02}
  x=row_check(row);self.assertTrue(x['passed']);self.assertAlmostEqual(x['tolerance_gwh'],.2)
  row['terms'][1]['coefficient']=-.9
  with self.assertRaises(ValueError):row_check(row)
 def test_distribution_is_joined_and_equal_weighted(self):
  prices=[{'grid_uid':'b','technology':'wind','province_code':'13','rc_ratio':.4,'rc_build':4},{'grid_uid':'a','technology':'pv','province_code':'11','rc_ratio':-.1,'rc_build':-1}]
  selection=[{'grid_uid':'a','technology':'pv','screened_out':'true','original_new_ub_gw':2,'rc_ratio':.3},{'grid_uid':'b','technology':'wind','screened_out':'true','original_new_ub_gw':3,'rc_ratio':.2}]
  r,_=distributions(prices,selection,2);self.assertEqual(r['below_0p1_fraction'],.5);self.assertAlmostEqual(r['delta_median'],-.1);self.assertEqual(r['B_recomputed_million_cny'],2)
  with self.assertRaises(ValueError):distributions(prices,selection,6195)
if __name__=='__main__':unittest.main()
