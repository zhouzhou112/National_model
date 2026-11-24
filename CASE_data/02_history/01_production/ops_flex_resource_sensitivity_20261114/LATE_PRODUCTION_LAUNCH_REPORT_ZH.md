## 2026-11-15 08:47UTC 作者单独授权LATE-Open2050正式求解已放行

作者在五轮测试与条件耗时报告后明确“启动LATE-Open，可以考量48核心吧”。按本次直接授权仅提前启动LATE-Open2050受限全年作业，覆盖该案等待第一批结束的时间条件，未授权其他第二/三批案例。考虑44线程实测进程树峰649.791GiB、48线程峰值及加速未验证，执行方推荐并沿用44线程；简单比例外推708.863GiB仅为风险提示，不是可靠内存预测。没有改模型源码/约束/目标/输入/数值参数，复用535项回归、真实1h界审计、24h自身解恒等性、全年结构审计与5轮测试。

新release：20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1；源提交c92ee1bb（授权236b8fa7，模型源码仍与29e3782d同字节），sbatch从最新成功测试5584392派生。原R1上游、4481自由/28846下界/3359上界固定清单SHA不变；生产profile与测试profile的numerics逐键相等，正式入口没有5轮回调，开启原MPS、BarX/BarPi和候选状态保全。独立复制/输入SHA/负荷逐行相等/preflight/bash语法检查均PASS。经held核对后release Job5587177。

08:47UTC：云端3RUNNING+1PENDING。5587177等待Resources，StartTime=Unknown，ReqTRES cpu64/mem750G/node1/billing64，UNLIMITED/Requeue=0；AllocTRES尚空、尚无startup_resources或compute_node_smoke，不能宣称已实际启动或内存已通过。脚本内启动门禁保留可用内存≥700GiB及资源核对；下一次先查原job，不重复提交或自动重跑。估时从实际启动计，条件3.6–4.1天，保守4.8–5.3天，不保证五天内。

测试5584392备份已在08:43:31UTC COMPLETE：42文件4191604666bytes，T1/T3全部VERIFIED、源manifest身份未变；T2按测试设计未产生，不伪称存在最终科学解。证据factor_test_backup_complete.json，原PID2744265不重复启动。

操作入口deploy_late_production.py prepare/preflight/submit-release/status，只能表示这一授权案例；snapshot_batch1.py已扩展读正式LATE。最新证据deployment/late_open_2050/、LATE_PRODUCTION_AUTHORIZATION.json、LATE_PRODUCTION_LAUNCH_GATES.json。没有碰3个运行作业或旧冻结包，没有后台监听。下一步核实际分配和启动内存、全年结构/参数；终态按原规则完整备份、relative_v1及本解自身双向定价B证书，报告与LATE2050目标比较，需放开重解先报作者。其余第二批仍等待原批次完成与作者确认。
