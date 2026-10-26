"""Document the verified launch; stage only this task's handoff addition."""
from pathlib import Path
import json
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
evidence=HERE/'deployment_v3'
r=json.loads((evidence/'startup_01.json').read_text(encoding='utf-8'))
assert r['job_id']=='5276703' and r['compute_node_smoke.json']['status']=='PASS'
assert r['v2_identity_reuse.json']['status']=='PASS'
summary='**2026-10-26 20:01 GMT：B2030 v3 已启动，Job5276703 RUNNING。** 源码仍9f0a042，479项源码/输入/冻结来源与v2逐字节一致、原门禁复用；新WLS路径字符串preflight PASS，未读取许可内容。m4cg1603实配64CPU/750G/billing64、48线程、UNLIMITED/no-requeue，Gurobi13.0.2启动smoke PASS，可用731.251629GiB。尚无Barrier轮次/最终RSS；既有日志持续记录，无后台监听。保留v1/v2及5276670失败备份，不碰5201318/5207165/case3 2050；后续年份仍等作者线程确认。'
details='''
### 2026-10-26 20:01 GMT：B2030 v3 新 WLS 启动通过

SUMMARY

- 模型源码 `9f0a042cbad241b13351b36dd68f3680666d42fb` 不变；部署工具提交 `ffc008b`。作者要求源码/冻结来源不变、不重跑门禁；本次复用481测试、身份门禁1/2和2030参数核准，未重新建模测试。479文件包括405源码、58输入、16个Base来源及补表，逐文件SHA与v2一致；FINAL_GATES_PASSED字节一致。
- release：`20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3`。payload SHA `689388ec11a8ca3e6ee7c64da96f9dcb9e99c2522ae4eadc6e589ed8ac61ce1c`；release清单 SHA `fc48114045304e4cbbb1f860e2378f2b4c4cec6a1d1b63914e0ff1938428a808`。启动脚本和launch元数据有变，新release总体SHA不冒称与v2相同。
- 按作者指定只读取得case3 2040 v2/continuation.sbatch，模板SHA `fa64961a54cd5094b8ddf5ebc342bb77f8e03841e4928a0285ce9bed4e61c0dc`。实查模板仍有旧许可fallback，已在执行中明确更正：新WLS登记与成功启动证据来自C2050 t40 WLS v2，B脚本显式使用该路径；只比较字符串，不读取/复制/散列许可。模板与逐行差异见deployment_v3/。
- 命令：`deploy_pilot_v3.py prepare`、`preflight`、`submit-release`；`collect_v3_performance.py --label startup_01`。新WLS路径字符串检查、全年输入preflight、bash语法、全部release SHA、held资源检查均通过，随即授权release。仅操作新作业5276703；原运行包不改写。
- 启动英国2026-10-26 20:01:42 GMT／北京10月27日04:01:42，20:01:50回读RUNNING、Restarts0。计算节点smoke PASS、启动可用731.251629GiB；资源记录在许可Env之前写入。sstat首次MaxRSS379216KiB（约0.362GiB）仅启动阶段快照，绝非全年峰值；当时无迭代记录、resource_usage未完成，最终RSS/每轮耗时/总轮数尚不可得。
- 后续性能由原 `output_8760/solver_telemetry.jsonl` 逐轮保存runtime，原 `gurobi.log`交叉核对；单次采集工具导出相邻轮runtime差CSV，首轮不把预处理时间算作迭代耗时，缺失不填零。进程峰值用终态 `/usr/bin/time -v` 的resource_usage，Slurm峰值另记。无后台监听/定时服务。新终态按10-20规则完整T550备份及扩展relative_v1验收；2040/2050/2060仍等待作者线程确认。
- 证据：`supplementary_materials/reviews/base_frozen_B_20261026/deployment_v3/{frozen_release,cloud_preflight,released_submission,startup_01}.json`，明确提交清单COMMIT_PATHS_v3_receipt.txt。保留未审核SI稿件及32行既有handoff，不将其纳入本轮Git。
'''.replace('SUMMARY',summary)
review=HERE/'REVIEW_ZH.md'
text=review.read_text(encoding='utf-8')
old='**当前状态：本地全部门禁和云端preflight通过；B2030作业5276670在旧许可检查失败，主模型未启动。失败记录已T550校验备份，下一步见第9节。**'
assert old in text
text=text.replace(old,'**当前状态：B2030 v3／Job5276703 已通过启动 smoke，RUNNING。启动可用731.25GiB，64CPU/750G，模型源码及门禁复用不变；见第10节。旧5276670失败证据和T550备份完整保留。**')
review.write_text(text+'\n## 10. B2030 v3 启动与性能记录\n'+details,encoding='utf-8')
status=REPO/'MODEL_SERVER_STATUS.md'
text=status.read_text(encoding='utf-8');pos=text.index('\n')+1
status.write_text(text[:pos]+'\n'+summary+'\n'+text[pos:],encoding='utf-8')
runbook=REPO/'SERVER_RUNBOOK.md'
with runbook.open('a',encoding='utf-8') as f:
    f.write('\n'+details+'\n后续 B 作业可从本次成功启动的 `base_frozen_2030_v3.sbatch` 派生，成功依据为deployment_v3/startup_01.json；仍须按目标年份核准其专属参数、路径和适用门禁。\n')
def update_handoff(text):
    marker='## Current validated snapshot\n'
    assert marker in text
    return text.replace(marker,marker+'\n- '+summary+'\n',1)+'\n'+details
handoff=REPO/'CODEX_HANDOFF.md'
handoff.write_text(update_handoff(handoff.read_text(encoding='utf-8')),encoding='utf-8')
# Stage only this addition on HEAD, preserving the unrelated 32 working-tree lines.
base=subprocess.check_output(['git','show','HEAD:CODEX_HANDOFF.md'],cwd=REPO).decode('utf-8')
staged=update_handoff(base).encode('utf-8')
blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=staged,cwd=REPO).decode().strip()
subprocess.run(['git','update-index','--cacheinfo','100644,'+blob+',CODEX_HANDOFF.md'],cwd=REPO,check=True)
print(summary)
