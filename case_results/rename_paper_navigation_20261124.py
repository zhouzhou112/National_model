"""Apply approved paper names to navigation; preserve all hashed core payloads.

Local: python case_results/rename_paper_navigation_20261124.py
T550: python rename_paper_navigation_20261124.py --remote ROOT --mapping FILE
"""
import argparse
import ast
import csv
import hashlib
import html
import json
import os
import shutil
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def renamed_html(text,old,new,definition):
    text=text.replace('<title>'+html.escape(old)+'</title>','<title>'+html.escape(new)+'</title>')
    text=text.replace('<h1>'+html.escape(old)+'</h1>','<h1>'+html.escape(new)+'</h1>')
    marker='<!-- paper-name-20261124 -->'
    if marker not in text:
        text=text.replace('</h1>','</h1>'+marker+'<p>'+html.escape(definition)+'；历史代号：'+html.escape(old.split()[0])+'。原始 release 与数据身份保持不变。</p>',1)
    return text


def verify_core(lib,cases):
    files=0
    for c in cases:
        p=lib/c['relative_directory'];m=json.loads((p/'core_manifest.json').read_text())
        for name,info in m['files'].items():
            assert sha(p/name)==info['sha256'],p/name
            files+=1
    return files


def remote(root,config):
    cases=json.loads((root/'catalog.json').read_text())['cases'];before=verify_core(root,cases)
    rows=[]
    for c in cases:
        legacy=c['case'];name=config['mapping'][legacy]
        original=root/c['relative_directory'];view=root/'by_paper_scenario'/name/str(c['year'])/c['release']
        view.mkdir(parents=True,exist_ok=True)
        for target,link in [(original,'archive'),(original/'core','core')]:
            p=view/link
            if p.is_symlink():assert p.resolve()==target.resolve()
            else:assert not p.exists();p.symlink_to(target,target_is_directory=True)
        (view/'README.md').write_text(f'# {name} {c["year"]}\n\n{config["definitions_zh"][name]}。\n\n历史代号 `{legacy}`；原始 release `{c["release"]}`。\n\n[核心小文件](core/) · [原归档、完整备份与分析入口](archive/)\n',encoding='utf-8')
        rows.append(dict(paper_scenario=name,legacy_case=legacy,year=c['year'],release=c['release'],
            kind=c['kind'],acceptance=c['acceptance'],paper_directory=str(view),original_directory=str(original)))
    index=root/'INDEX_ZH.md';history=root/'history';history.mkdir(exist_ok=True)
    previous=history/'INDEX_before_paper_names_20261124.md'
    if not previous.exists():shutil.copy2(index,previous)
    lines=['# T550 案例资料库：论文正式情景名','',
           '正式名称 REF / OPS / LATE / PLAN / PLAN-NC；资源敏感性保留 Open / Conservative 后缀。原件保持原位，旧代号仅用于溯源。','',
           '| 正式情景 | 年份 | 历史代号 | 类型 | 验收 | 入口 |','|---|---:|---|---|---|---|']
    for r in sorted(rows,key=lambda r:(r['paper_scenario'],r['year'],r['release'])):
        rel=Path(r['paper_directory']).relative_to(root)
        lines.append(f'| {r["paper_scenario"]} | {r["year"]} | {r["legacy_case"]} | {r["kind"]} | {r["acceptance"]} | [核心与全量导航]({rel}/README.md) |')
    index.write_text('\n'.join(lines)+'\n',encoding='utf-8');save(root/'paper_catalog.json',dict(cases=rows));save(root/'paper_scenarios.json',config)
    after=verify_core(root,cases);assert before==after
    receipt=dict(status='PASS',cases=len(rows),original_payload_files_sha_verified=after,navigation_links=2*len(rows),
                 root=str(root),mapping=config['mapping'],as_of_utc=datetime.now(timezone.utc).isoformat(),originals_renamed=False)
    save(root/'paper_naming_verification_20261124.json',receipt);print(json.dumps(receipt))


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.links.extend(v for k,v in attrs if k=='href')


