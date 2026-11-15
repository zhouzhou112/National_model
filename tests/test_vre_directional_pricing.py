"""Bidirectional fixed-site bounds include paired spur costs and reuse kink."""
from pathlib import Path
import hashlib,json,tempfile,unittest
import numpy as np
from cispo_model.vre_pricing import parse_vre_mps,directional_site_prices,directional_certificate

class DirectionalPricingTest(unittest.TestCase):
    def test_legacy_output_is_byte_identical_to_3e139ea6(self):
        from test_vre_pricing import MPS
        from cispo_model.vre_pricing import site_prices,certificate,write_csv
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'m.mps').write_text(MPS);np.save(p/'pi.npy',[17.,-7.])
            cols,stats=parse_vre_mps(p/'m.mps',p/'pi.npy')
            prices=site_prices(cols,[dict(grid_uid='G1',technology='pv',capacity_floor_gw=0,capacity_upper_gw=4,new_capacity_gw=0)])
            c,f=certificate(prices,[dict(grid_uid='G1',technology='pv',original_new_ub_gw=4,screened_out=True,rc_ratio=.5)],1000)
            write_csv(p/'out.csv',prices,list(prices[0]))
            raw=json.dumps(dict(columns=cols,stats=stats,prices=prices,certificate=c,flips=f),indent=2).encode()+b'\n'+(p/'out.csv').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),'333c13d90869173572771534ad3b8f5ec2b4abf8b05ef65ecf066be128c9e8de')

    def columns(self,*,lo=1,up=3,state='upper',stock=.4,other_value=0):
        # Pair objective=5, spur cost=4, maxCF=.5. The spur-row dual is
        # deliberately 20: independent spur relaxation would be unbounded.
        x=lo if state=='lower' else up;s=max(0,.5*x-stock)
        cap=dict(obj=2,rc=2-17+10-other_value,lb=x,ub=x,nnz=3,
                 spur_links=[dict(row='spur_capacity_non_dpv[0]',coefficient=-.5,sense='G',pi=20.,rhs=-stock)])
        new=dict(obj=3,rc=3+17,lb=x-lo,ub=x-lo,nnz=1)
        spur=dict(obj=4,rc=-16,lb=s,ub=s,nnz=1,
                  spur_links=[dict(row='spur_capacity_non_dpv[0]',coefficient=1.,sense='G',pi=20.,rhs=-stock)])
        cols={'vre_capacity_gw[0]':cap,'vre_new_gw[0]':new,'spur_augmentation_gw[0]':spur}
        rows=[dict(grid_uid='G1',technology='onwind',province_code='13',capacity_floor_gw=lo,capacity_upper_gw=up)]
        selection=[dict(grid_uid='G1',technology='onwind',state=state)]
        return cols,rows,selection

    def test_upper_removal_direction_matches_full_pair_cost(self):
        p=directional_site_prices(*self.columns(),require_fixed=True)
        self.assertAlmostEqual(p[0]['decrease_rc'],-7)
        self.assertAlmostEqual(directional_certificate(p,1000)['B_million_cny'],14)

    def test_lower_increase_direction_with_capacity_value(self):
        p=directional_site_prices(*self.columns(state='lower',other_value=10),require_fixed=True)
        self.assertAlmostEqual(p[0]['increase_rc'],-3)
        self.assertAlmostEqual(directional_certificate(p,1000)['B_million_cny'],6)

    def test_spur_reuse_kink_is_checked_not_only_endpoints(self):
        for state in ['lower','upper']:
            p=directional_site_prices(*self.columns(lo=0,up=4,state=state,stock=1,other_value=6),require_fixed=True)
            self.assertAlmostEqual(p[0]['best_relaxed_capacity_gw'],2)
            self.assertAlmostEqual(directional_certificate(p,1000)['B_million_cny'],2)

    def test_reference_scores_cannot_become_certificate(self):
        p=directional_site_prices(*self.columns(),require_fixed=False)
        with self.assertRaises(ValueError):directional_certificate(p,1000)

    def test_zero_design_CF_has_no_capacity_term_in_spur_row(self):
        c,r,s=self.columns(lo=0,up=.05,state='lower',stock=0)
        c['vre_capacity_gw[0]'].update(rc=2-17,spur_links=[])
        c['spur_augmentation_gw[0]'].update(lb=0.,ub=0.)
        prices=directional_site_prices(c,r,s,require_fixed=True)
        self.assertEqual(prices[0]['max_cf'],0.)
        self.assertEqual(prices[0]['increase_rc'],5.)
        self.assertEqual(directional_certificate(prices,1000)['B_million_cny'],0.)

    def test_extra_spur_rows_or_wrong_fixed_bounds_rejected(self):
        c,r,s=self.columns();c['spur_augmentation_gw[0]']['nnz']=2
        with self.assertRaises(ValueError):directional_site_prices(c,r,s,require_fixed=True)
        c,r,s=self.columns();c['vre_new_gw[0]']['ub']+=1
        with self.assertRaises(ValueError):directional_site_prices(c,r,s,require_fixed=True)

    def test_optional_parser_retains_spur_rhs_and_legacy_columns(self):
        mps='''NAME example
ROWS
 N OBJ
 E vre_capacity_accounting[0]
 G spur_capacity_non_dpv[0]
COLUMNS
 vre_capacity_gw[0] OBJ 2 vre_capacity_accounting[0] 1
 vre_capacity_gw[0] spur_capacity_non_dpv[0] -0.5
 vre_new_gw[0] OBJ 3 vre_capacity_accounting[0] -1
 spur_augmentation_gw[0] OBJ 4 spur_capacity_non_dpv[0] 1
RHS
 rhs vre_capacity_accounting[0] 1 spur_capacity_non_dpv[0] -0.4
BOUNDS
 FX bounds vre_capacity_gw[0] 3
 FX bounds vre_new_gw[0] 2
 FX bounds spur_augmentation_gw[0] 1.1
ENDATA
'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'model.mps';pi=Path(tmp)/'pi.npy';path.write_text(mps);np.save(pi,[17.,20.])
            old,stats=parse_vre_mps(path,pi);new,extended=parse_vre_mps(path,pi,include_spur=True)
            self.assertEqual(set(old),{'vre_capacity_gw[0]','vre_new_gw[0]'})
            self.assertEqual(stats,extended)
            for k in old:
                self.assertEqual(old[k],{n:v for n,v in new[k].items() if n!='spur_links'})
            _,rows,selection=self.columns()
            self.assertAlmostEqual(directional_site_prices(new,rows,selection,require_fixed=True)[0]['improvement_bound_million_cny'],14)

if __name__=='__main__':unittest.main()
