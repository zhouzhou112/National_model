"""Install only the allowlisted compact T550 package and build local navigation."""
import csv
import hashlib
import html
import json
import shutil
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
RESULTS = ROOT/'case_results'
DEST = RESULTS/'core_library_20261123'
ALIASES = {'Base':'REF / 无柔性基准','Case3':'PLAN / Flex-coopt（框架 A）','B':'OPS-Central / Base-frozen（框架 B）',
           'C':'LATE-Central（框架 C）','OPS-Open':'固定容量 / 开放资源','OPS-Conservative':'固定容量 / 保守资源',
           'LATE-Open':'受限联合优化 / 开放资源','nocredit':'无容量信用反事实','C5':'D1 / 省内城市链路诊断',
           'LATE-Open-TEST':'前五轮排序测试'}
DESCRIPTIONS = {'00_identity.json':'案例身份、版本、来源与登记状态','01_annual_summary.json':'年度汇总、碳核算、P/D 和求解质量',
 '02_costs.csv':'年化成本分项；按 included 标志区分总项与子项，勿重复相加','03_capacity.csv':'分省、分技术总装机与新建',
 '04_generation.csv':'分省、分技术年发电量','05_storage_capacity.csv':'储能功率与能量容量','06_storage_annual.csv':'全国储能运行',
 '07_interprovince_network.csv':'省际输电容量','08_city_network.csv':'省内城市网络','09_adequacy.csv':'分省充裕度',
 '10_resource_accounting.csv':'分省资源核算','11_annual_constraint_duals.csv':'年度约束工程影子值；不是完整逐时负荷价格',
 '12_dac.csv':'DAC 容量与捕集量','13_flex_services.csv':'统一服务池口径：签约、容量信用、上下调和等效调用小时',
 '14_vre_curtailment.csv':'风光可发、实际发电与弃电','15_storage_operation.csv':'分省储能运行与等效循环',
 '16_thermal_operation.csv':'连续启停容量及等效全容量次数；不是离散机组启停数','20_acceptance.json':'已有验收证据全文、原路径与 SHA',
 '90_remote_files.csv':'T550 全量原件路径、大小、SHA；本地不含这些大文件',
 '91_remote_directories.json':'T550 完整备份及既有分析目录与文件位置',
 '92_provenance.json':'本轮读取校验、闭合检查、方法与边界'}
CSS = '''body{font:16px/1.65 "Segoe UI","Microsoft YaHei",sans-serif;color:#183042;background:#f4f7f8;margin:0}main{max-width:1250px;margin:auto;padding:36px}h1{font-size:29px;margin-bottom:6px}p{max-width:1050px}a{color:#006481}code{font-size:12px;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;background:white;margin:22px 0}td,th{text-align:left;border-bottom:1px solid #dbe4e8;padding:11px;vertical-align:top}th{background:#e2edf0}small{color:#586e7d}input{padding:12px;width:95%;max-width:550px;font:inherit;border:1px solid #98aeb8}details{background:white;padding:10px 14px;margin:12px 0}.note{padding:16px;background:#e2edf0}.pill{font-size:12px;color:#345562}'''


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, obj):
    Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def page(title, body):
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+CSS+'</style><main>'+body+'</main></html>'


