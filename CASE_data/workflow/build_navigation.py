"""Build the CASE_data entry pages; no scientific payload edits."""
import csv
import hashlib
import html
import json
import os
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote,unquote

DATA=Path(__file__).resolve().parent.parent;ROOT=DATA.parent
CSS='''body{margin:0;background:#f3f6f7;color:#17313d;font:15px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1280px;margin:auto;padding:32px}h1{font-size:28px;margin-bottom:6px}a{color:#006c83;text-decoration:none}a:hover{text-decoration:underline}.note{background:#dfedf0;padding:16px;border-radius:8px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px}.card{background:#fff;border:1px solid #dbe5e9;border-radius:8px;padding:18px}.card h2{font-size:18px;margin:0 0 12px}small{color:#526d79}table{border-collapse:collapse;width:100%;background:#fff;margin:18px 0}td,th{border-bottom:1px solid #dbe5e9;text-align:left;padding:10px;vertical-align:top}th{background:#dce9ed}input{font:inherit;padding:10px;width:min(520px,90%);margin-top:15px}code{font-size:12px;overflow-wrap:anywhere}details{margin:12px 0;background:#fff;padding:12px}.badge{display:inline-block;padding:2px 8px;background:#e3efea;border-radius:4px;font-size:12px}.muted{color:#6e7b82}.cards li{margin-bottom:7px}'''
LABELS={'00_identity.json':'案例身份与来源','20_acceptance.json':'验收证据全文','01_annual_summary.json':'年度系统汇总及求解质量','02_costs.csv':'成本分项',
 '03_capacity.csv':'分省技术装机与新增','05_storage_capacity.csv':'储能功率与能量容量','07_interprovince_network.csv':'省际通道容量','08_city_network.csv':'城市网络',
 '09_adequacy.csv':'供电充裕度','10_resource_accounting.csv':'资源核算','04_generation.csv':'发电量','06_storage_annual.csv':'全国储能运行',
 '14_vre_curtailment.csv':'风光可发量与弃电','15_storage_operation.csv':'分省储能运行','16_thermal_operation.csv':'火电连续启停等效量',
 '13_flex_services.csv':'四类服务签约、上下调与调用小时','11_annual_constraint_duals.csv':'年度约束影子值','12_dac.csv':'DAC 容量与捕集',
 'carbon_accounting.json':'年度碳核算','90_remote_files.csv':'T550 全量文件路径、大小与SHA','91_remote_directories.json':'T550 已有分析目录',
 '92_provenance.json':'提取来源及校验'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def href(target,base):return quote(os.path.relpath(target,base).replace('\\','/'),safe='/')
def page(title,body):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+CSS+'</style><main>'+body+'</main></html>'
def redirect(path,target):
    path.parent.mkdir(parents=True,exist_ok=True);link=href(target,path.parent)
    path.write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url='+link+'"><a href="'+link+'">进入 CASE_data 正式资料库</a>',encoding='utf-8')


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.links.extend(v for k,v in attrs if k=='href')


def main():
    catalog=json.loads((DATA/'catalog.json').read_text());schema=json.loads((DATA/'schema.json').read_text());rows=[];coverage=[];pages=[];annual_rows=[]
    migration=DATA/'00_registry/migration_20261124'
    plan=json.loads((migration/'move_plan.json').read_text());mapping={x['source']:x['destination'] for x in plan['moves']}
    old_catalog=json.loads((ROOT/'case_results/case_catalog.json').read_text());old={c['release']:c for c in old_catalog['cases']}
    def migrated(s):
        if not isinstance(s,str):return s
        normalized=s.replace('\\','/');prefix=str(ROOT).replace('\\','/')+'/'
        absolute=normalized.startswith(prefix);rel=normalized[len(prefix):] if absolute else normalized
        for src,dst in mapping.items():
            if rel==src or rel.startswith(src+'/'):return (prefix if absolute else '')+dst+rel[len(src):]
        return s
    def map_value(value):
        if isinstance(value,str):return migrated(value)
        if isinstance(value,list):return [map_value(x) for x in value]
        if isinstance(value,dict):return {k:map_value(v) for k,v in value.items()}
        return value
    order={'REF':0,'OPS':1,'LATE':2,'PLAN':3,'PLAN-NC':4,'OPS-Conservative':5,'OPS-Open':6,'LATE-Open':7,'D1':8,'LATE-Open-TEST':9}
    for c in sorted(catalog['cases'],key=lambda x:(order[x['paper_scenario']],x['year'],x['release'])):
        folder=DATA/c['relative_directory'];meta=json.loads((folder/'case.json').read_text());manifest=json.loads((folder/'core_manifest.json').read_text())
        title=f'{c["paper_scenario"]} {c["year"]}';body='<p><a href="'+href(DATA/'00_案例总览.html',folder)+'">← 全部案例</a></p><h1>'+title+'</h1>'
        if c['scientific_tables']:
            a=json.loads((folder/'01_system_costs/01_annual_summary.json').read_text());metrics=a['barrier_metrics']
            annual_rows.append(dict(paper_scenario=c['paper_scenario'],legacy_case=c['legacy_case'],year=c['year'],release=c['release'],kind=c['kind'],
                P_million_cny=metrics['primal_objective'],D_million_cny=metrics['dual_objective'],P_minus_D_million_cny=metrics['primal_objective']-metrics['dual_objective'],
                **{k:a['annual'][k] for k in ['annual_load_gwh','annual_generation_gwh','vre_curtailment_gwh','storage_charge_gwh','storage_discharge_gwh']},
                **{k:a['carbon'][k] for k in ['annual_fossil_unabated_emissions_mtco2','annual_dac_removed_mtco2','annual_net_emissions_mtco2']}))
        body+='<p><span class="badge">'+html.escape(c['acceptance_status'])+'</span>　'+c['kind']+'　·　核心 '+f'{c["core_bytes"]/1024:.0f} KiB'+'</p>'
        if not c['scientific_tables']:body+='<p class="note">此记录是失败尝试或排序测试，没有完整生产解。保留身份及保全索引，不纳入生产结果比较。</p>'
        body+='<div class="grid">'
        for module,label in schema['modules'].items():
            (folder/module).mkdir(exist_ok=True)
            files=[n for n in manifest['files'] if n.startswith(module+'/')]
            body+='<section class="card"><h2>'+html.escape(label)+'</h2>'
            if not files:body+='<p class="muted">不适用：此记录没有完整生产结果。</p>'
            else:
                body+='<ul class="cards">'
                for name in files:
                    p=folder/name;assert sha(p)==manifest['files'][name]['sha256']
                    body+='<li><a href="'+quote(name,safe='/')+'">'+html.escape(LABELS.get(p.name,p.name))+'</a> <small>'+p.suffix[1:].upper()+'</small></li>'
                body+='</ul>'
            if module=='05_prices':body+='<small>年度约束工程对偶；完整逐时负荷价格及典型周仍在 T550 扩展分析目录。</small>'
            if module=='04_flexibility' and c['paper_scenario']=='REF':body+='<small>REF 未启用柔性服务，条目明确不适用，未填造零值。</small>'
            body+='</section>'
            coverage.append(dict(paper_scenario=c['paper_scenario'],year=c['year'],release=c['release'],module=module,
                status='AVAILABLE' if files else 'NOT_APPLICABLE_NO_COMPLETE_SOLUTION',files=len(files)))
        body+='</div><details><summary>版本、历史档案与 T550 原件位置</summary><p>release：<code>'+c['release']+'</code><br>历史代号：'+c['legacy_case']+'<br>T550 全量：<code>'+html.escape(meta['source_backup'])+'</code></p>'
        previous=map_value(old.get(c['release'],dict(case=c['legacy_case'],year=c['year'],release=c['release'],kind=c['kind'],paper_scenario=c['paper_scenario'],acceptance_status=c['acceptance_status'],remote_directory=meta['source_backup'])))
        card=ROOT/previous['case_card'] if previous.get('case_card') else None
        if card and card.exists():body+='<p><a href="'+href(card,folder)+'">查看历史交付卡</a> · <a href="'+href(DATA/'00_registry/migration_20261124/reviews_classification.csv',folder)+'">查看历史目录分类</a></p>'
        body+='</details>'
        index=folder/'index.html';index.write_text(page(title,body),encoding='utf-8');pages.append(index)
        previous.update(core_directory=str(folder.relative_to(ROOT)).replace('\\','/'),paper_directory=str(folder.relative_to(ROOT)).replace('\\','/'),
            core_index=str(index.relative_to(ROOT)).replace('\\','/'),paper_index=str(index.relative_to(ROOT)).replace('\\','/'),
            core_schema_version=schema['version'],core_file_count=c['core_file_count'],core_bytes=c['core_bytes'])
        old[c['release']]=previous
        legacy_view=ROOT/'case_results/by_paper_scenario'/c['paper_scenario']/str(c['year'])/c['release']/'index.html'
        redirect(legacy_view,index)
        rows.append('<tr><td><a href="'+href(index,DATA)+'"><b>'+title+'</b></a></td><td>'+c['kind']+'</td><td>'+c['acceptance_status']+'</td><td>'+str(c['core_file_count'])+'</td><td>'+f'{c["core_bytes"]/1024:.0f} KiB'+'</td></tr>')
    counts=Counter(c['kind'] for c in catalog['cases']);complete=sum(c['scientific_tables'] for c in catalog['cases'])
    body='<h1>CASE_data · 求解案例资料库</h1><p>从这里按论文正式情景查看文章所需核心结果。'+f'{counts["COMPLETED_PRODUCTION"]}个生产案例、{counts["COMPLETED_DIAGNOSTIC"]}个诊断案例、{counts["COMPLETED_FACTOR_TEST"]}个排序测试和{counts["FAILED_ATTEMPT"]}次失败尝试。'+'</p>'
    body+='<p class="note">'+str(complete)+'个完整解各有8个模块、22份一致的核心文件，合计约'+f'{sum(c["core_bytes"] for c in catalog["cases"])/2**20:.1f}'+' MiB。2026-11-24迁入62.05 GiB历史求解资料，原件完整保留。旧路径仅作兼容入口；移动本身不释放磁盘空间。</p>'
    body+='<p><a href="00_registry/annual_case_summary.csv">跨案例年度概要</a> · <a href="00_registry/module_coverage.csv">模块完整性表</a> · <a href="00_registry/case_catalog.json">案例台账</a> · <a href="00_registry/migration_20261124/REVIEW_INDEX.html">历史目录与冗余筛查</a> · <a href="workflow/WORKFLOW_ZH.md">标准工作流</a></p>'
    body+='<input id="q" placeholder="搜索 REF、PLAN、年份或验收状态"><table><thead><tr><th>案例</th><th>类型</th><th>验收</th><th>核心文件</th><th>大小</th></tr></thead><tbody id="cases">'+''.join(rows)+'</tbody></table>'
    body+='<p>Base→REF；B→OPS；C→LATE；Case3→PLAN；nocredit→PLAN-NC。Conservative、Base、Open是资源情景，和规划路径分开。完整MPS、BarX/BarPi和逐时数组留T550。</p>'
    body+='<script>document.getElementById("q").oninput=function(){let q=this.value.toLowerCase();document.querySelectorAll("#cases tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}</script>'
    (DATA/'00_案例总览.html').write_text(page('CASE_data 案例总览',body),encoding='utf-8');pages.append(DATA/'00_案例总览.html')
    redirect(ROOT/'case_results/00_案例总览.html',DATA/'00_案例总览.html')
    save(DATA/'00_registry/case_catalog.json',dict(schema_version=schema['version'],cases=list(old.values())))
    save(ROOT/'case_results/case_catalog.json',dict(schema_version=schema['version'],canonical_catalog='CASE_data/00_registry/case_catalog.json',cases=list(old.values())))
    with (DATA/'00_registry/module_coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
    with (DATA/'00_registry/annual_case_summary.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(annual_rows[0]));w.writeheader();w.writerows(annual_rows)
    with (migration/'reviews_classification.csv').open(encoding='utf-8-sig',newline='') as f:history=list(csv.DictReader(f))
    hbody='<h1>历史档案与清理候选</h1><p><a href="../../00_案例总览.html">返回案例总览</a></p><p>全部分类保留证据。本轮未删除数据；失败或旧版本不等于废弃。目录大小不跟随旧路径联接。</p>'
    hbody+='<p><a href="redundancy_summary.json">冗余筛查统计</a> · <a href="large_remote_copy_candidates.csv">已有T550完整备份匹配的大副本候选</a> · <a href="duplicate_groups.csv">同SHA重复组</a></p><table><tr><th>类别</th><th>目录</th><th>GiB</th><th>处理与理由</th></tr>'
    for r in sorted(history,key=lambda r:(r['category'],-int(r['bytes']))):
        p=ROOT/r['destination'];assert p.exists()
        hbody+='<tr><td>'+r['category']+'</td><td><a href="'+href(p,migration)+'/">'+html.escape(Path(r['directory']).name)+'</a></td><td>'+f'{int(r["bytes"])/2**30:.4f}'+'</td><td>'+html.escape(r['reason'])+'</td></tr>'
    hbody+='</table>';hindex=migration/'REVIEW_INDEX.html';hindex.write_text(page('历史档案分类',hbody),encoding='utf-8');pages.append(hindex)
    count=0
    for p in pages:
        parser=Links();parser.feed(p.read_text(encoding='utf-8'))
        for link in parser.links:
            assert (p.parent/unquote(link)).resolve().exists(),(p,link);count+=1
    save(DATA/'00_registry/navigation_verification.json',dict(status='PASS',pages=len(pages),links_checked=count,cases=len(catalog['cases']),
          core_files_per_complete_case=22,modules_per_case=8,scientific_payloads_modified=False))
    print(json.dumps(dict(status='PASS',pages=len(pages),links=count,cases=len(catalog['cases']))))


if __name__=='__main__':main()
