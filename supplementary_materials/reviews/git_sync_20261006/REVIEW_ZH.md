# Git差异分类、发布范围与云端版本核验（2026-10-06）

本次用户授权检查未提交内容、提交安全范围，并尽量保持本地与GitHub同步。结论：**存在真实模型与工程代码改动，不能称为只有日志文档**。本次只版本化已验证的工作成果，不修改任何模型语义、不部署云端、不触碰4844528。

## 同步前的版本

| 位置 | 核验状态 | 与本地关系 |
|---|---|---|
| 本地当前分支`codex/validation-pair-20261005` | HEAD `0a03cc452e95d158f36923ceb5210267979b6234` + dirty | 含9月V9修复和10月验证的未提交内容 |
| GitHub `main` | `796a6fc6d0e37db1156c56d9fcbe2468db8cceef`，2026-07-24 | 本地HEAD之前277个提交，无远端独有提交 |
| GitHub `codex/stagea-8760-final-v1` | `860ab84`，2026-09-05 | 本地HEAD之前11个提交 |
| 云2050生产包 | `20260930_base2050_v9_t48_m750_tol1e4_v1/repo`，无.git | 196个代码/配置/脚本/测试文件逐SHA；10个与本地原始字节不同，其中2040 profile JSON语义相同，余8模型文件和runner有代码差异 |
| 云F/S factor包 | 各200个同范围文件，无.git | 冻结V9加factor入口；本地另有A/C措施；云专用case3派生配置不在本地根config中 |
| 固定机主repo | clean，`ba8e09f97a6526e299f807eb9be8c579a217caeb` | 244个文件中26个同路径字节不同，本地还有新增文件；不更新该checkout |
| 固定机数值验证包 | 独立repo副本，无.git，198文件 | 同路径仅B profile身份metadata与本地不同，已在数值报告披露 |

这些是2026-10-06只读实时核验，详细路径和逐文件SHA见`cloud_versions.json`、`fixed_versions.json`。云包不是Git工作树，不能把本地旧HEAD当作其完整源码身份；冻结包中已有尚未提交Git的V9工程代码。2050原包的2040 profile与本地差异仅JSON格式，见`cloud_2040_profile_diff.json`（空语义差异表）。

`github` URL为`https://github.com/zhouzhou112/National_model.git`，仓库可见性public；`origin`为固定服务器裸库，两个remote不能混称。此次仅向GitHub同步，不改远端工作目录。

## 未提交内容分类

初始盘点（新增本次审计文件前后计数存在少量自增）：27个tracked修改；74456个untracked，约9.51 GiB，主要不是源码。

| 类型 | 初始数量 | 处理 |
|---|---:|---|
| 已跟踪代码/配置/脚本/测试修改 | 17 | 审查diff、与最终回归源码SHA核对后纳入 |
| 新代码/配置/脚本/测试 | 55 | 包括水电/DAC修复、显式profile、恢复工具、factor入口和A/B/C诊断，纳入 |
| 根说明/合同/交接 | 修改9、新增3 | 纳入；新增同步约定 |
| 临时树 | 55540项，约3.28GiB | 不提交、不删除，添加适当ignore |
| output运行环境与输出 | 1495项，约0.75GiB | 不提交、不删除 |
| review原始证据 | 9004项，约4.65GiB | 仅提交审查摘要、顶层小型配置/判定/脚本和最终回归记录，原件继续保留 |
| 新论文模块 | 8328项，约0.61GiB | 未审核稿件/配图/构建文件，本轮不发布 |
| 其他补充材料 | 新增27项，约0.22GiB | 包含PDF/压缩包等，本轮不整体提交 |
| 连接/凭据候选文件名 | 4项 | 未读取内容、不提交 |
| `MODEL_V0719_REVIEW_REPORT.md` | tracked，240增/388删 | 较大历史稿件改写，本轮留在本地，不混入工程同步 |

准确机器统计见`inventory_summary.json`；逐文件全量清单`inventory_local.tsv`仅本地保存，不发布数万条运行时路径。

## 代码变化是什么

1. **V9模型与数据口径修复**：水电库容纠正表/读取入口、源单位微量清理、周期库容/弃水界处理、VRE微小floor/headroom和2030 DAC开关/后续年DAC恢复。这些是有科学含义的明确profile差异，早于本次已完成验证或用于云V9，不能称无模型改动，也不把旧Base与V9混成同一身份。
2. **工程运行与结果保全**：规范化profile守卫、实际参数回读、恢复/备份/资源记录工具和GPU测试启动器。提交脚本不执行它们、不自动启动任务。
3. **10月隔离验证**：factor TEST_ONLY入口及`--vre-screen-csv`；A微界清理/续接、B齐次profile、C分段求和和各测试。新开关默认关闭；A/B/C本轮被否决晋级，保留诊断能力与失败记录不等于生产启用。
4. **回归修正**：过时portfolio停止阈值断言改为已有实际值1e-4、子进程错误诊断和catalog审计。没有为了本次Git同步放松QC门槛或改测试结果。

## 审查与局限

- 351个`cispo_model/scripts/tests/config`受测源文件SHA与`unittest_verified_20261005T185140Z.json`完全一致，复用412 tests/OK(skipped1)证据，不重复本机求解。最终日志随小型证据提交。
- 所选Python文件做AST语法检查，JSON做解析检查；前11个未推送提交的190个文件版本及本轮拟提交文本未发现常见凭据字面量。扫描只是降低泄露风险，不声明能证明任意文本绝对无秘密；已知凭据候选按文件名排除且未读取。
- 检查发现两个历史`.json`并非合法JSON（一个含额外输出、一个为空），记录在`invalid_historical_json.json`，已排除发布，原件未改；初次检查失败不计通过。它们不是本轮有效判定/回归证据。
- `.gitignore`补齐output、临时树、许可证/私钥和大型模型归档；这些操作只影响Git发现，不删除任何原件。
- `.gitattributes`对唯一入库的最终回归原log禁用文本换行转换，保留原SHA。既有测试源末尾一空行的whitespace提示保留，以维持受测原字节；其余工程diff用`core.whitespace=-blank-at-eof`检查通过，没有为排版修改受测代码。
- 未提交全部review原始文件，因此GitHub上的部分证据相对链接指向本地/远端档案，不能宣称仅clone即可取得全部数据。所有raw SHA和归档路径仍在报告中，数学/科学接受结论沿用既有QC状态。
- 同步使用普通fast-forward push，禁止force；不更新云release、不执行`scontrol`/`scancel`/`sbatch`。`main`同步到经审查的工程快照，不代表生产科学结果已经通过QC。

## 持续同步

采用`GIT_SYNC_POLICY_ZH.md`：任务收尾明确清单提交/推送，GitHub工作分支与无分叉的main及时快进；远端运行release保持冻结，下次部署建新目录。无后台自动监听/自动提交。实际提交号与远端核验写入本目录后续`SYNC_RESULT_ZH.md`及handoff。
