"""Author 2026-10-27 Mt boundary, evidence and preservation regression tests."""
import copy
import math
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from cispo_model.relative_acceptance import MT_METRICS, add_relative_profile, assess_relative_v1, archived_inputs
from test_relative_acceptance import fixture


class RelativeMtTests(unittest.TestCase):
    def qc(self, emissions=2000.):
        q = fixture()
        q['annual_fossil_unabated_emissions_mtco2'] = emissions
        q['annual_emissions_before_dac_mtco2'] = -100
        q['annual_net_emissions_mtco2'] = -200
        for check, metric in MT_METRICS.items():
            q['hard_checks'][check] = False
            q[metric] = max(1e-5, 1e-6*emissions)
        return q

    def test_each_balance_inclusive_boundary_and_failure(self):
        for check, metric in MT_METRICS.items():
            with self.subTest(check=check):
                q = self.qc()
                self.assertEqual(assess_relative_v1(q)['status'], 'PASS')
                q[metric] = math.nextafter(.002, math.inf)
                r = assess_relative_v1(q)
                self.assertEqual(r['status'], 'HARD_FAIL')
                self.assertEqual(r['checks']['extended_mt_mass_balance_checks']['failed'], [check])

    def test_floor_small_positive_emissions(self):
        for emission in [1., 10.]:
            q = self.qc(emission)
            r = assess_relative_v1(q)
            self.assertEqual(r['status'], 'PASS')
            self.assertEqual(r['checks']['extended_mt_mass_balance_checks']['checks']['co2_source']['relative_tolerance_mt'], 1e-5)
            q[MT_METRICS['co2_source']] = math.nextafter(1e-5, math.inf)
            self.assertEqual(assess_relative_v1(q)['status'], 'HARD_FAIL')

    def test_short_window_never_annualizes_or_uses_annual_label(self):
        q = self.qc(1e6)
        q['optimization_hours'] = 24
        for metric in MT_METRICS.values():
            q[metric] = 1e-5
        r = assess_relative_v1(q)
        self.assertEqual(r['status'], 'PASS')
        row = r['checks']['extended_mt_mass_balance_checks']['checks']['co2_source']
        self.assertIsNone(row['annual_total_emissions_mt'])
        q[MT_METRICS['co2_source']] = 1.1e-5
        self.assertEqual(assess_relative_v1(q)['status'], 'HARD_FAIL')

    def test_missing_nonfinite_and_mismatched_evidence_fails_closed(self):
        q = self.qc()
        del q['annual_fossil_unabated_emissions_mtco2']
        self.assertEqual(add_relative_profile(q)['status'], 'ERROR')
        self.assertEqual(assess_relative_v1(q, inputs={'annual_fossil_unabated_emissions_mtco2':2000.})['status'], 'PASS')
        for metric in list(MT_METRICS.values())+['annual_fossil_unabated_emissions_mtco2']:
            for bad in [float('nan'), float('inf')]:
                q = self.qc(); q[metric] = bad
                self.assertEqual(add_relative_profile(q)['status'], 'ERROR')
        for bad in [0., -1.]:
            q = self.qc(bad)
            self.assertEqual(add_relative_profile(q)['status'], 'ERROR')
        q = self.qc()
        self.assertEqual(add_relative_profile(q, inputs={'annual_fossil_unabated_emissions_mtco2':2001.})['status'], 'ERROR')
        q = self.qc(); del q[MT_METRICS['co2_source']]
        self.assertEqual(add_relative_profile(q)['status'], 'ERROR')

    def test_other_mt_limits_stay_strict_and_original_fields_unchanged(self):
        q = self.qc(); before = copy.deepcopy(q)
        self.assertEqual(add_relative_profile(q)['status'], 'PASS')
        q.pop('acceptance_profiles')
        self.assertEqual(q, before)
        for key in ['carbon', 'co2_sink', 'dac_selected_horizon_capacity']:
            q = self.qc(); q['hard_checks'][key] = False
            self.assertEqual(assess_relative_v1(q)['status'], 'HARD_FAIL')

    def test_archived_fossil_denominator_is_manifest_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            raw=json.dumps({'annual_fossil_unabated_emissions_mtco2':1234.0}).encode()
            path=root/'annual_carbon_ccs.json';path.write_bytes(raw)
            manifest={'files':[{'path':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}]}
            (root/'result_manifest.json').write_text(json.dumps(manifest))
            evidence=archived_inputs(root)
            self.assertEqual(evidence['annual_fossil_unabated_emissions_mtco2'],1234.0)
            self.assertEqual(evidence['annual_carbon_source']['sha256'],hashlib.sha256(raw).hexdigest())
            path.write_bytes(raw+b' ')
            with self.assertRaises(ValueError):archived_inputs(root)


if __name__ == '__main__':
    unittest.main()
