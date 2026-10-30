import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1]/'supplementary_materials/reviews/C2050_completed_20261029/review_author_conditions.py'
spec = importlib.util.spec_from_file_location('author_row', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AuthorRowConditionTests(unittest.TestCase):
    def row(self, violation):
        return dict(name='province_annual_external_sent_p13', status='ORDER_AND_ROW_VERIFIED',
                    sense='=', violation=violation, row_magnitude=272271.9813274182)

    def test_small_ratio_does_not_invent_new_tolerance(self):
        result = module.row_family_check(self.row(.012132954492699355))
        self.assertLess(result['relative_residual'], 1e-6)
        self.assertFalse(result['passed'])
        self.assertGreater(result['ratio_to_authorized_tolerance'], 12)

    def test_absolute_floor_boundary(self):
        self.assertTrue(module.row_family_check(self.row(.001))['passed'])
        self.assertFalse(module.row_family_check(self.row(.00100001))['passed'])

    def test_author_1030_annual_rule_is_explicit_and_bounded(self):
        result = module.row_family_check(self.row(.012132954492699355), annual_account_relative=True)
        self.assertTrue(result['passed'])
        self.assertAlmostEqual(result['tolerance_gwh'], .2722719813274182)
        self.assertFalse(module.row_family_check(self.row(.3), annual_account_relative=True)['passed'])
        row = self.row(.001);row['row_magnitude']=100
        self.assertEqual(module.row_family_check(row, annual_account_relative=True)['tolerance_gwh'], .001)

    def test_unknown_family_or_nonfinite_fails_closed(self):
        row = self.row(0)
        row['name'] = 'another_row'
        with self.assertRaises(ValueError):
            module.row_family_check(row)
        with self.assertRaises(ValueError):
            module.row_family_check(self.row(float('nan')))


if __name__ == '__main__':
    unittest.main()
