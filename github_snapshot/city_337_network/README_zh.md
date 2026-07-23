# city_337 网页审阅数据子集

该目录是完整 `data/load_center_network/city_337/` 包的轻量网页审阅副本，不替代完整模型输入。

| 文件 | 内容 | 用途 |
|---|---|---|
| `load_centers.csv` | 337 个城市级节点、经纬度、省内年度需求权重及来源字段 | 检查节点定义和负荷权重 |
| `intra_edges.csv` | 642 条同省 AC500kV 代理边及其距离、成本、2025 初始容量 | 检查省内网络拓扑和容量初始化 |
| `load_center_initial_capacity_2025.csv` | 节点级风光/DPV 接口初始化 | 检查资源接入的 2025 边界 |
| `initial_capacity_2025_audit.csv` | 31 省节点/边/容量平衡审计 | 检查初始化闭合 |
| `manifest.json` | 完整原始 `city_337` 数据包的 SHA256 与 QA 摘要 | 检查版本和完整包范围 |

未包含 `vre_routes.csv`、`hydro_routes.csv`、变电站接口表及 8760h 时序数据。它们必须从完整、版本化数据根读取，不能由本目录替代。

关键口径：节点为城市级用电代理；节点的 `annual_demand_share_in_province` 在每省内闭合为 1；省内边通过 MST+3 nearest-neighbours 地理拓扑生成；2025 初始容量是资源空间接入的同步铭牌容量压力代理，并非实测线路额定容量。
