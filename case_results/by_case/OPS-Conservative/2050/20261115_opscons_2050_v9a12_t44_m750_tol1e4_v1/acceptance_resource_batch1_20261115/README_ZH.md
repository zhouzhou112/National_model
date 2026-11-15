# OPS-Conservative 2050 验收包

当前relative_v1重评：PASS。备份全量bytes/SHA已通过，原QC与原输出不改。严格原标签：HARD_FAIL；失败项：unidirectional_interprovincial_flow, reservoir_transition, objective_components。水库逐站判定按作者规则暂缓并保留最大残差披露。此为质量标签，不自动决定作者采用规划状态。

P=5731237.048267890、D=5731044.783886630、P−D=192.264381260 million CNY。本案无候选筛选，不要求筛选证书。

年度行对偶因原SavedDual缺ConstrName而未自动导出；本包只读从本案原MPS+BarPi恢复1134行，原始54181831行的顺序哈希一致。annual_rows/annual_row_duals.csv是派生件，不是篡改原输出。工程对偶不代表市场结算。

analysis/包含各服务签约、上限占比、年调用、等效小时；全国及广东、江苏、山东、四川、内蒙古8760小时调度；31省逐时完整负荷侧边际价格；分省分技术发电与风光弃电、启停容量/等效次数/成本、储能运行和REF/中央OPS成本比较。启停是连续GW变量，等效次数不代表离散机组启动次数；D1/C5只作省内网络诊断。

原始小文件沿用Case3 2040清单的72项适用文件；无筛选的candidate_selection.csv不适用，另加本案冻结和结构审计。逐时原大型数组、MPS、BarX/BarPi留T550。