def local(results,config):
    repo=results.parent;lib=results/'core_library_20261123';work=results/'naming_20261124';work.mkdir(exist_ok=True)
    # Read the approved paper map as literal data, without importing plotting code.
    authority=repo.parent/'claude_workspace/paper/common/figstyle_paper.py'
    tree=ast.parse(authority.read_text(encoding='utf-8-sig'));official=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SCENARIO_LABEL' for t in node.targets):official=ast.literal_eval(node.value)
    assert official=={'Base':'REF','B':'OPS','C':'LATE','A':'PLAN','nocredit':'PLAN-NC'}
    for old,paper in official.items():assert config['mapping']['Case3' if old=='A' else old]==paper
    cases=json.loads((lib/'catalog.json').read_text())['cases'];before=verify_core(lib,cases)
    catalog=json.loads((results/'case_catalog.json').read_text(encoding='utf-8-sig'));lookup={c['release']:c for c in catalog['cases']}
    rootpage=results/'00_案例总览.html';text=rootpage.read_text(encoding='utf-8')
    backup=results/'history/00_案例总览_before_paper_names_20261124.html'
    if not backup.exists():shutil.copy2(rootpage,backup)
    pages=[];paper_rows=[]
    for c in cases:
        legacy=c['case'];paper=config['mapping'][legacy];old=f'{legacy} {c["year"]}';new=f'{paper} {c["year"]}'
        original=lib/c['relative_directory'];view=results/'by_paper_scenario'/paper/str(c['year'])/c['release'];view.mkdir(parents=True,exist_ok=True)
        original_page=original/'index.html';old_html=original_page.read_text(encoding='utf-8');updated=renamed_html(old_html,old,new,config['definitions_zh'][paper]);original_page.write_text(updated,encoding='utf-8')
        prefix=os.path.relpath(original/'core',view).replace('\\','/')+'/'
        (view/'index.html').write_text(updated.replace('href="core/','href="'+quote(prefix,safe='/') ),encoding='utf-8')
        # The source page uses only core-relative file hyperlinks.
        pages.extend([original_page,view/'index.html'])
        rel=str(view.relative_to(results)).replace('\\','/')
        old_href='core_library_20261123/'+c['relative_directory']+'/index.html'
        text=text.replace('href="'+old_href+'">'+old+'</a>','href="'+rel+'/index.html">'+new+'</a>')
        text=text.replace('REF / 无柔性基准','无付费终端柔性的参考路径').replace('OPS-Central / Base-frozen（框架 B）','固定 REF 设施、采购并调用柔性').replace('LATE-Central（框架 C）','2050 年起纳入柔性规划').replace('PLAN / Flex-coopt（框架 A）','2030 年起联合规划')
        entry=lookup[c['release']];entry.update(paper_scenario=paper,legacy_case=legacy,
            paper_directory=str(view.relative_to(repo)).replace('\\','/'),paper_index=str((view/'index.html').relative_to(repo)).replace('\\','/'))
        card=repo/entry['case_card'];s=card.read_text(encoding='utf-8-sig');s=s.replace('最新统一核心入口：['+old+']','最新统一核心入口：['+new+']')
        marker='<!-- paper-name-20261124 -->'
        if marker not in s:s=marker+'\n论文正式名称：**'+new+'**；历史代号：`'+legacy+'`。\n\n'+s
        card.write_text(s,encoding='utf-8')
        paper_rows.append(dict(paper_scenario=paper,year=c['year'],legacy_case=legacy,kind=c['kind'],release=c['release'],local_directory=str(view),original_core_directory=str(original/'core')))
    note='目录名 B 是历史框架 B（OPS-Central），不等同于资源情景的“基准 B”。Base 对应 REF，Case3 对应 PLAN，C 对应中央 LATE。'
    text=text.replace(note,'主要入口采用论文正式名：REF、OPS、LATE、PLAN、PLAN-NC。资源情景 Conservative、Base、Open 与规划路径分开；历史目录代号 B 对应 OPS，历史 Base 对应 REF。')
    text=text.replace('Base 的柔性服务明确为不适用','REF 的柔性服务明确为不适用')
    rootpage.write_text(text,encoding='utf-8');pages.append(rootpage)
    save(results/'case_catalog.json',catalog);save(results/'paper_catalog.json',dict(cases=paper_rows))
    # Add explicit names; keep the old case key for existing readers.
    for filename in ('case_catalog.csv','core_case_summary.csv','core_coverage.csv'):
        p=results/filename
        with p.open(encoding='utf-8-sig',newline='') as stream:reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        fields=['paper_scenario','legacy_case']+[f for f in fields if f not in ('paper_scenario','legacy_case')]
        for r in rows:r.update(paper_scenario=config['mapping'][r['case']],legacy_case=r['case'])
        with p.open('w',encoding='utf-8-sig',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    readme=results/'README.md';s=readme.read_text(encoding='utf-8');marker='<!-- paper-name-20261124 -->'
    if marker not in s:s=s.replace('\n\n','\n\n'+marker+'\n主要分类入口为 `by_paper_scenario/REF、OPS、LATE、PLAN、PLAN-NC/`，以及保留后缀的资源敏感性案例。正式名见 `paper_scenarios.json`；旧 `case` 字段/原件目录保持身份，新表增加 `paper_scenario` 与 `legacy_case`。\n\n',1)
    readme.write_text(s,encoding='utf-8')
    links=0
    for p in pages:
        parser=Links();parser.feed(p.read_text(encoding='utf-8'))
        for href in parser.links:assert (p.parent/unquote(href)).resolve().exists(),(p,href);links+=1
    assert verify_core(lib,cases)==before
    receipt=dict(status='PASS',cases=len(cases),pages=len(pages),local_links_checked=links,original_payload_files_sha_verified=before,
        authority_path=str(authority),authority_sha256=sha(authority),mapping=config['mapping'],originals_renamed=False,
        remote_status='PENDING',as_of_utc=datetime.now(timezone.utc).isoformat())
    save(work/'local_verification.json',receipt);print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--remote');ap.add_argument('--mapping');a=ap.parse_args()
    path=Path(a.mapping) if a.mapping else Path(__file__).resolve().parent/'paper_scenarios.json'
    config=json.loads(path.read_text(encoding='utf-8-sig'))
    if a.remote:remote(Path(a.remote),config)
    else:local(Path(__file__).resolve().parent,config)
