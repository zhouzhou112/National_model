"""Physical invariants for bounded cleanup; no national optimization."""
import unittest
import copy
from types import SimpleNamespace
import numpy as np
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3, clean_cascade_transfer_fractions
from cispo_model.monolithic import _reservoir_release_upper_scaled
from cispo_model.config import ModelConfig, load_model_config
from cispo_model.run_contract import analysis_case_identity


def fixture(local, storage, *, cascade=False):
    return SimpleNamespace(reservoir_local_inflow_m3s=np.asarray(local,float),
        reservoir_active_storage_m3=np.asarray(storage,float),
        cascade_station_local_rows=np.array([0,1] if cascade else [],int),
        cascade_edge_source_local_rows=[np.array([0])] if cascade else [],
        cascade_edge_target_local_rows=[np.array([1])] if cascade else [],
        cascade_edge_target_weights=[np.array([1.0])] if cascade else [],
        cascade_edge_transfer_fraction=[np.array([0.5,0.8])] if cascade else [])


class CyclicStorageTests(unittest.TestCase):
    def test_transfer_cleanup_is_monotone_and_records_every_discarded_hour(self):
        source=[np.array([0.,2e-5,1e-4,0.5,1.])]
        cleaned,audit=clean_cascade_transfer_fractions(source,1e-4)
        np.testing.assert_array_equal(cleaned[0],[0.,0.,1e-4,.5,1.])
        self.assertEqual(source[0][1],2e-5)
        self.assertEqual(audit['removed_edge_hours'],1)
        self.assertEqual(audit['edges'][0]['hour_indices'],[1])
        old,_=clean_cascade_transfer_fractions(source,0.)
        np.testing.assert_array_equal(old[0],source[0])

    def test_transfer_cleanup_rejects_invalid_data_or_cutoffs(self):
        for threshold in [-1,np.nan,1.]:
            with self.assertRaises(ValueError):clean_cascade_transfer_fractions([np.ones(2)],threshold)
        for value in [np.inf,np.nan,-1,1.1]:
            with self.assertRaises(ValueError):clean_cascade_transfer_fractions([np.array([value])],1e-4)

    def test_floor_cleanup_changes_scientific_identity(self):
        cfg=load_model_config()
        raw=copy.deepcopy(cfg.raw)
        raw['numerics']['capacity_floor_zero_gw']=1e-5
        candidate=ModelConfig(cfg.path,raw)
        self.assertNotEqual(
            analysis_case_identity(cfg)['resolved_scientific_configuration_sha256'],
            analysis_case_identity(candidate)['resolved_scientific_configuration_sha256'])

    def test_stronger_screening_still_rejects_unbounded_cutoffs(self):
        cfg=load_model_config()
        for key,invalid in [('capacity_floor_zero_gw',-1),('capacity_floor_zero_gw',np.nan),
                            ('capacity_headroom_zero_gw',1e-3),('coefficient_zero_tolerance',0.02)]:
            raw=copy.deepcopy(cfg.raw);raw['numerics'][key]=invalid
            with self.assertRaises(ValueError): ModelConfig(cfg.path,raw).validate()

    def test_headroom_cleanup_changes_scientific_identity(self):
        cfg=load_model_config()
        raw=copy.deepcopy(cfg.raw)
        raw['numerics']['capacity_headroom_zero_gw']=1e-8
        candidate=ModelConfig(cfg.path,raw)
        self.assertNotEqual(
            analysis_case_identity(cfg)['resolved_scientific_configuration_sha256'],
            analysis_case_identity(candidate)['resolved_scientific_configuration_sha256'])

    def test_zero_storage_dry_hours_do_not_receive_artificial_release_padding(self):
        h=fixture([[0,1]],[0]);h.cascade_edge_lag_h=[]
        upper=_reservoir_release_upper_scaled(h,flow_scale_m3s=1000,
                                             preserve_exact_hourly_zeros=True)
        self.assertEqual(upper[0,0],0)
        self.assertGreater(upper[0,1],0)

    def test_cascade_zero_hour_keeps_upstream_certificate(self):
        h=fixture([[0,1],[0,0]],[0,0],cascade=True)
        h.cascade_edge_lag_h=[0]
        upper=_reservoir_release_upper_scaled(h,flow_scale_m3s=1000,
                                             preserve_exact_hourly_zeros=True)
        np.testing.assert_array_equal(upper[:,0],0)
        self.assertTrue((upper[:,1]>0).all())

    def test_constant_inventory_offset_can_be_removed_without_altering_releases(self):
        rng=np.random.default_rng(17)
        for _ in range(40):
            incoming=rng.uniform(0,10,24)
            releases=np.full(24,incoming.mean())
            trajectory=np.cumsum((incoming-releases)*3600)
            trajectory-=trajectory.min()
            volume=trajectory+1e9
            cap=cyclic_inventory_upper_m3(fixture([incoming],[2e9]))[0]
            reduced=volume-volume.min()
            self.assertLessEqual(reduced.max(),cap)
            np.testing.assert_allclose(reduced-np.roll(reduced,1),
                                       (incoming-releases)*3600,atol=3e-7,rtol=0)

    def test_downstream_zero_local_flow_keeps_upstream_water_budget(self):
        h=fixture([[2,3],[0,0]],[1e9,1e9],cascade=True)
        cap=cyclic_inventory_upper_m3(h)
        self.assertAlmostEqual(cap[0],5*3600,places=6)
        self.assertAlmostEqual(cap[1],5*3600*0.8,places=6)

    def test_physical_small_storage_is_retained(self):
        cap=cyclic_inventory_upper_m3(fixture([[100,100]],[10]))
        np.testing.assert_array_equal(cap,[10])

    def test_dry_reservoir_has_zero_necessary_inventory(self):
        np.testing.assert_array_equal(cyclic_inventory_upper_m3(fixture([[0,0]],[1e9])),[0])

    def test_invalid_water_rejected(self):
        for v in [-1,np.nan,np.inf]:
            with self.assertRaises(ValueError):
                cyclic_inventory_upper_m3(fixture([[v,0]],[1e9]))


if __name__=='__main__':unittest.main()
