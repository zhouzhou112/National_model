"""Author pathway: enrollment-scaled accreditation and objective accounting."""
import copy
import json
import unittest
from pathlib import Path
import gurobipy as gp
import numpy as np
from cispo_model.config import load_model_config
from cispo_model.flexible_load import attach_flexible_load
from cispo_model.flexible_credit import audit_optional_credit
from cispo_model.solution_export import _value
from test_flexible_portfolio import fixture


class OptionalCreditTests(unittest.TestCase):
    def build(self, share=1.0, directional=True):
        config = load_model_config(scenario_path='config/scenarios/case3_thermal_ev_v5.json')
        data = fixture()
        data.flexible_load_v4.ev_mobility['driving_energy_withdrawal_gwh'] *= .20/.15
        if directional:
            for c in ('heating', 'cooling'):
                data.flexible_load_v4.service_costs[c].update(
                    activation_cost_release_yuan_per_mwh=np.full(2, 40.),
                    activation_cost_precondition_yuan_per_mwh=np.zeros(2))
        model = gp.Model('author_credit_test'); model.Params.OutputFlag=0; model.Params.Threads=2
        self.addCleanup(model.dispose)
        block = attach_flexible_load(model, config, data, hours=24)
        model.addConstr(block.variables['ev_enrolled_service_fraction'] == share)
        model.addConstr(block.variables['ev_bidirectional_service_fraction'] == .5*share)
        model.addConstr(block.variables['flexible_service_capacity'][:, :2] == .25*share)
        return config, data, model, block

    def test_credit_scales_with_enrollment_and_zero_recovers_base(self):
        credits=[]
        for share in (0., .25, .5, 1.):
            c,d,m,b=self.build(share)
            m.setObjective(-100*b.variables['firm_flexible_capacity_credit'].sum()+gp.quicksum(b.costs.values()));m.optimize()
            self.assertEqual(m.Status, gp.GRB.OPTIMAL)
            v={k:_value(x) for k,x in b.variables.items()}
            credit=v['firm_flexible_capacity_credit'];credits.append(credit)
            qc=audit_optional_credit(c.raw['flexible_load'],d,v['flexible_service_capacity'],
                v['ev_enrolled_service_fraction'],v['ev_bidirectional_service_fraction'],credit)
            self.assertLessEqual(max(qc.values()),1e-8)
            if share==0:
                np.testing.assert_allclose(_value(b.effective_load_gw),d.load_gw,atol=1e-9)
                np.testing.assert_array_equal(credit,np.zeros_like(credit))
                self.assertAlmostEqual(sum(float(_value(x)) for x in b.costs.values()),0)
        np.testing.assert_allclose(credits[1],credits[-1]*.25,atol=1e-8)
        np.testing.assert_allclose(credits[2],credits[-1]*.5,atol=1e-8)

    def test_authorization_required(self):
        c=load_model_config(scenario_path='config/scenarios/case3_thermal_ev_v5.json')
        del c.raw['flexible_load']['firm_capacity_credit']['optional_portfolio_authorization']
        with self.assertRaisesRegex(ValueError,'separately qualified'):c.validate()

    def test_zero_enrollment_upper_bounds_build_and_solve(self):
        c=load_model_config(scenario_path='config/scenarios/case3_thermal_ev_v5.json')
        c.raw['flexible_load']['response_contract']={
            'version':'proportional_enrollment_response_v1',
            'maximum_enrollment_fraction':{s:0 for s in ('heating','cooling','ev_v1g','ev_v2g')},
            'v2g_infrastructure_fraction':0, 'cost_multipliers':{}}
        c.validate();d=fixture();d.flexible_load_v4.ev_mobility['driving_energy_withdrawal_gwh'] *= .20/.15
        m=gp.Model();m.Params.OutputFlag=0;m.Params.Threads=2;self.addCleanup(m.dispose)
        b=attach_flexible_load(m,c,d,hours=24);m.setObjective(gp.quicksum(b.costs.values()));m.optimize()
        self.assertEqual(m.Status,gp.GRB.OPTIMAL)
        np.testing.assert_allclose(_value(b.effective_load_gw),d.load_gw,atol=1e-9)
        np.testing.assert_array_equal(_value(b.variables['firm_flexible_capacity_credit']),np.zeros((2,4)))

    def test_year_view_preserves_full_pathway(self):
        c=load_model_config(scenario_path='config/scenarios/case3_thermal_ev_v5.json')
        for y,factor in ((2030,.2),(2040,.3),(2050,.4),(2060,.5)):
            c=c.for_planning_year(y)
            self.assertEqual(c.raw['flexible_load']['ev_v1g']['shiftable_energy_fraction'],factor)
        self.assertEqual(c.raw['flexible_load']['firm_capacity_credit']['derating_fraction']['heating'],.45)

    def test_directional_details_not_double_counted_and_missing_columns_fallback(self):
        for directional in (False,True):
            c,d,m,b=self.build(1,directional)
            m.addConstr(b.variables['heating_shift_down'][:,12]>=.01)
            m.setObjective(gp.quicksum(b.costs.values()));m.optimize()
            self.assertEqual(m.Status,gp.GRB.OPTIMAL)
            activation=float(_value(b.costs['flexible_load_v5_thermal_activation']))
            if directional:
                self.assertAlmostEqual(activation,sum(float(_value(v)) for v in b.cost_details.values()))
                self.assertEqual(float(_value(b.cost_details['flexible_load_v5_thermal_precondition'])),0)
            else:
                self.assertTrue(b.structural_audit['legacy_bidirectional_activation'])
                expected=sum((_value(b.variables[c+'_shift_up'])+_value(b.variables[c+'_shift_down'])).sum()*.001 for c in ('heating','cooling'))
                self.assertAlmostEqual(activation,expected)

    def test_zero_contract_credit_qc_rejects_false_credit(self):
        c,d,m,b=self.build(0)
        qc=audit_optional_credit(c.raw['flexible_load'],d,np.zeros((2,4)),np.zeros(2),np.zeros(2),np.ones((2,4)))
        self.assertEqual(qc['firm_credit_zero_when_unenrolled'],1.)
