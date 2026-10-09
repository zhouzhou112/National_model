# 2050 Base只读进度：568轮，残差继续下降

取证：英国2026-10-09 18:53:57 BST（北京10-10 01:53:57）。原4844528仍RUNNING/m4cm1802，运行9天3小时44分20秒，64CPU/750G/UNLIMITED，48求解线程沿用冻结配置。最新完整Barrier记录568轮，尚无solve_report/solution_qc/preservation_report。

|打印指标|553轮|568轮|下降|
|---|---:|---:|---:|
|PInf|0.0530|0.0373|29.62%|
|DInf|1.25e-6|8.25e-7|34.00%|
|Compl|0.0211|0.0143|32.23%|
|abs(P-D)|1.62625172e6|1.10423232e6|32.10%|

P=6.50196561e6、D=5.39773329e6。553之后四项均逐轮下降，无新的局部对偶上升、PInf/Compl大幅跃升或显式警告，两份stderr空。DInf打印值低于1e-6不能单独当作满足整体求解停止条件：callback残差定义不同，三项与相对目标条件也需求解器判定。仍无可行/最优证书或科学QC。552的微小反弹已披露，不能声称424以后一直单调下降。

553–568对数拟合每轮下降PInf2.245%、DInf2.800%、Compl2.541%，log R²=0.9902/0.9937/0.9906，减半约12.16/9.72/10.72小时。短窗口仍近指数下降，速率不是未来保证。最近558→568平均24.3267分钟每轮。当前Slurm RSS420.09GiB/峰685.98GiB；原日志569条iter0..568连续、4源SHA一致、三调度命令exit0，未查询Restarts。

历史PInf/Compl/abs(P-D)各自最小log比例差匹配：2030第285/264/264轮，按当前速度余1.06–1.42天；2040第530/441/441轮，余1.27–2.77天。历史实际余时0.93–1.24/1.16–2.54天，DInf因非单调独立报告。安排上继续条件性余约1–3天（英国10月10–12日前后），需后段相似、无长平台/重大跳升、迭代成本保持；非保证上限，不含科学QC。历史OPTIMAL案例QC未过。

输入为冻结release原日志/telemetry/两份stderr和squeue/sacct/sstat输出。具体命令和源SHA见scheduler.json。运行本目录python analyze.py离线复算summary.json；依赖553轮快照与thread_comparison_20260930/evidence历史原日志。比较打印残差，callback用于时间戳/Work，Slurm/Gurobi内存分开；abs(P-D)为诊断量，不是MIPGap或确切停止测试。

Git基准d0cbc9f696d0e849818e6338d8341b2104fb3930；本次仅新增检查快照/追加CODEX_HANDOFF、MODEL_SERVER_STATUS、SERVER_RUNBOOK，审查报告/summary/scheduler/analyze/SHA小文件后同步GitHub。原始日志/remote_read.py及其他作者未审核稿件留本地/云端，sha256.json为本地原字节，未发布原件不保证随Git可得。原2050未应用极小界建议；无scontrol/scancel、模型/配置/输入/作业改动、新求解、监听或运行包部署。下一步按用户要求继续只读核验至终态与科学QC。
