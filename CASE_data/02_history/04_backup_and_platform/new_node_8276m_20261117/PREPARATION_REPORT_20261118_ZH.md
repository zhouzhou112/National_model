# 8276M新节点环境预设完成（2026-11-18）

**状态：PREPARATION_COMPLETE_TEST_DEFERRED_BY_AUTHOR。新节点直连云端已认证，测试软件和模型文件已准备好；作者明确暂不测试，未创建Gurobi授权环境/模型，未做许可smoke、presolve或optimize，未新增WLS会话。**

## 已核实的部署

| 项目 | 结果 |
|---|---|
| 本机→新节点 | 127.0.0.1:2222，用户zz2，专用密钥认证成功 |
| 新节点→云端 | 独立密钥；严格核验与本机既有可信RSA主机身份一致；hostname返回ln301.para.bscc |
| 新节点平台 | DESKTOP-30RRU21，Windows10工作站版，VMware虚拟机 |
| 当前资源 | 2026-11-18 17:44UTC复核44 vCPU、约800GiB系统可见内存、约785GiB可用；C盘剩余约640GiB |
| Python | 3.10.20，conda-forge，Windows x64 |
| Gurobi | 13.0.2，版本查询未创建Env |
| 依赖 | NumPy1.26.4、psutil7.0.0；pip check通过 |
| 环境路径（新节点） | C:/NationalModelBench/envs/gurobi1302_py31020 |
| 工作目录（新节点） | C:/NationalModelBench/ops_open2050_t32_20261118 |
| 授权状态 | setup/execution_authorization.json = PREPARE_ONLY |

此前700GiB是当时实测值；本轮最终两项独立系统字段（TotalVisibleMemorySize、TotalPhysicalMemory）均约800GiB，不能继续把700GiB当当前总量。未在本任务中修改虚拟机资源配置，不推定其宿主机物理内存、DRAM/Optane比例或独占核心数。未来诊断内存保护仍维持合同里较保守的650GiB准入/640GiB软限额/660GiB硬限额预设，本轮未执行任何求解器内存门禁。

## 模型与身份

从已完成OPS-Open2050冻结release选择10个文件，新节点直接SFTP拉取，目标逐文件bytes/SHA全通过；传输后源stat及archive_manifest SHA未变。

- release：20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1。
- 10件总量：4,148,859,327 bytes。包括原MPS、参数、归档/结果manifest、构建/求解/保全报告、运行环境、配置快照及原Gurobi日志。
- 压缩原MPS：4,148,509,456 bytes；SHA256 `33a4f822cbf894810082843e6ccabbb59db2183e3282f182b0df1cb807768a4b`。
- Python流式解压完成：44,277,662,634 bytes；SHA256 `eb226e5d4c7894cac319b6867b404ebbb6ba0ea3c928f04e0e4fa0706e2a7d72`；gzip CRC通过，解压用时245.281秒。
- 解压不创建Gurobi环境，也不是模型求解或性能测试。模型尚未加载到新节点Gurobi，因此没有宣称Windows侧模型指纹、排序峰值或迭代速度已经验证。
- 这是原LP回放准备，不是完整Python源码、所有CSV/时序输入及上游状态的重建部署。未来做新敏感性时仍需单独准备完整输入链。

## 许可与作者暂停决定

作者提供的管理页截图显示许可2868774的会话基线为2、截图时活跃3，月度最大4，并有Over Baseline usage事件。应按**两个并发会话基线**安排，而不是按两个线程或两台机器理解；100个最大分布式工作者是另一项能力，不能据此宣称普通会话额度为100。

WLS可跨机器，但仍受同一许可会话额度约束；结束环境后令牌还可能持续到寿命届满。官方说明普通学术WLS支持2个并发会话，需要更多额度应联系Gurobi支持。月度平均1.57和暂时能够并发3–4均不能证明长期额度提高。

依据：
- [学术WLS限制](https://support.gurobi.com/hc/en-us/articles/34672988479633-What-are-the-restrictions-on-using-an-academic-WLS-license)
- [Too many sessions与令牌寿命](https://support.gurobi.com/hc/en-us/articles/34567582787345-How-do-I-resolve-the-error-Too-many-sessions)

按作者本轮要求，只安装包、查询版本、校验/解压文件和验证执行锁；没有许可smoke，也未请求新令牌。用户默认gurobi.lic路径在最终核对时不存在，许可证内容未读取/复制/散列。现有云端作业和许可会话未做任何停止或更改；本轮未刷新其运行状态。

测试入口的smoke/run模式必须先通过execution_authorization.json，PREPARE_ONLY下在导入gurobipy前就拒绝执行。没有排队脚本、定时任务、后台监听或安装后自动测试。最终无本任务遗留Python/SFTP/Conda进程。

## 安装过程与保全

官方Miniforge26.9.4-2安装件SHA256：`9d83983669bc5d3b5dd4c631454bf953c3caf4ac78b9c9ada9971e5b021d83c3`，本机和新节点均验证。

新节点直接HTTPS取安装包失败，改本机取官方安装包并校验后上传；UU大文件传输导致两次控制连接超时。按作者恢复后先查旧进程，原模型直传继续并完成，未重复启动。安装包部分文件先与官方源前缀SHA核对，再续传；最终完整158,341,784bytes/SHA通过。后来尝试的云端中转安装包已无必要，按同UID/精确目标打开文件句柄确认本任务PID2855337后终止，云端8MiB部分文件及停止记录保留；生产目录未修改。

首次Conda安装在PowerShell遇到stderr警告被当作异常，实际依赖已安装；后续改为独立记录stdout/stderr并按进程退出码判断，核对已有环境后完成安装。旧失败与替换前日志保留。运行时使用显式路径，不改变系统PATH或系统默认Python。

## 验证、源码与后续入口

代码提交`6f379f79`已推送GitHub工作分支`codex/validation-pair-20261005`。Python语法检查、PowerShell语法检查、原参数身份校验、被修改参数拒绝、原LicenseID排除，以及PREPARE_ONLY对smoke/run的前置阻断均通过；这不是Gurobi实算验证。三个已部署脚本原始字节SHA与本机一致，见`validation_20261118.json`和最终收据；Git换行归一后的blob身份不冒充运行原件SHA。

依赖清单仅归一换行；远端原文件SHA另保留。pip_freeze含Conda构建机file://路径，只作审计，不直接用pip -r重建；重建使用conda_explicit清单，再安装gurobipy==13.0.2。

关键证据：
- final_preparation_receipt_20261118.json：环境、模型解压、授权锁、资源及无遗留进程。
- source_identity_20261118.json / target_transfer_verified_20261118.json / source_unchanged_after_transfer_20261118.json：传输身份闭合。
- conda_explicit_win64_20261118.txt / pip_freeze_win64_20261118.txt：精确软件清单。
- TEST_CONTRACT_ZH.md / validation_20261118.json：未来32线程五轮测试边界与执行锁。

**下一步必须等待作者重新明确放行测试，并先确认许可可用并发名额及新节点配置。** 不因环境已就绪、现有云端作业结束或网络恢复自动运行。本轮没有新求解、模型科学参数修改、云端冻结包改动、密钥私钥读取/复制或后台监听。
