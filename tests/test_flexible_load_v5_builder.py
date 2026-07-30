from __future__ import annotations

import gzip
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from scripts.build_flexible_load_v5_inputs import write_canonical_csv


class FlexibleLoadV5BuilderTests(unittest.TestCase):
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
