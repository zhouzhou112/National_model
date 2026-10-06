"""Runtime and case boundaries of the authorized repaired 8760h launch."""
import copy
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gurobipy as gp

from cispo_model.config import load_model_config
from cispo_model.diagnostics import configure_gurobi, validate_unlimited_stage_a_parameters
from scripts.run_cispo_2030_full_year import (
    NUMERIC_REPAIRED_STAGE_A_PROFILE_ID,
    cloud_full_year_profile_role,
    cloud_full_year_required_memory_gib,
    require_canonical_direct_nonbasic_profiles,
    require_direct_nonbasic_runtime_row_scaling,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'config/solver_profiles' / (NUMERIC_REPAIRED_STAGE_A_PROFILE_ID + '.json')


def configuration():
    return load_model_config('config/optimization_numeric_dac_by_year_v9.json', solver_path=PROFILE)


def annual_row_fixture(model, cfg):
    """Two actual Gurobi annual rows, including their physical-unit registry."""
    from cispo_model.annual_capacity_link_scaling import (
        row_scaling_metadata, select_annual_capacity_link_row_scale, ordered_name_sha256,
    )
    scales = {family: select_annual_capacity_link_row_scale(cfg, family, [1.0, 6000.0])
              for family in ('vre', 'ror')}
    registry = row_scaling_metadata(cfg, scales)
    for family, scale in scales.items():
        energy = model.addVar(name=f'load_center_{family}_generation_gwh[0]')
        capacity = model.addVar(name=f'{family}_capacity_gw[0]')
        name = f'load_center_{family}_availability_0'
        model.addConstr(scale.factor * energy <= 6000 * scale.factor * capacity, name=name)
        registry['families'][family].update(constraint_rows=1, matrix_nonzeros_scaled=2,
            constraint_names=[name], constraint_name_order_sha256=ordered_name_sha256([name]))
    model.update()
    return registry


class RepairedFormalLaunchTests(unittest.TestCase):
    def test_actual_runtime_rows_match_the_selected_contract(self):
        repaired = configuration()
        legacy = load_model_config(
            solver_path='config/solver_profiles/barrier_stagea_final_full_year_cloud_v10_threads44_no_softmem.json',
            formulation_path='config/formulation_profiles/annual_capacity_link_rows_8192_v1.json')
        for selected, wrong in ((repaired, legacy), (legacy, repaired)):
            with self.subTest(profile=selected.raw['solver_profile']['id']), gp.Model() as model:
                model.Params.OutputFlag = 0
                registry = annual_row_fixture(model, selected)
                self.assertIs(require_direct_nonbasic_runtime_row_scaling(selected, registry, model), registry)
                with self.assertRaises(RuntimeError):
                    require_direct_nonbasic_runtime_row_scaling(wrong, registry, model)

    def test_runtime_registry_cannot_be_missing_or_disagree_with_actual_coefficients(self):
        cfg = configuration()
        with gp.Model() as model:
            model.Params.OutputFlag = 0
            registry = annual_row_fixture(model, cfg)
            with self.assertRaises(ValueError):
                require_direct_nonbasic_runtime_row_scaling(cfg, None, model)
            model.chgCoeff(model.getConstrByName('load_center_vre_availability_0'),
                           model.getVarByName('load_center_vre_generation_gwh[0]'), 1/8192)
            model.update()
            with self.assertRaisesRegex(ValueError, 'anchor'):
                require_direct_nonbasic_runtime_row_scaling(cfg, registry, model)

    def test_real_runner_reaches_archive_after_runtime_guard_with_small_lp_fixture(self):
        # Run the real full-year entry and all postbuild guards. Only the LP
        # builder is replaced with two real annual rows; this is NOT a full-year
        # model qualification. build-only and a temporary directory prevent
        # solving or promoting a synthetic scientific result.
        from scripts import run_cispo_2030_full_year as runner
        cfg = configuration()
        cfg.raw['solver_profile']['minimum_gurobi_major_version'] = gp.gurobi.version()[0]
        with tempfile.TemporaryDirectory() as temporary, gp.Model() as model:
            model.Params.OutputFlag = 0
            registry = annual_row_fixture(model, cfg)
            art = SimpleNamespace(model=model, index={'annual_capacity_link_row_scaling': registry})
            out = Path(temporary)/'output'
            args = ['runner', '--config', str(cfg.path), '--solver-config', str(PROFILE),
                    '--horizon', 'full_year', '--build-only', '--archive-original-model',
                    '--output-dir', str(out)]
            with patch('sys.argv', args), patch.object(runner, 'load_model_config', return_value=cfg), \
                 patch.object(runner, 'cloud_full_year_required_memory_gib', return_value=0), \
                 patch('cispo_model.monolithic.build_full_year_monolithic', return_value=art), \
                 redirect_stdout(StringIO()):
                runner.main()
            self.assertEqual(json.loads((out/'model_archive/archive_manifest.json').read_text())['status'], 'COMPLETE')
            self.assertEqual(json.loads((out/'solver_parameters_before_optimize.json').read_text())['Threads'], 48)
            self.assertFalse((out/'solve_report.json').exists())
            self.assertFalse((out/'planning_state').exists())

    def test_reviewed_repair_is_allowed_without_old_row_scaling(self):
        cfg = configuration()
        require_canonical_direct_nonbasic_profiles(cfg)
        self.assertEqual(cloud_full_year_profile_role(NUMERIC_REPAIRED_STAGE_A_PROFILE_ID), 'STAGE_A')
        self.assertEqual(cloud_full_year_required_memory_gib(96, 'STAGE_A', NUMERIC_REPAIRED_STAGE_A_PROFILE_ID), 500)
        self.assertFalse(cfg.raw['features']['dac'])
        self.assertIsNone(cfg.formulation_path)

    def test_scientific_drift_and_old_8192_formulation_are_rejected(self):
        cfg = configuration()
        for change in ('dac', 'scaling', 'year'):
            edited = copy.deepcopy(cfg)
            if change == 'dac':
                edited.raw['features']['dac'] = True
            elif change == 'scaling':
                edited.raw['formulation']['annual_capacity_link_row_scaling'] = 'binary_power2_safe_8192_v1'
            else:
                edited = edited.for_planning_year(2040)
            with self.subTest(change=change), self.assertRaises(SystemExit):
                require_canonical_direct_nonbasic_profiles(edited)

    def test_tampered_solver_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'changed.json'
            raw = json.loads(PROFILE.read_text())
            raw['numerics']['time_limit_seconds'] = 900
            path.write_text(json.dumps(raw))
            cfg = load_model_config('config/optimization_numeric_dac_by_year_v9.json', solver_path=path)
            with self.assertRaises(SystemExit):
                require_canonical_direct_nonbasic_profiles(cfg)

    def test_actual_gurobi_clears_inherited_limits_and_preserves_finite_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary, gp.Env(empty=True) as env:
            env.setParam('OutputFlag', 0)
            env.start()
            with gp.Model(env=env) as model:
                cfg = configuration()
                # Local API check may use Gurobi 12; the immutable production
                # profile still requires 13, checked again on the compute node.
                cfg.raw['solver_profile']['minimum_gurobi_major_version'] = gp.gurobi.version()[0]
                model.Params.TimeLimit = 900
                model.Params.SoftMemLimit = 8
                configure_gurobi(model, cfg, Path(temporary) / 'unlimited.log')
                actual = validate_unlimited_stage_a_parameters(model, cfg)
                self.assertEqual(actual['Threads'], 48)
                self.assertEqual(actual['BarConvTol'], 1e-4)
                self.assertEqual(actual['Crossover'], 0)
                self.assertEqual(actual['BarIterLimit'], 2000000000)
                self.assertIsNone(actual['TimeLimit'])
                model.Params.WorkLimit = 1
                with self.assertRaises(RuntimeError):
                    validate_unlimited_stage_a_parameters(model, cfg)
                local = load_model_config('config/optimization_numeric_dac_by_year_v9.json')
                configure_gurobi(model, local, Path(temporary) / 'diagnostic.log')
                self.assertEqual(model.Params.TimeLimit, 900)
                self.assertEqual(model.Params.SoftMemLimit, 8)


if __name__ == '__main__':
    unittest.main()
