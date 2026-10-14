import importlib.util
import unittest
from pathlib import Path
import pandas as pd
from cispo_model.continuation_cleanup import active_retrofit_assets,assess

ROOT=Path(__file__).resolve().parents[1]


class ReusableContinuationTests(unittest.TestCase):
    def test_lifetime_protection_uses_target_year_not_2060(self):
        frame=pd.DataFrame([
            ['thermal','bio','31::bio','retrofit_out',2040,2060,0.],
            ['thermal','gas','11::gas','retrofit_out',2050,2080,-1e-15],
        ],columns=['asset_class','technology','asset_id','action','build_year','retire_year','capacity_delta'])
        before=frame.copy(deep=True)
        self.assertEqual(active_retrofit_assets(frame,2050),{('thermal','bio','31::bio'),('thermal','gas','11::gas')})
        self.assertEqual(active_retrofit_assets(frame,2060),{('thermal','gas','11::gas')})
        pd.testing.assert_frame_equal(before,frame)

    def test_known_2050_cleanup_matches_independent_historical_audit(self):
        source=ROOT/'supplementary_materials/reviews/base_acceptance_relative_v1_20261012/evidence/2050'
        required=['planning_state_candidate/capacity_cohorts.csv.gz',
            'annual_capacity_by_technology.csv','intra_grid_vre_site_design.csv',
            'transmission_capacity.csv','load_center_intra_transmission.csv',
            'intra_grid_substation_design.csv','hydro_capacity.csv']
        if not all((source/name).exists() for name in required):
            self.skipTest('Complete local immutable 2050 archive not installed')
        old=ROOT/'supplementary_materials/reviews/base_2060_launch_20261012/audit_cleanup_6b.py'
        spec=importlib.util.spec_from_file_location('old_cleanup_reference',old)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        a,ca,da,na=module.assess(source,protect_active_retrofit=True)
        b,cb,db,nb=assess(source,planning_year=2060,source_year=2050)
        pd.testing.assert_frame_equal(ca,cb);pd.testing.assert_series_equal(da,db);pd.testing.assert_series_equal(na,nb)
        for key in ['status','generation_and_storage_deleted_gw','network_deleted_gw',
                    'retrofit_protected_groups','retained_negative_zeroing_increase_gw','source_sha256']:
            self.assertEqual(a[key],b[key],key)


if __name__=='__main__':unittest.main()
