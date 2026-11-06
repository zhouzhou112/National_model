"""Reuse audited finite T550 workflows for this immutable completed case.
Usage: python execute_evidence.py row|price|assess|collect. No solver or scheduler.
"""
import sys, pathlib, importlib.util
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RELEASE='20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
if __name__=='__main__':
 action=sys.argv[1]
 if action=='row':
  source=HERE.parent/'C2050_completed_20261029/run_row_audit.py'
  text=source.read_text().replace("side=base/'acceptance_20261029'", "side=base/'acceptance_20261106'")
  ns={'__file__':str(HERE/'execute_evidence.py'),'__name__':'row_reuse'}
  exec(compile(text,str(source),'exec'),ns);ns['RELEASE']=RELEASE;ns['main']()
 elif action in ('price','assess','collect'):
  source=HERE.parent/'completed_results_20261027/postprocess.py'
  text=source.read_text().replace('postprocess_tools_20261027_collection','postprocess_tools_20261106_case3_2050_collection').replace('postprocess_tools_20261027_mt','postprocess_tools_20261106_case3_2050').replace("'postprocess_20261027_mt'","'postprocess_20261106'")
  ns={'__file__':str(HERE/'execute_evidence.py'),'__name__':'postprocess_reuse'}
  exec(compile(text,str(source),'exec'),ns);ns['RELEASES']={'case3_2050':RELEASE};sys.argv=[sys.argv[0],'case3_2050',action];ns['main']()
 else: raise SystemExit('row|price|assess|collect required')
