# 论文情景正式名称修正

上轮只在副说明中写正式名称，主入口仍以历史代号分类。本轮按作者指出的问题修正，主要入口使用论文已经批准的名称。

| 历史代号 | 正式情景名 |
|---|---|
| Base | REF |
| B | OPS |
| C | LATE |
| Case3 / A | PLAN |
| nocredit | PLAN-NC |
| C5 | D1（诊断） |

命名依据是 `claude_workspace/paper/common/figstyle_paper.py` 的 `SCENARIO_LABEL` 与《图件规范与五图定稿》正式命名表及批准执行条目。脚本读取该字典验证五个主情景映射，不导入绘图模块。资源敏感性保持 OPS-Open、OPS-Conservative、LATE-Open；资源情景的 Base 不等同于原模型代号 Base。

本地总览仍为 `case_results/00_案例总览.html`，现点击正式名进入 `case_results/by_paper_scenario/<正式名>/<year>/<release>/index.html`。旧核心目录中的页面标题也更新。目录台账、年度概要表、覆盖清单增加 `paper_scenario` 和 `legacy_case`，保留既有 `case` 字段以兼容分析脚本。`paper_scenarios.json` 是统一映射来源。

T550 总览仍为 `/home/zz2/National_model_server/case_library_v2_20261123/INDEX_ZH.md`，新建同根 `by_paper_scenario/<正式名>/<year>/<release>/`，含 `core` 和 `archive` 导航链接。原备份、核心数据、验收证据及 release 身份不重命名、不改写、不复制。旧总览留在 history 中。

验证：29 案对应唯一正式名；本地 59 个页面、1155 个链接通过；远端 58 个新导航链接通过；两端均重核 590 份原交付文件 SHA 不变。没有新分析、新求解或大文件传输。

入口安装脚本已追加正式命名步骤，避免重建总览时恢复旧标题。生成页面可本地重建，Git 保存脚本、映射、台账和校验收据。起始 Git `f1c6ebaa`；实现提交见本目录同步收据。
