"""National simultaneous-window T6 aggregates; min of national sum, never sum of minima."""
from pathlib import Path
import argparse,time,shutil,json
import numpy as np
import pandas as pd
from metrics_flex import Inputs,service_deviations,save,sha

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ['case','release','out','annual-duals','annual-sha']:ap.add_argument('--'+name,required=True)
 a=ap.parse_args();start=time.time();out=Path(a.out);out.mkdir(parents=True,exist_ok=False);(out/'scripts').mkdir()
 for name in ['metrics_flex.py','metrics_national.py']:shutil.copy2(Path(__file__).parent/name,out/'scripts'/name)
 inp=Inputs(a.release);c=json.loads(inp.path('model_config_snapshot.json').read_text())['resolved_configuration']
 f=np.load(inp.path('flexible_load_dispatch.npz'),allow_pickle=False);p=f['province_codes'];h=f['hour_index']
 assert len(p)==31 and np.array_equal(h,np.arange(8760))
 frac=float(c['flexible_load']['ev_v1g']['shiftable_energy_fraction']);deviation=service_deviations(f,frac);reduction=-deviation.sum(axis=0)
 annual=pd.read_csv(inp.path('annual_flexible_load_by_province.csv')).set_index('province_code').loc[p]
 services=['heating','cooling','ev_v1g','ev_v2g'];credits=annual[[f'firm_{s}_flexibility_credit_gw' for s in services]].to_numpy()
 assert np.max(np.abs(credits-f['firm_flexible_capacity_credit_gw']))<=1e-10
 national=f['baseline_total_load_gw'].sum(axis=0);peak=int(np.argmax(national));clock=np.arange((peak//4)*4,(peak//4)*4+4);top=np.argsort(-national,kind='stable')[:4]
 rows=[]
 for name,ix in [('national_baseline_top4',top),('national_baseline_peak_clock4h',clock)]:
  for si,service in enumerate(services):
   vals=reduction[si,ix];credit=float(credits[:,si].sum());mean=float(vals.mean());low=float(vals.min())
   rows.append(dict(scope='national_simultaneous',service=service,ranking=name,top_n=4,mean_reduction_gw=mean,min_reduction_gw=low,credit_gw=credit,ratio_mean=mean/credit if credit>1e-12 else None,ratio_min=low/credit if credit>1e-12 else None,hour_indices=';'.join(map(str,ix))))
 pd.DataFrame(rows).to_csv(out/'credit_realization_national_service.csv',index=False)
 save(out/'metrics_national_summary.json',dict(case=a.case,release=a.release,T6_national='PASS',rows=8,method='Sum provinces at each same hour first; then compute mean/min across selected four hours. Credit=sum provincial credits.',inputs=inp.checked,elapsed_seconds=time.time()-start,command=vars(a)))
 files={str(x.relative_to(out)):{'sha256':sha(x),'bytes':x.stat().st_size} for x in out.rglob('*') if x.is_file()};save(out/'metrics_manifest.json',files)
 print(json.dumps({'case':a.case,'T6_national':'PASS','rows':8,'seconds':time.time()-start}),flush=True)
if __name__=='__main__':main()
