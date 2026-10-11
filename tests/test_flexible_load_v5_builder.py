from __future__ import annotations

import gzip
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from scripts.build_flexible_load_v5_inputs import write_canonical_csv, parameters


class FlexibleLoadV5BuilderTests(unittest.TestCase):
    def test_pathways_and_scalar_fallback(self):
        current=parameters(Path('config/flexible_load_v5_central_parameters.csv'))
        legacy=parameters(Path('config/legacy/flexible_load_v5_central_parameters.csv'))
        self.assertEqual(current['ev.v1g_participation_fraction'][2060],.5)
        self.assertEqual(legacy['ev.v1g_participation_fraction'][2060],.15)
        self.assertEqual(current['thermal.activation_cost_precondition'][2030],0)
        frame=pd.read_csv('config/flexible_load_v5_central_parameters.csv')
        frame.loc[frame.parameter_id.eq('ev.v1g_participation_fraction'),'central_2060']=.1
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'parameters.csv';frame.to_csv(path,index=False)
            with self.assertRaisesRegex(ValueError,'nondecreasing'):parameters(path)

    def test_canonical_csv_is_repeatable_and_platform_neutral(self):
        frame = pd.DataFrame(
            {
                "province_code": [11, 12],
                "value": [0.1, 1.0 / 3.0],
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.csv.gz"
            second = root / "second.csv.gz"
            plain = root / "plain.csv"

            write_canonical_csv(frame, first, compressed=True)
            write_canonical_csv(frame, second, compressed=True)
            write_canonical_csv(frame, plain, compressed=False)

            expected = (
                b"province_code,value\n"
                b"11,0.10000000000000001\n"
                b"12,0.33333333333333331\n"
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(gzip.decompress(first.read_bytes()), expected)
            self.assertEqual(plain.read_bytes(), expected)
            self.assertEqual(first.read_bytes()[4:8], b"\x00\x00\x00\x00")


if __name__ == "__main__":
    unittest.main()
