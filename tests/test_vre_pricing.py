import copy
import csv
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
from cispo_model.vre_pricing import parse_vre_mps,site_prices,certificate

MPS='''NAME example
ROWS
 N OBJ
 E accounting
 L availability
COLUMNS
 vre_capacity_gw[0] OBJ 2 accounting 1
 vre_capacity_gw[0] availability -1
 vre_new_gw[0] OBJ 3 accounting -1
RHS
 rhs accounting 0
BOUNDS
 UP bounds vre_capacity_gw[0] 4
 FX bounds vre_new_gw[0] 0
ENDATA
'''


class PricingTests(unittest.TestCase):
    def test_both_offline_clis_with_verified_archive_and_descriptor(self):
        mps,pi=self.fixture();root=mps.parent/'run';root.mkdir()
        (root/'model_archive').mkdir();(root/'barrier_checkpoint').mkdir()
        (root/'model_archive/original.mps').write_bytes(mps.read_bytes())
        (root/'barrier_checkpoint/dual_barpi.npy').write_bytes(pi.read_bytes())
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        (root/'model_archive/archive_manifest.json').write_text(json.dumps(dict(gurobi_fingerprint=42,
            files=[dict(path='original.mps',sha256=sha(mps))])))
        (root/'barrier_checkpoint/barrier_checkpoint_manifest.json').write_text(json.dumps(dict(
            source={'optimization_hours':24,'scenario_id':'base'},gurobi_fingerprint=42,
            vectors={'dual':dict(path='dual_barpi.npy',sha256=sha(pi))},
            descriptor={'path':'dual_barpi.npy','attribute':'BarPi'})))
        (root/'vre_capacity.csv').write_text('grid_uid,technology,capacity_floor_gw,capacity_upper_gw,new_capacity_gw\nG1,pv,0,4,0\n')
        (root/'candidate_selection.csv').write_text('grid_uid,technology,rc_ratio,original_new_ub_gw,screened_out\nG1,pv,0.5,4,True\n')
        (root/'solve_report.json').write_text(json.dumps(dict(status='OPTIMAL',objective_value_million_cny=1000)))
        (root/'model_config_snapshot.json').write_text(json.dumps({'resolved_configuration':{'numerics':{'capacity_headroom_zero_gw':1e-5}}}))
        (root/'result_manifest.json').write_text(json.dumps({'files':[
            dict(path=p.name,sha256=sha(p)) for p in root.iterdir() if p.is_file()]}))
        before={p:sha(p) for p in root.rglob('*') if p.is_file()}
        reference=root.parent/'reference.csv'
        reference.write_text('grid_uid,technology,rc_build,rc_ratio\nG1,pv,-2,-0.4\n')
        scripts=Path(__file__).resolve().parents[1]/'scripts'
        for script,extra in [('price_screened_candidates.py',[]),
                             ('build_vre_screen_list.py',['--source-release','fixture','--margin','0.2','--reference-screen',str(reference)])]:
            out=root.parent/script.removesuffix('.py')
            result=subprocess.run([sys.executable,str(scripts/script),'--run-dir',str(root),
                '--output',str(out),*extra],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(before,{p:sha(p) for p in before})
        result=json.loads((root.parent/'price_screened_candidates/screen_pricing_certificate.json').read_text())
        self.assertEqual(result['B_million_cny'],8)
        result=json.loads((root.parent/'build_vre_screen_list/screen_identity.json').read_text())
        self.assertEqual(result['excluded_sites'],0)
        self.assertTrue(result['base_archive_self_check']['passed'])

    def fixture(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        root=Path(folder.name);mps=root/'original.mps';pi=root/'dual.npy'
        mps.write_text(MPS);np.save(pi,np.array([17.,-7.]))
        return mps,pi

    def test_pair_cancels_accounting_dual_and_has_correct_sign(self):
        mps,pi=self.fixture()
        columns,stats=parse_vre_mps(mps,pi)
        cap=[dict(grid_uid='G1',technology='pv',capacity_floor_gw=0,
                  capacity_upper_gw=4,new_capacity_gw=0)]
        prices=site_prices(columns,cap)
        self.assertEqual(stats['constraint_rows'],2)
        self.assertEqual(prices[0]['rc_build'],-2)
        np.save(pi,np.array([-30.,-7.]))
        other,_=parse_vre_mps(mps,pi)
        self.assertEqual(site_prices(other,cap)[0]['rc_build'],-2)
        selection=[dict(grid_uid='G1',technology='pv',original_new_ub_gw=4,screened_out=True,rc_ratio=.5)]
        result,flips=certificate(prices,selection,1000)
        self.assertEqual(result['B_million_cny'],8)
        self.assertEqual(result['near_optimality_decision'],'ACCEPT_DISCLOSE')
        self.assertEqual(result['base_comparison_decision'],'RESOLVE_NEGATIVE_COLUMNS_ONCE')
        self.assertEqual(len(flips),1)

    def test_distinct_thresholds_and_second_solve_no_loop(self):
        prices=[dict(grid_uid='G1',technology='pv',rc_build=-1,archived_new_lb_gw=0,archived_new_ub_gw=0)]
        selection=[dict(grid_uid='G1',technology='pv',original_new_ub_gw=.1,screened_out=True,rc_ratio=.5)]
        r,_=certificate(prices,selection,1000)
        self.assertEqual(r['base_comparison_decision'],'INTERVAL_WITH_B')
        selection[0]['original_new_ub_gw']=math.nextafter(.1,math.inf)
        r,_=certificate(prices,selection,1000)
        self.assertEqual(r['base_comparison_decision'],'RESOLVE_NEGATIVE_COLUMNS_ONCE')
        selection[0]['original_new_ub_gw']=20
        r,_=certificate(prices,selection,1000,re_solve_count=1)
        self.assertEqual(r['near_optimality_decision'],'ACCEPT_SECOND_SOLVE_DISCLOSE')
        self.assertEqual(r['base_comparison_decision'],'SECOND_SOLVE_INTERVAL_DISCLOSE')

    def test_identity_and_missing_dual_fail_closed(self):
        mps,pi=self.fixture();np.save(pi,np.array([1.]))
        with self.assertRaises(ValueError):parse_vre_mps(mps,pi)
        np.save(pi,np.array([1.,float('nan')]))
        with self.assertRaises(ValueError):parse_vre_mps(mps,pi)
        np.save(pi,np.array([1.,-7.]))
        mps.write_text(MPS.replace(' L availability',' L accounting'))
        with self.assertRaises(ValueError):parse_vre_mps(mps,pi)

    def test_only_excluded_terms_and_stable_identity_join(self):
        prices=[dict(grid_uid='G1',technology='pv',rc_build=-1,archived_new_lb_gw=0,archived_new_ub_gw=0),
                dict(grid_uid='G2',technology='wind',rc_build=-100,archived_new_lb_gw=0,archived_new_ub_gw=4)]
        selection=[dict(grid_uid='G2',technology='wind',original_new_ub_gw=4,screened_out=False,rc_ratio=0),
                   dict(grid_uid='G1',technology='pv',original_new_ub_gw=2,screened_out=True,rc_ratio=.3)]
        self.assertEqual(certificate(prices,selection,1000)[0]['B_million_cny'],2)
        bad=copy.deepcopy(selection);bad[1]['grid_uid']='missing'
        with self.assertRaises(ValueError):certificate(prices,bad,1000)
        bad=copy.deepcopy(selection);bad[0]['original_new_ub_gw']=5
        with self.assertRaises(ValueError):certificate(prices,bad,1000)


if __name__=='__main__':unittest.main()
