# OPS-Open 2040 第二批启动记录

Job 5590946 已提交并release；门禁及preflight PASS。当前等待节点资源，实际分配和启动内存尚待验证，不标为已运行。44线程，64CPU/750G/UNLIMITED/no-requeue，启动可用内存至少700GiB。

原冻结来源/上游/闭合复用已验收B2040，作者输入文件原样使用；全年碳上限不变。无候选筛选。终态后完整T550备份（5%余量）、relative_v1验收、年度行对偶恢复和小文件回传。第三批未授权，不自动提交。

证据：D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\reviews\ops_flex_resource_sensitivity_20261114\batch2\deployment\ops_open_2040

## 2026-11-15 22:53UTC 第二批2040/2060启动检查通过

Job5590946（OPS-Open2040/m4cm1702）和5590961（OPS-Open2060/m4cm1803）均于22:48:15UTC开始运行；实配cpu64/mem750G/node1/billing64、UNLIMITED/no-requeue。启动可用内存分别720.655060与719.145313GiB，均≥700，Gurobi13.0.2计算节点smoke PASS，stderr空，配置44线程；全年模型仍在构建，实际求解参数/全年服务上界读回待构建完成。云端3运行（含LATE5587177），无新增第四项；2030仍在门禁STOP等待作者窗口预算决定，不能因另两案已运行而绕过该门禁。

证据batch2/startup_verification_2040_2060.json及snapshots/20261115T225352Z/snapshot.json。放行与2030停止证据eb85777c，模型源码相对537项覆盖回归无变化。case_catalog已改RUNNING。下一步：作者明确2030短窗例外前不重跑或提交2030；后续询问时只读核实际模型构建/迭代，终态按5%余量规则备份、T550恢复年度对偶和验收；第三批未提交，无监听。
