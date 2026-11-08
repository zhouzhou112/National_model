# C 2060 · v1

2026-11-08：**PASS_AUTHOR_20261108**。本案原MPS+BarX独立定位河北年度外送行，0.030049423GWh / 296139.149785GWh = 1.014706e-7，小于0.296139150GWh容差。自身BarPi证书B=181.472947million CNY，B/obj=3.1756902e-5，B/(P−D)=3.959334%；8025剔除列中3个负价列，与两份2050翻转集合无交集，陕西11站本案全部非负、B贡献0。物理检查通过/水库暂缓，PInf条件披露；原QC保留，不重解。73小文件108474686bytes回本机；原备份106文件5.51GB收尾重新SHA全部通过，验收JSON双端一致。

[验收报告](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_acceptance_20261108/REVIEW_ZH.md>)；[验收JSON](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_acceptance_20261108/author_review/acceptance_author_20261108.json>)；[小文件目录](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_acceptance_20261108/C2060/output_8760/>)；[成本对照](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_acceptance_20261108/cost_comparison/primary_cost_comparison.csv>)。

2026-11-07 19:41 UTC一次性只读核对：云端1项RUNNING，Case3 2060/5411471运行1天05:39:51、第74轮；PInf1.2552731e10/DInf20773.543/Compl5.3633379e7，64→74下降15.99%/30.25%/16.82%，19.50分钟/轮，Slurm峰值RSS650.685GiB未升、stderr空。C2060/5318408仍COMPLETED；T550备份已于13:29:12UTC完成，106文件5,506,707,098bytes，T1/T2/T3逐文件bytes/SHA全部VERIFIED、source_unchanged=true，无重复传输。正式验收仍待原MPS+BarX行定位及自身BarPi证书，不将备份完成等同验收。未修改运行作业，不建监听。

2026-11-07 13:17 UTC：云端1项RUNNING，C2060/5318408于12:52:45UTC COMPLETED/0:0，527轮OPTIMAL，总8天12:25:33；目标5714441.107401 million CNY，进程树峰值603.149GiB，保全COMPLETE/errors=[]。原relative_v1仅solver失败，物理项全通过、水库暂缓；PInf0.0426386，最大行违反0.0300494（index53400865）尚未独立定位，自身BarPi证书待办，不宣称正式验收。Case3 2060/5411471运行23:15:44、第55轮，PInf2.08190e10/DInf48129.99/Compl8.98099e7；45→55下降14.93%/51.21%/17.40%，19.54分钟/轮，sstat峰值650.685GiB、stderr空。T550恢复后核无重复传输，13:20UTC自主全备份启动PID1382003，106文件5,506,707,098bytes，预计余量34.88%；当前传输中，未称完成，不建监听。

[终态与备份报告](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_completed_20261107/REVIEW_ZH.md>)

**2026-10-30 00:27 UTC：云端2项RUNNING，C2060已放行并通过启动检查。** C2060/5318408，release 20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1，节点m4cm1701，AllocTRES=64CPU/750G/billing64，40线程、UNLIMITED/no-requeue，启动可用内存720.917GiB、Gurobi13.0.2 compute smoke PASS、stderr空；当前全年模型构建，尚无Barrier轮次。Case3 2050/5294579第145轮，运行2天10:56:40，PInf9.01364e6/DInf0.253776/Compl44855.78，仅只读。C2050已按作者10-30年度汇总规则验收PASS，自身证书B/obj9.93512e-5，完整备份与73小文件取回完成，验收JSON双端SHA一致。

来源：C2050验收状态→R1；Base2060 margin0.2筛选；v9_a12/Aggregate0/40线程。

- [运行与门禁报告](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_launch_20261030/REVIEW_ZH.md>)
- [启动证据](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_launch_20261030/deployment/status.json>)
- [门禁汇总](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/C2060_launch_20261030/GATES_SUMMARY.json>)

完整云端路径：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1`。运行期间只读；终态后按10-20规则T550完整备份、验收与小文件取回，不建后台监听。
