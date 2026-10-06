# 8760h 对偶初筛五轮 Factor 配对验证（2026-10-05）

状态：两个授权作业已held提交、核验并放行；F=4981130、S=4981131，均RUNNING。尚无全年 Barrier 成本判定。

## 预注册边界

仅 case3_thermal_ev_v5、2030、2025共同边界、8760h/start0。F完整候选；S按 grid_uid × technology 一对一精确对齐源CSV，仅将 rc_ratio≥0.2 且当前headroom>0的 vre_new 上界设0。时间/空间/单位/成本/其余约束均沿用V9。48求解线程、64 CPU/750G、amd_a8_768、无限作业时限、BarIterLimit5、无TimeLimit/SoftMemLimit。所有输出 TEST_ONLY_FACTOR_SCREEN、scientific_acceptance_mode=NONE，不QC、不导出解/状态。

第2–5轮平均时间比≤75%且Dense cols明显下降才通过；75%–90%封存；>90%未达到通过标准亦封存；Dense cols未明显下降则无论时间如何封存。若证据不足，标记待判，不将缺测解释为成功或失败。5轮仅测每轮代价，不评价收敛或全年提速倍数。

## 已完成证据

|门禁|证据|结果|
|---|---|---|
|源代码身份|cloud_source_repo_sha256.json / frozen_local_sha256.json|云V9 196个py/json/csv/sh/sbatch源码文件；本地起始快照仅无关2040 profile不同，云包直接复制云V9而非工作区|
|真实1h F/S构建|gate_F/、gate_S/、one_hour_pair_identity.json|ROWS/COLUMNS/RHS（含目标）逐段SHA一致，仅20,272个vre_new上界置零|
|精确筛选身份|gate_S/candidate_selection.csv|36,686站一对一；34,439有当前headroom，14,167保留；排除headroom39,341.39949215136 GW|
|两行真实Gurobi入口fixture|fixture.stdout.log、fixture.stderr.log|3项PASS；参数回读48线程/5轮；无QC/状态输出|
|最终串行完整回归|../validation_coordination_20261005/unittest_verified_20261005T185140Z.log及.json|412 tests / 112.906s / OK / skipped1（Windows无/proc）/ exit0 / source_unchanged=true|

1h门禁只build/archive，无optimize；两行fixture对求解出口与身份隔离做验证，不代替真实模型性能。fixture将与小LP不相干的柔性预/后结构兼容摘要mock为同一PASS，实际1h和云8760预检查不mock。Windows的原模型归档实际为original.mps，云可为original.mps.gz，段SHA解析兼容两者。

本机18:23蓝屏中断的旧全套回归保留为“未完成”，不能称通过；用户随后授权本机串行继续，根代理协调本机独占执行完整回归并验证受测源码未变。先前411项通过后，补齐数值任务入口/白名单审计，最新上表412项再次通过。最新原日志SHA256=`bf65c47c52747ef14fb6385b1c1518e822d5f7af1c0771c2b4b98a7077fa2d79`；中间shell缺WAVE环境的失败另行保留。此后任务1仅云端只读取证，不额外启动本机测试或求解。

## 任务书与实际差异

1. 源筛选“14,170”使用headroom>1e-6统计。当前V9默认1e-5 GW cutoff已将三个DPV站的5.852501e-6、3.721000e-6、6.052454e-6 GW余量置零，因此当前可扩展保留14,167；不为凑计数改变V9科学规则。详细源/当前差异CSV还保留机器精度与<1e-6微量行，不能把全部57行当上述3站。
2. held作业尚未分配节点，AllocTRES为空；采用既有可执行顺序：held核ReqTRES→release→batch核AllocTRES/节点/内存通过才构建求解。
3. factor profile只改变生产numerics的bar_iter_limit=5，另改变身份声明。入口新增明确TEST_ONLY分支，绕过生产接受/状态出口但保留实际柔性数值兼容检查。
4. frozen_local是独立1h门禁执行副本；其runner/module/profile已更新，不称为完整未修改before目录。起始SHA另存，未更新的master/config等可与起始SHA核验。云payload以cloud_source_repo_sha256.json中的V9为源，新增/替换5个明确接口文件；所有数值稳健性改动隔离在外。

