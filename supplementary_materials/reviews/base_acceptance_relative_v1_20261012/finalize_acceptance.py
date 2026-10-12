"""Write explicit author acceptance sidecars after all three offline passes.

Source archives and candidate metadata are immutable. Server writes are confined
to sibling acceptance directories, never output_8760. Re-running verifies bytes.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import subprocess
from assess_on_t550 import SSH

HERE=Path(__file__).resolve().parent

def main():
    records={};table=[]
    for year in [2030,2040,2050]:
        root=HERE/'assessments'/str(year)
        evidence=json.loads((root/'evidence_manifest.json').read_text())
        assessment=json.loads((root/'solution_qc_relative_v1.json').read_text())
        profile=assessment['acceptance_profiles']['relative_v1']
        assert profile['status']=='PASS' and profile['checks']['reservoir_transition']['disclosure_complete']
        assert profile['dual']['BarConvTol']==1e-4
        for name,digest in evidence['source_sha256'].items():
            local=HERE/'evidence'/str(year)/name
            if local.exists():assert hashlib.sha256(local.read_bytes()).hexdigest()==digest,name
        qc=json.loads((HERE/'evidence'/str(year)/'solution_qc.json').read_text())
        record=dict(author_decision='ACCEPTED_RELATIVE_V1_20261012',planning_year=year,
            scenario_id='base',assessment=profile,source_evidence=evidence,
            assessment_sha256=hashlib.sha256((root/'solution_qc_relative_v1.json').read_bytes()).hexdigest(),
            source_candidate_flags_unchanged=True,frozen_archive_unchanged=True,
            effective_author_rule='AGENTS.md author decisions 2026-10-10 and 2026-10-12',
            generated_at=datetime.now(timezone.utc).isoformat())
        path=root/'acceptance_relative_v1.json'
        if not path.exists():path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        records[evidence['sidecar']+'/acceptance_relative_v1.json']=path.read_text(encoding='utf-8')
        c=profile['checks'];water=c['reservoir_transition']
        table.append(f"| {year} | {', '.join(k for k,v in qc['hard_checks'].items() if not v)} | PASS | {c['power_balance']['maximum_residual_gw']:.9g} | {c['objective_components']['relative_residual']:.9g} | {c['unidirectional_interprovincial_flow']['extra_loss_share_of_load']:.9g} | {water['maximum_residual_m3']:.9g} |")
    code='records='+repr(records)+'\n'+'''from pathlib import Path
import hashlib,json
result={}
for name,content in records.items():
    path=Path(name)
    assert path.parent.name=='acceptance_relative_v1_20261012'
    if path.exists():assert path.read_text()==content
    else:path.write_text(content)
    result[name]=hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps(result))
'''
    text='''# Base 2030/2040/2050 正式验收（2026-10-12）

作者决定 `ACCEPTED_RELATIVE_V1_20261012`：三年均通过修订后的 relative_v1。冻结归档和原 candidate 标记不变，验收 JSON 作为旁置证据保存。固定服务器每个 release 的 `acceptance_relative_v1_20261012/` 已有离线 assessment；正式验收 JSON 的同步结果以 `acceptance_sync_status.json` 为准。

| 年份 | 原严格失败项（保留） | relative_v1 | 最大功率残差 GW | 成本闭合相对残差 | 双向流额外损耗/系统负荷 | 最大水量残差 m³（暂缓） |
|---|---|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

水量项按作者决定暂缓逐站判定；站点、小时及活动库容见每年的 `assessments/<year>/acceptance_relative_v1.json`。小于 1 MW 新建量、储能充放电、火电启停与双向流重叠、历史 bound-close 和数值清理披露均保存在对应 assessment 中。省际结果报告净流。工程对偶等级为 `BARRIER_DUAL_ENGINEERING_GRADE`，BarConvTol=1e-4。

执行：`collect_evidence.py` 核对云端小文件；`assess_on_t550.py` 在已核验 T1 备份上运行独立离线评估，不重启备份；`finalize_acceptance.py` 在三年全部 PASS 后写正式记录。各证据 SHA 见 `evidence_manifest.json`、`collection_manifest.json` 与 `acceptance_server_sha256.json`，可追溯回各冻结 `result_manifest.json`。没有原 manifest 条目的文件（包括 manifest 本身）通过两端 SHA 核对。水库逐时残差从原 npz 重算并与原 QC 最大值一致。

差异：无新增科学判据；严格口径仍为 HARD_FAIL，作者验收为独立旁置记录，不伪装成历史严格 QC 已通过。
'''
    report_path=HERE/'REVIEW_ZH.md'
    marker='## 2026-10-12 续办：三年正式验收'
    if marker not in report_path.read_text(encoding='utf-8'):
        with report_path.open('a',encoding='utf-8') as handle:
            handle.write('\n\n'+marker+'\n\n'+text)
    try:
        p=subprocess.run(SSH+['python3 -'],input=code,capture_output=True,text=True,encoding='utf-8',timeout=60)
        if p.returncode:raise RuntimeError(p.stderr)
        (HERE/'acceptance_server_sha256.json').write_text(p.stdout,encoding='utf-8')
        status=dict(status='VERIFIED',server_sha256=json.loads(p.stdout))
    except Exception as error:
        status=dict(status='PENDING_CONNECTION',error=str(error),local_acceptance_complete=True)
    (HERE/'acceptance_sync_status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    if status['status']!='VERIFIED':raise RuntimeError(status['error'])
    print('Three acceptance sidecars written and server SHA verified.')

if __name__=='__main__':main()