def main():
    receipt=json.loads((WORK/'library_receipt.json').read_text())
    package=WORK/'core_library.tar.gz'
    assert sha(package)==receipt['archive_sha256'] and package.stat().st_size==receipt['archive_bytes']
    assert not DEST.exists(), 'Preserve existing library; use a new version or explicitly verify it'
    with tarfile.open(package,'r:gz') as tar:
        members=tar.getmembers()
        for m in members:
            path=PurePosixPath(m.name)
            assert not path.is_absolute() and '..' not in path.parts and not m.issym() and not m.islnk()
            assert m.isdir() or m.isfile()
            if m.isfile():
                assert m.size<=1024**2 and path.suffix in ('.json','.csv','.md')
        DEST.mkdir()
        tar.extractall(DEST)
    catalog=json.loads((DEST/'catalog.json').read_text())['cases']
    schema=json.loads((DEST/'schema.json').read_text())
    original_catalog=json.loads((RESULTS/'case_catalog.json').read_text(encoding='utf-8-sig'))
    by_release={x['release']:x for x in original_catalog['cases']}
    validations=[]; summaries=[]; filecount=0; totalsize=0; rows=[]
    for case in sorted(catalog,key=lambda r:(r['case'],r['year'],r['release'])):
        folder=DEST/case['relative_directory'];core=folder/'core'
        manifest=json.loads((folder/'core_manifest.json').read_text())
        for name,info in manifest['files'].items():
            p=folder/name
            assert sha(p)==info['sha256'] and p.stat().st_size==info['bytes'],p
            filecount+=1;totalsize+=p.stat().st_size
        if case['scientific_tables']:
            assert sorted(p.name for p in core.iterdir())==schema['scientific_core_files']
        for p in core.glob('*.csv'):
            with p.open(encoding='utf-8',newline='') as stream:
                assert next(csv.reader(stream))==schema['csv_columns'][p.name]
        identity=json.loads((core/'00_identity.json').read_text())
        provenance=json.loads((core/'92_provenance.json').read_text())
        remote=json.loads((core/'91_remote_directories.json').read_text())
        assert provenance['original_stats_unchanged'] is True
        acceptance=json.loads((core/'20_acceptance.json').read_text())
        if acceptance['evidence']:
            assert sha(acceptance['evidence']['local_path'])==acceptance['evidence']['sha256']
        case_label=f'{case["case"]} {case["year"]}'
        body='<h1>'+html.escape(case_label)+'</h1><p>'+html.escape(ALIASES[case['case']])+'</p>'
        body+='<p class="note">类型：'+case['kind']+'<br>登记验收：'+case['acceptance']+'<br>版本：<code>'+case['release']+'</code></p>'
        if not case['scientific_tables']:
            body+='<p>此条为失败尝试或排序测试，没有可用于科学比较的完整生产结果。保留身份和原件索引，未用空表伪装生产数据。</p>'
        body+='<h2>本地统一核心文件</h2><table><tr><th>文件</th><th>内容与口径</th><th>大小</th></tr>'
        for p in sorted(core.iterdir()):
            body+=f'<tr><td><a href="core/{p.name}">{p.name}</a></td><td>{DESCRIPTIONS.get(p.name,"")}</td><td>{p.stat().st_size/1024:.1f} KiB</td></tr>'
        body+='</table><h2>T550 全量原件与分析位置</h2><p>通过现有 SSH 入口 national-model-server 登录后访问以下路径。原目录保持原位；统一资料库提供导航链接。</p>'
        body+='<p>有序入口：<code>'+html.escape(remote['organized_entry'])+'</code><br>全量原件：<code>'+html.escape(remote['full_backup'])+'</code></p>'
        for d in remote['analysis_directories']:
            body+='<details><summary>'+html.escape(d['path'])+f'（{len(d["files"])} 个文件）</summary><p>导航：<code>'+html.escape(d['library_link'])+'</code></p>'
            body+='<ul>'+''.join('<li><code>'+html.escape(f['path'])+'</code> — '+f'{f["bytes"]/1024:.1f} KiB</li>' for f in d['files'])+'</ul></details>'
        body+='<p>对偶/定价等大分析输出留在上述目录。大文件逐项 SHA 见 90_remote_files.csv；目录索引不冒充新一次完整校验。</p>'
        (folder/'index.html').write_text(page(case_label,body),encoding='utf-8')
        entry=by_release[case['release']]
        entry.update(core_directory=str(folder.relative_to(ROOT)).replace('\\','/'),
                     core_index=str((folder/'index.html').relative_to(ROOT)).replace('\\','/'),
                     t550_library_directory=remote['organized_entry'],core_schema_version='20261123_v1',
                     core_sha_verified=True,core_bytes=case['core_bytes'])
        old_card=ROOT/entry['case_card']
        if old_card.exists():
            marker='<!-- unified-core-20261123 -->'
            if marker not in old_card.read_text(encoding='utf-8-sig'):
                text=old_card.read_text(encoding='utf-8-sig')
                old_card.write_text(marker+'\n最新统一核心入口：['+case_label+']('+str(folder/'index.html').replace('\\','/')+')。本卡以下内容作为历史记录保留。\n\n'+text,encoding='utf-8')
        href='core_library_20261123/'+case['relative_directory']+'/index.html'
        rows.append('<tr><td><a href="'+href+'">'+html.escape(case_label)+'</a><br><small>'+html.escape(ALIASES[case['case']])+'</small></td><td>'+case['kind']+'</td><td>'+case['acceptance']+'</td><td>'+f'{case["core_bytes"]/1024:.0f} KiB'+'</td><td><code>'+case['release']+'</code></td></tr>')
        validations.append(dict(release=case['release'],status='PASS',files=len(manifest['files']),original_stats_unchanged=True))
        if case['scientific_tables']:
            annual=json.loads((core/'01_annual_summary.json').read_text())
            met=annual['barrier_metrics']
            summaries.append(dict(case=case['case'],year=case['year'],kind=case['kind'],release=case['release'],
                acceptance=case['acceptance'],P_million_cny=met['primal_objective'],D_million_cny=met['dual_objective'],
                P_minus_D_million_cny=met['primal_objective']-met['dual_objective'],
                **{k:annual['annual'][k] for k in ['annual_load_gwh','annual_generation_gwh','vre_curtailment_gwh','storage_charge_gwh','storage_discharge_gwh']},
                **{k:annual['carbon'][k] for k in ['annual_fossil_unabated_emissions_mtco2','annual_dac_removed_mtco2','annual_net_emissions_mtco2']}))
    with (RESULTS/'core_case_summary.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(summaries[0]));writer.writeheader();writer.writerows(summaries)
    original_catalog['as_of_utc']=datetime.now(timezone.utc).isoformat()
    original_catalog['organized_core_library']='case_results/core_library_20261123'
    save(RESULTS/'case_catalog.json',original_catalog)
    with (RESULTS/'case_catalog.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['case','year','release','kind','solver_status','acceptance_status','backup_status','core_directory','t550_library_directory','remote_directory']
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(original_catalog['cases'])
    body='<h1>求解案例总览</h1><p>25 个生产案例、1 个诊断案例、1 个排序测试和 2 次失败尝试。按情景 → 年份 → release 查找；点击案例即可打开核心数据及 T550 原件位置。</p>'
    body+='<p class="note">本地统一核心包合计 '+f'{totalsize/1024**2:.2f} MiB'+'。26 个有完整解的案例均为同样 21 份核心文件、相同 CSV 字段。原模型、BarX/BarPi、逐时数组和详细分析留在 T550；旧交付包保留在原位。</p>'
    body+='<p><a href="core_case_summary.csv">全案例年度概要表</a> · <a href="case_catalog.csv">目录清单</a> · <a href="core_library_20261123/schema.json">统一字段定义</a> · <a href="LATE_OPEN_2060_ACCEPTANCE_20261123.md">LATE-Open 2060 条件验收报告</a></p>'
    body+='<p>目录名 B 是历史框架 B（OPS-Central），不等同于资源情景的“基准 B”。Base 对应 REF，Case3 对应 PLAN，C 对应中央 LATE。Base 的柔性服务明确为不适用，不把未启用服务当作缺失导出。</p>'
    body+='<input id="filter" placeholder="筛选：情景、年份、状态或 release"><table id="cases"><thead><tr><th>案例</th><th>类型</th><th>验收标签</th><th>核心大小</th><th>release</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    body+='<p>T550 总入口：<code>'+html.escape(receipt['library'])+'</code>。此目录用统一结构和导航链接组织完整备份，未移动原件。当前覆盖已登记 29 条记录；其他历史工程测试仍按旧审查记录追溯。</p>'
    body+='<script>document.getElementById("filter").addEventListener("input",function(){const q=this.value.toLowerCase();document.querySelectorAll("#cases tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))});</script>'
    (RESULTS/'00_案例总览.html').write_text(page('求解案例总览',body),encoding='utf-8')
    history=RESULTS/'history';history.mkdir(exist_ok=True)
    old=history/'README_before_20261123.md'
    if not old.exists():shutil.copy2(RESULTS/'README.md',old)
    readme='# 求解案例资料入口\n\n打开 [00_案例总览.html](00_案例总览.html)，按情景、年份和版本查找全部 29 条登记记录。\n\n'
    readme+='- `core_library_20261123/by_case/`：T550 预处理并逐文件 SHA 核验的统一轻量包；25 个生产案例和 1 个诊断案例各 21 个核心文件，字段一致。\n'
    readme+='- `core_case_summary.csv`：26 个完整解的年度汇总；用 kind 区分诊断与生产。\n- `case_catalog.json/csv`：本地入口、原备份和 T550 整理入口的对应表。\n'
    readme+='- 每案 `90_remote_files.csv`：全量原件路径、大小和 SHA；`91_remote_directories.json`：已有分析目录和文件位置。\n'
    readme+='- 失败尝试与排序测试仅保留身份和保全索引，明确无完整生产结果。Base 柔性关闭时同表保留条目，数值留空并标 DISABLED_BY_SCENARIO。\n\n'
    readme+=f'本轮统一核心文件约 {totalsize/1024**2:.2f} MiB，压缩回传 {receipt["archive_bytes"]/1024**2:.2f} MiB。未取回逐时数组、原 MPS、BarX/BarPi。\n\n'
    readme+='T550 统一入口：`'+receipt['library']+'`；每案含 `core/`、`full_backup/` 原件导航及 `analysis_links/` 分析导航。所有原备份和分析原位保留。\n\n'
    readme+='原 `by_case/`、`deliveries/` 和审查目录作为历史交付保留，旧脚本引用不失效；旧入口说明见 `history/README_before_20261123.md`。后续新案例应沿用本次核心模式，补齐全部适用条目再登记，原始大文件继续仅存 T550。\n\n'
    readme+='口径：年度约束影子值不等于完整负荷价格或结算价；启停表是连续容量等效次数；V2G 净调节不重复叠加放电量；本目录保留既有验收标签，不替作者采纳结果。\n'
    (RESULTS/'README.md').write_text(readme,encoding='utf-8')
    verification=dict(status='PASS',as_of_utc=datetime.now(timezone.utc).isoformat(),case_count=len(catalog),
        kinds=dict(Counter(c['kind'] for c in catalog)),verified_payload_files=filecount,verified_payload_bytes=totalsize,
        uniform_scientific_core_files=21,sha_match=True,core_schema_match=True,archive=receipt,
        exclusions=['No original large arrays, MPS, BarX, BarPi or full hourly CSV downloaded'],cases=validations)
    save(WORK/'local_library_verification.json',verification)
    print(json.dumps({k:v for k,v in verification.items() if k not in ('cases','archive')}))
    # Keep the user-facing entry points aligned with the approved paper names.
    import runpy
    naming=runpy.run_path(str(RESULTS/'rename_paper_navigation_20261124.py'))
    naming['local'](RESULTS,json.loads((RESULTS/'paper_scenarios.json').read_text(encoding='utf-8-sig')))


if __name__=='__main__':main()
