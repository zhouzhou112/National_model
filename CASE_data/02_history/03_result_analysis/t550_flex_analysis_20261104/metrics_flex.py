"""Read-only T6/T7 on SHA-anchored T550 backups; no solver or model imports.

Usage: python metrics_flex.py --case CASE --release RELEASE --annual-duals PATH
 --annual-sha SHA --out DIR [--typical-days]
Prices are planning duals. Only compact CSV/JSON outputs leave T550.
"""
from pathlib import Path
import argparse, hashlib, json, time, shutil
import numpy as np
import pandas as pd

BASE = Path('/home/zz2/National_model_server')
SERVICES = ('heating', 'cooling', 'ev_v1g', 'ev_v2g')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def save(p,x):
    Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

class Inputs:
    def __init__(self,release):
        self.root=BASE/'cloud_backup'/release; self.out=self.root/'output_8760'; self.checked={}
        backup=json.loads((self.root/'backup_manifest.json').read_text())
        mp=self.out/'result_manifest.json'
        assert sha(mp)==backup['source_result_manifest_sha256'],'result manifest SHA'
        self.index={x['path']:x for x in json.loads(mp.read_text())['files']}
        self.backup={x['path']:x for x in backup['files']}
        self.checked['result_manifest.json']={'sha256':sha(mp),'bytes':mp.stat().st_size}
    def path(self,name):
        p=self.out/name; v=self.index.get(name,self.backup.get('output_8760/'+name))
        assert v, 'unanchored input: '+name
        actual=sha(p); assert actual==v['sha256'], 'SHA mismatch: '+name
        if 'bytes' in v: assert p.stat().st_size==v['bytes']
        self.checked[name]={'sha256':actual,'bytes':p.stat().st_size,'source':str(p)}
        return p

def price_arrays(inputs,annual,annual_sha,provinces,hours,config):
    assert sha(annual)==annual_sha,'annual dual SHA'
    a=pd.read_csv(annual); q=a[a.row_family=='province_annual_effective_demand'].set_index('province_code')
    inj=a[a.row_family=='province_annual_non_spatial_injection'].set_index('province_code')
    assert len(q)==len(inj)==31 and q.index.is_unique and inj.index.is_unique
    assert set(q.index)==set(provinces)
    pair=float(np.max(np.abs(q.pi_million_cny_per_gwh+inj.pi_million_cny_per_gwh))*1000)
    f=pd.read_csv(inputs.path('hourly_marginal_prices.csv.gz'))
    assert not f.duplicated(['province_code','hour_index']).any() and len(f)==len(provinces)*len(hours)
    idx=pd.MultiIndex.from_product([provinces,hours],names=['province_code','hour_index'])
    f=f.set_index(['province_code','hour_index']).reindex(idx); assert not f.isna().any().any()
    numeric=f.select_dtypes(include=[np.number]).to_numpy();assert np.isfinite(numeric).all(),'Nonfinite hourly duals'
    dt=f.datetime_bj.to_numpy().reshape(len(provinces),len(hours));assert np.all(dt==dt[0]),'Province/hour datetime mismatch'
    def arr(col):return f[col].to_numpy(float).reshape(len(provinces),len(hours))
    energy=1000*(arr('power_balance_pi_million_cny_per_gwh')+q.loc[provinces].pi_million_cny_per_gwh.to_numpy()[:,None])
    sec=config['security']; up=float(sec['up_reserve_load_fraction'])
    down=float(sec['down_reserve_load_fraction'])
    # Exact production keys verified by caller/config below; no silent coefficient inference.
    assert up==down==.05
    inertia_seconds=float(sec['minimum_system_inertia_seconds']) if sec.get('minimum_system_inertia_seconds') is not None else float(sec['inertia_reference_seconds'])*float(sec['inertia_tolerance_fraction'])
    reserve=1000*.05*(arr('up_reserve_pi_million_cny_per_gwh')+arr('down_reserve_pi_million_cny_per_gwh'))
    inertia=1000*inertia_seconds*arr('inertia_pi_million_cny_per_gw_s')
    dates=pd.to_datetime(f.reset_index().iloc[:len(hours)].datetime_bj).to_numpy()
    meta={'annual_duals_path':str(annual),'annual_duals_sha256':annual_sha,'annual_pair_max_abs_cny_per_mwh':pair,'load_price_formula':'1000*(power_balance_pi+annual_effective_demand_pi+0.05*up_pi+0.05*down_pi+inertia_seconds*inertia_pi)','inertia_seconds':inertia_seconds,'energy_negative_hours':int((energy<0).sum()),'load_price_negative_hours':int((energy+reserve+inertia<0).sum())}
    return energy,reserve,inertia,dates,meta

