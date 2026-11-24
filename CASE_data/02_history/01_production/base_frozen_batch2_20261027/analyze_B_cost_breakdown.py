"""Read verified compact T550 results; write a small B versus Base breakdown.

Usage: --analysis PATH --output NEW_JSON. No source writes or solving.
Output cost unit is 100 million CNY/year (yi CNY).
"""
import argparse,csv,datetime,hashlib,json,socket
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    assert socket.gethostname().split('.')[0]=='t550'
    assert not a.output.exists()
    source={}
    manifest=json.loads((a.analysis.parent/'delivery_manifest.json').read_text())
    entries={r['path']:r for r in manifest['files']}
    for name in ['cost_components.csv','run_summaries.json','flexible_contracts.csv','national_generation.csv']:
        p=a.analysis/name;entry=entries['analysis/'+name]
        assert p.stat().st_size==entry['bytes']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
        source[name]=entry['sha256']
    def rows(name):
        with (a.analysis/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    costs=rows('cost_components.csv');flex=rows('flexible_contracts.csv');gen=rows('national_generation.csv')
    summaries={(r['case'],r['year']):r for r in json.loads((a.analysis/'run_summaries.json').read_text())}
    result={}
    for year in [2030,2040,2050,2060]:
        maps={c:{r['cost_component']:float(r['value_million_cny_per_year']) for r in costs if r['case']==c and int(r['year'])==year} for c in ['Base','B']}
        keys=set(maps['Base'])|set(maps['B'])
        saving={k:(maps['Base'].get(k,0)-maps['B'].get(k,0))/100 for k in sorted(keys)}
        primary={r['cost_component'] for r in costs if r['included_in_primary_cost'].lower()=='true'}
        op=[k for k in keys if k.startswith('operating_') and not k.startswith('operating_detail_')]
        reconciliation={c:sum(maps[c].get(k,0) for k in op)-maps[c]['annual_operation'] for c in maps}
        # Report roundoff in independently accumulated cost exports; no model/QC change.
        for difference in reconciliation.values():assert abs(difference)<1e-3
        net=(summaries['Base',year]['objective_million_cny']-summaries['B',year]['objective_million_cny'])/100
        assert abs(sum(saving[k] for k in primary)-net)<1e-5
        f=next(r for r in flex if r['case']=='B' and int(r['year'])==year)
        f={k:float(v) for k,v in f.items() if k not in ['case','year']}
        b=summaries['Base',year]['annual_summary'];v=summaries['B',year]['annual_summary']
        physical={k:dict(Base=b[k],B=v[k],B_minus_Base=v[k]-b[k]) for k in ['vre_curtailment_gwh','storage_charge_gwh','storage_discharge_gwh','interprovincial_transmission_losses_gwh','period_effective_peak_load_gw','annual_load_gwh']}
        gm={c:{r['technology']:float(r['generation_gwh']) for r in gen if r['case']==c and int(r['year'])==year} for c in ['Base','B']}
        generation={k:(gm['B'].get(k,0)-gm['Base'].get(k,0))/1000 for k in set(gm['Base'])|set(gm['B'])}
        result[year]=dict(net_saving_yi_cny=net,saving_percent=net*10000/summaries['Base',year]['objective_million_cny'],saving_by_component_yi_cny=saving,flex_service_cost_yi_cny=-sum(saving[k] for k in op if k.startswith('operating_flexible_load_')),other_fixed_cost_saving_yi_cny=sum(saving[k] for k in primary if k not in ['annual_operation','dac','ccs_capture','co2_transport_injection']),operation_detail_minus_total_million_cny=reconciliation,flex=f,physical=physical,generation_change_twh=generation)
    for name,digest in source.items():assert hashlib.sha256((a.analysis/name).read_bytes()).hexdigest()==digest
    output=dict(host=socket.gethostname(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=source,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cost_unit='100 million CNY/year; positive means Base minus B saving',years=result)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(a.output),bytes=a.output.stat().st_size,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest())))

if __name__=='__main__':main()
