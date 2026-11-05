"""T4 checks on T550: paired annual dual residual and unmodified price counts."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,time
import numpy as np

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 root=Path(a.root);out=Path(a.out);t=time.time()
 backup=json.loads((root/'backup_manifest.json').read_text());mf=root/'output_8760/result_manifest.json'
 assert sha(mf)==backup['source_result_manifest_sha256']
 idx={x['path']:x for x in json.loads(mf.read_text())['files']};bi={x['path']:x for x in backup['files']}
 inputs={}
 for n in ['hourly_marginal_prices.csv.gz','model_config_snapshot.json']:
  f=root/'output_8760'/n;ref=idx.get(n,bi.get('output_8760/'+n));h=sha(f);assert ref and ref['sha256']==h,n
  inputs[n]={'sha256':h,'bytes':f.stat().st_size}
 order=json.loads((out/'row_order_verification.json').read_text());assert order['status']=='PASS'
 with (out/'annual_row_duals.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 fam={}
 for r in rows:fam.setdefault(r['row_family'],{})[int(r['province_code'])]=float(r['pi_million_cny_per_gwh'])
 required=['province_annual_'+s for s in ['non_spatial_injection','effective_demand','external_sent','external_received','external_net_import']]
 for k in required:assert len(fam[k])==31,k
 prov=set(fam[required[0]]);assert all(set(fam[k])==prov for k in required)
 c=json.loads((root/'output_8760/model_config_snapshot.json').read_text())['resolved_configuration']['security']
 inertia=float(c.get('minimum_system_inertia_seconds',float(c.get('inertia_reference_seconds',3.5))*float(c.get('inertia_tolerance_fraction',1))))
 up=float(c['up_reserve_load_fraction']);down=float(c['down_reserve_load_fraction'])
 checks={p:dict(province_code=p,pair_residual_cny_per_mwh=1000*(fam[required[0]][p]+fam[required[1]][p]),hours=0,energy_negative_hours=0,energy_zero_hours=0,full_load_negative_hours=0,full_load_zero_hours=0,min_energy_price_cny_per_mwh=float('inf'),min_full_load_price_cny_per_mwh=float('inf')) for p in prov}
 seen=set()
 with gzip.open(root/'output_8760/hourly_marginal_prices.csv.gz','rt',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   p=int(r['province_code']);hour=int(r['hour_index']);assert (p,hour) not in seen;seen.add((p,hour))
   energy=1000*(float(r['power_balance_pi_million_cny_per_gwh'])+fam[required[1]][p])
   full=energy+1000*(up*float(r['up_reserve_pi_million_cny_per_gwh'])+down*float(r['down_reserve_pi_million_cny_per_gwh'])+inertia*float(r['inertia_pi_million_cny_per_gw_s']))
   assert np.isfinite([energy,full]).all()
   z=checks[p];z['hours']+=1
   for k,v in [('energy',energy),('full_load',full)]:
    z[k+'_negative_hours']+=int(v<0);z[k+'_zero_hours']+=int(abs(v)<=1e-6);z['min_'+k+'_price_cny_per_mwh']=min(z['min_'+k+'_price_cny_per_mwh'],v)
 assert seen=={(p,h) for p in prov for h in range(8760)}
 with (out/'annual_price_checks_by_province.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(next(iter(checks.values()))));w.writeheader();w.writerows(checks.values())
 result=dict(status='PASS',checks_scope='identity, exact row order, complete annual families, finite prices and complete province-hour coverage; paired residual disclosed, not thresholded without author criterion',pair_residual_max_abs_cny_per_mwh=max(abs(z['pair_residual_cny_per_mwh']) for z in checks.values()),annual_rows=len(rows),provincial_family_counts={k:sum(r['row_family']==k for r in rows) for k in required},inputs=inputs,annual_row_duals_sha256=sha(out/'annual_row_duals.csv'),coefficients=dict(up=up,down=down,inertia_seconds=inertia),formula='1000*(power_balance_pi+annual_effective_demand_pi+up*up_reserve_pi+down*down_reserve_pi+inertia_seconds*inertia_pi)',negative_price_is_failure=False,zero_price_tolerance_cny_per_mwh=1e-6,seconds=time.time()-t,counts={k:sum(z[k] for z in checks.values()) for k in ['energy_negative_hours','energy_zero_hours','full_load_negative_hours','full_load_zero_hours']})
 (out/'t4_price_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
