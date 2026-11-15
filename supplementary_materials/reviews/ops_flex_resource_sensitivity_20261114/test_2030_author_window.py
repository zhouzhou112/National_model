"""Scope and immutability checks for the explicit engineering-only exception."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,tempfile,unittest
import window_gate_2030_author as gate
class AuthorWindowTests(unittest.TestCase):
 def fixture(self,root):
  source=root/'source';source.mkdir();(source/'result_manifest.json').write_text('{}');digest=hashlib.sha256((source/'result_manifest.json').read_bytes()).hexdigest()
  quota=4000*24/8760;row=SimpleNamespace(Sense='<',RHS=quota);art=SimpleNamespace(index={'annual_flow_scaling_factor':24/8760,'annual_carbon_limit_mtco2_per_year':4000,'constraint_handles':{'annual_net_carbon_limit':row}},model=SimpleNamespace(update=lambda:None))
  budget=dict(status='PASS',year=2030,hour_indices=list(range(24)),budget_rule=gate.RULE,author_approval='2030沿用原B窗口额度（推荐）',source_result_manifest_sha256=digest,window_carbon_limit_mt=quota,original_annual_carbon_limit_mt=4000,previous_failed_budget_mt=9.002825025595003)
  p=root/'budget.json';p.write_text(json.dumps(budget),encoding='utf-8');return source,digest,row,art,budget,p
 def test_exact_quota_does_not_change_annual_limit(self):
  with tempfile.TemporaryDirectory() as t:
   source,digest,row,art,b,p=self.fixture(Path(t));before=row.RHS
   with patch.object(gate,'SOURCE_SHA',digest):r=gate.apply_window_budget(art,p,source,2030,24,Path(t))
   self.assertEqual(row.RHS,before);self.assertEqual(art.index['annual_carbon_limit_mtco2_per_year'],4000);self.assertEqual(r['scope'],'TEST_ONLY_TRUNCATED_HORIZON')
 def test_other_year_or_full_horizon_rejected_before_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   source,digest,row,art,b,p=self.fixture(Path(t));before=row.RHS
   for year,hours in [(2040,24),(2060,24),(2030,8760),(2030,1)]:
    with patch.object(gate,'SOURCE_SHA',digest),self.assertRaises(ValueError):gate.apply_window_budget(art,p,source,year,hours,Path(t))
    self.assertEqual(row.RHS,before)
 def test_wrong_identity_or_budget_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   source,digest,row,art,b,p=self.fixture(Path(t));before=row.RHS
   for k,v in [('window_carbon_limit_mt',11.),('original_annual_carbon_limit_mt',4001),('author_approval',''),('source_result_manifest_sha256','wrong')]:
    changed=dict(b);changed[k]=v;p.write_text(json.dumps(changed),encoding='utf-8')
    with patch.object(gate,'SOURCE_SHA',digest),self.assertRaises(ValueError):gate.apply_window_budget(art,p,source,2030,24,Path(t))
    self.assertEqual(row.RHS,before)
if __name__=='__main__':unittest.main()
