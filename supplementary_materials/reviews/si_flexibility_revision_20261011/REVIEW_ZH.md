# 需求侧柔性补充材料修订审查（2026-10-11）

记录时间：2026-10-11 16:51 UTC。状态：**在线交付与本地文档同步完成**。最终在线编译 `run6` 成功，97 页；未定义交叉引用/引文、重复标签、重复 bib 键、LaTeX 错误与溢出均为零；表格 S1–S26 连续，四张新表均有正文引用。13 条 `[VERIFY]` 中 12 条闭合，NESO 2025 条目部分核实并保留说明。

## 1. 范围、输入与工作流

- 在线项目：[Article Title (1)](https://latex.ustc.edu.cn/project/6a26c6aedd9bc0323aea31d8)。根文档 `Supplement_material.tex`，doc ID `6a26c6ffdd9bc0323aea33a1`，编译器 `pdflatex`，实际 bib 为 `02_sp.bib`。没有切换根文档或编译器。
- 已按 AGENTS 读取 Current validated snapshot、模型规格、MODEL_SERVER_STATUS、SERVER_RUNBOOK、通用论文同步经验及本轮完整任务书。模型服务器状态没有在本轮重新实查，不把历史交接的作业状态当实时状态。
- Git 实查基准 `3100bb325b691d8d398c680dcfd879b80f8f4026`；工作区另有参数落地任务的模型、配置、脚本和测试改动。本任务只写论文文本/书目、说明、交接与隔离审查证据，未修改模型实现、输入数据或运行包，未运行求解器，未 commit/push。
- 四份作者输入的原样备份在 `author_inputs/`，其 SHA256 见 [preflight.json](preflight.json)。模型参数和资源规模采用作者给定稿件，未独立重跑其科研结果。
- `olcli pull` 从在线项目下载全部 59 个文件到 `work/before/`，逐文件哈希见 [pull_manifest.json](pull_manifest.json)。Socket 读取的 21 份文本另存 `work/before_socket/`，与完整拉取文件按 LF 归一后一致；在线元数据见 `before_metadata.json`。
- 实际顺序为：在线最新基线 → 本地隔离定点修改 → 比较远端当前版本 → 只回传 4 个目标文件 → **中科大在线编译** → 下载 PDF/日志 → 远端回读/自动核验/PNG 版式检查 → 本地镜像同步。本地 `output/pdf` 是在线编译结果下载副本，本轮没有在本地 TeX 编译。

## 2. 修改映射及差异

完整替换前后差异：[manuscript_changes.diff](manuscript_changes.diff)，基线是本轮在线快照，不能用较旧本地副本代替。

| 文件/位置 | 已执行的变更 |
|---|---|
| `Supplement_material.tex` 原 1883–1953 行、S3.3 | 整段纳入作者修订，保留 `sec:demand_flexibility_representation` 和 `eq:effective_load`；增加政策、文献、中央参数、资源规模四表及正文引用 |
| 同文件 S3.1 总述 | 将旧的无额外容量信用表述改为四小时折减容量信用；仍不另给备用或惯量信用 |
| `06_model_formulation.tex` S6.9 | 替换热合同上限解释、EV 合格池、V2G 份额解释及资源成本式；原物理状态、功率、能量、有效负荷方程保持原样 |
| 同文件 S6.10 | 原充裕度条件替换为四小时窗口的服务信用及折减系数解释；成本/充裕度原标签 `eq:m-flexcost`、`eq:m-adequacy` 保留 |
| `07_technoeconomic_parameters.tex` S7.2 | 服务参数、参与率、年度/活动成本、信用说明与新表一致；保留原表标签 `tab:te-flex` |
| `02_sp.bib` | 原 108 条原文保留，去除 2 组同 DOI 新别名，净追加 25 条，总计 133 条；121 个正文引用键均可解析 |

### 相对输入文件的必要修正

1. 作者文献证据表两行误用单反斜线结束，已改为合法换行；将不兼容当前数字型 BST 的 `\citet` 改为显式作者名配 `\citep`，消除 `(author?)`，未更换引文样式。
2. 作者给出的 `rho=rho_y*f_y/f_y` 是恒等化表达，不能说明相对分母。定义全体 EV 中 V2G 上限份额 `q_y=0.10/0.15/0.20/0.25`，明确 `rho=rho_y=q_y/f_y=0.50`（中央路径），与同一 EV 总体和给定表值一致，不改 S50–S54 物理方程。
3. 容量信用式中的 D/Q 补为已有 EV 包络定义的上横线符号；长成本式按加法项断行。此为符号一致性和排版修正，未改变给定成本或信用计算含义。
4. 任务书所称旧服务 Table S16 在实际在线快照是 **S17**，标签为 `tab:te-flex`。按现有标签定位；替换旧 S3.3 一张表为四张，净增三张，服务表最终为 **S20**。
5. 新表 S11–S14 均用 `[p]` 与 `\resizebox{\textwidth}{!}`；其中前三张以 landscape 展示以保证可读性，资源规模表为纵向专页。S7.2 服务表按原项目习惯用 `[H]`，改善文字衔接；四张新表的专页要求未变。
6. 原 S50–S54 的五个 equation 块 LF 归一后逐字相同。因 S3.3 新增参与率公式，它们现在编号为 S51–S55；`eq:effective_load` 的式体也逐字相同，现在为 S24。成本原 S55→S56，充裕度原 S57→S58；由标签自动引用，不强行固定旧编号。
7. S7.2 原“分别开启热/EV/联合三情景”改为已在作者交接确认的 Base 与联合灵活性主比较。其他章节数值及原有图表内容未改，仅自动页码/编号顺延。
8. 文献核验改变了若干作者、题名和卷页；上海 2025/2026 两目标分引两份官方文件。英国 79% 改为官方可证的 **2024** 评估口径，引用新增 DESNZ 政府条目；未将未核实 NESO 2025 条目作为正文证据。

## 3. 编译、引用和版式验证

最终证据目录为 [work/run6](work/run6/)，此前各次编译保留供排错追溯，不是交付版本。

| 检查 | 结果/证据 |
|---|---|
| 在线编译 | `compile_summary.json` 为 success；[output.log](work/run6/output.log)、[output.blg](work/run6/output.blg) 无 TeX/BibTeX 错误 |
| PDF 完整性 | 97 页，43,425,528 bytes，与编译日志一致；SHA256 `d4f8a93198b4466f750ed3de573dfcf60e5612ac070fb46a2283c29cdfc96c17` |
| 引用与标签 | 157 个唯一 label；交叉引用缺失 0、引文缺失 0、重复 label 0、重复 bib key 0；[validation.json](validation.json) |
| 表格编号 | S1–S26 完整连续，`.aux` 与 PDF 提取结果交叉核验 |
| 原物理公式 | 除明确授权替换的成本/充裕度外，S6 的原有 40 个 equation 块全部保持；保护的五式及 S3.3 有效负荷式通过 |
| 回传边界 | 只回传 4 个目标文件；最后一次仅 S7 文件实际变化。21 份文本回读一致，17 份非目标文本未变；55 个非目标实体的 ID/名称/类型未变，没有新增、删除或上传图片 |
| 二进制边界 | 初始全部下载并记录 SHA；最终未重新下载所有非目标二进制内容，因此不声称逐字终态复核了全部图片 |
| 版式 | 已渲染并查看变化后 39–97 页接触表；新证据表/成本与信用公式放大检查，最终页 80 服务表放大检查；[visual_review.json](visual_review.json) |
| 剩余警告 | 仅原类文件的 `U/rsfs/m/n` 16pt 字号替代及汇总提示两条字体警告，无 Overfull 或 float-too-large |

| 标签 | 最终表号 | 表所在页 | PDF 中提及页（含正文和表题） |
|---|---|---:|---|
| `tab:flex-policy-anchors` | S11 | 43 | 40, 43 |
| `tab:flex-literature` | S12 | 44 | 41, 44 |
| `tab:flexibility-parameters` | S13 | 45 | 41, 45, 76 |
| `tab:flex-resource-scale` | S14 | 46 | 42, 46 |
| `tab:te-flex` | S20 | 80 | 80 |

## 4. 全文旧表述检索

检查范围为主文档及其实际加载的 04/05/06/07 章节，评论行剔除后核对引用。未将未加载的历史稿件全文重写后回推。

- “EV 池为 15% / f=0.15”已替换为分年 20/30/40/50%；V2G 全体份额和合格池相对份额分别说明。
- “300 激活成本”不再是中央真实资源成本。保留的 300 只出现在历史说明或明确标注的 compensation-basis sensitivity；两者与资源成本分开。其他不相关章节的 300 数值不擅改。
- “10/20/30/40 V2G 上限”已替换为 10/60/120/200 GW。
- “no additional firm-capacity credit”以及服务完全无容量信用的原表述已替换。无信用 `baseline_peak_v1` 仅作为敏感性口径保留。
- 所有含 300、15%、0.15 和旧信用口径的剩余匹配保存在 `validation.json` 的 `legacy_matches`，逐项区分敏感性、分年份额或无关原数据，未用机械替换破坏别处数值。

## 5. [VERIFY] 处理清单

完整逐条核验、官方 URL 与书目信息见 [REFERENCE_VERIFICATION_ZH.md](REFERENCE_VERIFICATION_ZH.md)，覆盖作者输入全部 13 个标记项。

**已核实 12 项**：`zhang2026chinatimes`、`han2026v2gwta`、`jia2026v2gtransport`、`roth2024heatpumps`、`odenweller2025dsm`、`blonz2021thermostat`、`e3spp2025`、`ndrcnea2026plan`、`ndrc2026capacity114`、`jiangsu2024dr`、`guangdong2025v2gtariff`、`shanghai2025ac`。

**部分核实 1 项**：`neso2025derating` 的直接 2025 报告 URL 和对应 DSR 因子未闭合，保留 `[VERIFY]` note 及 NESO 官方容量市场入口。英国政府公开文件明确把 79% 指向 2024 ECR；正文采用该可核实来源 `desnz2025clf`，未把 2024 的因子误记成 2025。政策/报告/预印本不编造期刊卷期页。没有把本轮书目身份核验夸大为全部外部文献数值重算。

## 6. 本地同步与文件清单

- 本地总稿目录 `modules/LATEX_manuscript/Article_Title__1_/` 的四份目标文件已从在线最终回读同步；补齐原来缺失的 `04_grid_connection.tex`、`05_other_generation.tex`、`supplement-nature.bst`，三者内容与线上基线一致。
- 原本地总稿/bib 在 `local_before/` 保留，不用其覆盖线上。本地同步哈希见 [local_sync.json](local_sync.json)。本地目录的历史图片未在本轮统一刷新；要从完整快照复现，请复制 `work/before/` 到新的隔离目录，再覆盖 `work/run6/readback/` 的四个目标文件，避免用旧图片目录冒充完整最终源包。
- Module 06 的 `README.md` 和 `README_load_reconstruction_and_flexibility_en.md` 均新增“2026-10-11 参数修订”，注明最新总稿来源及旧独立稿/生成器边界；未重建旧模块图表或 PDF。
- 最终 PDF：`output/pdf/Supplement_material_flexibility_revision_20261011.pdf`，与服务器下载文件逐字相同。
- 交接：`../CODEX_HANDOFF.md` 新增当前状态摘要，并在日志末尾追加本轮版本条目，不改写历史记录。
- 本轮脚本：`snapshot.mjs`（取证）、`prepare_revision.py`（定点合并与 diff）、`work/publish.mjs`（复用成熟定点上传流程）、`validate_revision.py`（自动核验/渲染）、`finalize_revision.py`（本地同步/报告/交接）。这些是审查辅助文件，不属于模型实现。

## 7. 可复现命令与执行边界

以下命令均从 `supplementary_materials` 运行。准备脚本在本地已有最终镜像时仍以 `work/before_socket/` 为在线基线；备份不覆盖。

```powershell
python reviews/si_flexibility_revision_20261011/prepare_revision.py
# 已执行的最后一次在线操作：expected 是上次已核验远端版本，run6 必须是新目录
node reviews/si_flexibility_revision_20261011/work/publish.mjs run5/readback run6
# 使用装有 pypdfium2、pypdf、Pillow 的 Python 运行时
python reviews/si_flexibility_revision_20261011/validate_revision.py --run run6
python reviews/si_flexibility_revision_20261011/finalize_revision.py
```

在线发布脚本逐项比对远端当前文本；后续重跑时必须重新拉取/合并作者变化并使用新的 expected/run 路径，不可机械照抄上述历史发布命令。自动检查脚本重跑会将视觉状态置为 PENDING，需要对对应产物再次确认。实际核验使用 Codex bundled Python（提供 pypdfium2、pypdf 和 Pillow），无本地 TeX 安装依赖。

## 8. 限制与下一步

本轮完成文档整合验收，不验证参数已在求解实现中生效。作者稿中的后期 V2G 上限“不约束”、基准电价下不签约以及资源规模/峰值比例等内容沿用授权输入；未在本轮重新运行价格接受者或全年模型，不能据此宣称已经获得新的科学结果。稿件中的补偿敏感性“保留/报告”描述的是研究口径，不证明相应情景已经计算完成。

剩余事项是 NESO 2025 原报告的直接核验，以及独立参数落地任务完成代码/配置/输入一致性与结果验收。作者重点审阅新 S11–S14、S20 及 S6.10 容量信用段。按当前指令，所有变更留在工作区，由参数落地任务审查明确文件清单后统一提交；本任务不提交、不推送、不自动部署或启动新作业。

## 9. 四个线上目标文件 SHA256

下表为 UTF-8/LF 规范文本，与本地同步副本一致；初始完整下载清单另见 `pull_manifest.json`。

| 文件 | 修改前 | 修改后 |
|---|---|---|
| `Supplement_material.tex` | `1fce8b4296b0eb114b2d61d5898944f31f3ee2d1dc9655274349ef5ab82ff13d` | `4c68d3367b108398a37110b923c54c24555f87695dda0cbbdae366bbd9bd9679` |
| `06_model_formulation.tex` | `d77a933661b326299f79a85cfaf09a646adac03f5a5760184e206c544479ca7f` | `f890dcf2acf0c54232cda920adebcf46b9f0952c30002f559fd7045aa174d46c` |
| `07_technoeconomic_parameters.tex` | `c329f92da6ef6e6ac0bc66af6a874254e53edeb4fa49c27ac957eddd8352896f` | `c30afd90fb73c9b28234603f423e6095fd1b4beb42b3a0bb80f47a9acb01fbb3` |
| `02_sp.bib` | `08d990f99e7ba10d401f0ea5ca02e73a1a4d1862397cddf3a760067ab027e84d` | `0d11ef431d9daa57a398c88f1a99ecc9a980be8b73de0a52df9b16c24c464740` |
