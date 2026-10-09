# 2050 Base只读进度：578轮

英国2026-10-09 23:03:06 BST（北京10-10 06:03:06）取证：4844528仍RUNNING/m4cm1802，运行9天7小时53分29秒，64CPU/750G/UNLIMITED，48线程沿用冻结配置。最新完整记录578轮，无solve_report/solution_qc/preservation_report。

|打印指标|568轮|578轮|下降|
|---|---:|---:|---:|
|PInf|0.0373|0.0304|18.50%|
|DInf|8.25e-7|6.23e-7|24.48%|
|Compl|0.0143|0.0113|20.98%|
|abs(P-D)|1.10423232e6|8.6768901e5|21.42%|

P=6.35450409e6、D=5.48681508e6。这10轮四项逐轮下降，无新对偶反弹或PInf/Compl大幅跃升，无显式警告/报错，两份stderr空；仍未收敛，无最优/可行证书或科学QC。打印残差与callback定义不同，不能以打印DInf低于1e-6判整体收敛。

近568–578对数拟合每轮下降PInf1.904%/DInf2.837%/Compl2.291%，log R²0.9864/0.9967/0.9950；窗口仅10轮，不固定斜率外推。近期23.8483分钟每轮。Slurm当前RSS422.50GiB（上次420.09GiB），峰值仍685.98GiB，无据此单独判断算法阶段变化。579条iter0..578连续、4源SHA一致、三调度命令exit0。未查询Restarts；Slurm内存与Gurobi内存分开。

历史PInf/Compl/abs(P-D)分别匹配：2030第289/268/268轮，按当前速度余0.98–1.32天；2040第537/450/450轮，余1.13–2.57天。历史实际余时0.88–1.18与1.05–2.41天。安排继续约1–3天的条件性估计：后段相似、无重大跳升/长平台及近况成本维持，非保证上限。DInf非单调独立报告，不用于主阶段。历史OPTIMAL案例QC未过，估计只针对求解终止，不含科学验收。

输入：冻结release原日志/telemetry/两份stderr与squeue/sacct/sstat，命令/源SHA见scheduler.json。运行本目录python analyze.py离线复算summary.json，依赖568轮快照与thread_comparison_20260930/evidence原日志。只比较打印残差，callback用于时间戳/Work；abs(P-D)为诊断量，不是MIPGap或确切停止测试。

Git基准8640d960413fbc51168cd4cbbea3bac29fbc9193。仅新增快照/追加CODEX_HANDOFF、MODEL_SERVER_STATUS、SERVER_RUNBOOK，审查报告/summary/scheduler/analyze/SHA小文件后同步GitHub。原始日志/remote_read.py和未审核稿件留本地/云端，sha256.json为本地原字节清单，未发布原件不保证随Git可得。无scontrol/scancel、模型/配置/输入/作业修改，新求解、后台监听或运行包部署；极小界建议未应用。下一步按用户要求只读观察终态与科学QC。
