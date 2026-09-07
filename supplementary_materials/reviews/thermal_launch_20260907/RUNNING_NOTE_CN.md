# 2030 Base＋冷热正式作业启动记录

2026-09-07 20:10:12（北京时间）启动：**job4533060**，节点`m4cm2204`。
20:11只读观测为RUNNING，计算节点preflight PASS，wrapper/Slurm两份stderr均为0字节；当时正在建模，未产生原始MPS归档或Barrier结果。

| 项目 | 已部署设置/已核验分配 |
|---|---|
| 情景 | case1_thermal_v5：2030年Base＋冷热，31省8760h |
| Gurobi | 13.0.2；Threads44；BarConvTol=1e-4；Method2、Crossover0、SolutionTarget1 |
| 资源/计费 | amd_a8_768，64 CPU、700G内存、billing64 |
| 时间上限 | Slurm UNLIMITED；Gurobi TimeLimit未设置；无定时STOP |
| 其他 | 无SoftMemLimit；不自动Stage B或进入下一年；科学QC与完整保全要求不变 |
| 部署提交 | ffd651aded605568bc1e02cc460eae5ecd113b5b |

release：
`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260907_thermal_stagea_1e4_t44_ffd651a_v2`

case/output目录名：
`2030_case1_thermal_v5_8760_rows8192_t44_m700_tol1e4_ffd651a_v2`

原Base job4479238继续在m4cg1605运行，本轮未停止、改参或覆盖它。没有启动EV或联合情景。

首次尝试job4533016因部署Git版本记录使用Windows CRLF，在启动器校验阶段1秒失败，未建模或优化。
源码SHA已通过，问题是版本字符串尾部回车；v1及失败日志保留。在独立v2将清单写为LF，额外核对实际读取的版本字符串后重新提交。
有效作业仅4533060，不应再提交一次。

启动证据：307个源码文件校验、V5五文件完整SHA、云端版本/配置校验、4项授权范围测试＋30项不求解回归、真实全年服务输入建模前检查。
这些均不是完整求解结果或最终科学验收。建模后须先归档原始模型与参数，再进入Barrier；最终状态、原始向量和QC按已有保全机制保存。

只读检查：`ssh paracloud-bscc-a8 'squeue -h -j 4533060,4479238 -o "%i %T %M %l %C %m %N"'`。
本地单次阶段检查脚本：`output/thermal_launch_20260907/probe.py`。
没有创建定时监测或自动停止任务；不要把关闭本地对话当作停止云作业。

原始证据保留于`output/thermal_launch_20260907/`；本目录evidence中调度文本副本仅去除行尾空白，字段内容不变。
