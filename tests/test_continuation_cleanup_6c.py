"""Author 6c protection: lifetime boundary, asset identity and no hidden cutoff."""
from pathlib import Path
import importlib.util
import unittest
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'supplementary_materials/reviews/base_2060_launch_20261012/audit_cleanup_6b.py'
spec=importlib.util.spec_from_file_location('cleanup_6c',PATH)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class RetrofitProtectionTests(unittest.TestCase):
    def test_retirement_boundary_and_action(self):
        frame=pd.DataFrame([
            ['thermal','bio','15::bio','retrofit_out',2050,2080,-.2],
            ['thermal','gas','54::gas','retrofit_out',2030,2060,-.1],
            ['thermal','coal','23::coal','retrofit_out',2061,2091,-.1],
            ['thermal','coalccs','23::coalccs','retrofit_in',2050,2080,.1],
            ['thermal','gas','46::gas','new_build',2050,2080,.1],
        ],columns=['asset_class','technology','asset_id','action','build_year','retire_year','capacity_delta'])
        self.assertEqual(audit.active_retrofit_assets(frame),{('thermal','bio','15::bio')})

    def test_presence_rule_has_no_implicit_magnitude_threshold(self):
        frame=pd.DataFrame([
            ['thermal','bio','31::bio','retrofit_out',2040,2070,-1e-15],
            ['thermal','gas','11::gas','retrofit_out',2050,2080,-0.0],
        ],columns=['asset_class','technology','asset_id','action','build_year','retire_year','capacity_delta'])
        before=frame.copy(deep=True)
        self.assertEqual(audit.active_retrofit_assets(frame),{('thermal','bio','31::bio'),('thermal','gas','11::gas')})
        pd.testing.assert_frame_equal(before,frame)

if __name__=='__main__':unittest.main()
