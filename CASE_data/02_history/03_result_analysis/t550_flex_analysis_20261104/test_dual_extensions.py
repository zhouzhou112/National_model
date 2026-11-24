"""Small non-solver tests for raw-order digest and AC/DC subset mapping."""
from collections import Counter
import hashlib
import struct
import unittest
import numpy as np
from dual_extensions import RowsObserver


class RowExtractionTest(unittest.TestCase):
    def test_raw_order_sense_digest_and_subset_mapping(self):
        rows = [("L","ac_line_shared_capacity_hourly[0,0]"),
                ("L","dc_line_forward_capacity_hourly[0,1]"),
                ("E","load_center_annual_energy_balance_0")]
        observer = RowsObserver.__new__(RowsObserver)
        observer.pi = np.array([-2., -3., 7.])
        observer.index = 0
        observer.digest = hashlib.sha256(b"cispo_raw_lp_constraint_order_v1\0"+struct.pack(">Q",3))
        observer.families = Counter()
        observer.examples, observer.senses = {}, {}
        observer.ac, observer.dc = [1], [0]
        observer.hourly = np.full((2,2), np.nan)
        observer.selected_counts = Counter()
        observer.centers = [{"province_code":"11","load_center_id":"LC_TEST"}]
        observer.annual = []
        expected = bytearray(b"cispo_raw_lp_constraint_order_v1\0"+struct.pack(">Q",3))
        for i,(sense,name) in enumerate(rows):
            observer.consume(sense,name)
            b=name.encode()
            expected += struct.pack(">QQ",i,len(b))+b+({"E":b"=","L":b"<"}[sense])+b"\0"
        self.assertEqual(observer.digest.hexdigest(),hashlib.sha256(expected).hexdigest())
        self.assertEqual(observer.hourly[1,0],-2.)
        self.assertEqual(observer.hourly[0,1],-3.)
        self.assertTrue(np.isnan(observer.hourly[0,0]))
        self.assertEqual(observer.annual[0]["pi_million_cny_per_gwh"],7.)
        self.assertEqual(observer.annual[0]["city_index"],0)
        self.assertEqual(observer.annual[0]["original_row_index"],2)


if __name__=="__main__":
    unittest.main()
