# 2026-10-27 已完成结果验收与后续排程（阶段记录）

作者新增条款以 AGENTS.md 2026-10-27 与本轮明确补充为准。Mt 分母只用 annual_fossil_unabated_emissions_mtco2；总排放与净排放不得替代。新评估器只改五项质量平衡验收标签，不改物理模型、严格 QC、归档或状态。全年阈值 max(1e-5 Mt,1e-6×化石未减排排放)，短窗维持1e-5 Mt。缺值、非有限、非正分母、字段冲突报 ERROR；源年度碳表按 result_manifest 的 bytes/SHA 核验。

Case3 2040：本地与T550重评均PASS，原严格标签保留。分母1438.364949678045 Mt，门槛0.0014383649496780449 Mt；CO2来源绝对残差1.0819820274173217e-5 Mt。T550 assessment侧车和三个小JSON已逐字节同步本地；作者采纳记录绑定原result_manifest/状态SHA。未改写原输出。

两项备份COMPLETE：2026-10-27 10:15:20 UTC完成，190文件11,025,800,982bytes，六个层全部VERIFIED，source_unchanged=true；本轮读取两个最终manifest并匹配result_manifest SHA，未重复传输。证据backup_complete_verified.json。

分析小文件与nocredit相同规则（每个output文件≤32MiB）：Case3 2040为73个；B2030为78个，详见collection_summary.json及各collect_receipt.json。各文件bytes/SHA回读与源result_manifest一致；Case3通过T550取回，B因转发临时失联改用云端只读取回，身份与T550计划一致。原模型和向量仍留云端/T550。

B2030：sacct COMPLETED/0:0、116轮。/usr/bin/time最大RSS587090392KiB=559.893028GiB；Slurm另记584730628KiB，二者来源区分。116个相邻轮次间隔平均288.65543秒、中位274.99493秒、最小162.76150秒、最大444.46455秒；不含首轮前排序等启动耗时。按作者650GiB门槛，B2040/2050/2060选择48线程。原始证据见base_frozen_B_20261026/deployment_v3/final_20261027.json和逐轮CSV。

实现：relative_acceptance.py新增Mt规则；solution_export.py额外记录已有化石未减排指标；frozen_capacity.py兼容原CSV整数大小8354.0并按经过SHA验证的原始CLI+环境+scope+metadata恢复候选标志，防止旧ENGINEERING_BARRIER_CHECKPOINT_ONLY标签被错误当成非候选。三年真实上游三方验证均PASS，源文件未改。run_gate.py新增年份/来源参数，默认2030旧行为不变；2060参数核准沿用10-11定案，未修改数据。

验证：新Mt边界/缺值/非有限/分母冲突/负总排放/短窗/严格口径不变/源SHA测试，22项相关测试PASS；冻结源10项测试PASS；Gurobi13.0.2叠加环境、既有波浪数据下全套489 tests OK（1项Linux /proc测试在Windows跳过，原Linux回归已验证该未改动模块）。最初本机未设置波浪路径及Gurobi12的环境失败记录保留，不当成科学门禁失败。R1_v1同样保留缺波浪路径失败；R1_v2使用既有数据根完成，11385 cohort，bound-close一项3.545909315521081e-9 GW。

Case3 2050：1h筛选/不筛选只差BOUNDS_VRE_NEW；24h 102轮OPTIMAL，参数、tiny width、R1/数值白名单、服务M/信用、relative_v1和完整保全PASS。最终门禁见case3_2050_launch_20261027/FINAL_GATES_PASSED.json。T550证书仍在计算，生产尚未提交。

B三年：原Base状态均已恢复核验；T550按序流式提取各年hydro spur补表，2040的36686个VRE交叉值最大差0；年度1h/24h门禁正在推进。全部新sbatch由最近成功B2030v3实际脚本派生，WLS只比较登记路径字符串，不读取内容。各年所有门禁完成后才冻结/preflight/held资源核验并release；B三年一起放行。5207165未修改，无后台监听；各阶段失败与产物完整保留。
