# Case3 2060：固定清单与44线程尝试（2026-11-06）

## 已通过的工程门禁

作者已采纳 Case3 2050，任务书第1b节固定 Base2060 margin0.2 清单，不放回站点，旧0.3条件作废。随后作者要求本次尝试44个 Gurobi线程；Slurm仍64CPU/750G/UNLIMITED/no-requeue，启动可用内存至少700GiB。此前48线程OOM发生于C2050；Case3 2050以40线程完成，峰值620.95GiB。44线程的全年排序峰值及加速效果尚未实测。

工程验证源码为391a5f1；部署工具为b3a5dfe，打包时逐文件验证core/config/scripts/tests与已测源码一致。未改变LP、容差、目标或清单，未触碰5318408和冻结包。

- T550 Gurobi13.0.2：19项测试运行，18通过、1项因缺既有fixture跳过。profile、production_screen、factor_screen全部通过。本机Gurobi12门槛失败原始记录保留，未绕过。
- R1：发电/储能删除0.473295579GW，网络删除0.317446754GW，分族总量/比例门禁PASS；改造关联保护新建0.008133849GW；保留负cohort置零107条、增量2.801144691e-9GW；bound-close为0，来源未改。逐技术审计见r1_audit.json。
- 清单SHA：831514fdb19da9ffa0a4ccca40def435a3972f37db00284524916c1d8b6c9fc3，与运行C2060原件相同；实际8025个剔除列集合完全相同，集合SHA ffb158fabfac69d8617749a5a9c7809a5c84572561b71bfe8a56312d35359cba。无站点放回。
- 1h筛选/不筛选MPS仅BOUNDS_VRE_NEW不同；两侧tiny_capacity_columns为空，数值审计通过白名单。
- 24h：101轮OPTIMAL，M=1.541792223e-7GWh，容量信用越界0，relative_v1 PASS，保全COMPLETE。原严格QC HARD_FAIL并存保留，不更改判据。诊断8线程遵循既有门禁流程，不将短窗表现外推全年。
- 2060参数逐项核准通过；最终33项全部PASS，见t550_evidence/FINAL_GATES_PASSED.json。

证据计算于T550独立目录 /home/zz2/National_model_server/case3_2060_launch_20261106_v1 。仅回传123个小证据文件共4,525,641bytes（含续接所需cohort压缩状态），原MPS/逐时/BarX/BarPi留T550。collect.json逐文件bytes/SHA核验。

## 复现入口与执行边界

`t550_work.py prepare → r1 → gate --name screen_1h → compare → gate --name unscreen_1h → gate --name gate_24h → finalize_gates.py → collect`。已有目录拒绝覆盖，不重复运行。`deploy_authorized.py A2060 prepare/preflight/submit/release/status`分阶段执行，首次sbatch使用hold，再按本次预授权release；不建立后台监听。新release目标为20261106_case3_2060_v9a12_screen0p2_agg0_t44_m750_tol1e4_v1。

历史阶段：门禁全过时尚未提交，随后完成下述启动验证。

## 放行和启动核验

2026-11-06 14:02 UTC：云端2项RUNNING。Case3 2060/5411471已按作者44线程尝试授权放行，节点m4cg1606，AllocTRES=64CPU/750G/billing64、UNLIMITED/no-requeue，启动可用内存719.298GiB，Gurobi13.0.2 smoke PASS、stderr空，目前全年构建。R1/1h身份/24h/2060参数33项门禁及云端preflight全部PASS；清单SHA和8025剔除列与C2060完全一致、margin0.2无放回。C2060/5318408仅只读确认仍运行，第466轮。44线程全年峰值/提速尚未验证，不外推短窗，不建监听。

冻结release：`20261106_case3_2060_v9a12_screen0p2_agg0_t44_m750_tol1e4_v1`；源码提交`7455614b082f9b39299a26b04d0f1e8e7d867c56`。云端497个文件冻结并SHA核验，58个数据文件独立复制；preflight PASS，首次sbatch --hold的ReqTRES验证后按本次预授权release。证据见deployment/freeze.json、preflight.json、held_submission.json、released_submission.json、startup_verified.json。全部已有运行和失败证据保留，未修改5318408。

Case3 2050完整备份93文件已校验、验收JSON已双端同步（本次复用，无重复传输）；新作业未终态，不启动结果备份。终态后按10-20规则备份、验收、取回小文件。44线程是否更快需等全年排序峰值及同阶段迭代耗时；没有保证，异常不自动重跑。