## 云端提交与当前资源证据

2026-10-05英国18:12左右完成held核验和放行；精确服务器时戳与UTC目录见submit/release原始记录。全程仅提交这两个作业，没有对4844528执行控制操作。

|成员|job id|节点|Req/AllocTRES|启动内存门禁|状态|
|---|---|---|---|---|---|
|F完整|4981130|m4cg1707|cpu64/mem750G/node1/billing64|PASS，约725.64GiB可用|RUNNING|
|S初筛|4981131|m4cg1801|cpu64/mem750G/node1/billing64|PASS|RUNNING|

两节点均amd_a8_768、128物理核（2×64）、ThreadsPerCore1、RealMemory768000MiB；具体CPU型号待Gurobi banner核验。启动门禁通过才进入fixture/构建；3项fixture在各计算节点重跑均PASS（F6.207s/S6.152s），随后进入真实8760构建，stderr为空。首版原始证据status_20261005T171244Z/，每份receipt保存远端SHA并对取回bytes复核；以后状态快照追加不覆盖。两成员基线源码和delta清单在各source_identity.json；输入均链接同一V9 data_overlay。status_20261005T171510Z/factor_summary.json独立比较确认两成员实际源码SHA完全相同、80条input_manifest记录仅规范化member路径后完全一致。云8760预检查和柔性数值兼容PASS；登录节点memory_gate=false是非计算节点内存，不冒充算力资格，实际计算节点独立通过500GiB门禁。

计时预注册：优先telemetry精确Runtime差分，第1轮=Runtime1−Runtime0，第2–5轮均值=(Runtime5−Runtime1)/4；逐轮Work同样差分，并另列总Work。Presolve/Ordering不混入每轮均值。费用暂未产生终态核时与账单单价，不能填金额。

## 待完成与一句话判定

### 2026-10-05英国19:24：本机蓝屏后只读复核

证据：`status_20261005T182419Z/`（原始日志以bytes取回并对远端SHA复核）。本机18:23重启未中断云端两个独立Slurm作业；恢复后没有本地求解或重测，没有云端控制、重提或额外提交。

|指标|F / 4981130|S / 4981131|
|---|---|---|
|Slurm状态/运行时长|RUNNING / 1:11:42|RUNNING / 1:11:42|
|当前阶段|Presolve约845s|Presolve约845s|
|节点/CPU|m4cg1707 / AMD EPYC 9554|m4cg1801 / AMD EPYC 9554|
|原LP行/列/非零|54,217,462 / 43,761,608 / 501,902,601|相同|
|实际线程/BarIterLimit|48 / 5|48 / 5|
|NF/Scale/Presolve/Aggregate/Cross/Target|2 / 2 / 2 / 1 / 0 / 1|相同|
|Time/SoftMem/Mem/Work限制|均无限|均无限|
|sstat峰值RSS|96,266,720K（约91.8GiB）|97,055,156K（约92.6GiB）|
|stderr|空|空|

真实8760 MPS分段身份已闭合：ROWS=`32801212fcc23dd8897017360b9efd576e409fd0d3369fcb839b83910cb7edb4`；COLUMNS（含目标）=`e5266fd7a996062e2fd34de75c4f78bd9950e5da16d2913201480fd5f3f1c4a4`；RHS=`6ef4b21b7eb61823f8d639af20dd002b9b67618a1040c35507bbad2376c0c1e7`；非vre_new BOUNDS=`9c5ea9801c62cf3608065c4bde1845e17047d5e5b76b43113c6f30e9ef629126`，两成员全部相同。唯一不同段为BOUNDS_VRE_NEW，实际筛选仍14,167保留/20,272置零。原始LP各自归档，未取回数GB MPS本体，仅取回计算节点流式段SHA证据。

19:50补取`status_20261005T185029Z/`中两份归档manifest：F的`original.mps.gz`为4,143,651,443 bytes / SHA256 `9f426316dff40fa03398c24f6d675249edd02176380ee66c5110a1a1fde24460`；S为4,143,496,357 bytes / `e2861cfc3612eef82450b626c1fce0a4963ca1573fe800a4b2a18d38afdf258f`。两份parameters.prm均185 bytes / `b57fdfe28a198b08ee3f01f87cc9a8a70998a5e589fbbedb510a71dd51ba4842`。当时两者仍Presolve约2415s、stderr空，不作性能判定。

