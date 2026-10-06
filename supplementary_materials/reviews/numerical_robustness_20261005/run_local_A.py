from pathlib import Path
import os, subprocess,sys
root=Path.cwd();review=root/'supplementary_materials/reviews/numerical_robustness_20261005'
env=os.environ.copy();env['PYTHONPATH']=str(root/'output/portfolio_runtime_gurobi13');env['CISPO_DATA_ROOT']=str(root/'data');env['CISPO_WAVE_ROOT']=str(root.parent/'wave_energy')
commands=[('explicit_off24',['--variant','explicit_off','--hours','24','--strict-equivalence']),('A2040_off1',['--variant','off','--year','2040','--hours','1','--build-only']),('A2040_on1',['--variant','A','--year','2040','--hours','1','--build-only']),('A2040_off24',['--variant','off','--year','2040','--hours','24','--strict-equivalence']),('A2040_on24',['--variant','A','--year','2040','--hours','24','--strict-equivalence'])]
for name,args in commands:
 if '--year' in args:args+=['--state-in',str(review/'upstream_2030_bound_closed/planning_state_candidate')]
 with (review/(name+'.console.log')).open('w',encoding='utf-8') as f:
  p=subprocess.run([sys.executable,str(review/'run_probe.py'),*args,'--output',str(review/name)],env=env,stdout=f,stderr=subprocess.STDOUT)
 if p.returncode:raise SystemExit(f'{name}: {p.returncode}')
