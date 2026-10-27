import hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
from window_carbon import account_window
from window_gate import apply_window_budget


class WindowTests(unittest.TestCase):
    def test_fossil_ccs_beccs_and_constant_dac(self):
        table=pd.DataFrame({'technology':['coal','gas','bioccs'],
            'emission_factor_mtco2_per_gwh':[.00082,.00037,-.00177],
            'ccs_capture_fraction':[.9,.9,np.nan]}).set_index('technology')
        tech=['coal','coalccs','cchp','gchpccs','bio','bioccs']
        g=np.ones((1,len(tech),8760))
        r=account_window(g,tech,np.arange(8760),list(range(24)),table,.876)
        expected=(.00082+.000082+.00082+.000037-.00177-.0001)*24
        self.assertAlmostEqual(r['base_window_net_emissions_mt'],expected,places=14)
        self.assertEqual(r['window_carbon_limit_mt'],r['base_window_net_emissions_mt']*1.0001)
        self.assertLess(expected,0)  # preserve the author's multiplier, even negative
        self.assertAlmostEqual(r['annual_reconstructed_net_emissions_mt'],expected*365,places=12)
        with self.assertRaises(ValueError):account_window(g,tech,np.arange(8760),list(range(1,25)),table,.876)

    def test_scope_source_and_formula_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'result_manifest.json').write_text('{}')
            b=dict(status='PASS',year=2040,hour_indices=list(range(24)),
                source_result_manifest_sha256=hashlib.sha256(b'{}').hexdigest(),
                base_window_net_emissions_mt=5.,window_carbon_limit_mt=5.*1.0001,
                original_annual_carbon_limit_mt=1300.)
            row=SimpleNamespace(RHS=np.asarray(1300*24/8760),Sense=np.asarray('<'))
            index=dict(annual_flow_scaling_factor=24/8760,annual_carbon_limit_mtco2_per_year=1300.,
                       constraint_handles={'annual_net_carbon_limit':row})
            art=SimpleNamespace(index=index,model=SimpleNamespace(update=lambda:None))
            budget=p/'budget.json';budget.write_text(json.dumps(b))
            for y,h in [(2050,24),(2040,8760),(2040,1)]:
                with self.assertRaises(ValueError):apply_window_budget(art,budget,p,y,h,p)
            for key,value in [('source_result_manifest_sha256','bad'),('window_carbon_limit_mt',6.)]:
                bad=dict(b);bad[key]=value;budget.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):apply_window_budget(art,budget,p,2040,24,p)
            self.assertEqual(row.RHS,1300*24/8760)
            budget.write_text(json.dumps(b));result=apply_window_budget(art,budget,p,2040,24,p)
            self.assertEqual(row.RHS,5.*1.0001)
            self.assertEqual(index['annual_carbon_limit_mtco2_per_year'],1300.)
            self.assertTrue(result['production_annual_carbon_limit_unchanged'])


if __name__=='__main__':unittest.main()
