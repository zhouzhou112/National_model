"""Finite year-specific OPS resource gates. No scheduler or automatic submission."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('year',type=int,choices=[2030]);ap.add_argument('--runtime',type=Path,required=True);a=ap.parse_args();runtime=a.runtime;config=json.loads((runtime/'installation_receipt.json').read_text());info=config['years'][str(a.year)]
 work=runtime/'gates'/str(a.year);work.mkdir(parents=True,exist_ok=False);records={};start=time.time()
 states=[('open_1h','open',1,'frozen',False),('original_B_24h','original',24,'frozen',False),('neutral_24h','neutral',24,'frozen',False),('open_24h','open',24,'frozen',False),('conservative_24h','conservative',24,'frozen',False),('zero_24h','neutral',24,'zero',False),('production_profile_1h','open',1,'frozen',True)]
 for name,resource,hours,mode,production in states:
  resource_flag='base' if resource in ['original','neutral'] else resource;env=dict(os.environ,CISPO_DATA_ROOT=info['data_roots'][resource],PYTHONPATH=str(REPO),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',CISPO_CF_ROOT='/data/zz2/National_model/data/hourly_cf',CISPO_HYDRO_ROOT='/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse',CISPO_RAW_GRFR_ROOT='/data/zz2/National_model/data/grfr_raw_2019',CISPO_WAVE_ROOT='/data/zz2/National_model/data/wave_energy_20260727')
  out=work/name;args=[sys.executable,str(HERE/'resource_gate_2030_author.py'),'--year',str(a.year),'--mode',mode,'--resource',resource_flag,'--hours',str(hours),'--source-release',info['source'],'--supplement',info['supplement'],'--output',str(out)]
  if info.get('closure'):args+=['--closure',info['closure']]
  if hours==24:args+=['--window-carbon-budget',info['budget']]
  if production:args+=['--production-profile']
  before=time.time()
  with (work/(name+'.stdout.log')).open('x') as f,(work/(name+'.stderr.log')).open('x') as g:p=subprocess.run(args,cwd=REPO,env=env,stdout=f,stderr=g)
  record=dict(command=args,returncode=p.returncode,seconds=time.time()-before)
  for filename in ['identity_gate_probe.json','parameter_verification.json','frozen_capacity_output_check.json','window_carbon_override.json']:
   if (out/filename).exists():record[filename]=json.loads((out/filename).read_text())
  if (out/'solution_qc.json').exists():record['relative_v1']=json.loads((out/'solution_qc.json').read_text())['acceptance_profiles']['relative_v1']['status']
  if (out/'preservation_report.json').exists():record['preservation']=json.loads((out/'preservation_report.json').read_text())['status']
  records[name]=record;save(work/'execution_results.json',records)
  probe=record.get('identity_gate_probe.json',{});passed=p.returncode==0 and probe.get('all_investment_families_fixed') is True
  if mode=='frozen':passed=passed and record.get('parameter_verification.json',{}).get('status')=='PASS'
  if hours==24:passed=passed and probe.get('status')==2 and record['relative_v1']=='PASS' and record['preservation']=='COMPLETE' and record['frozen_capacity_output_check.json']['status']=='PASS'
  print(json.dumps(dict(year=a.year,gate=name,status='PASS' if passed else 'STOP',seconds=record['seconds'])),flush=True)
  if not passed:
   save(work/'YEAR_GATES_STOP.json',dict(year=a.year,failed_gate=name,record=record));raise SystemExit(2)
 original=records['original_B_24h']['identity_gate_probe.json']['objective'];neutral=records['neutral_24h']['identity_gate_probe.json']['objective'];difference=abs(original-neutral)/max(1,abs(original))
 values=[records[n]['identity_gate_probe.json']['objective'] for n in ['open_24h','neutral_24h','conservative_24h','zero_24h']];violations=[max(0,values[i]-values[i+1])/max(1,abs(values[i]),abs(values[i+1])) for i in range(3)]
 status='PASS' if difference<=1e-7 and max(violations)<=1e-7 else 'STOP'
 report=dict(status=status,year=a.year,neutrality_relative_objective_difference=difference,reference_definition='Same Base-frozen case and author Base-window carbon budget; original production data bytes versus copied CISPO_DATA_ROOT',monotonicity_order=['open','central','conservative','zero'],objectives_million_cny=values,relative_order_violations=violations,comparison_relative_tolerance=1e-7,rule='Author Cross2/1e-8 objective comparison',source_identity=info,all_individual_gates_pass=True,production_threads=44,seconds=time.time()-start,records=records)
 save(work/('YEAR_GATES_PASSED.json' if status=='PASS' else 'YEAR_GATES_STOP.json'),report);print(json.dumps({k:v for k,v in report.items() if k not in ['records','source_identity']}),flush=True)
 if status!='PASS':raise SystemExit(2)
if __name__=='__main__':main()
