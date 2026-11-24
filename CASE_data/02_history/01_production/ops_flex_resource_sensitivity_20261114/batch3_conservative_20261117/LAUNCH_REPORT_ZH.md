# OPS-Conservative 2030/2040/2060 放行报告（2026-11-17）

三案各自门禁与preflight全部PASS，已按作者本次提前授权提交并release。核对时云端1运行+3排队，总计4项；LATE-Open2060未提交。

| 年份 | Job ID | 状态 | Gate / preflight |
|---|---|---|---|
| 2030 | 5613302 | PENDING（已release） | PASS / PASS |
| 2040 | 5613303 | PENDING（已release） | PASS / PASS |
| 2060 | 5613360 | PENDING（已release） | PASS / PASS |

队列核对时间：2026-11-17T12:49:40.263885Z。排队原因为调度优先级，当前未分配节点；AllocTRES和≥700 GiB启动可用内存尚待实际启动，不能提前记为通过。原LATE-Open2050（5587177）继续运行。

## 门禁与来源

详见 [提交前门禁](PRE_SUBMISSION_REPORT_ZH.md) 及各年 FINAL_YEAR_RELEASE_GATES.json。保守输入11文件本地/T550/云端SHA核验通过，使用Claude原输入、不生成或修补。原B冻结来源、上游与最小静态闭合逐文件复核，未重新闭合。三案新1h生产profile构建PASS；既有24h保守/原B/中性/开放/零签约对照源码与输入未变，回读远端结果并按原件内容和SHA绑定引用。逐项冻结容量最大误差5.68e-14 GW，低于1e-9门槛；中性/单调性通过。537项回归覆盖的模型源码LF SHA一致，未重复执行未变化的回归。

2030短窗沿用10.95890410958904 Mt（本次消息小数截断至10.958904109589）；全年4000 Mt及其他年份年度碳上限不变。2040/2060短窗仍用各自Base原同窗净排放×(1+1e-4)。全年命令不包含工程短窗覆盖入口。

新release源码commit为f75fb4f2；从最近成功启动的OPS-Open2030（5591162）原脚本派生，模板SHA见cloud_recheck.json，各案template_diff.patch记录仅作业名、年份/情景/本案路径等变化。三个脚本均在本轮首次提交前生成。冻结文件分别550/534/534件，manifest SHA见LAUNCH_RECEIPT.json。提交前再次sha256sum全清单，通过后sbatch --hold核验资源/目录，再按作者明确授权release。

资源：Gurobi44线程，Slurm64CPU/750G/billing64/UNLIMITED/no-requeue；启动脚本检查AllocTRES、可用内存≥700GiB、许可路径字符串一致及小模型smoke。未读取凭据内容。

## 后续检查点

下一次状态查询先读取三项启动资源、smoke、全年结构审计（四项服务合同上限须与任务书1.4全年表核对）。未通过时停止该案并报告，不自动重提。当前排队无需重复prepare/submit。

结束后按5%磁盘余量规则完整备份至T550，relative_v1验收、原MPS行序与自身BarPi恢复年度核算行对偶、只读分析并取小文件。已知年度对偶导出缺陷仍用旁置恢复，不改本次或其他冻结输出。所有失败与原结果完整保留，无后台监听。

LATE-Open2060仍须LATE-Open2050验收且B/obj≤1e-2，并由作者另行确认；本轮授权不包含它。OPS-Open2030/2040/2060作者采纳已登记case_catalog。