两份参数回读中BarHomogeneous均为-1，未混入另一任务的措施B。尚无Presolved终态、Factor或Barrier轮次，不能判定筛选收益。本机蓝屏原因另见协调报告；任务1本地1h构建早已完成，其builder监控峰值0.421/0.424GiB仅覆盖构建阶段，不是整机内存或蓝屏因果证据。

生产节点类型交叉核验仅使用此前已取回的`../base_2050_continuation_20260930/status_20261005T162312Z/output_8760__gurobi.log`第46–47行：生产同为AMD EPYC 9554、128物理/逻辑核、48线程。因此两新成员与生产的CPU型号、拓扑及amd_a8_768分区一致，m4cg/m4cm节点名前缀差异不等于硬件类型差异。

元数据说明：旧runner嵌套`barrier_first_workflow.primary_checkpoint_requested`仍按SolutionTarget1记为true；新factor专用路径在所有checkpoint/QC/状态导出之前返回，顶层身份为TEST_ONLY_FACTOR_SCREEN/NONE，fixture验证没有实际状态导出。此遗留描述不作为产物存在的证据，云包保持不可变。

**待判：F4981130与S4981131仍在运行，缺少第2–5轮时长与Dense cols，不能判定通过或封存。**

待记录：job id、Req/AllocTRES、节点类型、Presolved行列非零、Dense cols、AA' NZ、Factor NZ/Ops、Presolve/Ordering/每轮秒、Work、RSS、逐轮P/D/PInf/DInf/Compl、实际线程、两成员8760 MPS段SHA、输入SHA、资源计费记录。禁止操作4844528、禁止额外作业、禁止自动启动全年科学情景。

## 复现入口

2026-10-05英国22:55只读状态：证据`status_20261005T215542Z/`，F/S仍RUNNING4:43:05、64CPU/750G；F Presolve约13530s、S Ordering约2890s，stderr空，无五轮终态。因另一项固定机取证的转发持续不可达，依据本对话heartbeat外部阻塞规则，自动检查在22:57置PAUSED；**云作业本身未停止或重提**。恢复跟进时先收既有作业最新/终态结果，不能重复提交。

2026-10-05英国22:25阶段变化：`status_20261005T212543Z/`中两作业仍RUNNING4:13:06、stderr空。S已完成Presolve（10574.27秒），presolved为39,581,725行/35,714,859列/317,658,492非零，正在Ordering（日志约455秒）；F仍Presolve约11730秒。sstat峰RSS为F114,400,912KiB、S672,138,784KiB。S先进入Ordering只反映阶段进度，仍无Dense cols、Factor和第2–5轮数据，不能替代预注册Barrier成本判定。原始bytes/SHA已核验，无作业控制或追加提交。

2026-10-05英国20:25 heartbeat只读复核：新增证据`status_20261005T192548Z/`，F4981130/S4981131均RUNNING2:13:11、实际64CPU/750G、Presolve约4535s，尚无Factor或Barrier记录。当前presolve累计删除F为13,406,213行/7,616,921列，S为14,618,024行/8,063,973列；这些不是最终presolved规模。sstat峰值RSS分别96,358,072K/111,745,944K，两份stderr仍空。取回原始bytes与receipt SHA核验通过，`factor_summary.json`仍PENDING_COMPLETE_EVIDENCE；未增加/重提/控制任何云作业。

- cloud_payload/：冻结接口与batch；payload_sha256.json验证身份。
- deploy.py prepare/preflight/submit/release/status：一次性不可变部署和授权两个held作业；submit/release有持久哨兵，重试前先读证据。
- 本地：RL Python + output/portfolio_runtime_gurobi13；运行 tests/test_factor_screen.py；1h使用frozen_local runner、V9派生case3、build-only和archive-original-model，命令见gate run_environment.json。
- 资源费用仅记Slurm核时与节点时，未获账单单价时不得伪造金额。
