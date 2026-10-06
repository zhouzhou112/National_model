"""Small, solver-free mechanism checks; synthetic files stay under this review."""
import csv
import gzip
import datetime
import json
from pathlib import Path
import unittest

import audit_bounds as audit

HERE=Path(__file__).resolve().parent
RUN=HERE/'fixture_results'/datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f')


class AuditTests(unittest.TestCase):
    def fixture(self,name,body,expected=None):
        out=RUN/name
        out.mkdir(parents=True,exist_ok=False)
        p=out/'fixture.mps.gz'
        with gzip.open(p,'wt',encoding='ascii') as f:f.write(body)
        return out,audit.parse_mps(p,out,2030,expected,progress_every=10**9)

    def test_all_bound_rules_and_threshold_edges(self):
        cols=['default[0]','free[0]','mi[0]','pl[0]','fixed[0]','fixed_positive[0]',
              'tiny[0]','tiny[1]','edge[0]','edge[1]','edge[2]','edge[3]',
              'inherited[0]','inherited[1]','negative[0]']
        body='NAME fixture\nROWS\n N OBJ\n E ROW\nCOLUMNS\n'
        for c in cols:body+='    {} OBJ 1e20 ROW -2\n'.format(c)
        body+='RHS\n    rhs ROW 0\nBOUNDS\n'
        # Deliberately out of COLUMNS order, and repeated non-contiguous names.
        body+=' UP b tiny[1] 1e-10\n FR b free[0]\n MI b mi[0]\n UP b mi[0] -2\n'
        body+=' UP b pl[0] 3\n PL b pl[0]\n LO b pl[0] 2\n'
        body+=' FX b fixed[0] 0\n FX b fixed_positive[0] 2\n UP b tiny[0] 1e-14\n'
        for i,v in enumerate(['1e-12','1e-9','1e-6','1e-3']):body+=' UP b edge[{}] {}\n'.format(i,v)
        body+=' LO b inherited[0] 1\n UP b inherited[0] 1.0000001\n'
        body+=' UP b inherited[1] 2\n LO b inherited[1] 2\n'
        body+=' FR b negative[0]\n LO b negative[0] -2\n UP b negative[0] -1.99999999\nENDATA\n'
        out,r=self.fixture('rules',body,dict(rows=1,columns=15,nonzeros=15))
        t=r['totals']
        self.assertEqual([t[k] for k in ['fixed','infinite_range','finite_positive','tiny_nonfixed']], [3,4,8,6])
        self.assertEqual([t[k] for k in ['range_0_1e12','range_1e12_1e9','range_1e9_1e6','range_1e6_1e3']], [2,2,3,1])
        self.assertEqual(t['positive_lb_range_lt_1e6'],3)
        self.assertEqual(t['positive_lb_tiny_nonfixed'],1)
        self.assertEqual(t['zero_lb_positive_ub_lt_1e6'],4)
        self.assertEqual(r['matrix_abs_min'],2)
        self.assertEqual(r['matrix_abs_max'],2)
        self.assertEqual(r['objective_nnz_excluded'],15)
        with open(out/'tiny_bound_columns_2030.csv') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),9)
        self.assertEqual(sum(int(x['is_fixed']) for x in rows),3)
        with open(out/'smallest_50_nonfixed_2030.csv') as f:top=list(csv.DictReader(f))
        self.assertEqual(top[0]['name'],'tiny[0]')
        self.assertEqual([float(x['range']) for x in top],sorted(float(x['range']) for x in top))

    def test_dense_column_and_zero_objective_exclusion(self):
        n=10000
        body='NAME dense\nROWS\n N OBJ\n'+''.join(' E r{}\n'.format(i) for i in range(n))+'COLUMNS\n'
        body+='    dense[0] OBJ 5\n'+''.join('    dense[0] r{} {}\n'.format(i,1e-5 if i%2 else 6250) for i in range(n))
        body+='    sparse[0] OBJ 0 r0 0\nBOUNDS\n UP b dense[0] 1e-8\n FX b sparse[0] 0\nENDATA\n'
        _,r=self.fixture('dense',body,dict(rows=n,columns=2,nonzeros=n))
        self.assertEqual(r['tiny_nnz_distribution'],{'10000':1})
        self.assertEqual(r['totals']['tiny_nnz_ge_8760'],1)
        self.assertEqual(r['matrix_abs_min'],1e-5)
        self.assertEqual(r['matrix_abs_max'],6250)

    def test_no_bounds_defaults(self):
        _,r=self.fixture('defaults','NAME no_bounds\nROWS\n N OBJ\n E r\nCOLUMNS\n    x r 1\nENDATA\n')
        self.assertEqual(r['totals']['infinite_range'],1)

    def test_invalid_bounds_fail(self):
        with self.assertRaisesRegex(ValueError,'reversed'):
            self.fixture('invalid','NAME invalid\nROWS\n N OBJ\n E r\nCOLUMNS\n    x r 1\nBOUNDS\n LO b x 2\n UP b x 1\nENDATA\n')

    def test_noncontiguous_duplicate_fail(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            self.fixture('duplicate','NAME invalid\nROWS\n N OBJ\n E r\nCOLUMNS\n    x r 1\n    y r 2\n    x r 3\nENDATA\n')

    def test_unknown_bound_variable_fail(self):
        with self.assertRaisesRegex(ValueError,'absent'):
            self.fixture('unknown','NAME invalid\nROWS\n N OBJ\n E r\nCOLUMNS\n    x r 1\nBOUNDS\n UP b z 1\nENDATA\n')


if __name__=='__main__':unittest.main(verbosity=2)
