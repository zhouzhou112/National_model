from contextlib import ExitStack
import json, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path[:0] = [str(Path.cwd()), str(Path.cwd() / 'tests')]
import gurobipy as gp
from test_primal_dual_checkpoint import PrimalDualCheckpointTests

suite = unittest.TestSuite()
loader = unittest.defaultTestLoader
for name in ('test_final_preservation_no_solve.FinalPreservationNoSolveTests',
             'test_portfolio_no_solve.NoSolvePortfolioTests',
             'test_solver_telemetry.SolverTelemetryTests',
             'test_input_manifest_resume_identity', 'test_checkpoint_campaign_gate'):
    suite.addTests(loader.loadTestsFromName(name))
excluded = 'test_real_gurobi_accepts_memmapped_pstart_and_dstart'
for name in loader.getTestCaseNames(PrimalDualCheckpointTests):
    if name != excluded:
        suite.addTest(PrimalDualCheckpointTests(name))
with ExitStack() as stack:
    for name in ('optimize', 'optimizeAsync', 'presolve', 'feasRelax', 'feasRelaxS'):
        if hasattr(gp.Model, name):
            stack.enter_context(patch.object(gp.Model, name, side_effect=AssertionError(name + ' FORBIDDEN')))
    with open('output/portfolio_finalcheck_20260907/regression.log', 'w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
report = dict(tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
              excluded_optimizer_test=excluded, optimize_called=False, presolve_called=False,
              status='PASS' if result.wasSuccessful() else 'FAIL')
Path('output/portfolio_finalcheck_20260907/regression.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
sys.exit(0 if result.wasSuccessful() else 1)
