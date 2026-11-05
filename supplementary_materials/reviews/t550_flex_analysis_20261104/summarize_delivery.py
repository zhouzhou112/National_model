"""Small-metadata delivery audit; never accesses hourly scientific arrays."""
from pathlib import Path
import csv,hashlib,json
from finalize_cases import RET,HERE,finalize
CASES=['base2030','base2040','base2050','base2060','case3_2030','case3_2040','c2050','nocredit_2030','b2030','b2040','b2050','b2060']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[]
 for c in CASES:
  finalize(c);d=RET/c
  listed={}
  for line in (d/'sha256.txt').read_text(encoding='utf-8').splitlines():
   h,n=line.split('  ',1);assert sha(d/n)==h,n;listed[n]=h
  actual={p.relative_to(d).as_posix() for p in d.rglob('*') if p.is_file() and p.name!='sha256.txt'}
  assert set(listed)==actual,c
  s=json.loads((d/'summary.json').read_text(encoding='utf-8'));r={'case':c,**{t:s.get(t,'NOT_REQUESTED') for t in ['T1','T2','T3','T4','T6','T7','T8','T9']}}
  z=s.get('T4_checks',{});r['annual_pair_max_abs_cny_per_mwh']=z.get('pair_residual_max_abs_cny_per_mwh',s.get('T6_checks',{}).get('annual_pair_max_abs_cny_per_mwh',''))
  r['inertia_binding_share']=s['T9_checks']['binding_share'];r['service_decomposition_max_abs_gw']=s.get('T6_checks',{}).get('service_decomposition_max_abs_gw','')
  r['files']=len(actual)+1;r['total_bytes']=sum(p.stat().st_size for p in d.rglob('*') if p.is_file());r['largest_file_bytes']=max(p.stat().st_size for p in d.rglob('*') if p.is_file());r['sha256_manifest']=sha(d/'sha256.txt');rows.append(r)
 with (HERE/'delivery_summary.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 out=dict(status='PASS',cases=rows,total_files=sum(r['files'] for r in rows),total_bytes=sum(r['total_bytes'] for r in rows),largest_file_bytes=max(r['largest_file_bytes'] for r in rows),largest_case_bytes=max(r['total_bytes'] for r in rows),hourly_array_mps_barpi_returned=False,sha256_coverage='Every delivered file except sha256.txt itself; includes current summary/transfer receipts')
 (HERE/'delivery_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='cases'}))
if __name__=='__main__':main()
