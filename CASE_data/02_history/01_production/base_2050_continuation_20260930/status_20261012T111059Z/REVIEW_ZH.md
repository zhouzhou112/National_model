# 2050 Base终态：716轮OPTIMAL，科学验收尚未全部通过

英国2026-10-12 12:10:59 BST（北京19:10:59）取证，12:12补查终态accounting：原作业4844528已COMPLETED/ExitCode0:0；完成时刻英国04:54:27（北京11:54:27），总作业运行11天13小时44分50秒。Gurobi已在716轮返回OPTIMAL，solve_report于英国04:44:02生成，求解runtime996416.018759秒（11.532593天）。原冻结配置48线程/Barrier/Crossover0/BarConvTol1e-4未改变。无需继续预计剩余求解时间。

|打印指标|682轮|716终轮|下降|
|---|---:|---:|---:|
|PInf|0.00118|0.000225|80.93%|
|DInf|4.39e-6|1.45e-6|66.97%|
|Compl|0.000338|6.01e-5|82.22%|
|abs(P-D)|26080.73|4631.44|82.24%|

原始目标5751972.505310521 million CNY、对偶目标5747341.065335428，callback相对差0.0008051916（0.08052%）。683 DInf升至5.08e-6后总体回落，697–702再反弹至7.71e-6，703→716逐轮回落，最终成功终止；不能因曾多次反弹推断必然失败，也不能将终轮打印值和callback残差混用或据此自行重构停止判据。终态callback PInf0.0006742307/DInf1.958688e-6与打印口径不同。717条iter0..716连续，源文件8份SHA核验通过；stderr两份0B。squeue不再存在该job与sstat无在跑step符合COMPLETED，不属于求解错误。

## 结果保全与验收

preservation_report.status=COMPLETE，各保全阶段均COMPLETE、errors=[]；已记录原始checkpoint、容量/成本、运行/碳/对偶QC、summary、candidate state、catalog与原始模型档案完成。dual_export_status.available=true，BarPi逐小时271560行、年度3366行，原件解释仍RAW_DUAL_PENDING_AUTHOR_REVIEW。此次只核验报告和小文件，不重算巨大MPS/BarPi/BarX的全文件SHA，也不据报告宣称所有大文件已重新逐一校验。探查output_catalog.json不存在；报告记录catalog阶段完成，不能把猜测的.json文件名不存在当作阶段失败。

归档冻结包仍使用FIXED_STAGE_A_PRIMAL_AND_DUAL_SPLIT_V1：solution_qc.status=HARD_FAIL、scientifically_accepted=false、author_decision=PENDING。物理hard_checks失败项为unidirectional_interprovincial_flow、reservoir_transition、objective_components；旧solver contract还因约束/对偶/互补绝对质量阈值未通过。旧质量最大ConstraintVio5.343391e-4/BoundVio3.130127e-6/DualVio8.340092e-4/DualResidual1.355445e-5/ComplVio13.17239，与Barrier打印残差是不同指标，不能混用。

遵循作者2026-10-10新规则，不以旧严格口径HARD_FAIL自动否决或启动Stage B。依据TASK_case3_launch_contract_20261010.md第6节仅对已具备证据的relative_v1项目进行独立只读对照，未改写云端solution_qc.json，也未宣布完整新口径通过：

|新口径项目|已归档观测量|本次对照|
|---|---|---|
|功率平衡|max2.6538425e-7GW=0.2654kW|低于1MW最低门槛，可通过|
|成本闭合|绝对9.668339e-5 million CNY，相对目标1.680874e-11|低于1e-7门槛，可通过|
|省际双向重叠|7333.475GWh；占gross交换电量0.001203426=0.1203426%|按归档gross交换定义，高于1e-4=0.01%门槛约12.03倍，未通过|
|水库水量平衡|max29.274762m³|缺站点逐小时残差及活动库容分母，尚不能按max(1m³,1e-6×该站活动库容)完整判定|

省际重叠额外损耗198.727559GWh，按作者要求单独披露，不能把方向性问题全部归为机器精度噪声。若采用其他交换电量分母，须明确与原gross口径的关系，不能为通过门槛自行更换。碳约束：年净排放-100.000000717MtCO2，上限-100MtCO2；上/下备用、惯量、容量裕度均为正，原物理检查通过。relative_v1正式双口径字段未在冻结归档中生成，完整终态验收仍未完成；最终接受状态不能由OPTIMAL代替。

## 复现与执行边界

`python analyze.py`仅离线读取本次冻结证据，核验8源SHA、717轮连续、solve_report和accounting终态一致、保全阶段与errors，输出summary.json及独立relative_v1对照。输入为scheduler.json/terminal_scheduler.json所列命令与文件、682轮快照及convergence_eta_20261004/estimate.py；不调用求解器。原日志/telemetry/采集脚本留本地/云端，sha256.json为本地原字节清单，不保证未发布原件随Git可得。

Git基准a4d47278b0cb18422dc7b5726b334fa045bc2169。新增本次小文件并追加CODEX_HANDOFF.md/MODEL_SERVER_STATUS.md/SERVER_RUNBOOK.md；交接中另一个SI任务的未提交记录保留工作区，使用索引patch只提交本次新增条目，不将其文稿/图件/交接提交。其他作者MODEL_V0719_REVIEW_REPORT.md未审核改动保留。无scontrol/scancel、原模型/配置/数据/作业或归档修改、Stage B、新作业、部署或后台监听。

下一步是按作者新口径完成科学验收：复核水库逐站相对残差与省际重叠问题、正式记录双口径，不把未经接受的candidate state当作已经验收的续接状态。本次仅报告与只读对照，不启动2060或case3全年任务。
