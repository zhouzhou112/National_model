# 8276M节点32线程硬件测试合同（仅预设，2026-11-18）

## 当前执行边界

**PREPARE_ONLY。** 作者2026-11-18明确要求先不启动测试，只预设环境。
不创建Gurobi Env、Model或申请WLS令牌，不运行许可smoke，不读取MPS到求解器，
不执行presolve/optimize，也不停止或改动云端已有作业。
可以安装软件、导入模块查询版本、校验/解压已归档模型和检查脚本。

节点上的`setup/execution_authorization.json`保持`status=PREPARE_ONLY`。
`benchmark_mps.py`的`smoke`和`run`在导入gurobipy前检查该状态；未获作者新指令
不得修改为AUTHORIZED。脚本不会因环境安装成功、网络恢复或令牌过期自动启动。

## 固定来源

- 已解OPS-Open2050：`20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1`。
- 源`original.mps.gz`：4,148,509,456 bytes，SHA256
  `33a4f822cbf894810082843e6ccabbb59db2183e3282f182b0df1cb807768a4b`。
- 原模型归档指纹：`-17374259`（比较时转为无符号32位）。
- 原LP：54,288,578行、43,797,081列、503,239,404非零元。
- 源参数文件SHA256：`24d9ead7a115503af26481af3e1f8c5f8de5f5e0ff20459ffdf600943ae4a3c5`。
- 拷贝包括10个文件：模型、参数、归档/结果manifest、构建/求解/保全报告、
  运行环境、配置快照、原Gurobi日志；不是完整源码和全量输入部署。
- 大模型由新节点直接SFTP拉取，不经过本机磁盘中转。目标逐文件SHA/bytes通过，
  传输后源stat与归档manifest SHA未变；没有因旧QC标签改变或覆盖原件。

## 环境与未来测试方式

目标是Python3.10.20、Gurobi13.0.2、NumPy1.26.4、psutil7.0.0的独立Windows环境。
源生产环境是Linux/Python3.10.20/Gurobi13.0.2，平台差异须披露，不能声称纯CPU消融。
读取归档MPS可以测试求解器载入、排序和迭代，不能证明从Python源码构建全模型的峰值。

未来作者重新放行后，先确认许可额度、完成独立许可smoke，再运行单个有界测试。
采用32个求解线程，保留源数值参数；原LicenseID不写入新环境，许可身份与LP分开。
测试额外设置仅为日志、Threads32、Barrier前5轮停止、24h测试求解时间上限、
内存保护。Crossover仍为0；不改变模型、目标、变量、约束、容差或科学输入。

临时硬件试验的内存准入拟定为可用650GiB，低于30GiB空闲时请求终止；
Gurobi软/硬内存限额分别640/660GiB，传给Gurobi时换算成10^9 bytes的GB。
硬限额只约束Gurobi分配，不是整个OS内存的保证；软限额不能保证排序峰值严格受限。
这些是独立诊断的工程边界，不修改云端生产700GiB可用门槛，也不代表生产放行。

每次使用新输出目录，带互斥锁；保留参数、指纹、逐轮指标、1秒资源采样及
停止后仍可访问的BarX/BarPi/X/Pi。不可访问的向量标UNAVAILABLE，不伪称完整解。
硬内存错误可能导致求解器不再提供向量；原MPS和已有日志始终保留。
测试并非科学生产解，不外推5轮为收敛时间、全程内存上界或正式验收。

## WLS状态

作者提供的管理页面截图显示许可2868774的会话基线为2、截图时活跃会话为3，
并存在Over Baseline usage事件；月度最大4是已发生使用量，不是许可额度。
100个最大分布式工作者不等于100个普通并发会话。
WLS不绑定固定机器，但并发额度仍适用；不得用多建API Key、多个文件副本或
重新创建Env规避同一许可的会话限制。

官方依据：
- https://support.gurobi.com/hc/en-us/articles/34672988479633-What-are-the-restrictions-on-using-an-academic-WLS-license
- https://support.gurobi.com/hc/en-us/articles/34567582787345-How-do-I-resolve-the-error-Too-many-sessions
- https://docs.gurobi.com/projects/optimizer/en/13.0/reference/parameters.html

本轮不复制、读取或保存许可文件内容，不把任何凭据纳入工程包；实际许可配置
和并发名额确认留待作者下一次明确放行之前完成。
