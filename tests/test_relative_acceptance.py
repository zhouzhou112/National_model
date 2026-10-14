import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cispo_model.relative_acceptance import add_relative_profile, assess_relative_v1, DEFERRED

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    return dict(status='HARD_FAIL',optimization_hours=8760,
        maximum_power_balance_residual_gw=.001,
        objective_value_million_cny=1e6,objective_component_residual_million_cny=1e-7*1e6,
        maximum_reservoir_transition_residual_m3=100,
        interprovincial_directionality_assessment={'observed':{'excess_loss_share_of_system_load':1e-4}},
        hard_checks={'power_balance':False,'objective_components':False,
                     'unidirectional_interprovincial_flow':False,'reservoir_transition':False,'carbon':True},
        solver_contract={'barrier_status_code':2,'barrier_primal_dual_metrics':{
            'primal_infeasibility':.01,'relative_primal_dual_objective_gap':.01}})


class RelativeAcceptanceTests(unittest.TestCase):
    def test_extended_gw_gwh_boundary_and_untouched_units(self):
        q=fixture()
        q['hard_checks'].update(storage_transition=False, up_reserve=False, inertia=False)
        q['maximum_storage_transition_residual_gwh']=.001
        q['minimum_up_reserve_margin_gw']=-.001
        q['minimum_inertia_margin_gw_s']=-.0001
        before=copy.deepcopy(q)
        result=assess_relative_v1(q)
        self.assertTrue(result['checks']['extended_gw_gwh_physical_checks']['passed'])
        self.assertEqual(result['status'],'HARD_FAIL')
        self.assertEqual(q,before)
        q['hard_checks']['inertia']=True
        self.assertEqual(assess_relative_v1(q)['status'],'PASS')
        q['maximum_storage_transition_residual_gwh']=math.nextafter(.001,math.inf)
        self.assertEqual(assess_relative_v1(q)['status'],'HARD_FAIL')
        q['maximum_storage_transition_residual_gwh']=float('nan')
        self.assertEqual(add_relative_profile(q)['status'],'ERROR')

    def test_v5_all_stock_bounds_and_credit_reassessed(self):
        q=fixture();q['flexible_load_formulation']='integrated_service_constrained_v5'
        q['hard_checks'].update(heating_service_accounting=False,
            v5_firm_capacity_credit_physical_bound=False,ev_v1g_daily_energy_conservation=True)
        for suffix in ('state_transition_residual','periodic_boundary_residual',
                       'positive_state_bound_violation','negative_state_bound_violation',
                       'comfort_debt_violation'):
            q['maximum_v4_heating_'+suffix+'_gwh']=.0009
        q['maximum_v5_firm_capacity_credit_bound_violation_gw']=.001
        # This unused daily-energy diagnostic must not reject V5.
        q['maximum_ev_v1g_daily_energy_residual_gwh']=100
        self.assertEqual(assess_relative_v1(q)['status'],'PASS')
        q['maximum_v4_heating_negative_state_bound_violation_gwh']=.0011
        self.assertEqual(assess_relative_v1(q)['status'],'HARD_FAIL')
        del q['maximum_v4_heating_negative_state_bound_violation_gwh']
        self.assertEqual(add_relative_profile(q)['status'],'ERROR')

    def test_optional_dimensionless_limits_stay_strict(self):
        q=fixture();q['hard_checks']['optional_portfolio_physical_contract']=False
        q['optional_portfolio_qc']={'inventory_violation_gwh':.0008,
                                    'enrollment_fraction_violation':.0001}
        self.assertEqual(assess_relative_v1(q)['status'],'HARD_FAIL')
        q['optional_portfolio_qc']['enrollment_fraction_violation']=0
        self.assertEqual(assess_relative_v1(q)['status'],'PASS')

    def test_missing_formulation_cannot_promote_service_check(self):
        q=fixture();q['hard_checks']['v4_ev_mobility_service']=False
        self.assertEqual(add_relative_profile(q)['status'],'ERROR')

    def test_recorded_barrier_tolerance(self):
        result=assess_relative_v1(fixture(),{'solver_parameters':{'barrier_convergence_tolerance':1e-4}})
        self.assertEqual(result['dual']['BarConvTol'],1e-4)

    def test_2060_configuration_authorized_differences_only(self):
        from cispo_model.config import load_model_config
        folder=ROOT/'config'
        base=json.loads((folder/'optimization_numeric_dac_by_year_v9.json').read_text())
        new=json.loads((folder/'optimization_numeric_dac_by_year_v9_a12.json').read_text())
        expected=copy.deepcopy(base)
        expected['numerics'].update(hydro_capacity_headroom_zero_gw=1e-5,
            retrofit_upper_zero_gw=1e-5,inherited_floor_overrun_clip_gw=0,
            other_capacity_headroom_zero_gw_gwh=1e-5,capacity_cancellation_rhs_zero=1e-12)
        self.assertEqual(new,expected)
        profiles=folder/'solver_profiles'
        old=json.loads((profiles/'barrier_checkpoint_full_year_cloud_2050_numeric_v1_threads48.json').read_text())
        current=json.loads((profiles/'barrier_checkpoint_full_year_cloud_2060_numeric_v1_threads48.json').read_text())
        for key in ['profile_id','description']:old.pop(key);current.pop(key)
        self.assertEqual(old,current)
        cfg=load_model_config(folder/'optimization_numeric_dac_by_year_v9_a12.json',solver_path=profiles/'barrier_checkpoint_full_year_cloud_2060_numeric_v1_threads48.json').for_planning_year(2060)
        cfg.validate()
        self.assertEqual(cfg.boundary_year,2050)

    def test_legacy_fields_byte_serialization_unchanged(self):
        qc=fixture(); before=json.dumps(qc).encode()
        add_relative_profile(qc)
        self.assertEqual(qc['acceptance_profiles']['relative_v1']['status'],'PASS')
        qc.pop('acceptance_profiles')
        self.assertEqual(before,json.dumps(qc).encode())

    def test_cost_and_loss_threshold_inclusive(self):
        q=fixture()
        self.assertEqual(assess_relative_v1(q)['status'],'PASS')
        q['objective_component_residual_million_cny']=math.nextafter(1e-7*1e6,math.inf)
        self.assertFalse(assess_relative_v1(q)['checks']['objective_components']['passed'])
        q=fixture()
        q['interprovincial_directionality_assessment']['observed']['excess_loss_share_of_system_load']=math.nextafter(1e-4,math.inf)
        self.assertFalse(assess_relative_v1(q)['checks']['unidirectional_interprovincial_flow']['passed'])

    def test_power_province_boundary_and_mismatch(self):
        q=fixture(); q['maximum_power_balance_residual_gw']=.002
        inputs={'power_by_province':[dict(province_code=11,annual_peak_load_gw=2000,maximum_residual_gw=.002)]}
        self.assertTrue(assess_relative_v1(q,inputs=inputs)['checks']['power_balance']['passed'])
        value=math.nextafter(.002,math.inf)
        inputs['power_by_province'][0]['maximum_residual_gw']=value
        q['maximum_power_balance_residual_gw']=value
        self.assertFalse(assess_relative_v1(q,inputs=inputs)['checks']['power_balance']['passed'])
        with self.assertRaises(ValueError):assess_relative_v1(q)

    def test_deferred_water_and_remaining_checks(self):
        q=fixture()
        water=assess_relative_v1(q)['checks']['reservoir_transition']
        self.assertEqual(water['status'],DEFERRED); self.assertIsNone(water['passed'])
        q['hard_checks']['carbon']=False
        self.assertEqual(assess_relative_v1(q)['status'],'HARD_FAIL')

    def test_solver_and_nonfinite_fail_closed(self):
        q=fixture()
        q['solver_contract']['barrier_primal_dual_metrics']['primal_infeasibility']=.01001
        self.assertEqual(assess_relative_v1(q)['status'],'HARD_FAIL')
        q=fixture(); q['objective_value_million_cny']=float('nan')
        self.assertEqual(add_relative_profile(q)['status'],'ERROR')

    def test_context_and_evaluator_exceptions_isolated(self):
        q=fixture(); before=copy.deepcopy(q)
        def fail(): raise RuntimeError('injected context failure')
        self.assertEqual(add_relative_profile(q,inputs_factory=fail)['status'],'ERROR')
        q.pop('acceptance_profiles'); self.assertEqual(q,before)
        with patch('cispo_model.relative_acceptance.assess_relative_v1',side_effect=RuntimeError('injected')):
            self.assertEqual(add_relative_profile(q)['status'],'ERROR')
        q.pop('acceptance_profiles'); self.assertEqual(q,before)

    def test_archived_2050_and_offline_source_immutable(self):
        src=ROOT/'supplementary_materials/reviews/base_2050_continuation_20260930/status_20261012T111059Z'
        if not src.exists(): self.skipTest('Local archived review fixture unavailable')
        q=json.loads((src/'output_8760__solution_qc.json').read_text())
        old=json.loads((src/'summary.json').read_text())['relative_v1_review']
        result=assess_relative_v1(q)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['checks']['power_balance']['maximum_residual_gw'],old['maximum_power_balance_residual_gw'])
        self.assertEqual(result['checks']['objective_components']['relative_residual'],old['objective_closure_relative'])
        self.assertEqual(result['checks']['unidirectional_interprovincial_flow']['observed']['excess_loss_gwh'],old['excess_loss_gwh'])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/'source';source.mkdir()
            qcpath=source/'solution_qc.json';qcpath.write_text(json.dumps(q))
            solvepath=source/'solve_report.json';solvepath.write_text(json.dumps({'status':'OPTIMAL','solution_contract':q['solver_contract']}))
            before={p.name:p.read_bytes() for p in source.iterdir()}
            p=subprocess.run([sys.executable,str(ROOT/'scripts/assess_relative_v1.py'),str(source),'--output',str(root/'solution_qc_relative_v1.json')],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(before,{p.name:p.read_bytes() for p in source.iterdir()})

    def test_profile_failure_does_not_stop_candidate_preservation(self):
        from cispo_model.config import load_model_config
        from cispo_model.solution_preservation import preserve_stage_a
        with tempfile.TemporaryDirectory() as folder:
            with patch('cispo_model.master.export_master_solution'), \
                 patch('cispo_model.solution_export.export_operational_solution',return_value=fixture()), \
                 patch('cispo_model.result_summary.export_result_summary'), \
                 patch('cispo_model.planning_state.export_solution_planning_state') as state, \
                 patch('cispo_model.relative_acceptance.add_relative_profile',side_effect=RuntimeError('profile failure')):
                preserve_stage_a(None,None,load_model_config(),folder,
                    {'status':'OPTIMAL','result_use':'TEST_ONLY_TRUNCATED_HORIZON'},snapshot=False)
            state.assert_called_once()
            qc=json.loads((Path(folder)/'solution_qc.json').read_text())
            self.assertEqual(qc['acceptance_profiles']['relative_v1']['status'],'ERROR')
            self.assertEqual(qc['hard_checks'],fixture()['hard_checks'])

if __name__=='__main__':unittest.main()
