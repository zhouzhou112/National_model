from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from cispo_model.io_contract import write_output_catalog


class IOContractTests(unittest.TestCase):
    def test_output_catalog_is_pickle_free_and_excludes_runtime_wrapper_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            pd.DataFrame({"power_gw": [1.0], "hour_index": [0]}).to_csv(
                output_dir / "hourly.csv", index=False
            )
            np.savez_compressed(
                output_dir / "transmission_flows.npz",
                forward_gw=np.zeros((1, 2)),
                reverse_gw=np.zeros((1, 2)),
                line_ids=np.asarray(["L1"], dtype=str),
                hour_index=np.arange(2),
            )
            (output_dir / "solution_qc.json").write_text(
                json.dumps({"status": "PASS"}) + "\n", encoding="utf-8"
            )
            (output_dir / "run.stdout").write_text("runtime\n", encoding="utf-8")

            catalog_path, dictionary_path = write_output_catalog(output_dir)
            catalog = pd.read_csv(catalog_path)
            dictionary = pd.read_csv(dictionary_path)

            self.assertNotIn("run.stdout", set(catalog.file_path))
            self.assertIn("transmission_flows.npz", set(catalog.file_path))
            line_ids = dictionary.loc[
                dictionary.file_path.eq("transmission_flows.npz")
                & dictionary.field.eq("line_ids")
            ].iloc[0]
            self.assertEqual(line_ids["dimensions"], "corridor")
            with np.load(output_dir / "transmission_flows.npz", allow_pickle=False) as archive:
                self.assertEqual(archive["line_ids"].tolist(), ["L1"])


if __name__ == "__main__":
    unittest.main()
