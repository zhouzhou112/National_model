"""C2050 T550-only assess|price after verified complete backup.

Usage from repository root: python <this-file> C2050 assess|price
Full pricing evidence stays on T550; only existing small receipts/assessment
JSON return locally. No collection, solving, state promotion, or scheduling.
"""
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
RELEASES = {'C2050': '20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2'}

if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != 'C2050' or sys.argv[2] not in ('assess', 'price'):
        raise SystemExit(__doc__)
    spec = importlib.util.spec_from_file_location(
        'completed_postprocess', HERE.parent / 'completed_results_20261027/postprocess.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = HERE
    module.RELEASES = RELEASES
    module.main()
