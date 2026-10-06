"""DAC availability must switch by year without locking out later investment."""
from copy import deepcopy
import unittest

import numpy as np

from cispo_model.config import ModelConfig, load_model_config
from cispo_model.data import load_model_data
from cispo_model.monolithic import build_full_year_monolithic
from cispo_model.run_contract import analysis_case_identity


CONFIG = 'config/optimization_numeric_dac_by_year_v9.json'


class DacYearScheduleConfigTests(unittest.TestCase):
    def test_sequence_and_restart_resolve_same_availability_without_mutating_source(self):
        source = load_model_config(CONFIG)
        for year in source.planning_years:
            direct = source.for_planning_year(year)
            self.assertEqual(direct.raw['features']['dac'], year != 2030)
            restarted = source.for_planning_year(2040).for_planning_year(year)
            self.assertEqual(direct.raw, restarted.raw)
        self.assertFalse(source.raw['features']['dac'])

    def test_legacy_configs_keep_their_original_behavior(self):
        legacy = load_model_config()
        for year in legacy.planning_years:
            self.assertTrue(legacy.for_planning_year(year).raw['features']['dac'])
        with self.assertRaisesRegex(ValueError, 'Disabling DAC'):
            load_model_config('config/optimization_2030_numeric_final_v8.json').for_planning_year(2040)

    def test_incomplete_nonboolean_or_later_disabled_schedules_are_rejected(self):
        cfg = load_model_config(CONFIG)
        bad_schedules = [
            {'2030': False, '2040': True},
            {'2030': False, '2040': 'true', '2050': True, '2060': True},
            {'2030': False, '2040': True, '2050': True, '2060': False},
        ]
        for schedule in bad_schedules:
            with self.subTest(schedule=schedule):
                raw = deepcopy(cfg.raw)
                raw['features']['dac_by_planning_year'] = schedule
                with self.assertRaises(ValueError):
                    ModelConfig(cfg.path, raw).validate()

    def test_active_flag_cannot_disagree_with_schedule(self):
        cfg = load_model_config(CONFIG)
        raw = deepcopy(cfg.raw)
        raw['features']['dac'] = True
        with self.assertRaisesRegex(ValueError, 'active planning-year schedule'):
            ModelConfig(cfg.path, raw).validate()

    def test_full_schedule_is_part_of_scientific_identity(self):
        later = load_model_config(CONFIG).for_planning_year(2040)
        raw = deepcopy(later.raw)
        raw['features']['dac_by_planning_year']['2030'] = True
        changed = ModelConfig(later.path, raw)
        changed.validate()
        key = 'resolved_scientific_configuration_sha256'
        self.assertNotEqual(analysis_case_identity(later)[key], analysis_case_identity(changed)[key])


class DacLaterYearModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_model_config(CONFIG).for_planning_year(2040)
        cls.data = load_model_data(cls.cfg)
        cls.art = build_full_year_monolithic(
            cls.cfg, cls.data, compute_max_cf=False, optimization_hours=1)
        cls.art.model.update()

    @classmethod
    def tearDownClass(cls):
        cls.art.model.dispose()

    def test_zero_inherited_dac_allows_positive_new_capacity_and_capture(self):
        np.testing.assert_array_equal(self.art.index['dac_capacity_floor_mtpa'], 0.0)
        for name in ['dac_new', 'dac_capacity', 'dac_capture']:
            self.assertTrue(np.all(self.art.variables[name].UB > 0.0), name)
        model = self.art.model
        row = model.getRow(model.getConstrByName('dac_capacity_accounting[0,0]'))
        terms = {row.getVar(i).VarName: row.getCoeff(i) for i in range(row.size())}
        self.assertEqual(terms['dac_capacity_mtpa[0,0]'], 1.0)
        self.assertEqual(terms['dac_new_capacity_mtpa[0,0]'], -1.0)

    def test_later_year_restores_dac_electricity_and_preserves_carbon_limit(self):
        model = self.art.model
        for code in self.data.province_codes:
            row = model.getRow(model.getConstrByName(f'strict_power_balance_p{code}[0]'))
            self.assertTrue(any(row.getVar(i).VarName.startswith('dac_capture_mt')
                                for i in range(row.size())))
        expected = self.data.carbon.emissions_limit_mtco2_per_year * self.art.index['annual_flow_scaling_factor']
        self.assertAlmostEqual(model.getConstrByName('annual_net_carbon_limit').RHS, expected)
        self.assertTrue(self.data.dac.year.eq(2040).all())


if __name__ == '__main__':
    unittest.main()