def service_deviations(f,frac):
    alpha=f['ev_enrolled_service_fraction'][:,None]; beta=f['ev_bidirectional_service_fraction'][:,None]
    return np.stack((f['actual_heating_gw']-f['baseline_heating_gw'],f['actual_cooling_gw']-f['baseline_cooling_gw'],f['ev_v1g_pool_charge']-(alpha-beta)*frac*f['baseline_ev_gw'],f['ev_v2g_pool_charge']-beta*frac*f['baseline_ev_gw']-f['ev_v2g_discharge_gw']),axis=1)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('case','release','annual-duals','annual-sha','out'):ap.add_argument('--'+n,required=True)
    ap.add_argument('--typical-days',action='store_true');args=ap.parse_args(); start=time.time()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    (out/'scripts').mkdir();shutil.copy2(__file__,out/'scripts'/Path(__file__).name)
    inputs=Inputs(args.release)
    config=json.loads(inputs.path('model_config_snapshot.json').read_text())['resolved_configuration']
    f=np.load(inputs.path('flexible_load_dispatch.npz'),allow_pickle=False)
    p=f['province_codes'].astype(int); h=f['hour_index'].astype(int)
    assert len(p)==31 and len(h)==8760 and np.array_equal(h,np.arange(8760))
    assert len(set(p))==31
    annual=pd.read_csv(inputs.path('annual_flexible_load_by_province.csv')).set_index('province_code').loc[p]
    baseline=f['baseline_total_load_gw']; effective=f['effective_total_load_gw']
    alpha=f['ev_enrolled_service_fraction'][:,None]; beta=f['ev_bidirectional_service_fraction'][:,None]
    frac=float(config['flexible_load']['ev_v1g']['shiftable_energy_fraction'])
    deviations=service_deviations(f,frac)
    closure=float(np.max(np.abs(deviations.sum(axis=1)-(effective-baseline))))
    assert closure<=1e-6, 'service decomposition mismatch: '+str(closure)
    credits=annual[[f'firm_{s}_flexibility_credit_gw' for s in SERVICES]].to_numpy()
    credit_diff=float(np.max(np.abs(credits-f['firm_flexible_capacity_credit_gw'])))
    assert credit_diff<=1e-10,'credit CSV/NPZ mismatch'
    assert float(np.max(np.abs(alpha[:,0]-annual.ev_enrolled_service_fraction)))<=1e-10
    energy,reserve,inertia,dates,meta=price_arrays(inputs,Path(args.annual_duals),args.annual_sha,p,h,config)
    loadprice=energy+reserve+inertia
    peak=int(np.argmax(baseline.sum(axis=0))); national_top=np.argsort(-baseline.sum(axis=0),kind='stable')[:4]
    clock_start=(peak//4)*4; clock=np.arange(clock_start,clock_start+4)
    rows=[]; windows=[]
    def append(pi,service_idx,ranking,selected):
        red=-deviations[pi,service_idx,selected];credit=float(credits[pi,service_idx]); mean=float(red.mean());low=float(red.min())
        rows.append(dict(province_code=int(p[pi]),service=SERVICES[service_idx],ranking=ranking,top_n=len(selected),mean_reduction_gw=mean,min_reduction_gw=low,credit_gw=credit,ratio_mean=mean/credit if credit>1e-12 else None,ratio_min=low/credit if credit>1e-12 else None))
    for pi,province in enumerate(p):
        for ranking,data in [('baseline_peak',baseline),('effective_peak',effective),('load_marginal_price',loadprice)]:
            order=np.argsort(-data[pi],kind='stable')
            for n in [4,20,100]:
                ix=order[:n]
                windows.extend(dict(province_code=int(province),ranking=ranking,top_n=n,rank=j+1,hour_index=int(h[k]),datetime_bj=str(dates[k])) for j,k in enumerate(ix))
                for s in range(4):append(pi,s,ranking,ix)
        for ranking,ix in [('national_baseline_top4',national_top),('national_baseline_peak_clock4h',clock)]:
            for s in range(4):append(pi,s,ranking,ix)
    pd.DataFrame(rows).to_csv(out/'credit_realization_by_province_service.csv',index=False)
    pd.DataFrame(windows).to_csv(out/'credit_ranking_hours.csv',index=False)
    meta.update(case=args.case,release=args.release,shiftable_energy_fraction=frac,T6='PASS',service_decomposition_max_abs_gw=closure,credit_csv_npz_max_abs_gw=credit_diff,zero_credit_ratio_rule='Blank if credit <=1e-12 GW; no division by numerical zero',national_peak_hour_index=peak,national_top4_hour_indices=national_top.tolist(),national_peak_clock4h_indices=clock.tolist(),national_window_definition='Both national highest four synchronous hours and fixed Beijing clock 4h block containing national baseline peak; not conflated',inputs=inputs.checked)
    if args.typical_days:
        v=np.load(inputs.path('vre_dispatch.npz'),allow_pickle=False)
        assert np.array_equal(v['province_codes'],p) and np.array_equal(v['hour_index'],h)
        tech=list(v['technologies'].astype(str));gen=v['generation_gw']; assert gen.shape[:2]==(31,len(tech))
        wind=gen[:,[i for i,t in enumerate(tech) if t in ['onwind','offwind']],:].sum(axis=1)
        solar=gen[:,[i for i,t in enumerate(tech) if t in ['upv','dpv']],:].sum(axis=1)
        d=pd.DatetimeIndex(dates);peak_day=d[int(np.argmax(effective.sum(axis=0)))].date();records=[]
        requests=[(44,'calendar_june21',d[(d.month==6)&(d.day==21)][0].date()),(32,'calendar_june23',d[(d.month==6)&(d.day==23)][0].date()),(44,'national_effective_peak_day',peak_day),(32,'national_effective_peak_day',peak_day)]
        for province,label,day in requests:
            pi=list(p).index(province);ix=np.flatnonzero(d.date==day);assert len(ix)==24
            for k in ix:
                r=dict(province_code=province,selection=label,hour_index=int(h[k]),datetime_bj=str(d[k]),energy_price_cny_per_mwh=float(energy[pi,k]),reserve_component_cny_per_mwh=float(reserve[pi,k]),inertia_component_cny_per_mwh=float(inertia[pi,k]),load_marginal_price_cny_per_mwh=float(loadprice[pi,k]),wind_generation_gw=float(wind[pi,k]),pv_generation_gw=float(solar[pi,k]))
                for key in ['baseline_total_load_gw','effective_total_load_gw','baseline_heating_gw','baseline_cooling_gw','baseline_ev_gw','actual_heating_gw','actual_cooling_gw','actual_ev_gw','ev_v2g_discharge_gw']:r[key]=float(f[key][pi,k])
                r['actual_ev_gross_charge_gw']=r['actual_ev_gw']
                r['actual_ev_net_load_gw']=r['actual_ev_gw']-r['ev_v2g_discharge_gw']
                records.append(r)
        pd.DataFrame(records).to_csv(out/f'typical_day_{args.case}.csv',index=False)
        meta.update(T7='PASS',typical_day_rows=len(records),national_effective_peak_date=str(peak_day),ev_note='actual_ev_gw is gross charging; net EV load = actual_ev_gw - V2G discharge',wind_technologies=['onwind','offwind'],pv_technologies=['upv','dpv'])
    meta.update(inputs=inputs.checked,elapsed_seconds=time.time()-start,command=vars(args),solver_loaded=False)
    save(out/'metrics_summary.json',meta)
    files={str(x.relative_to(out)):{'sha256':sha(x),'bytes':x.stat().st_size} for x in out.rglob('*') if x.is_file()}
    assert all(x['bytes']<=30_000_000 for x in files.values()) and sum(x['bytes'] for x in files.values())<=100_000_000
    save(out/'metrics_manifest.json',files)
    print(json.dumps({'case':args.case,'T6':'PASS','T7':meta.get('T7'),'closure':closure,'rows':len(rows),'seconds':time.time()-start}),flush=True)

if __name__=='__main__':main()
