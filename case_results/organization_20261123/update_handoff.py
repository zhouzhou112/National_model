"""Append this task's evidence while preserving unrelated handoff edits.

Also prepares HEAD-based versions for selective Git staging of mixed documents.
"""
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
A=ROOT/'supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114/acceptance_late2060_20261123'
FRONT='- **2026-11-23 22:17UTC：LATE-Open2060条件验收收尾及全案例资料整理均完成。此前21:47的镜像/回读待办已于21:54补齐（closeout_verification=PASS）。T550 case_library_v2_20261123统一导航29条记录；25生产+1诊断各21核心文件，另2失败+1测试明确不适用。本地case_results/00_案例总览.html为总入口，统一核心约19.99MiB、压缩回传4.83MiB；590件SHA一致、594本地链接及111远端导航链接通过。大模型、逐时数组及分析留T550，原件未移动/删除，无新求解/监听。详见case_results/organization_20261123/REPORT_ZH.md。**\n\n'
HISTORY='''### 2026-11-23 — 统一 T550 全量导航与本地轻量核心库

- 起始 Git e91bd892；用户明确要求 T550 全量有序、本地只取 T550 预处理核心文件，并逐案对齐条目。模型、参数、release 和原输出未改。
- 旧 LATE-Open2060 报告同步与验收 JSON 回读于21:54:18UTC完成，原108件统计不变。该事实补正本日早先“镜像待完成”快照；既有历史保留。
- 从case_catalog登记29案、核全部备份COMPLETE。新T550根case_library_v2_20261123下按case/year/release组织，core/放派生小表、full_backup/和analysis_links/为导航符号链接，原目标未改写。v1整理尝试因重复解压低效停止，部分派生及旧脚本保留；v2只缓存数组，不改公式。
- 命令：prepare_library.py；T550 Python build_library_on_t550.py；仅scp core_library.tar.gz与receipt；install_local_library.py、verify_navigation.py；T550 verify_remote_library.py。26完整解同21核心文件/相同CSV字段，服务31×4条；按既有V5服务池公式闭合≤1e-6GW，弃电/储能汇总与原年度表吻合，所有读取源件SHA一致。Base关闭柔性显式不适用，失败/测试不混入生产比较。
- 590交付文件20956260bytes，压缩5064080bytes；archive SHA 15c4db7c30ff63c9730d3f3a24883c54435e301ba93b262dff5f8a0627cef03e。全部SHA匹配，30页/594本地链接通过；22:17:37UTC远端590件再核、111导航链接及原备份manifest通过，报告镜像SHA匹配。
- 本地入口case_results/00_案例总览.html；逐案核心core_library_20261123，core_case_summary.csv/core_coverage.csv供比较与缺项核查；远端原件路径与大小/SHA在90_remote_files.csv，既有分析目录在91_remote_directories.json。旧by_case、deliveries及审查目录保留引用，生成核心不入Git，仅明确清单的小型代码/报告/台账入Git。
- 证据：case_results/organization_20261123/{local_library_verification,navigation_verification,remote_closeout_verification}.json；报告REPORT_ZH.md。下一步为作者审阅LATE-Open2060条件验收结果；不自动放开重解或新增作业。后续完成案例按同模式补齐适用核心文件、SHA和总览。

'''
RUNBOOK='''## 全量与轻量案例资料统一入口（2026-11-23）

T550统一入口`/home/zz2/National_model_server/case_library_v2_20261123/INDEX_ZH.md`，按case/year/release排列。每案`core/`为统一预处理文件，`full_backup/`与`analysis_links/`仅为原备份/分析导航符号链接；不通过链接修改原件。当前29登记案，26完整解每案同21核心文件。

本机入口`case_results/00_案例总览.html`，数据在`core_library_20261123/`。原模型/逐时数组/BarX/BarPi不回本机；`90_remote_files.csv`和`91_remote_directories.json`保留远端路径与索引。后续按同核心schema补齐全部适用条目、SHA核验并登记；旧交付保留。有限脚本及收据见`case_results/organization_20261123/`。

LATE-Open2060备份与条件验收均完成，21:54UTC报告同步/回读PASS，不再续传旧备份或重算验收。全部原件保全，无后台监听。

'''


def insert_front(text,name,front,history=''):
    if name=='CODEX_HANDOFF.md':
        text=text.replace('## Current validated snapshot\n\n','## Current validated snapshot\n\n'+front,1)
        if history:text=text.replace('## Version history\n\n','## Version history\n\n'+history,1)
        return text
    head,tail=text.split('\n\n',1)
    return head+'\n\n'+front+tail


def main():
    earlier=json.loads((A/'handoff_additions.json').read_text())
    projection=WORK/'stage_projection';projection.mkdir(exist_ok=True)
    for name in ['CODEX_HANDOFF.md','MODEL_SERVER_STATUS.md','CLOUD_BACKUP_REGISTER_ZH.md','SERVER_RUNBOOK.md']:
        work=(ROOT/name).read_text(encoding='utf-8-sig')
        front=RUNBOOK if name=='SERVER_RUNBOOK.md' else FRONT
        hist=HISTORY if name=='CODEX_HANDOFF.md' else ''
        if front not in work:(ROOT/name).write_text(insert_front(work,name,front,hist),encoding='utf-8')
        head=subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT).decode('utf-8')
        if name in earlier:
            head=insert_front(head,name,earlier[name]['front'],earlier[name]['history'])
        head=insert_front(head,name,front,hist)
        (projection/name).write_bytes(head.replace('\r\n','\n').encode('utf-8'))
    print('Prepared four additive handoff updates and isolated staging versions.')


if __name__=='__main__':main()
