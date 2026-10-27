"""Record reviewed launch evidence without staging another session's handoff edits."""
from pathlib import Path
import json,subprocess,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
rows=read(HERE/'QUALIFIED_GATES_SUMMARY.json')
snapshot=sorted(HERE.glob('cloud_status_*.json'))[-1];state=read(snapshot)
names={5207165:'C2050',5294579:'Case3 2050',5297384:'B2040',5297390:'B2050',5297410:'B2060 v2'}
active=state['active_jobs'];nr=sum(r['state']=='RUNNING' for r in active)
np=sum(r['state']=='PENDING' for r in active)
summary=f'**2026-10-27 第二批 B 放行：** 云端快照 {state["utc"]} 为 {nr} RUNNING、{np} PENDING。B2040/5297384、B2050/5297390 已 release 且启动 smoke PASS；B2060 v2/5297410 已 release 且启动 smoke PASS。三年云端一致映射 1h/3×24h、目标/双向交叉可行/成本门禁 PASS，年度碳上限不变。首次 B2060/5295127 构建闭合核验 FAILED，已完整保全现存文件并 T550 SHA 备份；不是解。'
table='|项目|Job|状态|运行时间|Barrier轮次|PInf|DInf|Compl|\n|---|---|---|---|---|---|---|---|\n'
for r in active:
 e=r['barrier_last_11'][-1] if r['barrier_last_11'] else {}
 vals=[names.get(int(r['job_id']),r['name']),r['job_id'],r['state'],r['elapsed']]+[str(e.get(k,'—')) for k in ['iteration','primal_infeasibility','dual_infeasibility','complementarity']]
 table+='|'+'|'.join(vals)+'|\n'
gate='|年|闭合行|网络增加 MW|bio减少 W|年固定成本净增 CNY|24h碳上限 Mt|目标相对差|最大交叉违反|\n|---|---|---|---|---|---|---|---|\n'
for r in rows:gate+='|'+'|'.join(str(r[k]) for k in ['year','rows','network_add_mw','bio_reduction_w','cost_cny','budgets','objective_difference','max_cross_violation'])+'|\n'
backup=read(HERE/'B2060_v1_failure_backup.json')
tests='原模型源码完整本地回归 492 项通过（1 跳过），本轮模型源码未改；冻结相关 19 项和窗口碳核算 2 项通过。T550 第一轮缺测试夹具/Git 元数据，第二轮 492 项仅缺 source_screen.csv 一项报错（2 跳过）；该7.47MB夹具补传期间T550再次SSH握手超时，尚未完成目标SHA和定向重测；此项保持待办，不将失败日志改写为成功。'
report=f'''# 框架 B 第二批独立放行与生产映射核验

{summary}

## 当前云端项目

{table}
状态读取文件：{snapshot.name}。新 B 作业仍可能处于构建/排队，启动检查通过不是全年求解成功；不推断 ETA。5207165、5294579 仅只读。

## 本轮修正与来源

Windows scipy1.13.1 与原 Base 生产云端 scipy1.15.3 的等距离最近邻 PV fallback 有 25 个映射差异；T550 scipy1.17.1 的映射与云端逐项一致。数据表 SHA 无漂移。旧本地闭合审计中的多数较大网络调整是此环境差异造成，不是应当增加的物理容量。本轮没有修改最近邻规则、模型核心源码或科学容差；在新目录按原云端映射重新审计、逐行最小闭合，完整保留旧审计和失败运行。新 release 增加 fallback 全映射 preflight，必须与合格门禁映射相同。

首次 B2060 使用旧本地审计（源码80b5c3c），5295127运行44:07后在 apply_static_closure 来源核验报 Diagnosed row is not a positive finite gap，未进入 Barrier、无解。新 B2060 v2 在旧作业终态确认后才提交，未取消/修改/覆盖旧运行。新三年 release 源码 cdd833381b81acbb726bcc8aa9551013c2569344，sbatch 从 B2030 v3 派生，48线程/64CPU/750G/billing64/UNLIMITED/no-requeue，WLS仅核对路径字符串。

## 碳窗口与闭合门禁

{gate}
三年使用各自 Base2040/2050/2060 验收解及原上游（不串联 B 状态）。从原 thermal_dispatch.npz 逐时毛发电按模型因子核算净排放，包含 CCS/BECCS，DAC 按模型固定年度吞吐率分摊至24小时；窗口 hour_index=0..23。Base同窗净排放分别6.787488523830012、2.230911157033998、-0.8457527370979387 Mt，乘1.0001；负数也严格使用作者公式。三侧使用同一窗口上限，年度上限不变，生产 sbatch 无窗口 override。

原 Base 逐时文件、annual_carbon、DAC、input_manifest及相关因子表SHA验证；2040/2050全年碳重构差分别1.02318e-11/-1.20792e-12 Mt。逐列审计中只有授权投资 BOUNDS_OTHER 改变，原冻结CSV字节不变，目标/系数/RHS身份保持。没有启用 [Base,Base+1e-3 GW] 余量回退。完整模型/解在 T550 isolated repo 各年 cloud_identity_v2；本地各年 cloud_identity_v2_t550 是 SHA核验后的小证据副本。旧本地12/13/43行及旧成本只保留作历史，不再作为新生产输入。

## 验证和保全

{tests}

首次B2060失败备份：{len(backup['files'])}文件、{backup['bytes']} bytes，逐文件SHA、source_unchanged=True，剩余{backup['free_fraction']:.4%}。目标 {backup['destination']}；范围 PARTIAL_BUILD_FAILURE_NO_SOLUTION。云端全部原文件保留；无原模型归档/完整解可供备份，不能称已解结果备份。

## 复用入口与下一步

命令均在工程根目录运行，审计脚本在本目录：

- collect_cloud_status.py：一次只读快照，不监听。
- deploy_authorized.py B2040|B2050|B2060 status（B2060 加 --version 2）：核对启动；其他阶段不可盲目重跑。
- 发现终态后先核对导出/保全、backup_manifest、全局锁与已有进程。将本目录及 scripts/backup_completed_cloud.py 同步到独立 T550 工具目录，再运行 backup_B_completed.py plan|run --config <year>_backup_config.json。原模型/BarX/BarPi/全部output及显式闭合、映射、门禁元数据均备份；至少30%空间、逐文件SHA、源身份不变才完成。
- 完整备份后 postprocess_B.py B2040|B2050|B2060 collect，取回与 nocredit 同口径全部≤32MiB小文件；assess 做扩展relative_v1，全年Mt分母 annual_fossil_unabated_emissions_mtco2，验收JSON旁置T550并回传本地。原QC保留，不因FAIL丢解。

没有建立后台监听；上述收尾在人工查询发现终态时执行。新B尚未求解结束，当前没有新B全年验收JSON；不能把24h门禁PASS当作全年验收。其他会话 SI 修改保留、不提交、不修改 modules 或在线LaTeX。
'''
(HERE/'REVIEW_ZH.md').write_text(report,encoding='utf-8')
for year in [2040,2050,2060]:
 v=2 if year==2060 else 1
 release=f'20261027_basefrozen_{year}_v9a12_agg0_t48_m750_tol1e4_v{v}'
 save(HERE/f'{year}_backup_config.json',dict(operation=f'20261027_B{year}_v{v}_completed',releases=[release],destination='/home/zz2/National_model_server/cloud_backup',source='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud',ssh_config='/home/zz2/.ssh/paracloud_backup_20261012/ssh_config',minimum_free_fraction=.30,authorization='Author 2026-10-20 and 2026-10-27: full terminal backup, acceptance and nocredit-equivalent small files; no monitoring'))
