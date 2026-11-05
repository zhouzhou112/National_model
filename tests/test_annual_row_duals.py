"""Annual accounting dual schema, physical signs and export completeness."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import gurobipy as gp
import numpy as np
import pandas as pd

from cispo_model.solution_export import export_annual_row_duals
from cispo_model.io_contract import write_output_catalog


class AnnualRowDualTests(unittest.TestCase):
    def test_physical_annual_rows_and_paired_duals(self):
        model = gp.Model()
        model.Params.OutputFlag = 0
        model.Params.Method = 2
        model.Params.Crossover = 0
        provinces = np.arange(11, 42)
        families = ["non_spatial_injection", "effective_demand", "external_sent",
                    "external_received", "external_net_import"]
        registry = {"province_annual_" + f: {} for f in families}
        registry["load_center_annual_energy_balance"] = {}
        for city, province in enumerate(provinces):
            generation = model.addVar()
            injection = model.addVar(lb=-gp.GRB.INFINITY)
            demand = model.addVar(lb=-gp.GRB.INFINITY)
            registry["province_annual_non_spatial_injection"][province] = model.addConstr(
                injection == generation, name=f"province_annual_non_spatial_injection_p{province}")
            registry["province_annual_effective_demand"][province] = model.addConstr(
                demand == 1, name=f"province_annual_effective_demand_p{province}")
            for family in families[2:]:
                account = model.addVar(lb=-gp.GRB.INFINITY)
                registry["province_annual_" + family][province] = model.addConstr(
                    account == 0, name=f"province_annual_{family}_p{province}")
            registry["load_center_annual_energy_balance"][city] = model.addConstr(
                injection == demand, name=f"load_center_annual_energy_balance_{city}")
            generation.Obj = 0.5
        flow = model.addMVar(31, obj=-1)
        registry["intra_load_center_annual_capacity"] = model.addConstr(
            flow <= np.ones(31), name="intra_load_center_annual_capacity")
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.OPTIMAL)
        data = SimpleNamespace(province_codes=provinces,
            load_centers=pd.DataFrame({"province_code": provinces, "load_center_id": [f"C{i}" for i in range(31)]}),
            intra_load_center_edges=pd.DataFrame({"province_code": provinces, "intra_edge_id": [f"E{i}" for i in range(31)]}))
        artifacts = SimpleNamespace(index={"constraint_handles": {"annual_load_center_rows": registry}})
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            table = export_annual_row_duals(artifacts, data, output, dual_attribute="BarPi")
            self.assertTrue((output / "annual_row_duals.csv").is_file())
            self.assertEqual(len(table), 217)
            self.assertEqual(set(table.unit), {"million CNY/GWh"})
            self.assertEqual(list(table), ["row_family", "row_name", "index", "province_code", "city_index",
                "pi_million_cny_per_gwh", "original_row_index", "row_sense", "entity_id", "unit"])
            paired = table[table.row_family.isin(["province_annual_non_spatial_injection",
                "province_annual_effective_demand"])].groupby("province_code").pi_million_cny_per_gwh.sum()
            self.assertLess(float(paired.abs().max()), 1e-8)
            self.assertTrue(table[table.row_family.eq("intra_load_center_annual_capacity")].pi_million_cny_per_gwh.lt(0).all())
            original = np.asarray(model.getAttr("BarPi", model.getConstrs()))
            np.testing.assert_array_equal(table.pi_million_cny_per_gwh, original[table.original_row_index])
            write_output_catalog(output)
            dictionary = pd.read_csv(output / "output_data_dictionary.csv")
            self.assertEqual(dictionary.loc[dictionary.field.eq("pi_million_cny_per_gwh"), "unit"].iloc[0], "million CNY/GWh")
            registry["province_annual_effective_demand"].pop(11)
            with self.assertRaisesRegex(ValueError, "Incomplete annual row family"):
                export_annual_row_duals(artifacts, data, output, dual_attribute="BarPi")
        model.dispose()


if __name__ == "__main__":
    unittest.main()
