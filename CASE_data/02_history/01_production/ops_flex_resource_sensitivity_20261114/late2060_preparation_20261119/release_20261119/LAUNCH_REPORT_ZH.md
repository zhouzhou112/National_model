# LATE-Open2060已提交并放行（2026-11-19）

作者审阅准备思路后明确要求继续求解；执行方说明工程门禁支持启动，但不保证全年收敛或受限误差很小。本次授权只覆盖已准备的2060包，保留此前准备阶段未授权记录，以新增author_release_20261119.json记录新授权。

Job **5658666** 已经held提交、资源核验后release。截至2026-11-19T12:43:32.877168+00:00，状态为PENDING，排队原因Resources，尚未分配节点。当前云端1项排队，未创建监听。

复核515件冻结文件全部SHA通过，manifest仍为97f939102e142ab5c843b5c54520f68787d08a3b6aa150a34dbd98cc426390c4；4879自由组、margin0.02，原R1状态、源码52958cf1、输入、参数和提交脚本均未修改。检查同一注册WLS路径字符串，不读取凭据。提交前队列为空，未超过4项上限。

资源：44个Gurobi线程，64CPU/750G/billing64/UNLIMITED/no-requeue，启动可用内存≥700GiB门槛保留。实际AllocTRES、许可smoke、启动内存和全年结构审计尚待节点启动后核验，不能提前标PASS。冻结参数核对Method2/Crossover0/Aggregate0/NumericFocus2/BarConvTol1e-4通过。

当前没有全年求解结果或新证书。解后须完整备份至T550、当前relative_v1验收、独立最大违反行及本解自身BarPi双向定价，B纳入成本区间。任何失败完整保全，不自动重跑或重解；不修改其他作业。

放行工具commit906dd578；证据本目录AUTHORIZATION.json、release.json及带时间戳status快照。后续先读既有submission/release与状态，不再次提交。
