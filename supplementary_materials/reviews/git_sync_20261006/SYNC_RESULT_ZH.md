# 同步结果（2026-10-06英国23:27）

本次已完成用户授权的安全范围提交与GitHub同步，未部署或修改运行服务器。

| 提交 | 内容 |
|---|---|
| `865e9661c6fa1f203ff433dfa5f169af133e266e` | 72个工程文件；V9模型/配置/工具及opt-in验证/测试 |
| `95e8faf97abff438a13cfeabbad9565d0f1fb913` | 403个文档/小型证据文件及忽略/同步规则；包含历史未提交的验证报告 |

`git push --atomic github HEAD:refs/heads/codex/validation-pair-20261005 HEAD:refs/heads/main`成功；23:26 `git ls-remote`核验两ref均为`95e8faf97abff438a13cfeabbad9565d0f1fb913`。该操作是从旧main的快进，包含之前遗漏的277个已有提交以及本轮工程/文档提交，没有强推或改写旧历史。本收据、README入口与最终交接作为后续收尾提交再次同步，不把文件自身尚未生成的提交号写进自己。

当前工作分支上游设为`github/codex/validation-pair-20261005`，本仓库`remote.pushDefault=github`；避免把无参push误送到固定机的`origin`。历史`codex/stagea-8760-final-v1`仍保留原指针作旧工程线参考，当前最新入口为main/validation-pair分支。没有更改GitHub可见性（原为public）。

## 校验

- 351个受测源文件保持原SHA，复用412项全套OK（1项Windows不适用跳过），不重复本机求解。
- 160个所选Python脚本语法检查，所选JSON解析检查通过；2个无效历史JSON未上传、原件保留。
- 初始候选474文件/约9.06MB扫描未发现常见凭据字面量；前11个未推送提交190文件版本扫描无命中。之后排除无必要的机器事件原件与对话引用元数据，并加入Git换行属性和检查摘要。
- 最终回归原log的Git index字节SHA仍为`bf65c47c52747ef14fb6385b1c1518e822d5f7af1c0771c2b4b98a7077fa2d79`，与原件一致。Whitespace检查允许证据CRLF与历史尾部空行，不修改受测/原证据字节以清理排版。
- 未修改生产源、参数、数据、运行包或job4844528；cloud/fixed源码差异详见REVIEW表与原始manifest。

## 本地仍保留什么

工程目录`cispo_model/config/scripts/tests`已无待提交改动。受跟踪文件仅`../../MODEL_V0719_REVIEW_REPORT.md`的历史稿件改写仍留本地（240增/388删），本轮未审核其科学表述，不代为发布。其余未跟踪项是未审核论文模块/PDF/PPT/图、原始实验文件、小型历史日志、运行副本和临时记录；大运行环境/临时树已添加ignore，均未删除。

本次同步保证的是审查后的工程源码与GitHub，不声称把整块工作目录镜像到公开仓库。以后按GIT_SYNC_POLICY_ZH逐任务同步；没有恢复自动监听或建立后台自动提交。
