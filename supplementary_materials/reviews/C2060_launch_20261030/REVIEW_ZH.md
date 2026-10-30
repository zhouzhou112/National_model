# C2060 续接准备与门禁（2026-10-30）

**2026-10-30 00:27 UTC：云端2项RUNNING，C2060已放行并通过启动检查。** C2060/5318408，release 20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1，节点m4cm1701，AllocTRES=64CPU/750G/billing64，40线程、UNLIMITED/no-requeue，启动可用内存720.917GiB、Gurobi13.0.2 compute smoke PASS、stderr空；当前全年模型构建，尚无Barrier轮次。Case3 2050/5294579第145轮，运行2天10:56:40，PInf9.01364e6/DInf0.253776/Compl44855.78，仅只读。C2050已按作者10-30年度汇总规则验收PASS，自身证书B/obj9.93512e-5，完整备份与73小文件取回完成，验收JSON双端SHA一致。

**2026-10-30 C2060全部32项工程门禁PASS。** C2050按新增年度汇总口径正式采纳；R1删除发电/储能0.391715051GW、网络0.226504420GW，保护改造关联新建0.007264065GW；26条负尾差置零增量4.75e-15GW，单处bound-close2.34465e-8GW。1h筛选/不筛选只有BOUNDS_VRE_NEW不同，tiny_capacity_columns均空；24h 103轮OPTIMAL，M=2.49682e-7，relative_v1 PASS、保全COMPLETE、2060参数通过。下一步冻结新C2060 release并preflight，按预授权提交/release。

验证源码54ce73e；首轮7317181在运行器入口因新profile未登记而停止，未构建模型，完整保留。新增严格限定2060/case3同情景续接/Base2060 margin0.2/40线程的生产profile登记，18项focused tests通过；初次本地provenance测试因未设置CISPO_WAVE_ROOT失败，设置既有wave_energy目录后6/6通过。

T550隔离目录/home/zz2/National_model_server/C2060_launch_20261030_v2；数据58文件逐项SHA核对；R1和短窗全部在T550进行。attempt_2/t550_evidence为逐项SHA核验后的小证据与不足1MiB的完整R1派生包；大MPS、BarX/BarPi/短窗解留在T550。汇总见GATES_SUMMARY.json与attempt_2/t550_evidence/FINAL_GATES_PASSED.json。

门禁入口run_continuation_gate.py扩展2060且要求显式profile/清单；原MPS现在为gzip，finalize首次只识别.mps的工具错误已保留，v2按archive_manifest选择.mps或.mps.gz并核验SHA，32项全过。不是放松科学门禁。

提交脚本来自云端Case3 2050 v2原件，SHA a29a3635a69ce27fc1f31fe7e4ad4213c4f4c4c88107c381f059fa246e393559，与本地模板相同；只改说明、作业名、2060 profile路径和规划年。64CPU/750G/billing64/UNLIMITED/no-requeue/40线程及≥700GiB启动门禁保持。WLS仅路径字符串比较，不读凭据。

C2050完整备份105文件5,511,013,265bytes；验收记录本机/T550 SHA一致；73小结果108,454,785bytes已取回并纳入case_results，历史停止记录并列保留。未修改5294579或SI模块，无后台监听。


## 2026-10-30 C2060提交放行与启动验证完成

**2026-10-30 00:27 UTC：云端2项RUNNING，C2060已放行并通过启动检查。** C2060/5318408，release 20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1，节点m4cm1701，AllocTRES=64CPU/750G/billing64，40线程、UNLIMITED/no-requeue，启动可用内存720.917GiB、Gurobi13.0.2 compute smoke PASS、stderr空；当前全年模型构建，尚无Barrier轮次。Case3 2050/5294579第145轮，运行2天10:56:40，PInf9.01364e6/DInf0.253776/Compl44855.78，仅只读。C2050已按作者10-30年度汇总规则验收PASS，自身证书B/obj9.93512e-5，完整备份与73小文件取回完成，验收JSON双端SHA一致。

执行源码54ce73e、冻结提交7117aa2（相关核心源码SHA与门禁一致）；冻结493文件，release manifest SHA1621933d3ed323f7276aca166f44209702201ddfa58ed9e7e19f88caba2feaf2。32项门禁→preflight PASS→held资源核验→按既有授权release→实际资源/700GiB/计算节点smoke全通过。证据supplementary_materials/reviews/C2060_launch_20261030/deployment/{freeze,preflight,held_submission,released_submission,status}.json，GATES_SUMMARY.json及REVIEW_ZH.md。sbatch源为Case3 2050 v2已核验原件，WLS仅路径字符串比较。已更新case_results C2060卡片；未覆盖历史验证失败、原始QC或任一运行包，SI改动保持隔离，无后台监听。下一步：用户询问时同时只读检查两作业；任一新终态按10-20核对旧备份/活动传输→T550完整单次备份→扩展验收/证书→取回小文件。C2060启动成功不等于全年稳定或已收敛。
