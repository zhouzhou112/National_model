# Base2040 单轮变慢：只读诊断

检查时间：2026-09-25 03:17–03:22北京时间（英国09-24 20:17–20:22）。Git `0a03cc452e95d158f36923ceb5210267979b6234`+既有dirty，未提交。作业4682935，节点m4cg1701。未修改模型、配置、CPU绑定、内存策略或服务器权限，未暂停/重启/新提交作业。

## 结论与边界

现有证据支持：单轮内部工作量增加是变慢的重要原因，不支持“当前其他任务抢CPU、CPU配额节流、swap或磁盘等待”解释。不能从CPU利用率断言内存带宽已满或未满；全机性能计数器访问被拒绝，未测得DRAM GB/s。也不能确定增加的Work具体来自中心校正、数值精化或其他内部步骤。

## 计算与系统证据

- `squeue -w m4cg1701`仅显示4682935；`scontrol show node`为CPUAlloc64/CPUTot128、AllocMem768000MiB。`ps`所见无其他高CPU用户进程，主要计算进程为本作业python PID31149。
- 两次读取/proc间隔30.038s：进程CPU4384.3%（约43.84个核）；44个线程各约99.4–99.6%。这些工作线程调度等待约0.06–5.77ms/30s，非被其他任务长时间挤占。全机busy34.52%、iowait0%、steal0%；CPU64–127平均busy仅0.14%。该样本只代表所采阶段，不代表整轮平均。
- 进程132个总线程不等于132核忙碌：实测高占用44线程，其余主要休眠。任务及父job/uid的cpu.stat均nr_throttled0，task cpu.cfs_quota_us=-1。
- free显示约332GiB available，swap不存在；进程VmSwap0。vmstat三个5s间隔均wa0、si/so0、bi/bo0、blocked0。30秒进程read_bytes/write_bytes均无增加。GPFS诊断需注意这些计数不能单独代表全部网络文件系统流量。
- /proc/net/dev差分：ens16f0约0.0033MB/s接收、0.0032MB/s发送；ib0约0.1086MB/s接收、0.0047MB/s发送。此为网络接口计数，不是DRAM带宽，也不覆盖所有可能的原生RDMA流量；结合I/O等待为0，无网络文件读写瓶颈证据。
- perf针对本进程10s统计：cycles:u=1477290499961，instructions:u=4911922926671，IPC3.32；cache-misses:u=5000263256。不能将cache misses乘缓存行大小冒充DRAM流量。CPU governor=performance，部分核心cpuinfo瞬时3.10–3.35GHz，没有低频证据但没有历史频率曲线。
- perf全机`-a -e cycles:u -- sleep 1`被权限拒绝，perf_event_paranoid=2；amd_umc/amd_df PMU存在但没有events命名目录。没有修改权限或猜测raw事件编码，没有运行带宽压力测试。

## 单socket绑定事实

全部采样工作线程affinity与Slurm cpuset均0–63，lscpu证实均属socket0/NUMA0；不是双socket各22线程。numastat -p31149：NUMA0=364857.61MiB，NUMA1=41707.66MiB，远端驻留约10.26%（不是远端访问比例）。这可能限制可利用的内存通道范围，但无带宽实测，不能确认为本次突然变慢根因。

启动runtime_slurm_job.txt记录MinCPUsNode125，当前scontrol为64；SlurmdStartTime现为09-22 10:46:05，OS BootTime仍09-17、作业Restarts0。没有启动时逐线程affinity记录，不能由MinCPUsNode直接推导旧CPU集合，更不能断言调度器更改绑定导致变慢。

## 每轮Work分解

来源：release `20260919_base2040_v9_t44_m750_tol1e4_v1/output_8760/solver_telemetry.jsonl`，完整读取329条barrier事件（iter0–328）。代码`cispo_model/diagnostics.py`将Gurobi回调WORK原样记录为work_units，不是用墙钟时间代算。以下均端点差分除以轮数差。

| 迭代区间 | 分钟/轮 | Work/轮 | Work/秒 |
|---|---:|---:|---:|
|237→260|21.0330|2955.37|2.3418|
|260→277|21.8713|3307.23|2.5202|
|277→290|24.6631|4483.41|3.0298|
|290→306|32.0432|7617.84|3.9623|
|307→317|24.7810|4536.56|3.0511|
|317→327|29.1551|6398.70|3.6579|

相对260→277，最近317→327每轮Work增加93.48%，每轮墙钟增加33.30%；不是同样Work单纯等待更久。Work/秒不能跨不同内部工作组合当作硬件性能基准，但此结果与“纯外部抢占”解释不符。

单轮例子：iter325耗2598.84s（43.31分钟）/12384.44Work；iter326耗1511.60s（25.19分钟）/4720.09Work，慢轮伴随更多Work。迭代328已完成，P1.16295893e7、D1.82282919e6，尚未收敛。

Gurobi文档：Work不是墙钟Runtime，在同硬件/参数下具有确定性；中心校正数量可使每轮计算更昂贵，但本日志不报告实际校正数，故只是候选机理，不宣称已识别内部根因。
- https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/model.html#work
- https://docs.gurobi.com/projects/optimizer/en/current/concepts/parameters/guidelines.html

## 复现与下一步

只读命令：SSH登录别名paracloud-bscc-a8，再SSH计算节点；squeue/scontrol/ps/free/vmstat/numastat，读取/proc/stat、/proc/31149/task/*/{stat,schedstat}、/proc/net/dev、/proc/31149/io、cgroup cpu.stat/cpuset；perf stat用户态进程计数10秒与全机权限探测；读取原gurobi.log及solver_telemetry.jsonl。

下一步在后续状态查询中同时报告ΔRuntime与ΔWork。若需进一步确认DRAM饱和或NUMA方案收益，需管理员提供节点UMC/DF带宽历史或只读测量；任何改变当前CPU绑定/内存策略或进行新配对试验须另行明确授权，不能以此诊断自动干预现有长作业。
