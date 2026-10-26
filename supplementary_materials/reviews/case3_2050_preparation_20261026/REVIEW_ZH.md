# case3 2050 预置与2030收尾（2026-10-26）

## 已完成

1. nocredit2030：73个小文件逐项核验并取回；T550完整备份身份复核，定价证书留T550；扩展relative_v1为 PASS。详细三方目标/原对偶差及节省区间见 `../case3_2030_launch_20261014/nocredit_results_20261026/REVIEW_ZH.md`。
2. Base2060 margin0.2 清单：完整原MPS/BarPi在T550计算，P4同口径审核PASS；生产清单36686项，原Base正余量筛掉8025项，SHA `831514fdb19da9ffa0a4ccca40def435a3972f37db00284524916c1d8b6c9fc3`。
3. case3 2050：新profile逐键对照父48线程profile，**仅5个键不同**：Threads、ID、candidate_screen的3个来源字段；description及所有其他数值/验收设置不变。profile SHA `22c7e49f14f1eb7bcfbf19dc76bab61c935b4d9716f052f86785f3225b740f45`。Base2050清单沿用既有 P4，SHA `a55a93738a37c0cf51ef84b73f1e34177cfd7f26a040df146e0c83462190d528`。

## 预置包状态

云端独立目录：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/_preparations/20261026_case3_2050_t40_v1`，状态 **PREPARED_NOT_FROZEN_NOT_SUBMITTED**。58项数据本地与云端bytes/SHA匹配，批处理bash语法PASS；新增数据包括参与率v2与三份续接输入，其余只读链接已验证来源。11MB准备包SHA `b1d8f8b15f31efd72a4e34bd7afc95b66d9499a0e61cb95f0364e97bd6be0fd9`，精确大小/成员见 `package_identity.json`。其中source_commit仅为准备时Git基准0cbad43，成员身份另由SHA绑定；本轮功能已提交3c11ed7，最终生产源码须从门禁通过后的已审查commit重新冻结。

正式求解资源预设40线程，OMP/OPENBLAS/MKL均40；Slurm64CPU/750G/billing64/UNLIMITED/no-requeue，启动可用内存≥700GiB。框架A `case3_thermal_ev_v5`，规划2050/边界2040。sbatch没有Late-entry标志，要求最终门禁标记和真实R1状态；当前两者均不存在，不能用于生产提交。**未生成R1、未执行1h/24h门禁、未冻结最终release、未提交或release新作业。**

准备代码补充范围：`factor_screen.py` 仅登记新profile并限制2050/case3/同情景状态/40线程；旧C2050 profile仍限定Late-entry。现有门禁助手新增显式 `--same-scenario-continuation`，默认旧行为保持兼容。没有改变物理模型、变量定义、目标、约束、单位或数据。

## 验证

定价工具5项测试PASS；扩展评估13项本地PASS，另1项本地因gurobipy缺失未执行，在T550既有环境补验PASS；T550新旧profile/身份/授权边界7项PASS，其中新profile3项也在本地通过。程序语法、profile逐键diff、58输入SHA、生产清单SHA及云端bash语法均PASS。测试不冒充尚未执行的1h/24h科学与工程门禁。

## 尚待上游结束

两个运行作业仅只读，最新快照见本目录 `live_*.json`。case3 2040终态后先全备份、T550证书、扩展评估；B/obj≤1e-2时按既定授权采纳，再R1、1h/24h、2050实际参数核准、最终冻结与云端preflight，全部通过即提交并release。C2050终态只做备份/证书/扩展评估并回报，C2060/C′等作者决定。准确入口、命令、参数与停止条件见 `NEXT_ACTIONS_ZH.md`。

没有创建后台监听或自动轮询；本轮长时任务均为有界离线处理。未读取/复制凭据，未更改运行冻结包。最终profile生效须使用本轮已审查提交的新源码，不能仅把新JSON套到旧源码。用户原有SI交接/稿件和其他改动不进入本次明确提交清单。

Base2060生产三列清单的额外T550旁置同步因连接中断未验证；本地/Git生产清单及T550原全量清单均已核验。详见base_2060_screen_20261026/ready_t550_sync_status.json。
