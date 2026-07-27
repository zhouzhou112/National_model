# GitHub 网页审阅入口（city_337）

本仓库的生产空间层为 `city_337`：337 个城市级负荷中心、642 条省内候选输电边；278 节点 Natural Earth 层仅保留为 CISPO 复现/敏感性输入。网页端审阅可按以下顺序阅读：

1. `README.md`：模型边界、运行方法与成本口径；
2. `cispo_full_lp_model_spec.md`：变量、约束、目标函数和单位；
3. `cispo_model/master.py` 与 `cispo_model/monolithic.py`：容量成本、8760h 运行成本及 LP 构建；
4. `cispo_model/load_center.py`、`cispo_model/planning_state.py`：337 节点网络和严格跨年状态；
5. `config/optimization_2030.json` 与 `config/scenarios/`：波浪整合 Base 与唯一 V3+V2G 柔性覆盖；
6. `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md` 和 `SERVER_RUNBOOK.md`：已验证服务器门禁和下一步限制。

`github_snapshot/city_337_network/` 是专供网页审阅的小型数据包，包含 337 节点属性、642 条省内边、2025 节点接口初始化、初始化审计和原数据包 manifest。它用于检查空间口径、需求权重、拓扑和初始化，不是可独立求解的数据包。

未上传的完整输入包括 8760h 负荷/容量因子、站级水电序列、完整 VRE/水电路由及全部优化输出；这些数据体量大，且必须与版本化完整数据根一起做 SHA256 核验。仓库中不包含 Gurobi 许可证、密钥、服务器路径凭据或用户补充材料的未提交改动。

历史固定服务器的无波浪 Base、V1 和第一代 V2G 门禁仅是旧模型边界下的求解/接口证据，不能替代当前波浪整合 Base 的新 8760h 科学规划结果。
