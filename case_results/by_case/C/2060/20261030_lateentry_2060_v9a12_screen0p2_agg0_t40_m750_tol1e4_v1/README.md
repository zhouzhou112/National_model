# C 2060 · v1

2026-11-07 13:17 UTC：云端1项RUNNING，C2060/5318408于12:52:45UTC COMPLETED/0:0，527轮OPTIMAL，总8天12:25:33；目标5714441.107401 million CNY，进程树峰值603.149GiB，保全COMPLETE/errors=[]。原relative_v1仅solver失败，物理项全通过、水库暂缓；PInf0.0426386，最大行违反0.0300494（index53400865）尚未独立定位，自身BarPi证书待办，不宣称正式验收。Case3 2060/5411471运行23:15:44、第55轮，PInf2.08190e10/DInf48129.99/Compl8.98099e7；45→55下降14.93%/51.21%/17.40%，19.54分钟/轮，sstat峰值650.685GiB、stderr空。T550恢复后核无重复传输，13:20UTC自主全备份启动PID1382003，106文件5,506,707,098bytes，预计余量34.88%；当前传输中，未称完成，不建监听。

[终态与备份报告](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_completed_20261107/REVIEW_ZH.md>)

**2026-10-30 00:27 UTC：云端2项RUNNING，C2060已放行并通过启动检查。** C2060/5318408，release 20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1，节点m4cm1701，AllocTRES=64CPU/750G/billing64，40线程、UNLIMITED/no-requeue，启动可用内存720.917GiB、Gurobi13.0.2 compute smoke PASS、stderr空；当前全年模型构建，尚无Barrier轮次。Case3 2050/5294579第145轮，运行2天10:56:40，PInf9.01364e6/DInf0.253776/Compl44855.78，仅只读。C2050已按作者10-30年度汇总规则验收PASS，自身证书B/obj9.93512e-5，完整备份与73小文件取回完成，验收JSON双端SHA一致。

来源：C2050验收状态→R1；Base2060 margin0.2筛选；v9_a12/Aggregate0/40线程。

- [运行与门禁报告](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_launch_20261030/REVIEW_ZH.md>)
- [启动证据](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_launch_20261030/deployment/status.json>)
- [门禁汇总](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_launch_20261030/GATES_SUMMARY.json>)

完整云端路径：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1`。运行期间只读；终态后按10-20规则T550完整备份、验收与小文件取回，不建后台监听。
