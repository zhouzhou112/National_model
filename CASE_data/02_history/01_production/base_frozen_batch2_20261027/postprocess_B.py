"""After verified complete T550 backup: B2040|B2050|B2060 collect|assess.

Reuses the established nocredit <=32 MiB output collection and relative_v1
evaluator, including fossil-unabated annual Mt denominator. No polling.
"""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
RELEASES={
 'B2040':'20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1',
 'B2050':'20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1',
 'B2060':'20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2',
}
if __name__=='__main__':
 if any(x in sys.argv for x in ['--cloud-collect','price']):
  raise SystemExit('Use verified T550 complete backup; unscreened B needs no pricing certificate.')
 spec=importlib.util.spec_from_file_location('completed_postprocess',HERE.parent/'completed_results_20261027/postprocess.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.HERE=HERE;m.RELEASES=RELEASES;m.main()
