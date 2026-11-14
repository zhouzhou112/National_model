import unittest
from compare_costs import interval

class CostIntervalTest(unittest.TestCase):
    def test_unscreened_reference(self):
        self.assertEqual(interval(dict(P=110,D=108,B=0),dict(P=100,D=95,B=1)),dict(point=10,lower=8,upper=16))

    def test_screened_C_bound_reduces_lower_endpoint(self):
        r=interval(dict(P=102,D=96,B=.5),dict(P=100,D=95,B=1))
        self.assertEqual(r,dict(point=2,lower=-4.5,upper=8))
        self.assertLessEqual(r['lower'],0)
        self.assertGreaterEqual(r['upper'],0)

    def test_A_bound_only_increases_upper_endpoint(self):
        ref=dict(P=102,D=96,B=.5)
        before=interval(ref,dict(P=100,D=95,B=0))
        after=interval(ref,dict(P=100,D=95,B=2))
        self.assertEqual(before['point'],after['point'])
        self.assertEqual(before['lower'],after['lower'])
        self.assertEqual(after['upper']-before['upper'],2)

if __name__=='__main__':unittest.main()
