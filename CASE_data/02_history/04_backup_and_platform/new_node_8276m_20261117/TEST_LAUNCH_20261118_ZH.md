# 新节点32线程前5轮测试启动记录（2026-11-18）

作者已放行，并提供本机D:/gurobi1作为许可位置。新节点不存在该目录；本机目录只有gurobi.lic（308bytes）。按本次用途通过加密SCP直接放入新节点C:/Users/zz2/gurobi.lic并限制ACL，未将内容读入上下文、显示、散列或纳入Git；只记录路径/大小。

源码提交f6cb41961262701d3042c21714cb507df83c8968，已推送GitHub工作分支。冻结测试源码在新节点C:/NationalModelBench/ops_open2050_t32_20261118/runsource/t32_factor5_v1；输入原件和云端release不变。

18:57:11UTC一次性任务NationalModel_OPS2050_T32_Factor5_20261118_v1已手动启动；控制器9160，Python5340。输出目录runs/t32_factor5_v1。任务使用已登录zz2的Interactive主体、隐藏窗口，无触发器、无自动重试；XML确认Triggers实际为0，首份回执PowerShell @($null).Count=1是统计误差，已在同一JSON追加更正。30h任务上限仅为单次控制器的兜底，不是重复排程或后台监听。

测试保持32线程、Barrier最多5轮、Crossover0、原LP/数值参数；650GiB可用准入、640/660GiB软/硬内存限制、30GiB空闲保护照合同。小型许可检查和大MPS共用同一个Env，不另开smoke进程。参数仅按显式科学/运行白名单导出，不序列化整个环境，避免输出WLS凭据。

18:58:37UTC正在完整MPS SHA校验，CPU累计86.16秒、RSS约49MiB、stderr为空；仍未进入许可验证/模型载入，不以进程启动冒充许可成功或排序通过。源数据SHA、规模和指纹仍须后续门禁核对。

初始静态检查把普通文件日志/锁的write误判为模型参数导出；改为只检查model/env对象的write/writeParams后通过。源码未因该测试断言调整科学行为。PowerShell语法和单Env编排检查通过，实际结果待测试终态。

下一步：跟踪本次进程至有界终态，保留输出、参数、资源曲线与仍可访问的解向量；失败不覆盖/自动重跑，不触碰云端运行作业。新节点测试不是全年生产结果，平台/线程/硬件同时变化，不作纯CPU消融解释。
