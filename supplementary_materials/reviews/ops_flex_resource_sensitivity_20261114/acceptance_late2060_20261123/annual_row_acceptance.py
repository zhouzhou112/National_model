"""Exact annual-row family check reused from accepted Case3 2060 evidence workflow."""
import math,re
def row_check(row):
 if row['status']!='ORDER_AND_ROW_VERIFIED' or row['sense']!='=':raise ValueError('Row order/sense not verified')
 match=re.fullmatch(r'province_annual_external_sent_p(\d+)',row['name'])
 if not match:raise ValueError('Unreviewed row family; stop for author review')
 groups={}
 for t in row['terms']:groups.setdefault(t['variable'].split('[')[0],[]).append(t)
 expected={'province_annual_external_sent_gwh','flow_forward_gw','flow_reverse_ac_gw'}
 if not set(groups)<=expected or 'province_annual_external_sent_gwh' not in groups:raise ValueError('Unexpected annual row variables')
 account=groups['province_annual_external_sent_gwh']
 if len(account)!=1 or account[0]['coefficient']!=1:raise ValueError('Unexpected annual account coefficient')
 for k,terms in groups.items():
  if k!='province_annual_external_sent_gwh' and (len(terms)%8760 or any(t['coefficient']!=-1 for t in terms)):raise ValueError('Not an unscaled full-year flow sum')
 magnitude=float(row['row_magnitude']); residual=float(row['violation'])
 if not math.isfinite(magnitude) or magnitude<=0 or not math.isfinite(residual) or residual<0:raise ValueError('Invalid row values')
 limit=max(1e-3,1e-6*magnitude)
 return dict(name=row['name'],province_code=int(match[1]),family='province_annual_external_sent',unit='GWh',scope='8760 one-hour periods',row_magnitude_gwh=magnitude,residual_gwh=residual,relative_residual=residual/magnitude,tolerance_gwh=limit,ratio_to_tolerance=residual/limit,passed=residual<=limit,rule='AGENTS 2026-10-30 annual energy row: max(1e-3 GWh,1e-6*annual row energy)',equation='province_annual_external_sent_gwh = sum(outgoing forward GW and outgoing AC reverse GW)*1h',term_families={k:dict(count=len(v),coefficient_values=sorted(set(t['coefficient'] for t in v)),contribution=math.fsum(t['contribution'] for t in v)) for k,v in groups.items()})
