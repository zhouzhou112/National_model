"""Check that the explicit 2030 simplification reaches the actual LP."""
from copy import deepcopy
import unittest
import numpy as np
from cispo_model.config import load_model_config,ModelConfig
from cispo_model.data import load_model_data
from cispo_model.monolithic import build_full_year_monolithic


class NumericSimplificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=load_model_config(path='config/optimization_2030_numeric_simplified_no_dac_v6.json')
        cls.data=load_model_data(cls.cfg)
        cls.art=build_full_year_monolithic(cls.cfg,cls.data,compute_max_cf=False,
                                           optimization_hours=1,optimization_start_hour=3960)
        cls.art.model.update()

    @classmethod
    def tearDownClass(cls): cls.art.model.dispose()

    def test_dac_fixed_to_zero_without_relaxing_carbon(self):
        for name in ['dac_new','dac_capacity','dac_capture']:
            np.testing.assert_array_equal(self.art.variables[name].UB,0.)
        np.testing.assert_array_equal(self.art.variables['dac_load'],0.)
        limit=self.art.model.getConstrByName('annual_net_carbon_limit')
        expected=self.data.carbon.emissions_limit_mtco2_per_year*self.art.index['annual_flow_scaling_factor']
        self.assertAlmostEqual(limit.RHS,expected)
        for code in self.data.province_codes:
            row=self.art.model.getRow(self.art.model.getConstrByName(f'strict_power_balance_p{code}[0]'))
            self.assertFalse(any(row.getVar(i).VarName.startswith('dac_') for i in range(row.size())))

    def test_small_existing_floors_removed_with_audit_and_sites_preserved(self):
        source=self.data.vre_sites.capacity_floor_gw.to_numpy(float)
        cleared=(source>0)&(source<1e-5)
        actual=np.asarray(self.art.variables['vre_capacity'].LB)
        self.assertEqual(len(actual),len(source))
        np.testing.assert_array_equal(actual[cleared],0.)
        np.testing.assert_array_equal(actual[~cleared],source[~cleared])
        audit=self.art.index['vre_capacity_floor_cleanup']
        self.assertAlmostEqual(audit['total_removed_gw'],float(source[cleared].sum()))

    def test_stronger_cf_cutoff_keeps_actual_availability_rows_consistent(self):
        for c in self.art.model.getConstrs():
            if c.ConstrName.startswith(('vre_availability_','wave_availability_','ror_availability_')):
                row=self.art.model.getRow(c)
                for i in range(row.size()): self.assertGreaterEqual(abs(row.getCoeff(i)),.01)

    def test_no_dac_case_cannot_silently_extend_to_later_years(self):
        raw=deepcopy(self.cfg.raw);raw['planning_year']=2040
        with self.assertRaises(ValueError): ModelConfig(self.cfg.path,raw).validate()
        raw=deepcopy(self.cfg.raw);raw['scientific_case']['case_id']='base_2024_vre_wave_on_flex_off_v1'
        with self.assertRaises(ValueError): ModelConfig(self.cfg.path,raw).validate()


if __name__=='__main__':unittest.main()
