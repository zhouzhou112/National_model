"""Independent HiGHS checks of paired-column pricing and scenario drift."""
import unittest
import numpy as np
from scipy.optimize import linprog


def solve(night, restrict=False):
    # Two capacity/new pairs plus dispatch backup: columns capA,capB,newA,newB,backup.
    c=np.array([1.,1.5,0.,0.,2.])
    eq=np.array([[1.,0.,-1.,0.,0.],[0.,1.,0.,-1.,0.]])
    ub=np.array([[-1.,-1.,0.,0.,0.],[0.,-1.,0.,0.,-1.]])
    bounds=[(0,2),(0,2),(0,2),(0,0 if restrict else 2),(0,2)]
    r=linprog(c,A_ub=ub,b_ub=[-1,-night],A_eq=eq,b_eq=[0,0],bounds=bounds,method="highs")
    if not r.success:raise RuntimeError(r.message)
    rc=c-eq.T@r.eqlin.marginals-ub.T@r.ineqlin.marginals
    return r,rc


class PricingChecks(unittest.TestCase):
    def test_base_margin_can_omit_scenario_optimum(self):
        base,rc=solve(0)
        self.assertGreater((rc[1]+rc[3])/1.5,.2)
        full,_=solve(.5)
        restricted,rrc=solve(.5,True)
        self.assertGreater(restricted.fun,full.fun)
        self.assertLess(rrc[1]+rrc[3],0)

    def test_reentry_recovers_full_optimum(self):
        restricted,rc=solve(.5,True)
        self.assertLess(rc[1]+rc[3],-1e-6)
        restored,_=solve(.5,False)
        self.assertAlmostEqual(restored.fun,1.25)
        self.assertAlmostEqual(restored.x[1],.5)

    def test_pair_price_cancels_arbitrary_accounting_dual(self):
        _,rc=solve(.5,True)
        shifted=rc.copy();shifted[1]-=17;shifted[3]+=17
        self.assertAlmostEqual(rc[1]+rc[3],shifted[1]+shifted[3])

    def test_rc_matches_bound_duals(self):
        r,rc=solve(.5,True)
        np.testing.assert_allclose(rc,r.lower.marginals+r.upper.marginals,atol=1e-12)

    def test_negative_price_requires_potential_weighting(self):
        # A small tolerated price error can still imply a material system gap.
        rc=np.array([-0.0001,-0.0001]); headroom=np.array([1.,10000.])
        self.assertGreater(float(np.dot(np.maximum(-rc,0),headroom)),1.)


if __name__=="__main__":unittest.main()
