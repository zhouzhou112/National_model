from pathlib import Path
from types import SimpleNamespace
import json,tempfile,unittest
import numpy as np
import pandas as pd
from scripts.run_resource_sensitivity_case import runtime_contract_audit

class RuntimeResourceAuditTest(unittest.TestCase):
    def fixture(self,tmp):
        p=Path(tmp)/'reference.csv'
        p.write_text('resource_scenario,weather_year,planning_year,participation_setting,heating_ceiling_gw,cooling_ceiling_gw,smart_ceiling_gw,discharge_ceiling_gw\nOpen,2024,2050,Full,6,8,10,12\n')
        cfg=SimpleNamespace(planning_year=2050,weather_year=2024,raw={'flexible_load':{'ev_v2g':{'national_contracted_power_cap_gw_by_planning_year':{'2050':1000}}}})
        data=SimpleNamespace(provinces=pd.DataFrame({'province_code':[11,12]}))
        art=SimpleNamespace(model=SimpleNamespace(update=lambda:None),variables={'flexible_service_capacity':SimpleNamespace(UB=np.array([[1.,2,3,4],[5,6,7,8]]))},index={'optimization_hours':8760,'flexible_load_structural_audit':{'effective_load_nonnegative_constraint_rows_added':139}})
        return p,cfg,data,art

    def test_actual_annual_bounds_and_nonbinding_cap_are_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,c,d,a=self.fixture(tmp);before=a.variables['flexible_service_capacity'].UB.copy();r=runtime_contract_audit(c,d,a,'open',p)
            self.assertEqual(r['status'],'PASS');self.assertEqual(r['actual_upper_sums_gw'],[6,8,10,12]);self.assertEqual(r['national_v2g_slack_lower_bound_gw'],988.)
            json.dumps(r,allow_nan=False);np.testing.assert_array_equal(before,a.variables['flexible_service_capacity'].UB)

    def test_wrong_bounds_and_row_count_are_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,c,d,a=self.fixture(tmp);a.variables['flexible_service_capacity'].UB[0,0]+=.01;a.index['flexible_load_structural_audit']['effective_load_nonnegative_constraint_rows_added']=0
            r=runtime_contract_audit(c,d,a,'open',p);self.assertEqual(r['status'],'FAIL');self.assertFalse(r['checks']['annual_upper_matches_reference']);self.assertFalse(r['checks']['effective_load_row_count'])

    def test_short_windows_cannot_claim_annual_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,c,d,a=self.fixture(tmp);a.index['optimization_hours']=24
            with self.assertRaises(ValueError):runtime_contract_audit(c,d,a,'open',p)

if __name__=='__main__':unittest.main()
