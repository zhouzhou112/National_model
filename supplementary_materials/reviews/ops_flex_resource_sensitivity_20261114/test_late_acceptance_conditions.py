"""Small tests of the new evidence conjunction, without importing solver code."""
import ast,math,unittest
from pathlib import Path

source=Path(__file__).with_name('finalize_late_acceptance.py')
tree=ast.parse(source.read_text(encoding='utf-8'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='decide')
namespace={'math':math}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
decide=namespace['decide']

class Conditions(unittest.TestCase):
 def test_requires_all_independent_evidence(self):
  self.assertTrue(all(decide(True,True,True,.019,.0007,.001).values()))
  for i in range(3):
   flags=[True,True,True];flags[i]=False
   self.assertFalse(all(decide(*flags,.019,.0007,.001).values()))
 def test_large_certificate_stops(self):
  self.assertFalse(all(decide(True,True,True,.019,.0007,.010001).values()))
 def test_threshold_inclusive(self):
  self.assertTrue(all(decide(True,True,True,.1,.01,.01).values()))
 def test_bad_pinf_stops(self):
  for p in [-1,.009,.100001,float('inf'),float('nan')]:
   self.assertFalse(all(decide(True,True,True,p,.0007,.001).values()))
 def test_bad_gap_or_bound_stops(self):
  for x in [-1,.02,float('inf'),float('nan')]:
   self.assertFalse(all(decide(True,True,True,.019,x,.001).values()))
   self.assertFalse(all(decide(True,True,True,.019,.0007,x).values()))

if __name__=='__main__':unittest.main()
