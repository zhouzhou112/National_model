"""Offline checks of service-pool accounting and province/hour price alignment."""
import tempfile,unittest
from pathlib import Path
import numpy as np
import pandas as pd
from metrics_flex import service_deviations,price_arrays,sha

class MetricsTests(unittest.TestCase):
 def test_nested_pool_and_discharge_not_double_counted(self):
  f={'ev_enrolled_service_fraction':np.array([.8,.3]),'ev_bidirectional_service_fraction':np.array([.2,.1])}
  for name,value in [('baseline_heating_gw',3),('actual_heating_gw',2),('baseline_cooling_gw',5),('actual_cooling_gw',7),('baseline_ev_gw',10),('ev_v1g_pool_charge',.4),('ev_v2g_pool_charge',.3),('ev_v2g_discharge_gw',.2)]:f[name]=np.full((2,3),value,dtype=float)
  d=service_deviations(f,.2)
  expected_ev=.4+.3-.2-f['ev_enrolled_service_fraction'][:,None]*2
  np.testing.assert_allclose(d[:,2:].sum(axis=1),np.broadcast_to(expected_ev,(2,3)))
  np.testing.assert_allclose(d.sum(axis=1),1+np.broadcast_to(expected_ev,(2,3)))
 def test_price_alignment_and_unit_conversion(self):
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp);p=np.arange(11,42);h=np.arange(2)
   annual=[]
   for province in p:
    annual.extend([{'province_code':province,'row_family':'province_annual_effective_demand','pi_million_cny_per_gwh':-3.},{'province_code':province,'row_family':'province_annual_non_spatial_injection','pi_million_cny_per_gwh':3.000001}])
   ap=tmp/'annual.csv';pd.DataFrame(annual).to_csv(ap,index=False)
   data=[]
   for province in p:
    for hour in h:data.append(dict(province_code=province,hour_index=hour,datetime_bj=f'2024-01-01 0{hour}:00:00',power_balance_pi_million_cny_per_gwh=3.2+hour/10,up_reserve_pi_million_cny_per_gwh=.01,down_reserve_pi_million_cny_per_gwh=.03,inertia_pi_million_cny_per_gw_s=.02))
   path=tmp/'hourly_marginal_prices.csv.gz';pd.DataFrame(data[::-1]).to_csv(path,index=False)
   class I:
    def path(self,name):return tmp/name
   c={'security':{'up_reserve_load_fraction':.05,'down_reserve_load_fraction':.05,'inertia_reference_seconds':3.5,'inertia_tolerance_fraction':1}}
   e,r,i,dates,m=price_arrays(I(),ap,sha(ap),p,h,c)
   np.testing.assert_allclose(e,np.tile([200,300],(31,1)))
   np.testing.assert_allclose(r,2);np.testing.assert_allclose(i,70)
   self.assertAlmostEqual(m['annual_pair_max_abs_cny_per_mwh'],.001)
   self.assertEqual(pd.Timestamp(dates[0]).hour,0)

if __name__=='__main__':unittest.main()
