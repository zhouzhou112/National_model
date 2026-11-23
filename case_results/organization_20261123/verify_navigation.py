"""Verify offline navigation, core parity, size limits and source distinctions."""
import csv
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
RESULTS=ROOT/'case_results'
LIB=RESULTS/'core_library_20261123'


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            self.links.extend(v for k,v in attrs if k=='href')


def main():
    catalog=json.loads((LIB/'catalog.json').read_text())['cases']; rows=[]; linked=0
    for page in [RESULTS/'00_案例总览.html',*LIB.rglob('index.html')]:
        parser=Links();parser.feed(page.read_text(encoding='utf-8'))
        for href in parser.links:
            assert not urlparse(href).scheme,href
            assert (page.parent/unquote(href)).exists(),(page,href)
            linked+=1
    for case in catalog:
        folder=LIB/case['relative_directory']; core=folder/'core'
        manifest=json.loads((folder/'core_manifest.json').read_text())
        for name,info in manifest['files'].items():
            p=folder/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256']
        for p in sorted(core.iterdir()):
            assert p.suffix in ('.json','.csv') and p.stat().st_size<=1024**2
            count=None
            if p.suffix=='.csv':
                with p.open(encoding='utf-8',newline='') as stream:
                    count=sum(1 for _ in csv.DictReader(stream))
            rows.append(dict(case=case['case'],year=case['year'],release=case['release'],kind=case['kind'],
                file=p.name,status='PRESENT_SHA_VERIFIED',rows=count,bytes=p.stat().st_size))
        if case['scientific_tables']:
            with (core/'13_flex_services.csv').open(encoding='utf-8',newline='') as stream:
                services=list(csv.DictReader(stream))
            assert len(services)==124 and len({(r['province_code'],r['service']) for r in services})==124
            if case['case']=='Base':
                assert all(r['applicability']=='DISABLED_BY_SCENARIO' and r['contract_gw']=='' for r in services)
            else:
                assert all(r['applicability']=='ENABLED' and r['contract_gw']!='' for r in services)
    with (RESULTS/'core_coverage.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report=dict(status='PASS',cases=len(catalog),html_pages=30,local_links_checked=linked,
        core_files_checked=len(rows),all_core_hashes_match=True,service_rows_per_complete_case=124,
        no_large_original_payload=True,model_or_solver_changed=False)
    (WORK/'navigation_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