entry='\n\n## 2026-10-27 第二批 B 独立放行、生产映射修正与失败保全\n\n'+summary+'\n\n源码80b5c3c→3019462→d14206c→cdd8333；核心模型源码沿用已测版本，本轮修改review助手、作者AGENTS、审计/部署/交接。Windows与生产25个PV最近邻平局选择不同；T550与云端一致，按云端重生成8/12/40行最小闭合，净增成本20.5763/47.0188/243.7888 CNY/yr。三年窗口碳门禁与年度身份通过，生产仅用年度上限。完整命令、环境版本、SHA、测试及未解决项见 supplementary_materials/reviews/base_frozen_batch2_20261027/REVIEW_ZH.md、QUALIFIED_GATES_SUMMARY.json、各年cloud_identity_v2_t550及deployment。\n\n首次5295127失败包T550已备份14,503,317bytes，source unchanged、SHA全过；不是完整解备份。后续新B终态按备份→扩展验收→小文件取回执行，入口backup_B_completed.py/postprocess_B.py，各年config已准备，当前没有新B全年验收。无后台监听、无保护作业/SI修改。\n'
handoff=ROOT/'CODEX_HANDOFF.md';head=subprocess.check_output(['git','show','HEAD:CODEX_HANDOFF.md'],cwd=ROOT).decode('utf-8')
def amend(text):return text.replace('## Current validated snapshot\n','## Current validated snapshot\n\n- '+summary+'\n',1)+entry
working=handoff.read_text(encoding='utf-8');assert '## 2026-10-27 第二批 B 独立放行、生产映射修正与失败保全' not in working
handoff.write_text(amend(working),encoding='utf-8')
blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=amend(head).encode(),cwd=ROOT).decode().strip()
subprocess.check_call(['git','update-index','--cacheinfo','100644',blob,'CODEX_HANDOFF.md'],cwd=ROOT)
server=ROOT/'MODEL_SERVER_STATUS.md';text=server.read_text(encoding='utf-8');first,rest=text.split('\n',1);server.write_text(first+'\n\n'+summary+'\n'+rest+entry,encoding='utf-8')
runbook=ROOT/'SERVER_RUNBOOK.md';runbook.write_text(runbook.read_text(encoding='utf-8')+entry,encoding='utf-8')
print(summary)
