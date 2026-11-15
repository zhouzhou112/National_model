# LATE-Open-TEST 2050 — 第一批启动记录

Job 5584392，截至 2026-11-15T00:52:34.902580Z 为RUNNING，尚未验收/备份。44线程、64CPU/750G/UNLIMITED/no-requeue；启动可用内存 718.335464 GiB。

云端：/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261115_lateopen_2050_restricted_factor5_t44_m750_v1

门禁与证据：D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\reviews\ops_flex_resource_sensitivity_20261114

仅构建、排序、前5轮测试，回调终止；不产科学解或规划状态，不代表已授权第二批。

第一批全部终态后备份、验收并交批次报告，作者确认前不得提交第二批。

## 2026-11-15 08:33UTC 第一批进度与LATE五轮测试结束

云端3运行/1测试结束，无第二批提交。OPS-Open5584373运行7:45:05到79轮（打印PInf0.0617/DInf9.56e-8/Compl0.00909），OPS-Conservative5584377运行7:43:23到76轮（0.131/9.63e-8/0.0238），D1/C5 5584390运行7:42:21到82轮（0.0178/1.33e-7/0.00469）；近10轮打印PInf分别降69.75%/80.21%/75.41%，均无终态。这里用gurobi.log打印口径，与callback未缩放残差分开。四案全年服务上界结构审计均PASS，开放139条effective_load_nonnegative行，其余0。

LATE测试5584392于05:28:34UTC结束（Slurm显示北京13:28:34），COMPLETED/0:0，总4:36:18；solve status11为预定callback中断，requested_stop_observed=True、5轮、callback_stop_error=None，保全COMPLETE且明确TEST_ONLY_FACTOR_PROBE_NO_FINAL_SOLUTION。排序3915.91秒，DenseCols7872、FactorNZ2.233e10、FactorOps7.483e14、实际44线程；5轮增量684/511/547/510/545秒，平均559.4秒=9.323分钟。进程树峰649.791GiB，Slurm峰643.327GiB；两口径不混用。自由集4481。

只读取C2050、Case32050原日志：历史终态496/551轮，首5轮均值1468.2/1382.8秒，本次耗时为各自38.10%/40.45%。按历史轮数及后期相对增幅，完整受限求解条件估计3.568/4.034天；按Gurobi粗估800秒/轮则4.752/5.261天。不是收敛保证、不是纯线程消融；保守端超过5天提示线，记录给作者，禁止据此自行放行第二批。当前只跑了5轮，不能评价近优性/物理QC或签约结果。

T550已核无同名备份/旧传输，使用原backup_completed_cloud引擎并补显式测试启动元数据，未读凭据。42文件4191604666bytes，全量包含原MPS，测试按设计无BarX/BarPi或最终状态。备份后预计保留30.1665%，满足原门禁，无沿用旧空间例外。单次自主拉取PID2744265；当前T1的41件44330128bytes已VERIFIED、T3原MPS传输中，尚未COMPLETE，不重复启动。源输出/冻结release不改。

证据：status_20261115T083334Z/{summary.json,historical_timing.json,backup_launch.json,backup_status.json}及snapshots/20261115T083334Z/snapshot.json；源码基准0c1e0d53，本轮只加状态/只读取证与测试备份封装。下一步核已有备份终态及源身份，确认全部SHA后登记COMPLETE；只在询问时查3项原作业，不建监听。第一批全终态、备份、验收与批次报告后等作者确认，第二/三批保持未提交。
