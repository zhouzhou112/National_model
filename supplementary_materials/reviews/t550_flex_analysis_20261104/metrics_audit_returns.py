"""Verify small returned metrics artifacts, hashes, keys and independent accounting identities."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[4]/'claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns'
FLEX=['case3_2030','case3_2040','c2050','nocredit_2030','b2030','b2040','b2050','b2060']
REVENUE=['base2030','base2040','base2050','base2060','case3_2030','case3_2040','c2050','b2030','b2040','b2050','b2060']
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--allow-partial',action='store_true');a=ap.parse_args();records=[];missing=[]
 for case in sorted(set(FLEX+REVENUE)):
  p=ROOT/case
  for tag,needed in [('flex',case in FLEX),('national',case in FLEX),('revenue',case in REVENUE)]:
   if not needed:continue
   receipt=p/'metadata'/f'{tag}_transfer_receipt.json'
   if not receipt.exists():missing.append(case+':'+tag);continue
   files=json.loads(receipt.read_text())
   for name,x in files.items():
    f=p/name;assert f.is_file() and f.stat().st_size==x['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256'],str(f)
   if tag=='flex':
    d=pd.read_csv(p/'credit_realization_by_province_service.csv');assert len(d)==1364 and not d.duplicated(['province_code','service','ranking','top_n']).any()
    assert len(d.province_code.unique())==31 and len(d.service.unique())==4
    m=json.loads((p/'metadata/metrics_summary.json').read_text());assert m['T6']=='PASS' and m['credit_csv_npz_max_abs_gw']<=1e-10
    if case in ('case3_2030','case3_2040'):
     t=pd.read_csv(p/f'typical_day_{case}.csv');assert len(t)==96
     np.testing.assert_allclose(t.actual_ev_net_load_gw,t.actual_ev_gross_charge_gw-t.ev_v2g_discharge_gw,rtol=0,atol=1e-12)
   elif tag=='national':
    d=pd.read_csv(p/'credit_realization_national_service.csv');assert len(d)==8 and not d.duplicated(['service','ranking']).any()
    assert d.top_n.eq(4).all()
   else:
    d=pd.read_csv(p/'firm_revenue_by_province_technology.csv');assert len(d)==403 and not d.duplicated(['province_code','technology']).any()
    income=d[['energy_revenue_million_cny','capacity_revenue_million_cny','up_reserve_revenue_million_cny','down_reserve_revenue_million_cny','inertia_revenue_million_cny']].sum(axis=1)
    np.testing.assert_allclose(income,d.all_related_dual_revenue_million_cny,rtol=1e-12,atol=1e-8)
    net=income-d.direct_cash_cost_million_cny-d.carbon_opportunity_cost_million_cny-d.biomass_opportunity_cost_million_cny-d.co2_transport_injection_cost_million_cny
    np.testing.assert_allclose(net,d.net_economic_revenue_million_cny,rtol=1e-10,atol=1e-7)
    z=pd.read_csv(p/'co2_cost_allocation_by_province_source.csv');assert len(z)==186 and z.technology.eq('DAC').sum()==31
    total=z.groupby('province_code').allocated_co2_cost_million_cny.sum();expected=z.groupby('province_code').province_co2_transport_injection_cost_million_cny.first()
    np.testing.assert_allclose(total,expected,rtol=1e-12,atol=1e-8)
    assert z.groupby('province_code').province_co2_transport_injection_cost_million_cny.nunique().eq(1).all()
    cc=z[z.technology!='DAC'].set_index(['province_code','technology']);dd=d[d.technology.str.endswith('ccs')].set_index(['province_code','technology']).reindex(cc.index)
    np.testing.assert_allclose(cc.allocated_co2_cost_million_cny,dd.co2_transport_injection_cost_million_cny,rtol=1e-12,atol=1e-8)
    np.testing.assert_allclose(cc.captured_source_mtco2,dd.captured_mtco2,rtol=1e-12,atol=1e-8)
    assert pd.read_csv(p/'revenue_cost_reconciliation.csv').status.eq('PASS').all()
    assert d.market_scope_status.eq('NOT_DEFINED_NO_MARKET_RULE_EVIDENCE').all()
   records.append(dict(case=case,task=tag,files=len(files),bytes=sum(x['bytes'] for x in files.values()),status='PASS'))
 result=dict(status='PASS' if not missing else 'PARTIAL',completed=records,missing=missing)
 Path(__file__).with_name('metrics_return_audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));assert a.allow_partial or not missing,missing
if __name__=='__main__':main()
