# Module 06: integrated demand flexibility

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
