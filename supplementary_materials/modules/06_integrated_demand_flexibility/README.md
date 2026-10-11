# Module 06: integrated demand flexibility

## 2026-10-11 参数修订

本轮已将作者需求侧柔性修订并入中科大在线总稿的第 3.3、6.9、6.10、7.2 节，在线 pdfLaTeX 编译及引用、标签、编号、变化页版式核验通过。当前论文参数以[总稿镜像](../LATEX_manuscript/Article_Title__1_/Supplement_material.tex)及其 `06_model_formulation.tex`、`07_technoeconomic_parameters.tex`、`02_sp.bib` 为准；完整证据见[本轮审查报告](../../reviews/si_flexibility_revision_20261011/REVIEW_ZH.md)。

中央路径的供热/制冷参与率分别为 0.25/0.40/0.50/0.60 和 0.20/0.30/0.40/0.50；EV 合格池为 0.20/0.30/0.40/0.50，全体 EV 中 V2G 上限份额为 0.10/0.15/0.20/0.25，全国 V2G 功率上限为 10/60/120/200 GW（2030/2040/2050/2060）。真实资源成本与政策补偿支付分开，热服务仅对释放方向计活动成本，并采用四小时窗口的折减容量信用。具体成本、折减系数及敏感性口径见新 Tables S13、S20。

**本条记录论文文档修订，不代表模型代码、注册表或求解结果已经按新参数验收。** 参数落地和重算由独立任务处理。本目录既有独立 `.tex`、手工参考文献、生成表和 PDF 保留为历史交付，本轮未重新生成，不能继续作为 2026-10-11 总稿的最新参数来源；下文旧生成/编译命令仅复现原交付，不能用来覆盖在线总稿。最新交付 PDF 为[在线编译下载副本](../../output/pdf/Supplement_material_flexibility_revision_20261011.pdf)。

本目录记录 `flex_integrated_v5_central` 的论文补充材料、参考文献与可复现性边界。

## 文件

- `integrated_demand_flexibility_v5.tex`：可独立编译的中文补充材料章节；
- `integrated_demand_flexibility_methods_en.tex`：面向论文正文风格的英文补充
  材料章节，正文仅含四个小节，不暴露仓库内部情景和配置名称；
- `bibliography_manual_en.tex`：英文独立编译稿使用的手工参考文献表；
- `references.bib`：与正文引用键一致的机器可读参考文献；
- `README.md`：本说明。

正文采用手工 `thebibliography`，因此无需运行 BibTeX/Biber；`references.bib`
用于文献管理、查重和后续并入总稿。

中文稿保留完整技术合同与工程验证边界；英文稿是建议并入论文补充材料的正式
方法章节。二者服务对象不同，不应将中文技术稿直接翻译后投稿。

## 科学身份

正式主分析只比较：

1. `base`：固定负荷，不启用需求侧灵活性；
2. `flex_integrated_v5_central`：冷热服务、付费 V1G、内生付费 V2G 与
   降额后的可靠容量信用。

两者共享
`base_2024_vre_wave_on_flex_off_v1` baseline contract。V5 是独立的
analysis case，不反向修改 Base。历史 V3/V4 仅保留作可追溯工程记录。

## 证据与参数

正文参数表由以下当前仓库注册表解释：

- `config/flexible_load_v5_central_parameters.csv`
- `config/flexible_load_v5_parameter_registry.csv`
- `config/flexible_load_v5_source_registry.csv`
- `config/flexible_load_v5_source_count_qa.csv`

小时输入由 `scripts/build_flexible_load_v5_inputs.py` 确定性生成，并由
`scripts/validate_flexible_load_v5_inputs.py` 对源 ID、证据计数、四个规划年、
参数顺序和 SHA256 manifest 进行 fail-closed 审计。

## 编译

使用仓库外可用的 XeLaTeX/Tectonic 运行时编译：

```powershell
python <latex-skill-root>\scripts\compile_latex.py `
  D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\modules\06_integrated_demand_flexibility\integrated_demand_flexibility_v5.tex `
  --json
```

编译产物 PDF 仅是排版预览，不替代模型验收。任何 1h、24h、168h 或 744h
结果均为 `TEST_ONLY_TRUNCATED_HORIZON`；只有通过完整结果合同的 8760h
运行才能用于年度科学结论。
